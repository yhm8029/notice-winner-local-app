from __future__ import annotations

from datetime import date
from typing import Any


TRACKER_GLOBAL_MERGE_FIELDS = (
    "gross_area_scale",
    "construction_cost",
    "demand_org_name",
    "demand_contact",
    "client_location",
    "site_location_1",
    "site_location_2",
    "architect_office",
    "opening_scheduled_date",
    "construction_start_date",
    "contract_date",
    "construction_duration_days",
    "completion_expected_date_explicit",
    "completion_expected_date_computed",
    "last_checked_date",
    "progress_note",
    "notice_date",
    "manager_name",
    "building_automation_estimated_amount",
)


def _build_tracker_row_search_bucket(row: dict[str, Any]) -> str:
    search_bucket = " ".join(
        value
        for value in row.get("_search_texts") or []
        if str(value or "").strip()
    )
    return " ".join(
        filter(
            None,
            (
                search_bucket,
                str(row.get("demand_org_name") or "").strip(),
                str(row.get("architect_office") or "").strip(),
                str(row.get("site_location_1") or "").strip(),
                str(row.get("demand_contact") or "").strip(),
            ),
        )
    )


def tracker_row_merge_score(row: dict[str, Any]) -> tuple[int, int, int, int]:
    weighted = 0
    for field_name, weight in (
        ("architect_office", 5),
        ("demand_contact", 5),
        ("gross_area_scale", 4),
        ("construction_cost", 4),
        ("site_location_1", 3),
        ("demand_org_name", 3),
        ("opening_scheduled_date", 2),
        ("construction_start_date", 2),
        ("building_automation_estimated_amount", 2),
        ("progress_note", 1),
    ):
        if str(row.get(field_name) or "").strip():
            weighted += weight
    return (
        weighted,
        len(str(row.get("project_name") or "").strip()),
        len(str(row.get("entry_key") or "").strip()),
        1 if row.get("has_overrides") or row.get("overridden_fields") else 0,
    )


def tracker_row_merge_identity(
    row: dict[str, Any],
    *,
    normalize_tracker_bid_ord_fn: Any,
    norm_text_fn: Any,
) -> tuple[str, str, str]:
    bid_no = str(row.get("source_bid_no") or "").strip().upper()
    bid_ord = normalize_tracker_bid_ord_fn(row.get("source_bid_ord") or "000") if bid_no else ""
    if bid_no:
        return ("bid", bid_no, bid_ord)

    source_project_name_norm = norm_text_fn(str(row.get("source_project_name_norm") or "").strip())
    if source_project_name_norm:
        return ("project", source_project_name_norm, "")

    entry_key = norm_text_fn(str(row.get("entry_key") or "").strip())
    if entry_key:
        return ("entry", entry_key, "")

    project_name = norm_text_fn(str(row.get("project_name") or "").strip())
    return ("name", project_name, "")


def merge_global_tracker_row_group(
    rows: list[dict[str, Any]],
    *,
    tracker_row_merge_score_fn: Any,
    tracker_row_merge_identity_fn: Any,
    better_project_label_fn: Any,
) -> dict[str, Any]:
    ordered = sorted(
        rows,
        key=lambda row: (
            tracker_row_merge_score_fn(row),
            str(row.get("updated_at") or ""),
            str(row.get("notice_date") or ""),
            str(row.get("id") or ""),
        ),
        reverse=True,
    )
    merged = dict(ordered[0])
    merged_identity = tracker_row_merge_identity_fn(merged)
    project_name = str(merged.get("project_name") or "").strip()
    merged["_search_texts"] = [
        str(merged.get("project_name") or "").strip(),
        str(merged.get("entry_key") or "").strip(),
        str(merged.get("source_project_name_norm") or "").strip(),
    ]
    overridden_fields = set(str(value or "").strip() for value in merged.get("overridden_fields") or [] if str(value or "").strip())
    for row in ordered[1:]:
        if tracker_row_merge_identity_fn(row) != merged_identity:
            continue
        project_name = better_project_label_fn(project_name, str(row.get("project_name") or "").strip())
        merged["updated_at"] = max(str(merged.get("updated_at") or ""), str(row.get("updated_at") or ""))
        if str(row.get("created_at") or "") and (
            not str(merged.get("created_at") or "") or str(row.get("created_at") or "") < str(merged.get("created_at") or "")
        ):
            merged["created_at"] = row.get("created_at")
        for field_name in TRACKER_GLOBAL_MERGE_FIELDS:
            if str(merged.get(field_name) or "").strip():
                continue
            candidate = str(row.get(field_name) or "").strip()
            if candidate:
                merged[field_name] = candidate
        for field_name in ("project_name", "entry_key", "source_project_name_norm"):
            candidate = str(row.get(field_name) or "").strip()
            if candidate:
                merged["_search_texts"].append(candidate)
        overridden_fields.update(
            str(value or "").strip()
            for value in row.get("overridden_fields") or []
            if str(value or "").strip()
        )
    merged["project_name"] = project_name
    merged["overridden_fields"] = sorted(overridden_fields)
    merged["has_overrides"] = bool(merged["overridden_fields"] or merged.get("has_overrides"))
    return merged


