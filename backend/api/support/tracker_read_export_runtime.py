from __future__ import annotations

import logging
import threading
import time
from typing import Any
from uuid import UUID


def is_global_tracker_scope(
    *,
    source_run_id: UUID | None,
    source_tracker_run_id: UUID | None,
    sheet_name: str,
    section_name: str,
    app_mock: Any,
) -> bool:
    mock = app_mock("_is_global_tracker_scope")
    if mock is not None:
        return mock(
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        )
    return (
        source_run_id is None
        and source_tracker_run_id is None
        and not str(sheet_name or "").strip()
        and not str(section_name or "").strip()
    )


def load_global_tracker_rows(
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
    mock = app_mock("_load_global_tracker_rows")
    if mock is not None:
        return mock(force_refresh=force_refresh)

    build_event: threading.Event | None = None
    build_serial = 0

    while True:
        now = time.monotonic()
        wait_event: threading.Event | None = None
        with cache_lock:
            cache_state = cache_state_getter()
            if not force_refresh and cache_state is not None:
                expires_at, cached_rows = cache_state
                if expires_at > now:
                    return [dict(item) for item in cached_rows]
            current_build_event = cache_build_event_getter()
            if current_build_event is None:
                build_event = threading.Event()
                cache_build_event_setter(build_event)
                build_serial = cache_serial_getter()
                break
            wait_event = current_build_event
        if wait_event is not None:
            wait_event.wait(cache_wait_timeout_sec)

    assert build_event is not None
    try:
        rows = load_all_tracker_entries_for_global_summary_fn()
        collapsed = collapse_tracker_rows_by_project_fn(rows)
    except Exception:
        with cache_lock:
            if cache_build_event_getter() is build_event:
                cache_build_event_setter(None)
        build_event.set()
        raise

    stale_build = False
    with cache_lock:
        stale_build = cache_serial_getter() != build_serial
        if not stale_build:
            cache_state_setter(
                (
                    time.monotonic() + cache_ttl_sec,
                    [dict(item) for item in collapsed],
                )
            )
        if cache_build_event_getter() is build_event:
            cache_build_event_setter(None)
    build_event.set()
    if stale_build:
        return load_global_tracker_rows(
            force_refresh=False,
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
    return [dict(item) for item in collapsed]


def clear_global_tracker_rows_cache(
    *,
    cache_lock: threading.Lock,
    clear_cache_state: Any,
    increment_global_serial: Any,
    workbook_cache_lock: threading.Lock,
    clear_workbook_cache: Any,
    increment_workbook_serial: Any,
) -> None:
    with cache_lock:
        clear_cache_state()
        increment_global_serial()
    with workbook_cache_lock:
        clear_workbook_cache()
        increment_workbook_serial()


def list_tracker_entries_for_export(
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
    return _list_tracker_entries_for_export_impl(
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


def can_cache_tracker_export_workbook(
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
    return can_cache_tracker_export_workbook_impl_fn(
        format=format,
        q=q,
        region=region,
        edited_only=edited_only,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        is_global_tracker_scope_fn=is_global_tracker_scope_fn,
    )


def build_tracker_export_workbook_cache_key(
    *,
    q: str,
    region: str,
    edited_only: bool,
    exclude_auxiliary_titles: bool,
    blank_progress_note: bool,
    build_tracker_export_workbook_cache_key_impl_fn: Any,
) -> str:
    return build_tracker_export_workbook_cache_key_impl_fn(
        q=q,
        region=region,
        edited_only=edited_only,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        blank_progress_note=blank_progress_note,
    )


def get_or_build_cached_tracker_export_workbook_bytes(
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
    return get_or_build_cached_tracker_export_workbook_bytes_impl_fn(
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
        monotonic_fn=time.monotonic,
    )


def warm_default_user_tracker_export_workbook(
    *,
    get_or_build_cached_tracker_export_workbook_bytes_fn: Any,
    logger: Any | None = None,
    warm_default_user_tracker_export_workbook_impl_fn: Any = None,
) -> None:
    warm_default_user_tracker_export_workbook_impl_fn(
        get_or_build_cached_tracker_export_workbook_bytes_fn=get_or_build_cached_tracker_export_workbook_bytes_fn,
        logger=logger or logging.getLogger("perf.download"),
    )


def warm_tracker_export_workbook_for_request(
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
    if not can_cache_tracker_export_workbook_fn(
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
        get_or_build_cached_tracker_export_workbook_bytes_fn(
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
        (logger or logging.getLogger("perf.download")).exception("tracker export workbook filter warm failed")


def build_tracker_missing_report(
    *,
    limit: int,
    app_override: Any,
    original_override_target: Any,
    collect_all_tracker_entries_fn: Any | None,
    load_winner_index_by_run_fn: Any | None,
    app_dependency: Any,
    app_module: Any,
    default_load_winner_index_by_run_fn: Any,
    coerce_uuid_or_none_fn: Any,
    tracker_missing_field_specs: Any,
    tracker_missing_reason_explainers: Any,
    build_tracker_missing_report_impl_fn: Any,
) -> tuple[Any, list[Any]]:
    override = app_override("_build_tracker_missing_report", original_override_target)
    if override is not None and collect_all_tracker_entries_fn is None and load_winner_index_by_run_fn is None:
        return override(limit=limit)
    if collect_all_tracker_entries_fn is None:
        collect_all_tracker_entries_fn = app_dependency("_collect_all_tracker_entries", app_module()._collect_all_tracker_entries)
    if load_winner_index_by_run_fn is None:
        load_winner_index_by_run_fn = app_dependency("_load_winner_index_by_run", default_load_winner_index_by_run_fn)
    return build_tracker_missing_report_impl_fn(
        limit=limit,
        collect_all_tracker_entries=collect_all_tracker_entries_fn,
        load_winner_index_by_run_fn=load_winner_index_by_run_fn,
        coerce_uuid_or_none=coerce_uuid_or_none_fn,
        tracker_missing_field_specs=tracker_missing_field_specs,
        tracker_missing_reason_explainers=tracker_missing_reason_explainers,
    )


def flatten_tracker_missing_report_rows(
    *,
    summary: Any,
    items: list[Any],
    flatten_tracker_missing_report_rows_impl_fn: Any,
) -> list[dict[str, Any]]:
    return flatten_tracker_missing_report_rows_impl_fn(summary=summary, items=items)


from backend.services.tracker_export_workbook_backend import list_tracker_entries_for_export as _list_tracker_entries_for_export_impl
