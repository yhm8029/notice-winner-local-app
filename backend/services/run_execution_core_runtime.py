from __future__ import annotations

import json
import sys
import time
from typing import Any
from uuid import UUID

from backend.phase1_defaults import build_phase1_run_row
from backend.phase1_defaults import load_phase1_identity
from backend.phase1_defaults import TRACKER_EXPORT_RUN_TYPE
from backend.perf_runtime import log_task_duration
from backend.repositories import ArtifactRepositoryError
from backend.repositories import get_artifact_repository
from backend.repositories import get_related_notice_cache_repository
from backend.repositories import get_related_notice_publication_repository
from backend.repositories import get_run_log_repository
from backend.repositories import RelatedNoticeCacheRepositoryError
from backend.repositories import RunRepositoryError
from backend.repositories import TrackerChangeEventRepositoryError
from backend.repositories import TrackerEntryRepositoryError
from backend.repositories import get_run_repository
from backend.repositories import get_tracker_change_event_repository
from backend.repositories import get_tracker_entry_repository
from .artifact_files import copy_csv_artifact
from .artifact_files import copy_file_artifact
from .artifact_files import resolve_artifact_path
from .artifact_files import XLSX_MIME_TYPE
from .pipeline_stage_outputs import run_filter_stage_for_run
from .pipeline_stage_outputs import run_export_stage_for_run
from .pipeline_stage_outputs import run_rescan_stage_for_run
from . import run_execution_project_tracker as _run_execution_project_tracker_runtime
from . import run_execution_related_notice as _run_execution_related_notice_builder
from . import run_execution_tracker_export as _run_execution_tracker_export_runtime
from . import run_execution_lifecycle_runtime as _run_execution_lifecycle_runtime
from .run_execution_related_notice_runtime import build_related_notice_project_entry as _build_related_notice_project_entry_impl
from .run_execution_related_notice_runtime import build_related_notice_project_status_patch as _build_related_notice_project_status_patch_impl
from .run_execution_related_notice_runtime import is_missing_related_notice_cache_table_error as _is_missing_related_notice_cache_table_error_impl
from .run_execution_related_notice_runtime import load_existing_related_notice_payload as _load_existing_related_notice_payload_impl
from .run_execution_related_notice_runtime import merge_related_notice_payload as _merge_related_notice_payload_impl
from .run_execution_related_notice_runtime import related_notice_incremental_recompute_project_keys as _related_notice_incremental_recompute_project_keys_impl
from .run_execution_related_notice_runtime import related_notice_payload_has_project as _related_notice_payload_has_project_impl
from .run_execution_related_notice_runtime import related_notice_payload_project_keys as _related_notice_payload_project_keys_impl
from .run_execution_related_notice_runtime import related_notice_precompute_dedup_key as _related_notice_precompute_dedup_key_impl
from .run_execution_related_notice_precompute_runtime_support import resolve_existing_related_notice_artifact_state as _resolve_existing_related_notice_artifact_state_impl
from .run_execution_related_notice_precompute_runtime_support import validate_related_notice_precompute_run as _validate_related_notice_precompute_run_impl
from .run_execution_related_notice_precompute_runtime_support import write_related_notice_precompute_artifact as _write_related_notice_precompute_artifact_impl
from .run_execution_related_notice_runtime import seed_fallback_related_notice_items as _seed_fallback_related_notice_items_impl
from .run_execution_related_notice_runtime import should_skip_related_notice_project_recompute as _should_skip_related_notice_project_recompute_impl
from .run_execution_related_notice_cache_runtime import related_notice_reuse_snapshot_keys as _related_notice_reuse_snapshot_keys_impl
from .run_execution_related_notice_cache_runtime import resolve_related_notice_snapshot_set_id as _resolve_related_notice_snapshot_set_id_impl
from .run_execution_related_notice_cache_runtime import reusable_related_notice_project_entry as _reusable_related_notice_project_entry_impl
from .run_execution_related_notice_cache_runtime import upsert_related_notice_cache_entry as _upsert_related_notice_cache_entry_impl
from .run_execution_core_runtime_support import _build_run_execution_runtime_deps as _build_run_execution_runtime_deps_impl
from .run_execution_core_runtime_support import _PRECOMPUTE_ACTIVE
from .run_execution_core_runtime_support import _PRECOMPUTE_ACTIVE_LOCK
from .run_execution_core_runtime_support import RELATED_NOTICE_PRECOMPUTE_ACTIVE_STALE_SEC
from .run_execution_core_runtime_support import queue_related_notice_precompute_for_run as _queue_related_notice_precompute_for_run_impl
from .run_execution_core_runtime_support import related_notice_precompute_dedup_key as _related_notice_precompute_dedup_key_support_impl
from .run_execution_core_runtime_support import safely_precompute_related_notices_for_run as _safely_precompute_related_notices_for_run_impl
from .run_execution_core_runtime_support import _stage_delay_seconds
from .run_execution_core_runtime_support import _to_storage_path
from .run_execution_core_runtime_support import _to_uuid_or_none
from .run_execution_core_runtime_support import _utcnow
from .run_execution_seed_runtime import build_tracker_seed_entries as _build_tracker_seed_entries_impl
from .run_execution_support_runtime import create_artifact_record as _create_artifact_record_impl
from .run_execution_support_runtime import create_log as _create_log_impl
from .run_execution_support_runtime import merge_run_summary_output as _merge_run_summary_output_impl
from .run_execution_support_runtime import update_related_notice_summary as _update_related_notice_summary_impl
from .run_execution_tracker_queue_runtime import queue_tracker_export_run_for_parent as _queue_tracker_export_run_for_parent_impl
from .seed_collect import collect_seed_rows_for_run
from .seed_collect import load_seed_rows_for_run
from .seed_collect import resolve_collect_mode
from .seed_collect import synthetic_debug_enabled
from .related_notice_publish_backend import publish_related_notice_snapshot_set_for_run
from .related_notice_progress import finish_related_notice_progress
from .related_notice_query_runtime import RELATED_NOTICE_ALGORITHM_VERSION
from .related_notice_response_cache import clear_related_notice_response_cache
from .related_notice_progress import update_related_notice_progress
from .tracker_change_event_logic import build_tracker_change_event
from .tracker_change_event_logic import TrackerEventBuildInput
from .tracker_export_stage import prepare_tracker_export_for_run
from .artifact_files import write_tracking_workbook

