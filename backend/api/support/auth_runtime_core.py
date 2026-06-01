from __future__ import annotations

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
from backend.api.support.auth_runtime_config_helpers import auth_base_url as _auth_base_url_impl
from backend.api.support.auth_runtime_config_helpers import ensure_auth_enabled as _ensure_auth_enabled_impl
from backend.api.support.auth_runtime_config_helpers import public_api_key as _public_api_key_impl
from backend.api.support.auth_runtime_config_helpers import rest_base_url as _rest_base_url_impl
from backend.api.support.auth_runtime_config_helpers import service_api_key as _service_api_key_impl
from backend.api.support.auth_runtime_config_helpers import session_refresh_timeout_seconds as _session_refresh_timeout_seconds_impl
from backend.api.support.auth_runtime_config_helpers import supabase_url as _supabase_url_impl
from backend.api.support.auth_runtime_config_helpers import timeout_seconds as _timeout_seconds_impl
from backend.api.support.auth_runtime_config_helpers import normalize_truthy as _normalize_truthy_impl
from backend.api.support.auth_runtime_http_helpers import auth_request as _auth_request_impl
from backend.api.support.auth_runtime_http_helpers import create_supabase_auth_user as _create_supabase_auth_user_impl
from backend.api.support.auth_runtime_http_helpers import delete_supabase_auth_user as _delete_supabase_auth_user_impl
from backend.api.support.auth_runtime_http_helpers import rest_delete_rows as _rest_delete_rows_impl
from backend.api.support.auth_runtime_http_helpers import rest_upsert as _rest_upsert_impl
from backend.api.support.auth_runtime_http_helpers import reset_platform_admin_account_password as _reset_platform_admin_account_password_impl
from backend.api.support.auth_runtime_http_helpers import reset_platform_admin_account_password_with_context as _reset_platform_admin_account_password_with_context_impl
from backend.api.support.auth_runtime_session_cookie_helpers import decode_signed_payload as _decode_signed_payload_impl
from backend.api.support.auth_runtime_session_cookie_helpers import encode_signed_payload as _encode_signed_payload_impl
from backend.api.support.auth_runtime_session_cookie_helpers import read_access_token_expires_in as _read_access_token_expires_in_impl
from backend.api.support.auth_runtime_session_cookie_helpers import session_secret as _session_secret_impl
from backend.api.support.auth_runtime_session_cookie_helpers import urlsafe_b64decode as _urlsafe_b64decode_impl
from backend.api.support.auth_runtime_session_cookie_helpers import urlsafe_b64encode as _urlsafe_b64encode_impl

SESSION_COOKIE_NAME = "tracker_auth_session"
SESSION_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 30
SESSION_REFRESH_GRACE_SECONDS = 60
PROFILE_RECHECK_TTL_SECONDS = 60 * 5
LOCAL_BOOTSTRAP_AUTH_FILE = ".tmp-auth-server/bootstrap-local-auth.json"

DEFAULT_BOOTSTRAP_ORG_NAME = "(주)파노텍"
DEFAULT_BOOTSTRAP_ORG_SLUG = "internal-ops"

logger = logging.getLogger(__name__)


