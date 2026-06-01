from __future__ import annotations

import os


def normalize_truthy(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def supabase_url() -> str:
    return os.getenv("SUPABASE_URL", "").strip().rstrip("/")


def service_api_key() -> str:
    return (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_SECRET", "").strip()
    )


def public_api_key(*, error_cls) -> str:
    key = (
        os.getenv("SUPABASE_ANON_KEY", "").strip()
        or os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
    )
    if not key:
        raise error_cls(
            "SUPABASE_ANON_KEY or SUPABASE_PUBLISHABLE_KEY is required for sign-in and sign-up.",
            status_code=503,
            code="auth_config_error",
        )
    return key


def timeout_seconds() -> float:
    raw = os.getenv("SUPABASE_HTTP_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return 15.0
    try:
        parsed = float(raw)
    except ValueError:
        return 15.0
    return max(1.0, parsed)


def session_refresh_timeout_seconds(*, timeout_seconds_fn) -> float:
    raw = os.getenv("SUPABASE_AUTH_REFRESH_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return min(5.0, timeout_seconds_fn())
    try:
        parsed = float(raw)
    except ValueError:
        return min(5.0, timeout_seconds_fn())
    return max(1.0, parsed)


def auth_base_url(*, supabase_url_fn, error_cls) -> str:
    base_url = supabase_url_fn()
    if not base_url:
        raise error_cls("SUPABASE_URL is required", status_code=503, code="auth_config_error")
    return f"{base_url}/auth/v1"


def rest_base_url(*, supabase_url_fn, error_cls) -> str:
    base_url = supabase_url_fn()
    if not base_url:
        raise error_cls("SUPABASE_URL is required", status_code=503, code="auth_config_error")
    return f"{base_url}/rest/v1"


def ensure_auth_enabled(*, auth_is_enabled_fn, error_cls) -> None:
    if not auth_is_enabled_fn():
        raise error_cls("Phase 2 auth is not enabled.", status_code=503, code="auth_disabled")
