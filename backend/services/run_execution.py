from __future__ import annotations

import sys
import threading
import time
from typing import Any

from backend.phase1_defaults import build_phase1_run_row
from backend.phase1_defaults import load_phase1_identity
from backend.perf_runtime import log_task_duration
from backend.repositories import get_artifact_repository
from backend.repositories import get_related_notice_cache_repository
from backend.repositories import get_related_notice_publication_repository
from backend.repositories import get_run_log_repository
from backend.repositories import get_run_repository
from backend.repositories import get_tracker_change_event_repository
from backend.repositories import get_tracker_entry_repository

from .artifact_files import copy_csv_artifact
from .artifact_files import copy_file_artifact
from .artifact_files import resolve_artifact_path
from .artifact_files import write_json_artifact
from .artifact_files import write_tracking_workbook
from .pipeline_stage_outputs import run_export_stage_for_run
from .pipeline_stage_outputs import run_filter_stage_for_run
from .pipeline_stage_outputs import run_rescan_stage_for_run
from .seed_collect import collect_seed_rows_for_run
from .seed_collect import load_seed_rows_for_run
from .seed_collect import resolve_collect_mode
from .seed_collect import synthetic_debug_enabled
from .related_notice_publish_backend import publish_related_notice_snapshot_set_for_run
from .tracker_change_event_logic import build_tracker_change_event
from .tracker_change_event_logic import TrackerEventBuildInput
from .tracker_export_stage import prepare_tracker_export_for_run
from .run_execution_impl import *  # noqa: F403
from .run_execution_impl import _PRECOMPUTE_ACTIVE
from .run_execution_impl import _PRECOMPUTE_ACTIVE_LOCK
from .run_execution_impl import _build_related_notice_added_events
from .run_execution_impl import _build_related_notice_artifact_payload
from .run_execution_impl import _build_related_notice_project_status_patch
from .run_execution_impl import _build_related_notice_project_entry
from .run_execution_impl import _best_effort_update_run
from .run_execution_impl import _cancel_run_if_requested
from .run_execution_impl import _create_artifact_record
from .run_execution_impl import _create_log
from .run_execution_impl import _is_cancel_requested
from .run_execution_impl import _load_existing_related_notice_payload
from .run_execution_impl import _log_error
from .run_execution_impl import _log_info
from .run_execution_impl import _log_warning
from .run_execution_impl import _mark_run_cancelled
from .run_execution_impl import _merge_related_notice_payload
from .run_execution_impl import _merge_run_summary_output
from .run_execution_impl import _related_notice_incremental_recompute_project_keys
from .run_execution_impl import _related_notice_payload_has_project
from .run_execution_impl import _related_notice_payload_project_keys
from .run_execution_impl import _related_notice_precompute_dedup_key
from .run_execution_impl import _related_notice_reuse_snapshot_keys
from .run_execution_impl import _resolve_related_notice_snapshot_set_id
from .run_execution_impl import _should_preserve_terminal_run_status
from .run_execution_impl import _should_skip_related_notice_project_recompute
from .run_execution_impl import _stage_delay_seconds
from .run_execution_impl import _summary_json_preserving_related_notice_state
from .run_execution_impl import _to_storage_path
from .run_execution_impl import _to_uuid_or_none
from .run_execution_impl import _update_related_notice_summary
from .run_execution_impl import _update_tracker_export_parent_summary
from .run_execution_impl import _upsert_related_notice_cache_entry
from .run_execution_impl import _upsert_related_notice_snapshot_project_entry
from .run_execution_impl import build_tracker_seed_entries
from .run_execution_impl import fail_run as _fail_run_impl
from .run_execution_impl import queue_related_notice_precompute_for_run as _queue_related_notice_precompute_for_run_impl
from .run_execution_impl import queue_tracker_export_run_for_parent as _queue_tracker_export_run_for_parent_impl
from .run_execution_impl import safely_execute_project_tracker as _safely_execute_project_tracker_impl
from .run_execution_impl import safely_execute_tracker_export as _safely_execute_tracker_export_impl
from .run_execution_impl import safely_precompute_related_notices_for_run as _safely_precompute_related_notices_for_run_impl
from .run_execution_impl import execute_project_tracker as _execute_project_tracker_impl
from .run_execution_impl import execute_tracker_export as _execute_tracker_export_impl
from .run_execution_impl import precompute_related_notices_for_run as _precompute_related_notices_for_run_impl


