from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from backend.repositories import TrackerEntrySnapshotRepositoryError
from backend.repositories.tracker_entries import coerce_tracker_override_value
from backend.repositories.tracker_entries import estimate_tracker_building_automation_amount
from backend.repositories.tracker_entries import format_tracker_cost_display
from backend.repositories.tracker_entries import format_tracker_display_date
from backend.repositories.tracker_entries import is_legacy_tracker_building_automation_estimate
from backend.services.native_gui_rules import is_auxiliary_service_project
from backend.services.native_tracker_backend import normalize_tracker_site_locations
from backend.services.tracker_diagnostic_backend import winner_row_has_allowed_source_signal


def _should_prefer_contract_construction_start(
    entry: dict[str, Any],
    winner_row: dict[str, str] | None,
) -> bool:
    architect_office = str(entry.get("architect_office") or "").strip()
    if not architect_office or architect_office in {"-", "확인필요"}:
        return False
    contract_reference_date = str((winner_row or {}).get("contract_date") or "").strip() or str(
        (winner_row or {}).get("construction_start_date") or ""
    ).strip()
    if not contract_reference_date:
        return False
    if not winner_row_has_allowed_source_signal(winner_row):
        return False
    duration_days = str((winner_row or {}).get("construction_duration_days") or "").strip()
    current = re.sub(r"\s+", "", str(entry.get("construction_start_date") or "").strip())
    if not current:
        return bool(duration_days)
    return current.startswith(("착수일로부터", "착공일로부터", "계약일"))


def _should_format_contract_period_from_entry(entry: dict[str, Any]) -> bool:
    architect_office = str(entry.get("architect_office") or "").strip()
    if not architect_office or architect_office in {"-", "확인필요"}:
        return False
    contract_date = str(entry.get("last_checked_date") or "").strip()
    if not contract_date:
        return False
    current = re.sub(r"\s+", "", str(entry.get("construction_start_date") or "").strip())
    if not current.startswith(("착수일로부터", "착공일로부터")):
        return False
    progress_note = str(entry.get("progress_note") or "").upper()
    return any(
        signal in progress_note
        for signal in ("EAIS_CONTRACT", "LOFIN_CONTRACT", "G2B_CONTRACT", "HUB_CONTRACT", "CONTRACT_MATCH")
    )


def normalize_tracker_entry_presentation(
    entry: dict[str, Any],
    *,
    winner_row: dict[str, str] | None,
) -> dict[str, Any]:
    normalized = dict(entry)
    project_name = str(normalized.get("project_name") or "").strip()
    raw_cost = str(normalized.get("construction_cost") or "").strip()
    current_estimated_amount = str(normalized.get("building_automation_estimated_amount") or "").strip()
    normalized["construction_cost"] = format_tracker_cost_display(raw_cost)
    normalized["last_checked_date"] = format_tracker_display_date(normalized.get("last_checked_date"))
    if (
        (
            not current_estimated_amount
            or (raw_cost and is_legacy_tracker_building_automation_estimate(current_estimated_amount))
        )
        and not is_auxiliary_service_project(project_name)
    ):
        normalized["building_automation_estimated_amount"] = estimate_tracker_building_automation_amount(raw_cost)
    if _should_format_contract_period_from_entry(normalized):
        formatted_period = coerce_tracker_override_value(
            field_name="construction_start_date",
            new_value=str(normalized.get("last_checked_date") or "").strip(),
            current_effective_value=str(normalized.get("construction_start_date") or "").strip(),
        )
        normalized["construction_start_date"] = str(formatted_period or normalized.get("construction_start_date") or "").strip()
    if _should_prefer_contract_construction_start(normalized, winner_row):
        contract_date = str((winner_row or {}).get("contract_date") or "").strip() or str(
            (winner_row or {}).get("construction_start_date") or ""
        ).strip()
        current_start = str(normalized.get("construction_start_date") or "").strip()
        formatted_period = coerce_tracker_override_value(
            field_name="construction_start_date",
            new_value=contract_date,
            current_effective_value=current_start,
            source_value=str((winner_row or {}).get("construction_duration_days") or "").strip(),
        )
        if formatted_period and formatted_period != contract_date:
            normalized["construction_start_date"] = str(formatted_period).strip()
        elif current_start and current_start != contract_date:
            normalized["construction_start_date"] = current_start
        else:
            normalized["construction_start_date"] = ""
    site_region, site_city = normalize_tracker_site_locations(
        current_site_region=str(normalized.get("site_location_1") or "").strip(),
        current_site_city=str(normalized.get("site_location_2") or "").strip(),
        current_client_location=str(normalized.get("client_location") or "").strip(),
        demand_org_name=str(normalized.get("demand_org_name") or "").strip(),
        project_name=project_name,
    )
    normalized["site_location_1"] = site_region
    normalized["site_location_2"] = site_city
    return normalized


