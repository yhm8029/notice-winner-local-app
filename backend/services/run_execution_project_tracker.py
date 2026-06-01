from __future__ import annotations

from typing import Any
from uuid import UUID


def execute_project_tracker(deps: Any, run_id: UUID) -> None:
    run_repository = deps.get_run_repository()
    artifact_repository = deps.get_artifact_repository()
    run = run_repository.get_run(run_id)
    if run is None:
        raise deps.RunRepositoryError(f"run not found: {run_id}")

    params = dict(run.get("params_json") or {})
    stage_total = len(deps.PROJECT_TRACKER_STAGES)
    delay_seconds = deps._stage_delay_seconds(params=params, fallback_ms=20)
    started_at = deps._utcnow()
    run_repository.update_run(
        run_id,
        {
            "status": "running",
            "started_at": started_at.isoformat(),
            "progress_stage": deps.PROJECT_TRACKER_STAGES[0],
            "progress_current": 0,
            "progress_total": stage_total,
        },
    )
    deps._log_info(
        run_id=run_id,
        stage=deps.PROJECT_TRACKER_STAGES[0],
        message="project_tracker started",
        meta={"stage_total": stage_total},
    )

    collected_seed_output = None
    filter_output = None
    rescan_output = None
    export_output = None
    requested_collect_mode = deps.resolve_collect_mode(params)
    written_csv = None
    for index, stage in enumerate(deps.PROJECT_TRACKER_STAGES, start=1):
        if deps._cancel_run_if_requested(run_id=run_id, current_stage=stage):
            deps._log_warning(
                run_id=run_id,
                stage=stage,
                message="project_tracker cancelled before stage completion",
                meta={"stage": stage},
            )
            return
        run_repository.update_run(
            run_id,
            {
                "progress_stage": stage,
                "progress_current": index,
                "progress_total": stage_total,
            },
        )
        if stage == "collect":
            deps._log_info(
                run_id=run_id,
                stage=stage,
                message="collect stage started",
                meta={"progress_current": index, "progress_total": stage_total},
            )
            collected_seed_output = deps.collect_seed_rows_for_run(
                run_id=run_id,
                params=params,
                progress_cb=lambda message: deps._log_info(
                    run_id=run_id,
                    stage="collect",
                    message=message,
                    meta={},
                ),
            )
            deps._log_info(
                run_id=run_id,
                stage=stage,
                message="collect stage completed",
                meta={
                    "progress_current": index,
                    "progress_total": stage_total,
                    "seed_rows": len(collected_seed_output.rows),
                    "collect_backend": collected_seed_output.collect_backend,
                    "quota_fallback_used": collected_seed_output.quota_fallback_used,
                    "seed_csv_path": deps._to_storage_path(collected_seed_output.seed_csv_path),
                },
            )
            deps._create_artifact_record(
                artifact_repository=artifact_repository,
                run_id=run_id,
                artifact_type="seed_csv",
                written_artifact=deps.copy_csv_artifact(
                    run_id=run_id,
                    source_path=collected_seed_output.seed_csv_path,
                    artifact_file_name=collected_seed_output.seed_csv_path.name,
                ),
                meta={
                    "rows": len(collected_seed_output.rows),
                    "stage": "collect",
                    "backend": collected_seed_output.collect_backend,
                    "quota_fallback_used": collected_seed_output.quota_fallback_used,
                },
            )
        elif stage == "filter":
            deps._log_info(
                run_id=run_id,
                stage=stage,
                message="filter stage started",
                meta={"progress_current": index, "progress_total": stage_total},
            )
            filter_output = deps.run_filter_stage_for_run(
                run_id=run_id,
                params=params,
                collect_backend=(
                    collected_seed_output.collect_backend if collected_seed_output is not None else "synthetic"
                ),
                progress_cb=lambda message: deps._log_info(
                    run_id=run_id,
                    stage="filter",
                    message=message,
                    meta={},
                ),
                should_stop=lambda: deps._is_cancel_requested(run_id),
            )
            deps._log_info(
                run_id=run_id,
                stage=stage,
                message="filter stage completed",
                meta={
                    "progress_current": index,
                    "progress_total": stage_total,
                    "candidate_rows": filter_output.row_count,
                    "filter_backend": filter_output.stage_backend,
                    "candidate_csv_path": deps._to_storage_path(filter_output.candidate_csv_path),
                },
            )
            deps._create_artifact_record(
                artifact_repository=artifact_repository,
                run_id=run_id,
                artifact_type="candidate_csv",
                written_artifact=deps.copy_csv_artifact(
                    run_id=run_id,
                    source_path=filter_output.candidate_csv_path,
                    artifact_file_name=filter_output.candidate_csv_path.name,
                ),
                meta={
                    "rows": filter_output.row_count,
                    "stage": "filter",
                    "backend": filter_output.stage_backend,
                },
            )
        elif stage == "rescan":
            deps._log_info(
                run_id=run_id,
                stage=stage,
                message="rescan stage started",
                meta={"progress_current": index, "progress_total": stage_total},
            )
            rescan_output = deps.run_rescan_stage_for_run(
                run_id=run_id,
                params=params,
                filter_backend=(filter_output.stage_backend if filter_output is not None else "synthetic"),
                progress_cb=lambda message: deps._log_info(
                    run_id=run_id,
                    stage="rescan",
                    message=message,
                    meta={},
                ),
                should_stop=lambda: deps._is_cancel_requested(run_id),
            )
            deps._log_info(
                run_id=run_id,
                stage=stage,
                message="rescan stage completed",
                meta={
                    "progress_current": index,
                    "progress_total": stage_total,
                    "internal_nav_rows": rescan_output.row_count,
                    "rescan_backend": rescan_output.stage_backend,
                    "internal_nav_csv_path": deps._to_storage_path(rescan_output.internal_nav_csv_path),
                },
            )
            deps._create_artifact_record(
                artifact_repository=artifact_repository,
                run_id=run_id,
                artifact_type="internal_nav_csv",
                written_artifact=deps.copy_csv_artifact(
                    run_id=run_id,
                    source_path=rescan_output.internal_nav_csv_path,
                    artifact_file_name=rescan_output.internal_nav_csv_path.name,
                ),
                meta={
                    "rows": rescan_output.row_count,
                    "stage": "rescan",
                    "backend": rescan_output.stage_backend,
                },
            )
        elif stage == "export":
            deps._log_info(
                run_id=run_id,
                stage=stage,
                message="export stage started",
                meta={"progress_current": index, "progress_total": stage_total},
            )
            export_output = deps.run_export_stage_for_run(
                run_id=run_id,
                params=params,
                rescan_backend=(rescan_output.stage_backend if rescan_output is not None else "synthetic"),
                progress_cb=lambda message: deps._log_info(
                    run_id=run_id,
                    stage="export",
                    message=message,
                    meta={},
                ),
                should_stop=lambda: deps._is_cancel_requested(run_id),
            )
            if deps._cancel_run_if_requested(run_id=run_id, current_stage="export"):
                deps._log_warning(
                    run_id=run_id,
                    stage="export",
                    message="project_tracker cancelled before artifact generation",
                    meta={},
                )
                return
            written_csv = deps.copy_csv_artifact(
                run_id=run_id,
                source_path=export_output.post_collect_csv_path,
            )
            deps._create_artifact_record(
                artifact_repository=artifact_repository,
                run_id=run_id,
                artifact_type="winner_csv",
                written_artifact=written_csv,
                meta={
                    "rows": written_csv.row_count,
                    "stage": "export",
                    "backend": export_output.stage_backend,
                },
            )
            deps._log_info(
                run_id=run_id,
                stage=stage,
                message="export stage completed",
                meta={
                    "progress_current": index,
                    "progress_total": stage_total,
                    "export_backend": export_output.stage_backend,
                    "winner_csv_rows": export_output.row_count,
                    "post_collect_csv_path": deps._to_storage_path(export_output.post_collect_csv_path),
                    "artifact_file_name": written_csv.file_name,
                },
            )
        else:
            deps._log_info(
                run_id=run_id,
                stage=stage,
                message=f"{stage} stage completed",
                meta={"progress_current": index, "progress_total": stage_total},
            )
        if stage != deps.PROJECT_TRACKER_STAGES[-1]:
            deps.time.sleep(delay_seconds)

    if export_output is None or written_csv is None:
        raise RuntimeError("export stage did not produce winner_csv output")
    stage_backends = {
        "collect": collected_seed_output.collect_backend if collected_seed_output is not None else "synthetic",
        "filter": filter_output.stage_backend if filter_output is not None else "synthetic",
        "rescan": rescan_output.stage_backend if rescan_output is not None else "synthetic",
        "export": export_output.stage_backend,
    }
    execution_manifest = {
        "run_id": str(run_id),
        "runtime_profile": "web_native",
        "requested_collect_mode": requested_collect_mode,
        "quota_fallback_used": (
            collected_seed_output.quota_fallback_used if collected_seed_output is not None else False
        ),
        "native_collect_diagnostics": (
            {
                "requested_endpoint_mode": collected_seed_output.diagnostics.requested_endpoint_mode,
                "effective_endpoint_mode": collected_seed_output.diagnostics.effective_endpoint_mode,
                "attempted_endpoints": collected_seed_output.diagnostics.attempted_endpoints,
                "matched_endpoints": collected_seed_output.diagnostics.matched_endpoints,
                "all_scope_retry_used": collected_seed_output.diagnostics.all_scope_retry_used,
                "direct_bid_lookup_used": collected_seed_output.diagnostics.direct_bid_lookup_used,
                "title_broad_retry_used": collected_seed_output.diagnostics.title_broad_retry_used,
            }
            if collected_seed_output is not None and collected_seed_output.diagnostics is not None
            else {}
        ),
        "stage_backends": stage_backends,
        "row_counts": {
            "seed_rows": len(collected_seed_output.rows) if collected_seed_output is not None else 0,
            "candidate_rows": filter_output.row_count if filter_output is not None else 0,
            "internal_nav_rows": rescan_output.row_count if rescan_output is not None else 0,
            "winner_csv_rows": export_output.row_count,
        },
        "paths": {
            "seed_csv_path": (
                deps._to_storage_path(collected_seed_output.seed_csv_path)
                if collected_seed_output is not None
                else ""
            ),
            "candidate_csv_path": (
                deps._to_storage_path(filter_output.candidate_csv_path) if filter_output is not None else ""
            ),
            "internal_nav_csv_path": (
                deps._to_storage_path(rescan_output.internal_nav_csv_path) if rescan_output is not None else ""
            ),
            "post_collect_csv_path": deps._to_storage_path(export_output.post_collect_csv_path),
            "winner_csv_path": written_csv.storage_path,
            "related_notices_path": "",
        },
        "notice_search_backend": export_output.stage_backend,
    }
    execution_manifest_artifact = deps.write_json_artifact(
        run_id=run_id,
        file_name="project_tracker_execution_manifest.json",
        payload=execution_manifest,
    )
    deps._create_artifact_record(
        artifact_repository=artifact_repository,
        run_id=run_id,
        artifact_type="execution_manifest",
        written_artifact=execution_manifest_artifact,
        meta={
            "stage": "finalize",
            "runtime_profile": "web_native",
            "requested_collect_mode": requested_collect_mode,
        },
    )
    summary_json = {
        "output": {
            "runtime_profile": "web_native",
            "requested_collect_mode": requested_collect_mode,
            "collect_backend": stage_backends["collect"],
            "seed_rows": len(collected_seed_output.rows) if collected_seed_output is not None else 0,
            "seed_csv_path": (
                deps._to_storage_path(collected_seed_output.seed_csv_path)
                if collected_seed_output is not None
                else ""
            ),
            "quota_fallback_used": (
                collected_seed_output.quota_fallback_used if collected_seed_output is not None else False
            ),
            "native_collect_diagnostics": execution_manifest["native_collect_diagnostics"],
            "filter_backend": stage_backends["filter"],
            "candidate_rows": filter_output.row_count if filter_output is not None else 0,
            "candidate_csv_path": (
                deps._to_storage_path(filter_output.candidate_csv_path) if filter_output is not None else ""
            ),
            "rescan_backend": stage_backends["rescan"],
            "internal_nav_rows": rescan_output.row_count if rescan_output is not None else 0,
            "internal_nav_csv_path": (
                deps._to_storage_path(rescan_output.internal_nav_csv_path) if rescan_output is not None else ""
            ),
            "export_backend": stage_backends["export"],
            "post_collect_rows": export_output.row_count,
            "post_collect_csv_path": deps._to_storage_path(export_output.post_collect_csv_path),
            "winner_csv_rows": export_output.row_count,
            "tracker_candidate_rows": export_output.row_count,
            "primary_bid_no": export_output.primary_bid_no,
            "winner_csv_file_name": written_csv.file_name,
            "execution_manifest_file_name": execution_manifest_artifact.file_name,
            "related_notice_file_name": "",
            "related_notice_projects": 0,
            "related_notice_items": 0,
            "related_notice_precomputed": False,
            "related_notice_precompute_enabled": True,
            "related_notice_precompute_status": "queued",
            "related_notice_precompute_error": "",
            "related_notice_project_statuses": {},
            "related_notice_snapshot_set_id": "",
            "stage_backends": stage_backends,
            "notice_search_backend": export_output.stage_backend,
        }
    }
    finished_at = deps._utcnow()
    run_repository.update_run(
        run_id,
        {
            "status": "success",
            "progress_stage": deps.PROJECT_TRACKER_STAGES[-1],
            "progress_current": stage_total,
            "progress_total": stage_total,
            "summary_json": summary_json,
            "error_json": {},
            "finished_at": finished_at.isoformat(),
        },
    )
    deps._log_info(
        run_id=run_id,
        stage="finalize",
        message="project_tracker finished successfully",
        meta={
            "winner_csv_rows": export_output.row_count,
            "export_backend": export_output.stage_backend,
            "runtime_profile": "web_native",
        },
    )
    try:
        child_run, created = deps.queue_tracker_export_run_for_parent(run_id)
        summary_json["output"].update(
            {
                "auto_tracker_export_enabled": True,
                "auto_tracker_export_run_id": str(child_run["id"]),
                "auto_tracker_export_status": str(child_run.get("status") or ""),
                "auto_tracker_export_created": created,
            }
        )
        summary_json = deps._summary_json_preserving_related_notice_state(run_id, summary_json)
        deps._best_effort_update_run(
            run_id,
            {"summary_json": summary_json},
            context="auto_tracker_export_summary_success",
        )
        deps._log_info(
            run_id=run_id,
            stage="finalize",
            message="auto tracker_export queued" if created else "existing tracker_export reused",
            meta={
                "child_run_id": str(child_run["id"]),
                "created": created,
            },
        )
    except Exception as exc:
        summary_json["output"].update(
            {
                "auto_tracker_export_enabled": True,
                "auto_tracker_export_error": str(exc),
            }
        )
        summary_json = deps._summary_json_preserving_related_notice_state(run_id, summary_json)
        deps._best_effort_update_run(
            run_id,
            {"summary_json": summary_json},
            context="auto_tracker_export_summary_error",
        )
        deps._log_warning(
            run_id=run_id,
            stage="finalize",
            message="auto tracker_export queue failed",
            meta={"error_message": str(exc)},
        )
    try:
        queued = deps.queue_related_notice_precompute_for_run(run_id)
        summary_json["output"].update(
            {
                "related_notice_precompute_enabled": True,
                "related_notice_precompute_status": "queued" if queued else "skipped",
            }
        )
        summary_json = deps._summary_json_preserving_related_notice_state(run_id, summary_json)
        deps._best_effort_update_run(
            run_id,
            {"summary_json": summary_json},
            context="related_notice_queue_summary_success",
        )
        deps._log_info(
            run_id=run_id,
            stage="finalize",
            message="related notice precompute queued",
            meta={"queued": queued},
        )
    except Exception as exc:
        summary_json["output"].update(
            {
                "related_notice_precompute_enabled": True,
                "related_notice_precompute_status": "failed",
                "related_notice_precompute_error": str(exc),
            }
        )
        summary_json = deps._summary_json_preserving_related_notice_state(run_id, summary_json)
        deps._best_effort_update_run(
            run_id,
            {"summary_json": summary_json},
            context="related_notice_queue_summary_error",
        )
        deps._log_warning(
            run_id=run_id,
            stage="finalize",
            message="related notice precompute queue failed",
            meta={"error_message": str(exc)},
        )
