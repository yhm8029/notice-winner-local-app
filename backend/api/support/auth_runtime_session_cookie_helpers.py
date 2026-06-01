from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from typing import Any


def session_secret(*, configured_secret: str = "", service_api_key_fn, error_cls) -> str:
    configured = str(configured_secret or "").strip() or os.getenv("PHASE2_AUTH_SESSION_SECRET", "").strip()
    if configured:
        return configured
    service_key = service_api_key_fn()
    if service_key:
        return hashlib.sha256(service_key.encode("utf-8")).hexdigest()
    raise error_cls("PHASE2_AUTH_SESSION_SECRET is required", status_code=503, code="auth_config_error")


def encode_signed_payload(
    payload: dict[str, Any],
    *,
    session_secret_fn=None,
    session_secret=None,
    urlsafe_b64encode_fn=None,
    urlsafe_b64encode=None,
) -> str:
    session_secret_callable = session_secret_fn or session_secret
    urlsafe_b64encode_callable = urlsafe_b64encode_fn or urlsafe_b64encode
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    encoded = urlsafe_b64encode_callable(raw)
    signature = hmac.new(session_secret_callable().encode("utf-8"), encoded.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def decode_signed_payload(
    value: str,
    *,
    session_secret_fn=None,
    session_secret=None,
    urlsafe_b64decode_fn=None,
    urlsafe_b64decode=None,
) -> dict[str, Any]:
    session_secret_callable = session_secret_fn or session_secret
    urlsafe_b64decode_callable = urlsafe_b64decode_fn or urlsafe_b64decode
    encoded, separator, signature = str(value or "").partition(".")
    if not encoded or not separator or not signature:
        raise ValueError("Invalid auth session payload")
    expected = hmac.new(session_secret_callable().encode("utf-8"), encoded.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("Invalid auth session signature")
    try:
        raw = urlsafe_b64decode_callable(encoded)
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid auth session body") from exc
    if not isinstance(payload, dict):
        raise ValueError("Invalid auth session payload")
    return payload


def read_access_token_expires_in(access_token: str, *, urlsafe_b64decode_fn=None, urlsafe_b64decode=None) -> int:
    urlsafe_b64decode_callable = urlsafe_b64decode_fn or urlsafe_b64decode
    token = str(access_token or "").strip()
    if not token:
        return 3600
    parts = token.split(".")
    if len(parts) < 2:
        return 3600
    try:
        payload = json.loads(urlsafe_b64decode_callable(parts[1]).decode("utf-8"))
        exp = int(payload.get("exp") or 0)
    except (ValueError, json.JSONDecodeError, TypeError):
        return 3600
    if exp <= 0:
        return 3600
    return max(60, exp - int(time.time()))


def urlsafe_b64encode(value: bytes) -> str:
    import base64

    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def urlsafe_b64decode(value: str) -> bytes:
    import base64

    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
