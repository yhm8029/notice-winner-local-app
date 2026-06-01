from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from datetime import timezone
from uuid import UUID

from .tracker_entry_snapshots import TrackerEntrySnapshotRepository
from .tracker_entry_snapshots import TrackerEntrySnapshotRow


class InMemoryTrackerEntrySnapshotRepository(TrackerEntrySnapshotRepository):
    def __init__(self) -> None:
        self._rows_by_entry_id: dict[UUID, TrackerEntrySnapshotRow] = {}

    def upsert_snapshots(
        self,
        *,
        organization_id: UUID,
        snapshots: list[dict[str, object]],
    ) -> list[TrackerEntrySnapshotRow]:
        rows: list[TrackerEntrySnapshotRow] = []
        now = datetime.now(timezone.utc)
        for payload in snapshots:
            tracker_entry_id = payload.get("tracker_entry_id")
            if not isinstance(tracker_entry_id, UUID):
                continue
            row: TrackerEntrySnapshotRow = {
                "tracker_entry_id": tracker_entry_id,
                "organization_id": organization_id,
                "summary_json": deepcopy(dict(payload.get("summary_json") or {})),
                "detail_json": deepcopy(dict(payload.get("detail_json") or {})),
                "export_json": deepcopy(dict(payload.get("export_json") or {})),
                "updated_at": payload.get("updated_at") or now,
            }
            self._rows_by_entry_id[tracker_entry_id] = row
            rows.append(deepcopy(row))
        return rows

    def get_snapshots(
        self,
        *,
        organization_id: UUID,
        tracker_entry_ids: list[UUID],
    ) -> list[TrackerEntrySnapshotRow]:
        rows: list[TrackerEntrySnapshotRow] = []
        for tracker_entry_id in tracker_entry_ids:
            row = self._rows_by_entry_id.get(tracker_entry_id)
            if row is None:
                continue
            if row.get("organization_id") != organization_id:
                continue
            rows.append(deepcopy(row))
        return rows
