from __future__ import annotations

import csv
from datetime import datetime
from io import BytesIO
from uuid import UUID

from fastapi import APIRouter
from fastapi import File
from fastapi import Query
from fastapi import Request
from fastapi import UploadFile
from fastapi import status
from fastapi.responses import StreamingResponse

from backend.api.routers import app_support
from backend.api.support import app_compat_support
from backend.api.schemas import ErrorResponse
from backend.api.schemas import HomeBootstrapResponse
from backend.api.schemas import MessageResponse
from backend.api.schemas import RunCreateResponse
from backend.api.schemas import TrackerChangeEventListResponse
from backend.api.schemas import TrackerChangeEventMarkReadRequest
from backend.api.schemas import TrackerChangeEventMarkReadResponse
from backend.api.schemas import TrackerChangeEventUnreadCountResponse
from backend.api.schemas import TrackerDownloadJobCreateRequest
from backend.api.schemas import TrackerDownloadJobItem
from backend.api.schemas import TrackerEntryAuditLogListResponse
from backend.api.schemas import TrackerEntryItem
from backend.api.schemas import TrackerEntryListResponse
from backend.api.schemas import TrackerEntryPatchRequest
from backend.api.schemas import TrackerEntryPatchResponse
from backend.api.schemas import TrackerEntrySummaryListResponse
from backend.api.schemas import TrackerMissingReportResponse
from backend.api.schemas import TrackerTemplateStatusResponse

router = APIRouter()


def _app_module():
    from backend.api import app as tracker_app

    return tracker_app


