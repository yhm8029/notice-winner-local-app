from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any
from uuid import UUID

from fastapi import Request

from backend.api.schemas import TrackerEntryPatchRequest
from backend.api.schemas import TrackerEntryPatchResponse
from backend.api.support import tracker_read_support
from backend.api.support import tracker_support
from backend.api.support.runtime_common import _get_artifact_repository
from backend.api.support.runtime_common import _get_tracker_change_event_repository
from backend.api.support.runtime_common import _get_run_log_repository
from backend.api.support.runtime_common import _get_run_repository
from backend.api.support.runtime_common import _get_tracker_repository
from backend.api.support.runtime_common import _conflict_error
from backend.api.support.runtime_common import _not_found
from backend.api.support.runtime_common import _repository_error
from backend.api.support.runtime_common import _validation_error
from backend.api.routers.project_aggregate_handlers import _get_snapshot_project_aggregate
from backend.api.support.app_pure_helpers import json_safe_copy
from backend.api.support.run_support import _is_project_tracker_run_type
from backend.api.support.run_support import _load_run_execution_helpers
from backend.api.support.run_support import _run_visible_in_operational_views
from backend.api.support.run_support import _to_run_create_response
from backend.services.tracker_export_workbook_backend import TRACKER_EXPORT_WORKBOOK_LAYOUT_VERSION
from backend.repositories import ArtifactRepositoryError
from backend.repositories import get_home_bootstrap_snapshot_repository
from backend.repositories import RunRepositoryError
from backend.repositories import TrackerChangeEventRepositoryError
from backend.repositories import TrackerEntryRepositoryError
from backend.services.home_bootstrap_backend import invalidate_home_bootstrap_snapshot_best_effort
from backend.services.tracker_change_event_logic import build_tracker_change_event
from backend.services.tracker_change_event_logic import TrackerEventBuildInput
from backend.perf_runtime import ensure_request_id
from backend.perf_runtime import measure_stage


def _copy_response_model(payload: Any) -> Any:
    copy_fn = getattr(payload, "model_copy", None)
    if callable(copy_fn):
        return copy_fn(deep=True)
    return payload


def _read_ttl_model_cache(
    *,
    cache: dict[str, tuple[float, Any]] | tuple[float, Any] | None,
    cache_lock: threading.Lock,
    cache_key: str,
) -> Any | None:
    normalized_key = str(cache_key or "").strip()
    if not normalized_key:
        return None
    now = time.monotonic()
    with cache_lock:
      if isinstance(cache, dict):
          cached = cache.get(normalized_key)
          if cached is None:
              return None
          expires_at, payload = cached
      else:
          if cache is None:
              return None
          expires_at, payload = cache
      if expires_at <= now:
          if isinstance(cache, dict):
              cache.pop(normalized_key, None)
          return None
      return _copy_response_model(payload)


def _write_ttl_model_cache(
    *,
    cache: dict[str, tuple[float, Any]] | tuple[float, Any] | None,
    cache_lock: threading.Lock,
    cache_key: str,
    ttl_sec: float,
    payload: Any,
) -> Any:
    normalized_key = str(cache_key or "").strip()
    copied = _copy_response_model(payload)
    if not normalized_key:
        return copied
    with cache_lock:
        cache_entry = (time.monotonic() + ttl_sec, copied)
        if isinstance(cache, dict):
            cache[normalized_key] = cache_entry
        else:
            return _copy_response_model(copied)
    return _copy_response_model(copied)


def _clear_ttl_model_cache(
    *,
    cache: dict[str, tuple[float, Any]] | tuple[float, Any] | None,
    cache_lock: threading.Lock,
    cache_key: str | None = None,
) -> None:
    normalized_key = str(cache_key or "").strip()
    with cache_lock:
        if isinstance(cache, dict):
            if normalized_key:
                cache.pop(normalized_key, None)
            else:
                cache.clear()


def _json_safe_copy(value: Any) -> Any:
    return json_safe_copy(value)


