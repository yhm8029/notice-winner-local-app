from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
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
from backend.api.support.auth_runtime_directory_audit_helpers import append_audit_log as _append_audit_log_helper
from backend.api.support.auth_runtime_directory_audit_helpers import touch_last_login as _touch_last_login_helper
from backend.api.support.auth_runtime_directory_membership_helpers import cleanup_local_account as _cleanup_local_account_helper
from backend.api.support.auth_runtime_directory_membership_helpers import delete_local_user_account as _delete_local_user_account_helper
from backend.api.support.auth_runtime_directory_membership_helpers import update_local_user_status as _update_local_user_status_helper
from backend.api.support.auth_runtime_directory_membership_helpers import update_organization_membership as _update_organization_membership_helper
from backend.api.support.auth_runtime_directory_profile_helpers import ensure_bootstrap_local_user as _ensure_bootstrap_local_user_helper
from backend.api.support.auth_runtime_directory_profile_helpers import ensure_member_local_user as _ensure_member_local_user_helper
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

def list_local_users(*, organization_id: str, include_inactive: bool = False) -> list[dict[str, Any]]:
    return _list_local_users_impl(
        organization_id=organization_id,
        include_inactive=include_inactive,
        query_local_user_rows=_query_local_user_rows,
        normalize_local_user_row=_normalize_local_user_row,
    )

def list_local_users_overview(*, organization_id: str) -> list[dict[str, Any]]:
    return _list_local_users_overview_impl(
        organization_id=organization_id,
        request_json_fn=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        error_cls=AuthRuntimeError,
        membership_overview_select_columns=MEMBERSHIP_OVERVIEW_SELECT_COLUMNS,
        is_missing_relation_error=_is_missing_relation_error,
        normalize_local_user_row=_normalize_local_user_row,
        list_local_users=list_local_users,
    )

def update_local_user_status(*, organization_id: str, user_id: str, status: str) -> dict[str, Any]:
    return _update_local_user_status_helper(
        organization_id=organization_id,
        user_id=user_id,
        status=status,
        normalize_requested_membership_status_fn=_normalize_requested_membership_status,
        get_membership_row_fn=_get_membership_row,
        request_json_fn=request_json,
        rest_base_url_fn=_rest_base_url,
        service_api_key_fn=_service_api_key,
        timeout_seconds_fn=_timeout_seconds,
        sync_legacy_user_projection_fn=_sync_legacy_user_projection,
        get_local_user_fn=_get_local_user,
        error_cls=AuthRuntimeError,
    )

def _resolve_application_profile(
    *,
    auth_user: dict[str, Any],
    email: str,
    display_name: str,
) -> dict[str, Any]:
    auth_user_id = str(auth_user.get("id") or "").strip()
    bootstrap_email = bootstrap_platform_admin_email()
    if bootstrap_email and email == bootstrap_email:
        local_user = _ensure_bootstrap_local_user(
            auth_user_id=auth_user_id,
            email=email,
            display_name=display_name,
        )
        return {
            "authorized": True,
            "role": "platform_admin",
            "organization_id": str(local_user.get("organization_id") or ""),
            "organization_name": str(local_user.get("organization_name") or DEFAULT_BOOTSTRAP_ORG_NAME),
            "local_user_id": str(local_user.get("id") or ""),
            "membership_id": str(local_user.get("membership_id") or ""),
            "message": "",
            "status": _normalize_local_user_status(local_user.get("status")),
            "account_status": _normalize_account_status(local_user.get("account_status")),
            "membership_status": _normalize_membership_status(local_user.get("membership_status")),
            "mobile_phone": str(local_user.get("mobile_phone") or ""),
            "office_phone": str(local_user.get("office_phone") or ""),
        }

    local_user = _get_local_user(user_id=auth_user_id)
    if local_user is None:
        profile = _get_user_profile(user_id=auth_user_id, email=email)
        account_status = _normalize_account_status(profile.get("account_status")) if profile else "inactive"
        return {
            "authorized": False,
            "role": "unauthorized",
            "organization_id": None,
            "organization_name": "",
            "local_user_id": str(profile.get("id") or "") if profile else None,
            "membership_id": None,
            "message": "This account is authenticated but not invited to any organization.",
            "status": account_status,
            "account_status": account_status,
            "membership_status": "inactive",
            "mobile_phone": str(profile.get("mobile_phone") or "") if profile else "",
            "office_phone": str(profile.get("office_phone") or "") if profile else "",
        }

    account_status = _normalize_account_status(local_user.get("account_status"))
    membership_status = _normalize_membership_status(local_user.get("membership_status"))
    local_status = _normalize_local_user_status(local_user.get("status"))
    if local_status != "active":
        return {
            "authorized": False,
            "role": str(local_user.get("role") or "org_member"),
            "organization_id": str(local_user.get("organization_id") or ""),
            "organization_name": str(local_user.get("organization_name") or ""),
            "local_user_id": str(local_user.get("id") or ""),
            "membership_id": str(local_user.get("membership_id") or ""),
            "message": "이 계정은 비활성화되었습니다.",
            "status": local_status,
            "account_status": account_status,
            "membership_status": membership_status,
            "mobile_phone": str(local_user.get("mobile_phone") or ""),
            "office_phone": str(local_user.get("office_phone") or ""),
        }

    return {
        "authorized": True,
        "role": str(local_user.get("role") or "org_member"),
        "organization_id": str(local_user.get("organization_id") or ""),
        "organization_name": str(local_user.get("organization_name") or ""),
        "local_user_id": str(local_user.get("id") or ""),
        "membership_id": str(local_user.get("membership_id") or ""),
        "message": "",
        "status": local_status,
        "account_status": account_status,
        "membership_status": membership_status,
        "mobile_phone": str(local_user.get("mobile_phone") or ""),
        "office_phone": str(local_user.get("office_phone") or ""),
    }

