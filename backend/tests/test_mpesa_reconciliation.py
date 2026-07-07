"""Tests for M-Pesa deposit callback reconciliation bug fix.

Covers:
- Success callback reconciles a prematurely-failed wallet_transaction.
- Idempotency (double-callback does not double-credit).
- Cancel callback (1032) does not overwrite a completed txn.
- /wallet/deposit/status does not prematurely flip <30s pending txn.
- Happy-path deposit callback.
- Failure-path cancel callback.
- Admin financials render + include reconciled deposit.
- Historical stuck KSh 20 for user 06ff4307-... is reconciled.
"""
import os
import uuid
import asyncio
from datetime import datetime, timezone, timedelta

import pytest
import requests
from motor.motor_asyncio import AsyncIOMotorClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://hire-skilled-pros.preview.emergentagent.com").rstrip("/")
CB_SECRET = "kl_mpesa_cb_d8f3a1c97e2b4f6a"
CB_URL = f"{BASE_URL}/api/mpesa/callback/{CB_SECRET}"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "kazi_links"

# ---------- fixtures ----------
@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
def db():
    return AsyncIOMotorClient(MONGO_URL)[DB_NAME]

@pytest.fixture(scope="module")
def test_client_id(event_loop, db):
    """A real client user id to attach TEST_ wallet_transactions to."""
    async def _get():
        u = await db.users.find_one({"role": "client"}, {"_id": 0, "id": 1})
        return u["id"] if u else None
    uid = event_loop.run_until_complete(_get())
    assert uid, "No client user in db to seed test txns against"
    return uid

@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": "admin@kazilinks.com", "password": "admin123"},
                      timeout=15)
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text}")
    return r.json()["access_token"]

# ---------- helpers ----------
def cb_success(checkout_id, amount=50, receipt="TESTRCPT01"):
    return {
        "Body": {"stkCallback": {
            "MerchantRequestID": "test-mr-1",
            "CheckoutRequestID": checkout_id,
            "ResultCode": 0,
            "ResultDesc": "Success",
            "CallbackMetadata": {"Item": [
                {"Name": "Amount", "Value": amount},
                {"Name": "MpesaReceiptNumber", "Value": receipt},
                {"Name": "TransactionDate", "Value": 20260707100000},
                {"Name": "PhoneNumber", "Value": 254712345678},
            ]},
        }}
    }

def cb_cancel(checkout_id):
    return {"Body": {"stkCallback": {
        "MerchantRequestID": "test-mr-c",
        "CheckoutRequestID": checkout_id,
        "ResultCode": 1032,
        "ResultDesc": "Request cancelled by user",
    }}}

