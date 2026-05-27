"""Backend tests for KYC ID photo upload/verification and Push subscription.

Covers:
- /api/kyc/upload-id (front+back, validation: file type/size/side)
- /api/kyc/status
- /api/files/kyc/{path} access control (owner / admin / other / no-auth)
- /api/admin/kyc/pending and /api/admin/kyc/{user_id} (admin-only)
- /api/admin/kyc/{user_id}/verify (admin-only, requires both sides)
- Public privacy: /api/professionals/{id} must NOT leak KYC private fields
- Regression: login, search, wallet, jobs, conversations endpoints
- /api/notifications/subscribe stub fallback
"""
import io
import os
import uuid
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or "https://hire-skilled-pros.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@kazilinks.com", "password": "admin123"}
PRO = {"email": "jamesomolo@gmail.com", "password": "password"}
CLIENT = {"email": "client@test.com", "password": "password"}
BACKUP_PRO = {"email": "pro@test.com", "password": "password"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"login failed for {creds['email']}: {r.status_code} {r.text}"
    data = r.json()
    return data["access_token"], data.get("user", {})


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def _png_bytes():
    # 1x1 transparent PNG
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xcf"
        b"\xc0\xf0\x1f\x00\x05\x00\x01\xfe\xa2\xf8M\x9c\x00\x00\x00\x00IEND\xaeB`\x82"
    )


# ----------------- Fixtures -----------------

@pytest.fixture(scope="module")
def admin_token():
    tok, _ = _login(ADMIN)
    return tok


@pytest.fixture(scope="module")
def pro_token_and_id():
    tok, u = _login(PRO)
    return tok, u.get("id")


@pytest.fixture(scope="module")
def client_token_and_id():
    tok, u = _login(CLIENT)
    return tok, u.get("id")


@pytest.fixture(scope="module")
def backup_pro_token_and_id():
    tok, u = _login(BACKUP_PRO)
    return tok, u.get("id")


# ----------------- Auth / login -----------------

def test_login_admin_ok():
    tok, u = _login(ADMIN)
    assert tok
    assert u.get("role") == "admin"


def test_login_pro_ok():
    tok, u = _login(PRO)
    assert tok
    assert u.get("role") in ("professional", "client", "admin")  # exists


# ----------------- KYC Upload validation -----------------

def test_upload_id_rejects_invalid_side(pro_token_and_id):
    tok, _ = pro_token_and_id
    files = {"file": ("test.png", _png_bytes(), "image/png")}
    data = {"side": "middle"}
    r = requests.post(f"{API}/kyc/upload-id", headers=_h(tok), data=data, files=files, timeout=60)
    assert r.status_code == 400
    assert "front" in r.text or "side" in r.text.lower()


