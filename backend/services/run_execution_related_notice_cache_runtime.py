from __future__ import annotations

from typing import Any
from uuid import UUID


def upsert_related_notice_cache_entry(
    *,
    get_related_notice_cache_repository_fn: Any,
    load_phase1_identity_fn: Any,
    project_entry: dict[str, Any],
    status: str,
    source_run_id: UUID,
    error: str = "",
    snapshot_set_id: str = "",
) -> None:
    project_key = str(project_entry.get("project_key") or "").strip()
    if not project_key:
        return
    repository = get_related_notice_cache_repository_fn()
    identity = load_phase1_identity_fn()
    items = list(project_entry.get("items") or [])
    groups = dict(project_entry.get("groups") or {})
    stats = dict(project_entry.get("stats") or {})
    repository.upsert_cache(
        {
            "organization_id": str(identity.organization_id),
            "project_key": project_key,
            "snapshot_set_id": str(snapshot_set_id or "").strip() or "legacy",
            "project_name": str(project_entry.get("project_name") or ""),
            "project_search_name": str(project_entry.get("project_search_name") or ""),
            "issuer_name": str(project_entry.get("issuer_name") or ""),
            "status": status,
            "source": str(project_entry.get("source") or ""),
            "source_run_id": str(source_run_id),
            "algorithm_version": int(project_entry.get("algorithm_version") or 0),
            "payload_json": {
                "project_key": project_key,
                "project_name": str(project_entry.get("project_name") or ""),
                "project_search_name": str(project_entry.get("project_search_name") or ""),
                "issuer_name": str(project_entry.get("issuer_name") or ""),
                "latest_notice_date": str(project_entry.get("latest_notice_date") or ""),
                "source_run_id": str(source_run_id),
                "source": str(project_entry.get("source") or ""),
                "algorithm_version": int(project_entry.get("algorithm_version") or 0),
                "error": error,
                "search_debug": dict(project_entry.get("search_debug") or {}),
                "items": items,
                "groups": groups,
                "stats": stats,
                "item_count": len(items),
            },
            "error": error,
        }
    )


def resolve_related_notice_snapshot_set_id(
    *,
    run_repository: Any,
    run_id: UUID,
    snapshot_set_id: str,
) -> str:
    if snapshot_set_id:
        return snapshot_set_id
    run_row = run_repository.get_run(run_id)
    summary_output = dict((run_row or {}).get("summary_json") or {}).get("output") or {}
    return str(summary_output.get("related_notice_snapshot_set_id") or run_id)


def related_notice_reuse_snapshot_keys(
    *,
    load_phase1_identity_fn: Any,
    get_related_notice_publication_repository_fn: Any,
) -> list[str]:
    snapshot_keys: list[str] = []
    try:
        identity = load_phase1_identity_fn()
        publication = get_related_notice_publication_repository_fn().get_publication(
            organization_id=identity.organization_id,
        )
    except Exception:
        publication = None
    published_snapshot_key = str((publication or {}).get("published_snapshot_set_id") or "").strip()
    if published_snapshot_key:
        snapshot_keys.append(published_snapshot_key)
    if "legacy" not in snapshot_keys:
        snapshot_keys.append("legacy")
    return snapshot_keys


def reusable_related_notice_project_entry(
    *,
    get_related_notice_cache_repository_fn: Any,
    is_missing_related_notice_cache_table_error_fn: Any,
    project: dict[str, Any],
    run_id: UUID,
    reuse_snapshot_keys: list[str],
    related_notice_algorithm_version: int,
) -> dict[str, Any] | None:
    project_key = str(project.get("project_key") or "").strip()
    if not project_key:
        return None
    repository = get_related_notice_cache_repository_fn()
    for snapshot_key in reuse_snapshot_keys:
        cache_row = None
        try:
            cache_row = repository.get_cache(project_key=project_key, snapshot_set_id=snapshot_key)
        except TypeError as exc:
            if "snapshot_set_id" not in str(exc):
                raise
            cache_row = repository.get_cache(project_key=project_key)
        except Exception as exc:
            if is_missing_related_notice_cache_table_error_fn(str(exc)):
                cache_row = None
            else:
                raise
        if cache_row is None:
            continue
        if str(cache_row.get("status") or "").strip() != "success":
            continue
        payload = dict(cache_row.get("payload_json") or {})
        if int(payload.get("algorithm_version") or cache_row.get("algorithm_version") or 0) < related_notice_algorithm_version:
            continue
        items = [dict(item) for item in (payload.get("items") or []) if isinstance(item, dict)]
        groups = dict(payload.get("groups") or {})
        stats = dict(payload.get("stats") or {})
        return {
            "project_key": project_key,
            "project_name": str(project.get("project_name") or payload.get("project_name") or ""),
            "project_search_name": str(project.get("project_search_name") or payload.get("project_search_name") or ""),
            "algorithm_version": related_notice_algorithm_version,
            "issuer_name": str(project.get("issuer_name") or payload.get("issuer_name") or ""),
            "latest_notice_date": str(project.get("latest_notice_date") or payload.get("latest_notice_date") or ""),
            "source_run_id": str(run_id),
            "source": str(payload.get("source") or cache_row.get("source") or "cache"),
            "error": "",
            "search_debug": {
                "cache_reused": True,
                "reused_snapshot_set_id": snapshot_key,
                "reused_source_run_id": str(cache_row.get("source_run_id") or payload.get("source_run_id") or ""),
                "reused_item_count": len(items),
            },
            "items": items,
            "groups": groups,
            "stats": stats,
            "item_count": len(items),
        }
    return None