async def _seed_txn(db, user_id, checkout_id, status="pending", amount=50.0,
                    mpesa_receipt=None, failure_code=None, failure_reason=None):
    doc = {
        "id": str(uuid.uuid4()),
        "transaction_id": f"TEST_{uuid.uuid4().hex[:8]}",
        "user_id": user_id,
        "type": "deposit",
        "amount": amount,
        "status": status,
        "reference": "TEST_DEP",
        "phone_number": "254712345678",
        "checkout_request_id": checkout_id,
        "merchant_request_id": "test-mr",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if mpesa_receipt:
        doc["mpesa_receipt"] = mpesa_receipt
        doc["status"] = "completed"
    if failure_code:
        doc["failure_code"] = failure_code
    if failure_reason:
        doc["failure_reason"] = failure_reason
    await db.wallet_transactions.insert_one(doc)
    return doc

async def _get_balance(db, user_id):
    u = await db.users.find_one({"id": user_id}, {"_id": 0, "wallet_balance": 1})
    return float(u.get("wallet_balance") or 0)

async def _cleanup(db, checkout_ids):
    await db.wallet_transactions.delete_many({"checkout_request_id": {"$in": checkout_ids}})
    await db.ledger.delete_many({"metadata.checkout_request_id": {"$in": checkout_ids}})


# ---------- tests ----------

def test_success_callback_reconciles_prematurely_failed(event_loop, db, test_client_id):
    """A wallet_transactions doc marked 'failed' by the STK Query poll must be RECONCILED
    to 'completed' when the real success callback lands, and wallet must be credited."""
    checkout_id = f"TEST_CO_{uuid.uuid4().hex[:12]}"
    receipt = f"TEST{uuid.uuid4().hex[:6].upper()}"
    amount = 50.0
    async def _run():
        bal_before = await _get_balance(db, test_client_id)
        await _seed_txn(db, test_client_id, checkout_id, status="failed",
                        amount=amount, failure_code="1032",
                        failure_reason="test premature fail")
        r = requests.post(CB_URL, json=cb_success(checkout_id, amount=amount, receipt=receipt), timeout=15)
        assert r.status_code == 200
        assert r.json() == {"ResultCode": 0, "ResultDesc": "Accepted"}
        # verify txn reconciled
        t = await db.wallet_transactions.find_one({"checkout_request_id": checkout_id}, {"_id": 0})
        assert t["status"] == "completed", f"txn status: {t.get('status')}"
        assert t["mpesa_receipt"] == receipt
        assert "failure_code" not in t
        assert "failure_reason" not in t
        # wallet credited
        bal_after = await _get_balance(db, test_client_id)
        assert bal_after == pytest.approx(bal_before + amount), f"before={bal_before}, after={bal_after}"
        # ledger entry with reconciled_from_failed=true
        led = await db.ledger.find_one({"metadata.checkout_request_id": checkout_id}, {"_id": 0})
        assert led is not None
        assert led["reference_type"] == "wallet_deposit"
        assert led["metadata"].get("reconciled_from_failed") is True
        assert led["amount"] == amount
        # cleanup
        await _cleanup(db, [checkout_id])
        # revert balance
        await db.users.update_one({"id": test_client_id}, {"$inc": {"wallet_balance": -amount}})
    event_loop.run_until_complete(_run())


def test_success_callback_idempotency(event_loop, db, test_client_id):
    """Second identical success callback must NOT double-credit the wallet."""
    checkout_id = f"TEST_CO_{uuid.uuid4().hex[:12]}"
    receipt = f"TEST{uuid.uuid4().hex[:6].upper()}"
    amount = 30.0
    async def _run():
        bal_before = await _get_balance(db, test_client_id)
        await _seed_txn(db, test_client_id, checkout_id, status="pending", amount=amount)
        # first callback
        r1 = requests.post(CB_URL, json=cb_success(checkout_id, amount=amount, receipt=receipt), timeout=15)
        assert r1.status_code == 200
        bal_mid = await _get_balance(db, test_client_id)
        assert bal_mid == pytest.approx(bal_before + amount)
        # second identical callback
        r2 = requests.post(CB_URL, json=cb_success(checkout_id, amount=amount, receipt=receipt), timeout=15)
        assert r2.status_code == 200
        bal_after = await _get_balance(db, test_client_id)
        assert bal_after == pytest.approx(bal_mid), "double-credit occurred!"
        # cleanup
        await _cleanup(db, [checkout_id])
        await db.users.update_one({"id": test_client_id}, {"$inc": {"wallet_balance": -amount}})
    event_loop.run_until_complete(_run())


def test_cancel_callback_does_not_overwrite_completed(event_loop, db, test_client_id):
    """A ResultCode=1032 cancel callback for a txn that ALREADY has mpesa_receipt
    must NOT change its status back to failed nor debit wallet."""
    checkout_id = f"TEST_CO_{uuid.uuid4().hex[:12]}"
    receipt = f"TESTLOCK{uuid.uuid4().hex[:4].upper()}"
    async def _run():
        bal_before = await _get_balance(db, test_client_id)
        await _seed_txn(db, test_client_id, checkout_id, status="completed",
                        amount=40.0, mpesa_receipt=receipt)
        r = requests.post(CB_URL, json=cb_cancel(checkout_id), timeout=15)
        assert r.status_code == 200
        t = await db.wallet_transactions.find_one({"checkout_request_id": checkout_id}, {"_id": 0})
        assert t["status"] == "completed"
        assert t["mpesa_receipt"] == receipt
        assert "failure_code" not in t
        bal_after = await _get_balance(db, test_client_id)
        assert bal_after == pytest.approx(bal_before), "wallet was debited unexpectedly"
        await _cleanup(db, [checkout_id])
    event_loop.run_until_complete(_run())


def test_happy_path_success_callback(event_loop, db, test_client_id):
    """Normal happy path: pending -> completed via success callback, wallet credited,
    ledger entry created with reconciled_from_failed False/missing."""
    checkout_id = f"TEST_CO_{uuid.uuid4().hex[:12]}"
    receipt = f"TESTHP{uuid.uuid4().hex[:6].upper()}"
    amount = 25.0
    async def _run():
        bal_before = await _get_balance(db, test_client_id)
        await _seed_txn(db, test_client_id, checkout_id, status="pending", amount=amount)
        r = requests.post(CB_URL, json=cb_success(checkout_id, amount=amount, receipt=receipt), timeout=15)
        assert r.status_code == 200
        t = await db.wallet_transactions.find_one({"checkout_request_id": checkout_id}, {"_id": 0})
        assert t["status"] == "completed"
        assert t["mpesa_receipt"] == receipt
        bal_after = await _get_balance(db, test_client_id)
        assert bal_after == pytest.approx(bal_before + amount)
        led = await db.ledger.find_one({"metadata.checkout_request_id": checkout_id}, {"_id": 0})
        assert led is not None
        assert led["reference_type"] == "wallet_deposit"
        assert not led["metadata"].get("reconciled_from_failed", False)
        await _cleanup(db, [checkout_id])
        await db.users.update_one({"id": test_client_id}, {"$inc": {"wallet_balance": -amount}})
    event_loop.run_until_complete(_run())


def test_failure_path_cancel_callback(event_loop, db, test_client_id):
    """Normal failure: pending -> failed via 1032 callback, wallet unchanged."""
    checkout_id = f"TEST_CO_{uuid.uuid4().hex[:12]}"
    amount = 25.0
    async def _run():
        bal_before = await _get_balance(db, test_client_id)
        await _seed_txn(db, test_client_id, checkout_id, status="pending", amount=amount)
        r = requests.post(CB_URL, json=cb_cancel(checkout_id), timeout=15)
        assert r.status_code == 200
        t = await db.wallet_transactions.find_one({"checkout_request_id": checkout_id}, {"_id": 0})
        assert t["status"] == "failed"
        assert t["failure_code"] == "1032"
        assert t.get("failure_reason")
        assert "mpesa_receipt" not in t or not t.get("mpesa_receipt")
        bal_after = await _get_balance(db, test_client_id)
        assert bal_after == pytest.approx(bal_before)
        await _cleanup(db, [checkout_id])
    event_loop.run_until_complete(_run())


def test_deposit_status_young_pending_does_not_flip(event_loop, db, test_client_id):
    """A pending wallet_transactions doc younger than 30s must NOT be flipped to failed
    by the /wallet/deposit/status endpoint. We need to hit the endpoint as the txn owner,
    so we need a token for test_client_id — we generate one by calling the login endpoint
    is heavy; instead, we assert only via DB: seed a young pending txn, then hit endpoint
    with a fresh JWT for that user by minting via the internal seed user's password.

    Since we cannot know the user's password, we simply verify the endpoint code path
    guard by checking status does not flip when the txn is <30s old, by directly
    calling with the txn's owner. If no known-password user is available, we skip.
    """
    # Mint JWT directly using the backend secret (same lib+algorithm as server.py)
    import jwt as _jwt
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td
    uid = test_client_id
    payload = {"sub": uid, "role": "client",
               "exp": _dt.now(_tz.utc) + _td(hours=1)}
    token = _jwt.encode(payload, "kazi-links-jwt-secret-2024-secure", algorithm="HS256")

    checkout_id = f"TEST_CO_{uuid.uuid4().hex[:12]}"
    async def _run():
        await _seed_txn(db, uid, checkout_id, status="pending", amount=10.0)
        r = requests.get(f"{BASE_URL}/api/wallet/deposit/status/{checkout_id}",
                         headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert r.status_code == 200
        # young (<30s) pending must stay pending regardless of anything
        t = await db.wallet_transactions.find_one({"checkout_request_id": checkout_id}, {"_id": 0})
        assert t["status"] == "pending", f"young txn was flipped to {t['status']}"
        await _cleanup(db, [checkout_id])
    event_loop.run_until_complete(_run())


def test_admin_stats_includes_reconciled_deposits(admin_token):
    """Admin financials endpoint must render and total_wallet_deposits must include
    the historical reconciled KSh 20."""
    r = requests.get(f"{BASE_URL}/api/admin/stats",
                     headers={"Authorization": f"Bearer {admin_token}"}, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    fin = data.get("financials") or data
    # total_wallet_deposits key can live at top-level or under financials
    total = fin.get("total_wallet_deposits") if isinstance(fin, dict) else None
    if total is None and "financials" in data:
        total = data["financials"].get("total_wallet_deposits")
    assert total is not None, f"total_wallet_deposits missing from admin stats: {data}"
    assert float(total) >= 20.0


def test_historical_stuck_txn_reconciled(event_loop, db):
    """The KSh 20 txn ws_CO_07072026083332628745576048 must be reconciled and the user's
    wallet must reflect the credit."""
    async def _run():
        t = await db.wallet_transactions.find_one(
            {"checkout_request_id": "ws_CO_07072026083332628745576048"}, {"_id": 0})
        assert t is not None, "historical stuck txn missing from db"
        assert t["status"] == "completed"
        assert t.get("mpesa_receipt") == "UG768AP82F"
        assert t.get("reconciled_manually") is True
        u = await db.users.find_one({"id": "06ff4307-b702-45db-a32f-d0dbae46dd57"},
                                    {"_id": 0, "wallet_balance": 1})
        assert u is not None
        assert float(u.get("wallet_balance") or 0) >= 20.0
    event_loop.run_until_complete(_run())