MEMBERSHIP_VIEW_SELECT_COLUMNS = (
    "membership_id,organization_id,organization_name,user_id,email,display_name,"
    "mobile_phone,office_phone,account_status,global_role,membership_role,membership_status,"
    "team_name,job_title,last_login_at,profile_created_at,profile_updated_at,"
    "membership_created_at,membership_updated_at"
)
MEMBERSHIP_OVERVIEW_SELECT_COLUMNS = (
    "membership_id,organization_id,user_id,email,display_name,"
    "mobile_phone,office_phone,account_status,membership_role,membership_status,"
    "team_name,job_title"
)
LOCAL_USER_SELECT_COLUMNS = "id,organization_id,email,display_name,role,status"
LOCAL_USER_FALLBACK_SELECT_COLUMNS = "id,organization_id,email,display_name,role"
USER_PROFILE_SELECT_COLUMNS = (
    "id,email,display_name,mobile_phone,office_phone,account_status,global_role,last_login_at,created_at,updated_at"
)
VALID_ACCOUNT_STATUSES = frozenset({"active", "inactive", "deactivated"})
VALID_MEMBERSHIP_STATUSES = frozenset({"active", "inactive", "deactivated"})
VALID_ORG_ROLES = frozenset({"org_admin", "org_member"})
INVITATION_PASSWORD_UPPER = "ABCDEFGHJKLMNPQRSTUVWXYZ"
INVITATION_PASSWORD_LOWER = "abcdefghijkmnopqrstuvwxyz"
INVITATION_PASSWORD_DIGITS = "23456789"
INVITATION_PASSWORD_SPECIAL = "!@#$%^&*_-+="
INVITATION_PASSWORD_LENGTH = 16
DEFAULT_ORGANIZATION_PLAN_CODE = "A"
ORGANIZATION_PLAN_LIMITS = {
    "A": {"active_user_limit": 5, "pending_invite_limit": 5},
    "B": {"active_user_limit": 10, "pending_invite_limit": 10},
    "C": {"active_user_limit": 100, "pending_invite_limit": 100},
}
ORGANIZATION_PLAN_ORDER = ("A", "B", "C")
ORGANIZATION_SELECT_COLUMNS = "id,name,slug,plan_code,active_user_limit,pending_invite_limit"
ORGANIZATION_LEGACY_SELECT_COLUMNS = "id,name,slug"
AUDIT_LOG_SELECT_COLUMNS = (
    "id,organization_id,actor_user_id,actor_membership_id,event_type,target_type,target_id,payload_json,created_at"
)

class AuthRuntimeError(Exception):
    def __init__(self, message: str, *, status_code: int = 400, code: str = "auth_error") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


@dataclass(frozen=True)
class AuthContext:
    auth_user_id: UUID
    local_user_id: UUID | None
    membership_id: UUID | None
    email: str
    display_name: str
    role: str
    organization_id: UUID | None
    organization_name: str
    account_status: str
    membership_status: str
    authorized: bool
    access_expires_at: int

def auth_is_enabled() -> bool:
    if _normalize_truthy(os.getenv("LOCAL_APP_DISABLE_LOGIN", "")):
        return False
    if not _supabase_url():
        return False
    if not _service_api_key():
        return False
    explicit_raw = os.getenv("PHASE2_AUTH_ENABLED", "").strip()
    if explicit_raw:
        return _normalize_truthy(explicit_raw)
    bootstrap_email = bootstrap_platform_admin_email()
    return bool(bootstrap_email)

def bootstrap_platform_admin_email() -> str:
    return os.getenv("BOOTSTRAP_PLATFORM_ADMIN_EMAIL", "").strip().lower()

def _has_invitation_email_delivery_prerequisites() -> bool:
    return bool(_supabase_url()) and bool(_service_api_key())

def invitation_email_delivery_enabled() -> bool:
    explicit = os.getenv("PHASE2_AUTH_DELIVER_INVITE_EMAILS", "").strip()
    if explicit:
        return _normalize_truthy(explicit)
    return _has_invitation_email_delivery_prerequisites()

def build_auth_status_response() -> dict[str, Any]:
    public_auth_url = ""
    supabase_url = _supabase_url()
    if supabase_url:
        public_auth_url = f"{supabase_url}/auth/v1"
    public_api_key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip() or os.getenv("SUPABASE_ANON_KEY", "").strip()
    return {
        "enabled": auth_is_enabled(),
        "authenticated": False,
        "authorized": False,
        "bootstrap_email": bootstrap_platform_admin_email(),
        "public_auth_url": public_auth_url,
        "public_api_key": public_api_key,
        "public_auth_configured": bool(public_auth_url and public_api_key),
        "message": "",
        "user": None,
    }

def _normalize_invitation_row(row: dict[str, Any]) -> dict[str, Any]:
    return _normalize_invitation_row_impl(
        row,
        normalize_email=_normalize_email,
        normalize_org_role=_normalize_org_role,
    )

