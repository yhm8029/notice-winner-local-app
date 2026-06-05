from __future__ import annotations

import csv
import logging
import time
from datetime import datetime
from io import BytesIO
from io import StringIO
from pathlib import Path
from uuid import UUID
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import Query
from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse

from backend.api.routers import tracker_export_support as support
from backend.api.schemas import MessageResponse
from backend.api.schemas import TrackerDownloadJobCreateRequest
from backend.api.schemas import TrackerDownloadJobItem
from backend.api.schemas import TrackerEntryListResponse
from backend.api.schemas import TrackerEntrySummaryListResponse
from backend.repositories.tracker_entries import normalize_tracker_notice_year
from backend.repositories.tracker_entries import tracker_entry_matches_notice_year

PROJECT_STATUS_FILE_TIMEZONE = ZoneInfo("Asia/Seoul")


def _project_status_file_timestamp(*, include_microseconds: bool = False) -> str:
    fmt = "%Y%m%d_%H%M%S_%f" if include_microseconds else "%Y%m%d_%H%M%S"
    return datetime.now(PROJECT_STATUS_FILE_TIMEZONE).strftime(fmt)


def _filter_rows_by_notice_year(rows: list[dict[str, object]], notice_year: str) -> list[dict[str, object]]:
    normalized_notice_year = normalize_tracker_notice_year(notice_year)
    if not normalized_notice_year:
        return rows
    return [row for row in rows if tracker_entry_matches_notice_year(row, normalized_notice_year)]


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
    request_organization_id = support._resolve_request_organization_id(request)
    if support._is_global_tracker_scope(
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
    ):
        all_rows = [
            row
            for row in support._load_global_tracker_rows(force_refresh=refresh)
            if support._tracker_row_belongs_to_request_organization(
                row,
                organization_id=request_organization_id,
            )
        ]
        filtered = support._filter_tracker_rows_for_global_scope(
            all_rows,
            q=q,
            region=region,
            exclude_auxiliary_titles=exclude_auxiliary_titles,
            edited_only=edited_only,
        )
        filtered = _filter_rows_by_notice_year(filtered, notice_year)
        total = len(filtered)
        start = (page - 1) * page_size
        items = filtered[start:start + page_size]
    else:
        tracker_repository = support._get_tracker_repository()
        try:
            items, total = tracker_repository.list_entry_summaries(
                page=page,
                page_size=page_size,
                q=q,
                region=region,
                notice_year=notice_year,
                exclude_auxiliary_titles=exclude_auxiliary_titles,
                edited_only=edited_only,
                source_run_id=source_run_id,
                source_tracker_run_id=source_tracker_run_id,
                sheet_name=sheet_name,
                section_name=section_name,
            )
        except support.TrackerEntryRepositoryError as exc:
            support._repository_error(str(exc))

        items = [
            item
            for item in items
            if support._tracker_row_belongs_to_request_organization(
                item,
                organization_id=request_organization_id,
            )
        ]
        total = len(items)
        items = support._hydrate_tracker_entry_summary_rows(
            organization_id=request_organization_id,
            rows=items,
        )
    return TrackerEntrySummaryListResponse(
        items=[support._to_tracker_entry_summary_model(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


def _list_tracker_entries_for_export(
    *,
    q: str,
    region: str,
    exclude_auxiliary_titles: bool,
    edited_only: bool,
    source_run_id: UUID | None,
    source_tracker_run_id: UUID | None,
    sheet_name: str,
    section_name: str,
    notice_year: str = "",
) -> list[dict[str, object]]:
    rows = support._list_tracker_entries_for_export(
        q=q,
        region=region,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        edited_only=edited_only,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
    )
    return _filter_rows_by_notice_year(rows, notice_year)


def _get_or_build_cached_tracker_export_workbook_bytes(
    *,
    q: str,
    region: str,
    exclude_auxiliary_titles: bool,
    edited_only: bool,
    blank_progress_note: bool,
    source_run_id: UUID | None,
    source_tracker_run_id: UUID | None,
    sheet_name: str,
    section_name: str,
) -> bytes:
    artifact_file_helpers = support._load_artifact_file_helpers()
    return support._get_or_build_cached_tracker_export_workbook_bytes_impl(
        q=q,
        region=region,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        edited_only=edited_only,
        blank_progress_note=blank_progress_note,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        cache_lock=support._TRACKER_EXPORT_WORKBOOK_CACHE_LOCK,
        cache=support._TRACKER_EXPORT_WORKBOOK_CACHE,
        cache_build_events=support._TRACKER_EXPORT_WORKBOOK_CACHE_BUILD_EVENTS,
        cache_serial_fn=lambda: support._TRACKER_EXPORT_WORKBOOK_CACHE_SERIAL,
        cache_ttl_sec=support.TRACKER_EXPORT_WORKBOOK_CACHE_TTL_SEC,
        cache_wait_timeout_sec=support.TRACKER_EXPORT_WORKBOOK_CACHE_WAIT_TIMEOUT_SEC,
        cache_max_entries=support.TRACKER_EXPORT_WORKBOOK_CACHE_MAX_ENTRIES,
        list_tracker_entries_for_export_fn=support._list_tracker_entries_for_export,
        build_tracking_download_workbook_bytes_fn=support.build_tracking_download_workbook_bytes,
        build_tracker_export_workbook_cache_key_fn=support._build_tracker_export_workbook_cache_key,
        monotonic_fn=time.monotonic,
    )


def _warm_tracker_export_workbook_for_request(
    *,
    q: str,
    region: str,
    edited_only: bool,
    exclude_auxiliary_titles: bool,
    blank_progress_note: bool,
    source_run_id: UUID | None,
    source_tracker_run_id: UUID | None,
    sheet_name: str,
    section_name: str,
    notice_year: str = "",
) -> None:
    if normalize_tracker_notice_year(notice_year):
        return
    if not support._can_cache_tracker_export_workbook(
        format="xlsx",
        q=q,
        region=region,
        edited_only=edited_only,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
    ):
        return
    try:
        support._get_or_build_cached_tracker_export_workbook_bytes(
            q=q,
            region=region,
            exclude_auxiliary_titles=exclude_auxiliary_titles,
            edited_only=edited_only,
            blank_progress_note=blank_progress_note,
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        )
    except Exception:
        logging.getLogger("perf.download").exception("tracker export workbook filter warm failed")


def _run_tracker_download_job(job_id: UUID) -> None:
    row = support.get_stored_tracker_download_job(job_id)
    if row is None:
        return
    support.update_tracker_download_job(
        job_id,
        {"status": "running", "started_at": support._utc_now(), "error": "", "reused_existing": False},
    )
    try:
        q = str(row.get("q") or "")
        region = str(row.get("region") or "")
        notice_year = str(row.get("notice_year") or "")
        exclude_auxiliary_titles = bool(row.get("exclude_auxiliary_titles"))
        edited_only = bool(row.get("edited_only"))
        blank_progress_note = bool(row.get("blank_progress_note"))
        source_run_id = UUID(str(row["source_run_id"])) if str(row.get("source_run_id") or "").strip() else None
        source_tracker_run_id = (
            UUID(str(row["source_tracker_run_id"])) if str(row.get("source_tracker_run_id") or "").strip() else None
        )
        sheet_name = str(row.get("sheet_name") or "")
        section_name = str(row.get("section_name") or "")

        if not normalize_tracker_notice_year(notice_year) and support._can_cache_tracker_export_workbook(
            format="xlsx",
            q=q,
            region=region,
            edited_only=edited_only,
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        ):
            workbook_bytes = support._get_or_build_cached_tracker_export_workbook_bytes(
                q=q,
                region=region,
                exclude_auxiliary_titles=exclude_auxiliary_titles,
                edited_only=edited_only,
                blank_progress_note=blank_progress_note,
                source_run_id=source_run_id,
                source_tracker_run_id=source_tracker_run_id,
                sheet_name=sheet_name,
                section_name=section_name,
            )
            row_count = 0
        else:
            rows = _list_tracker_entries_for_export(
                q=q,
                region=region,
                notice_year=notice_year,
                exclude_auxiliary_titles=exclude_auxiliary_titles,
                edited_only=edited_only,
                source_run_id=source_run_id,
                source_tracker_run_id=source_tracker_run_id,
                sheet_name=sheet_name,
                section_name=section_name,
            )
            if blank_progress_note:
                rows = [{**item, "progress_note": ""} for item in rows]
            row_count = len(rows)
            workbook_bytes = support.build_tracking_download_workbook_bytes(rows=rows)

        output_path = Path(str(row["output_path"]))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(workbook_bytes)
        support.update_tracker_download_job(
            job_id,
            {
                "status": "success",
                "finished_at": support._utc_now(),
                "summary": {"row_count": row_count},
            },
        )
    except Exception as exc:
        support.update_tracker_download_job(
            job_id,
            {
                "status": "failed",
                "finished_at": support._utc_now(),
                "error": str(exc),
            },
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
    request_organization_id = support._resolve_request_organization_id(request)
    tracker_repository = support._get_tracker_repository()
    try:
        items, total = tracker_repository.list_entries(
            page=page,
            page_size=page_size,
            q=q,
            region=region,
            notice_year=notice_year,
            exclude_auxiliary_titles=exclude_auxiliary_titles,
            edited_only=edited_only,
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        )
    except support.TrackerEntryRepositoryError as exc:
        support._repository_error(str(exc))

    items = [
        item
        for item in items
        if support._tracker_row_belongs_to_request_organization(
            item,
            organization_id=request_organization_id,
        )
    ]
    total = len(items)
    items = support._annotate_tracker_entries_with_project_refs(items)
    items = support._annotate_tracker_entries_with_opening_dates(items)
    items = support._normalize_tracker_rows_for_presentation(items)

    return TrackerEntryListResponse(
        items=[support._to_tracker_entry_model(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


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
    normalized_format = str(format or "xlsx").strip().lower()
    if normalized_format not in {"csv", "xlsx"}:
        support._bad_request("format must be csv or xlsx")

    actor = support._resolve_sales_actor(request)
    timestamp = _project_status_file_timestamp()

    if normalized_format == "csv":
        rows = _list_tracker_entries_for_export(
            q=q,
            region=region,
            notice_year=notice_year,
            exclude_auxiliary_titles=exclude_auxiliary_titles,
            edited_only=edited_only,
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        )
        if blank_progress_note:
            rows = [{**row, "progress_note": ""} for row in rows]
        artifact_file_helpers = support._load_artifact_file_helpers()
        csv_io = StringIO()
        writer = csv.DictWriter(csv_io, fieldnames=artifact_file_helpers["tracking_export_fieldnames"])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    field: str(row.get(field, ""))
                    for field in artifact_file_helpers["tracking_export_fieldnames"]
                }
            )
        payload = BytesIO(csv_io.getvalue().encode("utf-8-sig"))
        file_name = f"project_status_{timestamp}.csv"
        support._record_download_audit_log(
            actor=actor,
            download_scope="global",
            download_format="csv",
            source_page="tracker_entries",
            file_name=file_name,
        )
        headers = {"Content-Disposition": f'attachment; filename="{file_name}"'}
        return StreamingResponse(payload, media_type="text/csv; charset=utf-8", headers=headers)

    if not normalize_tracker_notice_year(notice_year) and support._can_cache_tracker_export_workbook(
        format=normalized_format,
        q=q,
        region=region,
        edited_only=edited_only,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
    ):
        workbook_bytes = support._get_or_build_cached_tracker_export_workbook_bytes(
            q=q,
            region=region,
            exclude_auxiliary_titles=exclude_auxiliary_titles,
            edited_only=edited_only,
            blank_progress_note=blank_progress_note,
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        )
    else:
        rows = _list_tracker_entries_for_export(
            q=q,
            region=region,
            notice_year=notice_year,
            exclude_auxiliary_titles=exclude_auxiliary_titles,
            edited_only=edited_only,
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        )
        if blank_progress_note:
            rows = [{**row, "progress_note": ""} for row in rows]
        workbook_bytes = support.build_tracking_download_workbook_bytes(rows=rows)
    payload = BytesIO(workbook_bytes)
    file_name = f"project_status_{timestamp}.xlsx"
    support._record_download_audit_log(
        actor=actor,
        download_scope="global",
        download_format="xlsx",
        source_page="tracker_entries",
        file_name=file_name,
    )
    headers = {"Content-Disposition": f'attachment; filename="{file_name}"'}
    return StreamingResponse(
        payload,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


def create_tracker_entry_summary_download_job(
    payload: TrackerDownloadJobCreateRequest,
) -> TrackerDownloadJobItem:
    normalized_format = str(payload.format or "xlsx").strip().lower()
    if normalized_format != "xlsx":
        support._bad_request("download job format must be xlsx")
    data_version = _get_tracker_entries_data_version()
    cache_key = support._build_tracker_download_job_cache_key(
        q=payload.q,
        region=payload.region,
        notice_year=payload.notice_year,
        exclude_auxiliary_titles=payload.exclude_auxiliary_titles,
        edited_only=payload.edited_only,
        blank_progress_note=payload.blank_progress_note,
        source_run_id=payload.source_run_id,
        source_tracker_run_id=payload.source_tracker_run_id,
        sheet_name=payload.sheet_name,
        section_name=payload.section_name,
        data_version=data_version,
    )
    existing = support.find_reusable_tracker_download_job(cache_key)
    if existing is not None:
        existing["reused_existing"] = True
        support.update_tracker_download_job(UUID(str(existing["id"])), {"reused_existing": True})
        return support.to_tracker_download_job_item(existing)

    job_id = uuid4()
    stored = support.store_tracker_download_job(
        {
            "id": job_id,
            "status": "queued",
            "format": "xlsx",
            "cache_key": cache_key,
            "q": payload.q,
            "region": payload.region,
            "notice_year": payload.notice_year,
            "exclude_auxiliary_titles": payload.exclude_auxiliary_titles,
            "edited_only": payload.edited_only,
            "blank_progress_note": payload.blank_progress_note,
            "source_run_id": payload.source_run_id,
            "source_tracker_run_id": payload.source_tracker_run_id,
            "sheet_name": payload.sheet_name,
            "section_name": payload.section_name,
            "output_path": str(support._tracker_download_job_output_path(job_id)),
            "file_name": f"project_status_{_project_status_file_timestamp()}.xlsx",
            "created_at": support._utc_now(),
            "started_at": None,
            "finished_at": None,
            "error": "",
            "reused_existing": False,
            "summary": {},
        }
    )
    support._dispatch_background(support._run_tracker_download_job, job_id)
    return support.to_tracker_download_job_item(stored)


def _get_tracker_entries_data_version() -> str:
    try:
        return str(support._get_tracker_repository().get_entries_data_version() or "")
    except Exception:
        logging.getLogger("perf.download").exception("tracker download data version lookup failed")
        return f"lookup_failed={_project_status_file_timestamp(include_microseconds=True)}"


def get_tracker_entry_summary_download_job(job_id: UUID) -> TrackerDownloadJobItem:
    row = support.get_stored_tracker_download_job(job_id)
    if row is None:
        support._not_found(f"tracker download job not found: {job_id}")
    return support.to_tracker_download_job_item(row)


def download_tracker_entry_summary_download_job_file(request: Request, job_id: UUID):
    row = support.get_stored_tracker_download_job(job_id)
    if row is None:
        support._not_found(f"tracker download job not found: {job_id}")
    if str(row.get("status") or "") != "success":
        support._conflict_error("tracker download job is not ready")
    output_path = Path(str(row.get("output_path") or ""))
    if not output_path.exists():
        support._not_found(f"tracker download file not found: {job_id}")
    actor = support._resolve_sales_actor(request)
    file_name = f"project_status_{_project_status_file_timestamp()}.xlsx"
    support._record_download_audit_log(
        actor=actor,
        download_scope="global",
        download_format="xlsx",
        source_page="tracker_entries",
        file_name=file_name,
    )
    return FileResponse(
        path=output_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=file_name,
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
    normalized_format = str(format or "xlsx").strip().lower()
    if normalized_format != "xlsx":
        return MessageResponse(message="xlsx만 사전 준비합니다.")
    if normalize_tracker_notice_year(notice_year) or not support._can_cache_tracker_export_workbook(
        format=normalized_format,
        q=q,
        region=region,
        edited_only=edited_only,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
    ):
        return MessageResponse(message="현재 조건은 즉시 캐시 대상이 아닙니다.")
    support._dispatch_background(
        _warm_tracker_export_workbook_for_request,
        q=q,
        region=region,
        edited_only=edited_only,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        blank_progress_note=blank_progress_note,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        notice_year=notice_year,
    )
    return MessageResponse(message="엑셀 다운로드를 백그라운드에서 준비하고 있습니다.")
