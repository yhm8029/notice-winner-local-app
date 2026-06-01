from __future__ import annotations

from typing import Any
from uuid import UUID


def preview_tracker_cleanup(
    *,
    source_tracker_run_id: UUID,
    tracker_repository: Any,
    run_repository: Any,
    log_repository: Any,
    artifact_repository: Any,
) -> dict[str, Any]:
    entries, total = tracker_repository.list_entries(
        page=1,
        page_size=10_000,
        q="",
        region="",
        exclude_auxiliary_titles=False,
        edited_only=False,
        source_run_id=None,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name="",
        section_name="",
    )
    parent_run_id = _coerce_uuid_or_none((entries[0] if entries else {}).get("source_run_id"))
    child_run = run_repository.get_run(source_tracker_run_id)
    if parent_run_id is None and child_run is not None:
        parent_run_id = _coerce_uuid_or_none(child_run.get("parent_run_id"))
    parent_run = run_repository.get_run(parent_run_id) if parent_run_id is not None else None
    delete_parent = _should_delete_parent_run(
        source_tracker_run_id=source_tracker_run_id,
        parent_run_id=parent_run_id,
        run_repository=run_repository,
    )

    log_count = len(log_repository.list_logs(run_id=source_tracker_run_id, cursor=None, limit=10_000)[0])
    artifact_count = len(artifact_repository.list_artifacts(run_id=source_tracker_run_id))
    if delete_parent and parent_run_id is not None:
        log_count += len(log_repository.list_logs(run_id=parent_run_id, cursor=None, limit=10_000)[0])
        artifact_count += len(artifact_repository.list_artifacts(run_id=parent_run_id))

    return {
        "source_tracker_run_id": str(source_tracker_run_id),
        "parent_run_id": str(parent_run_id) if parent_run_id is not None else "",
        "tracker_entry_count": total,
        "child_run_count": 1 if child_run is not None else 0,
        "parent_run_count": 1 if delete_parent and parent_run is not None else 0,
        "log_count": log_count,
        "artifact_count": artifact_count,
    }


def apply_tracker_cleanup(
    *,
    source_tracker_run_id: UUID,
    tracker_repository: Any,
    run_repository: Any,
    log_repository: Any,
    artifact_repository: Any,
) -> dict[str, Any]:
    preview = preview_tracker_cleanup(
        source_tracker_run_id=source_tracker_run_id,
        tracker_repository=tracker_repository,
        run_repository=run_repository,
        log_repository=log_repository,
        artifact_repository=artifact_repository,
    )
    parent_run_id = _coerce_uuid_or_none(preview.get("parent_run_id"))

    deleted_artifact_count = artifact_repository.delete_artifacts_for_run(source_tracker_run_id)
    deleted_log_count = log_repository.delete_logs_for_run(source_tracker_run_id)
    deleted_run_count = 1 if run_repository.delete_run(source_tracker_run_id) else 0

    deleted_tracker_entry_count = tracker_repository.delete_entries_by_source_tracker_run_id(
        source_tracker_run_id=source_tracker_run_id
    )

    if preview.get("parent_run_count") and parent_run_id is not None:
        deleted_artifact_count += artifact_repository.delete_artifacts_for_run(parent_run_id)
        deleted_log_count += log_repository.delete_logs_for_run(parent_run_id)
        deleted_run_count += 1 if run_repository.delete_run(parent_run_id) else 0

    return {
        "source_tracker_run_id": str(source_tracker_run_id),
        "parent_run_id": str(parent_run_id) if parent_run_id is not None else "",
        "deleted_tracker_entry_count": deleted_tracker_entry_count,
        "deleted_run_count": deleted_run_count,
        "deleted_log_count": deleted_log_count,
        "deleted_artifact_count": deleted_artifact_count,
    }


def _coerce_uuid_or_none(value: Any) -> UUID | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    return UUID(raw)


def _should_delete_parent_run(
    *,
    source_tracker_run_id: UUID,
    parent_run_id: UUID | None,
    run_repository: Any,
) -> bool:
    if parent_run_id is None:
        return False
    sibling_runs, _total = run_repository.list_runs(
        page=1,
        page_size=1000,
        status="",
        run_type="tracker_export",
        parent_run_id=parent_run_id,
        date_from="",
        date_to="",
    )
    for row in sibling_runs:
        sibling_run_id = _coerce_uuid_or_none(row.get("id"))
        if sibling_run_id is not None and sibling_run_id != source_tracker_run_id:
            return False
    return True
