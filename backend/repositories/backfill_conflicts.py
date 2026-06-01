from __future__ import annotations

from typing import Any
from typing import Protocol
from uuid import UUID

BackfillConflictRow = dict[str, Any]


class BackfillConflictRepositoryError(RuntimeError):
    pass


class BackfillConflictRepositoryConfigError(BackfillConflictRepositoryError):
    pass


class BackfillConflictRepository(Protocol):
    def upsert_conflicts(
        self,
        *,
        organization_id: UUID,
        conflicts: list[dict[str, Any]],
    ) -> list[BackfillConflictRow]: ...

    def list_conflicts(
        self,
        *,
        organization_id: UUID,
        limit: int,
        tracker_entry_id: UUID | None = None,
        source_run_id: UUID | None = None,
        include_resolved: bool = False,
    ) -> list[BackfillConflictRow]: ...

    def resolve_conflict(
        self,
        *,
        organization_id: UUID,
        conflict_id: UUID,
        resolution: str,
    ) -> BackfillConflictRow | None: ...
