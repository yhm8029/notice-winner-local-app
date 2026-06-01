from __future__ import annotations

from datetime import datetime
from datetime import timezone
from uuid import UUID
from uuid import uuid4

from .backfill_conflicts import BackfillConflictRepository
from .backfill_conflicts import BackfillConflictRow


class InMemoryBackfillConflictRepository(BackfillConflictRepository):
    def __init__(self) -> None:
        self._rows_by_id: dict[UUID, BackfillConflictRow] = {}
        self._rows_by_key: dict[str, UUID] = {}

    def upsert_conflicts(self, *, organization_id: UUID, conflicts: list[dict[str, object]]) -> list[BackfillConflictRow]:
        rows: list[BackfillConflictRow] = []
        for payload in conflicts:
            conflict_key = str(payload.get("conflict_key") or "").strip()
            if conflict_key and conflict_key in self._rows_by_key:
                existing = self._rows_by_id[self._rows_by_key[conflict_key]]
                existing.update(
                    {
                        "current_value": str(payload.get("current_value") or existing.get("current_value") or ""),
                        "candidate_value": str(payload.get("candidate_value") or existing.get("candidate_value") or ""),
                        "current_value_norm": str(payload.get("current_value_norm") or existing.get("current_value_norm") or ""),
                        "candidate_value_norm": str(payload.get("candidate_value_norm") or existing.get("candidate_value_norm") or ""),
                        "reason_code": str(payload.get("reason_code") or existing.get("reason_code") or ""),
                        "source_kind": str(payload.get("source_kind") or existing.get("source_kind") or ""),
                        "source_ref": str(payload.get("source_ref") or existing.get("source_ref") or ""),
                        "source_run_id": payload.get("source_run_id") or existing.get("source_run_id"),
                        "extractor_version": str(payload.get("extractor_version") or existing.get("extractor_version") or ""),
                    }
                )
                rows.append(dict(existing))
                continue
            row_id = uuid4()
            row: BackfillConflictRow = {
                "id": row_id,
                "organization_id": organization_id,
                "tracker_entry_id": payload.get("tracker_entry_id"),
                "field_name": str(payload.get("field_name") or "").strip(),
                "current_value": str(payload.get("current_value") or ""),
                "candidate_value": str(payload.get("candidate_value") or ""),
                "current_value_norm": str(payload.get("current_value_norm") or "").strip(),
                "candidate_value_norm": str(payload.get("candidate_value_norm") or "").strip(),
                "reason_code": str(payload.get("reason_code") or "").strip(),
                "source_kind": str(payload.get("source_kind") or "").strip(),
                "source_ref": str(payload.get("source_ref") or "").strip(),
                "source_run_id": payload.get("source_run_id"),
                "extractor_version": str(payload.get("extractor_version") or "").strip(),
                "detected_at": payload.get("detected_at") or datetime.now(timezone.utc),
                "resolved_at": payload.get("resolved_at"),
                "resolution": str(payload.get("resolution") or "").strip() or None,
                "conflict_key": conflict_key,
            }
            self._rows_by_id[row_id] = row
            if conflict_key:
                self._rows_by_key[conflict_key] = row_id
            rows.append(dict(row))
        return rows

    def list_conflicts(
        self,
        *,
        organization_id: UUID,
        limit: int,
        tracker_entry_id: UUID | None = None,
        source_run_id: UUID | None = None,
        include_resolved: bool = False,
    ) -> list[BackfillConflictRow]:
        rows = [
            dict(row)
            for row in self._rows_by_id.values()
            if row.get("organization_id") == organization_id
            and (tracker_entry_id is None or row.get("tracker_entry_id") == tracker_entry_id)
            and (source_run_id is None or row.get("source_run_id") == source_run_id)
            and (include_resolved or row.get("resolved_at") is None)
        ]
        rows.sort(key=lambda item: (item.get("detected_at"), str(item.get("id"))), reverse=True)
        return rows[:limit]

    def resolve_conflict(
        self,
        *,
        organization_id: UUID,
        conflict_id: UUID,
        resolution: str,
    ) -> BackfillConflictRow | None:
        row = self._rows_by_id.get(conflict_id)
        if row is None or row.get("organization_id") != organization_id:
            return None
        row["resolution"] = str(resolution or "").strip() or None
        row["resolved_at"] = datetime.now(timezone.utc)
        return dict(row)
