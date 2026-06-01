from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from uuid import UUID
from uuid import NAMESPACE_URL
from uuid import uuid5

import requests
from fastapi import Request
from fastapi import Response

from backend.phase1_defaults import DEFAULT_PHASE1_ORGANIZATION_ID
from backend.repositories.factory import get_login_audit_log_repository
from backend.repositories.supabase_http import extract_error_message
from backend.repositories.supabase_http import request_json
from backend.services.auth_invitation_backend import can_manage_invitation_role as _can_manage_invitation_role_impl
from backend.services.auth_invitation_backend import create_invitation as _create_invitation_impl
from backend.services.auth_invitation_backend import deliver_invitation_email as _deliver_invitation_email_impl
from backend.services.auth_invitation_backend import expire_stale_invitations as _expire_stale_invitations_impl
from backend.services.auth_invitation_backend import filter_manageable_invitations as _filter_manageable_invitations_impl
from backend.services.auth_invitation_backend import persist_invitation_status as _persist_invitation_status_impl
from backend.services.auth_invitation_backend import raise_create_invitation_error as _raise_create_invitation_error_impl
from backend.services.auth_invitation_backend import resolve_allowed_invitation_roles as _resolve_allowed_invitation_roles_impl
from backend.services.auth_invitation_backend import revoke_invitation as _revoke_invitation_impl
from backend.services.auth_invitation_backend import validate_invitation_permissions as _validate_invitation_permissions_impl
from backend.services.auth_invitation_read_backend import get_invitation_by_id as _get_invitation_by_id_impl
from backend.services.auth_invitation_read_backend import get_invitation_by_token as _get_invitation_by_token_impl
from backend.services.auth_invitation_read_backend import get_invitation_preview as _get_invitation_preview_impl
from backend.services.auth_invitation_read_backend import get_invitation_preview_by_email as _get_invitation_preview_by_email_impl
from backend.services.auth_invitation_read_backend import list_invitations as _list_invitations_impl
from backend.services.auth_invitation_read_backend import list_pending_invitations_by_email as _list_pending_invitations_by_email_impl
from backend.services.auth_invitation_read_backend import normalize_invitation_row as _normalize_invitation_row_impl
from backend.services.auth_invitation_session_backend import can_use_invite_password_setup as _can_use_invite_password_setup_impl
from backend.services.auth_invitation_session_backend import raise_accept_invitation_error as _raise_accept_invitation_error_invite_impl
from backend.services.auth_invitation_session_backend import require_invitation_email_match as _require_invitation_email_match_impl
from backend.services.auth_invitation_session_backend import resolve_pending_invitation_token_for_email as _resolve_pending_invitation_token_for_email_impl
from backend.services.auth_invitation_session_backend import resolve_session_invitation_token as _resolve_session_invitation_token_impl
from backend.services.auth_admin_account_backend import create_platform_admin_account as _create_platform_admin_account_impl
from backend.services.auth_profile_lookup_backend import build_profile_from_legacy_user as _build_profile_from_legacy_user_lookup_impl
from backend.services.auth_profile_lookup_backend import get_local_user as _get_local_user_impl
from backend.services.auth_profile_lookup_backend import get_membership_row as _get_membership_row_impl
from backend.services.auth_profile_lookup_backend import get_user_profile as _get_user_profile_impl
from backend.services.auth_profile_write_backend import ensure_membership as _ensure_membership_impl
from backend.services.auth_profile_write_backend import ensure_user_profile as _ensure_user_profile_impl
from backend.services.auth_profile_write_backend import sync_legacy_user_projection as _sync_legacy_user_projection_impl
from backend.services.auth_profile_write_backend import update_local_user_profile as _update_local_user_profile_impl
from backend.services.auth_session_orchestration_backend import build_session_response as _build_session_response_impl
from backend.services.auth_session_orchestration_backend import ensure_fresh_session_payload as _ensure_fresh_session_payload_impl
from backend.services.auth_session_orchestration_backend import refresh_auth_session as _refresh_auth_session_impl
from backend.services.auth_session_orchestration_backend import send_password_reset_email as _send_password_reset_email_impl
from backend.services.auth_session_orchestration_backend import sign_in_with_password as _sign_in_with_password_impl
from backend.services.auth_session_orchestration_backend import sign_up_console_user as _sign_up_console_user_impl
from backend.services.auth_session_orchestration_backend import update_console_user_profile as _update_console_user_profile_impl
from backend.services.auth_runtime_support_backend import is_missing_column_error as _is_missing_column_error_impl
from backend.services.auth_runtime_support_backend import is_missing_relation_error as _is_missing_relation_error_impl
from backend.services.auth_runtime_support_backend import map_membership_role_to_legacy_role as _map_membership_role_to_legacy_role_impl
from backend.services.auth_runtime_support_backend import map_role_label as _map_role_label_impl
from backend.services.auth_runtime_support_backend import normalize_account_status as _normalize_account_status_impl
from backend.services.auth_runtime_support_backend import normalize_email as _normalize_email_impl
from backend.services.auth_runtime_support_backend import normalize_global_role as _normalize_global_role_impl
from backend.services.auth_runtime_support_backend import normalize_local_user_status as _normalize_local_user_status_impl
from backend.services.auth_runtime_support_backend import normalize_membership_status as _normalize_membership_status_impl
from backend.services.auth_runtime_support_backend import normalize_org_role as _normalize_org_role_impl
from backend.services.auth_runtime_support_backend import parse_datetime_value as _parse_datetime_value_impl
from backend.services.auth_organization_backend import get_organization as _get_organization_impl
from backend.services.auth_organization_backend import normalize_limit_value as _normalize_limit_value_impl
from backend.services.auth_organization_backend import normalize_organization_row as _normalize_organization_row_impl
from backend.services.auth_organization_backend import normalize_plan_code as _normalize_plan_code_impl
from backend.services.auth_organization_backend import resolve_next_plan_code as _resolve_next_plan_code_impl
from backend.services.auth_organization_plan_backend import build_organization_plan_summary as _build_organization_plan_summary_impl
from backend.services.auth_organization_plan_backend import build_plan_upgrade_message as _build_plan_upgrade_message_impl
from backend.services.auth_organization_plan_backend import counts_towards_active_user_limit as _counts_towards_active_user_limit_impl
from backend.services.auth_organization_plan_backend import ensure_acceptance_capacity as _ensure_acceptance_capacity_impl
from backend.services.auth_organization_plan_backend import ensure_invitation_capacity as _ensure_invitation_capacity_impl
from backend.services.auth_organization_plan_backend import get_organization_invitation_dashboard as _get_organization_invitation_dashboard_impl
from backend.services.auth_organization_plan_backend import get_organization_plan_summary as _get_organization_plan_summary_impl
from backend.services.auth_member_directory_backend import build_legacy_local_user_row as _build_legacy_local_user_row_impl
from backend.services.auth_member_directory_backend import list_local_users as _list_local_users_impl
from backend.services.auth_member_directory_backend import list_local_users_overview as _list_local_users_overview_impl
from backend.services.auth_member_directory_backend import list_organization_audit_logs as _list_organization_audit_logs_impl
from backend.services.auth_member_directory_backend import normalize_local_user_row as _normalize_local_user_row_impl
from backend.services.auth_member_directory_backend import query_local_user_rows as _query_local_user_rows_impl
from backend.services.auth_local_bootstrap_backend import bootstrap_local_auth_path as _bootstrap_local_auth_path_impl
from backend.services.auth_local_bootstrap_backend import build_invitation_initial_password as _build_invitation_initial_password_impl
from backend.services.auth_local_bootstrap_backend import build_invite_url as _build_invite_url_impl
from backend.services.auth_local_bootstrap_backend import build_local_bootstrap_session as _build_local_bootstrap_session_impl
from backend.services.auth_local_bootstrap_backend import can_use_local_bootstrap_fallback as _can_use_local_bootstrap_fallback_impl
from backend.services.auth_local_bootstrap_backend import hash_local_bootstrap_password as _hash_local_bootstrap_password_impl
from backend.services.auth_local_bootstrap_backend import has_local_bootstrap_password as _has_local_bootstrap_password_impl
from backend.services.auth_local_bootstrap_backend import load_local_bootstrap_auth_record as _load_local_bootstrap_auth_record_impl
from backend.services.auth_local_bootstrap_backend import local_bootstrap_auth_user_id as _local_bootstrap_auth_user_id_impl
from backend.services.auth_local_bootstrap_backend import register_local_bootstrap_password as _register_local_bootstrap_password_impl
from backend.services.auth_local_bootstrap_backend import resolve_local_bootstrap_auth_user_id as _resolve_local_bootstrap_auth_user_id_impl
from backend.services.auth_local_bootstrap_backend import save_local_bootstrap_auth_record as _save_local_bootstrap_auth_record_impl
from backend.services.auth_local_bootstrap_backend import verify_local_bootstrap_password as _verify_local_bootstrap_password_impl
from backend.services.auth_session_backend import build_session_response_payload as _build_session_response_payload_impl
from backend.services.auth_session_cookie_backend import decode_signed_payload as _decode_signed_payload_impl
from backend.services.auth_session_cookie_backend import encode_signed_payload as _encode_signed_payload_impl
from backend.services.auth_session_cookie_backend import read_access_token_expires_in as _read_access_token_expires_in_impl