PROJECT_TRACKER_STAGES = ("collect", "filter", "rescan", "export", "finalize")
TRACKER_EXPORT_STAGES = ("tracker_export", "finalize")
RELATED_NOTICE_ARTIFACT_TYPE = "related_notices_json"
RELATED_NOTICE_ARTIFACT_FILE_NAME = "project_tracker_related_notices.json"
RELATED_NOTICE_PRECOMPUTE_MAX_PROJECTS = 5

TRACKER_EVENT_FIELDS = ("gross_area_scale", "construction_cost", "demand_contact")


def _build_run_execution_runtime_deps() -> Any: return _build_run_execution_runtime_deps_impl(globals())


def queue_tracker_export_run_for_parent(parent_run_id: UUID, *, force_new: bool = False) -> tuple[dict[str, Any], bool]:
    return _queue_tracker_export_run_for_parent_impl(
        get_run_repository_fn=get_run_repository, get_artifact_repository_fn=get_artifact_repository, build_phase1_run_row_fn=build_phase1_run_row,
        safely_execute_tracker_export_fn=safely_execute_tracker_export, run_repository_error_cls=RunRepositoryError, track_export_run_type=TRACKER_EXPORT_RUN_TYPE,
        parent_run_id=parent_run_id, force_new=force_new,
    )


def _related_notice_precompute_dedup_key(
    run_id: UUID, *, project_key: str = "", backfill_remaining: bool = True, force_recompute: bool = False, snapshot_set_id: str = "",
) -> str:
    return _related_notice_precompute_dedup_key_support_impl(run_id, project_key=project_key, backfill_remaining=backfill_remaining, force_recompute=force_recompute, snapshot_set_id=snapshot_set_id)


