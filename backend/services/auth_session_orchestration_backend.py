from __future__ import annotations

from typing import Any


def sign_in_with_password(
    *,
    email: str,
    password: str,
    invite_token: str = "",
    request_host: str = "",
    ensure_auth_enabled: Any,
    normalize_email_fn: Any,
    can_use_local_bootstrap_fallback_fn: Any,
    has_local_bootstrap_password_fn: Any,
    verify_local_bootstrap_password_fn: Any,
    build_local_bootstrap_session_fn: Any,
    auth_request_fn: Any,
    finalize_session_payload_fn: Any,
    resolve_pending_invitation_token_for_email_fn: Any,
    require_invitation_email_match_fn: Any,
    accept_invitation_for_session_payload_fn: Any,
    touch_last_login_fn: Any,
    error_cls: Any,
    local_bootstrap_sign_in_message: str = "",
    local_bootstrap_invalid_password_message: str = "",
    local_bootstrap_missing_password_message: str = "",
) -> dict[str, Any]:
    ensure_auth_enabled()
    normalized_email = normalize_email_fn(email)
    if not normalized_email or not password:
        raise error_cls("email and password are required", status_code=400, code="validation_error")
    if can_use_local_bootstrap_fallback_fn(request_host=request_host, email=normalized_email):
        if has_local_bootstrap_password_fn(email=normalized_email):
            if verify_local_bootstrap_password_fn(email=normalized_email, password=password):
                return build_local_bootstrap_session_fn(
                    email=normalized_email,
                    display_name="",
                    message=local_bootstrap_sign_in_message,
                )
            raise error_cls(local_bootstrap_invalid_password_message, status_code=400, code="validation_error")
    try:
        token_payload = auth_request_fn(
            "POST",
            "/token",
            query=[("grant_type", "password")],
            payload={"email": normalized_email, "password": password},
            use_service_authorization=False,
        )
    except error_cls as exc:
        if can_use_local_bootstrap_fallback_fn(request_host=request_host, email=normalized_email):
            if not has_local_bootstrap_password_fn(email=normalized_email):
                raise error_cls(
                    local_bootstrap_missing_password_message,
                    status_code=400,
                    code="validation_error",
                ) from exc
            if verify_local_bootstrap_password_fn(email=normalized_email, password=password):
                return build_local_bootstrap_session_fn(
                    email=normalized_email,
                    display_name="",
                    message=local_bootstrap_sign_in_message,
                )
            raise error_cls(local_bootstrap_invalid_password_message, status_code=400, code="validation_error") from exc
        raise
    session_payload = finalize_session_payload_fn(token_payload)
    resolved_invite_token = resolve_pending_invitation_token_for_email_fn(
        email=normalized_email,
        invite_token=invite_token,
        required=False,
    )
    require_invitation_email_match_fn(invite_token=resolved_invite_token, email=normalized_email)
    if resolved_invite_token:
        return accept_invitation_for_session_payload_fn(
            session_payload=session_payload,
            invite_token=resolved_invite_token,
        )
    touch_last_login_fn(auth_user_id=str(session_payload.get("auth_user_id") or "").strip())
    return session_payload