SESSION_COOKIE_NAME = "tracker_auth_session"
SESSION_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 30
SESSION_REFRESH_GRACE_SECONDS = 60
PROFILE_RECHECK_TTL_SECONDS = 60 * 5
LOCAL_BOOTSTRAP_AUTH_FILE = ".tmp-auth-server/bootstrap-local-auth.json"

DEFAULT_BOOTSTRAP_ORG_NAME = "(주)파노텍"
DEFAULT_BOOTSTRAP_ORG_SLUG = "internal-ops"

logger = logging.getLogger(__name__)

# Runtime-bound globals are injected by backend.api.auth_runtime at import time.

def sign_out_session(session_payload: dict[str, Any] | None) -> None:
    if not session_payload:
        return
    access_token = str(session_payload.get("access_token") or "").strip()
    if not access_token:
        return
    try:
        _auth_request(
            "POST",
            "/logout",
            access_token=access_token,
            use_service_authorization=False,
        )
    except AuthRuntimeError:
        return

def build_session_response_payload(session_payload: dict[str, Any]) -> dict[str, Any]:
    return _build_session_response_payload_impl(
        session_payload=session_payload,
        build_auth_status_response_fn=build_auth_status_response,
    )

def sign_in_with_password(*, email: str, password: str, invite_token: str = "", request_host: str = "") -> dict[str, Any]:
    return _sign_in_with_password_impl(
        email=email,
        password=password,
        invite_token=invite_token,
        request_host=request_host,
        ensure_auth_enabled=_ensure_auth_enabled,
        normalize_email_fn=_normalize_email,
        can_use_local_bootstrap_fallback_fn=_can_use_local_bootstrap_fallback,
        has_local_bootstrap_password_fn=_has_local_bootstrap_password,
        verify_local_bootstrap_password_fn=_verify_local_bootstrap_password,
        build_local_bootstrap_session_fn=_build_local_bootstrap_session,
        auth_request_fn=_auth_request,
        finalize_session_payload_fn=_finalize_session_payload,
        resolve_pending_invitation_token_for_email_fn=_resolve_pending_invitation_token_for_email,
        require_invitation_email_match_fn=_require_invitation_email_match,
        accept_invitation_for_session_payload_fn=accept_invitation_for_session_payload,
        touch_last_login_fn=_touch_last_login,
        error_cls=AuthRuntimeError,
        local_bootstrap_sign_in_message="濡쒖뺄 bootstrap 濡쒓렇?몄쑝濡?吏꾩엯?덉뒿?덈떎.",
        local_bootstrap_invalid_password_message="濡쒖뺄 bootstrap 鍮꾨?踰덊샇媛 ?쇱튂?섏? ?딆뒿?덈떎.",
        local_bootstrap_missing_password_message="??PC?먯꽌??理쒖큹 ?댁쁺???깅줉 ??뿉??濡쒖뺄 鍮꾨?踰덊샇瑜?癒쇱? ?깅줉?댁빞 ?⑸땲??",
    )

