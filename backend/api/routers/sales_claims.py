from __future__ import annotations

from io import BytesIO
from uuid import UUID

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from fastapi import status
from fastapi.responses import StreamingResponse

from backend.api.schemas import AuthOrganizationUserItem
from backend.api.schemas import ErrorResponse
from backend.api.schemas import SalesActionRecommendationItem
from backend.api.schemas import SalesActionRecommendationListResponse
from backend.api.schemas import SalesClaimCloseRequest
from backend.api.schemas import SalesClaimItem
from backend.api.schemas import SalesClaimListResponse
from backend.api.schemas import SalesClaimMutationResponse
from backend.api.schemas import SalesClaimOverviewResponse
from backend.api.schemas import SalesClaimPatchRequest
from backend.api.schemas import SalesClaimReleaseRequest
from backend.api.schemas import SalesClaimRequest
from backend.api.schemas import SalesClaimSummaryByUserResponse
from backend.api.schemas import SalesClaimTransferRequest
from backend.services.sales_action_recommendations import ACTION_LABEL_RECHECK
from backend.services.sales_action_recommendations import build_sales_action_recommendations

router = APIRouter()


def _app_module():
    from backend.api import app as sales_claims_app

    return sales_claims_app


@router.get(
    "/api/sales-claims",
    response_model=SalesClaimListResponse,
)
def list_sales_claims(
    request: Request,
    project_id: list[UUID] | None = Query(default=None),
) -> SalesClaimListResponse:
    sales_claims_app = _app_module()
    actor = sales_claims_app._resolve_sales_actor(request)
    repository = sales_claims_app._get_sales_claim_repository()
    try:
        items = repository.list_claims(
            organization_id=actor.organization_id,
            project_ids=list(project_id or []) or None,
        )
    except sales_claims_app.SalesClaimRepositoryError as exc:
        sales_claims_app._repository_error(str(exc))
    return SalesClaimListResponse(items=[sales_claims_app._to_sales_claim_model(item) for item in items])


@router.get(
    "/api/sales-claims/overview",
    response_model=SalesClaimOverviewResponse,
)
def get_sales_claim_overview(request: Request) -> SalesClaimOverviewResponse:
    sales_claims_app = _app_module()
    actor = sales_claims_app._resolve_sales_actor(request)
    request_id = str(getattr(request.state, "request_id", "") or "")
    try:
        payload = sales_claims_app._build_sales_claim_overview_payload(
            actor=actor,
            request_id=request_id,
        )
    except sales_claims_app.SalesClaimRepositoryError as exc:
        sales_claims_app._repository_error(str(exc))
    except sales_claims_app.AuthRuntimeError as exc:
        raise sales_claims_app.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    return SalesClaimOverviewResponse(
        my_items=[SalesClaimItem.model_validate(item) for item in payload.get("my_items") or []],
        company_items=[SalesClaimItem.model_validate(item) for item in payload.get("company_items") or []],
        organization_users=[AuthOrganizationUserItem.model_validate(item) for item in payload.get("organization_users") or []],
    )


@router.get(
    "/api/sales-claims/action-recommendations",
    response_model=SalesActionRecommendationListResponse,
)
def list_sales_action_recommendations(
    request: Request,
    q: str = "",
    region: str = "",
    refresh: bool = False,
    limit: int = Query(default=30, ge=1, le=100),
) -> SalesActionRecommendationListResponse:
    sales_claims_app = _app_module()
    actor = sales_claims_app._resolve_sales_actor(request)
    try:
        all_rows = [
            row
            for row in sales_claims_app._load_global_tracker_rows(force_refresh=refresh)
            if sales_claims_app._tracker_row_belongs_to_request_organization(
                row,
                organization_id=actor.organization_id,
            )
        ]
        filtered_rows = sales_claims_app._filter_tracker_rows_for_global_scope(
            all_rows,
            q=q,
            region=region,
            exclude_auxiliary_titles=True,
            edited_only=False,
        )
    except sales_claims_app.TrackerEntryRepositoryError as exc:
        sales_claims_app._repository_error(str(exc))
    recommendations = build_sales_action_recommendations(
        filtered_rows,
        expose_internal_score=bool(getattr(actor, "is_admin", False)),
    )
    weekly_recheck_summary = _build_weekly_recheck_summary(recommendations)
    limited_items = recommendations[:limit]
    return SalesActionRecommendationListResponse(
        items=[SalesActionRecommendationItem.model_validate(item) for item in limited_items],
        total=len(recommendations),
        weekly_recheck_summary=weekly_recheck_summary,
    )


