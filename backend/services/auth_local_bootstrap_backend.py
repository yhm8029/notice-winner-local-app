from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import NAMESPACE_URL
from uuid import uuid5


def can_use_local_bootstrap_fallback(
    *,
    request_host: str,
    email: str,
    normalize_email: Any,
    bootstrap_platform_admin_email: Any,
) -> bool:
    host = str(request_host or "").strip().lower()
    normalized_email = normalize_email(email)
    bootstrap_email = bootstrap_platform_admin_email()
    if not bootstrap_email or normalized_email != bootstrap_email:
        return False
    return host in {"127.0.0.1", "::1", "localhost"}


def bootstrap_local_auth_path(*, default_path: str) -> str:
    configured = os.getenv("PHASE2_LOCAL_BOOTSTRAP_AUTH_FILE", "").strip()
    if configured:
        return configured
    return default_path


def load_local_bootstrap_auth_record(*, path: str) -> dict[str, Any]:
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def save_local_bootstrap_auth_record(*, path: str, payload: dict[str, Any]) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def hash_local_bootstrap_password(password: str, *, salt_hex: str = "") -> tuple[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", str(password or "").encode("utf-8"), salt, 120_000).hex()
    return salt.hex(), digest


def register_local_bootstrap_password(
    *,
    email: str,
    password: str,
    normalize_email: Any,
    hash_local_bootstrap_password_fn: Any,
    save_local_bootstrap_auth_record_fn: Any,
) -> None:
    normalized_email = normalize_email(email)
    salt_hex, password_hash = hash_local_bootstrap_password_fn(password)
    save_local_bootstrap_auth_record_fn(
        {
            "email": normalized_email,
            "salt_hex": salt_hex,
            "password_hash": password_hash,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )


def verify_local_bootstrap_password(
    *,
    email: str,
    password: str,
    normalize_email: Any,
    load_local_bootstrap_auth_record_fn: Any,
    hash_local_bootstrap_password_fn: Any,
) -> bool:
    payload = load_local_bootstrap_auth_record_fn()
    if normalize_email(payload.get("email")) != normalize_email(email):
        return False
    salt_hex = str(payload.get("salt_hex") or "").strip()
    password_hash = str(payload.get("password_hash") or "").strip()
    if not salt_hex or not password_hash:
        return False
    _salt_hex, computed_hash = hash_local_bootstrap_password_fn(password, salt_hex=salt_hex)
    return hmac.compare_digest(password_hash, computed_hash)


def has_local_bootstrap_password(
    *,
    email: str,
    normalize_email: Any,
    load_local_bootstrap_auth_record_fn: Any,
) -> bool:
    payload = load_local_bootstrap_auth_record_fn()
    return (
        normalize_email(payload.get("email")) == normalize_email(email)
        and bool(str(payload.get("salt_hex") or "").strip())
        and bool(str(payload.get("password_hash") or "").strip())
    )


def local_bootstrap_auth_user_id(email: str, *, normalize_email: Any) -> str:
    return str(uuid5(NAMESPACE_URL, f"local-bootstrap:{normalize_email(email)}"))


def resolve_local_bootstrap_auth_user_id(
    email: str,
    *,
    normalize_email: Any,
    get_user_profile: Any,
    get_local_user: Any,
    default_organization_id: Any,
    local_bootstrap_auth_user_id_fn: Any,
) -> str:
    normalized_email = normalize_email(email)
    existing_profile = get_user_profile(email=normalized_email)
    existing_profile_id = str(existing_profile.get("id") or "").strip() if existing_profile else ""
    if existing_profile_id:
        return existing_profile_id
    existing_local = get_local_user(email=normalized_email, organization_id=str(default_organization_id))
    existing_local_id = str(existing_local.get("id") or "").strip() if existing_local else ""
    if existing_local_id:
        return existing_local_id
    return local_bootstrap_auth_user_id_fn(normalized_email)


def build_local_bootstrap_session(
    *,
    email: str,
    display_name: str = "",
    message: str = "",
    normalize_email: Any,
    resolve_local_bootstrap_auth_user_id_fn: Any,
    ensure_bootstrap_local_user: Any,
    normalize_local_user_status: Any,
    normalize_account_status: Any,
    normalize_membership_status: Any,
    default_bootstrap_org_name: str,
    session_cookie_max_age_seconds: int,
) -> dict[str, Any]:
    normalized_email = normalize_email(email)
    auth_user_id = resolve_local_bootstrap_auth_user_id_fn(normalized_email)
    local_user = ensure_bootstrap_local_user(
        auth_user_id=auth_user_id,
        email=normalized_email,
        display_name=display_name or normalized_email.split("@", 1)[0],
    )
    return {
        "auth_user_id": auth_user_id,
        "email": normalized_email,
        "display_name": display_name or str(local_user.get("display_name") or normalized_email.split("@", 1)[0]),
        "role": "platform_admin",
        "authorized": True,
        "organization_id": str(local_user.get("organization_id") or ""),
        "organization_name": str(local_user.get("organization_name") or default_bootstrap_org_name),
        "local_user_id": str(local_user.get("id") or ""),
        "membership_id": str(local_user.get("membership_id") or ""),
        "status": normalize_local_user_status(local_user.get("status")),
        "account_status": normalize_account_status(local_user.get("account_status")),
        "membership_status": normalize_membership_status(local_user.get("membership_status")),
        "mobile_phone": str(local_user.get("mobile_phone") or ""),
        "office_phone": str(local_user.get("office_phone") or ""),
        "message": message,
        "access_token": "local-bootstrap",
        "refresh_token": "",
        "access_expires_at": int(time.time()) + session_cookie_max_age_seconds,
        "auth_provider": "local_bootstrap",
    }


def build_invite_url(base: str, token: str) -> str:
    normalized_base = str(base or "").strip().rstrip("/")
    if not normalized_base:
        return f"/app/?invite_token={token}"
    return f"{normalized_base}/app/?invite_token={token}"


def build_invitation_initial_password(token: str, *, session_secret: Any) -> str:
    normalized_token = str(token or "").strip()
    if not normalized_token:
        return ""
    seed = hmac.new(
        session_secret().encode("utf-8"),
        normalized_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    alphabet = (
        "ABCDEFGHJKLMNPQRSTUVWXYZ"
        "abcdefghijkmnopqrstuvwxyz"
        "23456789"
        "!@#$%^&*_-+="
    )
    chars = [alphabet[seed[index] % len(alphabet)] for index in range(16)]
    return "".join(chars)
