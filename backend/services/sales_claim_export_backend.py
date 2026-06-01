from __future__ import annotations

import re
from typing import Any
from uuid import UUID


def extract_latest_sales_note_text(raw_sales_note: Any) -> str:
    entries = [str(line or "").strip() for line in str(raw_sales_note or "").splitlines() if str(line or "").strip()]
    if not entries:
        return ""
    latest = entries[-1]
    return re.sub(r"^\[[^\]]+\]\s*", "", latest).strip()


def build_sales_claim_export_rows(
    *,
    claims: list[Any],
    tracker_repository: Any,
    format_tracker_export_date: Any,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for claim in claims:
        payload = claim.to_dict() if hasattr(claim, "to_dict") else dict(claim or {})
        source_entry_id = payload.get("source_entry_id")
        tracker_entry: dict[str, Any] | None = None
        if source_entry_id:
            try:
                tracker_entry = tracker_repository.get_entry(UUID(str(source_entry_id)))
            except (ValueError, TypeError):
                tracker_entry = None

        latest_note_text = extract_latest_sales_note_text(payload.get("sales_note"))
        progress_note = latest_note_text or str((tracker_entry or {}).get("progress_note") or "")
        last_checked = format_tracker_export_date(
            payload.get("sales_note_updated_at")
            or payload.get("updated_at")
            or (tracker_entry or {}).get("last_checked_date")
        )
        rows.append(
            {
                "project_name": str(payload.get("project_name") or (tracker_entry or {}).get("project_name") or ""),
                "gross_area_scale": str((tracker_entry or {}).get("gross_area_scale") or ""),
                "construction_cost": str((tracker_entry or {}).get("construction_cost") or ""),
                "demand_org_name": str((tracker_entry or {}).get("demand_org_name") or ""),
                "demand_contact": str((tracker_entry or {}).get("demand_contact") or ""),
                "client_location": str((tracker_entry or {}).get("client_location") or ""),
                "site_location_1": str((tracker_entry or {}).get("site_location_1") or ""),
                "site_location_2": str((tracker_entry or {}).get("site_location_2") or ""),
                "architect_office": str((tracker_entry or {}).get("architect_office") or ""),
                "construction_start_date": str((tracker_entry or {}).get("construction_start_date") or ""),
                "last_checked_date": last_checked,
                "progress_note": progress_note,
                "notice_date": str((tracker_entry or {}).get("notice_date") or ""),
                "manager_name": str(payload.get("owner_display_name") or payload.get("owner_email") or ""),
                "building_automation_estimated_amount": str(
                    payload.get("estimated_amount_text")
                    or (tracker_entry or {}).get("building_automation_estimated_amount")
                    or ""
                ),
            }
        )
    return rows
