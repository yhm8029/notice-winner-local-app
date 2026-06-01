from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import UUID

from backend.api.schemas import RelatedNoticeItem
from backend.repositories import ArtifactRepositoryError
from backend.repositories import RelatedNoticeCacheRepositoryError
from backend.repositories import RunRepositoryError
from backend.services.related_notice_classification import classify_related_notice_item
from backend.services.related_notice_query_runtime import _project_match_key


def dedupe_related_notice_rows(
    rows: list[dict[str, str]],
    *,
    norm_text_fn: Any,
) -> list[dict[str, str]]:
    deduped: dict[str, dict[str, str]] = {}
    for row in rows:
        key = "::".join(
            (
                str(row.get("bid_no") or "").strip(),
                str(row.get("bid_ord") or "").strip(),
                norm_text_fn(str(row.get("project_name") or "").strip()),
            )
        )
        if not key.strip(":"):
            continue
        deduped.setdefault(key, row)
    return list(deduped.values())


def project_source_runs(
    project: dict[str, Any],
    *,
    get_run_repository_fn: Any,
    repository_error_fn: Any,
) -> list[dict[str, Any]]:
    run_repository = get_run_repository_fn()
    run_rows: list[dict[str, Any]] = []
    for run_id_str in list(dict.fromkeys((project.get("source_json") or {}).get("run_ids") or [])):
        try:
            run_id = UUID(str(run_id_str))
        except ValueError:
            continue
        try:
            run_row = run_repository.get_run(run_id)
        except RunRepositoryError as exc:
            repository_error_fn(str(exc))
            continue
        else:
            if run_row is not None:
                run_rows.append(run_row)
    run_rows.sort(
        key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""),
        reverse=True,
    )
    return run_rows


def project_source_notice_keys(
    project: dict[str, Any],
    *,
    get_artifact_repository_fn: Any,
    project_source_runs_fn: Any,
    load_seed_rows_from_artifact_path_fn: Any,
    project_search_name_fn: Any,
    project_match_key_fn: Any,
    repository_error_fn: Any,
) -> set[tuple[str, str]]:
    cached = project.get("_source_notice_keys")
    if isinstance(cached, set):
        return cached

    target_key = str(project.get("_project_match_key") or "").strip()
    keys: set[tuple[str, str]] = set()
    artifact_repository = get_artifact_repository_fn()
    for run_row in project_source_runs_fn(project):
        try:
            run_id = UUID(str(run_row["id"]))
        except Exception:
            continue
        try:
            artifacts = artifact_repository.list_artifacts(run_id=run_id)
        except ArtifactRepositoryError as exc:
            repository_error_fn(str(exc))
            continue
        for artifact in artifacts:
            if str(artifact.get("artifact_type") or "").strip() != "seed_csv":
                continue
            storage_path = str(artifact.get("storage_path") or "").strip()
            if not storage_path:
                continue
            for row in load_seed_rows_from_artifact_path_fn(storage_path):
                bid_no = str(row.get("bid_no") or "").strip()
                bid_ord = str(row.get("bid_ord") or "").strip()
                if not bid_no:
                    continue
                project_name = str(row.get("project_name") or "").strip()
                candidate_search_name = project_search_name_fn(project_name)
                candidate_key = project_match_key_fn(candidate_search_name or project_name)
                if target_key and candidate_key != target_key:
                    continue
                keys.add((bid_no, bid_ord))
    project["_source_notice_keys"] = keys
    return keys


def filter_self_related_notice_payload_items(
    project: dict[str, Any],
    items: list[dict[str, Any]],
    *,
    project_source_notice_keys_fn: Any,
) -> list[dict[str, Any]]:
    source_notice_keys = project_source_notice_keys_fn(project)
    if not source_notice_keys:
        return list(items)
    filtered: list[dict[str, Any]] = []
    for raw_item in items:
        item = dict(raw_item)
        bid_no = str(item.get("bid_no") or "").strip()
        bid_ord = str(item.get("bid_ord") or "").strip()
        if bid_no and (bid_no, bid_ord) in source_notice_keys:
            continue
        filtered.append(item)
    return filtered


def is_related_notice_payload_entry_precomputed(
    entry: dict[str, Any],
    *,
    related_notice_algorithm_version: int = 11,
) -> bool:
    algorithm_version = int(entry.get("algorithm_version") or 0)
    items = list(entry.get("items") or [])
    return algorithm_version >= related_notice_algorithm_version and bool(items)