@router.post(
    "/api/runs/{run_id}/tracker-export",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=RunCreateResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def create_tracker_export_run(run_id: UUID) -> RunCreateResponse:
    return app_compat_support.create_tracker_export_run(run_id)


@router.get(
    "/api/home-bootstrap",
    response_model=HomeBootstrapResponse,
)
def get_home_bootstrap(request: Request) -> HomeBootstrapResponse:
    tracker_app = _app_module()
    return tracker_app.get_home_bootstrap(request)


@router.get(
    "/api/tracker-entry-summaries",
    response_model=TrackerEntrySummaryListResponse,
    responses={400: {"model": ErrorResponse}},
)
def list_tracker_entry_summaries(
    request: Request,
    q: str = "",
    region: str = "",
    notice_year: str = "",
    exclude_auxiliary_titles: bool = False,
    edited_only: bool = False,
    source_run_id: UUID | None = None,
    source_tracker_run_id: UUID | None = None,
    sheet_name: str = "",
    section_name: str = "",
    refresh: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> TrackerEntrySummaryListResponse:
    tracker_app = _app_module()
    return tracker_app.list_tracker_entry_summaries(
        request=request,
        q=q,
        region=region,
        notice_year=notice_year,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        edited_only=edited_only,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        refresh=refresh,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/api/tracker-entries",
    response_model=TrackerEntryListResponse,
    responses={400: {"model": ErrorResponse}},
)
def list_tracker_entries(
    request: Request,
    q: str = "",
    region: str = "",
    notice_year: str = "",
    exclude_auxiliary_titles: bool = False,
    edited_only: bool = False,
    source_run_id: UUID | None = None,
    source_tracker_run_id: UUID | None = None,
    sheet_name: str = "",
    section_name: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> TrackerEntryListResponse:
    tracker_app = _app_module()
    return tracker_app.list_tracker_entries(
        request=request,
        q=q,
        region=region,
        notice_year=notice_year,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        edited_only=edited_only,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        page=page,
        page_size=page_size,
    )


@router.get("/api/tracker-entry-summaries/download")
def download_tracker_entry_summaries(
    request: Request,
    format: str = Query(default="xlsx"),
    q: str = "",
    region: str = "",
    notice_year: str = "",
    exclude_auxiliary_titles: bool = False,
    edited_only: bool = False,
    blank_progress_note: bool = False,
    source_run_id: UUID | None = None,
    source_tracker_run_id: UUID | None = None,
    sheet_name: str = "",
    section_name: str = "",
):
    tracker_app = _app_module()
    return tracker_app.download_tracker_entry_summaries(
        request=request,
        format=format,
        q=q,
        region=region,
        notice_year=notice_year,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        edited_only=edited_only,
        blank_progress_note=blank_progress_note,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
    )


@router.post(
    "/api/tracker-entry-summaries/download-jobs",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TrackerDownloadJobItem,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def create_tracker_entry_summary_download_job(payload: TrackerDownloadJobCreateRequest) -> TrackerDownloadJobItem:
    tracker_app = _app_module()
    return tracker_app.create_tracker_entry_summary_download_job(payload)


@router.get(
    "/api/tracker-entry-summaries/download-jobs/{job_id}",
    response_model=TrackerDownloadJobItem,
    responses={404: {"model": ErrorResponse}},
)
def get_tracker_entry_summary_download_job(job_id: UUID) -> TrackerDownloadJobItem:
    tracker_app = _app_module()
    return tracker_app.get_tracker_entry_summary_download_job(job_id)


@router.get(
    "/api/tracker-entry-summaries/download-jobs/{job_id}/file",
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def download_tracker_entry_summary_download_job_file(request: Request, job_id: UUID):
    tracker_app = _app_module()
    return tracker_app.download_tracker_entry_summary_download_job_file(request=request, job_id=job_id)


@router.post(
    "/api/tracker-entry-summaries/download/warm",
    response_model=MessageResponse,
)
def warm_tracker_entry_summaries_download(
    format: str = Query(default="xlsx"),
    q: str = "",
    region: str = "",
    notice_year: str = "",
    exclude_auxiliary_titles: bool = False,
    edited_only: bool = False,
    blank_progress_note: bool = False,
    source_run_id: UUID | None = None,
    source_tracker_run_id: UUID | None = None,
    sheet_name: str = "",
    section_name: str = "",
) -> MessageResponse:
    tracker_app = _app_module()
    return tracker_app.warm_tracker_entry_summaries_download(
        format=format,
        q=q,
        region=region,
        notice_year=notice_year,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        edited_only=edited_only,
        blank_progress_note=blank_progress_note,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
    )


@router.get(
    "/api/tracker-template",
    response_model=TrackerTemplateStatusResponse,
    responses={400: {"model": ErrorResponse}},
)
def get_tracker_template_status() -> TrackerTemplateStatusResponse:
    tracker_app = _app_module()
    return tracker_app.get_tracker_template_status()


@router.post(
    "/api/tracker-template",
    response_model=TrackerTemplateStatusResponse,
    responses={400: {"model": ErrorResponse}},
)
async def upload_tracker_template(
    file: UploadFile = File(...),
) -> TrackerTemplateStatusResponse:
    tracker_app = _app_module()
    return await tracker_app.upload_tracker_template(file)


@router.delete(
    "/api/tracker-template",
    response_model=TrackerTemplateStatusResponse,
    responses={400: {"model": ErrorResponse}},
)
def delete_tracker_template_override() -> TrackerTemplateStatusResponse:
    tracker_app = _app_module()
    return tracker_app.delete_tracker_template_override()


@router.get(
    "/api/tracker-entries/missing-report",
    response_model=TrackerMissingReportResponse,
    responses={400: {"model": ErrorResponse}},
)
def get_tracker_entries_missing_report(
    limit: int = Query(default=40, ge=1, le=200),
) -> TrackerMissingReportResponse:
    summary, items = app_support._build_tracker_missing_report(limit=limit)
    return TrackerMissingReportResponse(summary=summary, items=items)


@router.get("/api/tracker-entries/missing-report/download")
def download_tracker_entries_missing_report(
    format: str = Query(default="csv"),
    limit: int = Query(default=500, ge=1, le=500),
):
    normalized_format = str(format or "csv").strip().lower()
    if normalized_format not in {"csv", "xlsx"}:
        app_support._bad_request("format must be csv or xlsx")

    summary, items = app_support._build_tracker_missing_report(limit=limit)
    rows = app_support._flatten_tracker_missing_report_rows(summary=summary, items=items)
    fieldnames = [
        "generated_at",
        "project_name",
        "bid_no",
        "bid_ord",
        "demand_org_name",
        "missing_field_key",
        "missing_field_label",
        "source_reason",
        "reason_group",
        "reason_explainer",
        "source_run_id",
        "source_tracker_run_id",
        "updated_at",
        "summary_total_entries",
        "summary_missing_entries",
        "summary_contact_missing",
        "summary_architect_missing",
        "summary_area_missing",
    ]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if normalized_format == "csv":
        from io import StringIO

        csv_io = StringIO()
        writer = csv.DictWriter(csv_io, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        payload = BytesIO(csv_io.getvalue().encode("utf-8-sig"))
        headers = {"Content-Disposition": f'attachment; filename="tracker_missing_report_{timestamp}.csv"'}
        return StreamingResponse(payload, media_type="text/csv; charset=utf-8", headers=headers)

    artifact_file_helpers = app_support._load_artifact_file_helpers()
    workbook = app_support._load_openpyxl_workbook_class()()
    summary_sheet = workbook.active
    summary_sheet.title = "summary"
    summary_rows = [
        ["generated_at", datetime.now().isoformat(timespec="seconds")],
        ["total_entries", summary.total_entries],
        ["missing_entries", summary.missing_entries],
        ["contact_missing", summary.contact_missing],
        ["architect_missing", summary.architect_missing],
        ["area_missing", summary.area_missing],
    ]
    for row_index, row_values in enumerate(summary_rows, start=2):
        for column_index, value in enumerate(row_values, start=1):
            summary_sheet.cell(row_index, column_index).value = value

    detail_sheet = workbook.create_sheet(title="missing_items")
    for column_index, field in enumerate(fieldnames, start=1):
        detail_sheet.cell(2, column_index).value = field
    for row_index, row in enumerate(rows, start=3):
        for column_index, field in enumerate(fieldnames, start=1):
            detail_sheet.cell(row_index, column_index).value = row.get(field, "")

    artifact_file_helpers["apply_standard_download_workbook_formatting"](workbook)
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    headers = {"Content-Disposition": f'attachment; filename="tracker_missing_report_{timestamp}.xlsx"'}
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


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
    tracker_app = _app_module()
    return tracker_app.get_tracker_change_event_unread_count(request)


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
    tracker_app = _app_module()
    return tracker_app.list_tracker_change_events(
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
    tracker_app = _app_module()
    return tracker_app.mark_tracker_change_events_read(request=request, payload=payload)


@router.get(
    "/api/tracker-entries/{entry_id}",
    response_model=TrackerEntryItem,
    responses={404: {"model": ErrorResponse}},
)
def get_tracker_entry(request: Request, entry_id: UUID) -> TrackerEntryItem:
    tracker_app = _app_module()
    return tracker_app.get_tracker_entry(request=request, entry_id=entry_id)


@router.get(
    "/api/tracker-entries/{entry_id}/notice-file-view",
    responses={404: {"model": ErrorResponse}},
)
def view_tracker_entry_notice_file(
    entry_id: UUID,
    embed: bool = Query(default=False),
    desktop: bool = Query(default=False),
):
    tracker_app = _app_module()
    return tracker_app.view_tracker_entry_notice_file(entry_id, embed=embed, desktop=desktop)


@router.post(
    "/api/tracker-entries/{entry_id}/notice-file-open-external",
    responses={404: {"model": ErrorResponse}},
)
def open_tracker_entry_notice_file_external(request: Request, entry_id: UUID):
    tracker_app = _app_module()
    return tracker_app.open_tracker_entry_notice_file_external(entry_id, base_url=str(request.base_url))


@router.post(
    "/api/tracker-entries/{entry_id}/notice-file-warm",
    responses={404: {"model": ErrorResponse}},
)
def warm_tracker_entry_notice_file(entry_id: UUID):
    tracker_app = _app_module()
    return tracker_app.warm_tracker_entry_notice_file(entry_id)


@router.get(
    "/api/tracker-entries/{entry_id}/audit-logs",
    response_model=TrackerEntryAuditLogListResponse,
    responses={404: {"model": ErrorResponse}},
)
def list_tracker_entry_audit_logs(
    entry_id: UUID,
    cursor: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
) -> TrackerEntryAuditLogListResponse:
    tracker_app = _app_module()
    return tracker_app.list_tracker_entry_audit_logs(entry_id=entry_id, cursor=cursor, limit=limit)