def _build_tracker_download_job_cache_key(
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
    notice_year: str = "",
    data_version: str = "",
) -> str:
    return json.dumps(
        {
            "format": "xlsx",
            "workbook_layout_version": TRACKER_EXPORT_WORKBOOK_LAYOUT_VERSION,
            "data_version": str(data_version or ""),
            "q": str(q or "").strip(),
            "region": str(region or "").strip(),
            "notice_year": str(notice_year or "").strip(),
            "exclude_auxiliary_titles": bool(exclude_auxiliary_titles),
            "edited_only": bool(edited_only),
            "blank_progress_note": bool(blank_progress_note),
            "source_run_id": str(source_run_id or ""),
            "source_tracker_run_id": str(source_tracker_run_id or ""),
            "sheet_name": str(sheet_name or "").strip(),
            "section_name": str(section_name or "").strip(),
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _tracker_row_belongs_to_request_organization(
    row: dict[str, Any],
    *,
    organization_id: UUID,
) -> bool:
    raw_organization_id = str(row.get("organization_id") or "").strip()
    if not raw_organization_id:
        return False
    try:
        return UUID(raw_organization_id) == organization_id
    except ValueError:
        return False


def create_tracker_export_run(run_id: UUID) -> Any:
    from backend.phase1_defaults import PROJECT_TRACKER_RUN_TYPE

    run_repository = _get_run_repository()
    artifact_repository = _get_artifact_repository()
    try:
        parent = run_repository.get_run(run_id)
    except RunRepositoryError as exc:
        _repository_error(str(exc))

    if parent is None or not _run_visible_in_operational_views(parent):
        _not_found(f"run not found: {run_id}")

    if not _is_project_tracker_run_type(str(parent["run_type"])):
        _validation_error(f"tracker-export requires a {PROJECT_TRACKER_RUN_TYPE} parent run")

    if str(parent["status"]) != "success":
        _conflict_error(f"tracker-export requires a successful {PROJECT_TRACKER_RUN_TYPE} run")

    try:
        parent_artifacts = artifact_repository.list_artifacts(run_id=run_id)
    except ArtifactRepositoryError as exc:
        _repository_error(str(exc))

    if not any(str(item["artifact_type"]) == "winner_csv" for item in parent_artifacts):
        _conflict_error("tracker-export requires a winner_csv artifact on the parent run")

    try:
        queue_tracker_export_run_for_parent, _unused_safely_execute_project_tracker = _load_run_execution_helpers()
        stored, _created = queue_tracker_export_run_for_parent(run_id)
    except RunRepositoryError as exc:
        _repository_error(str(exc))
    return _to_run_create_response(stored)


def patch_tracker_entry(
    request: Request,
    entry_id: UUID,
    payload: TrackerEntryPatchRequest,
) -> TrackerEntryPatchResponse:
    tracker_support._validate_tracker_patch_request(payload)
    actor_user_id, actor_label = tracker_support._resolve_tracker_patch_actor(request, payload)
    request_id = ensure_request_id(request)
    organization_id = tracker_support._resolve_request_organization_id(request)

    tracker_repository = _get_tracker_repository()
    with measure_stage("tracker_entry_patch.load_before_entry", request_id=request_id, entry_id=str(entry_id)):
        before_entry = tracker_repository.get_entry(entry_id)
    if before_entry is None:
        _not_found(f"tracker_entry not found: {entry_id}")

    try:
        with measure_stage(
            "tracker_entry_patch.apply_override",
            request_id=request_id,
            entry_id=str(entry_id),
            field_name=payload.field_name,
        ):
            result = tracker_repository.apply_override(
                entry_id=entry_id,
                field_name=payload.field_name,
                new_value=payload.value,
                actor_user_id=actor_user_id,
                actor_label=actor_label,
                change_source=payload.change_source,
            )
    except TrackerEntryRepositoryError as exc:
        _repository_error(str(exc))

    if result is None:
        _not_found(f"tracker_entry not found: {entry_id}")

    if result.changed:
        invalidate_home_bootstrap_snapshot_best_effort(
            organization_id=organization_id,
            clear_global_tracker_rows_cache=tracker_read_support._clear_global_tracker_rows_cache,
            get_home_bootstrap_snapshot_repository=get_home_bootstrap_snapshot_repository,
            logger=logging.getLogger(__name__),
        )
        source_run_id = tracker_support._to_uuid_or_none(
            result.entry.get("source_tracker_run_id") or result.entry.get("source_run_id")
        )
        with measure_stage(
            "tracker_entry_patch.build_manual_change_event",
            request_id=request_id,
            entry_id=str(entry_id),
            field_name=payload.field_name,
        ):
            event = build_tracker_change_event(
                TrackerEventBuildInput(
                    organization_id=organization_id,
                    tracker_entry_id=entry_id,
                    event_type="manual_updated",
                    field_name=payload.field_name,
                    old_value=str(before_entry.get(payload.field_name) or ""),
                    new_value=str(result.entry.get(payload.field_name) or ""),
                    source_kind="manual",
                    source_run_id=source_run_id,
                    source_ref=str((result.audit_log or {}).get("id") or "").strip(),
                    reason_code=str(payload.change_source or "").strip(),
                )
            )
        if event is not None:
            try:
                with measure_stage(
                    "tracker_entry_patch.append_change_event",
                    request_id=request_id,
                    entry_id=str(entry_id),
                    field_name=payload.field_name,
                ):
                    _get_tracker_change_event_repository().append_events(
                        organization_id=organization_id,
                        events=[event],
                    )
            except TrackerChangeEventRepositoryError as exc:
                _repository_error(str(exc))

    with measure_stage("tracker_entry_patch.snapshot_refresh", request_id=request_id, entry_id=str(entry_id)):
        tracker_read_support._upsert_tracker_entry_snapshots_best_effort(
            organization_id=organization_id,
            rows=[result.entry],
        )
    with measure_stage("tracker_entry_patch.snapshot_hydrate", request_id=request_id, entry_id=str(entry_id)):
        entry_row = tracker_read_support._hydrate_tracker_entry_detail_row(
            organization_id=organization_id,
            row=result.entry,
        )

    return TrackerEntryPatchResponse(
        changed=result.changed,
        entry=tracker_support._to_tracker_entry_model(entry_row),
        audit_log=tracker_support._to_audit_log_model(result.audit_log) if result.audit_log is not None else None,
    )


def _preview_tracker_cleanup(*, source_tracker_run_id: UUID) -> Any:
    from backend.services.tracker_cleanup_backend import preview_tracker_cleanup

    return preview_tracker_cleanup(
        source_tracker_run_id=source_tracker_run_id,
        tracker_repository=_get_tracker_repository(),
        run_repository=_get_run_repository(),
        log_repository=_get_run_log_repository(),
        artifact_repository=_get_artifact_repository(),
    )


def _apply_tracker_cleanup(*, source_tracker_run_id: UUID) -> Any:
    from backend.services.tracker_cleanup_backend import apply_tracker_cleanup

    return apply_tracker_cleanup(
        source_tracker_run_id=source_tracker_run_id,
        tracker_repository=_get_tracker_repository(),
        run_repository=_get_run_repository(),
        log_repository=_get_run_log_repository(),
        artifact_repository=_get_artifact_repository(),
    )


def _build_tracker_contact_resolution_summary(
    *,
    limit: int,
    source_run_id: UUID | None = None,
    source_tracker_run_id: UUID | None = None,
) -> Any:
    from backend.api import app as app_module
    from backend.services.tracker_contact_resolution_backend import build_tracker_contact_resolution_summary

    entries = app_module._load_all_tracker_entries_for_export(
        q="",
        region="",
        exclude_auxiliary_titles=False,
        edited_only=False,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name="",
        section_name="",
    )
    return build_tracker_contact_resolution_summary(
        entries=entries,
        limit=limit,
        load_winner_index_by_run_fn=app_module._load_winner_index_by_run,
        lookup_winner_row_for_entry_fn=app_module._lookup_winner_row_for_entry,
        coerce_uuid_or_none_fn=app_module._coerce_uuid_or_none,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
    )
