from __future__ import annotations

from fastapi import BackgroundTasks
from uuid import UUID

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from fastapi import Response
from fastapi import status

from backend.api.schemas import AuthAuditLogListResponse
from backend.api.schemas import AuthCredentialRequest
from backend.api.schemas import AuthInvitationAcceptRequest
from backend.api.schemas import AuthInvitationCreateRequest
from backend.api.schemas import AuthInvitationItem
from backend.api.schemas import AuthInvitationListResponse
from backend.api.schemas import AuthInvitationPreviewResponse
from backend.api.schemas import AuthOrganizationUserItem
from backend.api.schemas import AuthOrganizationUserListResponse
from backend.api.schemas import AuthOrganizationUserStatusUpdateRequest
from backend.api.schemas import AuthOrganizationUserUpdateRequest
from backend.api.schemas import AuthPasswordResetRequest
from backend.api.schemas import AuthProfileUpdateRequest
from backend.api.schemas import AuthSessionImportRequest
from backend.api.schemas import AuthSessionResponse
from backend.api.schemas import ErrorResponse
from backend.api.schemas import MessageResponse

router = APIRouter()


def _app_module():
    from backend.api import app as auth_app

    return auth_app


@router.get(
    "/api/auth/session",
    response_model=AuthSessionResponse,
)
def get_auth_session(request: Request, response: Response) -> AuthSessionResponse:
    auth_app = _app_module()
    try:
        payload = auth_app.build_session_response(request, response)
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    return AuthSessionResponse.model_validate(payload)


