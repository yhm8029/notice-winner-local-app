from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from fastapi import status

from backend.api.schemas import ErrorResponse
from backend.api.schemas import TrackerCleanupApplyRequest
from backend.api.schemas import TrackerCleanupApplyResponse
from backend.api.schemas import TrackerCleanupPreviewResponse
from backend.api.schemas import TrackerContactResolutionSummaryResponse
from backend.api.support.runtime_common import ApiError

router = APIRouter(prefix="/api")


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
            message="Only admins can read tracker cleanup previews.",
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
            message="Only admins can apply tracker cleanup.",
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
            message="Only admins can read tracker contact resolution summaries.",
        )
    return app_module._build_tracker_contact_resolution_summary(
        limit=limit,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
    )