def record_login_audit_log(*, request: Request, session_payload: dict[str, Any]) -> None:
    if not bool(session_payload.get("authorized")):
        return

    organization_id = _parse_uuid(session_payload.get("organization_id"))
    user_id = _parse_uuid(session_payload.get("local_user_id")) or _parse_uuid(session_payload.get("auth_user_id"))
    user_email = _normalize_email(session_payload.get("email"))
    user_role = str(session_payload.get("role") or "").strip()
    if organization_id is None or user_id is None or not user_email or not user_role:
        return

    ip_address = _resolve_login_audit_log_ip_address(request)
    user_agent = _resolve_login_audit_log_user_agent(request)
    try:
        repository = get_login_audit_log_repository()
        repository.create_log(
            organization_id=organization_id,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception as exc:
        logger.warning(
            "login_audit_log_write_failed organization_id=%s user_id=%s user_email=%s user_role=%s ip_address=%s user_agent=%s error=%s",
            organization_id,
            user_id,
            user_email,
            user_role,
            ip_address,
            user_agent,
            str(exc),
        )

def sign_up_console_user(*, email: str, password: str, display_name: str = "", invite_token: str = "", request_host: str = "") -> dict[str, Any]:
    return _sign_up_console_user_impl(
        email=email,
        password=password,
        display_name=display_name,
        invite_token=invite_token,
        request_host=request_host,
        ensure_auth_enabled=_ensure_auth_enabled,
        normalize_email_fn=_normalize_email,
        bootstrap_platform_admin_email_fn=bootstrap_platform_admin_email,
        resolve_pending_invitation_token_for_email_fn=_resolve_pending_invitation_token_for_email,
        require_invitation_email_match_fn=_require_invitation_email_match,
        can_use_local_bootstrap_fallback_fn=_can_use_local_bootstrap_fallback,
        register_local_bootstrap_password_fn=_register_local_bootstrap_password,
        build_local_bootstrap_session_fn=_build_local_bootstrap_session,
        auth_request_fn=_auth_request,
        is_existing_auth_user_error_fn=_is_existing_auth_user_error,
        sign_in_with_password_fn=sign_in_with_password,
        ensure_bootstrap_local_user_fn=_ensure_bootstrap_local_user,
        ensure_member_local_user_fn=_ensure_member_local_user,
        finalize_session_payload_fn=_finalize_session_payload,
        current_time_fn=time.time,
        error_cls=AuthRuntimeError,
        local_bootstrap_sign_up_message="濡쒖뺄 bootstrap 怨꾩젙???깅줉?덉뒿?덈떎.",
    )

def send_password_reset_email(*, email: str, request_host: str = "") -> dict[str, Any]:
    return _send_password_reset_email_impl(
        email=email,
        request_host=request_host,
        ensure_auth_enabled=_ensure_auth_enabled,
        normalize_email_fn=_normalize_email,
        can_use_local_bootstrap_fallback_fn=_can_use_local_bootstrap_fallback,
        auth_request_fn=_auth_request,
        error_cls=AuthRuntimeError,
        local_bootstrap_reset_message="\uc624\ud504\ub77c\uc778 \uac1c\ubc1c\ud658\uacbd bootstrap \uacc4\uc815\uc740 '\ucd5c\ucd08 \uc6b4\uc601\uc790 \ub4f1\ub85d'\uc5d0\uc11c \uac19\uc740 \uc774\uba54\uc77c\ub85c \uc0c8 \ube44\ubc00\ubc88\ud638\ub97c \ub2e4\uc2dc \uc124\uc815\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
        password_reset_sent_message="鍮꾨?踰덊샇 ?ъ꽕??硫붿씪??蹂대깉?듬땲?? 硫붿씪?⑥쓣 ?뺤씤?섏꽭??",
    )

def create_platform_admin_account(
    *,
    actor_user_id: str,
    actor_role: str,
    organization_id: str,
    email: str,
    password: str,
    display_name: str,
    role: str,
) -> dict[str, Any]:
    return _create_platform_admin_account_impl(
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        organization_id=organization_id,
        email=email,
        password=password,
        display_name=display_name,
        role=role,
        create_auth_user_fn=_create_supabase_auth_user,
        get_user_profile_fn=_get_user_profile,
        list_local_users_fn=list_local_users,
        ensure_user_profile_fn=_ensure_user_profile,
        ensure_membership_fn=_ensure_membership,
        append_audit_log_fn=_append_audit_log,
        cleanup_local_account_fn=_cleanup_local_account,
        delete_auth_user_fn=_delete_supabase_auth_user,
        warn_fn=logger.warning,
        normalize_email_fn=_normalize_email,
        normalize_org_role_fn=_normalize_org_role,
        auth_error_cls=AuthRuntimeError,
    )

def reset_platform_admin_account_password(
    *,
    actor_user_id: str,
    actor_role: str,
    organization_id: str,
    user_id: str,
    email: str,
    password: str,
) -> dict[str, Any]:
    return _reset_platform_admin_account_password_with_context(
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        organization_id=organization_id,
        user_id=user_id,
        email=email,
        password=password,
    )

def ensure_fresh_session_payload(request: Request, response: Response) -> dict[str, Any]:
    return _ensure_fresh_session_payload_impl(
        payload=read_signed_session_payload(request),
        response=response,
        ensure_auth_enabled=_ensure_auth_enabled,
        now=int(time.time()),
        grace_seconds=SESSION_REFRESH_GRACE_SECONDS,
        refresh_auth_session_fn=refresh_auth_session,
        clear_auth_session_cookie_fn=clear_auth_session_cookie,
        set_auth_session_cookie_fn=set_auth_session_cookie,
        error_cls=AuthRuntimeError,
        logger=logger,
        session_refresh_timeout_seconds_fn=_session_refresh_timeout_seconds,
    )

def update_console_user_profile(
    *,
    session_payload: dict[str, Any],
    display_name: str,
    mobile_phone: str = "",
    office_phone: str = "",
    current_password: str = "",
    password: str = "",
    invite_token: str = "",
) -> dict[str, Any]:
    return _update_console_user_profile_impl(
        session_payload=session_payload,
        display_name=display_name,
        mobile_phone=mobile_phone,
        office_phone=office_phone,
        current_password=current_password,
        password=password,
        invite_token=invite_token,
        ensure_auth_enabled=_ensure_auth_enabled,
        normalize_email_fn=_normalize_email,
        verify_local_bootstrap_password_fn=_verify_local_bootstrap_password,
        can_use_invite_password_setup_fn=_can_use_invite_password_setup,
        register_local_bootstrap_password_fn=_register_local_bootstrap_password,
        update_local_user_profile_fn=_update_local_user_profile,
        build_local_bootstrap_session_fn=_build_local_bootstrap_session,
        verify_password_fn=_verify_password,
        auth_request_fn=_auth_request,
        finalize_session_payload_fn=_finalize_session_payload,
        current_time_fn=time.time,
        error_cls=AuthRuntimeError,
        current_password_mismatch_message="?꾩옱 鍮꾨?踰덊샇媛 ?쇱튂?섏? ?딆뒿?덈떎.",
    )

def build_session_response(
    request: Request,
    response: Response,
) -> dict[str, Any]:
    return _build_session_response_impl(
        payload=read_signed_session_payload(request),
        response=response,
        now=int(time.time()),
        grace_seconds=SESSION_REFRESH_GRACE_SECONDS,
        refresh_auth_session_fn=refresh_auth_session,
        clear_auth_session_cookie_fn=clear_auth_session_cookie,
        set_auth_session_cookie_fn=set_auth_session_cookie,
        build_auth_status_response_fn=build_auth_status_response,
        build_session_response_payload_fn=build_session_response_payload,
        error_cls=AuthRuntimeError,
        logger=logger,
        session_refresh_timeout_seconds_fn=_session_refresh_timeout_seconds,
        refresh_failure_message="세션이 만료되었습니다. 다시 로그인해 주세요.",
    )

def refresh_auth_session(refresh_token: str, *, timeout_seconds: float | None = None) -> dict[str, Any]:
    return _refresh_auth_session_impl(
        refresh_token,
        timeout_seconds=timeout_seconds,
        auth_request_fn=_auth_request,
        finalize_session_payload_fn=_finalize_session_payload,
    )

def import_auth_session(*, access_token: str, refresh_token: str = "") -> dict[str, Any]:
    _ensure_auth_enabled()
    normalized_access_token = str(access_token or "").strip()
    normalized_refresh_token = str(refresh_token or "").strip()
    if not normalized_access_token:
        raise AuthRuntimeError("access token is required", status_code=400, code="validation_error")
    user = _auth_request(
        "GET",
        "/user",
        access_token=normalized_access_token,
        use_service_authorization=False,
    )
    return _finalize_session_payload(
        {
            "user": user,
            "access_token": normalized_access_token,
            "refresh_token": normalized_refresh_token,
            "expires_in": _read_access_token_expires_in(normalized_access_token),
        }
    )

def set_auth_session_cookie(response: Response, session_payload: dict[str, Any]) -> None:
    signed_payload = _encode_signed_payload(session_payload)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        signed_payload,
        httponly=True,
        max_age=SESSION_COOKIE_MAX_AGE_SECONDS,
        samesite="lax",
        secure=False,
        path="/",
    )