@router.post(
    "/api/auth/session/import",
    response_model=AuthSessionResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def post_auth_session_import(payload: AuthSessionImportRequest, response: Response) -> AuthSessionResponse:
    auth_app = _app_module()
    try:
        session_payload = auth_app.import_auth_session(
            access_token=payload.access_token,
            refresh_token=payload.refresh_token,
        )
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    auth_app.set_auth_session_cookie(response, session_payload)
    return AuthSessionResponse.model_validate(auth_app.build_session_response_payload(session_payload))


@router.post(
    "/api/auth/sign-in",
    response_model=AuthSessionResponse,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def post_auth_sign_in(request: Request, payload: AuthCredentialRequest, response: Response) -> AuthSessionResponse:
    auth_app = _app_module()
    try:
        session_payload = auth_app.sign_in_with_password(
            email=payload.email,
            password=payload.password,
            invite_token=payload.invite_token,
            request_host=str(getattr(request.client, "host", "") or ""),
        )
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    auth_app.set_auth_session_cookie(response, session_payload)
    auth_app._dispatch_background(
        auth_app.record_login_audit_log,
        request=request,
        session_payload=dict(session_payload),
    )
    return AuthSessionResponse.model_validate(auth_app.build_session_response_payload(session_payload))


@router.post(
    "/api/auth/sign-up",
    response_model=AuthSessionResponse,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def post_auth_sign_up(request: Request, payload: AuthCredentialRequest, response: Response) -> AuthSessionResponse:
    auth_app = _app_module()
    try:
        session_payload = auth_app.sign_up_console_user(
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
            invite_token=payload.invite_token,
            request_host=str(getattr(request.client, "host", "") or ""),
        )
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    auth_app.set_auth_session_cookie(response, session_payload)
    return AuthSessionResponse.model_validate(auth_app.build_session_response_payload(session_payload))


@router.post(
    "/api/auth/password-reset",
    response_model=MessageResponse,
    responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def post_auth_password_reset(request: Request, payload: AuthPasswordResetRequest) -> MessageResponse:
    auth_app = _app_module()
    try:
        result = auth_app.send_password_reset_email(
            email=payload.email,
            request_host=str(getattr(request.client, "host", "") or ""),
        )
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    return MessageResponse.model_validate(result)


@router.post(
    "/api/auth/sign-out",
    response_model=AuthSessionResponse,
)
def post_auth_sign_out(request: Request, response: Response) -> AuthSessionResponse:
    auth_app = _app_module()
    try:
        auth_app.sign_out_session(auth_app.read_signed_session_payload(request))
    except auth_app.AuthRuntimeError:
        pass
    auth_app.clear_auth_session_cookie(response)
    return AuthSessionResponse.model_validate(auth_app.build_auth_status_response())


@router.get(
    "/api/auth/invitations/preview",
    response_model=AuthInvitationPreviewResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_auth_invitation_preview(invite_token: str) -> AuthInvitationPreviewResponse:
    auth_app = _app_module()
    try:
        item = auth_app.get_invitation_preview(invite_token=invite_token)
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    return AuthInvitationPreviewResponse.model_validate(item)


@router.get(
    "/api/auth/invitations/preview-by-email",
    response_model=AuthInvitationPreviewResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def get_auth_invitation_preview_by_email(email: str) -> AuthInvitationPreviewResponse:
    auth_app = _app_module()
    try:
        item = auth_app.get_invitation_preview_by_email(email=email)
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    return AuthInvitationPreviewResponse.model_validate(item)


@router.patch(
    "/api/auth/profile",
    response_model=AuthSessionResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def patch_auth_profile(
    request: Request,
    response: Response,
    payload: AuthProfileUpdateRequest,
) -> AuthSessionResponse:
    auth_app = _app_module()
    try:
        session_payload = auth_app.ensure_fresh_session_payload(request, response)
        updated_session = auth_app.update_console_user_profile(
            session_payload=session_payload,
            display_name=payload.display_name,
            mobile_phone=payload.mobile_phone,
            office_phone=payload.office_phone,
            current_password=payload.current_password,
            password=payload.password,
            invite_token=payload.invite_token,
        )
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    auth_app.set_auth_session_cookie(response, updated_session)
    return AuthSessionResponse.model_validate(auth_app.build_session_response_payload(updated_session))


@router.get(
    "/api/auth/invitations",
    response_model=AuthInvitationListResponse,
)
def get_auth_invitations(request: Request) -> AuthInvitationListResponse:
    auth_app = _app_module()
    actor = auth_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise auth_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 초대 목록을 조회할 수 있습니다.",
        )
    try:
        dashboard = auth_app.get_organization_invitation_dashboard(
            organization_id=str(actor.organization_id),
            actor_role=str(actor.role or ""),
        )
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    return AuthInvitationListResponse(
        items=[auth_app._to_auth_invitation_model(request, item) for item in list(dashboard.get("items") or [])],
        plan_summary=auth_app._to_auth_org_plan_summary_model(dict(dashboard.get("plan_summary") or {})),
    )


@router.get(
    "/api/auth/audit-logs",
    response_model=AuthAuditLogListResponse,
)
def get_auth_audit_logs(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
) -> AuthAuditLogListResponse:
    auth_app = _app_module()
    actor = auth_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise auth_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 조직 감사 로그를 조회할 수 있습니다.",
        )
    try:
        items = auth_app.list_organization_audit_logs(
            organization_id=str(actor.organization_id),
            limit=limit,
        )
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    return AuthAuditLogListResponse(items=[auth_app._to_auth_audit_log_model(item) for item in items])


@router.post(
    "/api/auth/invitations",
    response_model=AuthInvitationItem,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def post_auth_invitation(
    background_tasks: BackgroundTasks,
    request: Request,
    payload: AuthInvitationCreateRequest,
) -> AuthInvitationItem:
    auth_app = _app_module()
    actor = auth_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise auth_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 사용자를 초대할 수 있습니다.",
        )
    normalized_target_email = str(payload.email or "").strip().lower()
    if normalized_target_email and normalized_target_email == str(actor.email or "").strip().lower():
        raise auth_app.ApiError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="validation_error",
            message="현재 로그인한 내 이메일로는 초대장을 만들 수 없습니다.",
        )
    send_email = auth_app.invitation_email_delivery_enabled()
    try:
        item = auth_app.create_invitation(
            organization_id=str(actor.organization_id),
            created_by=str(actor.user_id or ""),
            actor_role=str(actor.role or ""),
            email=payload.email,
            role=payload.role,
            display_name=payload.display_name,
            team_name=payload.team_name,
            job_title=payload.job_title,
            expires_in_days=payload.expires_in_days,
            invite_url_base=auth_app._resolve_public_app_base_url(request),
            send_email=False,
        )
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    if send_email:
        item["delivery_status"] = "queued"
        item["delivery_message"] = "초대 메일 발송을 시작했습니다. 도착하지 않으면 링크 복사로 직접 전달하세요."
        background_tasks.add_task(
            auth_app.deliver_invitation_email,
            email=str(item.get("email") or payload.email or ""),
            invite_url=str(item.get("invite_url") or ""),
            display_name=str(item.get("display_name") or payload.display_name or ""),
        )
    auth_app._clear_organization_admin_bootstrap_cache(organization_id=actor.organization_id)
    return auth_app._to_auth_invitation_model(request, item)


@router.post(
    "/api/auth/invitations/accept",
    response_model=AuthSessionResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def post_auth_invitation_accept(
    request: Request,
    response: Response,
    payload: AuthInvitationAcceptRequest,
) -> AuthSessionResponse:
    auth_app = _app_module()
    try:
        session_payload = auth_app.ensure_fresh_session_payload(request, response)
        updated_session = auth_app.accept_invitation_for_session_payload(
            session_payload=session_payload,
            invite_token=payload.invite_token,
        )
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    auth_app.set_auth_session_cookie(response, updated_session)
    auth_app._clear_organization_admin_bootstrap_cache(organization_id=updated_session.get("organization_id"))
    return AuthSessionResponse.model_validate(auth_app.build_session_response_payload(updated_session))


@router.post(
    "/api/auth/invitations/{invitation_id}/revoke",
    response_model=AuthInvitationItem,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def post_auth_invitation_revoke(
    request: Request,
    invitation_id: UUID,
) -> AuthInvitationItem:
    auth_app = _app_module()
    actor = auth_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise auth_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 초대를 철회할 수 있습니다.",
        )
    try:
        item = auth_app.revoke_invitation(
            organization_id=str(actor.organization_id),
            invitation_id=str(invitation_id),
            actor_user_id=str(actor.user_id or ""),
            actor_role=str(actor.role or ""),
        )
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    auth_app._clear_organization_admin_bootstrap_cache(organization_id=actor.organization_id)
    return auth_app._to_auth_invitation_model(request, item)


@router.get(
    "/api/auth/users",
    response_model=AuthOrganizationUserListResponse,
)
def get_auth_organization_users(
    request: Request,
    include_inactive: bool = False,
) -> AuthOrganizationUserListResponse:
    auth_app = _app_module()
    actor = auth_app._resolve_sales_actor(request)
    if include_inactive and not actor.is_admin:
        raise auth_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 비활성 사용자 목록을 조회할 수 있습니다.",
        )
    items = auth_app.list_local_users(organization_id=str(actor.organization_id), include_inactive=include_inactive)
    return AuthOrganizationUserListResponse(items=[auth_app._to_auth_org_user_model(item) for item in items])


@router.patch(
    "/api/auth/users/{user_id}/status",
    response_model=AuthOrganizationUserItem,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def patch_auth_organization_user_status(
    request: Request,
    user_id: UUID,
    payload: AuthOrganizationUserStatusUpdateRequest,
) -> AuthOrganizationUserItem:
    auth_app = _app_module()
    actor = auth_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise auth_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 사용자 상태를 변경할 수 있습니다.",
        )

    users = auth_app.list_local_users(organization_id=str(actor.organization_id), include_inactive=True)
    target_user = next((item for item in users if str(item.get("id") or "") == str(user_id)), None)
    if target_user is None:
        raise auth_app.ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="auth_user_not_found",
            message="사용자를 찾을 수 없습니다.",
        )
    if str(target_user.get("email") or "").strip().lower() == auth_app.bootstrap_platform_admin_email():
        raise auth_app.ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="auth_user_protected",
            message="부트스트랩 플랫폼 운영자 계정은 비활성화할 수 없습니다.",
        )
    if actor.user_id is not None and str(target_user.get("id") or "") == str(actor.user_id):
        raise auth_app.ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="auth_user_self_status_change_forbidden",
            message="자기 계정 상태는 이 화면에서 변경할 수 없습니다.",
        )

    normalized_status = str(payload.status or "").strip().lower()
    if normalized_status in {"inactive", "deactivated"}:
        try:
            summary_items = auth_app._get_sales_claim_repository().summarize_by_user(
                organization_id=actor.organization_id
            )
        except auth_app.SalesClaimRepositoryError as exc:
            auth_app._repository_error(str(exc))
        active_claims = next(
            (
                int(item.get("active_project_count") or 0)
                for item in summary_items
                if str(item.get("user_id") or "") == str(user_id)
            ),
            0,
        )
        if active_claims > 0:
            raise auth_app.ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="auth_user_has_active_sales_claims",
                message="이 사용자가 맡고 있는 진행 중 영업이 남아 있습니다. 먼저 이관하거나 해제하세요.",
            )

    try:
        updated = auth_app.update_local_user_status(
            organization_id=str(actor.organization_id),
            user_id=str(user_id),
            status=payload.status,
        )
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    auth_app._invalidate_sales_overview_cache(organization_id=actor.organization_id)
    auth_app._clear_organization_admin_bootstrap_cache(organization_id=actor.organization_id)
    return auth_app._to_auth_org_user_model(updated)


