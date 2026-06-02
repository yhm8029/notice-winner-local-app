from __future__ import annotations

from typing import Any
from urllib.parse import quote
from uuid import UUID

from fastapi import status
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response

from backend.api.routers import tracker_read_support as support


def get_tracker_change_event_unread_count(request) -> Any:
    try:
        repository = support._get_tracker_change_event_repository()
    except support.ApiError as exc:
        if exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            return support.TrackerChangeEventUnreadCountResponse(unread_count=0)
        raise
    try:
        unread_count = repository.count_unread(
            organization_id=support._resolve_request_organization_id(request),
        )
    except support.TrackerChangeEventRepositoryError as exc:
        if support._is_missing_tracker_change_events_table_error(str(exc)):
            return support.TrackerChangeEventUnreadCountResponse(unread_count=0)
        support._repository_error(str(exc))
    return support.TrackerChangeEventUnreadCountResponse(unread_count=int(unread_count or 0))


def list_tracker_change_events(
    request,
    *,
    limit: int,
    tracker_entry_id: UUID | None,
    include_silent: bool,
) -> Any:
    organization_id = support._resolve_request_organization_id(request)
    try:
        event_repository = support._get_tracker_change_event_repository()
    except support.ApiError as exc:
        if exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            return support.TrackerChangeEventListResponse(items=[], total=0)
        raise
    try:
        rows = event_repository.list_events(
            organization_id=organization_id,
            limit=limit,
            tracker_entry_id=tracker_entry_id,
            include_silent=include_silent,
        )
    except support.TrackerChangeEventRepositoryError as exc:
        if support._is_missing_tracker_change_events_table_error(str(exc)):
            return support.TrackerChangeEventListResponse(items=[], total=0)
        support._repository_error(str(exc))
    snapshot_map = support._load_tracker_entry_snapshot_map(
        organization_id=organization_id,
        rows=[{"id": row.get("tracker_entry_id")} for row in rows],
    )
    tracker_repository = support._get_tracker_repository()
    items: list[Any] = []
    for row in rows:
        entry_id = support._coerce_uuid_or_none(row.get("tracker_entry_id"))
        tracker_entry: dict[str, Any] | None = None
        if entry_id is not None:
            snapshot = snapshot_map.get(str(entry_id)) or {}
            snapshot_entry = dict((snapshot.get("detail_json") or snapshot.get("summary_json") or {})) or None
            try:
                live_entry = tracker_repository.get_entry(entry_id)
            except support.TrackerEntryRepositoryError as exc:
                support._repository_error(str(exc))
            if snapshot_entry is not None and (
                live_entry is None or support._is_tracker_entry_snapshot_fresh(snapshot, live_entry)
            ):
                tracker_entry = snapshot_entry
            else:
                tracker_entry = live_entry
        items.append(support._to_tracker_change_event_model(row, tracker_entry=tracker_entry))
    return support.TrackerChangeEventListResponse(items=items, total=len(items))


def mark_tracker_change_events_read(request, *, payload) -> Any:
    if not payload.event_ids and payload.tracker_entry_id is None:
        support._validation_error("event_ids or tracker_entry_id is required")
    repository = support._get_tracker_change_event_repository()
    try:
        updated_count = repository.mark_read(
            organization_id=support._resolve_request_organization_id(request),
            event_ids=payload.event_ids or None,
            tracker_entry_id=payload.tracker_entry_id,
        )
    except support.TrackerChangeEventRepositoryError as exc:
        support._repository_error(str(exc))
    return support.TrackerChangeEventMarkReadResponse(updated_count=updated_count)


def get_tracker_entry(request, *, entry_id: UUID) -> Any:
    request_id = support.ensure_request_id(request)
    tracker_repository = support._get_tracker_repository()
    organization_id = support._resolve_request_organization_id(request)
    try:
        with support.measure_stage("tracker_entry_detail.load_entry", request_id=request_id, entry_id=str(entry_id)):
            entry = tracker_repository.get_entry(entry_id)
    except support.TrackerEntryRepositoryError as exc:
        support._repository_error(str(exc))

    if entry is None:
        support._not_found(f"tracker_entry not found: {entry_id}")
    if not support._tracker_row_belongs_to_request_organization(entry, organization_id=organization_id):
        support._not_found(f"tracker_entry not found: {entry_id}")

    with support.measure_stage("tracker_entry_detail.snapshot_hydrate", request_id=request_id, entry_id=str(entry_id)):
        detail_row = support._hydrate_tracker_entry_detail_row(
            organization_id=organization_id,
            row=entry,
        )
    return support._to_tracker_entry_model(detail_row)


