from __future__ import annotations

import threading
import time

from fastapi import APIRouter
from fastapi import File
from fastapi import Query
from fastapi import UploadFile
from fastapi import status

from backend.api.routers.core import get_dashboard_summary as core_get_dashboard_summary
from backend.api.routers.runs import create_run_preset as runs_create_run_preset
from backend.api.routers.runs import list_run_presets as runs_list_run_presets
from backend.api.schemas import DashboardSummaryResponse
from backend.api.schemas import ErrorResponse
from backend.api.schemas import RunPresetCreateRequest
from backend.api.schemas import RunPresetItem
from backend.api.schemas import RunPresetListResponse
from backend.api.schemas import TrackerTemplateStatusResponse

router = APIRouter()
_TRACKER_TEMPLATE_STATUS_CACHE_LOCK = threading.Lock()
_TRACKER_TEMPLATE_STATUS_CACHE: tuple[float, dict[str, object]] | None = None
_TRACKER_TEMPLATE_STATUS_CACHE_TTL_SEC = 15.0


def _app_module():
    from backend.api import app as catalog_app

    return catalog_app


def _clear_tracker_template_status_cache() -> None:
    global _TRACKER_TEMPLATE_STATUS_CACHE
    with _TRACKER_TEMPLATE_STATUS_CACHE_LOCK:
        _TRACKER_TEMPLATE_STATUS_CACHE = None


def _get_cached_tracker_template_status() -> TrackerTemplateStatusResponse:
    global _TRACKER_TEMPLATE_STATUS_CACHE

    now = time.monotonic()
    with _TRACKER_TEMPLATE_STATUS_CACHE_LOCK:
        cached_entry = _TRACKER_TEMPLATE_STATUS_CACHE
        if cached_entry is not None:
            expires_at, payload = cached_entry
            if expires_at > now:
                return TrackerTemplateStatusResponse(**dict(payload))
            _TRACKER_TEMPLATE_STATUS_CACHE = None

    artifact_file_helpers = _app_module()._load_artifact_file_helpers()
    payload = dict(artifact_file_helpers["describe_active_tracker_template"]())
    with _TRACKER_TEMPLATE_STATUS_CACHE_LOCK:
        _TRACKER_TEMPLATE_STATUS_CACHE = (
            time.monotonic() + _TRACKER_TEMPLATE_STATUS_CACHE_TTL_SEC,
            dict(payload),
        )
    return TrackerTemplateStatusResponse(**payload)


@router.get(
    "/api/dashboard/summary",
    response_model=DashboardSummaryResponse,
)
def get_dashboard_summary() -> DashboardSummaryResponse:
    return core_get_dashboard_summary()


@router.get(
    "/api/run-presets",
    response_model=RunPresetListResponse,
)
def list_run_presets(
    limit: int = Query(default=20, ge=1, le=50),
) -> RunPresetListResponse:
    return runs_list_run_presets(limit=limit)


@router.post(
    "/api/run-presets",
    status_code=status.HTTP_201_CREATED,
    response_model=RunPresetItem,
    responses={400: {"model": ErrorResponse}},
)
def create_run_preset(payload: RunPresetCreateRequest) -> RunPresetItem:
    return runs_create_run_preset(payload)


@router.get(
    "/api/tracker-template",
    response_model=TrackerTemplateStatusResponse,
    responses={400: {"model": ErrorResponse}},
)
def get_tracker_template_status() -> TrackerTemplateStatusResponse:
    try:
        return _get_cached_tracker_template_status()
    except FileNotFoundError as exc:
        _app_module()._validation_error(str(exc))


@router.post(
    "/api/tracker-template",
    response_model=TrackerTemplateStatusResponse,
    responses={400: {"model": ErrorResponse}},
)
async def upload_tracker_template(
    file: UploadFile = File(...),
) -> TrackerTemplateStatusResponse:
    file_name = str(file.filename or "").strip()
    if not file_name:
        _app_module()._validation_error("template file name is required")
    if not file_name.lower().endswith(".xlsx"):
        _app_module()._validation_error("template file must be .xlsx")

    payload = await file.read()
    try:
        artifact_file_helpers = _app_module()._load_artifact_file_helpers()
        status_payload = artifact_file_helpers["save_uploaded_tracker_template"](
            payload=payload,
            original_file_name=file_name,
        )
    except ValueError as exc:
        _app_module()._validation_error(str(exc))
    _clear_tracker_template_status_cache()
    return TrackerTemplateStatusResponse(**status_payload)


@router.delete(
    "/api/tracker-template",
    response_model=TrackerTemplateStatusResponse,
    responses={400: {"model": ErrorResponse}},
)
def delete_tracker_template_override() -> TrackerTemplateStatusResponse:
    try:
        artifact_file_helpers = _app_module()._load_artifact_file_helpers()
        status_payload = artifact_file_helpers["clear_uploaded_tracker_template"]()
    except FileNotFoundError as exc:
        _app_module()._validation_error(str(exc))
    _clear_tracker_template_status_cache()
    return TrackerTemplateStatusResponse(**status_payload)
