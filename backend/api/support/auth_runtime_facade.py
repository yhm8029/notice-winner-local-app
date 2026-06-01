from __future__ import annotations

import sys
import time
import types

from backend.phase1_defaults import DEFAULT_PHASE1_ORGANIZATION_ID
from backend.repositories.factory import get_login_audit_log_repository
from backend.repositories.supabase_http import extract_error_message
from backend.repositories.supabase_http import request_json
from backend.services.auth_admin_account_backend import create_platform_admin_account as _create_platform_admin_account_impl
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
from backend.services.auth_member_directory_backend import build_legacy_local_user_row as _build_legacy_local_user_row_impl
from backend.services.auth_member_directory_backend import list_local_users as _list_local_users_impl
from backend.services.auth_member_directory_backend import list_local_users_overview as _list_local_users_overview_impl
from backend.services.auth_member_directory_backend import list_organization_audit_logs as _list_organization_audit_logs_impl
from backend.services.auth_member_directory_backend import normalize_local_user_row as _normalize_local_user_row_impl
from backend.services.auth_member_directory_backend import query_local_user_rows as _query_local_user_rows_impl
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
from backend.services.auth_profile_lookup_backend import build_profile_from_legacy_user as _build_profile_from_legacy_user_lookup_impl
from backend.services.auth_profile_lookup_backend import get_local_user as _get_local_user_impl
from backend.services.auth_profile_lookup_backend import get_membership_row as _get_membership_row_impl
from backend.services.auth_profile_lookup_backend import get_user_profile as _get_user_profile_impl
from backend.services.auth_profile_write_backend import ensure_membership as _ensure_membership_impl
from backend.services.auth_profile_write_backend import ensure_user_profile as _ensure_user_profile_impl
from backend.services.auth_profile_write_backend import sync_legacy_user_projection as _sync_legacy_user_projection_impl
from backend.services.auth_profile_write_backend import update_local_user_profile as _update_local_user_profile_impl
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
from backend.services.auth_session_backend import build_session_response_payload as _build_session_response_payload_impl
from backend.services.auth_session_cookie_backend import decode_signed_payload as _decode_signed_payload_impl
from backend.services.auth_session_cookie_backend import encode_signed_payload as _encode_signed_payload_impl
from backend.services.auth_session_cookie_backend import read_access_token_expires_in as _read_access_token_expires_in_impl
from backend.services.auth_session_orchestration_backend import build_session_response as _build_session_response_impl
from backend.services.auth_session_orchestration_backend import ensure_fresh_session_payload as _ensure_fresh_session_payload_impl
from backend.services.auth_session_orchestration_backend import refresh_auth_session as _refresh_auth_session_impl
from backend.services.auth_session_orchestration_backend import send_password_reset_email as _send_password_reset_email_impl
from backend.services.auth_session_orchestration_backend import sign_in_with_password as _sign_in_with_password_impl
from backend.services.auth_session_orchestration_backend import sign_up_console_user as _sign_up_console_user_impl
from backend.services.auth_session_orchestration_backend import update_console_user_profile as _update_console_user_profile_impl

from backend.api.support import auth_runtime_core as _auth_runtime_core
from backend.api.support import auth_runtime_directory as _auth_runtime_directory
from backend.api.support import auth_runtime_invitations as _auth_runtime_invitations
from backend.api.support import auth_runtime_session as _auth_runtime_session

_RUNTIME_MODULES = (
    _auth_runtime_core,
    _auth_runtime_directory,
    _auth_runtime_invitations,
    _auth_runtime_session,
)