def queue_related_notice_precompute_for_run(
    run_id: UUID,
    *,
    project_key: str = "",
    backfill_remaining: bool = True,
    force_recompute: bool = False,
    snapshot_set_id: str = "",
) -> bool:
    return _queue_related_notice_precompute_for_run_impl(
        run_id,
        project_key=project_key,
        backfill_remaining=backfill_remaining,
        force_recompute=force_recompute,
        snapshot_set_id=snapshot_set_id,
        safely_precompute_related_notices_for_run_fn=safely_precompute_related_notices_for_run,
    )


def safely_precompute_related_notices_for_run(
    run_id: UUID,
    *,
    project_key: str = "",
    backfill_remaining: bool = True,
    force_recompute: bool = False,
    snapshot_set_id: str = "",
) -> None:
    return _safely_precompute_related_notices_for_run_impl(
        run_id,
        project_key=project_key,
        backfill_remaining=backfill_remaining,
        force_recompute=force_recompute,
        snapshot_set_id=snapshot_set_id,
        precompute_related_notices_for_run_fn=precompute_related_notices_for_run,
        log_task_duration_fn=log_task_duration,
    )


def _load_existing_related_notice_payload(storage_path: str) -> dict[str, Any] | None:
    return _load_existing_related_notice_payload_impl(
        storage_path,
        resolve_artifact_path_fn=resolve_artifact_path,
    )


def _related_notice_payload_has_project(payload: dict[str, Any] | None, project_key: str) -> bool:
    return _related_notice_payload_has_project_impl(
        payload,
        project_key,
        algorithm_version=RELATED_NOTICE_ALGORITHM_VERSION,
    )


def _should_skip_related_notice_project_recompute(
    *,
    existing_payload: dict[str, Any] | None,
    project_key: str,
    force_recompute: bool,
) -> bool:
    return _should_skip_related_notice_project_recompute_impl(
        existing_payload=existing_payload,
        project_key=project_key,
        force_recompute=force_recompute,
        related_notice_payload_has_project_fn=_related_notice_payload_has_project,
    )


def _is_missing_related_notice_cache_table_error(message: str) -> bool:
    return _is_missing_related_notice_cache_table_error_impl(message)


def _upsert_related_notice_cache_entry(
    *,
    project_entry: dict[str, Any],
    status: str,
    source_run_id: UUID,
    error: str = "",
    snapshot_set_id: str = "",
) -> None:
    try:
        result = _upsert_related_notice_cache_entry_impl(
            get_related_notice_cache_repository_fn=get_related_notice_cache_repository,
            load_phase1_identity_fn=load_phase1_identity,
            project_entry=project_entry,
            status=status,
            source_run_id=source_run_id,
            error=error,
            snapshot_set_id=snapshot_set_id,
        )
        if status == "success":
            clear_related_notice_response_cache()
        return result
    except RelatedNoticeCacheRepositoryError as exc:
        if not _is_missing_related_notice_cache_table_error(str(exc)):
            raise


def _related_notice_incremental_recompute_project_keys(payload: dict[str, Any] | None) -> list[str]:
    return _related_notice_incremental_recompute_project_keys_impl(payload)


def _queue_related_notice_incremental_recompute(
    *,
    run_id: UUID,
    payload: dict[str, Any] | None,
    published_snapshot_set_id: str,
) -> None:
    snapshot_key = str(published_snapshot_set_id or "").strip()
    if not snapshot_key:
        return
    for project_key in _related_notice_incremental_recompute_project_keys(payload):
        queue_related_notice_precompute_for_run(
            run_id,
            project_key=project_key,
            backfill_remaining=False,
            force_recompute=True,
            snapshot_set_id=snapshot_key,
        )


def _resolve_related_notice_snapshot_set_id(*, run_id: UUID, snapshot_set_id: str) -> str:
    return _resolve_related_notice_snapshot_set_id_impl(
        run_repository=get_run_repository(),
        run_id=run_id,
        snapshot_set_id=snapshot_set_id,
    )


def _upsert_related_notice_snapshot_project_entry(
    *,
    run_id: UUID,
    project_entry: dict[str, Any],
    snapshot_set_id: str,
) -> None:
    snapshot_key = _resolve_related_notice_snapshot_set_id(run_id=run_id, snapshot_set_id=snapshot_set_id)
    if not snapshot_key:
        return
    _upsert_related_notice_cache_entry(
        project_entry=project_entry,
        status="success",
        source_run_id=run_id,
        snapshot_set_id=snapshot_key,
    )