def _proxy(name: str):
    def _call(*args: Any, **kwargs: Any):
        return globals()[name](*args, **kwargs)

    return _call


_PUBLIC_IMPL_NAMES = (
    "queue_tracker_export_run_for_parent",
    "queue_related_notice_precompute_for_run",
    "safely_precompute_related_notices_for_run",
    "precompute_related_notices_for_run",
    "execute_project_tracker",
    "execute_tracker_export",
    "fail_run",
    "safely_execute_project_tracker",
    "safely_execute_tracker_export",
    "_create_log",
    "_log_info",
    "_log_warning",
    "_log_error",
    "_best_effort_update_run",
    "_cancel_run_if_requested",
    "_is_cancel_requested",
    "_mark_run_cancelled",
    "_update_related_notice_summary",
    "_merge_run_summary_output",
    "_update_tracker_export_parent_summary",
    "_create_artifact_record",
    "_should_preserve_terminal_run_status",
    "_load_existing_related_notice_payload",
    "_related_notice_payload_has_project",
    "_should_skip_related_notice_project_recompute",
    "_related_notice_incremental_recompute_project_keys",
    "_resolve_related_notice_snapshot_set_id",
    "_upsert_related_notice_cache_entry",
    "_upsert_related_notice_snapshot_project_entry",
    "_related_notice_payload_project_keys",
    "_related_notice_reuse_snapshot_keys",
    "_build_related_notice_project_status_patch",
    "_build_related_notice_artifact_payload",
    "_build_related_notice_added_events",
    "_merge_related_notice_payload",
    "_related_notice_precompute_dedup_key",
    "_stage_delay_seconds",
    "_summary_json_preserving_related_notice_state",
    "_to_storage_path",
    "_to_uuid_or_none",
    "build_tracker_seed_entries",
)

_PROXY_DEPENDENCIES = (
    "get_run_repository",
    "get_artifact_repository",
    "get_run_log_repository",
    "get_tracker_change_event_repository",
    "get_tracker_entry_repository",
    "get_related_notice_cache_repository",
    "get_related_notice_publication_repository",
    "load_phase1_identity",
    "log_task_duration",
    "copy_csv_artifact",
    "copy_file_artifact",
    "resolve_artifact_path",
    "write_json_artifact",
    "write_tracking_workbook",
    "run_filter_stage_for_run",
    "run_rescan_stage_for_run",
    "run_export_stage_for_run",
    "collect_seed_rows_for_run",
    "load_seed_rows_for_run",
    "resolve_collect_mode",
    "synthetic_debug_enabled",
    "publish_related_notice_snapshot_set_for_run",
    "build_tracker_change_event",
    "TrackerEventBuildInput",
    "prepare_tracker_export_for_run",
    "build_phase1_run_row",
)

for _name in _PROXY_DEPENDENCIES:
    globals()[_name] = globals().get(_name)
    setattr(sys.modules[__name__], _name, globals()[_name])

for _name in _PUBLIC_IMPL_NAMES:
    setattr(sys.modules[__name__], _name, getattr(sys.modules["backend.services.run_execution_impl"], _name))

