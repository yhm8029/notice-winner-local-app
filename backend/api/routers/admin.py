from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from fastapi import status

from backend.api.schemas import AuthAdminAccountCreateRequest
from backend.api.schemas import AuthAdminAccountItem
from backend.api.schemas import AuthAdminAccountPasswordResetRequest
from backend.api.schemas import AuthAdminAccountPasswordResetResponse
from backend.api.schemas import AuthAuditLogSliceResponse
from backend.api.schemas import DownloadAuditLogListResponse
from backend.api.schemas import DownloadAuditLogSliceResponse
from backend.api.schemas import ErrorResponse
from backend.api.schemas import LoginAuditLogListResponse
from backend.api.schemas import LoginAuditLogSliceResponse
from backend.api.schemas import OrganizationAdminBootstrapResponse

router = APIRouter()


def _app_module():
    from backend.api import app as admin_app

    return admin_app


@router.post(
    "/api/admin/accounts",
    response_model=AuthAdminAccountItem,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def post_admin_accounts(request: Request, payload: AuthAdminAccountCreateRequest) -> AuthAdminAccountItem:
    admin_app = _app_module()
    actor = admin_app._resolve_sales_actor(request)
    if str(actor.role or "").strip() != "platform_admin":
        raise admin_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="Platform admin access is required.",
        )
    try:
        item = admin_app.create_platform_admin_account(
            actor_user_id=str(actor.user_id or ""),
            actor_role=str(actor.role or ""),
            organization_id=str(actor.organization_id or ""),
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
            role=payload.role,
        )
    except admin_app.AuthRuntimeError as exc:
        raise admin_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    return AuthAdminAccountItem.model_validate({**item, "platform_admin_managed": True})


@router.post(
    "/api/admin/accounts/{user_id}/password-reset",
    response_model=AuthAdminAccountPasswordResetResponse,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def post_admin_account_password_reset(
    request: Request,
    user_id: UUID,
    payload: AuthAdminAccountPasswordResetRequest,
) -> AuthAdminAccountPasswordResetResponse:
    admin_app = _app_module()
    actor = admin_app._resolve_sales_actor(request)
    if str(actor.role or "").strip() != "platform_admin":
        raise admin_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="Platform admin access is required.",
        )
    target_user = next(
        (
            item
            for item in admin_app.list_local_users(
                organization_id=str(actor.organization_id or ""),
                include_inactive=True,
            )
            if str(item.get("id") or "").strip() == str(user_id)
        ),
        None,
    )
    if target_user is None:
        raise admin_app.ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="auth_user_not_found",
            message="User not found.",
        )
    target_email = str(target_user.get("email") or "").strip().lower()
    if target_email == admin_app.bootstrap_platform_admin_email():
        raise admin_app.ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="auth_user_protected",
            message="The bootstrap admin account password cannot be reset here.",
        )
    if actor.user_id is not None and str(target_user.get("id") or "").strip() == str(actor.user_id):
        raise admin_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_user_self_password_reset_forbidden",
            message="You cannot reset your own password from this screen.",
        )
    try:
        result = admin_app.reset_platform_admin_account_password(
            actor_user_id=str(actor.user_id or ""),
            actor_role=str(actor.role or ""),
            organization_id=str(actor.organization_id or ""),
            user_id=str(user_id),
            email=target_email,
            password=payload.password,
        )
    except admin_app.AuthRuntimeError as exc:
        raise admin_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    return AuthAdminAccountPasswordResetResponse.model_validate(result)


@router.get(
    "/api/admin/download-audit-logs",
    response_model=DownloadAuditLogListResponse,
)
def get_download_audit_logs(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
) -> DownloadAuditLogListResponse:
    admin_app = _app_module()
    actor = admin_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise admin_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="Admin access is required.",
        )
    repository = admin_app._get_download_audit_log_repository()
    try:
        items = repository.list_logs(
            organization_id=actor.organization_id,
            limit=limit,
        )
    except admin_app.DownloadAuditLogRepositoryError as exc:
        admin_app._repository_error(str(exc))
    return DownloadAuditLogListResponse(items=[admin_app._to_download_audit_log_model(item) for item in items])


