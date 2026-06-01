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

def accept_invitation_for_session_payload(*, session_payload: dict[str, Any], invite_token: str) -> dict[str, Any]:
    auth_user_id = str(session_payload.get("auth_user_id") or "").strip()
    email = _normalize_email(session_payload.get("email"))
    display_name = str(session_payload.get("display_name") or "").strip()
    if not auth_user_id or not email:
        raise AuthRuntimeError("valid authenticated session is required", status_code=401, code="auth_required")
    normalized_invite_token = _resolve_session_invitation_token(
        invite_token=str(invite_token or "").strip(),
        auth_user_id=auth_user_id,
        email=email,
    )
    invitation = _get_invitation_by_token(normalized_invite_token)
    if invitation is None:
        raise AuthRuntimeError("invitation not found", status_code=404, code="invite_not_found")
    accepted_user_id = str(invitation.get("accepted_user_id") or "").strip()
    if accepted_user_id and accepted_user_id != auth_user_id:
        raise AuthRuntimeError("invitation already belongs to another account", status_code=409, code="invite_already_claimed")
    _require_invitation_email_match(invite_token=normalized_invite_token, email=email)
    _ensure_user_profile(
        user_id=auth_user_id,
        email=email,
        display_name=display_name or email.split("@", 1)[0],
        account_status="active",
    )
    _ensure_acceptance_capacity(
        organization_id=str(invitation.get("organization_id") or ""),
        auth_user_id=auth_user_id,
        email=email,
    )
    try:
        result, _headers = request_json(
            rest_url=_rest_base_url(),
            api_key=_service_api_key(),
            timeout_seconds=_timeout_seconds(),
            method="POST",
            path="/rpc/accept_invitation",
            payload={
                "p_invite_token": normalized_invite_token,
                "p_user_profile_id": auth_user_id,
                "p_email": email,
                "p_display_name": display_name,
            },
            error_cls=AuthRuntimeError,
        )
    except AuthRuntimeError as exc:
        _raise_accept_invitation_error(
            exc=exc,
            invitation_id=str(invitation.get("id") or "").strip(),
        )
    accepted = None
    if isinstance(result, list) and result:
        accepted = dict(result[0])
    elif isinstance(result, dict):
        accepted = dict(result)
    if accepted is not None:
        _append_audit_log(
            organization_id=str(accepted.get("organization_id") or ""),
            actor_user_id=auth_user_id,
            actor_membership_id=str(accepted.get("membership_id") or ""),
            event_type="invite_accepted",
            target_type="invitation",
            target_id=str(accepted.get("invitation_id") or ""),
            payload={
                "email": email,
                "organization_name": str(accepted.get("organization_name") or ""),
            },
        )
    _touch_last_login(auth_user_id=auth_user_id)
    return _finalize_session_payload(
        {
            "user": {
                "id": auth_user_id,
                "email": email,
                "user_metadata": {"display_name": display_name},
            },
            "access_token": str(session_payload.get("access_token") or ""),
            "refresh_token": str(session_payload.get("refresh_token") or ""),
            "expires_in": max(60, int(session_payload.get("access_expires_at") or 0) - int(time.time())),
        }
    )

def _raise_accept_invitation_error(*, exc: AuthRuntimeError, invitation_id: str) -> None:
    _raise_accept_invitation_error_invite_impl(
        exc=exc,
        invitation_id=invitation_id,
        persist_invitation_status_fn=_persist_invitation_status,
        auth_error_cls=AuthRuntimeError,
    )

def _resolve_session_invitation_token(*, invite_token: str, auth_user_id: str, email: str) -> str:
    return _resolve_session_invitation_token_impl(
        invite_token=invite_token,
        auth_user_id=auth_user_id,
        email=email,
        list_pending_invitations_by_email_fn=_list_pending_invitations_by_email,
        auth_error_cls=AuthRuntimeError,
    )

def _resolve_pending_invitation_token_for_email(
    *,
    email: str,
    invite_token: str = "",
    required: bool = False,
) -> str:
    return _resolve_pending_invitation_token_for_email_impl(
        email=email,
        invite_token=invite_token,
        required=required,
        list_pending_invitations_by_email_fn=_list_pending_invitations_by_email,
        auth_error_cls=AuthRuntimeError,
    )