def clear_auth_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/", samesite="lax")

def read_signed_session_payload(request: Request) -> dict[str, Any] | None:
    signed_value = str(request.cookies.get(SESSION_COOKIE_NAME) or "").strip()
    if not signed_value:
        return None
    try:
        payload = _decode_signed_payload(signed_value)
    except AuthRuntimeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload

def _read_authorization_bearer_token(request: Request) -> str:
    header_value = str(request.headers.get("authorization") or "").strip()
    if not header_value:
        return ""
    scheme, _, token = header_value.partition(" ")
    if scheme.lower() != "bearer":
        return ""
    return str(token or "").strip()

def _read_bearer_session_payload(request: Request) -> dict[str, Any] | None:
    access_token = _read_authorization_bearer_token(request)
    if not access_token:
        return None
    try:
        user = _auth_request(
            "GET",
            "/user",
            access_token=access_token,
            use_service_authorization=False,
        )
    except AuthRuntimeError:
        return None
    try:
        return _finalize_session_payload(
            {
                "user": user,
                "access_token": access_token,
                "refresh_token": "",
                "expires_in": _read_access_token_expires_in(access_token),
            }
        )
    except AuthRuntimeError:
        return None

def read_auth_context(request: Request) -> AuthContext | None:
    payload = read_signed_session_payload(request)
    if payload is None:
        payload = _read_bearer_session_payload(request)
    if payload is None:
        return None
    if int(payload.get("access_expires_at") or 0) <= int(time.time()):
        return None
    auth_user_id = _parse_uuid(payload.get("auth_user_id"))
    if auth_user_id is None:
        return None
    local_user_id = _parse_uuid(payload.get("local_user_id"))
    membership_id = _parse_uuid(payload.get("membership_id"))
    email = str(payload.get("email") or "")
    if int(payload.get("profile_checked_at") or 0) > int(time.time()) - PROFILE_RECHECK_TTL_SECONDS:
        return AuthContext(
            auth_user_id=auth_user_id,
            local_user_id=local_user_id,
            membership_id=membership_id,
            email=email,
            display_name=str(payload.get("display_name") or ""),
            role=str(payload.get("role") or ""),
            organization_id=_parse_uuid(payload.get("organization_id")),
            organization_name=str(payload.get("organization_name") or ""),
            account_status=str(payload.get("account_status") or "active"),
            membership_status=str(payload.get("membership_status") or "active"),
            authorized=bool(payload.get("authorized")),
            access_expires_at=int(payload.get("access_expires_at") or 0),
        )
    if local_user_id is not None or email:
        local_user = _get_local_user(
            user_id=str(local_user_id or ""),
            email=email,
            organization_id=str(payload.get("organization_id") or ""),
        )
        if payload.get("authorized") and local_user is None:
            return None
        if local_user is not None and str(local_user.get("status") or "active") != "active":
            return None
        if local_user is not None:
            local_user_id = _parse_uuid(local_user.get("id")) or local_user_id
            membership_id = _parse_uuid(local_user.get("membership_id")) or membership_id
            organization_id = _parse_uuid(local_user.get("organization_id")) or _parse_uuid(payload.get("organization_id"))
            organization_name = str(local_user.get("organization_name") or payload.get("organization_name") or "")
            role = str(local_user.get("role") or payload.get("role") or "")
            if str(payload.get("role") or "") == "platform_admin" or str(local_user.get("global_role") or "") == "platform_admin":
                role = "platform_admin"
            return AuthContext(
                auth_user_id=auth_user_id,
                local_user_id=local_user_id,
                membership_id=membership_id,
                email=email,
                display_name=str(payload.get("display_name") or ""),
                role=role,
                organization_id=organization_id,
                organization_name=organization_name,
                account_status=str(local_user.get("account_status") or payload.get("account_status") or "active"),
                membership_status=str(local_user.get("membership_status") or payload.get("membership_status") or "active"),
                authorized=bool(payload.get("authorized")),
                access_expires_at=int(payload.get("access_expires_at") or 0),
            )
    return AuthContext(
        auth_user_id=auth_user_id,
        local_user_id=local_user_id,
        membership_id=membership_id,
        email=email,
        display_name=str(payload.get("display_name") or ""),
        role=str(payload.get("role") or ""),
        organization_id=_parse_uuid(payload.get("organization_id")),
        organization_name=str(payload.get("organization_name") or ""),
        account_status=str(payload.get("account_status") or "active"),
        membership_status=str(payload.get("membership_status") or "active"),
        authorized=bool(payload.get("authorized")),
        access_expires_at=int(payload.get("access_expires_at") or 0),
    )

