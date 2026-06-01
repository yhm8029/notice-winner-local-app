from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request

from backend.api.support import app_compat_support
from backend.api.routers import tracker_read_handlers
from backend.api.schemas import ErrorResponse
from backend.api.schemas import TrackerChangeEventListResponse
from backend.api.schemas import TrackerChangeEventMarkReadRequest
from backend.api.schemas import TrackerChangeEventMarkReadResponse
from backend.api.schemas import TrackerChangeEventUnreadCountResponse
from backend.api.schemas import TrackerEntryPatchRequest
from backend.api.schemas import TrackerEntryPatchResponse

router = APIRouter()


@router.patch(
    "/api/tracker-entries/{entry_id}",
    response_model=TrackerEntryPatchResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def patch_tracker_entry(
    request: Request,
    entry_id: UUID,
    payload: TrackerEntryPatchRequest,
) -> TrackerEntryPatchResponse:
    return app_compat_support.patch_tracker_entry(request=request, entry_id=entry_id, payload=payload)


@router.get(
    "/api/tracker-change-events/unread-count",
    response_model=TrackerChangeEventUnreadCountResponse,
    responses={503: {"model": ErrorResponse}},
)
def get_tracker_change_event_unread_count(request: Request) -> TrackerChangeEventUnreadCountResponse:
    return tracker_read_handlers.get_tracker_change_event_unread_count(request)


@router.get(
    "/api/tracker-change-events",
    response_model=TrackerChangeEventListResponse,
    responses={503: {"model": ErrorResponse}},
)
def list_tracker_change_events(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    tracker_entry_id: UUID | None = None,
    include_silent: bool = False,
) -> TrackerChangeEventListResponse:
    return tracker_read_handlers.list_tracker_change_events(
        request=request,
        limit=limit,
        tracker_entry_id=tracker_entry_id,
        include_silent=include_silent,
    )


@router.post(
    "/api/tracker-change-events/mark-read",
    response_model=TrackerChangeEventMarkReadResponse,
    responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def mark_tracker_change_events_read(
    request: Request,
    payload: TrackerChangeEventMarkReadRequest,
) -> TrackerChangeEventMarkReadResponse:
    return tracker_read_handlers.mark_tracker_change_events_read(request=request, payload=payload)
