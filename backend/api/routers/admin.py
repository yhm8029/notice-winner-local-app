from __future__ import annotations

import time
from uuid import UUID

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from fastapi import status

from backend.perf_runtime import log_google_sheets_admin_duration
from backend.api.schemas import AuthAdminAccountCreateRequest
from backend.api.schemas import AuthAdminAccountItem
from backend.api.schemas import AuthAdminAccountPasswordResetRequest
from backend.api.schemas import AuthAdminAccountPasswordResetResponse
from backend.api.schemas import DownloadAuditLogListResponse
from backend.api.schemas import AdminGoogleSheetPayloadResponse
from backend.api.schemas import AdminGoogleSheetsBootstrapResponse
from backend.api.schemas import AdminGoogleSheetsSyncResponse
from backend.api.schemas import AdminGoogleSheetTabItem
from backend.api.schemas import ErrorResponse
from backend.api.schemas import LoginAuditLogListResponse
from backend.api.schemas import OrganizationAdminBootstrapResponse
from backend.api.schemas import AuthAuditLogSliceResponse
from backend.api.schemas import DownloadAuditLogSliceResponse
from backend.api.schemas import LoginAuditLogSliceResponse

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
            message="플랫폼 관리자만 계정을 생성할 수 있습니다.",
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
            message="플랫폼 관리자만 계정 비밀번호를 재설정할 수 있습니다.",
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
            message="사용자를 찾을 수 없습니다.",
        )
    target_email = str(target_user.get("email") or "").strip().lower()
    if target_email == admin_app.bootstrap_platform_admin_email():
        raise admin_app.ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="auth_user_protected",
            message="부트스트랩 플랫폼 운영자 계정은 비밀번호를 재설정할 수 없습니다.",
        )
    if actor.user_id is not None and str(target_user.get("id") or "").strip() == str(actor.user_id):
        raise admin_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_user_self_password_reset_forbidden",
            message="자기 계정 비밀번호는 이 화면에서 재설정할 수 없습니다.",
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
            message="관리자만 다운로드 감사 로그를 조회할 수 있습니다.",
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
            message="관리자만 로그인 감사 로그를 조회할 수 있습니다.",
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
            message="관리자만 조직 운영 패널 데이터를 조회할 수 있습니다.",
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


@router.get(
    "/api/admin/google-sheets/bootstrap",
    response_model=AdminGoogleSheetsBootstrapResponse,
    responses={403: {"model": ErrorResponse}},
)
def get_admin_google_sheets_bootstrap(request: Request) -> AdminGoogleSheetsBootstrapResponse:
    started = time.perf_counter()
    admin_app = _app_module()
    actor = admin_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise admin_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 Google Sheets 상태를 조회할 수 있습니다.",
        )

    config = admin_app.load_google_sheets_admin_config()
    if not config:
        log_google_sheets_admin_duration(
            event="admin_bootstrap_route",
            duration=time.perf_counter() - started,
            path="/api/admin/google-sheets/bootstrap",
        )
        return AdminGoogleSheetsBootstrapResponse(
            enabled=False,
            sync_status="not_configured",
            tabs=[],
        )

    admin_app.ensure_google_sheets_admin_sync_worker_started(config=config)
    snapshot = admin_app.read_google_sheets_admin_snapshot(config=config)
    snapshot = snapshot or {}

    sheets = dict(snapshot.get("sheets") or {})
    tabs_source = list(snapshot.get("tabs") or [])
    if not tabs_source and sheets:
        def _fallback_sheet_sort_key(item: tuple[str, dict]) -> tuple[int, int, str]:
            key, sheet = item
            raw_sheet_id = sheet.get("sheet_id")
            try:
                sheet_id = int(raw_sheet_id or 0)
            except (TypeError, ValueError):
                sheet_id = 0
            display_title = str(sheet.get("display_title") or sheet.get("raw_title") or key or "")
            return (0 if sheet_id > 0 else 1, sheet_id if sheet_id > 0 else 0, display_title)

        tabs_source = [
            {
                "key": key,
                "sheet_id": sheet.get("sheet_id"),
                "raw_title": sheet.get("raw_title"),
                "display_title": sheet.get("display_title"),
                "sheet_order": index,
            }
            for index, (key, sheet) in enumerate(sorted(sheets.items(), key=_fallback_sheet_sort_key), start=1)
        ]

    tabs: list[AdminGoogleSheetTabItem] = []
    for tab in tabs_source:
        tab_key = str((tab or {}).get("key") or "").strip()
        sheet = dict(sheets.get(tab_key) or {})
        tabs.append(
            AdminGoogleSheetTabItem(
                key=tab_key,
                sheet_id=(tab or {}).get("sheet_id"),
                raw_title=str((tab or {}).get("raw_title") or ""),
                display_title=str((tab or {}).get("display_title") or ""),
                sheet_order=int((tab or {}).get("sheet_order") or 0),
                row_count=int(sheet.get("row_count") or 0),
                column_count=int(sheet.get("column_count") or 0),
            )
        )

    log_google_sheets_admin_duration(
        event="admin_bootstrap_route",
        duration=time.perf_counter() - started,
        path="/api/admin/google-sheets/bootstrap",
    )
    return AdminGoogleSheetsBootstrapResponse(
        enabled=bool(snapshot.get("enabled", True)),
        source_title=str(snapshot.get("source_title") or ""),
        source_url=str(snapshot.get("source_url") or ""),
        sync_status=str(snapshot.get("sync_status") or "initializing"),
        last_successful_sync_at=snapshot.get("last_successful_sync_at"),
        last_failed_sync_at=snapshot.get("last_failed_sync_at"),
        last_error=str(snapshot.get("last_error") or ""),
        tabs=tabs,
    )