def _finalize_session_payload(token_payload: dict[str, Any]) -> dict[str, Any]:
    user = token_payload.get("user")
    if not isinstance(user, dict):
        raise AuthRuntimeError("Supabase auth response did not include a user", status_code=502, code="auth_invalid")
    auth_user_id = str(user.get("id") or "").strip()
    email = _normalize_email(user.get("email"))
    if not auth_user_id or not email:
        raise AuthRuntimeError("Supabase auth response did not include user id/email", status_code=502, code="auth_invalid")

    display_name = _resolve_display_name(user)
    app_profile = _resolve_application_profile(auth_user=user, email=email, display_name=display_name)
    expires_in = int(token_payload.get("expires_in") or 3600)
    access_expires_at = int(time.time()) + max(60, expires_in)

    payload = {
        "auth_user_id": auth_user_id,
        "email": email,
        "display_name": display_name,
        "role": app_profile["role"],
        "authorized": app_profile["authorized"],
        "organization_id": app_profile.get("organization_id"),
        "organization_name": app_profile.get("organization_name", ""),
        "local_user_id": app_profile.get("local_user_id"),
        "membership_id": app_profile.get("membership_id"),
        "status": app_profile.get("status", "active"),
        "account_status": app_profile.get("account_status", "active"),
        "membership_status": app_profile.get("membership_status", "active"),
        "mobile_phone": app_profile.get("mobile_phone", ""),
        "office_phone": app_profile.get("office_phone", ""),
        "message": app_profile.get("message", ""),
        "access_token": str(token_payload.get("access_token") or ""),
        "refresh_token": str(token_payload.get("refresh_token") or ""),
        "access_expires_at": access_expires_at,
        "profile_checked_at": int(time.time()),
    }
    return payload

def _resolve_login_audit_log_ip_address(request: Request) -> str:
    forwarded_for = str(request.headers.get("x-forwarded-for", "") or "").split(",")[0].strip()
    if forwarded_for:
        return forwarded_for
    real_ip = str(request.headers.get("x-real-ip", "") or "").strip()
    if real_ip:
        return real_ip
    client = getattr(request, "client", None)
    return str(getattr(client, "host", "") or "").strip()

def _resolve_login_audit_log_user_agent(request: Request) -> str:
    return str(request.headers.get("user-agent", "") or "").strip()