def _parse_datetime_value(value: Any) -> datetime | None:
    return _parse_datetime_value_impl(value)

def _can_use_local_bootstrap_fallback(*, request_host: str, email: str) -> bool:
    return _can_use_local_bootstrap_fallback_impl(
        request_host=request_host,
        email=email,
        normalize_email=_normalize_email,
        bootstrap_platform_admin_email=bootstrap_platform_admin_email,
    )

def _bootstrap_local_auth_path() -> str:
    return _bootstrap_local_auth_path_impl(default_path=LOCAL_BOOTSTRAP_AUTH_FILE)

def _load_local_bootstrap_auth_record() -> dict[str, Any]:
    return _load_local_bootstrap_auth_record_impl(path=_bootstrap_local_auth_path())

def _save_local_bootstrap_auth_record(payload: dict[str, Any]) -> None:
    _save_local_bootstrap_auth_record_impl(path=_bootstrap_local_auth_path(), payload=payload)

def _hash_local_bootstrap_password(password: str, *, salt_hex: str = "") -> tuple[str, str]:
    return _hash_local_bootstrap_password_impl(password, salt_hex=salt_hex)

def _register_local_bootstrap_password(*, email: str, password: str) -> None:
    _register_local_bootstrap_password_impl(
        email=email,
        password=password,
        normalize_email=_normalize_email,
        hash_local_bootstrap_password_fn=_hash_local_bootstrap_password,
        save_local_bootstrap_auth_record_fn=_save_local_bootstrap_auth_record,
    )

def _verify_local_bootstrap_password(*, email: str, password: str) -> bool:
    return _verify_local_bootstrap_password_impl(
        email=email,
        password=password,
        normalize_email=_normalize_email,
        load_local_bootstrap_auth_record_fn=_load_local_bootstrap_auth_record,
        hash_local_bootstrap_password_fn=_hash_local_bootstrap_password,
    )

def _has_local_bootstrap_password(*, email: str) -> bool:
    return _has_local_bootstrap_password_impl(
        email=email,
        normalize_email=_normalize_email,
        load_local_bootstrap_auth_record_fn=_load_local_bootstrap_auth_record,
    )

def _local_bootstrap_auth_user_id(email: str) -> str:
    return _local_bootstrap_auth_user_id_impl(email, normalize_email=_normalize_email)

def _resolve_local_bootstrap_auth_user_id(email: str) -> str:
    return _resolve_local_bootstrap_auth_user_id_impl(
        email,
        normalize_email=_normalize_email,
        get_user_profile=_get_user_profile,
        get_local_user=_get_local_user,
        default_organization_id=DEFAULT_PHASE1_ORGANIZATION_ID,
        local_bootstrap_auth_user_id_fn=_local_bootstrap_auth_user_id,
    )

def _build_local_bootstrap_session(*, email: str, display_name: str = "", message: str = "") -> dict[str, Any]:
    return _build_local_bootstrap_session_impl(
        email=email,
        display_name=display_name,
        message=message,
        normalize_email=_normalize_email,
        resolve_local_bootstrap_auth_user_id_fn=_resolve_local_bootstrap_auth_user_id,
        ensure_bootstrap_local_user=_ensure_bootstrap_local_user,
        normalize_local_user_status=_normalize_local_user_status,
        normalize_account_status=_normalize_account_status,
        normalize_membership_status=_normalize_membership_status,
        default_bootstrap_org_name=DEFAULT_BOOTSTRAP_ORG_NAME,
        session_cookie_max_age_seconds=SESSION_COOKIE_MAX_AGE_SECONDS,
    )

def _build_invite_url(base: str, token: str) -> str:
    return _build_invite_url_impl(base, token)

def _build_invitation_initial_password(token: str) -> str:
    return _build_invitation_initial_password_impl(token, session_secret=_session_secret)

def _normalize_local_user_status(value: Any) -> str:
    return _normalize_local_user_status_impl(value)