@router.get(
    "/api/admin/google-sheets/sheets/{sheet_key}",
    response_model=AdminGoogleSheetPayloadResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def get_admin_google_sheets_sheet_payload(
    request: Request,
    sheet_key: str,
) -> AdminGoogleSheetPayloadResponse:
    started = time.perf_counter()
    admin_app = _app_module()
    actor = admin_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise admin_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 Google Sheets 내용을 조회할 수 있습니다.",
        )

    config = admin_app.load_google_sheets_admin_config()
    if not config:
        raise admin_app.ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="google_sheets_not_configured",
            message="Google Sheets 연동이 설정되지 않았습니다.",
        )

    admin_app.ensure_google_sheets_admin_sync_worker_started(config=config)
    snapshot = admin_app.read_google_sheets_admin_snapshot(config=config)
    if not snapshot:
        raise admin_app.ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="google_sheets_not_ready",
            message="Google Sheets 동기화가 아직 완료되지 않았습니다.",
        )
    sheets = dict(snapshot.get("sheets") or {})
    sheet_payload = sheets.get(sheet_key)
    if not sheet_payload:
        raise admin_app.ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="google_sheet_not_found",
            message="요청한 시트를 찾을 수 없습니다.",
        )

    payload = dict(sheet_payload or {})
    header_cells = list(payload.get("header_cells") or [])
    row_cells = list(payload.get("row_cells") or [])
    log_google_sheets_admin_duration(
        event="admin_sheet_payload_route",
        duration=time.perf_counter() - started,
        path=f"/api/admin/google-sheets/sheets/{sheet_key}",
        sheet_key=sheet_key,
    )
    return AdminGoogleSheetPayloadResponse(
        key=sheet_key,
        synced_at=snapshot.get("last_successful_sync_at"),
        sheet_id=payload.get("sheet_id"),
        raw_title=str(payload.get("raw_title") or ""),
        display_title=str(payload.get("display_title") or ""),
        headers=list(payload.get("headers") or []),
        header_cells=header_cells,
        rows=list(payload.get("rows") or []),
        row_cells=row_cells,
        row_count=int(payload.get("row_count") or 0),
        column_count=int(payload.get("column_count") or 0),
    )


@router.post(
    "/api/admin/google-sheets/sync",
    response_model=AdminGoogleSheetsSyncResponse,
    responses={403: {"model": ErrorResponse}},
)
def post_admin_google_sheets_sync(request: Request) -> AdminGoogleSheetsSyncResponse:
    admin_app = _app_module()
    actor = admin_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise admin_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 Google Sheets 동기화를 실행할 수 있습니다.",
        )

    config = admin_app.load_google_sheets_admin_config()
    if not config:
        return AdminGoogleSheetsSyncResponse(started=False, sync_status="not_configured")

    started = bool(admin_app.queue_google_sheets_admin_sync_now(config=config))
    return AdminGoogleSheetsSyncResponse(
        started=started,
        sync_status="queued" if started else "already_running",
    )