@router.get(
    "/api/admin/login-audit-logs",
    response_model=LoginAuditLogListResponse,
)
def get_login_audit_logs(
    request: Request,
    limit: int = Query(default=5, ge=1, le=100),
) -> LoginAuditLogListResponse:
    admin_app = _app_module()
    actor = admin_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise admin_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="Admin access is required.",
        )
    repository = admin_app._get_login_audit_log_repository()
    try:
        items = repository.list_logs(
            organization_id=actor.organization_id,
            limit=limit,
        )
    except admin_app.LoginAuditLogRepositoryError as exc:
        admin_app._repository_error(str(exc))
    return LoginAuditLogListResponse(items=[admin_app._to_login_audit_log_model(item) for item in items])


@router.get(
    "/api/admin/organization-panel-bootstrap",
    response_model=OrganizationAdminBootstrapResponse,
)
def get_organization_panel_bootstrap(
    request: Request,
) -> OrganizationAdminBootstrapResponse:
    admin_app = _app_module()
    actor = admin_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise admin_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="Admin access is required.",
        )
    cached = admin_app._read_organization_admin_bootstrap_cache(organization_id=actor.organization_id)
    if cached is not None:
        return cached
    visible_limit = 5
    fetch_limit = visible_limit + 1
    try:
        member_items = admin_app.list_local_users(organization_id=str(actor.organization_id), include_inactive=True)
        invitation_dashboard = admin_app.get_organization_invitation_dashboard(
            organization_id=str(actor.organization_id),
            actor_role=str(actor.role or ""),
        )
        auth_audit_items = admin_app.list_organization_audit_logs(
            organization_id=str(actor.organization_id),
            limit=fetch_limit,
        )
    except admin_app.AuthRuntimeError as exc:
        raise admin_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc

    download_repository = admin_app._get_download_audit_log_repository()
    login_repository = admin_app._get_login_audit_log_repository()
    try:
        download_audit_items = download_repository.list_logs(
            organization_id=actor.organization_id,
            limit=fetch_limit,
        )
        login_audit_items = login_repository.list_logs(
            organization_id=actor.organization_id,
            limit=fetch_limit,
        )
    except admin_app.DownloadAuditLogRepositoryError as exc:
        admin_app._repository_error(str(exc))
    except admin_app.LoginAuditLogRepositoryError as exc:
        admin_app._repository_error(str(exc))

    visible_auth_audit_items, auth_has_more = admin_app._slice_items_with_has_more(
        list(auth_audit_items),
        visible_limit=visible_limit,
    )
    visible_download_audit_items, download_has_more = admin_app._slice_items_with_has_more(
        list(download_audit_items),
        visible_limit=visible_limit,
    )
    visible_login_audit_items, login_has_more = admin_app._slice_items_with_has_more(
        list(login_audit_items),
        visible_limit=visible_limit,
    )
    invitation_rows = list(invitation_dashboard.get("items") or [])
    plan_summary_row = dict(invitation_dashboard.get("plan_summary") or {})
    response_payload = OrganizationAdminBootstrapResponse(
        members=[admin_app._to_auth_org_user_model(item) for item in member_items],
        plan_summary=admin_app._to_auth_org_plan_summary_model(plan_summary_row) if plan_summary_row else None,
        invitations=[admin_app._to_auth_invitation_model(request, item) for item in invitation_rows],
        auth_audit_logs=AuthAuditLogSliceResponse(
            items=[admin_app._to_auth_audit_log_model(item) for item in visible_auth_audit_items],
            has_more=auth_has_more,
        ),
        download_audit_logs=DownloadAuditLogSliceResponse(
            items=[admin_app._to_download_audit_log_model(item) for item in visible_download_audit_items],
            has_more=download_has_more,
        ),
        login_audit_logs=LoginAuditLogSliceResponse(
            items=[admin_app._to_login_audit_log_model(item) for item in visible_login_audit_items],
            has_more=login_has_more,
        ),
        generated_at=admin_app.datetime.now(admin_app.timezone.utc),
    )
    return admin_app._write_organization_admin_bootstrap_cache(
        organization_id=actor.organization_id,
        payload=response_payload,
    )
