from __future__ import annotations

import logging
import sys
import threading
import time
from typing import Any
from uuid import UUID

from backend.api.routers import tracker_cache_support as support


def _app_module():
    return support._app_module()


def _materialize_tracker_entry_snapshot_views(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    artifact_file_helpers = support._load_artifact_file_helpers()
    return support._materialize_tracker_entry_snapshot_views_impl(
        rows,
        annotate_tracker_entries_with_project_refs_fn=support._annotate_tracker_entries_with_project_refs,
        annotate_tracker_entries_with_opening_dates_fn=support._annotate_tracker_entries_with_opening_dates,
        annotate_tracker_entries_with_field_diagnostics_fn=support._annotate_tracker_entries_with_field_diagnostics,
        normalize_tracker_rows_for_presentation_fn=support._normalize_tracker_rows_for_presentation,
        coerce_uuid_or_none_fn=support._coerce_uuid_or_none,
        model_to_json_dict_fn=support._model_to_json_dict,
        to_tracker_entry_summary_model_fn=support._to_tracker_entry_summary_model,
        to_tracker_entry_model_fn=support._to_tracker_entry_model,
        tracking_export_fieldnames=artifact_file_helpers["tracking_export_fieldnames"],
        utc_now_fn=support._utc_now,
    )


def _is_tracker_entry_snapshot_fresh(snapshot: dict[str, Any], row: dict[str, Any]) -> bool:
    return support._is_tracker_entry_snapshot_fresh_impl(
        snapshot,
        row,
        parse_iso_datetime_fn=support._parse_iso_datetime,
    )


def _load_tracker_entry_snapshot_map(
    *,
    organization_id: UUID,
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return support._load_tracker_entry_snapshot_map_impl(
        organization_id=organization_id,
        rows=rows,
        coerce_uuid_or_none_fn=support._coerce_uuid_or_none,
        get_tracker_entry_snapshot_repository_fn=support._get_tracker_entry_snapshot_repository,
    )


def _upsert_tracker_entry_snapshots_best_effort(
    *,
    organization_id: UUID,
    rows: list[dict[str, Any]],
    materialized: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    return support._upsert_tracker_entry_snapshots_best_effort_impl(
        organization_id=organization_id,
        rows=rows,
        materialized=materialized,
        get_tracker_entry_snapshot_repository_fn=support._get_tracker_entry_snapshot_repository,
        materialize_tracker_entry_snapshot_views_fn=support._materialize_tracker_entry_snapshot_views,
    )


def _hydrate_tracker_entry_summary_rows(
    *,
    organization_id: UUID,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return support._hydrate_tracker_entry_summary_rows_impl(
        organization_id=organization_id,
        rows=rows,
        load_tracker_entry_snapshot_map_fn=support._load_tracker_entry_snapshot_map,
        is_tracker_entry_snapshot_fresh_fn=support._is_tracker_entry_snapshot_fresh,
        upsert_tracker_entry_snapshots_best_effort_fn=support._upsert_tracker_entry_snapshots_best_effort,
    )


def _hydrate_tracker_entry_export_rows(
    *,
    organization_id: UUID,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return support._hydrate_tracker_entry_export_rows_impl(
        organization_id=organization_id,
        rows=rows,
        load_tracker_entry_snapshot_map_fn=support._load_tracker_entry_snapshot_map,
        is_tracker_entry_snapshot_fresh_fn=support._is_tracker_entry_snapshot_fresh,
        upsert_tracker_entry_snapshots_best_effort_fn=support._upsert_tracker_entry_snapshots_best_effort,
    )


def _hydrate_tracker_entry_detail_row(
    *,
    organization_id: UUID,
    row: dict[str, Any],
) -> dict[str, Any]:
    return support._hydrate_tracker_entry_detail_row_impl(
        organization_id=organization_id,
        row=row,
        load_tracker_entry_snapshot_map_fn=support._load_tracker_entry_snapshot_map,
        is_tracker_entry_snapshot_fresh_fn=support._is_tracker_entry_snapshot_fresh,
        upsert_tracker_entry_snapshots_best_effort_fn=support._upsert_tracker_entry_snapshots_best_effort,
    )


def _load_all_tracker_entries_for_global_summary() -> list[dict[str, Any]]:
    tracker_repository = support._get_tracker_repository()
    organization_id = support.load_phase1_identity().organization_id
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
        except support.TrackerEntryRepositoryError as exc:
            support._repository_error(str(exc))
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page_size:
            break
        page += 1
    return support._hydrate_tracker_entry_summary_rows(
        organization_id=organization_id,
        rows=rows,
    )


def _load_global_tracker_rows(*, force_refresh: bool = False) -> list[dict[str, Any]]:
    support._maybe_clear_tracker_caches_for_memory_soft_cap()
    app_module = _app_module()
    build_event: threading.Event | None = None
    build_serial = 0

    while True:
        now = time.monotonic()
        wait_event: threading.Event | None = None
        with app_module._TRACKER_GLOBAL_ROWS_CACHE_LOCK:
            if not force_refresh and app_module._TRACKER_GLOBAL_ROWS_CACHE is not None:
                expires_at, cached_rows = app_module._TRACKER_GLOBAL_ROWS_CACHE
                if expires_at > now:
                    return [dict(item) for item in cached_rows]
            if app_module._TRACKER_GLOBAL_ROWS_CACHE_BUILD_EVENT is None:
                build_event = threading.Event()
                app_module._TRACKER_GLOBAL_ROWS_CACHE_BUILD_EVENT = build_event
                build_serial = app_module._TRACKER_GLOBAL_ROWS_CACHE_SERIAL
                break
            wait_event = app_module._TRACKER_GLOBAL_ROWS_CACHE_BUILD_EVENT
        if wait_event is not None:
            wait_event.wait(app_module.TRACKER_GLOBAL_ROWS_CACHE_WAIT_TIMEOUT_SEC)

    assert build_event is not None
    try:
        rows = support._load_all_tracker_entries_for_global_summary()
        collapsed = support._collapse_tracker_rows_by_project(rows)
    except Exception:
        with app_module._TRACKER_GLOBAL_ROWS_CACHE_LOCK:
            if app_module._TRACKER_GLOBAL_ROWS_CACHE_BUILD_EVENT is build_event:
                app_module._TRACKER_GLOBAL_ROWS_CACHE_BUILD_EVENT = None
        build_event.set()
        raise

    stale_build = False
    with app_module._TRACKER_GLOBAL_ROWS_CACHE_LOCK:
        stale_build = app_module._TRACKER_GLOBAL_ROWS_CACHE_SERIAL != build_serial
        if not stale_build:
            app_module._TRACKER_GLOBAL_ROWS_CACHE = (
                time.monotonic() + app_module.TRACKER_GLOBAL_ROWS_CACHE_TTL_SEC,
                [dict(item) for item in collapsed],
            )
        if app_module._TRACKER_GLOBAL_ROWS_CACHE_BUILD_EVENT is build_event:
            app_module._TRACKER_GLOBAL_ROWS_CACHE_BUILD_EVENT = None
    build_event.set()
    if stale_build:
        return support._load_global_tracker_rows(force_refresh=False)
    return [dict(item) for item in collapsed]


def _clear_global_tracker_rows_cache() -> None:
    app_module = _app_module()
    with app_module._TRACKER_GLOBAL_ROWS_CACHE_LOCK:
        app_module._TRACKER_GLOBAL_ROWS_CACHE = None
        app_module._TRACKER_GLOBAL_ROWS_CACHE_SERIAL += 1
    with app_module._TRACKER_EXPORT_WORKBOOK_CACHE_LOCK:
        app_module._TRACKER_EXPORT_WORKBOOK_CACHE.clear()
        app_module._TRACKER_EXPORT_WORKBOOK_CACHE_SERIAL += 1


def _get_process_rss_bytes() -> int | None:
    if not sys.platform.startswith("linux"):
        return None
    try:
        with open("/proc/self/status", "r", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        return int(parts[1]) * 1024
    except OSError:
        return None
    return None


def _maybe_clear_tracker_caches_for_memory_soft_cap() -> bool:
    app_module = _app_module()
    rss_bytes = support._get_process_rss_bytes()
    if rss_bytes is None or rss_bytes < app_module.TRACKER_MEMORY_SOFT_CAP_RSS_BYTES:
        return False

    now = time.monotonic()
    last_clear = app_module._TRACKER_MEMORY_SOFT_CAP_LAST_CLEAR_MONOTONIC
    if last_clear is not None and (now - last_clear) < app_module.TRACKER_MEMORY_SOFT_CAP_COOLDOWN_SEC:
        return False

    support._clear_global_tracker_rows_cache()
    app_module._TRACKER_MEMORY_SOFT_CAP_LAST_CLEAR_MONOTONIC = now
    logging.getLogger("perf.tracker").warning(
        "TRACKER_MEMORY_SOFT_CAP_CLEAR rss_bytes=%s threshold_bytes=%s cooldown_sec=%s",
        rss_bytes,
        app_module.TRACKER_MEMORY_SOFT_CAP_RSS_BYTES,
        app_module.TRACKER_MEMORY_SOFT_CAP_COOLDOWN_SEC,
    )
    return True
