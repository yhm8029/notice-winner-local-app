from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import status

from backend.api.routers.runs import cancel_run as runs_cancel_run
from backend.api.routers.runs import create_run as runs_create_run
from backend.api.routers.tracker import create_tracker_export_run as tracker_create_tracker_export_run
from backend.api.schemas import ErrorResponse
from backend.api.schemas import RunCancelResponse
from backend.api.schemas import RunCreateRequest
from backend.api.schemas import RunCreateResponse

router = APIRouter()


@router.post(
    "/api/runs",
    status_code=status.HTTP_201_CREATED,
    response_model=RunCreateResponse,
    responses={400: {"model": ErrorResponse}},
)
def create_run(payload: RunCreateRequest) -> RunCreateResponse:
    return runs_create_run(payload)


@router.post(
    "/api/runs/{run_id}/cancel",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=RunCancelResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def cancel_run(run_id: UUID) -> RunCancelResponse:
    return runs_cancel_run(run_id)


@router.post(
    "/api/runs/{run_id}/tracker-export",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=RunCreateResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def create_tracker_export_run(run_id: UUID) -> RunCreateResponse:
    return tracker_create_tracker_export_run(run_id)