_EXPORT_GROUPS = (
    (
        _auth_runtime_core,
        (
            "SESSION_COOKIE_NAME",
            "SESSION_COOKIE_MAX_AGE_SECONDS",
            "SESSION_REFRESH_GRACE_SECONDS",
            "PROFILE_RECHECK_TTL_SECONDS",
            "LOCAL_BOOTSTRAP_AUTH_FILE",
            "DEFAULT_BOOTSTRAP_ORG_NAME",
            "DEFAULT_BOOTSTRAP_ORG_SLUG",
            "MEMBERSHIP_VIEW_SELECT_COLUMNS",
            "MEMBERSHIP_OVERVIEW_SELECT_COLUMNS",
            "LOCAL_USER_SELECT_COLUMNS",
            "LOCAL_USER_FALLBACK_SELECT_COLUMNS",
            "USER_PROFILE_SELECT_COLUMNS",
            "VALID_ACCOUNT_STATUSES",
            "VALID_MEMBERSHIP_STATUSES",
            "VALID_ORG_ROLES",
            "INVITATION_PASSWORD_UPPER",
            "INVITATION_PASSWORD_LOWER",
            "INVITATION_PASSWORD_DIGITS",
            "INVITATION_PASSWORD_SPECIAL",
            "INVITATION_PASSWORD_LENGTH",
            "DEFAULT_ORGANIZATION_PLAN_CODE",
            "ORGANIZATION_PLAN_LIMITS",
            "ORGANIZATION_PLAN_ORDER",
            "ORGANIZATION_SELECT_COLUMNS",
            "ORGANIZATION_LEGACY_SELECT_COLUMNS",
            "AUDIT_LOG_SELECT_COLUMNS",
            "logger",
            "AuthRuntimeError",
            "AuthContext",
            "auth_is_enabled",
            "bootstrap_platform_admin_email",
            "_has_invitation_email_delivery_prerequisites",
            "invitation_email_delivery_enabled",
            "build_auth_status_response",
            "_normalize_invitation_row",
            "_parse_datetime_value",
            "_can_use_local_bootstrap_fallback",
            "_bootstrap_local_auth_path",
            "_load_local_bootstrap_auth_record",
            "_save_local_bootstrap_auth_record",
            "_hash_local_bootstrap_password",
            "_register_local_bootstrap_password",
            "_verify_local_bootstrap_password",
            "_has_local_bootstrap_password",
            "_local_bootstrap_auth_user_id",
            "_resolve_local_bootstrap_auth_user_id",
            "_build_local_bootstrap_session",
            "_build_invite_url",
            "_build_invitation_initial_password",
            "_normalize_local_user_status",
            "_normalize_requested_local_user_status",
            "_normalize_account_status",
            "_normalize_membership_status",
            "_normalize_requested_membership_status",
            "_normalize_org_role",
            "_normalize_global_role",
            "_normalize_plan_code",
            "_normalize_limit_value",
            "_resolve_next_plan_code",
            "_is_existing_auth_user_error",
            "_is_missing_relation_error",
            "_is_missing_column_error",
            "_normalize_organization_row",
            "_get_organization",
            "_rest_upsert",
            "_rest_delete_rows",
            "_delete_supabase_auth_user",
            "_create_supabase_auth_user",
            "_reset_platform_admin_account_password",
            "_reset_platform_admin_account_password_with_context",
            "_auth_request",
            "_ensure_auth_enabled",
            "_auth_base_url",
            "_rest_base_url",
            "_supabase_url",
            "_service_api_key",
            "_public_api_key",
            "_timeout_seconds",
            "_session_refresh_timeout_seconds",
            "_read_access_token_expires_in",
            "_session_secret",
            "_encode_signed_payload",
            "_decode_signed_payload",
            "_normalize_email",
            "_resolve_display_name",
            "_map_role_label",
            "_map_membership_role_to_legacy_role",
            "_parse_uuid",
            "_urlsafe_b64encode",
            "_urlsafe_b64decode",
            "_normalize_truthy",
        ),
    ),
    (
        _auth_runtime_directory,
        (
            "list_local_users",
            "list_local_users_overview",
            "update_local_user_status",
            "_resolve_application_profile",
            "_ensure_bootstrap_local_user",
            "_ensure_member_local_user",
            "_get_local_user",
            "_get_membership_row",
            "_get_user_profile",
            "_update_local_user_profile",
            "_query_local_user_rows",
            "_normalize_local_user_row",
            "_build_legacy_local_user_row",
            "_build_profile_from_legacy_user",
            "_ensure_user_profile",
            "_ensure_membership",
            "_sync_legacy_user_projection",
            "_touch_last_login",
            "update_organization_membership",
            "delete_local_user_account",
            "_cleanup_local_account",
            "append_audit_log",
            "_append_audit_log",
        ),
    ),
    (
        _auth_runtime_invitations,
        (
            "accept_invitation_for_session_payload",
            "_raise_accept_invitation_error",
            "_resolve_session_invitation_token",
            "_resolve_pending_invitation_token_for_email",
            "_list_pending_invitations_by_email",
            "list_invitations",
            "get_invitation_preview",
            "get_invitation_preview_by_email",
            "_counts_towards_active_user_limit",
            "_build_plan_upgrade_message",
            "_build_organization_plan_summary",
            "get_organization_plan_summary",
            "get_organization_invitation_dashboard",
            "list_organization_audit_logs",
            "_resolve_allowed_invitation_roles",
            "_validate_invitation_permissions",
            "_can_manage_invitation_role",
            "_filter_manageable_invitations",
            "_ensure_invitation_capacity",
            "_ensure_acceptance_capacity",
            "create_invitation",
            "_raise_create_invitation_error",
            "_expire_stale_invitations",
            "_persist_invitation_status",
            "revoke_invitation",
            "deliver_invitation_email",
            "_get_invitation_by_token",
            "_get_invitation_by_id",
            "_require_invitation_email_match",
            "_can_use_invite_password_setup",
            "_send_invitation_email",
            "_format_invitation_delivery_error",
            "_verify_password",
        ),
    ),
    (
        _auth_runtime_session,
        (
            "sign_out_session",
            "build_session_response_payload",
            "sign_in_with_password",
            "record_login_audit_log",
            "sign_up_console_user",
            "send_password_reset_email",
            "create_platform_admin_account",
            "reset_platform_admin_account_password",
            "ensure_fresh_session_payload",
            "update_console_user_profile",
            "build_session_response",
            "refresh_auth_session",
            "import_auth_session",
            "set_auth_session_cookie",
            "clear_auth_session_cookie",
            "read_signed_session_payload",
            "read_auth_context",
            "_finalize_session_payload",
            "_resolve_login_audit_log_ip_address",
            "_resolve_login_audit_log_user_agent",
        ),
    ),
)