def _ensure_bootstrap_local_user(*, auth_user_id: str, email: str, display_name: str) -> dict[str, Any]:
    return _ensure_bootstrap_local_user_helper(
        auth_user_id=auth_user_id,
        email=email,
        display_name=display_name,
        rest_upsert_fn=_rest_upsert,
        ensure_user_profile_fn=_ensure_user_profile,
        ensure_membership_fn=_ensure_membership,
        sync_legacy_user_projection_fn=_sync_legacy_user_projection,
        get_local_user_fn=_get_local_user,
        default_phase1_organization_id=DEFAULT_PHASE1_ORGANIZATION_ID,
        default_bootstrap_org_name=DEFAULT_BOOTSTRAP_ORG_NAME,
        default_bootstrap_org_slug=DEFAULT_BOOTSTRAP_ORG_SLUG,
        error_cls=AuthRuntimeError,
    )

def _ensure_member_local_user(*, auth_user_id: str, email: str, display_name: str) -> dict[str, Any]:
    return _ensure_member_local_user_helper(
        auth_user_id=auth_user_id,
        email=email,
        display_name=display_name,
        ensure_user_profile_fn=_ensure_user_profile,
        get_user_profile_fn=_get_user_profile,
        error_cls=AuthRuntimeError,
    )

def _get_local_user(*, user_id: str = "", email: str = "", organization_id: str = "") -> dict[str, Any] | None:
    return _get_local_user_impl(
        user_id=user_id,
        email=email,
        organization_id=organization_id,
        query_local_user_rows=_query_local_user_rows,
        normalize_local_user_row=_normalize_local_user_row,
    )

def _get_membership_row(*, organization_id: str = "", user_id: str = "", membership_id: str = "", email: str = "") -> dict[str, Any] | None:
    return _get_membership_row_impl(
        organization_id=organization_id,
        user_id=user_id,
        membership_id=membership_id,
        email=email,
        query_local_user_rows=_query_local_user_rows,
        normalize_local_user_row=_normalize_local_user_row,
    )

def _get_user_profile(*, user_id: str = "", email: str = "") -> dict[str, Any] | None:
    return _get_user_profile_impl(
        user_id=user_id,
        email=email,
        request_json=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        user_profile_select_columns=USER_PROFILE_SELECT_COLUMNS,
        is_missing_relation_error=_is_missing_relation_error,
        build_profile_from_legacy_user=_build_profile_from_legacy_user,
        normalize_account_status=_normalize_account_status,
        normalize_global_role=_normalize_global_role,
        auth_error_cls=AuthRuntimeError,
    )