def _list_pending_invitations_by_email(*, email: str) -> list[dict[str, Any]]:
    return _list_pending_invitations_by_email_impl(
        email=email,
        normalize_email=_normalize_email,
        request_json=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        normalize_invitation_row=_normalize_invitation_row,
        auth_error_cls=AuthRuntimeError,
    )

def list_invitations(*, organization_id: str, include_non_pending: bool = True) -> list[dict[str, Any]]:
    return _list_invitations_impl(
        organization_id=organization_id,
        include_non_pending=include_non_pending,
        expire_stale_invitations=_expire_stale_invitations,
        request_json=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        normalize_invitation_row=_normalize_invitation_row,
        auth_error_cls=AuthRuntimeError,
    )

def get_invitation_preview(*, invite_token: str) -> dict[str, Any]:
    return _get_invitation_preview_impl(
        invite_token=invite_token,
        get_invitation_by_token=_get_invitation_by_token,
        get_organization=_get_organization,
        build_invitation_initial_password=_build_invitation_initial_password,
        auth_error_cls=AuthRuntimeError,
    )

def get_invitation_preview_by_email(*, email: str) -> dict[str, Any]:
    return _get_invitation_preview_by_email_impl(
        email=email,
        list_pending_invitations_by_email=_list_pending_invitations_by_email,
        get_organization=_get_organization,
        auth_error_cls=AuthRuntimeError,
    )

def _counts_towards_active_user_limit(item: dict[str, Any]) -> bool:
    return _counts_towards_active_user_limit_impl(
        item=item,
        normalize_global_role=_normalize_global_role,
        normalize_account_status=_normalize_account_status,
        normalize_membership_status=_normalize_membership_status,
    )

def _build_plan_upgrade_message(
    *,
    plan_code: str,
    active_user_limit: int,
    pending_invite_limit: int,
    active_user_limit_reached: bool,
    pending_invite_limit_reached: bool,
) -> str:
    return _build_plan_upgrade_message_impl(
        plan_code=plan_code,
        active_user_limit=active_user_limit,
        pending_invite_limit=pending_invite_limit,
        active_user_limit_reached=active_user_limit_reached,
        pending_invite_limit_reached=pending_invite_limit_reached,
        resolve_next_plan_code=_resolve_next_plan_code,
        organization_plan_limits=ORGANIZATION_PLAN_LIMITS,
    )

def _build_organization_plan_summary(
    *,
    organization: dict[str, Any],
    members: list[dict[str, Any]],
    pending_invitations: list[dict[str, Any]],
) -> dict[str, Any]:
    return _build_organization_plan_summary_impl(
        organization=organization,
        members=members,
        pending_invitations=pending_invitations,
        normalize_plan_code=_normalize_plan_code,
        normalize_limit_value=_normalize_limit_value,
        counts_towards_active_user_limit=_counts_towards_active_user_limit,
        build_plan_upgrade_message=_build_plan_upgrade_message,
        resolve_next_plan_code=_resolve_next_plan_code,
        organization_plan_limits=ORGANIZATION_PLAN_LIMITS,
    )

def get_organization_plan_summary(*, organization_id: str) -> dict[str, Any]:
    return _get_organization_plan_summary_impl(
        organization_id=organization_id,
        get_organization=_get_organization,
        list_local_users=list_local_users,
        list_invitations=list_invitations,
        build_organization_plan_summary=_build_organization_plan_summary,
        auth_error_cls=AuthRuntimeError,
    )

def get_organization_invitation_dashboard(*, organization_id: str, actor_role: str) -> dict[str, Any]:
    return _get_organization_invitation_dashboard_impl(
        organization_id=organization_id,
        actor_role=actor_role,
        get_organization=_get_organization,
        list_local_users=list_local_users,
        list_invitations=list_invitations,
        build_organization_plan_summary=_build_organization_plan_summary,
        filter_manageable_invitations=_filter_manageable_invitations,
        auth_error_cls=AuthRuntimeError,
    )

