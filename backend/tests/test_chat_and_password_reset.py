"""
Tests for chat/messaging system, admin moderation, forgot/reset password,
and regression on core endpoints.
"""
import io
import os
import re
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://hire-skilled-pros.preview.emergentagent.com").rstrip("/")

CLIENT_EMAIL = "client@test.com"
CLIENT_PWD = "password"
PRO_EMAIL = "pro@test.com"
PRO_PWD = "password"
ADMIN_EMAIL = "admin@kazilinks.com"
ADMIN_PWD = "admin123"


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    body = r.json()
    return body["access_token"] if "access_token" in body else body.get("token"), body.get("user")


@pytest.fixture(scope="module")
def client_auth():
    tok, user = _login(CLIENT_EMAIL, CLIENT_PWD)
    return {"token": tok, "user": user, "headers": {"Authorization": f"Bearer {tok}"}}


@pytest.fixture(scope="module")
def pro_auth():
    tok, user = _login(PRO_EMAIL, PRO_PWD)
    return {"token": tok, "user": user, "headers": {"Authorization": f"Bearer {tok}"}}


@pytest.fixture(scope="module")
def admin_auth():
    tok, user = _login(ADMIN_EMAIL, ADMIN_PWD)
    return {"token": tok, "user": user, "headers": {"Authorization": f"Bearer {tok}"}}


# ============ CHAT ============