def normalize_tracker_rows_for_presentation(
    rows: list[dict[str, Any]],
    *,
    lookup_winner_row_for_entry_fn: Any,
) -> list[dict[str, Any]]:
    winner_cache: dict[Any, Any] = {}
    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        winner_row = lookup_winner_row_for_entry_fn(row, winner_cache)
        normalized_rows.append(normalize_tracker_entry_presentation(row, winner_row=winner_row))
    return normalized_rows


def materialize_tracker_entry_snapshot_views(
    rows: list[dict[str, Any]],
    *,
    annotate_tracker_entries_with_project_refs_fn: Any,
    annotate_tracker_entries_with_opening_dates_fn: Any,
    annotate_tracker_entries_with_field_diagnostics_fn: Any,
    normalize_tracker_rows_for_presentation_fn: Any,
    coerce_uuid_or_none_fn: Any,
    model_to_json_dict_fn: Any,
    to_tracker_entry_summary_model_fn: Any,
    to_tracker_entry_model_fn: Any,
    tracking_export_fieldnames: tuple[str, ...],
    utc_now_fn: Any,
) -> dict[str, dict[str, Any]]:
    if not rows:
        return {}
    project_rows = annotate_tracker_entries_with_project_refs_fn(rows)
    opening_rows = annotate_tracker_entries_with_opening_dates_fn(project_rows)
    summary_rows = normalize_tracker_rows_for_presentation_fn(opening_rows)
    detail_source_rows = annotate_tracker_entries_with_field_diagnostics_fn(opening_rows)
    detail_rows = normalize_tracker_rows_for_presentation_fn(detail_source_rows)

    materialized: dict[str, dict[str, Any]] = {}
    for raw_row, summary_row, detail_row in zip(rows, summary_rows, detail_rows):
        entry_id = coerce_uuid_or_none_fn(raw_row.get("id"))
        if entry_id is None:
            continue
        export_row = {
            field_name: str(detail_row.get(field_name, "") or "")
            for field_name in tracking_export_fieldnames
        }
        summary_json = model_to_json_dict_fn(to_tracker_entry_summary_model_fn(summary_row))
        detail_json = model_to_json_dict_fn(to_tracker_entry_model_fn(detail_row))
        materialized[str(entry_id)] = {
            "summary_row": summary_json,
            "detail_row": detail_json,
            "export_row": export_row,
            "snapshot": {
                "tracker_entry_id": entry_id,
                "updated_at": raw_row.get("updated_at") or raw_row.get("created_at") or utc_now_fn(),
                "summary_json": summary_json,
                "detail_json": detail_json,
                "export_json": export_row,
            },
        }
    return materialized


def is_tracker_entry_snapshot_fresh(
    snapshot: dict[str, Any],
    row: dict[str, Any],
    *,
    parse_iso_datetime_fn: Any,
) -> bool:
    snapshot_updated_at = parse_iso_datetime_fn(snapshot.get("updated_at"))
    row_updated_at = parse_iso_datetime_fn(row.get("updated_at") or row.get("created_at"))
    if snapshot_updated_at is None:
        return False
    if row_updated_at is None:
        return True
    return snapshot_updated_at >= row_updated_at


def load_tracker_entry_snapshot_map(
    *,
    organization_id: UUID,
    rows: list[dict[str, Any]],
    coerce_uuid_or_none_fn: Any,
    get_tracker_entry_snapshot_repository_fn: Any,
) -> dict[str, dict[str, Any]]:
    tracker_entry_ids = [
        tracker_entry_id
        for tracker_entry_id in (coerce_uuid_or_none_fn(row.get("id")) for row in rows)
        if tracker_entry_id is not None
    ]
    if not tracker_entry_ids:
        return {}
    try:
        repository = get_tracker_entry_snapshot_repository_fn()
        snapshots = repository.get_snapshots(
            organization_id=organization_id,
            tracker_entry_ids=tracker_entry_ids,
        )
    except TrackerEntrySnapshotRepositoryError:
        return {}
    return {
        str(item.get("tracker_entry_id") or "").strip(): dict(item)
        for item in snapshots
        if str(item.get("tracker_entry_id") or "").strip()
    }


