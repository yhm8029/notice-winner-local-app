from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any
from uuid import UUID

TRACKER_EXPORT_WORKBOOK_LAYOUT_VERSION = 2


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
    if is_global_tracker_scope_fn(
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
    ):
        rows = filter_tracker_rows_for_global_scope_fn(
            load_global_tracker_rows_fn(),
            q=q,
            region=region,
            exclude_auxiliary_titles=exclude_auxiliary_titles,
            edited_only=edited_only,
        )
        return normalize_tracker_rows_for_presentation_fn(rows)
    return normalize_tracker_rows_for_presentation_fn(
        load_all_tracker_entries_for_export_fn(
            q=q,
            region=region,
            exclude_auxiliary_titles=exclude_auxiliary_titles,
            edited_only=edited_only,
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        )
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
    is_global_tracker_scope_fn: Any | None = None,
) -> bool:
    del q
    del region
    del edited_only
    normalized_format = str(format or "").strip().lower()
    if normalized_format != "xlsx":
        return False
    if is_global_tracker_scope_fn is None:
        return not any(
            (
                source_run_id,
                source_tracker_run_id,
                str(sheet_name or "").strip(),
                str(section_name or "").strip(),
            )
        )
    return bool(
        is_global_tracker_scope_fn(
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        )
    )


def build_tracker_export_workbook_cache_key(
    *,
    q: str,
    region: str,
    edited_only: bool,
    exclude_auxiliary_titles: bool,
    blank_progress_note: bool,
) -> str:
    return json.dumps(
        {
            "scope": "global-xlsx",
            "workbook_layout_version": TRACKER_EXPORT_WORKBOOK_LAYOUT_VERSION,
            "q": str(q or "").strip(),
            "region": str(region or "").strip(),
            "edited_only": bool(edited_only),
            "exclude_auxiliary_titles": bool(exclude_auxiliary_titles),
            "blank_progress_note": bool(blank_progress_note),
        },
        ensure_ascii=False,
        sort_keys=True,
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
    build_tracker_export_workbook_cache_key_fn: Any = build_tracker_export_workbook_cache_key,
    monotonic_fn: Any = time.monotonic,
) -> bytes:
    cache_key = build_tracker_export_workbook_cache_key_fn(
        q=q,
        region=region,
        edited_only=edited_only,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        blank_progress_note=blank_progress_note,
    )
    build_event: threading.Event | None = None
    build_serial = 0

    while True:
        now = monotonic_fn()
        wait_event: threading.Event | None = None
        with cache_lock:
            cached = cache.get(cache_key)
            if cached is not None:
                expires_at, payload = cached
                if expires_at > now:
                    return payload
            build_event = cache_build_events.get(cache_key)
            if build_event is None:
                build_event = threading.Event()
                cache_build_events[cache_key] = build_event
                build_serial = int(cache_serial_fn())
                break
            wait_event = build_event
        if wait_event is not None:
            wait_event.wait(cache_wait_timeout_sec)

    assert build_event is not None
    try:
        rows = list_tracker_entries_for_export_fn(
            q=q,
            region=region,
            exclude_auxiliary_titles=exclude_auxiliary_titles,
            edited_only=edited_only,
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        )
        if blank_progress_note:
            rows = [{**row, "progress_note": ""} for row in rows]
        payload = build_tracking_download_workbook_bytes_fn(rows=rows)
    except Exception:
        with cache_lock:
            current_event = cache_build_events.get(cache_key)
            if current_event is build_event:
                cache_build_events.pop(cache_key, None)
        build_event.set()
        raise

    stale_build = False
    with cache_lock:
        stale_build = int(cache_serial_fn()) != build_serial
        if not stale_build:
            if len(cache) >= cache_max_entries:
                expired_keys = [key for key, (expires_at, _payload) in cache.items() if expires_at <= monotonic_fn()]
                for expired_key in expired_keys:
                    cache.pop(expired_key, None)
                if len(cache) >= cache_max_entries:
                    oldest_key = min(cache.items(), key=lambda item: item[1][0])[0]
                    cache.pop(oldest_key, None)
            cache[cache_key] = (monotonic_fn() + cache_ttl_sec, payload)
        current_event = cache_build_events.get(cache_key)
        if current_event is build_event:
            cache_build_events.pop(cache_key, None)
    build_event.set()
    if stale_build:
        return get_or_build_cached_tracker_export_workbook_bytes(
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
            monotonic_fn=monotonic_fn,
        )
    return payload


def warm_default_user_tracker_export_workbook(
    *,
    get_or_build_cached_tracker_export_workbook_bytes_fn: Any,
    logger: Any | None = None,
) -> None:
    try:
        get_or_build_cached_tracker_export_workbook_bytes_fn(
            q="",
            region="",
            exclude_auxiliary_titles=True,
            edited_only=False,
            blank_progress_note=True,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )
    except Exception:
        target_logger = logger or logging.getLogger("perf.download")
        target_logger.exception("tracker export workbook warm failed")
