from __future__ import annotations

import threading
from typing import Any
from uuid import UUID

from backend.api.support import tracker_read_export_runtime
from backend.services.tracker_diagnostic_backend import flatten_tracker_missing_report_rows as _flatten_tracker_missing_report_rows_impl
from backend.services.tracker_export_workbook_backend import build_tracker_export_workbook_cache_key as _build_tracker_export_workbook_cache_key_impl
from backend.services.tracker_export_workbook_backend import can_cache_tracker_export_workbook as _can_cache_tracker_export_workbook_impl
from backend.services.tracker_export_workbook_backend import get_or_build_cached_tracker_export_workbook_bytes as _get_or_build_cached_tracker_export_workbook_bytes_impl
from backend.services.tracker_export_workbook_backend import list_tracker_entries_for_export as _list_tracker_entries_for_export_impl
from backend.services.tracker_export_workbook_backend import warm_default_user_tracker_export_workbook as _warm_default_user_tracker_export_workbook_impl
from backend.services.tracker_global_summary_backend import collapse_tracker_rows_by_project as _collapse_tracker_rows_by_project_impl
from backend.services.tracker_global_summary_backend import filter_tracker_rows_for_global_scope as _filter_tracker_rows_for_global_scope_impl
from backend.services.tracker_global_summary_backend import merge_global_tracker_row_group as _merge_global_tracker_row_group_impl
from backend.services.tracker_global_summary_backend import tracker_row_merge_identity as _tracker_row_merge_identity_impl
from backend.services.tracker_global_summary_backend import tracker_row_merge_score as _tracker_row_merge_score_impl
from backend.repositories import TrackerEntryRepositoryError


def _tracker_row_merge_score(row: dict[str, Any]) -> tuple[int, int, int, int]:
    return _tracker_row_merge_score_impl(row)


def _tracker_row_merge_identity(
    row: dict[str, Any],
    *,
    normalize_tracker_bid_ord_fn: Any,
    norm_text_fn: Any,
) -> tuple[str, str, str]:
    return _tracker_row_merge_identity_impl(
        row,
        normalize_tracker_bid_ord_fn=normalize_tracker_bid_ord_fn,
        norm_text_fn=norm_text_fn,
    )


def _merge_global_tracker_row_group(
    rows: list[dict[str, Any]],
    *,
    tracker_row_merge_score_fn: Any,
    tracker_row_merge_identity_fn: Any,
    better_project_label_fn: Any,
) -> dict[str, Any]:
    return _merge_global_tracker_row_group_impl(
        rows,
        tracker_row_merge_score_fn=tracker_row_merge_score_fn,
        tracker_row_merge_identity_fn=tracker_row_merge_identity_fn,
        better_project_label_fn=better_project_label_fn,
    )


def _collapse_tracker_rows_by_project(
    rows: list[dict[str, Any]],
    *,
    derive_tracker_entry_project_identity_fn: Any,
    norm_text_fn: Any,
    merge_global_tracker_row_group_fn: Any,
) -> list[dict[str, Any]]:
    return _collapse_tracker_rows_by_project_impl(
        rows,
        derive_tracker_entry_project_identity_fn=derive_tracker_entry_project_identity_fn,
        norm_text_fn=norm_text_fn,
        merge_global_tracker_row_group_fn=merge_global_tracker_row_group_fn,
    )


def _filter_tracker_rows_for_global_scope(
    rows: list[dict[str, Any]],
    *,
    q: str,
    region: str,
    exclude_auxiliary_titles: bool,
    edited_only: bool,
    norm_text_fn: Any,
    tracker_entry_matches_title_visibility_fn: Any,
    tracker_entry_matches_region_fn: Any,
) -> list[dict[str, Any]]:
    return _filter_tracker_rows_for_global_scope_impl(
        rows,
        q=q,
        region=region,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        edited_only=edited_only,
        norm_text_fn=norm_text_fn,
        tracker_entry_matches_title_visibility_fn=tracker_entry_matches_title_visibility_fn,
        tracker_entry_matches_region_fn=tracker_entry_matches_region_fn,
    )


