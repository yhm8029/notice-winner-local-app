from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from datetime import timezone
from uuid import UUID

from .home_bootstrap_snapshots import HomeBootstrapSnapshotRepository
from .home_bootstrap_snapshots import HomeBootstrapSnapshotRow


class InMemoryHomeBootstrapSnapshotRepository(HomeBootstrapSnapshotRepository):
    def __init__(self) -> None:
        self._rows_by_org: dict[UUID, HomeBootstrapSnapshotRow] = {}

    def get_snapshot(
        self,
        *,
        organization_id: UUID,
    ) -> HomeBootstrapSnapshotRow | None:
        row = self._rows_by_org.get(organization_id)
        if row is None:
            return None
        return deepcopy(row)

    def upsert_snapshot(
        self,
        *,
        organization_id: UUID,
        snapshot_version: int,
        payload_json: dict[str, object],
        generated_at: object,
    ) -> HomeBootstrapSnapshotRow | None:
        now = datetime.now(timezone.utc)
        previous = self._rows_by_org.get(organization_id)
        row: HomeBootstrapSnapshotRow = {
            "organization_id": organization_id,
            "snapshot_version": int(snapshot_version or 0),
            "payload_json": deepcopy(dict(payload_json or {})),
            "generated_at": generated_at or now,
            "invalidated_at": None,
            "created_at": previous.get("created_at") if previous else now,
            "updated_at": now,
        }
        self._rows_by_org[organization_id] = row
        return deepcopy(row)

    def invalidate_snapshot(
        self,
        *,
        organization_id: UUID,
    ) -> None:
        row = self._rows_by_org.get(organization_id)
        if row is None:
            return
        row["invalidated_at"] = datetime.now(timezone.utc)
        row["updated_at"] = row["invalidated_at"]
