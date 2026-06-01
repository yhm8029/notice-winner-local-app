from __future__ import annotations

import threading
from typing import Any
from uuid import UUID


def queue_tracker_export_run_for_parent(
    *,
    get_run_repository_fn: Any,
    get_artifact_repository_fn: Any,
    build_phase1_run_row_fn: Any,
    safely_execute_tracker_export_fn: Any,
    run_repository_error_cls: Any,
    track_export_run_type: str,
    parent_run_id: UUID,
    force_new: bool = False,
):
    run_repository = get_run_repository_fn()
    artifact_repository = get_artifact_repository_fn()

    parent = run_repository.get_run(parent_run_id)
    if parent is None:
        raise run_repository_error_cls(f"parent run not found: {parent_run_id}")
    if str(parent.get("run_type") or "").strip() not in {"project_tracker", "winner_pipeline"}:
        raise run_repository_error_cls(f"tracker_export requires a project_tracker parent run: {parent_run_id}")
    if str(parent.get("status") or "").strip() != "success":
        raise run_repository_error_cls(f"tracker_export requires a successful project_tracker run: {parent_run_id}")

    parent_artifacts = artifact_repository.list_artifacts(run_id=parent_run_id)
    if not any(str(item.get("artifact_type") or "").strip() == "winner_csv" for item in parent_artifacts):
        raise run_repository_error_cls("tracker_export requires a winner_csv artifact on the parent run")

    existing_rows, _total = run_repository.list_runs(
        page=1,
        page_size=50,
        status="",
        run_type=track_export_run_type,
        parent_run_id=parent_run_id,
        date_from="",
        date_to="",
    )
    existing_rows = sorted(existing_rows, key=lambda row: str(row.get("created_at") or ""), reverse=True)
    reusable_statuses = {"queued", "running", "success"}
    if not force_new:
        for row in existing_rows:
            if str(row.get("status") or "").strip() in reusable_statuses:
                return row, False

    child_row = build_phase1_run_row_fn(
        run_type=track_export_run_type,
        params={"source_run_id": str(parent_run_id), "auto_created": True},
        parent_run_id=parent_run_id,
        progress_stage="",
    )
    stored = run_repository.create_run(child_row)
    worker = threading.Thread(
        target=safely_execute_tracker_export_fn,
        args=(parent_run_id, UUID(str(stored["id"]))),
        daemon=True,
    )
    worker.start()
    return stored, True
