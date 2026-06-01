from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from datetime import timezone
from uuid import UUID

from .related_notice_publications import RelatedNoticePublicationRepository
from .related_notice_publications import RelatedNoticePublicationRow


def _coerce_uuid(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _coerce_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class InMemoryRelatedNoticePublicationRepository(RelatedNoticePublicationRepository):
    def __init__(self) -> None:
        self._rows_by_organization_id: dict[str, RelatedNoticePublicationRow] = {}

    def get_publication(self, *, organization_id: UUID) -> RelatedNoticePublicationRow | None:
        key = str(organization_id)
        row = self._rows_by_organization_id.get(key)
        if row is None:
            return None
        return deepcopy(row)

    def upsert_publication(
        self,
        *,
        organization_id: UUID,
        published_snapshot_set_id: str,
        source_run_id: UUID,
        generated_at: object,
        published_at: object,
    ) -> RelatedNoticePublicationRow:
        key = str(organization_id)
        existing = dict(self._rows_by_organization_id.get(key) or {})
        generated_at_value = _coerce_datetime(generated_at)
        published_at_value = _coerce_datetime(published_at)
        row: RelatedNoticePublicationRow = {
            "organization_id": _coerce_uuid(organization_id),
            "published_snapshot_set_id": str(published_snapshot_set_id or ""),
            "source_run_id": _coerce_uuid(source_run_id),
            "generated_at": generated_at_value,
            "published_at": published_at_value,
            "created_at": _coerce_datetime(existing["created_at"]) if existing.get("created_at") is not None else generated_at_value,
            "updated_at": published_at_value,
        }
        self._rows_by_organization_id[key] = dict(row)
        return deepcopy(row)

    def upsert_publication_if_current(
        self,
        *,
        organization_id: UUID,
        expected_updated_at: object,
        published_snapshot_set_id: str,
        source_run_id: UUID,
        generated_at: object,
        published_at: object,
    ) -> RelatedNoticePublicationRow:
        key = str(organization_id)
        existing = dict(self._rows_by_organization_id.get(key) or {})
        if existing:
            current_updated_at = _coerce_datetime(existing["updated_at"])
            if _coerce_datetime(expected_updated_at) != current_updated_at:
                return deepcopy(existing)
        return self.upsert_publication(
            organization_id=organization_id,
            published_snapshot_set_id=published_snapshot_set_id,
            source_run_id=source_run_id,
            generated_at=generated_at,
            published_at=published_at,
        )
