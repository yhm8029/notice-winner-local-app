from __future__ import annotations

import os
from typing import Any

from fastapi import BackgroundTasks
from fastapi import Request
from fastapi import status

from backend.api.schemas import AuthInvitationCreateRequest
from backend.api.schemas import AuthAuditLogItem
from backend.api.schemas import AuthInvitationItem
from backend.api.schemas import AuthOrganizationPlanSummary
from backend.api.schemas import AuthOrganizationUserItem
from backend.api.schemas import DownloadAuditLogItem
from backend.api.schemas import LoginAuditLogItem
from backend.api.schemas import SalesClaimSummaryProjectItem
from backend.api.support.runtime_common import ApiError
from backend.api.support.runtime_common import _backend_api_app
from backend.services.api_response_model_backend import to_auth_audit_log_model as _to_auth_audit_log_model_impl
from backend.services.api_response_model_backend import to_auth_invitation_model as _to_auth_invitation_model_impl
from backend.services.api_response_model_backend import to_auth_org_plan_summary_model as _to_auth_org_plan_summary_model_impl
from backend.services.api_response_model_backend import to_auth_org_user_model as _to_auth_org_user_model_impl
from backend.services.api_response_model_backend import to_sales_claim_summary_project_model as _to_sales_claim_summary_project_model_impl


def _app_override(name: str, original: Any) -> Any | None:
    value = getattr(_backend_api_app, name, None)
    if value is None or value is original:
        return None
    return value


def _normalize_public_app_url(value: str, *, default_scheme: str = "https") -> str:
    raw = str(value or "").strip().rstrip("/")
    if not raw:
        return ""
    if "://" in raw:
        return raw
    return f"{default_scheme}://{raw}"


def _resolve_public_app_base_url(request: Request) -> str:
    override = _app_override("_resolve_public_app_base_url", _RESOLVE_PUBLIC_APP_BASE_URL_ORIGINAL)
    if override is not None:
        return override(request)
    for env_name in ("PUBLIC_APP_URL", "APP_BASE_URL", "FRONTEND_PUBLIC_URL"):
        resolved = _normalize_public_app_url(os.getenv(env_name, "").strip())
        if resolved:
            return resolved
    for env_name in ("VERCEL_PROJECT_PRODUCTION_URL", "VERCEL_BRANCH_URL", "VERCEL_URL"):
        resolved = _normalize_public_app_url(os.getenv(env_name, "").strip())
        if resolved:
            return resolved
    forwarded_host = str(request.headers.get("x-forwarded-host", "") or "").split(",")[0].strip()
    if forwarded_host:
        forwarded_proto = str(request.headers.get("x-forwarded-proto", "") or "").split(",")[0].strip() or request.url.scheme or "https"
        return _normalize_public_app_url(forwarded_host, default_scheme=forwarded_proto)
    origin = _normalize_public_app_url(str(request.headers.get("origin", "") or "").strip(), default_scheme=request.url.scheme or "https")
    if origin:
        return origin
    return str(request.base_url).rstrip("/")


def _to_auth_invitation_model(request: Request, item: dict[str, Any]) -> AuthInvitationItem:
    override = _app_override("_to_auth_invitation_model", _TO_AUTH_INVITATION_MODEL_ORIGINAL)
    if override is not None:
        return override(request, item)
    return _to_auth_invitation_model_impl(
        invite_url_base=_resolve_public_app_base_url(request),
        item=item,
        auth_invitation_item_cls=AuthInvitationItem,
    )