@router.patch(
    "/api/auth/users/{user_id}",
    response_model=AuthOrganizationUserItem,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def patch_auth_organization_user(
    request: Request,
    user_id: UUID,
    payload: AuthOrganizationUserUpdateRequest,
) -> AuthOrganizationUserItem:
    auth_app = _app_module()
    actor = auth_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise auth_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 조직 사용자 정보를 수정할 수 있습니다.",
        )
    users = auth_app.list_local_users(organization_id=str(actor.organization_id), include_inactive=True)
    target_user = next((item for item in users if str(item.get("id") or "") == str(user_id)), None)
    if target_user is None:
        raise auth_app.ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="auth_user_not_found",
            message="사용자를 찾을 수 없습니다.",
        )
    is_bootstrap_user = str(target_user.get("email") or "").strip().lower() == auth_app.bootstrap_platform_admin_email()
    is_self = actor.user_id is not None and str(target_user.get("id") or "") == str(actor.user_id)
    if is_bootstrap_user and (payload.role or payload.membership_status):
        raise auth_app.ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="auth_user_protected",
            message="부트스트랩 플랫폼 운영자 계정의 권한/상태는 여기서 수정할 수 없습니다.",
        )
    if is_self and (payload.role or payload.membership_status):
        raise auth_app.ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="auth_user_self_role_change_forbidden",
            message="자기 계정의 역할/상태는 이 화면에서 수정할 수 없습니다.",
        )
    normalized_membership_status = str(payload.membership_status or "").strip().lower()
    if normalized_membership_status in {"inactive", "deactivated"}:
        try:
            summary_items = auth_app._get_sales_claim_repository().summarize_by_user(
                organization_id=actor.organization_id
            )
        except auth_app.SalesClaimRepositoryError as exc:
            auth_app._repository_error(str(exc))
        active_claims = next(
            (
                int(item.get("active_project_count") or 0)
                for item in summary_items
                if str(item.get("user_id") or "") == str(user_id)
            ),
            0,
        )
        if active_claims > 0:
            raise auth_app.ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="auth_user_has_active_sales_claims",
                message="이 사용자가 맡고 있는 진행 중 영업이 남아 있습니다. 먼저 이관하거나 해제하세요.",
            )
    try:
        updated = auth_app.update_organization_membership(
            organization_id=str(actor.organization_id),
            user_id=str(user_id),
            role=payload.role,
            membership_status=payload.membership_status,
            team_name=payload.team_name,
            job_title=payload.job_title,
            actor_user_id=str(actor.user_id or ""),
        )
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    auth_app._invalidate_sales_overview_cache(organization_id=actor.organization_id)
    auth_app._clear_organization_admin_bootstrap_cache(organization_id=actor.organization_id)
    return auth_app._to_auth_org_user_model(updated)


