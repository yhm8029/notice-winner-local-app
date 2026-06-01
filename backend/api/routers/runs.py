from __future__ import annotations

from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from fastapi import status
from fastapi.responses import StreamingResponse

from backend.api.schemas import ArtifactListResponse
from backend.api.schemas import ErrorResponse
from backend.api.schemas import RunCancelResponse
from backend.api.schemas import RunCreateRequest
from backend.api.schemas import RunCreateResponse
from backend.api.schemas import RunDetailResponse
from backend.api.schemas import RunListResponse
from backend.api.schemas import RunLogListResponse
from backend.api.schemas import RunPresetCreateRequest
from backend.api.schemas import RunPresetItem
from backend.api.schemas import RunPresetListResponse
from backend.phase1_defaults import build_phase1_run_row

router = APIRouter()


def _app_module():
    from backend.api import app as runs_app

    return runs_app


@router.post(
    "/api/runs",
    status_code=status.HTTP_201_CREATED,
    response_model=RunCreateResponse,
    responses={400: {"model": ErrorResponse}},
)
def create_run(payload: RunCreateRequest) -> RunCreateResponse:
    runs_app = _app_module()
    runs_app._validate_run_create_request(payload)

    run_repository = runs_app._get_run_repository()
    run_row = build_phase1_run_row(
        run_type=payload.run_type,
        params=runs_app._dump_request_params(payload),
        parent_run_id=None,
        progress_stage="",
    )
    try:
        stored = run_repository.create_run(run_row)
    except runs_app.RunRepositoryError as exc:
        runs_app._repository_error(str(exc))

    _unused_queue_tracker_export_run_for_parent, _safely_execute_project_tracker = runs_app._load_run_execution_helpers()
    runs_app._dispatch_background(_safely_execute_project_tracker, UUID(str(stored["id"])))
    return runs_app._to_run_create_response(stored)


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
    runs_app = _app_module()
    runs_app._validate_run_list_filters(
        status_value=status_value.strip(),
        run_type=run_type.strip(),
        date_from=date_from.strip(),
        date_to=date_to.strip(),
    )

    try:
        rows, total = runs_app._get_run_repository().list_runs(
            page=page,
            page_size=page_size,
            status=status_value.strip(),
            run_type=run_type.strip(),
            parent_run_id=parent_run_id,
            date_from=date_from.strip(),
            date_to=date_to.strip(),
        )
    except runs_app.RunRepositoryError as exc:
        runs_app._repository_error(str(exc))
    items = runs_app._filter_visible_runs(rows)

    return RunListResponse(
        items=[runs_app._to_run_list_item(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/api/runs/{run_id}",
    response_model=RunDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_run(run_id: UUID) -> RunDetailResponse:
    runs_app = _app_module()
    run_repository = runs_app._get_run_repository()
    try:
        row = run_repository.get_run(run_id)
    except runs_app.RunRepositoryError as exc:
        runs_app._repository_error(str(exc))

    if row is None or not runs_app._run_visible_in_operational_views(row):
        runs_app._not_found(f"run not found: {run_id}")

    return runs_app._to_run_detail(row)


@router.get(
    "/api/runs/{run_id}/artifacts",
    response_model=ArtifactListResponse,
    responses={404: {"model": ErrorResponse}},
)
def list_run_artifacts(run_id: UUID, request: Request) -> ArtifactListResponse:
    runs_app = _app_module()
    run_repository = runs_app._get_run_repository()
    artifact_repository = runs_app._get_artifact_repository()
    try:
        run_row = run_repository.get_run(run_id)
    except runs_app.RunRepositoryError as exc:
        runs_app._repository_error(str(exc))

    if run_row is None or not runs_app._run_visible_in_operational_views(run_row):
        runs_app._not_found(f"run not found: {run_id}")

    try:
        items = artifact_repository.list_artifacts(run_id=run_id)
    except runs_app.ArtifactRepositoryError as exc:
        runs_app._repository_error(str(exc))

    return ArtifactListResponse(items=[runs_app._to_artifact_item(request, item) for item in items])


@router.post(
    "/api/runs/{run_id}/cancel",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=RunCancelResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def cancel_run(run_id: UUID) -> RunCancelResponse:
    runs_app = _app_module()
    run_repository = runs_app._get_run_repository()
    log_repository = runs_app._get_run_log_repository()

    try:
        row = run_repository.get_run(run_id)
    except runs_app.RunRepositoryError as exc:
        runs_app._repository_error(str(exc))

    if row is None or not runs_app._run_visible_in_operational_views(row):
        runs_app._not_found(f"run not found: {run_id}")

    if str(row["status"]) in {"success", "failed", "cancelled"}:
        runs_app._conflict_error("cancel is only allowed for queued or running runs")

    if not bool(row.get("cancel_requested")):
        try:
            row = run_repository.update_run(run_id, {"cancel_requested": True})
        except runs_app.RunRepositoryError as exc:
            runs_app._repository_error(str(exc))
        if row is None:
            runs_app._not_found(f"run not found: {run_id}")

        try:
            log_repository.create_log(
                {
                    "run_id": str(run_id),
                    "organization_id": row["organization_id"],
                    "level": "warning",
                    "stage": str(row.get("progress_stage") or ""),
                    "message": "cancel requested",
                    "meta_json": {"status": row["status"]},
                }
            )
        except runs_app.RunLogRepositoryError as exc:
            runs_app._repository_error(str(exc))

    return RunCancelResponse(
        id=UUID(str(row["id"])),
        status=str(row["status"]),
        cancel_requested=bool(row["cancel_requested"]),
    )


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
    runs_app = _app_module()
    run_repository = runs_app._get_run_repository()
    log_repository = runs_app._get_run_log_repository()

    try:
        run_row = run_repository.get_run(run_id)
    except runs_app.RunRepositoryError as exc:
        runs_app._repository_error(str(exc))

    if run_row is None or not runs_app._run_visible_in_operational_views(run_row):
        runs_app._not_found(f"run not found: {run_id}")

    try:
        items, next_cursor = log_repository.list_logs(
            run_id=run_id,
            cursor=cursor,
            limit=limit,
        )
    except runs_app.RunLogRepositoryError as exc:
        runs_app._repository_error(str(exc))

    return RunLogListResponse(
        items=[runs_app._to_run_log_item(item) for item in items],
        next_cursor=next_cursor,
    )


@router.get(
    "/api/runs/{run_id}/events",
    responses={404: {"model": ErrorResponse}},
)
def stream_run_events(
    run_id: UUID,
    poll_interval_ms: int = Query(default=1000, ge=250, le=10000),
):
    runs_app = _app_module()
    run_repository = runs_app._get_run_repository()
    try:
        run_row = run_repository.get_run(run_id)
    except runs_app.RunRepositoryError as exc:
        runs_app._repository_error(str(exc))
    if run_row is None or not runs_app._run_visible_in_operational_views(run_row):
        runs_app._not_found(f"run not found: {run_id}")
    return StreamingResponse(
        runs_app._stream_run_events(run_id=run_id, poll_interval_ms=poll_interval_ms),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/api/run-presets",
    response_model=RunPresetListResponse,
)
def list_run_presets(
    limit: int = Query(default=20, ge=1, le=50),
) -> RunPresetListResponse:
    runs_app = _app_module()
    return RunPresetListResponse(items=[runs_app.to_run_preset_item(item) for item in runs_app.list_stored_run_presets(limit=limit)])


@router.post(
    "/api/run-presets",
    status_code=status.HTTP_201_CREATED,
    response_model=RunPresetItem,
    responses={400: {"model": ErrorResponse}},
)
def create_run_preset(payload: RunPresetCreateRequest) -> RunPresetItem:
    runs_app = _app_module()
    name = payload.name.strip()
    if not name:
        runs_app._validation_error("name is required")
    now = runs_app._utc_now()
    stored = runs_app.store_run_preset(
        {
            "id": uuid4(),
            "name": name,
            "params": dict(payload.params or {}),
            "created_at": now,
            "updated_at": now,
        }
    )
    return runs_app.to_run_preset_item(stored)
