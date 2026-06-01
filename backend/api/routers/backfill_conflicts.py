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

router = APIRouter()


def _app_module():
    from backend.api import app as backfill_conflicts_app

    return backfill_conflicts_app


@router.get(
    "/api/backfill-conflicts",
    response_model=BackfillConflictListResponse,
    responses={503: {"model": ErrorResponse}},
)
def list_backfill_conflicts(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    tracker_entry_id: UUID | None = None,
    include_resolved: bool = False,
) -> BackfillConflictListResponse:
    backfill_conflicts_app = _app_module()
    actor = backfill_conflicts_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise backfill_conflicts_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 백필 충돌 목록을 조회할 수 있습니다.",
        )
    conflict_repository = backfill_conflicts_app.get_backfill_conflict_repository()
    tracker_repository = backfill_conflicts_app._get_tracker_repository()
    try:
        rows = conflict_repository.list_conflicts(
            organization_id=backfill_conflicts_app._resolve_request_organization_id(request),
            limit=limit,
            tracker_entry_id=tracker_entry_id,
            include_resolved=include_resolved,
        )
    except backfill_conflicts_app.BackfillConflictRepositoryError as exc:
        backfill_conflicts_app._repository_error(str(exc))
    items: list[BackfillConflictItem] = []
    for row in rows:
        try:
            tracker_entry = tracker_repository.get_entry(UUID(str(row["tracker_entry_id"])))
        except backfill_conflicts_app.TrackerEntryRepositoryError as exc:
            backfill_conflicts_app._repository_error(str(exc))
        items.append(backfill_conflicts_app._to_backfill_conflict_model(row, tracker_entry=tracker_entry))
    return BackfillConflictListResponse(items=items, total=len(items))


@router.post(
    "/api/backfill-conflicts/{conflict_id}/resolve",
    response_model=BackfillConflictItem,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def resolve_backfill_conflict(
    request: Request,
    conflict_id: UUID,
    payload: BackfillConflictResolveRequest,
) -> BackfillConflictItem:
    backfill_conflicts_app = _app_module()
    actor = backfill_conflicts_app._resolve_sales_actor(request)
    if not actor.is_admin:
        raise backfill_conflicts_app.ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="관리자만 백필 충돌을 처리할 수 있습니다.",
        )
    resolution = str(payload.resolution or "").strip()
    if resolution not in backfill_conflicts_app.BACKFILL_CONFLICT_RESOLUTIONS:
        backfill_conflicts_app._validation_error("resolution is not supported")
    conflict_repository = backfill_conflicts_app.get_backfill_conflict_repository()
    tracker_repository = backfill_conflicts_app._get_tracker_repository()
    try:
        row = conflict_repository.resolve_conflict(
            organization_id=backfill_conflicts_app._resolve_request_organization_id(request),
            conflict_id=conflict_id,
            resolution=resolution,
        )
    except backfill_conflicts_app.BackfillConflictRepositoryError as exc:
        backfill_conflicts_app._repository_error(str(exc))
    if row is None:
        backfill_conflicts_app._not_found(f"backfill conflict not found: {conflict_id}")
    try:
        tracker_entry = tracker_repository.get_entry(UUID(str(row["tracker_entry_id"])))
    except backfill_conflicts_app.TrackerEntryRepositoryError as exc:
        backfill_conflicts_app._repository_error(str(exc))
    return backfill_conflicts_app._to_backfill_conflict_model(row, tracker_entry=tracker_entry)