@router.delete(
    "/api/auth/users/{user_id}",
    response_model=MessageResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def delete_auth_organization_user(
    request: Request,
    user_id: UUID,
) -> MessageResponse:
    auth_app = _app_module()
    actor = auth_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise auth_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 계정을 삭제할 수 있습니다.",
        )
    users = auth_app.list_local_users(organization_id=str(actor.organization_id), include_inactive=True)
    target_user = next((item for item in users if str(item.get("id") or "") == str(user_id)), None)
    if target_user is None:
        raise auth_app.ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="auth_user_not_found",
            message="사용자를 찾을 수 없습니다.",
        )
    if str(target_user.get("email") or "").strip().lower() == auth_app.bootstrap_platform_admin_email():
        raise auth_app.ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="auth_user_protected",
            message="부트스트랩 플랫폼 운영자 계정은 삭제할 수 없습니다.",
        )
    if actor.user_id is not None and str(target_user.get("id") or "") == str(actor.user_id):
        raise auth_app.ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="auth_user_self_delete_forbidden",
            message="자기 계정은 이 화면에서 삭제할 수 없습니다.",
        )
    try:
        auth_app.delete_local_user_account(
            organization_id=str(actor.organization_id),
            user_id=str(user_id),
        )
    except auth_app.AuthRuntimeError as exc:
        raise auth_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    auth_app._invalidate_sales_overview_cache(organization_id=actor.organization_id)
    auth_app._clear_organization_admin_bootstrap_cache(organization_id=actor.organization_id)
    return MessageResponse(message="계정을 삭제했습니다.")