def view_tracker_entry_notice_file(entry_id: UUID):
    notice_view_helpers = support._load_notice_view_helpers()
    tracker_repository = support._get_tracker_repository()
    try:
        entry = tracker_repository.get_entry(entry_id)
    except support.TrackerEntryRepositoryError as exc:
        support._repository_error(str(exc))

    if entry is None:
        support._not_found(f"tracker_entry not found: {entry_id}")

    source_row = support._select_tracker_entry_source_notice_row(entry)
    notice_source_row = _build_tracker_entry_notice_source_row(source_row=source_row, entry=entry)
    attachment = notice_view_helpers["select_primary_notice_attachment"](notice_source_row)
    attachment_url = str(attachment.get("url") or "").strip()
    file_name = str(attachment.get("file_name") or "").strip()
    title = str(entry.get("project_name") or file_name or "공고문").strip() or "공고문"
    bid_no = str((notice_source_row or {}).get("bid_no") or entry.get("source_bid_no") or "").strip().upper()
    bid_ord = str((notice_source_row or {}).get("bid_ord") or entry.get("source_bid_ord") or "000").strip() or "000"
    unty_atch_file_no = str(
        (notice_source_row or {}).get("item_pbanc_unty_atch_file_no")
        or (notice_source_row or {}).get("itemPbancUntyAtchFileNo")
        or ""
    ).strip()
    if not attachment_url:
        return HTMLResponse(
            notice_view_helpers["build_notice_file_fallback_html"](
                title=title,
                message="원공고 첨부 공고문을 찾지 못했습니다.",
            ),
            status_code=status.HTTP_404_NOT_FOUND,
        )

    try:
        viewer_url = notice_view_helpers["resolve_notice_viewer_url"](
            bid_no=bid_no,
            bid_ord=bid_ord,
            attachment_url=attachment_url,
            unty_atch_file_no=unty_atch_file_no,
        )
    except Exception:
        viewer_url = ""
    if viewer_url:
        return RedirectResponse(url=viewer_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    try:
        data, content_type = notice_view_helpers["download_notice_attachment"](url=attachment_url)
    except Exception:
        return HTMLResponse(
            notice_view_helpers["build_notice_file_fallback_html"](
                title=title,
                message="공고문 파일을 불러오지 못했습니다.",
                file_url=attachment_url,
            ),
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    suffix = notice_view_helpers["infer_notice_attachment_suffix"](
        file_name=file_name,
        content_type=content_type,
        data=data,
    )
    if suffix == ".pdf":
        headers = {"Content-Disposition": f"inline; filename*=UTF-8''{quote(file_name or 'notice.pdf')}"}
        return Response(content=data, media_type="application/pdf", headers=headers)
    if suffix == ".hwp":
        rendered_html = notice_view_helpers["render_hwp_notice_html"](data=data, title=title)
        if rendered_html:
            return HTMLResponse(content=rendered_html)
        return HTMLResponse(
            notice_view_helpers["build_notice_file_fallback_html"](
                title=title,
                message="HWP 공고문을 화면에 표시하지 못했습니다. 아래 링크로 원본 파일을 열 수 있습니다.",
                file_url=attachment_url,
            ),
            status_code=status.HTTP_200_OK,
        )
    if str(content_type).startswith("image/"):
        headers = {"Content-Disposition": f"inline; filename*=UTF-8''{quote(file_name or 'notice')}"}
        return Response(content=data, media_type=content_type or "image/png", headers=headers)
    return HTMLResponse(
        notice_view_helpers["build_notice_file_fallback_html"](
            title=title,
            message="이 형식의 공고문은 브라우저에서 바로 표시하지 못했습니다. 아래 링크로 원본 파일을 열 수 있습니다.",
            file_url=attachment_url,
        ),
        status_code=status.HTTP_200_OK,
    )


def _build_tracker_entry_notice_source_row(
    *,
    source_row: dict[str, Any] | None,
    entry: dict[str, Any],
) -> dict[str, Any] | None:
    row = dict(source_row or {})
    bid_no = str(row.get("bid_no") or entry.get("source_bid_no") or "").strip().upper()
    if not bid_no:
        return row or None
    bid_ord = str(row.get("bid_ord") or entry.get("source_bid_ord") or "000").strip() or "000"
    row["bid_no"] = bid_no
    row["bid_ord"] = bid_ord
    if not _tracker_notice_source_row_has_url(row):
        fallback_url = (
            "https://www.g2b.go.kr/link/PNPE027_01/single/"
            f"?bidPbancNo={quote(bid_no, safe='')}&bidPbancOrd={quote(bid_ord, safe='')}"
        )
        row["notice_url"] = fallback_url
        row["bid_ntce_dtl_url"] = fallback_url
    return row


def _tracker_notice_source_row_has_url(row: dict[str, Any]) -> bool:
    for key in ("notice_url", "bid_ntce_dtl_url", "bid_ntce_url", "base_url"):
        if str(row.get(key) or "").strip():
            return True
    return False


def list_tracker_entry_audit_logs(*, entry_id: UUID, cursor: int | None, limit: int) -> Any:
    tracker_repository = support._get_tracker_repository()
    try:
        entry = tracker_repository.get_entry(entry_id)
    except support.TrackerEntryRepositoryError as exc:
        support._repository_error(str(exc))

    if entry is None:
        support._not_found(f"tracker_entry not found: {entry_id}")

    try:
        items, next_cursor = tracker_repository.list_audit_logs(
            entry_id=entry_id,
            cursor=cursor,
            limit=limit,
        )
    except support.TrackerEntryRepositoryError as exc:
        support._repository_error(str(exc))

    return support.TrackerEntryAuditLogListResponse(
        items=[support._to_audit_log_model(item) for item in items],
        next_cursor=next_cursor,
    )