def upsert_tracker_entry_snapshots_best_effort(
    *,
    organization_id: UUID,
    rows: list[dict[str, Any]],
    get_tracker_entry_snapshot_repository_fn: Any,
    materialize_tracker_entry_snapshot_views_fn: Any,
    materialized: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    if not rows:
        return materialized or {}
    prepared = materialized if materialized is not None else materialize_tracker_entry_snapshot_views_fn(rows)
    payloads = [dict(item.get("snapshot") or {}) for item in prepared.values() if item.get("snapshot")]
    if not payloads:
        return prepared
    try:
        get_tracker_entry_snapshot_repository_fn().upsert_snapshots(
            organization_id=organization_id,
            snapshots=payloads,
        )
    except TrackerEntrySnapshotRepositoryError:
        return prepared
    return prepared


def hydrate_tracker_entry_summary_rows(
    *,
    organization_id: UUID,
    rows: list[dict[str, Any]],
    load_tracker_entry_snapshot_map_fn: Any,
    is_tracker_entry_snapshot_fresh_fn: Any,
    upsert_tracker_entry_snapshots_best_effort_fn: Any,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    snapshot_map = load_tracker_entry_snapshot_map_fn(organization_id=organization_id, rows=rows)
    hydrated: list[dict[str, Any] | None] = [None] * len(rows)
    missing_rows: list[dict[str, Any]] = []
    missing_indexes: list[int] = []
    for index, row in enumerate(rows):
        tracker_entry_id = str(row.get("id") or "").strip()
        snapshot = snapshot_map.get(tracker_entry_id)
        summary_json = dict((snapshot or {}).get("summary_json") or {})
        if snapshot and summary_json and is_tracker_entry_snapshot_fresh_fn(snapshot, row):
            merged = dict(row)
            merged.update(summary_json)
            hydrated[index] = merged
            continue
        missing_rows.append(dict(row))
        missing_indexes.append(index)
    if missing_rows:
        materialized = upsert_tracker_entry_snapshots_best_effort_fn(
            organization_id=organization_id,
            rows=missing_rows,
        )
        for index, row in zip(missing_indexes, missing_rows):
            tracker_entry_id = str(row.get("id") or "").strip()
            merged = dict(row)
            merged.update(dict((materialized.get(tracker_entry_id) or {}).get("summary_row") or {}))
            hydrated[index] = merged
    return [dict(item or {}) for item in hydrated]


def hydrate_tracker_entry_export_rows(
    *,
    organization_id: UUID,
    rows: list[dict[str, Any]],
    load_tracker_entry_snapshot_map_fn: Any,
    is_tracker_entry_snapshot_fresh_fn: Any,
    upsert_tracker_entry_snapshots_best_effort_fn: Any,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    snapshot_map = load_tracker_entry_snapshot_map_fn(organization_id=organization_id, rows=rows)
    hydrated: list[dict[str, Any] | None] = [None] * len(rows)
    missing_rows: list[dict[str, Any]] = []
    missing_indexes: list[int] = []
    for index, row in enumerate(rows):
        tracker_entry_id = str(row.get("id") or "").strip()
        snapshot = snapshot_map.get(tracker_entry_id)
        export_json = dict((snapshot or {}).get("export_json") or {})
        if snapshot and export_json and is_tracker_entry_snapshot_fresh_fn(snapshot, row):
            hydrated[index] = export_json
            continue
        missing_rows.append(dict(row))
        missing_indexes.append(index)
    if missing_rows:
        materialized = upsert_tracker_entry_snapshots_best_effort_fn(
            organization_id=organization_id,
            rows=missing_rows,
        )
        for index, row in zip(missing_indexes, missing_rows):
            tracker_entry_id = str(row.get("id") or "").strip()
            hydrated[index] = dict((materialized.get(tracker_entry_id) or {}).get("export_row") or {})
    return [dict(item or {}) for item in hydrated]


def hydrate_tracker_entry_detail_row(
    *,
    organization_id: UUID,
    row: dict[str, Any],
    load_tracker_entry_snapshot_map_fn: Any,
    is_tracker_entry_snapshot_fresh_fn: Any,
    upsert_tracker_entry_snapshots_best_effort_fn: Any,
) -> dict[str, Any]:
    if not row:
        return {}
    snapshot_map = load_tracker_entry_snapshot_map_fn(organization_id=organization_id, rows=[row])
    tracker_entry_id = str(row.get("id") or "").strip()
    snapshot = snapshot_map.get(tracker_entry_id)
    detail_json = dict((snapshot or {}).get("detail_json") or {})
    if snapshot and detail_json and is_tracker_entry_snapshot_fresh_fn(snapshot, row):
        return detail_json
    materialized = upsert_tracker_entry_snapshots_best_effort_fn(
        organization_id=organization_id,
        rows=[row],
    )
    return dict((materialized.get(tracker_entry_id) or {}).get("detail_row") or {})