def _related_notice_reuse_snapshot_keys() -> list[str]:
    return _related_notice_reuse_snapshot_keys_impl(
        load_phase1_identity_fn=load_phase1_identity,
        get_related_notice_publication_repository_fn=get_related_notice_publication_repository,
    )


def _reusable_related_notice_project_entry(
    *,
    project: dict[str, Any],
    run_id: UUID,
    reuse_snapshot_keys: list[str],
) -> dict[str, Any] | None:
    return _reusable_related_notice_project_entry_impl(
        get_related_notice_cache_repository_fn=get_related_notice_cache_repository,
        is_missing_related_notice_cache_table_error_fn=_is_missing_related_notice_cache_table_error,
        project=project,
        run_id=run_id,
        reuse_snapshot_keys=reuse_snapshot_keys,
        related_notice_algorithm_version=RELATED_NOTICE_ALGORITHM_VERSION,
    )


def _seed_fallback_related_notice_items(
    *,
    project: dict[str, Any],
    seed_rows: list[dict[str, Any]],
    score_related_notice_match_fn: Any,
    project_search_name_fn: Any,
    dedupe_related_notice_payload_items_fn: Any,
) -> list[dict[str, Any]]:
    return _seed_fallback_related_notice_items_impl(
        project=project,
        seed_rows=seed_rows,
        score_related_notice_match_fn=score_related_notice_match_fn,
        project_search_name_fn=project_search_name_fn,
        dedupe_related_notice_payload_items_fn=dedupe_related_notice_payload_items_fn,
    )


def _build_related_notice_project_entry(
    *,
    project: dict[str, Any],
    run_id: UUID,
    items: list[dict[str, Any]],
    source: str,
    error_message: str,
    search_debug: dict[str, Any],
) -> dict[str, Any]:
    return _build_related_notice_project_entry_impl(
        project=project,
        run_id=run_id,
        items=items,
        source=source,
        error_message=error_message,
        search_debug=search_debug,
        algorithm_version=RELATED_NOTICE_ALGORITHM_VERSION,
    )


def _merge_related_notice_payload(
    existing_payload: dict[str, Any] | None,
    new_payload: dict[str, Any],
) -> dict[str, Any]:
    return _merge_related_notice_payload_impl(
        existing_payload,
        new_payload,
        utcnow_fn=_utcnow,
    )


def _related_notice_payload_project_keys(payload: dict[str, Any] | None) -> list[str]:
    return _related_notice_payload_project_keys_impl(payload)


def _build_related_notice_project_status_patch(
    project_keys: list[str] | set[str] | tuple[str, ...],
    *,
    status: str,
    error: str = "",
) -> dict[str, dict[str, str]]:
    return _build_related_notice_project_status_patch_impl(
        project_keys,
        status=status,
        error=error,
        utcnow_fn=_utcnow,
    )