def _normalize_requested_local_user_status(value: Any) -> str:
    return _normalize_requested_membership_status(value)

def _normalize_account_status(value: Any) -> str:
    return _normalize_account_status_impl(value)

def _normalize_membership_status(value: Any) -> str:
    return _normalize_membership_status_impl(value)

def _normalize_requested_membership_status(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized not in VALID_MEMBERSHIP_STATUSES:
        allowed = ", ".join(sorted(VALID_MEMBERSHIP_STATUSES))
        raise AuthRuntimeError(
            f"status must be one of {allowed}",
            status_code=400,
            code="validation_error",
        )
    return normalized

def _normalize_org_role(value: Any) -> str:
    return _normalize_org_role_impl(value, valid_org_roles=VALID_ORG_ROLES)

def _normalize_global_role(value: Any) -> str:
    return _normalize_global_role_impl(value)

def _normalize_plan_code(value: Any) -> str:
    return _normalize_plan_code_impl(
        value,
        default_organization_plan_code=DEFAULT_ORGANIZATION_PLAN_CODE,
        organization_plan_limits=ORGANIZATION_PLAN_LIMITS,
    )

def _normalize_limit_value(value: Any, *, default: int, minimum: int = 0) -> int:
    return _normalize_limit_value_impl(value, default=default, minimum=minimum)

def _resolve_next_plan_code(plan_code: str) -> str:
    return _resolve_next_plan_code_impl(plan_code, organization_plan_order=ORGANIZATION_PLAN_ORDER)

def _is_existing_auth_user_error(message: str) -> bool:
    lowered = str(message or "").lower()
    return any(token in lowered for token in ("already", "exists", "registered", "users_email_partial_key"))

def _is_missing_relation_error(message: str, relation_name: str) -> bool:
    return _is_missing_relation_error_impl(message, relation_name)

def _is_missing_column_error(message: str, column_name: str) -> bool:
    return _is_missing_column_error_impl(message, column_name)

def _normalize_organization_row(raw: dict[str, Any]) -> dict[str, Any]:
    return _normalize_organization_row_impl(
        raw=raw,
        normalize_plan_code=_normalize_plan_code,
        normalize_limit_value=_normalize_limit_value,
        organization_plan_limits=ORGANIZATION_PLAN_LIMITS,
    )

def _get_organization(organization_id: str) -> dict[str, Any] | None:
    return _get_organization_impl(
        organization_id,
        request_json_fn=request_json,
        rest_base_url=_rest_base_url,
        service_api_key=_service_api_key,
        timeout_seconds=_timeout_seconds,
        error_cls=AuthRuntimeError,
        organization_select_columns=ORGANIZATION_SELECT_COLUMNS,
        organization_legacy_select_columns=ORGANIZATION_LEGACY_SELECT_COLUMNS,
        is_missing_column_error=_is_missing_column_error,
        normalize_organization_row=_normalize_organization_row,
    )


def _reset_platform_admin_account_password(*, user_id: str, email: str, password: str) -> dict[str, Any]:
    normalized_user_id = str(user_id or "").strip()
    normalized_email = _normalize_email(email)
    normalized_password = str(password or "").strip()
    if not normalized_user_id:
        raise AuthRuntimeError("user_id is required", status_code=400, code="validation_error")
    if not normalized_email:
        raise AuthRuntimeError("email is required", status_code=400, code="validation_error")
    if not normalized_password:
        raise AuthRuntimeError("password is required", status_code=400, code="validation_error")
    _auth_request(
        "PUT",
        f"/admin/users/{normalized_user_id}",
        payload={"password": normalized_password},
        use_service_authorization=True,
    )
    if normalized_email == bootstrap_platform_admin_email():
        _register_local_bootstrap_password(email=normalized_email, password=normalized_password)
    return {"message": "비밀번호를 재설정했습니다."}

def _reset_platform_admin_account_password_with_context(
    *,
    actor_user_id: str,
    actor_role: str,
    organization_id: str,
    user_id: str,
    email: str,
    password: str,
) -> dict[str, Any]:
    normalized_actor_role = str(actor_role or "").strip().lower()
    if normalized_actor_role != "platform_admin":
        raise AuthRuntimeError("platform admin only", status_code=403, code="auth_forbidden")

    normalized_organization_id = str(organization_id or "").strip()
    normalized_actor_user_id = str(actor_user_id or "").strip()
    normalized_user_id = str(user_id or "").strip()
    normalized_email = _normalize_email(email)
    normalized_password = str(password or "").strip()
    if not normalized_organization_id:
        raise AuthRuntimeError("organization_id is required", status_code=400, code="validation_error")
    if not normalized_user_id:
        raise AuthRuntimeError("user_id is required", status_code=400, code="validation_error")
    if not normalized_email:
        raise AuthRuntimeError("email is required", status_code=400, code="validation_error")
    if not normalized_password:
        raise AuthRuntimeError("password is required", status_code=400, code="validation_error")
    if normalized_email == bootstrap_platform_admin_email():
        raise AuthRuntimeError(
            "bootstrap platform admin account is protected",
            status_code=409,
            code="auth_user_protected",
        )
    if normalized_actor_user_id and normalized_actor_user_id == normalized_user_id:
        raise AuthRuntimeError(
            "platform admins cannot reset their own password here",
            status_code=403,
            code="auth_user_self_password_reset_forbidden",
        )

    _auth_request(
        "PUT",
        f"/admin/users/{normalized_user_id}",
        payload={"password": normalized_password},
        use_service_authorization=True,
    )
    try:
        append_audit_log(
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

def _normalize_email(value: Any) -> str:
    return _normalize_email_impl(value)

def _resolve_display_name(user: dict[str, Any]) -> str:
    metadata = user.get("user_metadata")
    if isinstance(metadata, dict):
        for key in ("display_name", "full_name", "name"):
            raw = str(metadata.get(key) or "").strip()
            if raw:
                return raw
    email = _normalize_email(user.get("email"))
    if email:
        return email.split("@", 1)[0]
    return "User"

def _map_role_label(role: str) -> str:
    return _map_role_label_impl(role)

def _map_membership_role_to_legacy_role(role: str) -> str:
    return _map_membership_role_to_legacy_role_impl(role, normalize_org_role_fn=_normalize_org_role)

def _parse_uuid(value: Any) -> UUID | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None

def _supabase_url() -> str:
    return _supabase_url_impl()


def _service_api_key() -> str:
    return _service_api_key_impl()


def _public_api_key() -> str:
    return _public_api_key_impl(error_cls=AuthRuntimeError)


def _timeout_seconds() -> float:
    return _timeout_seconds_impl()


def _session_refresh_timeout_seconds() -> float:
    return _session_refresh_timeout_seconds_impl(timeout_seconds_fn=_timeout_seconds)


def _ensure_auth_enabled() -> None:
    _ensure_auth_enabled_impl(auth_is_enabled_fn=auth_is_enabled, error_cls=AuthRuntimeError)


def _auth_base_url() -> str:
    return _auth_base_url_impl(supabase_url_fn=_supabase_url, error_cls=AuthRuntimeError)


def _rest_base_url() -> str:
    return _rest_base_url_impl(supabase_url_fn=_supabase_url, error_cls=AuthRuntimeError)


def _auth_request(
    method: str,
    path: str,
    *,
    query: list[tuple[str, str]] | None = None,
    payload: dict[str, Any] | None = None,
    access_token: str = "",
    use_service_authorization: bool,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    return _auth_request_impl(
        method,
        path,
        query=query,
        payload=payload,
        access_token=access_token,
        use_service_authorization=use_service_authorization,
        timeout_seconds=timeout_seconds,
        auth_base_url_fn=_auth_base_url,
        service_api_key_fn=_service_api_key,
        public_api_key_fn=_public_api_key,
        timeout_seconds_fn=_timeout_seconds,
        error_cls=AuthRuntimeError,
        requests_request_fn=requests.request,
        extract_error_message_fn=extract_error_message,
    )


def _rest_upsert(path: str, payload: dict[str, Any], *, on_conflict: str) -> None:
    _rest_upsert_impl(
        path,
        payload,
        on_conflict=on_conflict,
        rest_base_url_fn=_rest_base_url,
        service_api_key_fn=_service_api_key,
        timeout_seconds_fn=_timeout_seconds,
        error_cls=AuthRuntimeError,
        request_json_fn=request_json,
    )


def _rest_delete_rows(path: str, query: list[tuple[str, str]]) -> None:
    _rest_delete_rows_impl(
        path,
        query,
        rest_base_url_fn=_rest_base_url,
        service_api_key_fn=_service_api_key,
        timeout_seconds_fn=_timeout_seconds,
        error_cls=AuthRuntimeError,
        request_json_fn=request_json,
    )


def _delete_supabase_auth_user(*, auth_user_id: str) -> None:
    _delete_supabase_auth_user_impl(auth_user_id=auth_user_id, auth_request_fn=_auth_request, error_cls=AuthRuntimeError)


def _create_supabase_auth_user(*, email: str, password: str, display_name: str = "") -> dict[str, Any]:
    return _create_supabase_auth_user_impl(
        email=email,
        password=password,
        display_name=display_name,
        normalize_email_fn=_normalize_email,
        auth_request_fn=_auth_request,
        error_cls=AuthRuntimeError,
    )


def _reset_platform_admin_account_password(*, user_id: str, email: str, password: str) -> dict[str, Any]:
    return _reset_platform_admin_account_password_impl(
        user_id=user_id,
        email=email,
        password=password,
        normalize_email_fn=_normalize_email,
        auth_request_fn=_auth_request,
        bootstrap_platform_admin_email_fn=bootstrap_platform_admin_email,
        register_local_bootstrap_password_fn=_register_local_bootstrap_password,
        error_cls=AuthRuntimeError,
    )


def _reset_platform_admin_account_password_with_context(
    *,
    actor_user_id: str,
    actor_role: str,
    organization_id: str,
    user_id: str,
    email: str,
    password: str,
) -> dict[str, Any]:
    return _reset_platform_admin_account_password_with_context_impl(
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        organization_id=organization_id,
        user_id=user_id,
        email=email,
        password=password,
        normalize_email_fn=_normalize_email,
        auth_request_fn=_auth_request,
        bootstrap_platform_admin_email_fn=bootstrap_platform_admin_email,
        register_local_bootstrap_password_fn=_register_local_bootstrap_password,
        append_audit_log_fn=append_audit_log,
        logger=logger,
        error_cls=AuthRuntimeError,
    )


def _read_access_token_expires_in(access_token: str) -> int:
    return _read_access_token_expires_in_impl(access_token, urlsafe_b64decode=_urlsafe_b64decode)


def _session_secret() -> str:
    return _session_secret_impl(
        configured_secret=os.getenv("PHASE2_AUTH_SESSION_SECRET", ""),
        service_api_key_fn=_service_api_key,
        error_cls=AuthRuntimeError,
    )


def _encode_signed_payload(payload: dict[str, Any]) -> str:
    return _encode_signed_payload_impl(payload, session_secret=_session_secret, urlsafe_b64encode=_urlsafe_b64encode)


def _decode_signed_payload(value: str) -> dict[str, Any]:
    try:
        return _decode_signed_payload_impl(value, session_secret=_session_secret, urlsafe_b64decode=_urlsafe_b64decode)
    except ValueError as exc:
        raise AuthRuntimeError(str(exc), status_code=401, code="auth_invalid") from exc


def _urlsafe_b64encode(value: bytes) -> str:
    return _urlsafe_b64encode_impl(value)


def _urlsafe_b64decode(value: str) -> bytes:
    return _urlsafe_b64decode_impl(value)


def _normalize_truthy(value: str) -> bool:
    return _normalize_truthy_impl(value)