def seed_related_notice_items(
    project: dict[str, Any],
    *,
    trace_id: str | None = None,
    project_id: UUID | None = None,
    get_artifact_repository_fn: Any,
    load_seed_rows_from_artifact_path_fn: Any,
    score_related_notice_match_fn: Any,
    project_search_name_fn: Any,
    filter_self_related_notice_payload_items_fn: Any,
    dedupe_related_notice_payload_items_fn: Any,
    append_related_notice_trace_fn: Any | None = None,
    repository_error_fn: Any | None = None,
    related_notice_item_cls: Any = RelatedNoticeItem,
) -> list[Any]:
    if repository_error_fn is None:
        repository_error_fn = lambda message: (_ for _ in ()).throw(RuntimeError(message))
    artifact_repository = get_artifact_repository_fn()
    related_items: dict[str, dict[str, Any]] = {}
    for run_id_str in list(dict.fromkeys((project.get("source_json") or {}).get("run_ids") or [])):
        try:
            run_id = UUID(str(run_id_str))
        except ValueError:
            continue
        try:
            artifacts = artifact_repository.list_artifacts(run_id=run_id)
        except ArtifactRepositoryError as exc:
            repository_error_fn(str(exc))
            continue
        for artifact in artifacts:
            if str(artifact.get("artifact_type") or "") != "seed_csv":
                continue
            storage_path = str(artifact.get("storage_path") or "").strip()
            if not storage_path:
                continue
            for row in load_seed_rows_from_artifact_path_fn(storage_path):
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
                item = related_items.setdefault(
                    key,
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
                if score > int(item.get("match_score") or 0):
                    item["match_score"] = score
                    item["match_reason"] = reason

    items = filter_self_related_notice_payload_items_fn(
        project,
        dedupe_related_notice_payload_items_fn(list(related_items.values())),
    )
    if trace_id and append_related_notice_trace_fn is not None:
        append_related_notice_trace_fn(
            trace_id=trace_id,
            event="seed_fallback_items_built",
            project_id=project_id,
            project=project,
            payload={
                "seed_item_count": len(items),
                "seed_bid_nos": [
                    str(item.get("bid_no") or "").strip()
                    for item in items
                    if str(item.get("bid_no") or "").strip()
                ],
            },
        )
    return [related_notice_item_cls(**classify_related_notice_item(project, dict(item))) for item in items]


def precomputed_related_notice_items(
    project: dict[str, Any],
    *,
    trace_id: str | None = None,
    project_id: UUID | None = None,
    published_snapshot_set_id: str | None = None,
    get_related_notice_cache_repository_fn: Any,
    is_missing_related_notice_cache_table_error_fn: Any,
    repository_error_fn: Any,
    filter_self_related_notice_payload_items_fn: Any,
    dedupe_related_notice_payload_items_fn: Any,
    project_source_runs_fn: Any,
    get_artifact_repository_fn: Any,
    load_json_artifact_payload_fn: Any,
    append_related_notice_trace_fn: Any,
    is_related_notice_payload_entry_precomputed_fn: Any | None = None,
    related_notice_item_cls: Any = RelatedNoticeItem,
    project_match_key_fn: Any = _project_match_key,
    related_notice_algorithm_version: int = 11,
    allow_artifact_scan: bool = True,
) -> tuple[list[Any], bool]:
    if is_related_notice_payload_entry_precomputed_fn is None:
        is_related_notice_payload_entry_precomputed_fn = lambda entry: is_related_notice_payload_entry_precomputed(
            entry,
            related_notice_algorithm_version=related_notice_algorithm_version,
        )
    target_key = str(project.get("_project_match_key") or "").strip()
    published_snapshot_key = str(published_snapshot_set_id or "").strip() or None
    if not target_key:
        return [], False
    cache_repository = get_related_notice_cache_repository_fn()
    try:
        cache_row = cache_repository.get_cache(project_key=target_key, snapshot_set_id=published_snapshot_key)
    except TypeError as exc:
        if "snapshot_set_id" not in str(exc):
            raise
        cache_row = cache_repository.get_cache(project_key=target_key)
    except RelatedNoticeCacheRepositoryError as exc:
        if is_missing_related_notice_cache_table_error_fn(str(exc)):
            cache_row = None
        else:
            repository_error_fn(str(exc))
            cache_row = None
    if cache_row is not None:
        cache_payload = dict(cache_row.get("payload_json") or {})
        if is_related_notice_payload_entry_precomputed_fn(cache_payload):
            payload_items = filter_self_related_notice_payload_items_fn(
                project,
                dedupe_related_notice_payload_items_fn(list(cache_payload.get("items") or [])),
            )
            items = [related_notice_item_cls(**classify_related_notice_item(project, dict(item))) for item in payload_items]
            if trace_id and append_related_notice_trace_fn is not None:
                append_related_notice_trace_fn(
                    trace_id=trace_id,
                    event="global_cache_hit",
                    project_id=project_id,
                    project=project,
                    payload={
                        "item_count": len(items),
                        "source": str(cache_row.get("source") or ""),
                        "algorithm_version": int(cache_row.get("algorithm_version") or 0),
                    },
                )
            return items, True
    if trace_id and append_related_notice_trace_fn is not None:
        append_related_notice_trace_fn(
            trace_id=trace_id,
            event="published_snapshot_miss" if published_snapshot_key else "legacy_cache_miss",
            project_id=project_id,
            project=project,
            payload={"published_snapshot_set_id": published_snapshot_key or ""},
        )
    return [], False


def select_project_source_notice_row(
    project: dict[str, Any],
    *,
    get_artifact_repository_fn: Any,
    project_source_runs_fn: Any,
    normalize_tracker_bid_ord_fn: Any,
    norm_text_fn: Any,
    load_seed_rows_from_artifact_path_fn: Any,
    score_related_notice_match_fn: Any,
    load_notice_seed_row_by_bid_fn: Any,
    repository_error_fn: Any,
) -> dict[str, str] | None:
    artifact_repository = get_artifact_repository_fn()
    target_bid_no = str((project.get("source_json") or {}).get("source_bid_no") or "").strip().upper()
    target_bid_ord = normalize_tracker_bid_ord_fn((project.get("source_json") or {}).get("source_bid_ord") or "000")
    target_issuer = norm_text_fn(str(project.get("issuer_name") or "").strip())
    best_rank: tuple[int, int, int, int, int, str, str] | None = None
    best_row: dict[str, str] | None = None
    for run_row in project_source_runs_fn(project):
        run_id = run_row.get("id")
        if run_id is None:
            continue
        try:
            artifacts = artifact_repository.list_artifacts(run_id=UUID(str(run_id)))
        except ArtifactRepositoryError as exc:
            repository_error_fn(str(exc))
        run_updated_at = str(run_row.get("updated_at") or run_row.get("created_at") or "")
        for artifact in artifacts:
            if str(artifact.get("artifact_type") or "") != "seed_csv":
                continue
            storage_path = str(artifact.get("storage_path") or "").strip()
            if not storage_path:
                continue
            for row in load_seed_rows_from_artifact_path_fn(storage_path):
                score, _candidate_search_name, _reason = score_related_notice_match_fn(project, row)
                if score < 20:
                    continue
                bid_no = str(row.get("bid_no") or "").strip().upper()
                bid_ord = normalize_tracker_bid_ord_fn(row.get("bid_ord") or "000") if bid_no else ""
                issuer_match = 1 if target_issuer and target_issuer in norm_text_fn(str(row.get("org_name") or "").strip()) else 0
                rank = (
                    1 if target_bid_no and bid_no == target_bid_no and bid_ord == target_bid_ord else 0,
                    score,
                    issuer_match,
                    1 if str(row.get("bid_ntce_dtl_url") or "").strip() else 0,
                    1 if str(row.get("bid_ntce_url") or "").strip() else 0,
                    str(row.get("announce_date") or "").strip(),
                    run_updated_at,
                )
                if best_rank is None or rank > best_rank:
                    best_rank = rank
                    best_row = row
    if best_row is None and target_bid_no:
        best_row = load_notice_seed_row_by_bid_fn(bid_no=target_bid_no, bid_ord=target_bid_ord)
    return best_row


def select_tracker_entry_source_notice_row(
    entry: dict[str, Any],
    *,
    coerce_uuid_or_none_fn: Any,
    derive_tracker_entry_bid_identity_fn: Any,
    get_artifact_repository_fn: Any,
    load_seed_rows_from_artifact_path_fn: Any,
    normalize_tracker_bid_ord_fn: Any,
    load_notice_seed_row_by_bid_fn: Any,
    repository_error_fn: Any,
) -> dict[str, str] | None:
    source_run_id = coerce_uuid_or_none_fn(entry.get("source_run_id"))
    if source_run_id is None:
        return None
    target_bid_no, target_bid_ord = derive_tracker_entry_bid_identity_fn(entry)
    if not target_bid_no:
        return None
    artifact_repository = get_artifact_repository_fn()
    try:
        artifacts = artifact_repository.list_artifacts(run_id=source_run_id)
    except ArtifactRepositoryError as exc:
        repository_error_fn(str(exc))
        return None
    for artifact in artifacts:
        if str(artifact.get("artifact_type") or "").strip() != "seed_csv":
            continue
        storage_path = str(artifact.get("storage_path") or "").strip()
        if not storage_path:
            continue
        for row in load_seed_rows_from_artifact_path_fn(storage_path):
            bid_no = str(row.get("bid_no") or "").strip().upper()
            if bid_no != target_bid_no:
                continue
            bid_ord = normalize_tracker_bid_ord_fn(row.get("bid_ord") or "000")
            if bid_ord == target_bid_ord:
                return row
    return load_notice_seed_row_by_bid_fn(bid_no=target_bid_no, bid_ord=target_bid_ord)


_dedupe_related_notice_rows = dedupe_related_notice_rows
_project_source_runs = project_source_runs
_project_source_notice_keys = project_source_notice_keys
_filter_self_related_notice_payload_items = filter_self_related_notice_payload_items
_is_related_notice_payload_entry_precomputed = is_related_notice_payload_entry_precomputed
_seed_related_notice_items = seed_related_notice_items
_precomputed_related_notice_items = precomputed_related_notice_items
_select_project_source_notice_row = select_project_source_notice_row
_select_tracker_entry_source_notice_row = select_tracker_entry_source_notice_row