_BOUND_GLOBAL_NAMES = (
    "DEFAULT_PHASE1_ORGANIZATION_ID",
    "get_login_audit_log_repository",
    "extract_error_message",
    "request_json",
    "_can_manage_invitation_role_impl",
    "_create_invitation_impl",
    "_deliver_invitation_email_impl",
    "_expire_stale_invitations_impl",
    "_filter_manageable_invitations_impl",
    "_persist_invitation_status_impl",
    "_raise_create_invitation_error_impl",
    "_resolve_allowed_invitation_roles_impl",
    "_revoke_invitation_impl",
    "_validate_invitation_permissions_impl",
    "_get_invitation_by_id_impl",
    "_get_invitation_by_token_impl",
    "_get_invitation_preview_impl",
    "_get_invitation_preview_by_email_impl",
    "_list_invitations_impl",
    "_list_pending_invitations_by_email_impl",
    "_normalize_invitation_row_impl",
    "_can_use_invite_password_setup_impl",
    "_raise_accept_invitation_error_invite_impl",
    "_require_invitation_email_match_impl",
    "_resolve_pending_invitation_token_for_email_impl",
    "_resolve_session_invitation_token_impl",
    "_create_platform_admin_account_impl",
    "_build_profile_from_legacy_user_lookup_impl",
    "_get_local_user_impl",
    "_get_membership_row_impl",
    "_get_user_profile_impl",
    "_ensure_membership_impl",
    "_ensure_user_profile_impl",
    "_sync_legacy_user_projection_impl",
    "_update_local_user_profile_impl",
    "_build_session_response_impl",
    "_ensure_fresh_session_payload_impl",
    "_refresh_auth_session_impl",
    "_send_password_reset_email_impl",
    "_sign_in_with_password_impl",
    "_sign_up_console_user_impl",
    "_update_console_user_profile_impl",
    "_is_missing_column_error_impl",
    "_is_missing_relation_error_impl",
    "_map_membership_role_to_legacy_role_impl",
    "_map_role_label_impl",
    "_normalize_account_status_impl",
    "_normalize_email_impl",
    "_normalize_global_role_impl",
    "_normalize_local_user_status_impl",
    "_normalize_membership_status_impl",
    "_normalize_org_role_impl",
    "_parse_datetime_value_impl",
    "_get_organization_impl",
    "_normalize_limit_value_impl",
    "_normalize_organization_row_impl",
    "_normalize_plan_code_impl",
    "_resolve_next_plan_code_impl",
    "_build_organization_plan_summary_impl",
    "_build_plan_upgrade_message_impl",
    "_counts_towards_active_user_limit_impl",
    "_ensure_acceptance_capacity_impl",
    "_ensure_invitation_capacity_impl",
    "_get_organization_invitation_dashboard_impl",
    "_get_organization_plan_summary_impl",
    "_build_legacy_local_user_row_impl",
    "_list_local_users_impl",
    "_list_local_users_overview_impl",
    "_list_organization_audit_logs_impl",
    "_normalize_local_user_row_impl",
    "_query_local_user_rows_impl",
    "_bootstrap_local_auth_path_impl",
    "_build_invitation_initial_password_impl",
    "_build_invite_url_impl",
    "_build_local_bootstrap_session_impl",
    "_can_use_local_bootstrap_fallback_impl",
    "_hash_local_bootstrap_password_impl",
    "_has_local_bootstrap_password_impl",
    "_load_local_bootstrap_auth_record_impl",
    "_local_bootstrap_auth_user_id_impl",
    "_register_local_bootstrap_password_impl",
    "_resolve_local_bootstrap_auth_user_id_impl",
    "_save_local_bootstrap_auth_record_impl",
    "_verify_local_bootstrap_password_impl",
    "_build_session_response_payload_impl",
    "_decode_signed_payload_impl",
    "_encode_signed_payload_impl",
    "_read_access_token_expires_in_impl",
    "time",
    "_auth_runtime_core",
    "_auth_runtime_directory",
    "_auth_runtime_invitations",
    "_auth_runtime_session",
)

_EXPORT_NAMES = tuple(name for _module, names in _EXPORT_GROUPS for name in names)
_SYNC_NAMES = _EXPORT_NAMES + _BOUND_GLOBAL_NAMES
__all__ = _EXPORT_NAMES


def _bind_runtime(module, namespace: dict[str, object]) -> None:
    for name in _SYNC_NAMES:
        module.__dict__[name] = namespace[name]


class _AuthRuntimeFacadeModule(types.ModuleType):
    def __setattr__(self, name: str, value) -> None:
        super().__setattr__(name, value)
        if name in _SYNC_NAMES:
            for module in _RUNTIME_MODULES:
                module.__dict__[name] = value


def initialize_auth_runtime_facade(namespace: dict[str, object]) -> None:
    for module, names in _EXPORT_GROUPS:
        for name in names:
            namespace[name] = getattr(module, name)
    for name in _BOUND_GLOBAL_NAMES:
        namespace[name] = globals()[name]
    namespace["__all__"] = __all__
    module = sys.modules[namespace["__name__"]]
    if not isinstance(module, _AuthRuntimeFacadeModule):
        module.__class__ = _AuthRuntimeFacadeModule
    for module in _RUNTIME_MODULES:
        _bind_runtime(module, namespace)
