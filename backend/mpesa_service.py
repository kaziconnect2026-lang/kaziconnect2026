"""
M-Pesa Daraja API service module.
Handles OAuth token generation, STK Push initiation, and callback parsing.
"""
import os
import base64
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

SANDBOX_BASE = "https://sandbox.safaricom.co.ke"
PRODUCTION_BASE = "https://api.safaricom.co.ke"

# Cached OAuth token to avoid regenerating on each call (token TTL ~3600s)
_token_cache = {"access_token": None, "expires_at": None}


def _base_url() -> str:
    env = os.environ.get("MPESA_ENVIRONMENT", "sandbox").lower()
    return PRODUCTION_BASE if env == "production" else SANDBOX_BASE


def normalize_phone(phone: str) -> str:
    """Normalize Kenyan phone number to 2547XXXXXXXX format expected by Safaricom."""
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("254"):
        return digits
    if digits.startswith("0") and len(digits) == 10:
        return "254" + digits[1:]
    if len(digits) == 9 and digits.startswith("7"):
        return "254" + digits
    return digits


async def get_access_token() -> str:
    """Generate / fetch cached OAuth access token from Safaricom Daraja."""
    now = datetime.now(timezone.utc)
    if (
        _token_cache["access_token"]
        and _token_cache["expires_at"]
        and _token_cache["expires_at"] > now
    ):
        return _token_cache["access_token"]

    consumer_key = os.environ["MPESA_CONSUMER_KEY"]
    consumer_secret = os.environ["MPESA_CONSUMER_SECRET"]
    auth = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
    url = f"{_base_url()}/oauth/v1/generate?grant_type=client_credentials"

    async with httpx.AsyncClient(timeout=20.0) as http:
        resp = await http.get(url, headers={"Authorization": f"Basic {auth}"})
        resp.raise_for_status()
        data = resp.json()

    token = data.get("access_token")
    expires_in = int(data.get("expires_in", 3599))
    _token_cache["access_token"] = token
    # Refresh 60s before expiry
    _token_cache["expires_at"] = now + timedelta(seconds=max(60, expires_in - 60))
    return token


def _generate_password(timestamp: str) -> str:
    shortcode = os.environ["MPESA_SHORTCODE"]
    passkey = os.environ["MPESA_PASSKEY"]
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode()).decode()


def _callback_url() -> str:
    base = os.environ["MPESA_CALLBACK_BASE_URL"].rstrip("/")
    secret = os.environ["MPESA_CALLBACK_SECRET"]
    return f"{base}/api/mpesa/callback/{secret}"


async def stk_push(
    phone_number: str,
    amount: float,
    account_reference: str,
    transaction_desc: str = "Wallet Deposit",
) -> dict:
    """
    Initiate STK Push (Lipa Na M-Pesa Online).
    Returns dict with MerchantRequestID, CheckoutRequestID, ResponseCode, etc.
    """
    token = await get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = _generate_password(timestamp)
    shortcode = os.environ["MPESA_SHORTCODE"]
    phone = normalize_phone(phone_number)

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(round(amount)),
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": _callback_url(),
        "AccountReference": account_reference[:12] if account_reference else "KaziLinks",
        "TransactionDesc": (transaction_desc or "Wallet Deposit")[:13],
    }

    url = f"{_base_url()}/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30.0) as http:
        resp = await http.post(url, json=payload, headers=headers)

    try:
        body = resp.json()
    except Exception:
        body = {"raw": resp.text}

    if resp.status_code != 200:
        logger.error("M-Pesa STK push failed: %s %s", resp.status_code, body)
        raise RuntimeError(
            body.get("errorMessage")
            or body.get("ResponseDescription")
            or f"M-Pesa STK Push failed (status {resp.status_code})"
        )

    if body.get("ResponseCode") != "0":
        logger.error("M-Pesa STK push non-zero response: %s", body)
        raise RuntimeError(
            body.get("ResponseDescription") or "STK Push request rejected by Safaricom"
        )

    return body


def parse_callback(payload: dict) -> dict:
    """
    Parse Safaricom STK Push callback payload into a flat dict.
    """
    stk = (payload or {}).get("Body", {}).get("stkCallback", {}) or {}
    result = {
        "merchant_request_id": stk.get("MerchantRequestID"),
        "checkout_request_id": stk.get("CheckoutRequestID"),
        "result_code": stk.get("ResultCode"),
        "result_desc": stk.get("ResultDesc"),
        "amount": None,
        "mpesa_receipt": None,
        "transaction_date": None,
        "phone_number": None,
    }
    items = (stk.get("CallbackMetadata") or {}).get("Item") or []
    for item in items:
        name = item.get("Name")
        value = item.get("Value")
        if name == "Amount":
            result["amount"] = float(value) if value is not None else None
        elif name == "MpesaReceiptNumber":
            result["mpesa_receipt"] = value
        elif name == "TransactionDate":
            result["transaction_date"] = str(value) if value is not None else None
        elif name == "PhoneNumber":
            result["phone_number"] = str(value) if value is not None else None
    return result


async def query_stk_status(checkout_request_id: str) -> dict:
    """Query the status of a previously-initiated STK push (used as fallback if callback delayed)."""
    token = await get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = _generate_password(timestamp)
    payload = {
        "BusinessShortCode": os.environ["MPESA_SHORTCODE"],
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id,
    }
    url = f"{_base_url()}/mpesa/stkpushquery/v1/query"
    async with httpx.AsyncClient(timeout=20.0) as http:
        resp = await http.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text, "status": resp.status_code}