def test_upload_id_rejects_pdf(pro_token_and_id):
    tok, _ = pro_token_and_id
    files = {"file": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf")}
    data = {"side": "front"}
    r = requests.post(f"{API}/kyc/upload-id", headers=_h(tok), data=data, files=files, timeout=60)
    assert r.status_code == 400, r.text


def test_upload_id_rejects_txt(pro_token_and_id):
    tok, _ = pro_token_and_id
    files = {"file": ("notes.txt", b"hello world", "text/plain")}
    data = {"side": "front"}
    r = requests.post(f"{API}/kyc/upload-id", headers=_h(tok), data=data, files=files, timeout=60)
    assert r.status_code == 400


def test_upload_id_rejects_too_large(pro_token_and_id):
    tok, _ = pro_token_and_id
    big = b"\x89PNG\r\n\x1a\n" + b"0" * (8 * 1024 * 1024 + 100)
    files = {"file": ("big.png", big, "image/png")}
    data = {"side": "front"}
    r = requests.post(f"{API}/kyc/upload-id", headers=_h(tok), data=data, files=files, timeout=120)
    assert r.status_code == 400, r.text


def test_upload_id_requires_auth():
    files = {"file": ("test.png", _png_bytes(), "image/png")}
    data = {"side": "front"}
    r = requests.post(f"{API}/kyc/upload-id", data=data, files=files, timeout=30)
    assert r.status_code in (401, 403)


# ----------------- KYC Upload happy paths -----------------

@pytest.fixture(scope="module")
def uploaded_kyc(backup_pro_token_and_id):
    """Upload both front + back for backup pro so we can test access control + admin verify
    without disturbing the already-verified jamesomolo account."""
    tok, uid = backup_pro_token_and_id
    files_front = {"file": ("front.png", _png_bytes(), "image/png")}
    r1 = requests.post(f"{API}/kyc/upload-id", headers=_h(tok), data={"side": "front"}, files=files_front, timeout=60)
    assert r1.status_code == 200, r1.text
    front_path = r1.json()["path"]

    files_back = {"file": ("back.png", _png_bytes(), "image/png")}
    r2 = requests.post(f"{API}/kyc/upload-id", headers=_h(tok), data={"side": "back"}, files=files_back, timeout=60)
    assert r2.status_code == 200, r2.text
    back_path = r2.json()["path"]

    return {"user_id": uid, "token": tok, "front_path": front_path, "back_path": back_path}


def test_uploaded_kyc_status(uploaded_kyc):
    tok = uploaded_kyc["token"]
    r = requests.get(f"{API}/kyc/status", headers=_h(tok), timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["id_front_uploaded"] is True
    assert d["id_back_uploaded"] is True
    assert d["id_front_url"] and d["id_front_url"].startswith("/api/files/kyc/")
    assert d["id_back_url"] and d["id_back_url"].startswith("/api/files/kyc/")
    assert d["id_verification_status"] == "pending"
    assert d["id_verified"] is False


# ----------------- File access control -----------------

def test_file_access_owner(uploaded_kyc):
    tok = uploaded_kyc["token"]
    r = requests.get(f"{API}/files/kyc/{uploaded_kyc['front_path']}", headers=_h(tok), timeout=30)
    assert r.status_code == 200
    assert r.content[:4] == b"\x89PNG"


def test_file_access_admin(uploaded_kyc, admin_token):
    r = requests.get(f"{API}/files/kyc/{uploaded_kyc['front_path']}", headers=_h(admin_token), timeout=30)
    assert r.status_code == 200


def test_file_access_other_user_forbidden(uploaded_kyc, client_token_and_id):
    other_tok, _ = client_token_and_id
    r = requests.get(f"{API}/files/kyc/{uploaded_kyc['front_path']}", headers=_h(other_tok), timeout=30)
    assert r.status_code == 403


def test_file_access_no_auth_forbidden(uploaded_kyc):
    r = requests.get(f"{API}/files/kyc/{uploaded_kyc['front_path']}", timeout=30)
    assert r.status_code in (401, 403)


# ----------------- Admin KYC -----------------

def test_admin_list_pending_kyc(admin_token, uploaded_kyc):
    r = requests.get(f"{API}/admin/kyc/pending", headers=_h(admin_token), timeout=30)
    assert r.status_code == 200
    users = r.json()
    assert isinstance(users, list)
    target = next((u for u in users if u.get("id") == uploaded_kyc["user_id"]), None)
    assert target is not None, "Uploaded user should appear in pending KYC list"
    # never leak password_hash
    if target:
        assert "password_hash" not in target


def test_admin_list_pending_kyc_forbidden_for_non_admin(client_token_and_id):
    tok, _ = client_token_and_id
    r = requests.get(f"{API}/admin/kyc/pending", headers=_h(tok), timeout=30)
    assert r.status_code == 403


def test_admin_get_user_kyc_detail(admin_token, uploaded_kyc):
    r = requests.get(f"{API}/admin/kyc/{uploaded_kyc['user_id']}", headers=_h(admin_token), timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["id_front_url"] is not None
    assert d["id_back_url"] is not None
    assert d["user"]["id"] == uploaded_kyc["user_id"]


def test_admin_get_user_kyc_forbidden_for_non_admin(uploaded_kyc, client_token_and_id):
    tok, _ = client_token_and_id
    r = requests.get(f"{API}/admin/kyc/{uploaded_kyc['user_id']}", headers=_h(tok), timeout=30)
    assert r.status_code == 403


def test_admin_verify_rejects_without_both_sides(admin_token, client_token_and_id):
    """A user who has uploaded nothing -> verify should 400."""
    # Use the client which we assume has no KYC uploads
    _, cid = client_token_and_id
    r = requests.post(
        f"{API}/admin/kyc/{cid}/verify",
        headers=_h(admin_token),
        json={"approved": True, "notes": "test"},
        timeout=30,
    )
    # If client has no uploads we expect 400; if by chance they've uploaded, accept 200
    assert r.status_code in (400,), f"Expected 400 (missing photos) got {r.status_code} {r.text}"


def test_admin_verify_approve_then_reject_flow(admin_token, uploaded_kyc):
    uid = uploaded_kyc["user_id"]
    # Approve
    r1 = requests.post(
        f"{API}/admin/kyc/{uid}/verify",
        headers=_h(admin_token),
        json={"approved": True, "notes": "TEST approved by pytest"},
        timeout=30,
    )
    assert r1.status_code == 200, r1.text
    assert r1.json()["id_verified"] is True
    assert r1.json()["status"] == "verified"

    # Verify state in user status
    r_status = requests.get(f"{API}/kyc/status", headers=_h(uploaded_kyc["token"]), timeout=30)
    assert r_status.status_code == 200
    assert r_status.json()["id_verified"] is True

    # Reject
    r2 = requests.post(
        f"{API}/admin/kyc/{uid}/verify",
        headers=_h(admin_token),
        json={"approved": False, "notes": "TEST rejected by pytest"},
        timeout=30,
    )
    assert r2.status_code == 200
    assert r2.json()["id_verified"] is False
    assert r2.json()["status"] == "rejected"


def test_admin_verify_forbidden_for_non_admin(uploaded_kyc, client_token_and_id):
    tok, _ = client_token_and_id
    r = requests.post(
        f"{API}/admin/kyc/{uploaded_kyc['user_id']}/verify",
        headers=_h(tok),
        json={"approved": True},
        timeout=30,
    )
    assert r.status_code == 403


# ----------------- Public privacy: NO LEAK -----------------

def test_public_professional_does_not_leak_kyc_fields():
    """GET /api/professionals/{id} must expose only id_verified boolean, NOT the
    path/notes/verifier/timestamp fields."""
    r = requests.get(f"{API}/professionals/search", timeout=30)
    assert r.status_code == 200
    pros = r.json()
    if isinstance(pros, dict):
        pros = pros.get("results") or pros.get("professionals") or []
    assert isinstance(pros, list) and len(pros) > 0, "Search returned no professionals"
    target = pros[0]
    # /api/professionals/{id} expects user_id, not profile.id
    pro_id = target.get("user_id") or (target.get("user") or {}).get("id") or target.get("id")
    r2 = requests.get(f"{API}/professionals/{pro_id}", timeout=30)
    assert r2.status_code == 200, r2.text
    data = r2.json()
    user = data.get("user") or {}
    leaked = []
    for k in (
        "id_front_path", "id_back_path",
        "id_verification_notes", "id_verified_by",
        "id_verified_at", "id_uploaded_at",
        "id_verification_status",
        "phone",
        "password_hash",
    ):
        if k in user:
            leaked.append(k)
    assert not leaked, f"Public professional endpoint LEAKED private fields: {leaked}"
    # id_verified boolean trust signal IS allowed (may be true/false/missing)


# ----------------- Regression -----------------

def test_regression_professionals_search():
    r = requests.get(f"{API}/professionals/search", timeout=30)
    assert r.status_code == 200


def test_regression_wallet_balance(client_token_and_id):
    tok, _ = client_token_and_id
    r = requests.get(f"{API}/wallet/balance", headers=_h(tok), timeout=30)
    assert r.status_code == 200
    assert "balance" in r.json()


def test_regression_jobs_available(backup_pro_token_and_id):
    tok, _ = backup_pro_token_and_id
    r = requests.get(f"{API}/jobs/available", headers=_h(tok), timeout=30)
    # may be 200 or 403 if pro doesn't have profile; accept 200/403
    assert r.status_code in (200, 403), r.text


def test_regression_conversations_list(client_token_and_id):
    tok, _ = client_token_and_id
    r = requests.get(f"{API}/conversations", headers=_h(tok), timeout=30)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ----------------- Notifications subscribe -----------------

def test_notifications_subscribe_stub(client_token_and_id):
    tok, uid = client_token_and_id
    payload = {
        "endpoint": f"local-{uid}",
        "keys": {"p256dh": "stub", "auth": "stub"},
    }
    r = requests.post(f"{API}/notifications/subscribe", headers=_h(tok), json=payload, timeout=30)
    assert r.status_code in (200, 201), r.text