class TestChatFlow:
    def test_start_conversation_client_to_pro(self, client_auth, pro_auth):
        r = requests.post(
            f"{BASE_URL}/api/conversations",
            json={"other_user_id": pro_auth["user"]["id"]},
            headers=client_auth["headers"], timeout=15
        )
        assert r.status_code == 200, r.text
        convo = r.json()
        assert convo["client_id"] == client_auth["user"]["id"]
        assert convo["professional_id"] == pro_auth["user"]["id"]
        assert "id" in convo
        pytest.conv_id = convo["id"]

    def test_start_conversation_idempotent(self, client_auth, pro_auth):
        r = requests.post(
            f"{BASE_URL}/api/conversations",
            json={"other_user_id": pro_auth["user"]["id"]},
            headers=client_auth["headers"], timeout=15
        )
        assert r.status_code == 200
        assert r.json()["id"] == pytest.conv_id

    def test_start_conversation_with_self_rejected(self, client_auth):
        r = requests.post(
            f"{BASE_URL}/api/conversations",
            json={"other_user_id": client_auth["user"]["id"]},
            headers=client_auth["headers"], timeout=15
        )
        assert r.status_code == 400

    def test_list_conversations_client(self, client_auth):
        r = requests.get(f"{BASE_URL}/api/conversations", headers=client_auth["headers"], timeout=15)
        assert r.status_code == 200
        convos = r.json()
        assert isinstance(convos, list)
        ids = [c["id"] for c in convos]
        assert pytest.conv_id in ids
        match = next(c for c in convos if c["id"] == pytest.conv_id)
        assert match.get("other_user") is not None
        assert "unread" in match

    def test_list_conversations_admin_blocked(self, admin_auth):
        r = requests.get(f"{BASE_URL}/api/conversations", headers=admin_auth["headers"], timeout=15)
        assert r.status_code == 400

    def test_get_conversation_as_participant(self, pro_auth):
        r = requests.get(f"{BASE_URL}/api/conversations/{pytest.conv_id}", headers=pro_auth["headers"], timeout=15)
        assert r.status_code == 200
        assert r.json()["id"] == pytest.conv_id

    def test_get_conversation_non_participant_forbidden(self):
        # Make a stray user
        stray = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_stray_{int(time.time())}@example.com",
            "password": "password",
            "name": "Stray User",
            "role": "client",
            "phone": "+254700000001",
        }, timeout=15)
        if stray.status_code not in (200, 201):
            pytest.skip(f"Could not create stray user: {stray.status_code} {stray.text}")
        body = stray.json()
        token = body.get("access_token") or body.get("token")
        r = requests.get(f"{BASE_URL}/api/conversations/{pytest.conv_id}",
                         headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert r.status_code == 403

    def test_send_message_client(self, client_auth):
        r = requests.post(
            f"{BASE_URL}/api/conversations/{pytest.conv_id}/messages",
            json={"content": "Hello pro, are you available?"},
            headers=client_auth["headers"], timeout=15
        )
        assert r.status_code == 200, r.text
        msg = r.json()
        assert msg["content"] == "Hello pro, are you available?"
        assert msg["sender_role"] == "client"

    def test_send_empty_message_rejected(self, client_auth):
        r = requests.post(
            f"{BASE_URL}/api/conversations/{pytest.conv_id}/messages",
            json={"content": "   "},
            headers=client_auth["headers"], timeout=15
        )
        assert r.status_code == 400

    def test_list_messages_clears_unread_for_pro(self, pro_auth):
        r = requests.get(
            f"{BASE_URL}/api/conversations/{pytest.conv_id}/messages",
            headers=pro_auth["headers"], timeout=15
        )
        assert r.status_code == 200
        msgs = r.json()
        assert len(msgs) >= 1

        # After listing, unread should be 0 for pro
        r2 = requests.get(f"{BASE_URL}/api/conversations", headers=pro_auth["headers"], timeout=15)
        assert r2.status_code == 200
        for c in r2.json():
            if c["id"] == pytest.conv_id:
                assert c.get("unread", 0) == 0

    def test_send_message_pro_reply(self, pro_auth):
        r = requests.post(
            f"{BASE_URL}/api/conversations/{pytest.conv_id}/messages",
            json={"content": "Yes, when do you need me?"},
            headers=pro_auth["headers"], timeout=15
        )
        assert r.status_code == 200
        assert r.json()["sender_role"] == "professional"

    def test_invalid_attachment_path_rejected(self, client_auth):
        r = requests.post(
            f"{BASE_URL}/api/conversations/{pytest.conv_id}/messages",
            json={"content": "Hi", "attachment_paths": ["kazi-links/chat/fake/notmine.jpg"]},
            headers=client_auth["headers"], timeout=15
        )
        assert r.status_code == 400


# ============ CHAT ATTACHMENTS ============

class TestChatAttachments:
    def test_upload_invalid_extension(self, client_auth):
        files = {"file": ("evil.exe", io.BytesIO(b"MZfake"), "application/octet-stream")}
        r = requests.post(f"{BASE_URL}/api/chat/attachments", files=files,
                          headers=client_auth["headers"], timeout=20)
        assert r.status_code == 400

    def test_upload_valid_image(self, client_auth):
        # tiny PNG header
        png = bytes.fromhex(
            "89504E470D0A1A0A0000000D49484452000000010000000108020000"
            "00907753DE0000000C49444154789C6360000000000200013F0DC8"
            "B40000000049454E44AE426082"
        )
        files = {"file": ("test.png", io.BytesIO(png), "image/png")}
        r = requests.post(f"{BASE_URL}/api/chat/attachments", files=files,
                          headers=client_auth["headers"], timeout=30)
        if r.status_code == 502:
            pytest.skip(f"Object storage unavailable: {r.text}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "path" in body and "content_type" in body
        pytest.attachment_path = body["path"]

    def test_send_message_with_valid_attachment(self, client_auth):
        if not hasattr(pytest, "attachment_path"):
            pytest.skip("Upload step skipped")
        r = requests.post(
            f"{BASE_URL}/api/conversations/{pytest.conv_id}/messages",
            json={"content": "See photo", "attachment_paths": [pytest.attachment_path]},
            headers=client_auth["headers"], timeout=15
        )
        assert r.status_code == 200, r.text
        assert len(r.json().get("attachments", [])) == 1


# ============ ADMIN MODERATION ============

class TestAdminModeration:
    def test_admin_can_list_all_conversations(self, admin_auth):
        r = requests.get(f"{BASE_URL}/api/admin/conversations", headers=admin_auth["headers"], timeout=15)
        assert r.status_code == 200
        convos = r.json()
        assert isinstance(convos, list)
        found = next((c for c in convos if c["id"] == pytest.conv_id), None)
        assert found is not None
        assert found.get("client") is not None
        assert found.get("professional") is not None
        assert "message_count" in found
        assert found["message_count"] >= 1

    def test_non_admin_cannot_access_admin_conversations(self, client_auth):
        r = requests.get(f"{BASE_URL}/api/admin/conversations", headers=client_auth["headers"], timeout=15)
        assert r.status_code == 403

    def test_admin_can_view_any_conversation_messages(self, admin_auth):
        r = requests.get(f"{BASE_URL}/api/conversations/{pytest.conv_id}/messages",
                         headers=admin_auth["headers"], timeout=15)
        assert r.status_code == 200
        assert len(r.json()) >= 1


# ============ FORGOT / RESET PASSWORD ============

class TestPasswordReset:
    def test_forgot_password_generic_response_unknown_email(self):
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                          json={"email": "nobody_unknown_xyz@example.com"}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        # Should not leak that the user doesn't exist
        assert "If an account exists" in body.get("message", "") or "reset" in body.get("message", "").lower()

    def test_forgot_password_real_email_generic_response_no_link_in_body(self):
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                          json={"email": CLIENT_EMAIL}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        # Reset link must NOT appear in API response
        assert "reset-password?token=" not in str(body)
        assert "token" not in body

    def test_forgot_password_logs_link_when_resend_missing(self):
        # Trigger and then read backend log to confirm the link is logged
        unique_email = CLIENT_EMAIL
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                          json={"email": unique_email}, timeout=15)
        assert r.status_code == 200
        time.sleep(1)
        # Read recent backend log
        try:
            with open("/var/log/supervisor/backend.err.log", "r") as f:
                # read last 20KB
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(0, size - 20000))
                tail = f.read()
        except Exception as e:
            pytest.skip(f"Cannot read backend log: {e}")

        # Look for reset link
        assert "reset-password?token=" in tail, "Reset link should appear in backend logs when RESEND_API_KEY missing"

    def test_reset_password_with_valid_token_flow(self):
        # Trigger reset
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                          json={"email": CLIENT_EMAIL}, timeout=15)
        assert r.status_code == 200
        time.sleep(1)
        with open("/var/log/supervisor/backend.err.log", "r") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 30000))
            tail = f.read()
        matches = re.findall(r"reset-password\?token=([\w\-\.]+)", tail)
        assert matches, "No reset token found in logs"
        token = matches[-1]

        # Reset password to same value
        r2 = requests.post(f"{BASE_URL}/api/auth/reset-password",
                           json={"token": token, "new_password": CLIENT_PWD}, timeout=15)
        assert r2.status_code == 200, r2.text

        # Verify can log back in
        r3 = requests.post(f"{BASE_URL}/api/auth/login",
                           json={"email": CLIENT_EMAIL, "password": CLIENT_PWD}, timeout=15)
        assert r3.status_code == 200

    def test_reset_password_invalid_token_rejected(self):
        r = requests.post(f"{BASE_URL}/api/auth/reset-password",
                          json={"token": "INVALID_TOKEN_XYZ", "new_password": "newpass123"}, timeout=15)
        assert r.status_code == 400


# ============ REGRESSION ============

class TestRegression:
    def test_login_admin(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": ADMIN_EMAIL, "password": ADMIN_PWD}, timeout=15)
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "admin"

    def test_professionals_list(self):
        r = requests.get(f"{BASE_URL}/api/professionals/search", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_jobs_list(self, client_auth):
        r = requests.get(f"{BASE_URL}/api/jobs", headers=client_auth["headers"], timeout=15)
        # Some apps require auth; accept 200
        assert r.status_code == 200

    def test_wallet_balance(self, client_auth):
        r = requests.get(f"{BASE_URL}/api/wallet/balance", headers=client_auth["headers"], timeout=15)
        assert r.status_code == 200
        assert "balance" in r.json()

    def test_admin_stats(self, admin_auth):
        r = requests.get(f"{BASE_URL}/api/admin/stats", headers=admin_auth["headers"], timeout=15)
        assert r.status_code == 200
