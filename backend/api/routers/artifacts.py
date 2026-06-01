from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Query
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse

from backend.api.schemas import ErrorResponse

router = APIRouter()


def _app_module():
    from backend.api import app as artifacts_app

    return artifacts_app


@router.get(
    "/api/artifacts/{artifact_id}/download",
    name="download_artifact",
    responses={404: {"model": ErrorResponse}},
)
def download_artifact(artifact_id: UUID):
    artifacts_app = _app_module()
    artifact = artifacts_app._get_visible_artifact(artifact_id)

    file_path = artifacts_app.resolve_artifact_path(str(artifact["storage_path"]))
    if not file_path.exists():
        artifacts_app._not_found(f"artifact file not found: {artifact_id}")

    return FileResponse(
        path=file_path,
        media_type=str(artifact["mime_type"]),
        filename=str(artifact["file_name"]),
    )


@router.get(
    "/api/artifacts/{artifact_id}/preview",
    responses={404: {"model": ErrorResponse}},
)
def preview_artifact(
    artifact_id: UUID,
    limit: int = Query(default=6, ge=1, le=20),
) -> JSONResponse:
    artifacts_app = _app_module()
    artifact = artifacts_app._get_visible_artifact(artifact_id)

    try:
        payload = artifacts_app._build_artifact_preview_payload(
            artifact_row=artifact,
            limit=limit,
        )
    except FileNotFoundError:
        artifacts_app._not_found(f"artifact file not found: {artifact_id}")
    return JSONResponse(content=payload)
