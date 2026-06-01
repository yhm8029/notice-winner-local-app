from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID


def best_effort_update_run(*, run_repository: Any, sys_module: Any, run_id: UUID, fields: dict[str, Any], context: str) -> None:
    try:
        run_repository.update_run(run_id, fields)
    except Exception as exc:
        print(
            f"[run_execution] failed to update run ({context}, run_id={run_id}): {exc}",
            file=sys_module.stderr,
        )


def summary_json_preserving_related_notice_state(
    *,
    run_repository: Any,
    run_id: UUID,
    summary_json: dict[str, Any],
) -> dict[str, Any]:
    current_run = run_repository.get_run(run_id)
    if current_run is None:
        return summary_json

    current_summary_json = dict(current_run.get("summary_json") or {})
    current_output = dict(current_summary_json.get("output") or {})
    if not current_output:
        return summary_json

    merged_summary_json = dict(summary_json)
    merged_output = dict(merged_summary_json.get("output") or {})
    incoming_status = str(merged_output.get("related_notice_precompute_status") or "").strip()
    if incoming_status in {"skipped", "failed"}:
        merged_summary_json["output"] = merged_output
        return merged_summary_json

    current_status = str(current_output.get("related_notice_precompute_status") or "").strip()
    if current_status != "success":
        merged_summary_json["output"] = merged_output
        return merged_summary_json

    for key, current_value in current_output.items():
        if str(key).startswith("related_notice_"):
            merged_output[key] = current_value
    merged_summary_json["output"] = merged_output
    return merged_summary_json


def should_preserve_terminal_run_status(*, run_repository: Any, sys_module: Any, run_id: UUID, exc: Exception) -> bool:
    try:
        run = run_repository.get_run(run_id)
    except Exception as lookup_exc:
        print(
            f"[run_execution] failed to inspect run status after background error for {run_id}: {lookup_exc}",
            file=sys_module.stderr,
        )
        return False
    if run is None:
        return False
    status = str(run.get("status") or "").strip().lower()
    if status not in {"success", "cancelled"}:
        return False
    print(
        f"[run_execution] suppressed background error after terminal status "
        f"(run_id={run_id}, status={status}): {exc}",
        file=sys_module.stderr,
    )
    return True


def create_log(
    *,
    log_repository: Any,
    sys_module: Any,
    organization_id: Any,
    run_id: UUID,
    level: str,
    stage: str,
    message: str,
    meta: dict[str, Any],
) -> None:
    try:
        log_repository.create_log(
            {
                "run_id": str(run_id),
                "organization_id": str(organization_id),
                "level": level,
                "stage": stage,
                "message": message,
                "meta_json": meta,
            }
        )
    except Exception as exc:
        print(
            f"[run_execution] failed to persist log "
            f"(run_id={run_id}, level={level}, stage={stage}, message={message}): {exc}",
            file=sys_module.stderr,
        )


def is_cancel_requested(*, run_repository: Any, run_id: UUID) -> bool:
    run = run_repository.get_run(run_id)
    return bool(run and run.get("cancel_requested"))


def cancel_run_if_requested(deps: Any, *, run_id: UUID, current_stage: str) -> bool:
    run_repository = deps.get_run_repository()
    run = run_repository.get_run(run_id)
    if run is None or not bool(run.get("cancel_requested")):
        return False
    finished_at = deps._utcnow()
    run_repository.update_run(
        run_id,
        {
            "status": "cancelled",
            "progress_stage": current_stage,
            "finished_at": finished_at.isoformat(),
        },
    )
    if str(run.get("run_type") or "").strip() == deps.TRACKER_EXPORT_RUN_TYPE and run.get("parent_run_id"):
        parent_run_id = UUID(str(run["parent_run_id"]))
        deps._update_tracker_export_parent_summary(
            parent_run_id=parent_run_id,
            summary_patch={
                "auto_tracker_export_enabled": True,
                "auto_tracker_export_run_id": str(run_id),
                "auto_tracker_export_status": "cancelled",
                "auto_tracker_export_progress_stage": current_stage,
            },
            context="tracker_export_parent_cancelled_requested",
        )
    return True


