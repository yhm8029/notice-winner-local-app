from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID


def slugify(value: str) -> str:
    compact = "-".join(part for part in value.strip().lower().replace("/", " ").split() if part)
    return compact or "notice-winner-pipeline"


def normalize_bid_ord(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "000"
    if raw.isdigit():
        return f"{int(raw):03d}"
    return raw


def to_iso_date(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) != 8:
        return ""
    return f"{digits[0:4]}-{digits[4:6]}-{digits[6:8]}"


def to_storage_path(path: Any) -> str:
    path_obj = Path(path) if not isinstance(path, Path) else path
    try:
        return str(path_obj.relative_to(Path(__file__).resolve().parents[2])).replace("\\", "/")
    except Exception:
        return str(path_obj).replace("\\", "/")


def stage_delay_seconds(*, params: dict[str, Any], fallback_ms: int) -> float:
    advanced_options = dict(params.get("_advanced_options") or {})
    raw_ms = advanced_options.get("simulate_stage_delay_ms", fallback_ms)
    try:
        value_ms = max(0, int(raw_ms))
    except (TypeError, ValueError):
        value_ms = fallback_ms
    return value_ms / 1000.0


def build_tracker_seed_entries(
    *,
    run_id: UUID,
    params: dict[str, Any],
    seed_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    bid_no = str(params.get("bid_no") or f"WNP{str(run_id).replace('-', '')[:12].upper()}")
    notice_title = str(params.get("notice_title") or "Project Tracker")
    demand_org = str(params.get("demand_org") or "Internal Demand Organization")
    start_date = str(params.get("start_date") or "20250101")
    end_date = str(params.get("end_date") or start_date)
    contract_date_hint = str(params.get("contract_date_hint") or end_date or start_date)
    max_pages = int(params.get("max_pages") or 1)
    rows_per_page = int(params.get("rows_per_page") or 100)
    api_scope = str(params.get("api_scope") or "construction")
    title_slug = slugify(notice_title)
    demand_slug = slugify(demand_org)

    if seed_rows:
        entries: list[dict[str, Any]] = []
        for index, seed_row in enumerate(seed_rows, start=1):
            source_bid_no = str(seed_row.get("bid_no") or bid_no).strip() or bid_no
            source_bid_ord = normalize_bid_ord(seed_row.get("bid_ord"))
            project_name = str(seed_row.get("project_name") or notice_title).strip() or notice_title
            org_name = str(seed_row.get("org_name") or demand_org).strip() or demand_org
            announce_date = str(seed_row.get("announce_date") or end_date).strip() or end_date
            g2b_verified = str(seed_row.get("g2b_verified") or "N").strip().upper() or "N"
            project_name_norm = slugify(project_name)
            entry_key = "|".join(
                (
                    source_bid_no.strip().lower(),
                    source_bid_ord.strip().lower(),
                    project_name_norm.strip().lower(),
                )
            )
            entries.append(
                {
                    "entry_key": entry_key,
                    "row_no": index,
                    "sheet_name": "Sheet1",
                    "section_name": "facility_cost",
                    "source_bid_no": source_bid_no,
                    "source_bid_ord": source_bid_ord,
                    "source_project_name_norm": project_name_norm,
                    "project_name": project_name,
                    "gross_area_scale": f"{api_scope} / pages={max_pages} / rows={rows_per_page}",
                    "construction_cost": str(max(1, rows_per_page) * 1000000 * index),
                    "demand_org_name": org_name,
                    "demand_contact": "Internal Ops",
                    "client_location": "Seoul",
                    "site_location_1": org_name,
                    "site_location_2": api_scope,
                    "architect_office": "GUI Parity Architects",
                    "construction_start_date": to_iso_date(start_date),
                    "last_checked_date": to_iso_date(contract_date_hint or end_date),
                    "progress_note": f"Collected seed ({g2b_verified}) from project_tracker {run_id}",
                    "notice_date": to_iso_date(announce_date),
                    "manager_name": "Phase1 Internal User",
                    "building_automation_estimated_amount": str(max_pages * 5000000 * index),
                }
            )
        return entries

    base_entry = {
        "sheet_name": "Sheet1",
        "section_name": "facility_cost",
        "source_bid_no": bid_no,
        "source_bid_ord": "000",
        "source_project_name_norm": title_slug,
        "project_name": notice_title,
        "gross_area_scale": f"{max_pages} pages / {rows_per_page} rows",
        "construction_cost": str(max(1, rows_per_page) * 1000000),
        "demand_org_name": demand_org,
        "demand_contact": "Internal Ops",
        "client_location": "Seoul",
        "site_location_1": "Seoul Headquarters",
        "site_location_2": api_scope,
        "architect_office": "GUI Parity Architects",
        "construction_start_date": to_iso_date(start_date),
        "last_checked_date": to_iso_date(contract_date_hint or end_date),
        "progress_note": f"Generated from project_tracker {run_id}",
        "notice_date": to_iso_date(end_date),
        "manager_name": "Phase1 Internal User",
        "building_automation_estimated_amount": str(max_pages * 5000000),
    }
    entries: list[dict[str, Any]] = []
    for index, source in enumerate(
        (
            base_entry,
            {
                **base_entry,
                "source_bid_ord": "001",
                "source_project_name_norm": f"{title_slug}-follow-up",
                "project_name": f"{notice_title} Follow-up",
                "construction_cost": str(max(1, rows_per_page) * 800000),
                "demand_org_name": f"{demand_org} - {api_scope}",
                "progress_note": f"Generated from {demand_slug}",
                "building_automation_estimated_amount": str(max_pages * 3500000),
            },
        ),
        start=1,
    ):
        entry_key = "|".join(
            (
                str(source["source_bid_no"]).strip().lower(),
                str(source["source_bid_ord"]).strip().lower(),
                str(source["source_project_name_norm"]).strip().lower(),
            )
        )
        row = {
            "entry_key": entry_key,
            "row_no": index,
        }
        row.update(source)
        entries.append(row)

    return entries
