from __future__ import annotations

from typing import Any
from typing import Protocol
from uuid import UUID

HomeBootstrapSnapshotRow = dict[str, Any]


class HomeBootstrapSnapshotRepositoryError(RuntimeError):
    pass


class HomeBootstrapSnapshotRepositoryConfigError(HomeBootstrapSnapshotRepositoryError):
    pass


class HomeBootstrapSnapshotRepository(Protocol):
    def get_snapshot(
        self,
        *,
        organization_id: UUID,
    ) -> HomeBootstrapSnapshotRow | None: ...

    def upsert_snapshot(
        self,
        *,
        organization_id: UUID,
        snapshot_version: int,
        payload_json: dict[str, Any],
        generated_at: Any,
    ) -> HomeBootstrapSnapshotRow | None: ...

    def invalidate_snapshot(
        self,
        *,
        organization_id: UUID,
    ) -> None: ...