_impl = sys.modules["backend.services.run_execution_impl"]
_impl.threading = threading
_impl.time = time
_impl.sys = sys
_impl.get_run_repository = _proxy("get_run_repository")
_impl.get_artifact_repository = _proxy("get_artifact_repository")
_impl.get_run_log_repository = _proxy("get_run_log_repository")
_impl.get_tracker_change_event_repository = _proxy("get_tracker_change_event_repository")
_impl.get_tracker_entry_repository = _proxy("get_tracker_entry_repository")
_impl.get_related_notice_cache_repository = _proxy("get_related_notice_cache_repository")
_impl.get_related_notice_publication_repository = _proxy("get_related_notice_publication_repository")
_impl.load_phase1_identity = _proxy("load_phase1_identity")
_impl.log_task_duration = _proxy("log_task_duration")
_impl.copy_csv_artifact = _proxy("copy_csv_artifact")
_impl.copy_file_artifact = _proxy("copy_file_artifact")
_impl.resolve_artifact_path = _proxy("resolve_artifact_path")
_impl.write_json_artifact = _proxy("write_json_artifact")
_impl.write_tracking_workbook = _proxy("write_tracking_workbook")
_impl.run_filter_stage_for_run = _proxy("run_filter_stage_for_run")
_impl.run_rescan_stage_for_run = _proxy("run_rescan_stage_for_run")
_impl.run_export_stage_for_run = _proxy("run_export_stage_for_run")
_impl.collect_seed_rows_for_run = _proxy("collect_seed_rows_for_run")
_impl.load_seed_rows_for_run = _proxy("load_seed_rows_for_run")
_impl.resolve_collect_mode = _proxy("resolve_collect_mode")
_impl.synthetic_debug_enabled = _proxy("synthetic_debug_enabled")
_impl.publish_related_notice_snapshot_set_for_run = _proxy("publish_related_notice_snapshot_set_for_run")
_impl.build_tracker_change_event = _proxy("build_tracker_change_event")
_impl.TrackerEventBuildInput = _proxy("TrackerEventBuildInput")
_impl.prepare_tracker_export_for_run = _proxy("prepare_tracker_export_for_run")
_impl.build_phase1_run_row = _proxy("build_phase1_run_row")
_impl._create_log = _proxy("_create_log")
_impl._log_info = _proxy("_log_info")
_impl._log_warning = _proxy("_log_warning")
_impl._log_error = _proxy("_log_error")
_impl._best_effort_update_run = _proxy("_best_effort_update_run")
_impl._cancel_run_if_requested = _proxy("_cancel_run_if_requested")
_impl._is_cancel_requested = _proxy("_is_cancel_requested")
_impl._mark_run_cancelled = _proxy("_mark_run_cancelled")
_impl._update_related_notice_summary = _proxy("_update_related_notice_summary")
_impl._merge_run_summary_output = _proxy("_merge_run_summary_output")
_impl._update_tracker_export_parent_summary = _proxy("_update_tracker_export_parent_summary")
_impl._create_artifact_record = _proxy("_create_artifact_record")
_impl._should_preserve_terminal_run_status = _proxy("_should_preserve_terminal_run_status")
_impl._load_existing_related_notice_payload = _proxy("_load_existing_related_notice_payload")
_impl._related_notice_payload_has_project = _proxy("_related_notice_payload_has_project")
_impl._should_skip_related_notice_project_recompute = _proxy("_should_skip_related_notice_project_recompute")
_impl._related_notice_incremental_recompute_project_keys = _proxy("_related_notice_incremental_recompute_project_keys")
_impl._resolve_related_notice_snapshot_set_id = _proxy("_resolve_related_notice_snapshot_set_id")
_impl._upsert_related_notice_cache_entry = _proxy("_upsert_related_notice_cache_entry")
_impl._upsert_related_notice_snapshot_project_entry = _proxy("_upsert_related_notice_snapshot_project_entry")
_impl._related_notice_payload_project_keys = _proxy("_related_notice_payload_project_keys")
_impl._related_notice_reuse_snapshot_keys = _proxy("_related_notice_reuse_snapshot_keys")
_impl._build_related_notice_project_status_patch = _proxy("_build_related_notice_project_status_patch")
_impl._build_related_notice_artifact_payload = _proxy("_build_related_notice_artifact_payload")
_impl._build_related_notice_added_events = _proxy("_build_related_notice_added_events")
_impl._merge_related_notice_payload = _proxy("_merge_related_notice_payload")
_impl._related_notice_precompute_dedup_key = _proxy("_related_notice_precompute_dedup_key")
_impl._stage_delay_seconds = _proxy("_stage_delay_seconds")
_impl._summary_json_preserving_related_notice_state = _proxy("_summary_json_preserving_related_notice_state")
_impl._to_storage_path = _proxy("_to_storage_path")
_impl._to_uuid_or_none = _proxy("_to_uuid_or_none")
_impl.build_tracker_seed_entries = _proxy("build_tracker_seed_entries")
_impl.queue_tracker_export_run_for_parent = _proxy("queue_tracker_export_run_for_parent")
_impl.queue_related_notice_precompute_for_run = _proxy("queue_related_notice_precompute_for_run")
_impl.safely_precompute_related_notices_for_run = _proxy("safely_precompute_related_notices_for_run")
_impl.precompute_related_notices_for_run = _proxy("precompute_related_notices_for_run")
_impl.execute_project_tracker = _proxy("execute_project_tracker")
_impl.execute_tracker_export = _proxy("execute_tracker_export")
_impl.fail_run = _proxy("fail_run")
_impl.safely_execute_project_tracker = _proxy("safely_execute_project_tracker")
_impl.safely_execute_tracker_export = _proxy("safely_execute_tracker_export")


