from __future__ import annotations

from datetime import datetime
from datetime import timezone
from uuid import UUID
from uuid import uuid4

from .tracker_change_events import TrackerChangeEventRepository
from .tracker_change_events import TrackerChangeEventRow


class InMemoryTrackerChangeEventRepository(TrackerChangeEventRepository):
    def __init__(self) -> None:
        self._rows_by_id: dict[UUID, TrackerChangeEventRow] = {}
        self._rows_by_dedupe: dict[str, UUID] = {}

    def append_events(
        self,
        *,
        organization_id: UUID,
        events: list[dict[str, object]],
    ) -> list[TrackerChangeEventRow]:
        rows: list[TrackerChangeEventRow] = []
        for payload in events:
            dedupe_key = str(payload.get("dedupe_key") or "").strip()
            if dedupe_key and dedupe_key in self._rows_by_dedupe:
                rows.append(dict(self._rows_by_id[self._rows_by_dedupe[dedupe_key]]))
                continue
            now = datetime.now(timezone.utc)
            row_id = uuid4()
            row: TrackerChangeEventRow = {
                "id": row_id,
                "organization_id": organization_id,
                "tracker_entry_id": payload.get("tracker_entry_id"),
                "event_type": str(payload.get("event_type") or "").strip(),
                "field_name": str(payload.get("field_name") or "").strip(),
                "old_value": str(payload.get("old_value") or ""),
                "new_value": str(payload.get("new_value") or ""),
                "old_value_norm": str(payload.get("old_value_norm") or "").strip(),
                "new_value_norm": str(payload.get("new_value_norm") or "").strip(),
                "source_run_id": payload.get("source_run_id"),
                "source_kind": str(payload.get("source_kind") or "").strip(),
                "source_ref": str(payload.get("source_ref") or "").strip(),
                "extractor_version": str(payload.get("extractor_version") or "").strip(),
                "reason_code": str(payload.get("reason_code") or "").strip(),
                "batch_key": str(payload.get("batch_key") or "").strip(),
                "dedupe_key": dedupe_key,
                "is_silent": bool(payload.get("is_silent")),
                "created_at": payload.get("created_at") or now,
                "is_read": bool(payload.get("is_read")),
                "read_at": payload.get("read_at"),
            }
            self._rows_by_id[row_id] = row
            if dedupe_key:
                self._rows_by_dedupe[dedupe_key] = row_id
            rows.append(dict(row))
        return rows

    def list_events(self, *, organization_id: UUID, limit: int, tracker_entry_id: UUID | None = None, include_silent: bool = False) -> list[TrackerChangeEventRow]:
        rows = [
            dict(row)
            for row in self._rows_by_id.values()
            if row.get("organization_id") == organization_id
            and (tracker_entry_id is None or row.get("tracker_entry_id") == tracker_entry_id)
            and (include_silent or not bool(row.get("is_silent")))
        ]
        rows.sort(key=lambda item: (item.get("created_at"), str(item.get("id"))), reverse=True)
        return rows[:limit]

    def count_unread(self, *, organization_id: UUID) -> int:
        return sum(
            1
            for row in self._rows_by_id.values()
            if row.get("organization_id") == organization_id and not bool(row.get("is_read")) and not bool(row.get("is_silent"))
        )

    def mark_read(self, *, organization_id: UUID, event_ids: list[UUID] | None = None, tracker_entry_id: UUID | None = None) -> int:
        updated = 0
        targets = set(event_ids or [])
        now = datetime.now(timezone.utc)
        for row in self._rows_by_id.values():
            if row.get("organization_id") != organization_id:
                continue
            if targets and row.get("id") not in targets:
                continue
            if not targets and tracker_entry_id is not None and row.get("tracker_entry_id") != tracker_entry_id:
                continue
            if bool(row.get("is_read")):
                continue
            row["is_read"] = True
            row["read_at"] = now
            updated += 1
        return updated
