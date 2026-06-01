from __future__ import annotations

from typing import Any

import requests

from backend.repositories.supabase_http import extract_error_message
from backend.repositories.supabase_http import request_json


def auth_request(
    method: str,
    path: str,
    *,
    query: list[tuple[str, str]] | None = None,
    payload: dict[str, Any] | None = None,
    access_token: str = "",
    use_service_authorization: bool,
    timeout_seconds: float | None = None,
    auth_base_url_fn,
    service_api_key_fn,
    public_api_key_fn,
    timeout_seconds_fn,
    error_cls,
    requests_request_fn=requests.request,
    extract_error_message_fn=extract_error_message,
) -> dict[str, Any]:
    url = f"{auth_base_url_fn()}{path}"
    api_key = service_api_key_fn() if use_service_authorization else public_api_key_fn()
    authorization_token = service_api_key_fn() if use_service_authorization else access_token or api_key
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {authorization_token}",
        "Accept": "application/json",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    try:
        response = requests_request_fn(
            method=method,
            url=url,
            params=query or None,
            headers=headers,
            json=payload if payload is not None else None,
            timeout=timeout_seconds if timeout_seconds is not None else timeout_seconds_fn(),
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        body = exc.response.text if exc.response is not None else ""
        status_code = exc.response.status_code if exc.response is not None else 502
        message = extract_error_message_fn(body.strip()) or f"Supabase auth request failed: HTTP {status_code}"
        raise error_cls(message, status_code=status_code, code="auth_upstream_error") from exc
    except requests.RequestException as exc:
        raise error_cls(
            f"Supabase auth request failed: {exc}",
            status_code=503,
            code="auth_upstream_error",
        ) from exc

    raw = response.text.strip()
    if not raw:
        return {}
    try:
        parsed = response.json()
    except ValueError as exc:
        raise error_cls("Supabase auth response is not valid JSON", status_code=502, code="auth_invalid") from exc
    if not isinstance(parsed, dict):
        raise error_cls("Supabase auth response is not a JSON object", status_code=502, code="auth_invalid")
    return parsed


def rest_upsert(
    path: str,
    payload: dict[str, Any],
    *,
    on_conflict: str,
    rest_base_url_fn,
    service_api_key_fn,
    timeout_seconds_fn,
    error_cls,
    request_json_fn=request_json,
) -> None:
    request_json_fn(
        rest_url=rest_base_url_fn(),
        api_key=service_api_key_fn(),
        timeout_seconds=timeout_seconds_fn(),
        method="POST",
        path=f"/{path}",
        query=[("on_conflict", on_conflict)],
        headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
        payload=payload,
        allow_retry=False,
        error_cls=error_cls,
    )


def rest_delete_rows(
    path: str,
    query: list[tuple[str, str]],
    *,
    rest_base_url_fn,
    service_api_key_fn,
    timeout_seconds_fn,
    error_cls,
    request_json_fn=request_json,
) -> None:
    request_json_fn(
        rest_url=rest_base_url_fn(),
        api_key=service_api_key_fn(),
        timeout_seconds=timeout_seconds_fn(),
        method="DELETE",
        path=f"/{path}",
        query=query,
        headers={"Prefer": "return=minimal"},
        allow_retry=False,
        error_cls=error_cls,
    )


def delete_supabase_auth_user(*, auth_user_id: str, auth_request_fn, error_cls) -> None:
    if not str(auth_user_id or "").strip():
        return
    try:
        auth_request_fn(
            "DELETE",
            f"/admin/users/{auth_user_id}",
            use_service_authorization=True,
        )
    except error_cls as exc:
        lowered = str(exc.message or "").lower()
        if exc.status_code == 404 or "user not found" in lowered:
            return
        raise


def create_supabase_auth_user(
    *,
    email: str,
    password: str,
    display_name: str = "",
    normalize_email_fn,
    auth_request_fn,
    error_cls,
) -> dict[str, Any]:
    normalized_email = normalize_email_fn(email)
    if not normalized_email or not str(password or "").strip():
        raise error_cls("email and password are required", status_code=400, code="validation_error")
    metadata: dict[str, Any] = {}
    normalized_display_name = str(display_name or "").strip()
    if normalized_display_name:
        metadata["display_name"] = normalized_display_name
    return auth_request_fn(
        "POST",
        "/admin/users",
        payload={
            "email": normalized_email,
            "password": password,
            "email_confirm": True,
            "user_metadata": metadata,
        },
        use_service_authorization=True,
    )


def reset_platform_admin_account_password(
    *,
    user_id: str,
    email: str,
    password: str,
    normalize_email_fn,
    auth_request_fn,
    bootstrap_platform_admin_email_fn,
    register_local_bootstrap_password_fn,
    error_cls,
) -> dict[str, Any]:
    normalized_user_id = str(user_id or "").strip()
    normalized_email = normalize_email_fn(email)
    normalized_password = str(password or "").strip()
    if not normalized_user_id:
        raise error_cls("user_id is required", status_code=400, code="validation_error")
    if not normalized_email:
        raise error_cls("email is required", status_code=400, code="validation_error")
    if not normalized_password:
        raise error_cls("password is required", status_code=400, code="validation_error")
    auth_request_fn(
        "PUT",
        f"/admin/users/{normalized_user_id}",
        payload={"password": normalized_password},
        use_service_authorization=True,
    )
    if normalized_email == bootstrap_platform_admin_email_fn():
        register_local_bootstrap_password_fn(email=normalized_email, password=normalized_password)
    return {"message": "鍮꾨?踰덊샇瑜??ъ꽕?뺥뻽?듬땲??"}


def reset_platform_admin_account_password_with_context(
    *,
    actor_user_id: str,
    actor_role: str,
    organization_id: str,
    user_id: str,
    email: str,
    password: str,
    normalize_email_fn,
    auth_request_fn,
    bootstrap_platform_admin_email_fn,
    register_local_bootstrap_password_fn,
    append_audit_log_fn,
    logger,
    error_cls,
) -> dict[str, Any]:
    normalized_actor_role = str(actor_role or "").strip().lower()
    if normalized_actor_role != "platform_admin":
        raise error_cls("platform admin only", status_code=403, code="auth_forbidden")

    normalized_organization_id = str(organization_id or "").strip()
    normalized_actor_user_id = str(actor_user_id or "").strip()
    normalized_user_id = str(user_id or "").strip()
    normalized_email = normalize_email_fn(email)
    normalized_password = str(password or "").strip()
    if not normalized_organization_id:
        raise error_cls("organization_id is required", status_code=400, code="validation_error")
    if not normalized_user_id:
        raise error_cls("user_id is required", status_code=400, code="validation_error")
    if not normalized_email:
        raise error_cls("email is required", status_code=400, code="validation_error")
    if not normalized_password:
        raise error_cls("password is required", status_code=400, code="validation_error")
    if normalized_email == bootstrap_platform_admin_email_fn():
        raise error_cls(
            "bootstrap platform admin account is protected",
            status_code=409,
            code="auth_user_protected",
        )
    if normalized_actor_user_id and normalized_actor_user_id == normalized_user_id:
        raise error_cls(
            "platform admins cannot reset their own password here",
            status_code=403,
            code="auth_user_self_password_reset_forbidden",
        )

    auth_request_fn(
        "PUT",
        f"/admin/users/{normalized_user_id}",
        payload={"password": normalized_password},
        use_service_authorization=True,
    )
    try:
        append_audit_log_fn(
            organization_id=normalized_organization_id,
            actor_user_id=normalized_actor_user_id,
            event_type="account_password_reset",
            target_type="user_profile",
            target_id=normalized_user_id,
            payload={"email": normalized_email},
        )
    except Exception:
        try:
            logger.warning(
                "account_password_reset audit log failed (organization_id=%s, user_id=%s, email=%s)",
                normalized_organization_id,
                normalized_user_id,
                normalized_email,
            )
        except Exception:
            pass
    return {"message": "password reset scheduled"}
