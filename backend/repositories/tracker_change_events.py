from __future__ import annotations

from typing import Any
from typing import Protocol
from uuid import UUID

TrackerChangeEventRow = dict[str, Any]


class TrackerChangeEventRepositoryError(RuntimeError):
    pass


class TrackerChangeEventRepositoryConfigError(TrackerChangeEventRepositoryError):
    pass


class TrackerChangeEventRepository(Protocol):
    def append_events(
        self,
        *,
        organization_id: UUID,
        events: list[dict[str, Any]],
    ) -> list[TrackerChangeEventRow]: ...

    def list_events(
        self,
        *,
        organization_id: UUID,
        limit: int,
        tracker_entry_id: UUID | None = None,
        include_silent: bool = False,
    ) -> list[TrackerChangeEventRow]: ...

    def count_unread(
        self,
        *,
        organization_id: UUID,
    ) -> int: ...

    def mark_read(
        self,
        *,
        organization_id: UUID,
        event_ids: list[UUID] | None = None,
        tracker_entry_id: UUID | None = None,
    ) -> int: ...
