from __future__ import annotations

from typing import Any

from .tracker_entries import TRACKER_REGION_FIELD_NAMES
from .tracker_entries import TRACKER_REGION_TOKEN_ONLY_CANONICALS
from .tracker_entries import TRACKER_USER_HIDDEN_TITLE_KEYWORDS
from .tracker_entries import get_tracker_region_aliases
from .tracker_entries import parse_tracker_regions

TRACKER_ENTRY_SELECT = ",".join(
    (
        "id",
        "organization_id",
        "source_run_id",
        "source_tracker_run_id",
        "entry_key",
        "sheet_name",
        "section_name",
        "row_no",
        "source_bid_no",
        "source_bid_ord",
        "source_project_name_norm",
        "project_name",
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
        "overridden_fields",
        "has_overrides",
        "last_edited_at",
        "last_edited_by",
        "last_edited_by_label",
        "created_at",
        "updated_at",
    )
)
TRACKER_ENTRY_SUMMARY_SELECT = ",".join(
    (
        "id",
        "organization_id",
        "source_run_id",
        "source_tracker_run_id",
        "entry_key",
        "row_no",
        "project_name",
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
        "building_automation_estimated_amount",
        "overridden_fields",
        "has_overrides",
    )
)
TRACKER_ENTRY_EXPORT_SELECT = ",".join(
    (
        "id",
        "organization_id",
        "source_run_id",
        "entry_key",
        "source_bid_no",
        "source_bid_ord",
        "source_project_name_norm",
        "project_name",
        "gross_area_scale",
        "construction_cost",
        "demand_org_name",
        "demand_contact",
        "client_location",
        "site_location_1",
        "site_location_2",
        "architect_office",
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
)
TRACKER_EFFECTIVE_EXTENDED_FIELDS = (
    "contract_date",
    "construction_duration_days",
    "completion_expected_date_explicit",
    "completion_expected_date_computed",
)
TRACKER_SOURCE_EXTENDED_FIELDS = tuple(f"{field_name}_source" for field_name in TRACKER_EFFECTIVE_EXTENDED_FIELDS)
TRACKER_ENTRY_SELECT_LEGACY = ",".join(
    field_name
    for field_name in TRACKER_ENTRY_SELECT.split(",")
    if field_name not in TRACKER_EFFECTIVE_EXTENDED_FIELDS
)
TRACKER_ENTRY_SUMMARY_SELECT_LEGACY = ",".join(
    field_name
    for field_name in TRACKER_ENTRY_SUMMARY_SELECT.split(",")
    if field_name not in TRACKER_EFFECTIVE_EXTENDED_FIELDS
)
TRACKER_ENTRY_EXPORT_SELECT_LEGACY = ",".join(
    field_name
    for field_name in TRACKER_ENTRY_EXPORT_SELECT.split(",")
    if field_name not in TRACKER_EFFECTIVE_EXTENDED_FIELDS
)
TRACKER_AUDIT_LOG_SELECT = ",".join(
    (
        "id",
        "field_name",
        "old_value",
        "new_value",
        "actor_user_id",
        "actor_label",
        "change_source",
        "created_at",
    )
)
TRACKER_PROJECT_NAME_SEARCH_FIELD = "project_name"


def sanitize_ilike_term(value: str) -> str:
    sanitized = value.strip().replace(",", " ").replace("(", " ").replace(")", " ")
    sanitized = sanitized.replace("%", "").replace("*", "")
    return " ".join(sanitized.split())


def escape_postgrest_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace(",", "\\,").replace(")", "\\)")


def build_region_or_clause(region: str) -> str:
    canonicals = parse_tracker_regions(region)
    if not canonicals:
        return ""
    conditions: list[str] = []
    seen: set[str] = set()
    for canonical in canonicals:
        aliases = get_tracker_region_aliases(canonical)
        for alias in aliases:
            search_term = sanitize_ilike_term(alias)
            if not search_term:
                continue
            escaped = escape_postgrest_literal(search_term)
            for field_name in TRACKER_REGION_FIELD_NAMES:
                if alias == canonical and canonical in TRACKER_REGION_TOKEN_ONLY_CANONICALS:
                    next_conditions = (
                        f"{field_name}.eq.{escaped}",
                        f"{field_name}.ilike.{escaped} *",
                        f"{field_name}.ilike.* {escaped}",
                        f"{field_name}.ilike.* {escaped} *",
                    )
                else:
                    next_conditions = (f"{field_name}.ilike.*{escaped}*",)
                for condition in next_conditions:
                    if condition in seen:
                        continue
                    seen.add(condition)
                    conditions.append(condition)
    if not conditions:
        return ""
    return f"({','.join(conditions)})"


def build_exclude_auxiliary_titles_clause(enabled: bool) -> str:
    if not enabled:
        return ""
    conditions: list[str] = []
    for keyword in TRACKER_USER_HIDDEN_TITLE_KEYWORDS:
        search_term = sanitize_ilike_term(keyword)
        if not search_term:
            continue
        escaped = escape_postgrest_literal(search_term)
        conditions.append(f"project_name.not.ilike.*{escaped}*")
    if not conditions:
        return ""
    return f"({','.join(conditions)})"


def normalize_entry(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    for field_name in TRACKER_EFFECTIVE_EXTENDED_FIELDS:
        normalized.setdefault(field_name, "")
    normalized["overridden_fields"] = list(normalized.get("overridden_fields") or [])
    normalized.pop("has_overrides", None)
    return normalized


def normalize_audit_log(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized["id"] = int(normalized["id"])
    return normalized


def parse_total_count(headers: dict[str, str], *, fallback: int) -> int:
    content_range = headers.get("Content-Range", "")
    if "/" not in content_range:
        return fallback
    total = content_range.rsplit("/", 1)[-1].strip()
    if not total or total == "*":
        return fallback
    try:
        return int(total)
    except ValueError:
        return fallback


def effective_select_clause(select_clause: str, *, supports_effective_extended_fields: bool) -> str:
    if supports_effective_extended_fields:
        return select_clause
    return legacy_select_clause(select_clause)


def legacy_select_clause(select_clause: str) -> str:
    if select_clause == TRACKER_ENTRY_SELECT:
        return TRACKER_ENTRY_SELECT_LEGACY
    if select_clause == TRACKER_ENTRY_SUMMARY_SELECT:
        return TRACKER_ENTRY_SUMMARY_SELECT_LEGACY
    if select_clause == TRACKER_ENTRY_EXPORT_SELECT:
        return TRACKER_ENTRY_EXPORT_SELECT_LEGACY
    fields = [
        field_name
        for field_name in select_clause.split(",")
        if field_name not in TRACKER_EFFECTIVE_EXTENDED_FIELDS
    ]
    return ",".join(fields)


def replace_select_clause(query: list[tuple[str, str]], select_clause: str) -> list[tuple[str, str]]:
    replaced = list(query)
    for index, (key, _value) in enumerate(replaced):
        if key == "select":
            replaced[index] = ("select", select_clause)
            break
    return replaced


def is_missing_extended_column_error(message: str) -> bool:
    lowered = str(message or "").lower()
    return any(
        field_name in lowered and any(token in lowered for token in ("column", "schema cache", "does not exist"))
        for field_name in TRACKER_EFFECTIVE_EXTENDED_FIELDS
    )


def is_missing_extended_source_column_error(message: str) -> bool:
    lowered = str(message or "").lower()
    return any(
        field_name in lowered and any(token in lowered for token in ("column", "schema cache", "does not exist"))
        for field_name in TRACKER_SOURCE_EXTENDED_FIELDS
    )
