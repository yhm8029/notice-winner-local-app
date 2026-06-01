from __future__ import annotations

from typing import Any
from uuid import UUID


def update_related_notice_summary(
    *,
    run_repository: Any,
    run_id: UUID,
    summary_patch: dict[str, Any],
) -> None:
    run_row = run_repository.get_run(run_id)
    if run_row is None:
        return
    patch = dict(summary_patch)
    project_status_patch = dict(patch.pop("related_notice_project_statuses", {}) or {})
    summary_json = dict(run_row.get("summary_json") or {})
    output = dict(summary_json.get("output") or {})
    if project_status_patch:
        merged_statuses = dict(output.get("related_notice_project_statuses") or {})
        for project_key, entry in project_status_patch.items():
            key = str(project_key or "").strip()
            if not key:
                continue
            current = dict(merged_statuses.get(key) or {})
            current.update(dict(entry or {}))
            merged_statuses[key] = current
        output["related_notice_project_statuses"] = merged_statuses
    output.update(patch)
    summary_json["output"] = output
    run_repository.update_run(run_id, {"summary_json": summary_json})


def merge_run_summary_output(
    *,
    run_repository: Any,
    best_effort_update_run_fn: Any,
    run_id: UUID,
    summary_patch: dict[str, Any],
    context: str,
) -> None:
    run_row = run_repository.get_run(run_id)
    if run_row is None:
        return
    summary_json = dict(run_row.get("summary_json") or {})
    output = dict(summary_json.get("output") or {})
    output.update(dict(summary_patch or {}))
    summary_json["output"] = output
    best_effort_update_run_fn(run_id, {"summary_json": summary_json}, context=context)


def create_artifact_record(
    *,
    load_phase1_identity_fn: Any,
    artifact_repository: Any,
    run_id: UUID,
    artifact_type: str,
    written_artifact: Any,
    meta: dict[str, Any],
) -> None:
    identity = load_phase1_identity_fn()
    artifact_repository.create_artifact(
        {
            "run_id": str(run_id),
            "organization_id": str(identity.organization_id),
            "artifact_type": artifact_type,
            "storage_path": written_artifact.storage_path,
            "file_name": written_artifact.file_name,
            "mime_type": written_artifact.mime_type,
            "size_bytes": written_artifact.size_bytes,
            "checksum": written_artifact.checksum,
            "meta_json": meta,
        }
    )


def create_log(
    *,
    load_phase1_identity_fn: Any,
    get_run_log_repository_fn: Any,
    lifecycle_runtime: Any,
    sys_module: Any,
    run_id: UUID,
    level: str,
    stage: str,
    message: str,
    meta: dict[str, Any],
) -> None:
    identity = load_phase1_identity_fn()
    return lifecycle_runtime.create_log(
        log_repository=get_run_log_repository_fn(),
        sys_module=sys_module,
        organization_id=identity.organization_id,
        run_id=run_id,
        level=level,
        stage=stage,
        message=message,
        meta=meta,
    )
