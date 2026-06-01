from __future__ import annotations

from collections import Counter
from typing import Any
from uuid import UUID


CONTACT_RESOLUTION_STATUS_ORDER = (
    "resolved",
    "review",
    "no_owner_candidate",
    "missing",
)


def build_tracker_contact_resolution_summary(
    *,
    entries: list[dict[str, Any]],
    limit: int,
    load_winner_index_by_run_fn: Any,
    lookup_winner_row_for_entry_fn: Any,
    coerce_uuid_or_none_fn: Any,
    source_run_id: UUID | None = None,
    source_tracker_run_id: UUID | None = None,
) -> dict[str, Any]:
    filtered_entries: list[dict[str, Any]] = []
    for row in entries:
        entry_source_run_id = coerce_uuid_or_none_fn(row.get("source_run_id"))
        entry_source_tracker_run_id = coerce_uuid_or_none_fn(row.get("source_tracker_run_id"))
        if source_run_id is not None and entry_source_run_id != source_run_id:
            continue
        if source_tracker_run_id is not None and entry_source_tracker_run_id != source_tracker_run_id:
            continue
        filtered_entries.append(dict(row))

    winner_cache: dict[UUID, tuple[dict[tuple[str, str, str], dict[str, str]], dict[tuple[str, str], dict[str, str]]]] = {}
    status_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    items: list[dict[str, Any]] = []

    for entry in filtered_entries:
        winner_row = lookup_winner_row_for_entry_fn(
            entry,
            winner_cache,
            load_winner_index_by_run_fn=load_winner_index_by_run_fn,
            coerce_uuid_or_none=coerce_uuid_or_none_fn,
        )
        resolution_status = str((winner_row or {}).get("demand_contact_resolution_status") or "").strip() or "missing"
        resolution_reason = str((winner_row or {}).get("demand_contact_resolution_reason") or "").strip()
        resolution_phase = str((winner_row or {}).get("demand_contact_resolution_phase") or "").strip()
        resolution_role = str((winner_row or {}).get("demand_contact_resolution_role") or "").strip()
        resolution_owner_side = str((winner_row or {}).get("demand_contact_resolution_owner_side") or "").strip()
        resolution_owner_side_basis = str((winner_row or {}).get("demand_contact_resolution_owner_side_basis") or "").strip()

        status_counts[resolution_status] += 1
        if resolution_reason:
            reason_counts[resolution_reason] += 1

        if len(items) >= limit:
            continue
        items.append(
            {
                "entry_id": entry.get("id"),
                "source_run_id": coerce_uuid_or_none_fn(entry.get("source_run_id")),
                "source_tracker_run_id": coerce_uuid_or_none_fn(entry.get("source_tracker_run_id")),
                "project_name": str(entry.get("project_name") or "").strip(),
                "demand_org_name": str(entry.get("demand_org_name") or "").strip(),
                "demand_contact": str(entry.get("demand_contact") or "").strip(),
                "resolution_status": resolution_status,
                "resolution_reason": resolution_reason,
                "resolution_phase": resolution_phase,
                "resolution_role": resolution_role,
                "resolution_owner_side": resolution_owner_side,
                "resolution_owner_side_basis": resolution_owner_side_basis,
                "updated_at": entry.get("updated_at"),
            }
        )

    ordered_statuses = [
        *CONTACT_RESOLUTION_STATUS_ORDER,
        *sorted(status for status in status_counts if status not in CONTACT_RESOLUTION_STATUS_ORDER),
    ]
    status_items = [
        {"status": status, "count": status_counts[status]}
        for status in ordered_statuses
        if status_counts.get(status, 0) > 0
    ]
    reason_items = [
        {"reason": reason, "count": count}
        for reason, count in sorted(reason_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    return {
        "total_entries": len(filtered_entries),
        "status_counts": status_items,
        "reason_counts": reason_items,
        "items": items,
    }
