from __future__ import annotations

from typing import Any
from typing import Protocol
from uuid import UUID

RelatedNoticePublicationRow = dict[str, Any]


class RelatedNoticePublicationRepositoryError(RuntimeError):
    pass


class RelatedNoticePublicationRepositoryConfigError(RelatedNoticePublicationRepositoryError):
    pass


class RelatedNoticePublicationRepository(Protocol):
    def get_publication(self, *, organization_id: UUID) -> RelatedNoticePublicationRow | None: ...

    def upsert_publication(
        self,
        *,
        organization_id: UUID,
        published_snapshot_set_id: str,
        source_run_id: UUID,
        generated_at: Any,
        published_at: Any,
    ) -> RelatedNoticePublicationRow: ...

    def upsert_publication_if_current(
        self,
        *,
        organization_id: UUID,
        expected_updated_at: Any,
        published_snapshot_set_id: str,
        source_run_id: UUID,
        generated_at: Any,
        published_at: Any,
    ) -> RelatedNoticePublicationRow: ...
