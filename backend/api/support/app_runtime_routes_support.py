from __future__ import annotations

from uuid import UUID

from fastapi import Query
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse

from backend.api.schemas import RunLogListResponse
from backend.repositories.artifacts import ArtifactRepositoryError
from backend.repositories.runs import RunRepositoryError


def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


def frontend_root() -> RedirectResponse:
    return RedirectResponse(url="/app/", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


def frontend_app_root() -> RedirectResponse:
    return RedirectResponse(url="/app/", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


def list_run_logs(
    run_id: UUID,
    cursor: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
) -> RunLogListResponse:
    from backend.api.routers.runs_read import list_run_logs as list_run_logs_route

    return list_run_logs_route(run_id=run_id, cursor=cursor, limit=limit)


def stream_run_events(
    run_id: UUID,
    poll_interval_ms: int = Query(default=1000, ge=250, le=10000),
):
    from backend.api.routers.runs_read import stream_run_events as stream_run_events_route

    return stream_run_events_route(run_id=run_id, poll_interval_ms=poll_interval_ms)


def download_artifact(artifact_id: UUID):
    from backend.api import app as app_module

    artifact_repository = app_module._get_artifact_repository()
    try:
        artifact = artifact_repository.get_artifact(artifact_id)
    except ArtifactRepositoryError as exc:
        app_module._repository_error(str(exc))
    if artifact is None:
        app_module._not_found(f"artifact not found: {artifact_id}")

    run_repository = app_module._get_run_repository()
    try:
        run_row = run_repository.get_run(UUID(str(artifact["run_id"])))
    except RunRepositoryError as exc:
        app_module._repository_error(str(exc))
    if run_row is None or not app_module._run_visible_in_operational_views(run_row):
        app_module._not_found(f"artifact not found: {artifact_id}")

    file_path = app_module.resolve_artifact_path(str(artifact["storage_path"]))
    if not file_path.exists():
        app_module._not_found(f"artifact file not found: {artifact_id}")

    from fastapi.responses import FileResponse

    return FileResponse(
        path=file_path,
        media_type=str(artifact["mime_type"]),
        filename=str(artifact["file_name"]),
    )


def preview_artifact(
    artifact_id: UUID,
    limit: int = Query(default=6, ge=1, le=20),
) -> JSONResponse:
    from backend.api import app as app_module

    artifact_repository = app_module._get_artifact_repository()
    try:
        artifact = artifact_repository.get_artifact(artifact_id)
    except ArtifactRepositoryError as exc:
        app_module._repository_error(str(exc))
    if artifact is None:
        app_module._not_found(f"artifact not found: {artifact_id}")

    run_repository = app_module._get_run_repository()
    try:
        run_row = run_repository.get_run(UUID(str(artifact["run_id"])))
    except RunRepositoryError as exc:
        app_module._repository_error(str(exc))
    if run_row is None or not app_module._run_visible_in_operational_views(run_row):
        app_module._not_found(f"artifact not found: {artifact_id}")

    try:
        payload = app_module._build_artifact_preview_payload(
            artifact_row=artifact,
            limit=limit,
        )
    except FileNotFoundError:
        app_module._not_found(f"artifact file not found: {artifact_id}")
    return JSONResponse(content=payload)