def sign_up_console_user(
    *,
    email: str,
    password: str,
    display_name: str = "",
    invite_token: str = "",
    request_host: str = "",
    ensure_auth_enabled: Any,
    normalize_email_fn: Any,
    bootstrap_platform_admin_email_fn: Any,
    resolve_pending_invitation_token_for_email_fn: Any,
    require_invitation_email_match_fn: Any,
    can_use_local_bootstrap_fallback_fn: Any,
    register_local_bootstrap_password_fn: Any,
    build_local_bootstrap_session_fn: Any,
    auth_request_fn: Any,
    is_existing_auth_user_error_fn: Any,
    sign_in_with_password_fn: Any,
    ensure_bootstrap_local_user_fn: Any,
    ensure_member_local_user_fn: Any,
    finalize_session_payload_fn: Any,
    current_time_fn: Any,
    error_cls: Any,
    local_bootstrap_sign_up_message: str = "",
) -> dict[str, Any]:
    ensure_auth_enabled()
    normalized_email = normalize_email_fn(email)
    bootstrap_email = bootstrap_platform_admin_email_fn()
    resolved_invite_token = str(invite_token or "").strip()
    if normalized_email != bootstrap_email or resolved_invite_token:
        resolved_invite_token = resolve_pending_invitation_token_for_email_fn(
            email=normalized_email,
            invite_token=resolved_invite_token,
            required=normalized_email != bootstrap_email,
        )
    if not password:
        raise error_cls("password is required", status_code=400, code="validation_error")
    require_invitation_email_match_fn(invite_token=resolved_invite_token, email=normalized_email)
    if normalized_email == bootstrap_email and can_use_local_bootstrap_fallback_fn(
        request_host=request_host,
        email=normalized_email,
    ):
        register_local_bootstrap_password_fn(email=normalized_email, password=password)
        return build_local_bootstrap_session_fn(
            email=normalized_email,
            display_name=display_name.strip(),
            message=local_bootstrap_sign_up_message,
        )

    metadata: dict[str, Any] = {}
    if display_name.strip():
        metadata["display_name"] = display_name.strip()
    try:
        auth_request_fn(
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
    except error_cls as exc:
        lowered = str(getattr(exc, "message", "") or str(exc) or "").lower()
        if not is_existing_auth_user_error_fn(lowered):
            if normalized_email == bootstrap_email and can_use_local_bootstrap_fallback_fn(
                request_host=request_host,
                email=normalized_email,
            ):
                register_local_bootstrap_password_fn(email=normalized_email, password=password)
                return build_local_bootstrap_session_fn(
                    email=normalized_email,
                    display_name=display_name.strip(),
                    message=local_bootstrap_sign_up_message,
                )
            raise

    session_payload = sign_in_with_password_fn(
        email=normalized_email,
        password=password,
        invite_token=resolved_invite_token,
        request_host=request_host,
    )
    resolved_display_name = str(session_payload.get("display_name") or display_name or "").strip()
    if normalized_email == bootstrap_email:
        ensure_bootstrap_local_user_fn(
            auth_user_id=str(session_payload.get("auth_user_id") or "").strip(),
            email=normalized_email,
            display_name=resolved_display_name,
        )
    else:
        ensure_member_local_user_fn(
            auth_user_id=str(session_payload.get("auth_user_id") or "").strip(),
            email=normalized_email,
            display_name=resolved_display_name,
        )
    return finalize_session_payload_fn(
        {
            "access_token": session_payload.get("access_token"),
            "refresh_token": session_payload.get("refresh_token"),
            "expires_in": max(60, int(session_payload.get("access_expires_at") or 0) - int(current_time_fn())),
            "user": {
                "id": session_payload.get("auth_user_id"),
                "email": normalized_email,
                "user_metadata": {"display_name": resolved_display_name},
            },
        }
    )


def send_password_reset_email(
    *,
    email: str,
    request_host: str = "",
    ensure_auth_enabled: Any,
    normalize_email_fn: Any,
    can_use_local_bootstrap_fallback_fn: Any,
    auth_request_fn: Any,
    error_cls: Any,
    local_bootstrap_reset_message: str = "",
    password_reset_sent_message: str = "",
) -> dict[str, Any]:
    ensure_auth_enabled()
    normalized_email = normalize_email_fn(email)
    if not normalized_email:
        raise error_cls("email is required", status_code=400, code="validation_error")
    if can_use_local_bootstrap_fallback_fn(request_host=request_host, email=normalized_email):
        return {"message": local_bootstrap_reset_message}
    auth_request_fn(
        "POST",
        "/recover",
        payload={"email": normalized_email},
        use_service_authorization=False,
    )
    return {"message": password_reset_sent_message}


def ensure_fresh_session_payload(
    *,
    payload: dict[str, Any] | None,
    response: Any,
    ensure_auth_enabled: Any,
    now: int,
    grace_seconds: int,
    refresh_auth_session_fn: Any,
    clear_auth_session_cookie_fn: Any,
    set_auth_session_cookie_fn: Any,
    error_cls: Any,
    logger: Any,
    session_refresh_timeout_seconds_fn: Any,
) -> dict[str, Any]:
    ensure_auth_enabled()
    if payload is None:
        raise error_cls("sign-in required", status_code=401, code="auth_required")

    needs_refresh = int(payload.get("access_expires_at") or 0) <= now + grace_seconds
    if needs_refresh:
        refresh_token = str(payload.get("refresh_token") or "").strip()
        if not refresh_token:
            clear_auth_session_cookie_fn(response)
            raise error_cls("sign-in required", status_code=401, code="auth_required")
        try:
            payload = refresh_auth_session_fn(
                refresh_token,
                timeout_seconds=session_refresh_timeout_seconds_fn(),
            )
        except error_cls as exc:
            logger.warning(
                "auth session refresh failed during protected request: %s",
                str(getattr(exc, "message", "") or str(exc)),
            )
            clear_auth_session_cookie_fn(response)
            raise error_cls("sign-in required", status_code=401, code="auth_required") from exc
        set_auth_session_cookie_fn(response, payload)
    return payload


def build_session_response(
    *,
    payload: dict[str, Any] | None,
    response: Any,
    now: int,
    grace_seconds: int,
    refresh_auth_session_fn: Any,
    clear_auth_session_cookie_fn: Any,
    set_auth_session_cookie_fn: Any,
    build_auth_status_response_fn: Any,
    build_session_response_payload_fn: Any,
    error_cls: Any,
    logger: Any,
    session_refresh_timeout_seconds_fn: Any,
    refresh_failure_message: str,
) -> dict[str, Any]:
    if payload is None:
        return build_auth_status_response_fn()
    if not payload.get("authorized"):
        return build_session_response_payload_fn(payload)

    needs_refresh = int(payload.get("access_expires_at") or 0) <= now + grace_seconds
    if needs_refresh:
        refresh_token = str(payload.get("refresh_token") or "").strip()
        if refresh_token:
            try:
                payload = refresh_auth_session_fn(
                    refresh_token,
                    timeout_seconds=session_refresh_timeout_seconds_fn(),
                )
            except error_cls as exc:
                logger.warning(
                    "auth session refresh failed during status check: %s",
                    str(getattr(exc, "message", "") or str(exc)),
                )
                clear_auth_session_cookie_fn(response)
                logged_out = build_auth_status_response_fn()
                logged_out["message"] = refresh_failure_message
                return logged_out
            set_auth_session_cookie_fn(response, payload)
        else:
            clear_auth_session_cookie_fn(response)
            return build_auth_status_response_fn()

    return build_session_response_payload_fn(payload)


def refresh_auth_session(
    refresh_token: str,
    *,
    timeout_seconds: float | None = None,
    auth_request_fn: Any,
    finalize_session_payload_fn: Any,
) -> dict[str, Any]:
    token_payload = auth_request_fn(
        "POST",
        "/token",
        query=[("grant_type", "refresh_token")],
        payload={"refresh_token": refresh_token},
        use_service_authorization=False,
        timeout_seconds=timeout_seconds,
    )
    return finalize_session_payload_fn(token_payload)


def update_console_user_profile(
    *,
    session_payload: dict[str, Any],
    display_name: str,
    mobile_phone: str = "",
    office_phone: str = "",
    current_password: str = "",
    password: str = "",
    invite_token: str = "",
    ensure_auth_enabled: Any,
    normalize_email_fn: Any,
    verify_local_bootstrap_password_fn: Any,
    can_use_invite_password_setup_fn: Any,
    register_local_bootstrap_password_fn: Any,
    update_local_user_profile_fn: Any,
    build_local_bootstrap_session_fn: Any,
    verify_password_fn: Any,
    auth_request_fn: Any,
    finalize_session_payload_fn: Any,
    current_time_fn: Any,
    error_cls: Any,
    current_password_mismatch_message: str = "",
) -> dict[str, Any]:
    ensure_auth_enabled()
    auth_user_id = str(session_payload.get("auth_user_id") or "").strip()
    email = normalize_email_fn(session_payload.get("email"))
    access_token = str(session_payload.get("access_token") or "").strip()
    if not auth_user_id or not email or not access_token:
        raise error_cls("valid authenticated session is required", status_code=401, code="auth_required")

    normalized_display_name = str(display_name or "").strip()
    if not normalized_display_name:
        raise error_cls("display_name is required", status_code=400, code="validation_error")
    normalized_current_password = str(current_password or "")
    normalized_invite_token = str(invite_token or "").strip()
    local_bootstrap_session = str(session_payload.get("auth_provider") or "") == "local_bootstrap"
    if normalized_current_password:
        if local_bootstrap_session:
            if not verify_local_bootstrap_password_fn(email=email, password=normalized_current_password):
                raise error_cls(current_password_mismatch_message, status_code=400, code="validation_error")
        else:
            verify_password_fn(email=email, password=normalized_current_password)
    elif not can_use_invite_password_setup_fn(
        auth_user_id=auth_user_id,
        email=email,
        invite_token=normalized_invite_token,
    ):
        raise error_cls("current password is required", status_code=400, code="validation_error")

    normalized_password = str(password or "")
    if normalized_password and len(normalized_password) < 8:
        raise error_cls("password must be at least 8 characters", status_code=400, code="validation_error")

    if local_bootstrap_session:
        if normalized_password:
            register_local_bootstrap_password_fn(email=email, password=normalized_password)
        update_local_user_profile_fn(
            user_id=auth_user_id,
            email=email,
            display_name=normalized_display_name,
            mobile_phone=mobile_phone,
            office_phone=office_phone,
        )
        return build_local_bootstrap_session_fn(
            email=email,
            display_name=normalized_display_name,
            message="",
        )

    auth_update_payload: dict[str, Any] = {"data": {"display_name": normalized_display_name}}
    if normalized_password:
        auth_update_payload["password"] = normalized_password
    updated_user = auth_request_fn(
        "PUT",
        "/user",
        payload=auth_update_payload,
        access_token=access_token,
        use_service_authorization=False,
    )
    if not isinstance(updated_user, dict) or not str(updated_user.get("id") or "").strip():
        raise error_cls("Supabase auth response did not include an updated user", status_code=502, code="auth_invalid")

    update_local_user_profile_fn(
        user_id=auth_user_id,
        email=email,
        display_name=normalized_display_name,
        mobile_phone=mobile_phone,
        office_phone=office_phone,
    )
    expires_in = max(60, int(session_payload.get("access_expires_at") or 0) - int(current_time_fn()))
    return finalize_session_payload_fn(
        {
            "user": updated_user,
            "access_token": access_token,
            "refresh_token": str(session_payload.get("refresh_token") or ""),
            "expires_in": expires_in,
        }
    )
