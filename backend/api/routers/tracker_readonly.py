from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from fastapi import status

from backend.api.routers import app_support
from backend.api.routers import tracker_export_handlers
from backend.api.routers import tracker_read_handlers
from backend.api.schemas import ErrorResponse
from backend.api.schemas import MessageResponse
from backend.api.schemas import TrackerDownloadJobCreateRequest
from backend.api.schemas import TrackerDownloadJobItem
from backend.api.schemas import TrackerEntryAuditLogListResponse
from backend.api.schemas import TrackerEntryItem
from backend.api.schemas import TrackerEntryListResponse
from backend.api.schemas import TrackerEntrySummaryListResponse
from backend.api.schemas import TrackerMissingReportResponse

router = APIRouter()


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
    return tracker_export_handlers.list_tracker_entry_summaries(
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
    return tracker_export_handlers.download_tracker_entry_summaries(
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
    return tracker_export_handlers.create_tracker_entry_summary_download_job(payload)


@router.get(
    "/api/tracker-entry-summaries/download-jobs/{job_id}",
    response_model=TrackerDownloadJobItem,
    responses={404: {"model": ErrorResponse}},
)
def get_tracker_entry_summary_download_job(job_id: UUID) -> TrackerDownloadJobItem:
    return tracker_export_handlers.get_tracker_entry_summary_download_job(job_id)


@router.get(
    "/api/tracker-entry-summaries/download-jobs/{job_id}/file",
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def download_tracker_entry_summary_download_job_file(request: Request, job_id: UUID):
    return tracker_export_handlers.download_tracker_entry_summary_download_job_file(request=request, job_id=job_id)


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
    return tracker_export_handlers.warm_tracker_entry_summaries_download(
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
    return tracker_export_handlers.list_tracker_entries(
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


@router.get(
    "/api/tracker-entries/missing-report",
    response_model=TrackerMissingReportResponse,
    responses={400: {"model": ErrorResponse}},
)
def get_tracker_entries_missing_report(
    limit: int = Query(default=40, ge=1, le=200),
) -> TrackerMissingReportResponse:
    return app_support.get_tracker_entries_missing_report(limit=limit)


@router.get("/api/tracker-entries/missing-report/download")
def download_tracker_entries_missing_report(
    format: str = Query(default="csv"),
    limit: int = Query(default=500, ge=1, le=500),
):
    return app_support.download_tracker_entries_missing_report(format=format, limit=limit)


@router.get(
    "/api/tracker-entries/{entry_id}",
    response_model=TrackerEntryItem,
    responses={404: {"model": ErrorResponse}},
)
def get_tracker_entry(request: Request, entry_id: UUID) -> TrackerEntryItem:
    return tracker_read_handlers.get_tracker_entry(request=request, entry_id=entry_id)


@router.get(
    "/api/tracker-entries/{entry_id}/notice-file-view",
    responses={404: {"model": ErrorResponse}},
)
def view_tracker_entry_notice_file(
    entry_id: UUID,
    embed: bool = Query(default=False),
    desktop: bool = Query(default=False),
):
    return tracker_read_handlers.view_tracker_entry_notice_file(entry_id, embed=embed, desktop=desktop)


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
    return tracker_read_handlers.list_tracker_entry_audit_logs(entry_id=entry_id, cursor=cursor, limit=limit)
