from __future__ import annotations

from typing import Any
from uuid import UUID


def filter_tracker_rows_for_organization(
    *,
    rows: list[dict[str, Any]],
    organization_id: UUID,
) -> list[dict[str, Any]]:
    expected = str(organization_id)
    return [dict(row) for row in rows if str(row.get("organization_id") or "").strip() == expected]


def tracker_row_in_organization(*, row: dict[str, Any] | None, organization_id: UUID) -> bool:
    if row is None:
        return False
    return str(row.get("organization_id") or "").strip() == str(organization_id)
