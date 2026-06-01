from __future__ import annotations

from typing import Any
from typing import Protocol
from uuid import UUID

TrackerEntrySnapshotRow = dict[str, Any]


class TrackerEntrySnapshotRepositoryError(RuntimeError):
    pass


class TrackerEntrySnapshotRepositoryConfigError(TrackerEntrySnapshotRepositoryError):
    pass


class TrackerEntrySnapshotRepository(Protocol):
    def upsert_snapshots(
        self,
        *,
        organization_id: UUID,
        snapshots: list[dict[str, Any]],
    ) -> list[TrackerEntrySnapshotRow]: ...

    def get_snapshots(
        self,
        *,
        organization_id: UUID,
        tracker_entry_ids: list[UUID],
    ) -> list[TrackerEntrySnapshotRow]: ...
