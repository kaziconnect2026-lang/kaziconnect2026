"""
Emergent Object Storage service module.
Handles chat attachment uploads and downloads.
"""
import os
import uuid
import logging
import requests

logger = logging.getLogger(__name__)

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "kazi-links"

# Module-level cached storage key (session-scoped per playbook)
_storage_key = None


MIME_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
    "pdf": "application/pdf",
}

ALLOWED_EXTS = {"jpg", "jpeg", "png", "webp", "gif", "pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def init_storage():
    """Initialize storage session. Call once at app startup; key is cached."""
    global _storage_key
    if _storage_key:
        return _storage_key

    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise RuntimeError("EMERGENT_LLM_KEY env var is required for object storage")

    resp = requests.post(
        f"{STORAGE_URL}/init",
        json={"emergent_key": emergent_key},
        timeout=30,
    )
    resp.raise_for_status()
    _storage_key = resp.json()["storage_key"]
    logger.info("Object storage initialized successfully")
    return _storage_key


def _ensure_key():
    """Re-initialize storage key if expired/missing."""
    global _storage_key
    if not _storage_key:
        init_storage()
    return _storage_key


def get_content_type(filename: str) -> str:
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    return MIME_TYPES.get(ext, "application/octet-stream")


def validate_upload(filename: str, size: int) -> str:
    """Returns lowercase extension or raises ValueError if invalid."""
    if not filename or "." not in filename:
        raise ValueError("Filename must include an extension")
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTS:
        raise ValueError(f"File type .{ext} is not supported. Allowed: jpg, png, webp, gif, pdf")
    if size > MAX_FILE_SIZE:
        raise ValueError(f"File too large ({size} bytes). Max is {MAX_FILE_SIZE} bytes (5 MB)")
    return ext


def build_chat_path(user_id: str, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"{APP_NAME}/chat/{user_id}/{uuid.uuid4()}.{ext}"


def put_object(path: str, data: bytes, content_type: str) -> dict:
    """Upload bytes to object storage. Returns {path, size, etag}."""
    key = _ensure_key()
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data,
        timeout=120,
    )
    if resp.status_code == 403:
        # Storage key may have expired; force re-init and retry once
        global _storage_key
        _storage_key = None
        key = _ensure_key()
        resp = requests.put(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key, "Content-Type": content_type},
            data=data,
            timeout=120,
        )
    resp.raise_for_status()
    return resp.json()


def get_object(path: str):
    """Download bytes. Returns (content_bytes, content_type)."""
    key = _ensure_key()
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key},
        timeout=60,
    )
    if resp.status_code == 403:
        global _storage_key
        _storage_key = None
        key = _ensure_key()
        resp = requests.get(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key},
            timeout=60,
        )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")