def precompute_related_notices_for_run(
    run_id: UUID,
    *,
    project_key: str = "",
    backfill_remaining: bool = True,
    force_recompute: bool = False,
    snapshot_set_id: str = "",
) -> None:
    run_repository = get_run_repository()
    artifact_repository = get_artifact_repository()
    run = _validate_related_notice_precompute_run_impl(
        run_id=run_id,
        run=run_repository.get_run(run_id),
        run_repository_error_cls=RunRepositoryError,
    )

    try:
        artifacts = artifact_repository.list_artifacts(run_id=run_id)
    except ArtifactRepositoryError as exc:
        raise RunRepositoryError(str(exc)) from exc
    existing_related_artifact, existing_payload, should_skip = _resolve_existing_related_notice_artifact_state_impl(
        artifacts=artifacts,
        related_notice_artifact_type=RELATED_NOTICE_ARTIFACT_TYPE,
        project_key=project_key,
        force_recompute=force_recompute,
        load_existing_related_notice_payload_fn=_load_existing_related_notice_payload,
        should_skip_related_notice_project_recompute_fn=_should_skip_related_notice_project_recompute,
    )
    if should_skip:
        _update_related_notice_summary(
            run_id=run_id,
            summary_patch={
                "related_notice_precompute_status": "success",
                "related_notice_project_statuses": _build_related_notice_project_status_patch(
                    [project_key] if project_key else [],
                    status="success",
                ),
            },
        )
        return

    params = dict(run.get("params_json") or {})
    seed_rows = load_seed_rows_for_run(run_id)
    _update_related_notice_summary(
        run_id=run_id,
        summary_patch={
            "related_notice_precompute_status": "running",
            "related_notice_project_statuses": _build_related_notice_project_status_patch(
                [project_key] if project_key else [],
                status="running",
            ),
        },
    )
    if project_key:
        _upsert_related_notice_cache_entry(
            project_entry={
                "project_key": project_key,
                "project_name": "",
                "project_search_name": "",
                "issuer_name": "",
                "source": "",
                "algorithm_version": RELATED_NOTICE_ALGORITHM_VERSION,
                "items": [],
            },
            status="running",
            source_run_id=run_id,
        )
    _log_info(
        run_id=run_id,
        stage="finalize",
        message="related notice precompute started",
        meta={"seed_rows": len(seed_rows)},
    )

    try:
        related_notice_payload = _build_related_notice_artifact_payload(
            run_id=run_id,
            params=params,
            seed_rows=seed_rows,
            target_project_keys={project_key} if project_key else None,
            limit_projects=bool(project_key),
            prefer_seed_fallback_on_cache_miss=not bool(project_key),
        )
        if project_key:
            related_notice_payload = _merge_related_notice_payload(existing_payload, related_notice_payload)
        payload_project_keys = [
            str(item.get("project_key") or "").strip()
            for item in (related_notice_payload.get("projects") or [])
            if str(item.get("project_key") or "").strip()
        ]
        for project_entry in (related_notice_payload.get("projects") or []):
            _upsert_related_notice_cache_entry(
                project_entry=dict(project_entry),
                status="success",
                source_run_id=run_id,
            )
        if project_key:
            updated_project_entry = next(
                (
                    dict(item)
                    for item in (related_notice_payload.get("projects") or [])
                    if str(item.get("project_key") or "").strip() == project_key
                ),
                None,
            )
            if updated_project_entry is not None:
                _upsert_related_notice_snapshot_project_entry(
                    run_id=run_id,
                    project_entry=updated_project_entry,
                    snapshot_set_id=snapshot_set_id,
                )
        _related_notice_artifact, _payload_project_keys = _write_related_notice_precompute_artifact_impl(
            run_id=run_id,
            artifact_repository=artifact_repository,
            existing_related_artifact=existing_related_artifact,
            related_notice_payload=related_notice_payload,
            related_notice_artifact_file_name=RELATED_NOTICE_ARTIFACT_FILE_NAME,
            related_notice_artifact_type=RELATED_NOTICE_ARTIFACT_TYPE,
            write_json_artifact_fn=write_json_artifact,
            create_artifact_record_fn=_create_artifact_record,
            update_related_notice_summary_fn=_update_related_notice_summary,
            build_related_notice_project_status_patch_fn=_build_related_notice_project_status_patch,
            log_info_fn=_log_info,
        )
        if not project_key:
            try:
                published_snapshot = publish_related_notice_snapshot_set_for_run(
                    run_id=run_id,
                    related_notice_payload=related_notice_payload,
                )
                published_snapshot_set_id = str(
                    published_snapshot.get("published_snapshot_set_id") or ""
                ).strip()
                _update_related_notice_summary(
                    run_id=run_id,
                    summary_patch={
                        "related_notice_snapshot_set_id": published_snapshot_set_id,
                    },
                )
                _queue_related_notice_incremental_recompute(
                    run_id=run_id,
                    payload=related_notice_payload,
                    published_snapshot_set_id=published_snapshot_set_id,
                )
            except Exception as exc:
                _log_warning(
                    run_id=run_id,
                    stage="finalize",
                    message="related notice publish failed",
                    meta={"error": str(exc)},
                )
        if project_key and backfill_remaining:
            all_project_payload = _build_related_notice_artifact_payload(
                run_id=run_id,
                params=params,
                seed_rows=seed_rows,
                target_project_keys=None,
                limit_projects=False,
                prefer_seed_fallback_on_cache_miss=True,
            )
            existing_keys = set(_related_notice_payload_project_keys(related_notice_payload))
            remaining_keys = [
                str(item.get("project_key") or "").strip()
                for item in (all_project_payload.get("projects") or [])
                if str(item.get("project_key") or "").strip() and str(item.get("project_key") or "").strip() not in existing_keys
            ]
            if remaining_keys:
                _update_related_notice_summary(
                    run_id=run_id,
                    summary_patch={
                        "related_notice_project_statuses": _build_related_notice_project_status_patch(
                            remaining_keys,
                            status="queued",
                        ),
                    },
                )
                for remaining_key in remaining_keys:
                    try:
                        precompute_related_notices_for_run(
                            run_id,
                            project_key=remaining_key,
                            backfill_remaining=False,
                        )
                    except Exception:
                        continue
    except Exception as exc:
        if project_key:
            _upsert_related_notice_cache_entry(
                project_entry={
                    "project_key": project_key,
                    "project_name": "",
                    "project_search_name": "",
                    "issuer_name": "",
                    "source": "",
                    "algorithm_version": RELATED_NOTICE_ALGORITHM_VERSION,
                    "items": [],
                },
                status="failed",
                source_run_id=run_id,
                error=str(exc),
            )
        _update_related_notice_summary(
            run_id=run_id,
            summary_patch={
                "related_notice_precomputed": False,
                "related_notice_precompute_status": "failed",
                "related_notice_precompute_error": str(exc),
                "related_notice_project_statuses": _build_related_notice_project_status_patch(
                    [project_key] if project_key else [],
                    status="failed",
                    error=str(exc),
                ),
            },
        )
        _log_warning(
            run_id=run_id,
            stage="finalize",
            message="related notice precompute failed",
            meta={"error": str(exc)},
        )