PROJECT_TRACKER_STAGES = _impl.PROJECT_TRACKER_STAGES
TRACKER_EXPORT_STAGES = _impl.TRACKER_EXPORT_STAGES
RELATED_NOTICE_ARTIFACT_TYPE = _impl.RELATED_NOTICE_ARTIFACT_TYPE
RELATED_NOTICE_ARTIFACT_FILE_NAME = _impl.RELATED_NOTICE_ARTIFACT_FILE_NAME
RELATED_NOTICE_PRECOMPUTE_MAX_PROJECTS = _impl.RELATED_NOTICE_PRECOMPUTE_MAX_PROJECTS
RELATED_NOTICE_ALGORITHM_VERSION = _impl.RELATED_NOTICE_ALGORITHM_VERSION
RELATED_NOTICE_PRECOMPUTE_ACTIVE_STALE_SEC = _impl.RELATED_NOTICE_PRECOMPUTE_ACTIVE_STALE_SEC
TRACKER_EVENT_FIELDS = _impl.TRACKER_EVENT_FIELDS


def queue_tracker_export_run_for_parent(parent_run_id, *, force_new: bool = False):  # type: ignore[no-untyped-def]
    return _queue_tracker_export_run_for_parent_impl(parent_run_id, force_new=force_new)


def queue_related_notice_precompute_for_run(  # type: ignore[no-untyped-def]
    run_id,
    *,
    project_key: str = "",
    backfill_remaining: bool = True,
    force_recompute: bool = False,
    snapshot_set_id: str = "",
):
    return _queue_related_notice_precompute_for_run_impl(
        run_id,
        project_key=project_key,
        backfill_remaining=backfill_remaining,
        force_recompute=force_recompute,
        snapshot_set_id=snapshot_set_id,
    )


def safely_precompute_related_notices_for_run(  # type: ignore[no-untyped-def]
    run_id,
    *,
    project_key: str = "",
    backfill_remaining: bool = True,
    force_recompute: bool = False,
    snapshot_set_id: str = "",
):
    return _safely_precompute_related_notices_for_run_impl(
        run_id,
        project_key=project_key,
        backfill_remaining=backfill_remaining,
        force_recompute=force_recompute,
        snapshot_set_id=snapshot_set_id,
    )


def precompute_related_notices_for_run(  # type: ignore[no-untyped-def]
    run_id,
    *,
    project_key: str = "",
    backfill_remaining: bool = True,
    force_recompute: bool = False,
    snapshot_set_id: str = "",
):
    return _precompute_related_notices_for_run_impl(
        run_id,
        project_key=project_key,
        backfill_remaining=backfill_remaining,
        force_recompute=force_recompute,
        snapshot_set_id=snapshot_set_id,
    )


def execute_project_tracker(run_id):  # type: ignore[no-untyped-def]
    return _execute_project_tracker_impl(run_id)


def execute_tracker_export(parent_run_id, child_run_id):  # type: ignore[no-untyped-def]
    return _execute_tracker_export_impl(parent_run_id, child_run_id)


def fail_run(run_id, message: str):  # type: ignore[no-untyped-def]
    return _fail_run_impl(run_id, message)


def safely_execute_project_tracker(run_id):  # type: ignore[no-untyped-def]
    return _safely_execute_project_tracker_impl(run_id)


def safely_execute_tracker_export(parent_run_id, child_run_id):  # type: ignore[no-untyped-def]
    return _safely_execute_tracker_export_impl(parent_run_id, child_run_id)


__all__ = [name for name in dir(_impl) if not name.startswith("__")]
