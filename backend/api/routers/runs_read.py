from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request

from backend.api.routers.runs import get_run as runs_get_run
from backend.api.routers.runs import list_run_artifacts as runs_list_run_artifacts
from backend.api.routers.runs import list_run_logs as runs_list_run_logs
from backend.api.routers.runs import list_runs as runs_list_runs
from backend.api.routers.runs import stream_run_events as runs_stream_run_events
from backend.api.schemas import ArtifactListResponse
from backend.api.schemas import ErrorResponse
from backend.api.schemas import RunDetailResponse
from backend.api.schemas import RunListResponse
from backend.api.schemas import RunLogListResponse

router = APIRouter()


@router.get(
    "/api/runs",
    response_model=RunListResponse,
    responses={400: {"model": ErrorResponse}},
)
def list_runs(
    status_value: str = Query(default="", alias="status"),
    run_type: str = "",
    parent_run_id: UUID | None = None,
    date_from: str = Query(default="", alias="from"),
    date_to: str = Query(default="", alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> RunListResponse:
    return runs_list_runs(
        status_value=status_value,
        run_type=run_type,
        parent_run_id=parent_run_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/api/runs/{run_id}",
    response_model=RunDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_run(run_id: UUID) -> RunDetailResponse:
    return runs_get_run(run_id)


@router.get(
    "/api/runs/{run_id}/artifacts",
    response_model=ArtifactListResponse,
    responses={404: {"model": ErrorResponse}},
)
def list_run_artifacts(run_id: UUID, request: Request) -> ArtifactListResponse:
    return runs_list_run_artifacts(run_id=run_id, request=request)


@router.get(
    "/api/runs/{run_id}/logs",
    response_model=RunLogListResponse,
    responses={404: {"model": ErrorResponse}},
)
def list_run_logs(
    run_id: UUID,
    cursor: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
) -> RunLogListResponse:
    return runs_list_run_logs(run_id=run_id, cursor=cursor, limit=limit)


@router.get(
    "/api/runs/{run_id}/events",
    responses={404: {"model": ErrorResponse}},
)
def stream_run_events(
    run_id: UUID,
    poll_interval_ms: int = Query(default=1000, ge=250, le=10000),
):
    return runs_stream_run_events(run_id=run_id, poll_interval_ms=poll_interval_ms)