def post_auth_invitation(
    background_tasks: BackgroundTasks,
    request: Request,
    payload: AuthInvitationCreateRequest,
) -> AuthInvitationItem:
    actor = _backend_api_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="\uad00\ub9ac\uc790\ub9cc \uc0ac\uc6a9\uc790\ub97c \ucd08\ub300\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
        )
    normalized_target_email = str(payload.email or "").strip().lower()
    if normalized_target_email and normalized_target_email == str(actor.email or "").strip().lower():
        raise ApiError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="validation_error",
            message="\ud604\uc7ac \ub85c\uadf8\uc778\ud55c \ub0b4 \uc774\uba54\uc77c\ub85c\ub294 \ucd08\ub300\uc7a5\uc744 \ub9cc\ub4e4 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.",
        )
    send_email = _backend_api_app.invitation_email_delivery_enabled()
    try:
        item = _backend_api_app.create_invitation(
            organization_id=str(actor.organization_id),
            created_by=str(actor.user_id or ""),
            actor_role=str(actor.role or ""),
            email=payload.email,
            role=payload.role,
            display_name=payload.display_name,
            team_name=payload.team_name,
            job_title=payload.job_title,
            expires_in_days=payload.expires_in_days,
            invite_url_base=_resolve_public_app_base_url(request),
            send_email=False,
        )
    except _backend_api_app.AuthRuntimeError as exc:
        raise ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    if send_email:
        item["delivery_status"] = "queued"
        item["delivery_message"] = "\ucd08\ub300 \uba54\uc77c \ubc1c\uc1a1\uc744 \uc2dc\uc791\ud588\uc2b5\ub2c8\ub2e4. \ub3c4\ucc29\ud558\uc9c0 \uc54a\uc73c\uba74 \ub9c1\ud06c \ubcf5\uc0ac\ub85c \uc9c1\uc811 \uc804\ub2ec\ud558\uc138\uc694."
        background_tasks.add_task(
            _backend_api_app.deliver_invitation_email,
            email=str(item.get("email") or payload.email or ""),
            invite_url=str(item.get("invite_url") or ""),
            display_name=str(item.get("display_name") or payload.display_name or ""),
        )
    return _to_auth_invitation_model(request, item)


def _to_auth_org_user_model(item: dict[str, Any]) -> AuthOrganizationUserItem:
    return _to_auth_org_user_model_impl(item, auth_org_user_item_cls=AuthOrganizationUserItem)


def _to_auth_org_plan_summary_model(item: dict[str, Any]) -> AuthOrganizationPlanSummary:
    return _to_auth_org_plan_summary_model_impl(item, auth_org_plan_summary_cls=AuthOrganizationPlanSummary)


def _to_auth_audit_log_model(item: dict[str, Any]) -> AuthAuditLogItem:
    return _to_auth_audit_log_model_impl(item, auth_audit_log_item_cls=AuthAuditLogItem)


def _to_download_audit_log_model(item: dict[str, Any]) -> DownloadAuditLogItem:
    return DownloadAuditLogItem(
        id=item.get("id"),
        organization_id=item.get("organization_id"),
        user_id=item.get("user_id"),
        user_email=str(item.get("user_email") or ""),
        user_role=str(item.get("user_role") or ""),
        download_scope=str(item.get("download_scope") or ""),
        download_format=str(item.get("download_format") or ""),
        source_page=str(item.get("source_page") or ""),
        file_name=str(item.get("file_name") or ""),
        created_at=item.get("created_at"),
    )


def _to_login_audit_log_model(item: dict[str, Any]) -> LoginAuditLogItem:
    return LoginAuditLogItem(
        id=item.get("id"),
        organization_id=item.get("organization_id"),
        user_id=item.get("user_id"),
        user_email=str(item.get("user_email") or ""),
        user_role=str(item.get("user_role") or ""),
        ip_address=str(item.get("ip_address") or ""),
        user_agent=str(item.get("user_agent") or ""),
        created_at=item.get("created_at"),
    )


def _to_sales_claim_summary_project_model(item: dict[str, Any]) -> SalesClaimSummaryProjectItem:
    return _to_sales_claim_summary_project_model_impl(
        item,
        sales_claim_summary_project_item_cls=SalesClaimSummaryProjectItem,
    )


_RESOLVE_PUBLIC_APP_BASE_URL_ORIGINAL = _resolve_public_app_base_url
_TO_AUTH_INVITATION_MODEL_ORIGINAL = _to_auth_invitation_model
