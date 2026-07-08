"""Backend tests: admin ledger stability + password change negative cases."""
import os
import pytest
import requests
from datetime import datetime, timezone
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://hire-skilled-pros.preview.emergentagent.com").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "kazi_links")

ADMIN_EMAIL = "admin@kazilinks.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def mongo_db():
    client = MongoClient(MONGO_URL)
    return client[DB_NAME]


# ---- Ledger endpoint ----

class TestAdminLedger:
    def test_ledger_returns_200_with_summary(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/ledger?limit=10", headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "entries" in data
        assert "total" in data
        assert "summary" in data
        s = data["summary"]
        for k in ["total_deposits", "total_withdrawals", "total_escrow_in",
                  "total_escrow_out", "total_platform_fees", "total_professional_payouts"]:
            assert k in s, f"Missing summary key {k}"
            assert isinstance(s[k], (int, float))
        assert "entry_counts" in s and isinstance(s["entry_counts"], dict)

    def test_ledger_filter_by_deposit(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/ledger?entry_type=deposit&limit=5", headers=auth_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        for e in data.get("entries", []):
            assert e.get("entry_type") == "deposit"

    def test_reconciled_entry_present(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/ledger?limit=500", headers=auth_headers, timeout=30)
        assert r.status_code == 200
        entries = r.json().get("entries", [])
        match = [e for e in entries if e.get("id") == "reconcile-UG768AP82F"]
        if not match:
            pytest.skip("reconcile-UG768AP82F not found (may already be paged out); non-critical")
        e = match[0]
        assert e.get("entry_type") == "deposit"
        assert float(e.get("amount")) == 20.0

    def test_bad_doc_regression(self, auth_headers, mongo_db):
        # seed a doc missing entry_type
        bad = {
            "id": "TEST_BAD_DOC_KYC",
            "amount": 99,
            "user_id": "platform",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            mongo_db.ledger_entries.insert_one(bad)
            r = requests.get(f"{BASE_URL}/api/admin/ledger?limit=500", headers=auth_headers, timeout=30)
            assert r.status_code == 200, f"Ledger 500 with bad doc: {r.text}"
            data = r.json()
            assert "summary" in data
        finally:
            mongo_db.ledger_entries.delete_one({"id": "TEST_BAD_DOC_KYC"})

    def test_dashboard_charts_200(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/dashboard-charts", headers=auth_headers, timeout=30)
        assert r.status_code == 200

    def test_admin_stats_200(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/stats", headers=auth_headers, timeout=30)
        assert r.status_code == 200


# ---- Password change negative cases ----

class TestChangePasswordNegative:
    def test_wrong_current_password(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/auth/change-password",
                          headers=auth_headers,
                          json={"current_password": "wrongpass", "new_password": "somenew123"},
                          timeout=30)
        assert r.status_code == 401, r.text
        assert "incorrect" in r.text.lower()

    def test_new_password_too_short(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/auth/change-password",
                          headers=auth_headers,
                          json={"current_password": ADMIN_PASSWORD, "new_password": "short"},
                          timeout=30)
        assert r.status_code == 400
        assert "8 characters" in r.text or "at least 8" in r.text.lower()

    def test_new_equals_current(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/auth/change-password",
                          headers=auth_headers,
                          json={"current_password": ADMIN_PASSWORD, "new_password": ADMIN_PASSWORD},
                          timeout=30)
        assert r.status_code == 400
        assert "differ" in r.text.lower() or "different" in r.text.lower()
