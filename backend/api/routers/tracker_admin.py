from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from fastapi import status

from backend.api.schemas import BackfillConflictItem
from backend.api.schemas import BackfillConflictListResponse
from backend.api.schemas import BackfillConflictResolveRequest
from backend.api.schemas import ErrorResponse
from backend.api.schemas import TrackerCleanupApplyRequest
from backend.api.schemas import TrackerCleanupApplyResponse
from backend.api.schemas import TrackerCleanupPreviewResponse
from backend.api.schemas import TrackerContactResolutionSummaryResponse
from backend.api.support.runtime_common import ApiError
from backend.repositories import BackfillConflictRepositoryError
from backend.repositories import TrackerEntryRepositoryError

router = APIRouter(prefix="/api")


@router.get(
    "/backfill-conflicts",
    response_model=BackfillConflictListResponse,
    responses={503: {"model": ErrorResponse}},
)
def list_backfill_conflicts(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    tracker_entry_id: UUID | None = None,
    include_resolved: bool = False,
) -> BackfillConflictListResponse:
    from backend.api import app as app_module

    actor = app_module._resolve_sales_actor(request)
    if not actor.is_admin:
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 backfill conflict 목록을 조회할 수 있습니다.",
        )
    conflict_repository = app_module.get_backfill_conflict_repository()
    tracker_repository = app_module._get_tracker_repository()
    try:
        rows = conflict_repository.list_conflicts(
            organization_id=app_module._resolve_request_organization_id(request),
            limit=limit,
            tracker_entry_id=tracker_entry_id,
            include_resolved=include_resolved,
        )
    except BackfillConflictRepositoryError as exc:
        app_module._repository_error(str(exc))
    items: list[BackfillConflictItem] = []
    for row in rows:
        try:
            tracker_entry = tracker_repository.get_entry(UUID(str(row["tracker_entry_id"])))
        except TrackerEntryRepositoryError as exc:
            app_module._repository_error(str(exc))
        items.append(app_module._to_backfill_conflict_model(row, tracker_entry=tracker_entry))
    return BackfillConflictListResponse(items=items, total=len(items))


@router.post(
    "/backfill-conflicts/{conflict_id}/resolve",
    response_model=BackfillConflictItem,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def resolve_backfill_conflict(
    request: Request,
    conflict_id: UUID,
    payload: BackfillConflictResolveRequest,
) -> BackfillConflictItem:
    from backend.api import app as app_module

    actor = app_module._resolve_sales_actor(request)
    if not actor.is_admin:
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 backfill conflict를 처리할 수 있습니다.",
        )
    resolution = str(payload.resolution or "").strip()
    if resolution not in app_module.BACKFILL_CONFLICT_RESOLUTIONS:
        app_module._validation_error("resolution is not supported")
    conflict_repository = app_module.get_backfill_conflict_repository()
    tracker_repository = app_module._get_tracker_repository()
    try:
        row = conflict_repository.resolve_conflict(
            organization_id=app_module._resolve_request_organization_id(request),
            conflict_id=conflict_id,
            resolution=resolution,
        )
    except BackfillConflictRepositoryError as exc:
        app_module._repository_error(str(exc))
    if row is None:
        app_module._not_found(f"backfill conflict not found: {conflict_id}")
    try:
        tracker_entry = tracker_repository.get_entry(UUID(str(row["tracker_entry_id"])))
    except TrackerEntryRepositoryError as exc:
        app_module._repository_error(str(exc))
    return app_module._to_backfill_conflict_model(row, tracker_entry=tracker_entry)


@router.get(
    "/admin/tracker-cleanup/preview",
    response_model=TrackerCleanupPreviewResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def get_tracker_cleanup_preview(
    request: Request,
    source_tracker_run_id: UUID,
) -> TrackerCleanupPreviewResponse:
    from backend.api import app as app_module

    actor = app_module._resolve_sales_actor(request)
    if not actor.is_admin:
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 tracker cleanup preview를 조회할 수 있습니다.",
        )
    return app_module._preview_tracker_cleanup(source_tracker_run_id=source_tracker_run_id)


@router.post(
    "/admin/tracker-cleanup/apply",
    response_model=TrackerCleanupApplyResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def post_tracker_cleanup_apply(
    request: Request,
    payload: TrackerCleanupApplyRequest,
) -> TrackerCleanupApplyResponse:
    from backend.api import app as app_module

    actor = app_module._resolve_sales_actor(request)
    if not actor.is_admin:
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 tracker cleanup을 실행할 수 있습니다.",
        )
    return app_module._apply_tracker_cleanup(source_tracker_run_id=payload.source_tracker_run_id)


@router.get(
    "/admin/tracker-contact-resolution-summary",
    response_model=TrackerContactResolutionSummaryResponse,
    responses={403: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def get_tracker_contact_resolution_summary(
    request: Request,
    limit: int = Query(12, ge=1, le=200),
    source_run_id: UUID | None = None,
    source_tracker_run_id: UUID | None = None,
) -> TrackerContactResolutionSummaryResponse:
    from backend.api import app as app_module

    actor = app_module._resolve_sales_actor(request)
    if not actor.is_admin:
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 연락처 재추출 요약을 조회할 수 있습니다.",
        )
    return app_module._build_tracker_contact_resolution_summary(
        limit=limit,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
    )
