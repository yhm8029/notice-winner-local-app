from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from backend.services.related_notice_classification import classify_related_notice_item
from backend.services.related_notice_classification import group_related_notice_items


def related_notice_precompute_dedup_key(
    run_id: UUID,
    *,
    project_key: str = "",
    backfill_remaining: bool = True,
    force_recompute: bool = False,
    snapshot_set_id: str = "",
) -> str:
    if backfill_remaining and not force_recompute and not str(snapshot_set_id or "").strip():
        return f"{run_id}:{str(project_key or '').strip()}"
    return "::".join(
        (
            str(run_id),
            str(project_key or "").strip(),
            "backfill" if backfill_remaining else "single",
            "force" if force_recompute else "normal",
            str(snapshot_set_id or "").strip(),
        )
    )


def load_existing_related_notice_payload(
    storage_path: str,
    *,
    resolve_artifact_path_fn: Any,
) -> dict[str, Any] | None:
    artifact_path = resolve_artifact_path_fn(storage_path)
    if not artifact_path.exists():
        return None
    try:
        with artifact_path.open("r", encoding="utf-8") as fp:
            payload = json.load(fp)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def related_notice_payload_has_project(
    payload: dict[str, Any] | None,
    project_key: str,
    *,
    algorithm_version: int,
) -> bool:
    if not payload or not project_key:
        return False
    for item in payload.get("projects") or []:
        if (
            str(item.get("project_key") or "").strip() == project_key
            and int(item.get("algorithm_version") or 0) >= algorithm_version
            and bool(list(item.get("items") or []))
        ):
            return True
    return False


def should_skip_related_notice_project_recompute(
    *,
    existing_payload: dict[str, Any] | None,
    project_key: str,
    force_recompute: bool,
    related_notice_payload_has_project_fn: Any,
) -> bool:
    if force_recompute:
        return False
    return bool(related_notice_payload_has_project_fn(existing_payload, project_key))


def is_missing_related_notice_cache_table_error(message: str) -> bool:
    lowered = str(message or "").lower()
    if "project_related_notice_cache" not in lowered:
        return False
    return any(
        token in lowered
        for token in (
            "could not find the table",
            "schema cache",
            "relation",
            "does not exist",
        )
    )


def related_notice_incremental_recompute_project_keys(payload: dict[str, Any] | None) -> list[str]:
    if not payload:
        return []
    project_keys: list[str] = []
    for item in payload.get("projects") or []:
        project_key = str(item.get("project_key") or "").strip()
        if not project_key:
            continue
        if str(item.get("source") or "").strip() != "seed_fallback":
            continue
        project_keys.append(project_key)
    return project_keys


def seed_fallback_related_notice_items(
    *,
    project: dict[str, Any],
    seed_rows: list[dict[str, Any]],
    score_related_notice_match_fn: Any,
    project_search_name_fn: Any,
    dedupe_related_notice_payload_items_fn: Any,
) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for row in seed_rows:
        score, candidate_search_name, reason = score_related_notice_match_fn(project, row)
        if score < 20:
            continue
        key = "::".join(
            (
                str(row.get("bid_no") or "").strip(),
                str(row.get("bid_ord") or "").strip(),
                candidate_search_name or project_search_name_fn(str(row.get("project_name") or "").strip()),
            )
        )
        item = classify_related_notice_item(
            project,
            {
            "id": key,
            "project_name": str(row.get("project_name") or "").strip(),
            "project_search_name": candidate_search_name,
            "issuer_name": str(row.get("org_name") or "").strip(),
            "announce_date": str(row.get("announce_date") or "").strip(),
            "bid_no": str(row.get("bid_no") or "").strip(),
            "bid_ord": str(row.get("bid_ord") or "").strip(),
            "g2b_verified": str(row.get("g2b_verified") or "").strip(),
            "notice_url": str(row.get("bid_ntce_url") or "").strip(),
            "notice_detail_url": str(row.get("bid_ntce_dtl_url") or "").strip(),
            "match_score": score,
            "match_reason": reason,
            },
        )
        current = deduped.get(key)
        if current is None or int(item["match_score"]) > int(current.get("match_score") or 0):
            deduped[key] = item
    return dedupe_related_notice_payload_items_fn(list(deduped.values()))


def build_related_notice_project_entry(
    *,
    project: dict[str, Any],
    run_id: UUID,
    items: list[dict[str, Any]],
    source: str,
    error_message: str,
    search_debug: dict[str, Any],
    algorithm_version: int,
) -> dict[str, Any]:
    classified_items = [classify_related_notice_item(project, dict(item)) for item in items]
    groups = group_related_notice_items(project, classified_items)
    stats = {
        "item_count": len(classified_items),
        "sales_relevant_count": len(groups["sales_relevant"]),
        "reference_count": len(groups["reference"]),
        "excluded_count": len(groups["excluded"]),
    }
    return {
        "project_key": str(project.get("project_key") or ""),
        "project_name": str(project.get("project_name") or ""),
        "project_search_name": str(project.get("project_search_name") or ""),
        "algorithm_version": algorithm_version,
        "issuer_name": str(project.get("issuer_name") or ""),
        "latest_notice_date": str(project.get("latest_notice_date") or ""),
        "source_run_id": str(run_id),
        "source": source,
        "error": error_message,
        "search_debug": search_debug,
        "items": classified_items,
        "groups": groups,
        "stats": stats,
        "item_count": len(classified_items),
    }


def merge_related_notice_payload(
    existing_payload: dict[str, Any] | None,
    new_payload: dict[str, Any],
    *,
    utcnow_fn: Any,
) -> dict[str, Any]:
    if not existing_payload:
        return new_payload
    merged_projects: dict[str, dict[str, Any]] = {}
    for payload in (existing_payload, new_payload):
        for item in payload.get("projects") or []:
            key = str(item.get("project_key") or "").strip()
            if not key:
                continue
            merged_projects[key] = dict(item)
    merged_list = list(merged_projects.values())
    merged_list.sort(
        key=lambda item: (
            str(item.get("latest_notice_date") or ""),
            int(item.get("item_count") or 0),
            str(item.get("project_name") or ""),
        ),
        reverse=True,
    )
    return {
        "run_id": str(new_payload.get("run_id") or existing_payload.get("run_id") or ""),
        "generated_at": utcnow_fn().isoformat(),
        "project_count": len(merged_list),
        "item_count": sum(int(item.get("item_count") or 0) for item in merged_list),
        "projects": merged_list,
    }


def related_notice_payload_project_keys(payload: dict[str, Any] | None) -> list[str]:
    if not payload:
        return []
    return [
        str(item.get("project_key") or "").strip()
        for item in (payload.get("projects") or [])
        if str(item.get("project_key") or "").strip()
    ]


def build_related_notice_project_status_patch(
    project_keys: list[str] | set[str] | tuple[str, ...],
    *,
    status: str,
    error: str = "",
    utcnow_fn: Any,
) -> dict[str, dict[str, str]]:
    timestamp = utcnow_fn().isoformat()
    patch: dict[str, dict[str, str]] = {}
    for project_key in project_keys:
        key = str(project_key or "").strip()
        if not key:
            continue
        patch[key] = {
            "status": status,
            "error": str(error or ""),
            "updated_at": timestamp,
        }
    return patch
