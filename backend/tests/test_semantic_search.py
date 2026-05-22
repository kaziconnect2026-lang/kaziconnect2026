"""Backend tests for the rewritten /api/professionals/search endpoint.

Covers:
- Filter-only search (category, location) with NO `q` text
- category id snake_case ↔ profession display name mapping
- Semantic intent expansion (leaky tap → plumber, haircut → barber,
  windshield broken → mechanic via last-word fallback, power socket → electrician)
- Name search
- Empty-params returns all available pros sorted by rating
- Scoring requires real content hit (no rating-only matches in q-mode)
- Regression: /api/match still returns hybrid scoring fields
- Regression: /api/auth/login, /api/professionals/{id}, /api/jobs,
  /api/wallet/balance, /api/conversations all still work
"""
import os
import pytest
import requests
from pathlib import Path

# Load REACT_APP_BACKEND_URL from frontend/.env (single source of truth)
def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        env_path = Path("/app/frontend/.env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("REACT_APP_BACKEND_URL="):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    assert url, "REACT_APP_BACKEND_URL not set"
    return url.rstrip("/")

BASE_URL = _load_backend_url()
SEARCH = f"{BASE_URL}/api/professionals/search"


# ---------- Fixtures ----------
@pytest.fixture(scope="session")
def s():
    return requests.Session()


@pytest.fixture(scope="session")
def admin_token(s):
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": "admin@kazilinks.com", "password": "admin123"})
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    body = r.json()
    return body.get("token") or body.get("access_token")


@pytest.fixture(scope="session")
def client_token(s):
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": "client@test.com", "password": "password"})
    assert r.status_code == 200, f"client login failed: {r.status_code} {r.text}"
    body = r.json()
    return body.get("token") or body.get("access_token")


def _professions(results):
    return [(p.get("profession") or "").lower() for p in results]


# ---------- /api/professionals/search ----------
class TestSearchFilterOnly:
    def test_category_barber_location_karen_returns_barbers(self, s):
        r = s.get(SEARCH, params={"category": "barber", "location": "Karen"})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1, "expected at least 1 barber in Karen"
        # All returned must be barbers
        for p in data:
            assert "barber" in (p.get("profession") or "").lower()
        # All locations must contain 'karen'
        for p in data:
            loc = (p.get("user", {}).get("location") or "").lower()
            assert "karen" in loc, f"location {loc} doesn't contain karen"

    def test_category_tattoo_artist_snake_case_matches_profession(self, s):
        """category='tattoo_artist' must transform to regex 'tattoo artist' and match the profession field."""
        r = s.get(SEARCH, params={"category": "tattoo_artist"})
        assert r.status_code == 200
        data = r.json()
        # If no tattoo artists in seed, list is empty — that's fine. But every result must be tattoo artist.
        for p in data:
            assert "tattoo" in (p.get("profession") or "").lower()

    def test_location_only_returns_all_in_location(self, s):
        r = s.get(SEARCH, params={"location": "Nairobi"})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        # All results must have Nairobi in location
        for p in data:
            loc = (p.get("user", {}).get("location") or "").lower()
            assert "nairobi" in loc
        # Verify rating-desc ordering (allow ties)
        ratings = [p.get("rating") or 0 for p in data]
        assert ratings == sorted(ratings, reverse=True)

    def test_no_params_returns_all_available(self, s):
        r = s.get(SEARCH)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
        ratings = [p.get("rating") or 0 for p in data]
        assert ratings == sorted(ratings, reverse=True)


class TestSemanticIntent:
    def test_leaky_tap_returns_plumbers(self, s):
        r = s.get(SEARCH, params={"q": "leaky tap"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0, "expected plumbers for 'leaky tap'"
        profs = _professions(data)
        assert all("plumb" in p for p in profs), f"non-plumber in results: {profs}"

    def test_haircut_returns_barbers(self, s):
        r = s.get(SEARCH, params={"q": "haircut"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0
        profs = _professions(data)
        assert all("barber" in p for p in profs), f"non-barber in results: {profs}"

    def test_windshield_broken_returns_mechanics(self, s):
        """'windshield' → 'car mechanic'; last-word fallback 'mechanic' regex matches DB profession 'Mechanic'."""
        r = s.get(SEARCH, params={"q": "windshield broken"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0, "expected mechanics for 'windshield broken'"
        profs = _professions(data)
        assert all("mechanic" in p for p in profs), f"non-mechanic in results: {profs}"

    def test_power_socket_returns_electricians(self, s):
        r = s.get(SEARCH, params={"q": "power socket"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0
        profs = _professions(data)
        assert all("electric" in p for p in profs), f"non-electrician: {profs}"


class TestNameSearch:
    def test_name_john_returns_john_kamau(self, s):
        r = s.get(SEARCH, params={"q": "john"})
        assert r.status_code == 200
        data = r.json()
        # Must include at least one user whose name contains 'john'
        names = [(p.get("user", {}).get("name") or "").lower() for p in data]
        assert any("john" in n for n in names), f"no 'john' in {names}"


class TestScoringRequiresHit:
    def test_garbage_query_with_no_filters_returns_empty(self, s):
        """Random gibberish with no other filters should NOT return all pros via rating boost."""
        r = s.get(SEARCH, params={"q": "zzzqqxywvnonsensekeyword"})
        assert r.status_code == 200
        data = r.json()
        assert data == [], f"expected empty result, got {len(data)}"


# ---------- /api/match regression ----------
class TestMatchHybridRegression:
    def test_match_returns_hybrid_fields(self, s, client_token):
        headers = {"Authorization": f"Bearer {client_token}"}
        r = s.post(f"{BASE_URL}/api/match",
                   headers=headers,
                   json={"description": "I need a plumber to fix a leaky tap in my kitchen",
                         "location": "Nairobi"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("hybrid") is True
        assert "matches" in body and isinstance(body["matches"], list)
        if body["matches"]:
            m = body["matches"][0]
            assert "match_score" in m
            assert "match_reason" in m
            assert "score_breakdown" in m
            assert isinstance(m["match_score"], (int, float))
            assert 0 <= m["match_score"] <= 100
        assert body.get("scoring", {}).get("algorithm") == "hybrid_bm25_bayesian_ai"


# ---------- General regression ----------
class TestRegression:
    def test_login_admin(self, s):
        r = s.post(f"{BASE_URL}/api/auth/login",
                   json={"email": "admin@kazilinks.com", "password": "admin123"})
        assert r.status_code == 200
        body = r.json()
        assert body.get("token") or body.get("access_token")

    def test_get_professional_detail(self, s):
        # Pick first pro from search
        all_pros = s.get(SEARCH).json()
        assert len(all_pros) > 0
        pid = all_pros[0]["user_id"]
        r = s.get(f"{BASE_URL}/api/professionals/{pid}")
        assert r.status_code == 200
        body = r.json()
        assert body["user_id"] == pid
        assert "user" in body
        assert "reviews" in body

    def test_jobs_list(self, s, client_token):
        r = s.get(f"{BASE_URL}/api/jobs",
                  headers={"Authorization": f"Bearer {client_token}"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_wallet_balance(self, s, client_token):
        r = s.get(f"{BASE_URL}/api/wallet/balance",
                  headers={"Authorization": f"Bearer {client_token}"})
        assert r.status_code == 200
        assert "balance" in r.json()

    def test_conversations_list(self, s, client_token):
        r = s.get(f"{BASE_URL}/api/conversations",
                  headers={"Authorization": f"Bearer {client_token}"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)