def mark_run_cancelled(deps: Any, run_id: UUID) -> None:
    run_repository = deps.get_run_repository()
    run = run_repository.get_run(run_id)
    if run is None:
        return
    current_stage = str(run.get("progress_stage") or "finalize").strip() or "finalize"
    finished_at = deps._utcnow()
    deps._log_warning(
        run_id=run_id,
        stage=current_stage,
        message="project_tracker cancelled during stage execution",
        meta={"stage": current_stage},
    )
    run_repository.update_run(
        run_id,
        {
            "status": "cancelled",
            "progress_stage": current_stage,
            "finished_at": finished_at.isoformat(),
        },
    )
    if str(run.get("run_type") or "").strip() == deps.TRACKER_EXPORT_RUN_TYPE and run.get("parent_run_id"):
        parent_run_id = UUID(str(run["parent_run_id"]))
        deps._update_tracker_export_parent_summary(
            parent_run_id=parent_run_id,
            summary_patch={
                "auto_tracker_export_enabled": True,
                "auto_tracker_export_run_id": str(run_id),
                "auto_tracker_export_status": "cancelled",
                "auto_tracker_export_progress_stage": current_stage,
            },
            context="tracker_export_parent_cancelled",
        )


def fail_run(deps: Any, run_id: UUID, message: str) -> None:
    run_repository = deps.get_run_repository()
    run = run_repository.get_run(run_id)
    deps._log_error(
        run_id=run_id,
        stage="finalize",
        message="run execution failed",
        meta={"error_message": message},
    )
    run_repository.update_run(
        run_id,
        {
            "status": "failed",
            "progress_stage": "finalize",
            "error_json": {"code": "execution_error", "message": message},
            "finished_at": deps._utcnow().isoformat(),
        },
    )
    if run is not None and str(run.get("run_type") or "").strip() == deps.TRACKER_EXPORT_RUN_TYPE and run.get("parent_run_id"):
        parent_run_id = UUID(str(run["parent_run_id"]))
        deps._update_tracker_export_parent_summary(
            parent_run_id=parent_run_id,
            summary_patch={
                "auto_tracker_export_enabled": True,
                "auto_tracker_export_run_id": str(run_id),
                "auto_tracker_export_status": "failed",
                "auto_tracker_export_progress_stage": "finalize",
                "auto_tracker_export_error": message,
            },
            context="tracker_export_parent_failed",
        )


def safely_execute_project_tracker(deps: Any, run_id: UUID) -> None:
    started = deps.time.perf_counter()
    try:
        deps.execute_project_tracker(run_id)
        deps.log_task_duration(
            task_name="project_tracker",
            duration=deps.time.perf_counter() - started,
            status="ok",
            run_id=str(run_id),
        )
    except InterruptedError:
        deps._mark_run_cancelled(run_id)
        deps.log_task_duration(
            task_name="project_tracker",
            duration=deps.time.perf_counter() - started,
            status="cancelled",
            run_id=str(run_id),
        )
    except Exception as exc:
        if deps._should_preserve_terminal_run_status(run_id, exc):
            deps.log_task_duration(
                task_name="project_tracker",
                duration=deps.time.perf_counter() - started,
                status="preserved",
                run_id=str(run_id),
            )
            return
        deps.fail_run(run_id, str(exc))
        deps.log_task_duration(
            task_name="project_tracker",
            duration=deps.time.perf_counter() - started,
            status="error",
            run_id=str(run_id),
        )


def safely_execute_tracker_export(deps: Any, parent_run_id: UUID, child_run_id: UUID) -> None:
    started = deps.time.perf_counter()
    try:
        deps.execute_tracker_export(parent_run_id, child_run_id)
        deps.log_task_duration(
            task_name="tracker_export",
            duration=deps.time.perf_counter() - started,
            status="ok",
            parent_run_id=str(parent_run_id),
            child_run_id=str(child_run_id),
        )
    except Exception as exc:
        if deps._should_preserve_terminal_run_status(child_run_id, exc):
            deps.log_task_duration(
                task_name="tracker_export",
                duration=deps.time.perf_counter() - started,
                status="preserved",
                parent_run_id=str(parent_run_id),
                child_run_id=str(child_run_id),
            )
            return
        deps.fail_run(child_run_id, str(exc))
        deps.log_task_duration(
            task_name="tracker_export",
            duration=deps.time.perf_counter() - started,
            status="error",
            parent_run_id=str(parent_run_id),
            child_run_id=str(child_run_id),
        )