def _update_related_notice_summary(*, run_id: UUID, summary_patch: dict[str, Any]) -> None:
    return _update_related_notice_summary_impl(
        run_repository=get_run_repository(),
        run_id=run_id,
        summary_patch=summary_patch,
    )


def _merge_run_summary_output(*, run_id: UUID, summary_patch: dict[str, Any], context: str) -> None:
    return _merge_run_summary_output_impl(
        run_repository=get_run_repository(),
        best_effort_update_run_fn=_best_effort_update_run,
        run_id=run_id,
        summary_patch=summary_patch,
        context=context,
    )


def _update_tracker_export_parent_summary(*, parent_run_id: UUID, summary_patch: dict[str, Any], context: str) -> None:
    _merge_run_summary_output(run_id=parent_run_id, summary_patch=summary_patch, context=context)


def execute_project_tracker(run_id: UUID) -> None:
    return _run_execution_project_tracker_runtime.execute_project_tracker(
        _build_run_execution_runtime_deps(),
        run_id,
    )


def _build_related_notice_added_events(
    *,
    organization_id: UUID,
    source_run_id: UUID,
    upserted_entries: list[dict[str, Any]],
    before_entries_by_key: dict[str, dict[str, Any] | None],
) -> list[dict[str, Any]]:
    return _run_execution_tracker_export_runtime.build_related_notice_added_events(
        _build_run_execution_runtime_deps(),
        organization_id=organization_id,
        source_run_id=source_run_id,
        upserted_entries=upserted_entries,
        before_entries_by_key=before_entries_by_key,
    )


def execute_tracker_export(parent_run_id: UUID, child_run_id: UUID) -> None:
    return _run_execution_tracker_export_runtime.execute_tracker_export(
        _build_run_execution_runtime_deps(),
        parent_run_id,
        child_run_id,
    )
def fail_run(run_id: UUID, message: str) -> None:
    return _run_execution_lifecycle_runtime.fail_run(
        _build_run_execution_runtime_deps(),
        run_id,
        message,
    )


def safely_execute_project_tracker(run_id: UUID) -> None:
    return _run_execution_lifecycle_runtime.safely_execute_project_tracker(
        _build_run_execution_runtime_deps(),
        run_id,
    )


def safely_execute_tracker_export(parent_run_id: UUID, child_run_id: UUID) -> None:
    return _run_execution_lifecycle_runtime.safely_execute_tracker_export(
        _build_run_execution_runtime_deps(),
        parent_run_id,
        child_run_id,
    )


