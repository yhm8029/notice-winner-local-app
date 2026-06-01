from __future__ import annotations

from typing import Any
from typing import Callable
from uuid import UUID


def validate_related_notice_precompute_run(
    *,
    run_id: UUID,
    run: dict[str, Any] | None,
    run_repository_error_cls: type[Exception],
) -> dict[str, Any]:
    if run is None:
        raise run_repository_error_cls(f"run not found: {run_id}")
    if str(run.get("run_type") or "").strip() not in {"project_tracker", "winner_pipeline"}:
        raise run_repository_error_cls(f"related notice precompute requires a project_tracker run: {run_id}")
    if str(run.get("status") or "").strip() != "success":
        raise run_repository_error_cls(f"related notice precompute requires a successful run: {run_id}")
    return run


def resolve_existing_related_notice_artifact_state(
    *,
    artifacts: list[dict[str, Any]],
    related_notice_artifact_type: str,
    project_key: str,
    force_recompute: bool,
    load_existing_related_notice_payload_fn: Callable[[str], dict[str, Any] | None],
    should_skip_related_notice_project_recompute_fn: Callable[..., bool],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bool]:
    existing_related_artifact = next(
        (
            item
            for item in artifacts
            if str(item.get("artifact_type") or "").strip() == related_notice_artifact_type
        ),
        None,
    )
    existing_payload = None
    if existing_related_artifact is not None:
        existing_payload = load_existing_related_notice_payload_fn(
            str(existing_related_artifact.get("storage_path") or "").strip()
        )
    should_skip = bool(
        existing_related_artifact is not None
        and project_key
        and should_skip_related_notice_project_recompute_fn(
            existing_payload=existing_payload,
            project_key=project_key,
            force_recompute=force_recompute,
        )
    )
    return existing_related_artifact, existing_payload, should_skip


def write_related_notice_precompute_artifact(
    *,
    run_id: UUID,
    artifact_repository: Any,
    existing_related_artifact: dict[str, Any] | None,
    related_notice_payload: dict[str, Any],
    related_notice_artifact_file_name: str,
    related_notice_artifact_type: str,
    write_json_artifact_fn: Callable[..., Any],
    create_artifact_record_fn: Callable[..., Any],
    update_related_notice_summary_fn: Callable[..., None],
    build_related_notice_project_status_patch_fn: Callable[..., dict[str, dict[str, str]]],
    log_info_fn: Callable[..., None],
) -> tuple[Any, list[str]]:
    related_notice_artifact = write_json_artifact_fn(
        run_id=run_id,
        file_name=related_notice_artifact_file_name,
        payload=related_notice_payload,
    )
    if existing_related_artifact is None:
        create_artifact_record_fn(
            artifact_repository=artifact_repository,
            run_id=run_id,
            artifact_type=related_notice_artifact_type,
            written_artifact=related_notice_artifact,
            meta={
                "stage": "finalize",
                "project_count": int(related_notice_payload.get("project_count") or 0),
                "item_count": int(related_notice_payload.get("item_count") or 0),
                "backend": "precomputed",
            },
        )
    payload_project_keys = [
        str(item.get("project_key") or "").strip()
        for item in (related_notice_payload.get("projects") or [])
        if str(item.get("project_key") or "").strip()
    ]
    update_related_notice_summary_fn(
        run_id=run_id,
        summary_patch={
            "related_notice_file_name": related_notice_artifact.file_name,
            "related_notice_projects": int(related_notice_payload.get("project_count") or 0),
            "related_notice_items": int(related_notice_payload.get("item_count") or 0),
            "related_notice_precomputed": True,
            "related_notice_precompute_status": "success",
            "related_notice_precompute_error": "",
            "related_notice_project_statuses": build_related_notice_project_status_patch_fn(
                payload_project_keys,
                status="success",
            ),
        },
    )
    log_info_fn(
        run_id=run_id,
        stage="finalize",
        message="related notices precomputed",
        meta={
            "project_count": int(related_notice_payload.get("project_count") or 0),
            "item_count": int(related_notice_payload.get("item_count") or 0),
            "artifact_file_name": related_notice_artifact.file_name,
        },
    )
    return related_notice_artifact, payload_project_keys