def _update_local_user_profile(
    *,
    user_id: str,
    email: str,
    display_name: str,
    mobile_phone: str = "",
    office_phone: str = "",
) -> dict[str, Any]:
    return _update_local_user_profile_impl(
        user_id=user_id,
        email=email,
        display_name=display_name,
        mobile_phone=mobile_phone,
        office_phone=office_phone,
        request_json_fn=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        auth_error_cls=AuthRuntimeError,
        is_missing_relation_error_fn=_is_missing_relation_error,
        get_local_user_fn=_get_local_user,
        sync_legacy_user_projection_fn=_sync_legacy_user_projection,
        get_user_profile_fn=_get_user_profile,
        default_phase1_org_id=DEFAULT_PHASE1_ORGANIZATION_ID,
    )

def _query_local_user_rows(*, filters: list[tuple[str, str]]) -> list[dict[str, Any]]:
    return _query_local_user_rows_impl(
        filters=filters,
        request_json_fn=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        error_cls=AuthRuntimeError,
        membership_view_select_columns=MEMBERSHIP_VIEW_SELECT_COLUMNS,
        local_user_select_columns=LOCAL_USER_SELECT_COLUMNS,
        local_user_fallback_select_columns=LOCAL_USER_FALLBACK_SELECT_COLUMNS,
        is_missing_relation_error=_is_missing_relation_error,
        build_legacy_local_user_row=_build_legacy_local_user_row,
    )

def _normalize_local_user_row(raw: dict[str, Any]) -> dict[str, Any]:
    return _normalize_local_user_row_impl(
        raw=raw,
        normalize_account_status=_normalize_account_status,
        normalize_membership_status=_normalize_membership_status,
        normalize_global_role=_normalize_global_role,
        build_legacy_local_user_row=_build_legacy_local_user_row,
    )

def _build_legacy_local_user_row(raw: dict[str, Any]) -> dict[str, Any]:
    return _build_legacy_local_user_row_impl(
        raw=raw,
        map_role_label=_map_role_label,
        normalize_local_user_status=_normalize_local_user_status,
        get_organization=_get_organization,
    )

def _build_profile_from_legacy_user(*, user_id: str = "", email: str = "") -> dict[str, Any] | None:
    return _build_profile_from_legacy_user_lookup_impl(
        user_id=user_id,
        email=email,
        request_json=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        local_user_select_columns=LOCAL_USER_SELECT_COLUMNS,
        local_user_fallback_select_columns=LOCAL_USER_FALLBACK_SELECT_COLUMNS,
        is_missing_column_error=_is_missing_column_error,
        normalize_account_status=_normalize_local_user_status,
        normalize_global_role=_normalize_global_role,
        auth_error_cls=AuthRuntimeError,
    )

def _ensure_user_profile(
    *,
    user_id: str,
    email: str,
    display_name: str,
    account_status: str = "active",
    global_role: str = "",
    created_by_user_id: str | None = None,
    password_setup_mode: str | None = None,
    force_password_change: bool | None = None,
) -> None:
    _ensure_user_profile_impl(
        user_id=user_id,
        email=email,
        display_name=display_name,
        account_status=account_status,
        global_role=global_role,
        created_by_user_id=created_by_user_id,
        password_setup_mode=password_setup_mode,
        force_password_change=force_password_change,
        get_user_profile_fn=_get_user_profile,
        request_json_fn=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        rest_upsert_fn=_rest_upsert,
        normalize_account_status_fn=_normalize_account_status,
        normalize_global_role_fn=_normalize_global_role,
        is_missing_relation_error_fn=_is_missing_relation_error,
        is_missing_column_error_fn=_is_missing_column_error,
        auth_error_cls=AuthRuntimeError,
    )

def _ensure_membership(
    *,
    organization_id: str,
    user_id: str,
    role: str,
    membership_status: str = "active",
    team_name: str = "",
    job_title: str = "",
) -> None:
    _ensure_membership_impl(
        organization_id=organization_id,
        user_id=user_id,
        role=role,
        membership_status=membership_status,
        team_name=team_name,
        job_title=job_title,
        rest_upsert_fn=_rest_upsert,
        normalize_org_role_fn=_normalize_org_role,
        normalize_membership_status_fn=_normalize_membership_status,
        is_missing_relation_error_fn=_is_missing_relation_error,
        auth_error_cls=AuthRuntimeError,
    )