def _should_preserve_terminal_run_status(run_id: UUID, exc: Exception) -> bool:
    return _run_execution_lifecycle_runtime.should_preserve_terminal_run_status(
        run_repository=get_run_repository(),
        sys_module=sys,
        run_id=run_id,
        exc=exc,
    )


def build_tracker_seed_entries(
    *,
    run_id: UUID,
    params: dict[str, Any],
    seed_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    return _build_tracker_seed_entries_impl(
        run_id=run_id,
        params=params,
        seed_rows=seed_rows,
    )


def _build_related_notice_artifact_payload(
    *,
    run_id: UUID,
    params: dict[str, Any],
    seed_rows: list[dict[str, Any]],
    target_project_keys: set[str] | None = None,
    limit_projects: bool = True,
    prefer_seed_fallback_on_cache_miss: bool = False,
) -> dict[str, Any]:
    return _run_execution_related_notice_builder.build_related_notice_artifact_payload(
        _build_run_execution_runtime_deps(),
        run_id=run_id,
        params=params,
        seed_rows=seed_rows,
        target_project_keys=target_project_keys,
        limit_projects=limit_projects,
        prefer_seed_fallback_on_cache_miss=prefer_seed_fallback_on_cache_miss,
    )


def _create_artifact_record(
    *,
    artifact_repository: Any,
    run_id: UUID,
    artifact_type: str,
    written_artifact: Any,
    meta: dict[str, Any],
) -> None:
    return _create_artifact_record_impl(
        load_phase1_identity_fn=load_phase1_identity,
        artifact_repository=artifact_repository,
        run_id=run_id,
        artifact_type=artifact_type,
        written_artifact=written_artifact,
        meta=meta,
    )


def _cancel_run_if_requested(*, run_id: UUID, current_stage: str) -> bool:
    return _run_execution_lifecycle_runtime.cancel_run_if_requested(
        _build_run_execution_runtime_deps(),
        run_id=run_id,
        current_stage=current_stage,
    )


def _is_cancel_requested(run_id: UUID) -> bool:
    return _run_execution_lifecycle_runtime.is_cancel_requested(
        run_repository=get_run_repository(),
        run_id=run_id,
    )


def _mark_run_cancelled(run_id: UUID) -> None:
    return _run_execution_lifecycle_runtime.mark_run_cancelled(
        _build_run_execution_runtime_deps(),
        run_id,
    )


def _best_effort_update_run(run_id: UUID, fields: dict[str, Any], *, context: str) -> None:
    return _run_execution_lifecycle_runtime.best_effort_update_run(
        run_repository=get_run_repository(),
        sys_module=sys,
        run_id=run_id,
        fields=fields,
        context=context,
    )


def _summary_json_preserving_related_notice_state(run_id: UUID, summary_json: dict[str, Any]) -> dict[str, Any]:
    return _run_execution_lifecycle_runtime.summary_json_preserving_related_notice_state(
        run_repository=get_run_repository(),
        run_id=run_id,
        summary_json=summary_json,
    )


def _log_info(*, run_id: UUID, stage: str, message: str, meta: dict[str, Any]) -> None:
    _create_log(run_id=run_id, level="info", stage=stage, message=message, meta=meta)


def _log_warning(*, run_id: UUID, stage: str, message: str, meta: dict[str, Any]) -> None:
    _create_log(run_id=run_id, level="warning", stage=stage, message=message, meta=meta)


def _log_error(*, run_id: UUID, stage: str, message: str, meta: dict[str, Any]) -> None:
    _create_log(run_id=run_id, level="error", stage=stage, message=message, meta=meta)


def _create_log(*, run_id: UUID, level: str, stage: str, message: str, meta: dict[str, Any]) -> None:
    return _create_log_impl(
        load_phase1_identity_fn=load_phase1_identity,
        get_run_log_repository_fn=get_run_log_repository,
        lifecycle_runtime=_run_execution_lifecycle_runtime,
        sys_module=sys,
        run_id=run_id,
        level=level,
        stage=stage,
        message=message,
        meta=meta,
    )
