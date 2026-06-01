from __future__ import annotations

from typing import Any
from uuid import UUID
from uuid import uuid5


def normalize_tracker_bid_ord(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "000"
    if raw.isdigit():
        return f"{int(raw):03d}"
    return raw


def derive_tracker_entry_bid_identity(entry: dict[str, Any], *, normalize_tracker_bid_ord_fn: Any) -> tuple[str, str]:
    bid_no = str(entry.get("source_bid_no") or "").strip().upper()
    bid_ord_raw = entry.get("source_bid_ord") or "000"
    if not bid_no:
        entry_key = str(entry.get("entry_key") or "").strip()
        bid_part, sep, remainder = entry_key.partition("|")
        if sep and bid_part.strip():
            bid_no = bid_part.strip().upper()
            ord_part, sep2, _ = remainder.partition("|")
            if sep2 and ord_part.strip():
                bid_ord_raw = ord_part.strip()
    return bid_no, normalize_tracker_bid_ord_fn(bid_ord_raw)


def coerce_uuid_or_none(value: Any) -> UUID | None:
    if isinstance(value, UUID):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return UUID(text)
    except Exception:
        return None


def derive_tracker_entry_project_identity(
    entry: dict[str, Any],
    *,
    select_project_search_name: Any,
    project_match_key: Any,
) -> tuple[str, str, str]:
    project_name = str(entry.get("project_name") or "").strip()
    source_project_name_norm = str(entry.get("source_project_name_norm") or "").strip()
    project_search_name = select_project_search_name(project_name, source_project_name_norm)
    project_key = project_match_key(project_search_name or project_name or source_project_name_norm)
    return project_name, project_search_name, project_key


def upsert_project_aggregate_from_tracker_entry(
    aggregates: dict[str, dict[str, Any]],
    entry: dict[str, Any],
    *,
    project_namespace: UUID,
    derive_tracker_entry_project_identity_fn: Any,
    normalize_tracker_bid_ord_fn: Any,
    slugify: Any,
    better_project_label: Any,
    better_project_search_name: Any,
    utc_now: Any,
) -> None:
    project_name, project_search_name, key = derive_tracker_entry_project_identity_fn(entry)
    if not project_name or not key:
        return
    created_at = entry.get("created_at") or utc_now()
    updated_at = entry.get("updated_at") or created_at
    entry_bid_no = str(entry.get("source_bid_no") or "").strip().upper()
    entry_bid_ord = normalize_tracker_bid_ord_fn(entry.get("source_bid_ord") or "000") if entry_bid_no else ""
    item = aggregates.setdefault(
        key,
        {
            "id": uuid5(project_namespace, f"project:{key}"),
            "project_name": project_name,
            "project_name_norm": slugify(project_search_name or project_name),
            "project_search_name": project_search_name,
            "issuer_name": str(entry.get("demand_org_name") or "").strip(),
            "first_notice_date": str(entry.get("notice_date") or "").strip(),
            "latest_notice_date": str(entry.get("notice_date") or "").strip(),
            "latest_notice_title": project_name,
            "source_json": {
                "run_ids": [str(entry.get("source_run_id") or "")] if entry.get("source_run_id") else [],
                "winner_csv_rows": 0,
                "tracker_entry_rows": 0,
                "source_bid_no": entry_bid_no,
                "source_bid_ord": entry_bid_ord,
            },
            "created_at": created_at,
            "updated_at": updated_at,
            "_project_match_key": key,
        },
    )
    item["project_name"] = better_project_label(item.get("project_name") or "", project_name)
    item["project_search_name"] = better_project_search_name(item.get("project_search_name") or "", project_search_name)
    item["source_json"]["tracker_entry_rows"] = int(item["source_json"].get("tracker_entry_rows") or 0) + 1
    source_run_id = str(entry.get("source_run_id") or "").strip()
    if source_run_id and source_run_id not in item["source_json"]["run_ids"]:
        item["source_json"]["run_ids"].append(source_run_id)
    if not str(item["source_json"].get("source_bid_no") or "").strip() and entry_bid_no:
        item["source_json"]["source_bid_no"] = entry_bid_no
        item["source_json"]["source_bid_ord"] = entry_bid_ord
    entry_notice_date = str(entry.get("notice_date") or "").strip()
    if entry_notice_date and (
        not str(item.get("first_notice_date") or "").strip()
        or entry_notice_date < str(item.get("first_notice_date") or "").strip()
    ):
        item["first_notice_date"] = entry_notice_date
    if str(entry.get("notice_date") or "").strip() >= str(item.get("latest_notice_date") or ""):
        item["latest_notice_date"] = str(entry.get("notice_date") or "").strip()
        item["latest_notice_title"] = project_name
        if entry_bid_no:
            item["source_json"]["source_bid_no"] = entry_bid_no
            item["source_json"]["source_bid_ord"] = entry_bid_ord
    if str(entry.get("demand_org_name") or "").strip():
        item["issuer_name"] = str(entry.get("demand_org_name") or "").strip()
    if updated_at > item["updated_at"]:
        item["updated_at"] = updated_at


def build_project_aggregates(
    *,
    collect_all_runs: Any,
    collect_all_tracker_entries: Any,
    is_project_tracker_run_type: Any,
    project_search_name: Any,
    is_generic_project_term: Any,
    project_match_key: Any,
    normalize_tracker_bid_ord_fn: Any,
    upsert_project_aggregate_from_tracker_entry_fn: Any,
    slugify: Any,
    better_project_label: Any,
    better_project_search_name: Any,
    project_namespace: UUID,
    utc_now: Any,
) -> dict[str, dict[str, Any]]:
    runs = collect_all_runs()
    entries = collect_all_tracker_entries()
    aggregates: dict[str, dict[str, Any]] = {}

    for run in runs:
        if not is_project_tracker_run_type(str(run.get("run_type") or "")):
            continue
        if str(run.get("status") or "") != "success":
            continue
        params = dict(run.get("params_json") or {})
        summary = dict((run.get("summary_json") or {}).get("output") or {})
        project_name_value = str(params.get("notice_title") or params.get("bid_no") or "").strip()
        if not project_name_value:
            continue
        project_search_name_value = project_search_name(project_name_value)
        if is_generic_project_term(project_search_name_value or project_name_value):
            continue
        key = project_match_key(project_search_name_value or project_name_value)
        if not key:
            continue
        created_at = run.get("created_at") or utc_now()
        updated_at = run.get("updated_at") or created_at
        item = aggregates.setdefault(
            key,
            {
                "id": uuid5(project_namespace, f"project:{key}"),
                "project_name": project_name_value,
                "project_name_norm": slugify(project_search_name_value or project_name_value),
                "project_search_name": project_search_name_value,
                "issuer_name": str(params.get("demand_org") or "").strip(),
                "first_notice_date": str(params.get("start_date") or "").strip(),
                "latest_notice_date": str(params.get("end_date") or "").strip(),
                "latest_notice_title": project_name_value,
                "source_json": {
                    "run_ids": [str(run["id"])],
                    "winner_csv_rows": int(summary.get("winner_csv_rows") or 0),
                    "tracker_entry_rows": 0,
                    "source_bid_no": str(params.get("bid_no") or "").strip().upper(),
                    "source_bid_ord": normalize_tracker_bid_ord_fn(params.get("bid_ord") or "000")
                    if str(params.get("bid_no") or "").strip()
                    else "",
                },
                "created_at": created_at,
                "updated_at": updated_at,
                "_project_match_key": key,
            },
        )
        item["project_name"] = better_project_label(item.get("project_name") or "", project_name_value)
        item["project_search_name"] = better_project_search_name(
            item.get("project_search_name") or "",
            project_search_name_value,
        )
        if str(run["id"]) not in item["source_json"]["run_ids"]:
            item["source_json"]["run_ids"].append(str(run["id"]))
        item["source_json"]["winner_csv_rows"] = max(
            int(item["source_json"].get("winner_csv_rows") or 0),
            int(summary.get("winner_csv_rows") or 0),
        )
        run_start_date = str(params.get("start_date") or "").strip()
        if run_start_date and (
            not str(item.get("first_notice_date") or "").strip()
            or run_start_date < str(item.get("first_notice_date") or "").strip()
        ):
            item["first_notice_date"] = run_start_date
        if updated_at > item["updated_at"]:
            item["updated_at"] = updated_at

    for entry in entries:
        upsert_project_aggregate_from_tracker_entry_fn(aggregates, entry)
    return aggregates


def build_project_aggregate_from_tracker_entries(
    project_id: UUID,
    *,
    collect_all_tracker_entries: Any,
    upsert_project_aggregate_from_tracker_entry_fn: Any,
) -> dict[str, Any] | None:
    aggregates: dict[str, dict[str, Any]] = {}
    for entry in collect_all_tracker_entries():
        upsert_project_aggregate_from_tracker_entry_fn(aggregates, entry)
    for item in aggregates.values():
        if item["id"] == project_id:
            return item
    return None


def to_project_item(item: dict[str, Any], *, project_item_cls: Any, utc_now: Any) -> Any:
    return project_item_cls(
        id=item["id"],
        project_name=str(item.get("project_name") or ""),
        project_name_norm=str(item.get("project_name_norm") or ""),
        project_search_name=str(item.get("project_search_name") or ""),
        issuer_name=str(item.get("issuer_name") or ""),
        latest_notice_date=str(item.get("latest_notice_date") or ""),
        latest_notice_title=str(item.get("latest_notice_title") or ""),
        source_json=dict(item.get("source_json") or {}),
        created_at=item.get("created_at") or utc_now(),
        updated_at=item.get("updated_at") or utc_now(),
    )


def build_projects_page(
    *,
    page: int,
    page_size: int,
    q: str,
    build_project_aggregates_fn: Any,
    norm_text: Any,
    to_project_item_fn: Any,
) -> tuple[list[Any], int]:
    aggregates = build_project_aggregates_fn()
    items = list(aggregates.values())

    if q:
        q_norm = norm_text(q)
        items = [
            item for item in items
            if q_norm in norm_text(item["project_name"])
            or q_norm in norm_text(item.get("project_search_name") or "")
            or q_norm in norm_text(item["issuer_name"])
            or q_norm in norm_text(item["latest_notice_title"])
        ]
    items.sort(key=lambda item: item["updated_at"], reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start:start + page_size]
    return [to_project_item_fn(item) for item in page_items], total


def annotate_tracker_entries_with_project_refs(
    rows: list[dict[str, Any]],
    *,
    derive_tracker_entry_project_identity_fn: Any,
    project_namespace: UUID,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    enriched: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        _project_name, project_search_name, project_key = derive_tracker_entry_project_identity_fn(item)
        item["project_id"] = uuid5(project_namespace, f"project:{project_key}") if project_key else None
        item["project_search_name"] = project_search_name
        enriched.append(item)
    return enriched


def annotate_tracker_entries_with_opening_dates(
    rows: list[dict[str, Any]],
    *,
    get_artifact_repository: Any,
    artifact_repository_error_types: tuple[type[Exception], ...],
    load_seed_rows_from_artifact_path: Any,
    coerce_uuid_or_none_fn: Any,
    normalize_tracker_bid_ord_fn: Any,
) -> list[dict[str, Any]]:
    if not rows:
        return []

    try:
        artifact_repository = get_artifact_repository()
    except artifact_repository_error_types:
        return [dict(row, opening_scheduled_date=str(row.get("opening_scheduled_date") or "").strip()) for row in rows]
    seed_index_by_run: dict[UUID, dict[tuple[str, str], str]] = {}

    def load_run_seed_index(run_id: UUID) -> dict[tuple[str, str], str]:
        cached = seed_index_by_run.get(run_id)
        if cached is not None:
            return cached
        try:
            artifacts = artifact_repository.list_artifacts(run_id=run_id)
        except artifact_repository_error_types[1]:
            seed_index_by_run[run_id] = {}
            return seed_index_by_run[run_id]

        seed_artifact = next(
            (
                item for item in artifacts
                if str(item.get("artifact_type") or "").strip() == "seed_csv"
                or str(item.get("file_name") or "").strip() == "project_tracker_seed_input.csv"
            ),
            None,
        )
        if seed_artifact is None:
            seed_index_by_run[run_id] = {}
            return seed_index_by_run[run_id]

        storage_path = str(seed_artifact.get("storage_path") or "").strip()
        if not storage_path:
            seed_index_by_run[run_id] = {}
            return seed_index_by_run[run_id]

        index: dict[tuple[str, str], str] = {}
        for seed_row in load_seed_rows_from_artifact_path(storage_path):
            bid_no = str(seed_row.get("bid_no") or "").strip().upper()
            bid_ord = normalize_tracker_bid_ord_fn(seed_row.get("bid_ord") or "000")
            opening_scheduled_date = str(seed_row.get("opening_scheduled_date") or "").strip()
            if not bid_no or not opening_scheduled_date:
                continue
            index[(bid_no, bid_ord)] = opening_scheduled_date

        seed_index_by_run[run_id] = index
        return index

    enriched: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        opening_scheduled_date = str(item.get("opening_scheduled_date") or "").strip()
        source_run_id = coerce_uuid_or_none_fn(item.get("source_run_id"))
        bid_no = str(item.get("source_bid_no") or "").strip().upper()
        bid_ord = normalize_tracker_bid_ord_fn(item.get("source_bid_ord") or "000")
        if not opening_scheduled_date and source_run_id is not None and bid_no:
            seed_index = load_run_seed_index(source_run_id)
            opening_scheduled_date = str(seed_index.get((bid_no, bid_ord)) or "").strip()
        item["opening_scheduled_date"] = opening_scheduled_date
        enriched.append(item)
    return enriched
