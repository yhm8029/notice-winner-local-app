from __future__ import annotations

from typing import Any
from typing import Protocol

RelatedNoticeCacheRow = dict[str, Any]


class RelatedNoticeCacheRepositoryError(RuntimeError):
    pass


class RelatedNoticeCacheRepositoryConfigError(RelatedNoticeCacheRepositoryError):
    pass


class RelatedNoticeCacheRepository(Protocol):
    def get_cache(self, *, project_key: str, snapshot_set_id: str | None = None) -> RelatedNoticeCacheRow | None: ...

    def upsert_cache(self, row: RelatedNoticeCacheRow) -> RelatedNoticeCacheRow: ...

    def list_queued(self, *, limit: int = 5) -> list[RelatedNoticeCacheRow]: ...

    def claim_queued(self, *, project_key: str, snapshot_set_id: str | None = None) -> RelatedNoticeCacheRow | None: ...