def list_organization_audit_logs(*, organization_id: str, limit: int = 20) -> list[dict[str, Any]]:
    return _list_organization_audit_logs_impl(
        organization_id=organization_id,
        limit=limit,
        get_organization=_get_organization,
        request_json_fn=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        error_cls=AuthRuntimeError,
        audit_log_select_columns=AUDIT_LOG_SELECT_COLUMNS,
        list_local_users=list_local_users,
    )

def _resolve_allowed_invitation_roles(actor_role: str) -> tuple[str, ...]:
    return _resolve_allowed_invitation_roles_impl(actor_role)

def _validate_invitation_permissions(*, actor_role: str, role: str) -> str:
    return _validate_invitation_permissions_impl(
        actor_role=actor_role,
        role=role,
        normalize_org_role=_normalize_org_role,
        auth_error_cls=AuthRuntimeError,
    )

def _can_manage_invitation_role(*, actor_role: str, target_role: str) -> bool:
    return _can_manage_invitation_role_impl(actor_role=actor_role, target_role=target_role)

def _filter_manageable_invitations(
    *,
    actor_role: str,
    invitations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return _filter_manageable_invitations_impl(actor_role=actor_role, invitations=invitations)

def _ensure_invitation_capacity(*, organization_id: str) -> dict[str, Any]:
    return _ensure_invitation_capacity_impl(
        organization_id=organization_id,
        get_organization_plan_summary=get_organization_plan_summary,
        auth_error_cls=AuthRuntimeError,
    )

def _ensure_acceptance_capacity(*, organization_id: str, auth_user_id: str, email: str) -> None:
    return _ensure_acceptance_capacity_impl(
        organization_id=organization_id,
        auth_user_id=auth_user_id,
        email=email,
        get_user_profile=_get_user_profile,
        get_membership_row=_get_membership_row,
        counts_towards_active_user_limit=_counts_towards_active_user_limit,
        get_organization_plan_summary=get_organization_plan_summary,
        normalize_global_role=_normalize_global_role,
        auth_error_cls=AuthRuntimeError,
    )

def create_invitation(
    *,
    organization_id: str,
    created_by: str,
    actor_role: str,
    email: str,
    role: str,
    display_name: str = "",
    team_name: str = "",
    job_title: str = "",
    expires_in_days: int = 7,
    invite_url_base: str = "",
    send_email: bool = True,
) -> dict[str, Any]:
    item = _create_invitation_impl(
        organization_id=organization_id,
        created_by=created_by,
        actor_role=actor_role,
        email=email,
        role=role,
        display_name=display_name,
        team_name=team_name,
        job_title=job_title,
        expires_in_days=expires_in_days,
        invite_url_base=invite_url_base,
        send_email=send_email,
        normalize_email=_normalize_email,
        normalize_org_role=_normalize_org_role,
        request_json=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        normalize_invitation_row=_normalize_invitation_row,
        build_invite_url=_build_invite_url,
        build_invitation_initial_password=_build_invitation_initial_password,
        append_audit_log=_append_audit_log,
        send_invitation_email=_send_invitation_email,
        format_invitation_delivery_error=_format_invitation_delivery_error,
        get_organization_plan_summary=get_organization_plan_summary,
        auth_error_cls=AuthRuntimeError,
    )
    if not send_email:
        if str(item.get("delivery_status") or "").strip().lower() in {"", "queued"}:
            item["delivery_status"] = "manual"
            item["delivery_message"] = (
                "자동 초대 메일 발송은 현재 비활성화되어 있습니다. "
                "초대 링크와 초기 암호를 복사해 직접 전달하세요."
            )
        else:
            item.setdefault("delivery_status", "manual")
            item.setdefault(
                "delivery_message",
                "자동 초대 메일 발송은 현재 비활성화되어 있습니다. "
                "초대 링크와 초기 암호를 복사해 직접 전달하세요.",
            )
    return item

def _raise_create_invitation_error(*, exc: AuthRuntimeError, organization_id: str) -> None:
    _raise_create_invitation_error_impl(
        exc=exc,
        organization_id=organization_id,
        get_organization_plan_summary=get_organization_plan_summary,
        auth_error_cls=AuthRuntimeError,
    )

def _expire_stale_invitations(*, organization_id: str, email: str = "") -> None:
    _expire_stale_invitations_impl(
        organization_id=organization_id,
        email=email,
        normalize_email=_normalize_email,
        request_json=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        parse_datetime_value=_parse_datetime_value,
        persist_invitation_status_fn=_persist_invitation_status,
        auth_error_cls=AuthRuntimeError,
    )

def _persist_invitation_status(*, invitation_id: str, status: str) -> None:
    _persist_invitation_status_impl(
        invitation_id=invitation_id,
        status=status,
        request_json=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        auth_error_cls=AuthRuntimeError,
    )

def revoke_invitation(*, organization_id: str, invitation_id: str, actor_user_id: str, actor_role: str) -> dict[str, Any]:
    return _revoke_invitation_impl(
        organization_id=organization_id,
        invitation_id=invitation_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        get_invitation_by_id=_get_invitation_by_id,
        request_json=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        normalize_invitation_row=_normalize_invitation_row,
        append_audit_log=_append_audit_log,
        auth_error_cls=AuthRuntimeError,
    )

def deliver_invitation_email(*, email: str, invite_url: str, display_name: str = "") -> None:
    _deliver_invitation_email_impl(
        email=email,
        invite_url=invite_url,
        display_name=display_name,
        invitation_email_delivery_enabled=invitation_email_delivery_enabled,
        send_invitation_email=_send_invitation_email,
        normalize_email=_normalize_email,
        logger=logger,
    )

def _get_invitation_by_token(invite_token: str) -> dict[str, Any] | None:
    return _get_invitation_by_token_impl(
        invite_token,
        request_json=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        normalize_invitation_row=_normalize_invitation_row,
        persist_invitation_status=_persist_invitation_status,
        auth_error_cls=AuthRuntimeError,
    )

def _get_invitation_by_id(*, organization_id: str, invitation_id: str) -> dict[str, Any] | None:
    return _get_invitation_by_id_impl(
        organization_id=organization_id,
        invitation_id=invitation_id,
        request_json=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        normalize_invitation_row=_normalize_invitation_row,
        auth_error_cls=AuthRuntimeError,
    )

def _require_invitation_email_match(*, invite_token: str, email: str) -> None:
    _require_invitation_email_match_impl(
        invite_token=invite_token,
        email=email,
        normalize_email_fn=_normalize_email,
        get_invitation_by_token_fn=_get_invitation_by_token,
        auth_error_cls=AuthRuntimeError,
    )

def _can_use_invite_password_setup(*, auth_user_id: str, email: str, invite_token: str) -> bool:
    return _can_use_invite_password_setup_impl(
        auth_user_id=auth_user_id,
        email=email,
        invite_token=invite_token,
        normalize_email_fn=_normalize_email,
        get_invitation_by_token_fn=_get_invitation_by_token,
        parse_datetime_value_fn=_parse_datetime_value,
    )

def _send_invitation_email(*, email: str, invite_url: str, display_name: str = "") -> None:
    normalized_email = _normalize_email(email)
    if not normalized_email:
        raise AuthRuntimeError("email is required", status_code=400, code="validation_error")
    payload: dict[str, Any] = {
        "email": normalized_email,
        "data": {"display_name": str(display_name or "").strip()},
        "redirect_to": str(invite_url or "").strip(),
    }
    _auth_request(
        "POST",
        "/invite",
        payload=payload,
        use_service_authorization=True,
    )

def _format_invitation_delivery_error(message: str) -> str:
    lowered = str(message or "").lower()
    if "over_email_send_rate_limit" in lowered or "email rate limit exceeded" in lowered:
        return "초대 메일 발송 제한에 걸렸습니다. 잠시 후 다시 시도하거나 링크 복사로 직접 전달하세요."
    if "smtp" in lowered:
        return "초대 메일 발송 설정이 준비되지 않았습니다. 링크 복사로 직접 전달하세요."
    return "초대 메일을 자동 발송하지 못했습니다. 링크 복사로 직접 전달하세요."

def _verify_password(*, email: str, password: str) -> None:
    try:
        _auth_request(
            "POST",
            "/token",
            query=[("grant_type", "password")],
            payload={"email": _normalize_email(email), "password": str(password or "")},
            use_service_authorization=False,
        )
    except AuthRuntimeError as exc:
        raise AuthRuntimeError("현재 비밀번호가 일치하지 않습니다.", status_code=400, code="validation_error") from exc
