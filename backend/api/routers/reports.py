from __future__ import annotations

from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter
from fastapi import Query
from fastapi import status
from fastapi.responses import JSONResponse

from backend.api.schemas import ErrorResponse
from backend.api.schemas import ReportJobCreateRequest
from backend.api.schemas import ReportJobItem
from backend.api.schemas import ReportJobListResponse

router = APIRouter()


def _app_module():
    from backend.api import app as reports_app

    return reports_app


@router.get(
    "/api/reports/{report_name}",
    responses={404: {"model": ErrorResponse}},
)
def get_report(report_name: str) -> JSONResponse:
    reports_app = _app_module()
    payload = reports_app._load_report_payload(report_name)
    return JSONResponse(content=payload)


@router.post(
    "/api/report-jobs",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ReportJobItem,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def create_report_job(payload: ReportJobCreateRequest) -> ReportJobItem:
    reports_app = _app_module()
    command, output_path, _gui_root, seed_csv = reports_app._build_report_job_command(payload)
    job_id = uuid4()
    stored = reports_app.store_report_job(
        {
            "id": job_id,
            "report_name": payload.report_name,
            "status": "queued",
            "output_path": str(output_path),
            "command": command,
            "seed_limit": payload.seed_limit,
            "seed_csv": seed_csv,
            "created_at": reports_app._utc_now(),
            "started_at": None,
            "finished_at": None,
            "exit_code": None,
            "summary": {},
            "log_excerpt": "",
            "error": "",
        }
    )
    reports_app._dispatch_background(reports_app._run_report_job, job_id)
    return reports_app.to_report_job_item(stored)


@router.get(
    "/api/report-jobs",
    response_model=ReportJobListResponse,
)
def list_report_jobs(
    report_name: str = "",
    limit: int = Query(default=10, ge=1, le=20),
) -> ReportJobListResponse:
    reports_app = _app_module()
    return ReportJobListResponse(
        items=[reports_app.to_report_job_item(item) for item in reports_app.list_stored_report_jobs(report_name=report_name, limit=limit)]
    )


@router.get(
    "/api/report-jobs/{job_id}",
    response_model=ReportJobItem,
    responses={404: {"model": ErrorResponse}},
)
def get_report_job(job_id: UUID) -> ReportJobItem:
    reports_app = _app_module()
    row = reports_app.get_stored_report_job(job_id)
    if row is None:
        reports_app._not_found(f"report job not found: {job_id}")
    return reports_app.to_report_job_item(row)