def _load_all_tracker_entries_for_export(
    *,
    q: str,
    region: str,
    exclude_auxiliary_titles: bool,
    edited_only: bool,
    source_run_id: UUID | None,
    source_tracker_run_id: UUID | None,
    sheet_name: str,
    section_name: str,
    get_tracker_repository_fn: Any,
    load_phase1_identity_fn: Any,
    hydrate_tracker_entry_export_rows_fn: Any,
    repository_error_fn: Any,
) -> list[dict[str, Any]]:
    tracker_repository = get_tracker_repository_fn()
    organization_id = load_phase1_identity_fn().organization_id
    page = 1
    page_size = 500
    rows: list[dict[str, Any]] = []
    while True:
        try:
            batch, _total = tracker_repository.list_entries_for_export(
                page=page,
                page_size=page_size,
                q=q,
                region=region,
                exclude_auxiliary_titles=exclude_auxiliary_titles,
                edited_only=edited_only,
                source_run_id=source_run_id,
                source_tracker_run_id=source_tracker_run_id,
                sheet_name=sheet_name,
                section_name=section_name,
            )
        except TrackerEntryRepositoryError as exc:
            repository_error_fn(str(exc))
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page_size:
            break
        page += 1
    return hydrate_tracker_entry_export_rows_fn(
        organization_id=organization_id,
        rows=rows,
    )


def _load_all_tracker_entries_for_global_summary(
    *,
    get_tracker_repository_fn: Any,
    load_phase1_identity_fn: Any,
    hydrate_tracker_entry_summary_rows_fn: Any,
    repository_error_fn: Any,
) -> list[dict[str, Any]]:
    tracker_repository = get_tracker_repository_fn()
    organization_id = load_phase1_identity_fn().organization_id
    page = 1
    page_size = 200
    rows: list[dict[str, Any]] = []
    while True:
        try:
            batch, _total = tracker_repository.list_entries(
                page=page,
                page_size=page_size,
                q="",
                region="",
                exclude_auxiliary_titles=False,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=None,
                sheet_name="",
                section_name="",
            )
        except TrackerEntryRepositoryError as exc:
            repository_error_fn(str(exc))
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page_size:
            break
        page += 1
    return hydrate_tracker_entry_summary_rows_fn(
        organization_id=organization_id,
        rows=rows,
    )


def _is_global_tracker_scope(
    *,
    source_run_id: UUID | None,
    source_tracker_run_id: UUID | None,
    sheet_name: str,
    section_name: str,
    app_mock: Any,
) -> bool:
    return tracker_read_export_runtime.is_global_tracker_scope(
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        app_mock=app_mock,
    )


def _load_global_tracker_rows(
    *,
    force_refresh: bool,
    app_mock: Any,
    cache_lock: threading.Lock,
    cache_state_getter: Any,
    cache_state_setter: Any,
    cache_build_event_getter: Any,
    cache_build_event_setter: Any,
    cache_serial_getter: Any,
    cache_ttl_sec: float,
    cache_wait_timeout_sec: float,
    load_all_tracker_entries_for_global_summary_fn: Any,
    collapse_tracker_rows_by_project_fn: Any,
) -> list[dict[str, Any]]:
    return tracker_read_export_runtime.load_global_tracker_rows(
        force_refresh=force_refresh,
        app_mock=app_mock,
        cache_lock=cache_lock,
        cache_state_getter=cache_state_getter,
        cache_state_setter=cache_state_setter,
        cache_build_event_getter=cache_build_event_getter,
        cache_build_event_setter=cache_build_event_setter,
        cache_serial_getter=cache_serial_getter,
        cache_ttl_sec=cache_ttl_sec,
        cache_wait_timeout_sec=cache_wait_timeout_sec,
        load_all_tracker_entries_for_global_summary_fn=load_all_tracker_entries_for_global_summary_fn,
        collapse_tracker_rows_by_project_fn=collapse_tracker_rows_by_project_fn,
    )


def _clear_global_tracker_rows_cache(
    *,
    cache_lock: threading.Lock,
    clear_cache_state: Any,
    increment_global_serial: Any,
    workbook_cache_lock: threading.Lock,
    clear_workbook_cache: Any,
    increment_workbook_serial: Any,
) -> None:
    tracker_read_export_runtime.clear_global_tracker_rows_cache(
        cache_lock=cache_lock,
        clear_cache_state=clear_cache_state,
        increment_global_serial=increment_global_serial,
        workbook_cache_lock=workbook_cache_lock,
        clear_workbook_cache=clear_workbook_cache,
        increment_workbook_serial=increment_workbook_serial,
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
    is_global_tracker_scope_fn: Any,
    filter_tracker_rows_for_global_scope_fn: Any,
    load_global_tracker_rows_fn: Any,
    normalize_tracker_rows_for_presentation_fn: Any,
    load_all_tracker_entries_for_export_fn: Any,
) -> list[dict[str, Any]]:
    return tracker_read_export_runtime.list_tracker_entries_for_export(
        q=q,
        region=region,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        edited_only=edited_only,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        is_global_tracker_scope_fn=is_global_tracker_scope_fn,
        filter_tracker_rows_for_global_scope_fn=filter_tracker_rows_for_global_scope_fn,
        load_global_tracker_rows_fn=load_global_tracker_rows_fn,
        normalize_tracker_rows_for_presentation_fn=normalize_tracker_rows_for_presentation_fn,
        load_all_tracker_entries_for_export_fn=load_all_tracker_entries_for_export_fn,
    )


