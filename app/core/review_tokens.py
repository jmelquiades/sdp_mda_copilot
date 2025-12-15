"""Token helpers for experiencia review links."""

import base64
import hashlib
import hmac
import json
import time
from typing import Dict


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def generate_token(ticket_id: str, secret: str, ttl_hours: int) -> str:
    """Create a short-lived token signed with HMAC-SHA256."""
    if not secret:
        raise ValueError("secret_missing")
    now = int(time.time())
    payload = {
        "ticket_id": ticket_id,
        "iat": now,
        "exp": now + ttl_hours * 3600,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    return f"{_b64encode(payload_bytes)}.{_b64encode(sig)}"


def decode_token(token: str, secret: str) -> Dict[str, str]:
    """Validate token and return payload dict."""
    if not token or "." not in token or not secret:
        raise ValueError("invalid_token")
    payload_b64, sig_b64 = token.split(".", 1)
    try:
        payload_bytes = _b64decode(payload_b64)
        sig = _b64decode(sig_b64)
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError("invalid_token") from exc

    expected_sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected_sig):
        raise ValueError("invalid_token")

    try:
        payload = json.loads(payload_bytes)
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError("invalid_token") from exc

    now = int(time.time())
    exp = int(payload.get("exp", 0))
    if now > exp:
        raise ValueError("token_expired")
    return payload
