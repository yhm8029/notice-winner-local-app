from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any


def encode_signed_payload(payload: dict[str, Any], *, session_secret: Any, urlsafe_b64encode: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    encoded = urlsafe_b64encode(raw)
    signature = hmac.new(session_secret().encode("utf-8"), encoded.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def decode_signed_payload(value: str, *, session_secret: Any, urlsafe_b64decode: Any) -> dict[str, Any]:
    encoded, separator, signature = str(value or "").partition(".")
    if not encoded or not separator or not signature:
        raise ValueError("Invalid auth session payload")
    expected = hmac.new(session_secret().encode("utf-8"), encoded.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("Invalid auth session signature")
    try:
        raw = urlsafe_b64decode(encoded)
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid auth session body") from exc
    if not isinstance(payload, dict):
        raise ValueError("Invalid auth session payload")
    return payload


def read_access_token_expires_in(access_token: str, *, urlsafe_b64decode: Any) -> int:
    token = str(access_token or "").strip()
    if not token:
        return 3600
    parts = token.split(".")
    if len(parts) < 2:
        return 3600
    try:
        payload = json.loads(urlsafe_b64decode(parts[1]).decode("utf-8"))
        exp = int(payload.get("exp") or 0)
    except (ValueError, json.JSONDecodeError, TypeError):
        return 3600
    if exp <= 0:
        return 3600
    return max(60, exp - int(time.time()))
