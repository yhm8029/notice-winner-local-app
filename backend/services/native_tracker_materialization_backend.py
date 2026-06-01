from __future__ import annotations

from pathlib import Path
from typing import Any

from . import native_tracker_backend as tracker_backend


def build_tracker_entries_from_winner_csv(
    *,
    winner_csv_path: Path,
    seed_csv_path: Path | None,
) -> list[dict[str, Any]]:
    seed_index = tracker_backend._load_seed_index(seed_csv_path)
    existing_defaults = tracker_backend._load_existing_tracker_defaults()
    rows: list[dict[str, Any]] = []
    with winner_csv_path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = tracker_backend.csv.DictReader(fp)
        for index, row in enumerate(reader, start=1):
            bid_no = str(row.get("bid_no") or "").strip().upper()
            bid_ord = tracker_backend._normalize_bid_ord(row.get("bid_ord") or "000")
            seed_meta = seed_index.get((bid_no, bid_ord), {})
            project_name = tracker_backend._resolve_project_name(row=row, seed_meta=seed_meta, bid_no=bid_no)
            source_project_name_norm = tracker_backend._slugify(project_name)
            entry_key = "|".join((bid_no.lower(), bid_ord.lower(), source_project_name_norm.lower()))
            defaults = existing_defaults.get(tracker_backend._norm_text(project_name), {})

            contract_amount = str(row.get("contract_amount") or "").strip()
            contract_amount_source = str(row.get("contract_amount_source") or "").strip()
            notice_construction_cost = str(row.get("notice_construction_cost") or "").strip()
            notice_construction_cost_source = str(row.get("notice_construction_cost_source") or "").strip()
            contract_date = str(row.get("contract_date") or "").strip()
            source_type = str(row.get("source_type") or "").strip()
            notice_date = str(seed_meta.get("announce_date") or "").strip()
            demand_org_name = str(seed_meta.get("org_name") or "").strip()
            reason_code = str(row.get("reason_code") or "").strip() or str(seed_meta.get("service_name") or "").strip()

            gross_area_scale = str(defaults.get("gross_area_scale") or "").strip() or tracker_backend._normalize_tracker_gross_area(
                project_name=project_name,
                value=row.get("gross_area_scale"),
                source=row.get("gross_area_scale_source"),
            )
            demand_contact_source = str(row.get("demand_contact_source") or "").strip()
            demand_contact = tracker_backend._normalize_tracker_contact(
                tracker_backend._tracker_safe_value(
                    row.get("demand_contact"),
                    demand_contact_source,
                    allowed_prefixes=("confirmed", "fallback_seed_contact"),
                ),
                allow_person_only=demand_contact_source.startswith("fallback_seed_contact"),
            )
            client_location = tracker_backend._tracker_safe_value(
                row.get("client_location"),
                row.get("client_location_source"),
            )
            site_location = tracker_backend._tracker_safe_value(
                row.get("site_location"),
                row.get("site_location_source"),
            )
            architect_office = tracker_backend._tracker_safe_value(
                row.get("architect_office"),
                row.get("architect_office_source"),
            )
            construction_start_date_explicit = tracker_backend._tracker_safe_value(
                row.get("construction_start_date"),
                row.get("construction_start_date_source"),
            )
            construction_duration_days = str(row.get("construction_duration_days") or "").strip()
            completion_expected_date_explicit = str(row.get("completion_expected_date_explicit") or "").strip()
            completion_expected_date_computed = (
                ""
                if completion_expected_date_explicit
                else tracker_backend._compute_completion_expected_date(
                    contract_date=contract_date,
                    duration_days=construction_duration_days,
                    source_type=source_type,
                )
            )
            construction_cost = tracker_backend._resolve_tracker_construction_cost(
                notice_construction_cost=notice_construction_cost,
                notice_construction_cost_source=notice_construction_cost_source,
                contract_amount=contract_amount,
                contract_amount_source=contract_amount_source,
                source_type=source_type,
                project_name=str(row.get("title") or row.get("contract_name") or project_name).strip(),
            )
            construction_cost = tracker_backend._sanitize_tracker_construction_cost(
                project_name=project_name,
                cost_value=construction_cost,
                gross_area_scale=gross_area_scale,
            )
            building_automation_estimated_amount = tracker_backend._tracker_safe_value(
                row.get("building_automation_estimated_amount"),
                row.get("building_automation_estimated_amount_source"),
                allowed_prefixes=("confirmed", "estimated"),
            )
            if not building_automation_estimated_amount and construction_cost:
                building_automation_estimated_amount = tracker_backend._estimate_building_automation_amount_from_cost(construction_cost)
            site_region, site_city = tracker_backend._derive_site_locations(
                current_site_location=site_location,
                demand_org_name=demand_org_name,
                project_name=project_name,
            )
            if str(defaults.get("site_location_1") or "").strip():
                site_region = str(defaults.get("site_location_1") or "").strip()
            if str(defaults.get("site_location_2") or "").strip():
                site_city = str(defaults.get("site_location_2") or "").strip()
            tracker_client_location = str(defaults.get("client_location") or "").strip() or tracker_backend._resolve_tracker_client_location(
                current_client_location=client_location,
                demand_org_name=demand_org_name,
                project_name=project_name,
                site_region=site_region,
                site_city=site_city,
            )
            site_region, site_city = tracker_backend.normalize_tracker_site_locations(
                current_site_region=site_region,
                current_site_city=site_city,
                current_client_location=tracker_client_location,
                demand_org_name=demand_org_name,
                project_name=project_name,
                trusted_current_site=bool(site_location) and not bool(str(defaults.get("site_location_2") or "").strip()),
            )
            architect_office = architect_office or str(defaults.get("architect_office") or "").strip()
            tracker_construction_period = tracker_backend._format_construction_period(
                contract_date=contract_date,
                duration_days=construction_duration_days,
                fallback_value=construction_start_date_explicit or contract_date,
                completion_expected_date_explicit=completion_expected_date_explicit,
                completion_expected_date_computed=completion_expected_date_computed,
                source_type=source_type,
            )
            progress_note = tracker_backend._build_progress_note(
                reason_code=reason_code,
                seed_meta=seed_meta,
                fallback_values=[
                    ("contract_amount", contract_amount, contract_amount_source),
                    ("notice_construction_cost", notice_construction_cost, notice_construction_cost_source),
                    (
                        "demand_contact",
                        str(row.get("demand_contact") or "").strip(),
                        str(row.get("demand_contact_source") or "").strip(),
                    ),
                    (
                        "architect_office",
                        str(row.get("architect_office") or "").strip(),
                        str(row.get("architect_office_source") or "").strip(),
                    ),
                    (
                        "building_automation_estimated_amount",
                        str(row.get("building_automation_estimated_amount") or "").strip(),
                        str(row.get("building_automation_estimated_amount_source") or "").strip(),
                    ),
                ],
            )

            rows.append(
                {
                    "entry_key": entry_key,
                    "row_no": index,
                    "sheet_name": "Sheet1",
                    "section_name": "facility_cost",
                    "source_bid_no": bid_no,
                    "source_bid_ord": bid_ord,
                    "source_project_name_norm": source_project_name_norm,
                    "project_name": project_name,
                    "gross_area_scale": gross_area_scale,
                    "construction_cost": construction_cost,
                    "demand_org_name": demand_org_name,
                    "demand_contact": demand_contact,
                    "client_location": tracker_client_location,
                    "site_location_1": site_region,
                    "site_location_2": site_city,
                    "architect_office": architect_office,
                    "opening_scheduled_date": str(seed_meta.get("opening_scheduled_date") or "").strip(),
                    "construction_start_date": tracker_construction_period,
                    "contract_date": contract_date,
                    "construction_duration_days": construction_duration_days,
                    "completion_expected_date_explicit": completion_expected_date_explicit,
                    "completion_expected_date_computed": completion_expected_date_computed,
                    "last_checked_date": contract_date or notice_date,
                    "progress_note": progress_note,
                    "notice_date": notice_date,
                    "manager_name": str(defaults.get("manager_name") or "").strip(),
                    "building_automation_estimated_amount": building_automation_estimated_amount,
                }
            )
    return rows