def _can_cache_tracker_export_workbook(
    *,
    format: str,
    q: str,
    region: str,
    edited_only: bool,
    source_run_id: UUID | None,
    source_tracker_run_id: UUID | None,
    sheet_name: str,
    section_name: str,
    is_global_tracker_scope_fn: Any,
    can_cache_tracker_export_workbook_impl_fn: Any,
) -> bool:
    return tracker_read_export_runtime.can_cache_tracker_export_workbook(
        format=format,
        q=q,
        region=region,
        edited_only=edited_only,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        is_global_tracker_scope_fn=is_global_tracker_scope_fn,
        can_cache_tracker_export_workbook_impl_fn=can_cache_tracker_export_workbook_impl_fn,
    )


def _build_tracker_export_workbook_cache_key(
    *,
    q: str,
    region: str,
    edited_only: bool,
    exclude_auxiliary_titles: bool,
    blank_progress_note: bool,
    build_tracker_export_workbook_cache_key_impl_fn: Any,
) -> str:
    return tracker_read_export_runtime.build_tracker_export_workbook_cache_key(
        q=q,
        region=region,
        edited_only=edited_only,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        blank_progress_note=blank_progress_note,
        build_tracker_export_workbook_cache_key_impl_fn=build_tracker_export_workbook_cache_key_impl_fn,
    )


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
    cache_lock: threading.Lock,
    cache: dict[str, tuple[float, bytes]],
    cache_build_events: dict[str, threading.Event],
    cache_serial_fn: Any,
    cache_ttl_sec: float,
    cache_wait_timeout_sec: float,
    cache_max_entries: int,
    list_tracker_entries_for_export_fn: Any,
    build_tracking_download_workbook_bytes_fn: Any,
    build_tracker_export_workbook_cache_key_fn: Any,
    get_or_build_cached_tracker_export_workbook_bytes_impl_fn: Any,
) -> bytes:
    return tracker_read_export_runtime.get_or_build_cached_tracker_export_workbook_bytes(
        q=q,
        region=region,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        edited_only=edited_only,
        blank_progress_note=blank_progress_note,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        cache_lock=cache_lock,
        cache=cache,
        cache_build_events=cache_build_events,
        cache_serial_fn=cache_serial_fn,
        cache_ttl_sec=cache_ttl_sec,
        cache_wait_timeout_sec=cache_wait_timeout_sec,
        cache_max_entries=cache_max_entries,
        list_tracker_entries_for_export_fn=list_tracker_entries_for_export_fn,
        build_tracking_download_workbook_bytes_fn=build_tracking_download_workbook_bytes_fn,
        build_tracker_export_workbook_cache_key_fn=build_tracker_export_workbook_cache_key_fn,
        get_or_build_cached_tracker_export_workbook_bytes_impl_fn=get_or_build_cached_tracker_export_workbook_bytes_impl_fn,
    )


def _warm_default_user_tracker_export_workbook(
    *,
    get_or_build_cached_tracker_export_workbook_bytes_fn: Any,
    logger: Any | None = None,
    warm_default_user_tracker_export_workbook_impl_fn: Any,
) -> None:
    tracker_read_export_runtime.warm_default_user_tracker_export_workbook(
        get_or_build_cached_tracker_export_workbook_bytes_fn=get_or_build_cached_tracker_export_workbook_bytes_fn,
        logger=logger,
        warm_default_user_tracker_export_workbook_impl_fn=warm_default_user_tracker_export_workbook_impl_fn,
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
    can_cache_tracker_export_workbook_fn: Any,
    get_or_build_cached_tracker_export_workbook_bytes_fn: Any,
    logger: Any | None = None,
) -> None:
    tracker_read_export_runtime.warm_tracker_export_workbook_for_request(
        q=q,
        region=region,
        edited_only=edited_only,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        blank_progress_note=blank_progress_note,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        can_cache_tracker_export_workbook_fn=can_cache_tracker_export_workbook_fn,
        get_or_build_cached_tracker_export_workbook_bytes_fn=get_or_build_cached_tracker_export_workbook_bytes_fn,
        logger=logger,
    )