def _build_weekly_recheck_summary(items: list[dict[str, object]]) -> dict[str, int]:
    summary = {
        "total": 0,
        "over_3eok": 0,
        "one_to_3eok": 0,
        "under_1eok": 0,
    }
    for item in items:
        if ACTION_LABEL_RECHECK not in list(item.get("action_labels") or []):
            continue
        summary["total"] += 1
        amount = int(item.get("automation_amount_low_krw") or 0)
        if amount >= 300_000_000:
            summary["over_3eok"] += 1
        elif amount >= 100_000_000:
            summary["one_to_3eok"] += 1
        else:
            summary["under_1eok"] += 1
    return summary


@router.get("/api/sales-claims/export")
def download_sales_claims_workbook(
    request: Request,
    scope: str = Query(default="my"),
) -> StreamingResponse:
    sales_claims_app = _app_module()
    actor = sales_claims_app._resolve_sales_actor(request)
    normalized_scope = str(scope or "").strip().lower()
    if normalized_scope not in {"my", "company"}:
        sales_claims_app._validation_error("scope must be one of my, company")

    repository = sales_claims_app._get_sales_claim_repository()
    tracker_repository = sales_claims_app._get_tracker_repository()
    try:
        claims = repository.list_claims(
            organization_id=actor.organization_id,
            project_ids=None,
        )
    except sales_claims_app.SalesClaimRepositoryError as exc:
        sales_claims_app._repository_error(str(exc))

    if normalized_scope == "my":
        claims = [item for item in claims if sales_claims_app._sales_claim_belongs_to_actor(item, actor)]

    try:
        export_rows = sales_claims_app._build_sales_claim_export_rows(
            claims=claims,
            tracker_repository=tracker_repository,
        )
    except sales_claims_app.TrackerEntryRepositoryError as exc:
        sales_claims_app._repository_error(str(exc))

    file_name = "my_active_sales.xlsx" if normalized_scope == "my" else "company_active_sales.xlsx"
    artifact_file_helpers = sales_claims_app._load_artifact_file_helpers()
    payload = BytesIO(artifact_file_helpers["build_tracking_download_workbook_bytes"](rows=export_rows))
    sales_claims_app._record_download_audit_log(
        actor=actor,
        download_scope=normalized_scope,
        download_format="xlsx",
        source_page="my_active_sales" if normalized_scope == "my" else "company_active_sales",
        file_name=file_name,
    )
    return StreamingResponse(
        payload,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.post(
    "/api/sales-claims/projects/{project_id}/claim",
    response_model=SalesClaimMutationResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def claim_sales_project(
    request: Request,
    project_id: UUID,
    payload: SalesClaimRequest,
) -> SalesClaimMutationResponse:
    sales_claims_app = _app_module()
    actor = sales_claims_app._resolve_sales_actor(request)
    repository = sales_claims_app._get_sales_claim_repository()
    try:
        changed, claim = repository.claim_project(
            actor=actor,
            project_id=project_id,
            source_entry_id=payload.source_entry_id,
            source_run_id=payload.source_run_id,
            project_name=payload.project_name.strip(),
            estimated_amount_text=payload.estimated_amount_text.strip(),
        )
    except sales_claims_app.SalesClaimConflictError as exc:
        raise sales_claims_app.ApiError(status_code=status.HTTP_409_CONFLICT, code="sales_claim_conflict", message=str(exc)) from exc
    except sales_claims_app.SalesClaimRepositoryError as exc:
        sales_claims_app._repository_error(str(exc))
    sales_claims_app._invalidate_sales_claim_view_caches(organization_id=actor.organization_id)
    return SalesClaimMutationResponse(changed=changed, claim=sales_claims_app._to_sales_claim_model(claim))


@router.patch(
    "/api/sales-claims/projects/{project_id}",
    response_model=SalesClaimMutationResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def patch_sales_claim(
    request: Request,
    project_id: UUID,
    payload: SalesClaimPatchRequest,
) -> SalesClaimMutationResponse:
    sales_claims_app = _app_module()
    actor = sales_claims_app._resolve_sales_actor(request)
    repository = sales_claims_app._get_sales_claim_repository()
    try:
        claim = repository.update_sales_note(
            actor=actor,
            project_id=project_id,
            sales_note=payload.sales_note,
            force_admin_override=bool(payload.force_admin_override),
        )
    except sales_claims_app.SalesClaimNotFoundError as exc:
        raise sales_claims_app.ApiError(status_code=status.HTTP_404_NOT_FOUND, code="sales_claim_not_found", message=str(exc)) from exc
    except sales_claims_app.SalesClaimPermissionError as exc:
        raise sales_claims_app.ApiError(status_code=status.HTTP_403_FORBIDDEN, code="sales_claim_forbidden", message=str(exc)) from exc
    except sales_claims_app.SalesClaimInvalidTransitionError as exc:
        raise sales_claims_app.ApiError(status_code=status.HTTP_409_CONFLICT, code="sales_claim_invalid_transition", message=str(exc)) from exc
    except sales_claims_app.SalesClaimRepositoryError as exc:
        sales_claims_app._repository_error(str(exc))
    sales_claims_app._invalidate_sales_claim_view_caches(organization_id=actor.organization_id)
    return SalesClaimMutationResponse(changed=True, claim=sales_claims_app._to_sales_claim_model(claim))


@router.post(
    "/api/sales-claims/projects/{project_id}/transfer",
    response_model=SalesClaimMutationResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def transfer_sales_claim(
    request: Request,
    project_id: UUID,
    payload: SalesClaimTransferRequest,
) -> SalesClaimMutationResponse:
    sales_claims_app = _app_module()
    actor = sales_claims_app._resolve_sales_actor(request)
    auth_context = getattr(request.state, "auth_context", None)
    repository = sales_claims_app._get_sales_claim_repository()
    target_user = sales_claims_app._resolve_transfer_target_user(
        actor,
        target_user_id=payload.target_user_id,
        target_email=payload.target_email,
    )
    try:
        claim = repository.transfer_project(
            actor=actor,
            project_id=project_id,
            target_user_id=UUID(str(target_user.get("id"))),
            target_email=str(target_user.get("email") or ""),
            target_display_name=str(target_user.get("display_name") or target_user.get("email") or ""),
            force=bool(payload.force),
        )
    except sales_claims_app.SalesClaimNotFoundError as exc:
        raise sales_claims_app.ApiError(status_code=status.HTTP_404_NOT_FOUND, code="sales_claim_not_found", message=str(exc)) from exc
    except sales_claims_app.SalesClaimPermissionError as exc:
        raise sales_claims_app.ApiError(status_code=status.HTTP_403_FORBIDDEN, code="sales_claim_forbidden", message=str(exc)) from exc
    except sales_claims_app.SalesClaimInvalidTransitionError as exc:
        raise sales_claims_app.ApiError(status_code=status.HTTP_409_CONFLICT, code="sales_claim_invalid_transition", message=str(exc)) from exc
    except sales_claims_app.SalesClaimRepositoryError as exc:
        sales_claims_app._repository_error(str(exc))
    try:
        sales_claims_app.append_audit_log(
            organization_id=str(actor.organization_id),
            actor_user_id=str(actor.user_id or ""),
            actor_membership_id=str(getattr(auth_context, "membership_id", "") or ""),
            event_type="project_transferred",
            target_type="project",
            target_id=str(project_id),
            payload={
                "project_name": str(getattr(claim, "project_name", "") or ""),
                "target_user_id": str(target_user.get("id") or ""),
                "target_email": str(target_user.get("email") or ""),
            },
        )
    except sales_claims_app.AuthRuntimeError:
        pass
    sales_claims_app._invalidate_sales_claim_view_caches(organization_id=actor.organization_id)
    return SalesClaimMutationResponse(changed=True, claim=sales_claims_app._to_sales_claim_model(claim))


@router.post(
    "/api/sales-claims/projects/{project_id}/close",
    response_model=SalesClaimMutationResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def close_sales_claim(
    request: Request,
    project_id: UUID,
    payload: SalesClaimCloseRequest,
) -> SalesClaimMutationResponse:
    sales_claims_app = _app_module()
    normalized_outcome = str(payload.outcome or "").strip().lower()
    if normalized_outcome == "won" and not str(payload.contract_amount_text or "").strip():
        sales_claims_app._validation_error("contract_amount_text is required when outcome is won")
    actor = sales_claims_app._resolve_sales_actor(request)
    repository = sales_claims_app._get_sales_claim_repository()
    try:
        claim = repository.close_project(
            actor=actor,
            project_id=project_id,
            outcome=payload.outcome,
            contract_amount_text=str(payload.contract_amount_text or "").strip(),
            force=bool(payload.force),
        )
    except sales_claims_app.SalesClaimNotFoundError as exc:
        raise sales_claims_app.ApiError(status_code=status.HTTP_404_NOT_FOUND, code="sales_claim_not_found", message=str(exc)) from exc
    except sales_claims_app.SalesClaimPermissionError as exc:
        raise sales_claims_app.ApiError(status_code=status.HTTP_403_FORBIDDEN, code="sales_claim_forbidden", message=str(exc)) from exc
    except sales_claims_app.SalesClaimInvalidTransitionError as exc:
        raise sales_claims_app.ApiError(status_code=status.HTTP_409_CONFLICT, code="sales_claim_invalid_transition", message=str(exc)) from exc
    except sales_claims_app.SalesClaimRepositoryError as exc:
        sales_claims_app._repository_error(str(exc))
    sales_claims_app._invalidate_sales_claim_view_caches(organization_id=actor.organization_id)
    return SalesClaimMutationResponse(changed=True, claim=sales_claims_app._to_sales_claim_model(claim))


@router.post(
    "/api/sales-claims/projects/{project_id}/release",
    response_model=SalesClaimMutationResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def release_sales_claim(
    request: Request,
    project_id: UUID,
    payload: SalesClaimReleaseRequest,
) -> SalesClaimMutationResponse:
    sales_claims_app = _app_module()
    actor = sales_claims_app._resolve_sales_actor(request)
    repository = sales_claims_app._get_sales_claim_repository()
    try:
        claim = repository.release_project(
            actor=actor,
            project_id=project_id,
            force=bool(payload.force),
        )
    except sales_claims_app.SalesClaimNotFoundError as exc:
        raise sales_claims_app.ApiError(status_code=status.HTTP_404_NOT_FOUND, code="sales_claim_not_found", message=str(exc)) from exc
    except sales_claims_app.SalesClaimPermissionError as exc:
        raise sales_claims_app.ApiError(status_code=status.HTTP_403_FORBIDDEN, code="sales_claim_forbidden", message=str(exc)) from exc
    except sales_claims_app.SalesClaimInvalidTransitionError as exc:
        raise sales_claims_app.ApiError(status_code=status.HTTP_409_CONFLICT, code="sales_claim_invalid_transition", message=str(exc)) from exc
    except sales_claims_app.SalesClaimRepositoryError as exc:
        sales_claims_app._repository_error(str(exc))
    sales_claims_app._invalidate_sales_claim_view_caches(organization_id=actor.organization_id)
    return SalesClaimMutationResponse(changed=True, claim=sales_claims_app._to_sales_claim_model(claim))


@router.get(
    "/api/sales-claims/summary-by-user",
    response_model=SalesClaimSummaryByUserResponse,
)
def get_sales_claim_summary_by_user(request: Request) -> SalesClaimSummaryByUserResponse:
    sales_claims_app = _app_module()
    actor = sales_claims_app._resolve_sales_actor(request)
    cached = sales_claims_app._read_sales_claim_summary_by_user_cache(organization_id=actor.organization_id)
    if cached is not None:
        return cached
    repository = sales_claims_app._get_sales_claim_repository()
    try:
        items = repository.summarize_by_user(organization_id=actor.organization_id)
    except sales_claims_app.SalesClaimRepositoryError as exc:
        sales_claims_app._repository_error(str(exc))
    response_payload = SalesClaimSummaryByUserResponse(
        items=[sales_claims_app._to_sales_claim_summary_user_model(item) for item in items]
    )
    return sales_claims_app._write_sales_claim_summary_by_user_cache(
        organization_id=actor.organization_id,
        payload=response_payload,
    )
