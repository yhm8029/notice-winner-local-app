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
from backend.api.routers import related_notice_read_support
from backend.api.support.app_repository_support import _get_related_notice_cache_repository
from backend.api.support.app_pure_helpers import is_related_notice_precompute_stale
from backend.api.support.app_pure_helpers import json_safe_copy
from backend.api.support.run_support import _is_project_tracker_run_type
from backend.api.support.run_support import _load_run_execution_helpers
from backend.api.support.run_support import _run_visible_in_operational_views
from backend.api.support.run_support import _to_run_create_response
from backend.services.related_notice_query_runtime import _build_related_notice_primary_queries
from backend.services.related_notice_query_runtime import _build_related_notice_primary_scopes
from backend.services.related_notice_query_runtime import RELATED_NOTICE_ALGORITHM_VERSION
from backend.services.related_notice_query_runtime import _is_missing_related_notice_cache_table_error
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


def _is_related_notice_precompute_stale(
    run_row: dict[str, Any],
    precompute_status: str,
    *,
    updated_at: Any = None,
) -> bool:
    return is_related_notice_precompute_stale(
        run_row,
        precompute_status,
        updated_at=updated_at,
    )


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
    data_version: str = "",
) -> str:
    return json.dumps(
        {
            "format": "xlsx",
            "workbook_layout_version": TRACKER_EXPORT_WORKBOOK_LAYOUT_VERSION,
            "data_version": str(data_version or ""),
            "q": str(q or "").strip(),
            "region": str(region or "").strip(),
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


def _get_published_related_notice_snapshot_set_id() -> str:
    from backend.api import app as app_module

    return related_notice_read_support._get_published_related_notice_snapshot_set_id(
        get_related_notice_publication_repository_fn=app_module._get_related_notice_publication_repository,
    )


def _precomputed_related_notice_items(
    project: dict[str, Any],
    *,
    trace_id: str | None = None,
    project_id: UUID | None = None,
    published_snapshot_set_id: str | None | object = related_notice_read_support._RELATED_NOTICE_PUBLISHED_SNAPSHOT_SET_ID_UNSET,
) -> Any:
    from backend.api import app as app_module

    if published_snapshot_set_id is related_notice_read_support._RELATED_NOTICE_PUBLISHED_SNAPSHOT_SET_ID_UNSET:
        published_snapshot_set_id = app_module._get_published_related_notice_snapshot_set_id()

    return related_notice_read_support._precomputed_related_notice_items(
        project,
        trace_id=trace_id,
        project_id=project_id,
        published_snapshot_set_id=published_snapshot_set_id,
        get_related_notice_cache_repository_fn=app_module._get_related_notice_cache_repository,
        get_artifact_repository_fn=app_module._get_artifact_repository,
        project_source_runs_fn=app_module._project_source_runs,
        load_json_artifact_payload_fn=app_module._load_json_artifact_payload,
        dedupe_related_notice_payload_items_fn=app_module._dedupe_related_notice_payload_items,
        filter_self_related_notice_payload_items_fn=app_module._filter_self_related_notice_payload_items,
        append_related_notice_trace_fn=app_module._append_related_notice_trace,
        repository_error_fn=app_module._repository_error,
        is_missing_related_notice_cache_table_error_fn=app_module._is_missing_related_notice_cache_table_error,
        is_related_notice_payload_entry_precomputed_fn=app_module._is_related_notice_payload_entry_precomputed,
    )


def _related_notice_response_without_live(
    project: dict[str, Any],
    project_id: UUID,
    *,
    trace_id: str | None = None,
) -> Any:
    from backend.api import app as app_module

    cache_repository = app_module._get_related_notice_cache_repository()
    return related_notice_read_support._related_notice_response_without_live(
        project,
        project_id,
        trace_id=trace_id,
        project_source_runs_fn=app_module._project_source_runs,
        get_related_notice_cache_fn=lambda project_key: cache_repository.get_cache(project_key=project_key),
        is_missing_related_notice_cache_table_error_fn=app_module._is_missing_related_notice_cache_table_error,
        repository_error_fn=app_module._repository_error,
        is_related_notice_precompute_stale_fn=app_module._is_related_notice_precompute_stale,
        is_related_notice_payload_entry_precomputed_fn=app_module._is_related_notice_payload_entry_precomputed,
        filter_self_related_notice_payload_items_fn=app_module._filter_self_related_notice_payload_items,
        dedupe_related_notice_payload_items_fn=app_module._dedupe_related_notice_payload_items,
        seed_related_notice_items_fn=app_module._seed_related_notice_items,
        append_related_notice_trace_fn=app_module._append_related_notice_trace,
        get_run_repository_fn=app_module._get_run_repository,
        queue_related_notice_precompute_for_run_fn=app_module._load_related_notice_precompute_helper(),
        upsert_related_notice_cache_fn=lambda row: cache_repository.upsert_cache(row),
        get_related_notice_project_precompute_state_fn=related_notice_read_support._get_related_notice_project_precompute_state,
        related_notice_algorithm_version=RELATED_NOTICE_ALGORITHM_VERSION,
    )


def _list_related_notices_for_project(project_id: UUID, *, force_refresh: bool = False, quick: bool = False) -> Any:
    from backend.api import app as app_module

    return related_notice_read_support._list_related_notices_for_project(
        project_id,
        force_refresh=force_refresh,
        quick=quick,
        get_published_related_notice_snapshot_set_id_fn=app_module._get_published_related_notice_snapshot_set_id,
        append_related_notice_trace_fn=app_module._append_related_notice_trace,
        get_related_notice_response_cache_fn=app_module._get_related_notice_response_cache,
        get_snapshot_project_aggregate_fn=app_module._get_snapshot_project_aggregate,
        get_project_aggregate_fn=app_module._get_project_aggregate,
        get_related_notice_cache_fn=lambda **kwargs: app_module._get_related_notice_cache_repository().get_cache(**kwargs),
        quick_related_notice_search_fn=app_module._quick_related_notice_search,
        precomputed_related_notice_items_fn=app_module._precomputed_related_notice_items,
        set_related_notice_response_cache_fn=app_module._set_related_notice_response_cache,
    )


def _get_related_notice_progress_for_project(project_id: UUID) -> Any:
    from backend.api import app as app_module
    from backend.services.related_notice_progress import get_related_notice_progress

    project = app_module._get_snapshot_project_aggregate(project_id) or app_module._get_project_aggregate(project_id)
    project_key = str(project.get("_project_match_key") or "").strip()
    progress = get_related_notice_progress(project_key=project_key)
    items = list(progress.get("items") or []) if progress else []
    status = str(progress.get("status") or "idle") if progress else "idle"
    message = str(progress.get("message") or "") if progress else ""
    if not progress:
        message = "아직 진행 중인 연관 공고 검색이 없습니다."
    return app_module.RelatedNoticeProgressResponse(
        project_id=project_id,
        project_name=str(progress.get("project_name") or project.get("project_name") or "") if progress else str(project.get("project_name") or ""),
        project_search_name=str(progress.get("project_search_name") or project.get("project_search_name") or "") if progress else str(project.get("project_search_name") or ""),
        project_key=project_key,
        run_id=str(progress.get("run_id") or "") if progress else "",
        status=status,
        message=message,
        item_count=len(items),
        started_at=str(progress.get("started_at") or "") if progress else "",
        updated_at=str(progress.get("updated_at") or "") if progress else "",
        completed_at=str(progress.get("completed_at") or "") if progress else "",
        items=items,
    )


def _force_recompute_related_notices_for_project(project_id: UUID) -> Any:
    from backend.api import app as app_module
    from backend.services.related_notice_progress import start_related_notice_progress

    project = app_module._get_snapshot_project_aggregate(project_id) or app_module._get_project_aggregate(project_id)
    project_key = str(project.get("_project_match_key") or "").strip()
    if not project_key:
        _validation_error("project key is required for related notice recompute")

    source_runs = sorted(
        app_module._project_source_runs(project),
        key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""),
        reverse=True,
    )
    source_run = next(
        (row for row in source_runs if str(row.get("status") or "").strip() == "success"),
        source_runs[0] if source_runs else None,
    )
    if source_run is None:
        _not_found(f"project source run not found for related notice recompute: {project_id}")
    if str(source_run.get("status") or "").strip() != "success":
        _not_found(f"successful project source run not found for related notice recompute: {project_id}")
    try:
        run_id = UUID(str(source_run.get("id") or ""))
    except ValueError:
        _not_found(f"project source run is invalid for related notice recompute: {project_id}")

    published_snapshot_set_id = str(app_module._get_published_related_notice_snapshot_set_id() or "").strip()
    app_module._clear_related_notice_response_cache(project_id)
    start_related_notice_progress(
        project_key=project_key,
        project_name=str(project.get("project_name") or ""),
        project_search_name=str(project.get("project_search_name") or ""),
        run_id=str(run_id),
        status="queued",
        message="후속공고 갱신 요청이 등록되었습니다.",
    )
    queued = True
    cache_status = "queued"
    try:
        cache_repository = app_module._get_related_notice_cache_repository()
        snapshot_key = published_snapshot_set_id or "legacy"
        existing_cache = cache_repository.get_cache(project_key=project_key, snapshot_set_id=snapshot_key)
        existing_status = str((existing_cache or {}).get("status") or "").strip()
        if existing_status in {"queued", "running"}:
            queued = False
            cache_status = existing_status
        else:
            existing_payload = dict((existing_cache or {}).get("payload_json") or {})
            existing_items = list(existing_payload.get("items") or [])
            cache_repository.upsert_cache(
                {
                    "project_key": project_key,
                    "snapshot_set_id": snapshot_key,
                    "project_name": str(project.get("project_name") or ""),
                    "project_search_name": str(project.get("project_search_name") or ""),
                    "issuer_name": str(project.get("issuer_name") or ""),
                    "status": "queued",
                    "source": "refresh_request",
                    "source_run_id": str(run_id),
                    "algorithm_version": int(app_module.RELATED_NOTICE_ALGORITHM_VERSION),
                    "item_count": len(existing_items),
                    "error": "",
                    "payload_json": {
                        **existing_payload,
                        "project_key": project_key,
                        "project_name": str(project.get("project_name") or ""),
                        "project_search_name": str(project.get("project_search_name") or ""),
                        "issuer_name": str(project.get("issuer_name") or ""),
                        "source_run_id": str(run_id),
                        "algorithm_version": int(app_module.RELATED_NOTICE_ALGORITHM_VERSION),
                        "refresh_status": "queued",
                        "data_status": (
                            "ready"
                            if existing_items
                            else "zero_result"
                            if existing_cache is not None and existing_status == "success"
                            else "empty"
                        ),
                    },
                }
            )
        app_module.ensure_related_notice_refresh_worker_started(
            get_related_notice_cache_repository_fn=app_module.get_related_notice_cache_repository,
            safely_precompute_related_notices_for_run_fn=app_module.safely_precompute_related_notices_for_run,
        )
        app_module.wake_related_notice_refresh_worker()
    except Exception as exc:
        _validation_error(f"related notice refresh request failed: {exc}")
    return app_module.RelatedNoticeRecomputeResponse(
        project_id=project_id,
        project_name=str(project.get("project_name") or ""),
        project_search_name=str(project.get("project_search_name") or ""),
        project_key=project_key,
        run_id=str(run_id),
        status=cache_status,
        queued=queued,
        message=(
            "후속공고 갱신 요청이 등록되었습니다."
            if queued
            else "후속공고 갱신이 이미 진행 중입니다."
        ),
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