def collapse_tracker_rows_by_project(
    rows: list[dict[str, Any]],
    *,
    derive_tracker_entry_project_identity_fn: Any,
    norm_text_fn: Any,
    merge_global_tracker_row_group_fn: Any,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    passthrough: list[dict[str, Any]] = []
    for row in rows:
        project_id = str(row.get("project_id") or "").strip()
        if project_id:
            grouped.setdefault(project_id, []).append(row)
            continue
        project_name, project_search_name, project_key = derive_tracker_entry_project_identity_fn(row)
        fallback_key = project_key or norm_text_fn(project_search_name or project_name)
        if fallback_key:
            grouped.setdefault(f"fallback:{fallback_key}", []).append(row)
        else:
            passthrough.append(dict(row))
    collapsed = [merge_global_tracker_row_group_fn(group) for group in grouped.values()]
    collapsed.extend(passthrough)
    for row in collapsed:
        row["_search_text_norm"] = norm_text_fn(_build_tracker_row_search_bucket(row))
    collapsed.sort(key=lambda row: (str(row.get("updated_at") or ""), str(row.get("id") or "")), reverse=True)
    return collapsed


def _tracker_global_scope_default_order_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("opening_scheduled_date") or "").strip(),
        str(row.get("updated_at") or "").strip(),
        str(row.get("id") or "").strip(),
    )


def _tracker_global_scope_default_opening_date_sort_key(row: dict[str, Any]) -> tuple[int, int]:
    raw_value = str(row.get("opening_scheduled_date") or "").strip()
    if not raw_value:
        return (1, 0)
    parsed_date: date | None = None
    if len(raw_value) == 8 and raw_value.isdigit():
        try:
            parsed_date = date(int(raw_value[0:4]), int(raw_value[4:6]), int(raw_value[6:8]))
        except ValueError:
            parsed_date = None
    else:
        try:
            parsed_date = date.fromisoformat(raw_value)
        except ValueError:
            parsed_date = None
    if parsed_date is None:
        return (1, 0)
    return (0, -parsed_date.toordinal())


def filter_tracker_rows_for_global_scope(
    rows: list[dict[str, Any]],
    *,
    q: str,
    region: str,
    exclude_auxiliary_titles: bool,
    edited_only: bool,
    norm_text_fn: Any,
    tracker_entry_matches_title_visibility_fn: Any,
    tracker_entry_matches_region_fn: Any,
) -> list[dict[str, Any]]:
    q_norm = norm_text_fn(q)
    filtered: list[dict[str, Any]] = []
    for row in rows:
        if edited_only and not (row.get("has_overrides") or row.get("overridden_fields")):
            continue
        if not tracker_entry_matches_title_visibility_fn(row, exclude_auxiliary_titles=exclude_auxiliary_titles):
            continue
        if not tracker_entry_matches_region_fn(row, region):
            continue
        if q_norm:
            search_text_norm = str(row.get("_search_text_norm") or "").strip()
            if not search_text_norm:
                search_text_norm = norm_text_fn(_build_tracker_row_search_bucket(row))
            if q_norm not in search_text_norm:
                continue
        filtered.append(dict(row))
    filtered.sort(key=lambda row: str(row.get("id") or ""), reverse=True)
    filtered.sort(key=lambda row: str(row.get("updated_at") or ""), reverse=True)
    filtered.sort(key=_tracker_global_scope_default_opening_date_sort_key)
    return filtered