def _sync_legacy_user_projection(
    *,
    user_id: str,
    organization_id: str,
    email: str,
    display_name: str,
    membership_role: str,
    membership_status: str,
) -> None:
    _sync_legacy_user_projection_impl(
        user_id=user_id,
        organization_id=organization_id,
        email=email,
        display_name=display_name,
        membership_role=membership_role,
        membership_status=membership_status,
        rest_upsert_fn=_rest_upsert,
        map_membership_role_to_legacy_role_fn=_map_membership_role_to_legacy_role,
        normalize_membership_status_fn=_normalize_membership_status,
    )

def _touch_last_login(*, auth_user_id: str) -> None:
    _touch_last_login_helper(
        auth_user_id=auth_user_id,
        request_json_fn=request_json,
        rest_base_url_fn=_rest_base_url,
        service_api_key_fn=_service_api_key,
        timeout_seconds_fn=_timeout_seconds,
        error_cls=AuthRuntimeError,
    )

def update_organization_membership(
    *,
    organization_id: str,
    user_id: str,
    role: str = "",
    membership_status: str = "",
    team_name: str = "",
    job_title: str = "",
    actor_user_id: str = "",
) -> dict[str, Any]:
    return _update_organization_membership_helper(
        organization_id=organization_id,
        user_id=user_id,
        role=role,
        membership_status=membership_status,
        team_name=team_name,
        job_title=job_title,
        actor_user_id=actor_user_id,
        get_membership_row_fn=_get_membership_row,
        normalize_org_role_fn=_normalize_org_role,
        normalize_requested_membership_status_fn=_normalize_requested_membership_status,
        request_json_fn=request_json,
        rest_base_url_fn=_rest_base_url,
        service_api_key_fn=_service_api_key,
        timeout_seconds_fn=_timeout_seconds,
        get_local_user_fn=_get_local_user,
        sync_legacy_user_projection_fn=_sync_legacy_user_projection,
        append_audit_log_fn=_append_audit_log,
        error_cls=AuthRuntimeError,
    )

def delete_local_user_account(
    *,
    organization_id: str,
    user_id: str,
) -> dict[str, Any]:
    return _delete_local_user_account_helper(
        organization_id=organization_id,
        user_id=user_id,
        get_local_user_fn=_get_local_user,
        normalize_email_fn=_normalize_email,
        get_user_profile_fn=_get_user_profile,
        rest_delete_rows_fn=_rest_delete_rows,
        delete_supabase_auth_user_fn=_delete_supabase_auth_user,
        error_cls=AuthRuntimeError,
    )

def _cleanup_local_account(*, organization_id: str, user_id: str, email: str) -> None:
    _cleanup_local_account_helper(
        organization_id=organization_id,
        user_id=user_id,
        email=email,
        get_local_user_fn=_get_local_user,
        normalize_email_fn=_normalize_email,
        get_user_profile_fn=_get_user_profile,
        rest_delete_rows_fn=_rest_delete_rows,
    )

def append_audit_log(
    *,
    organization_id: str,
    actor_user_id: str = "",
    actor_membership_id: str = "",
    event_type: str,
    target_type: str = "",
    target_id: str = "",
    payload: dict[str, Any] | None = None,
) -> None:
    _append_audit_log(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        actor_membership_id=actor_membership_id,
        event_type=event_type,
        target_type=target_type,
        target_id=target_id,
        payload=payload or {},
    )

def _append_audit_log(
    *,
    organization_id: str = "",
    actor_user_id: str = "",
    actor_membership_id: str = "",
    event_type: str,
    target_type: str = "",
    target_id: str = "",
    payload: dict[str, Any] | None = None,
) -> None:
    _append_audit_log_helper(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        actor_membership_id=actor_membership_id,
        event_type=event_type,
        target_type=target_type,
        target_id=target_id,
        payload=payload,
        request_json_fn=request_json,
        rest_base_url_fn=_rest_base_url,
        service_api_key_fn=_service_api_key,
        timeout_seconds_fn=_timeout_seconds,
        error_cls=AuthRuntimeError,
    )
