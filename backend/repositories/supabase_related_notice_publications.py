from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from uuid import UUID

from backend.phase1_defaults import load_phase1_identity

from .related_notice_publications import RelatedNoticePublicationRepository
from .related_notice_publications import RelatedNoticePublicationRepositoryConfigError
from .related_notice_publications import RelatedNoticePublicationRepositoryError
from .related_notice_publications import RelatedNoticePublicationRow
from .supabase_http import request_json

RELATED_NOTICE_PUBLICATION_SELECT = ",".join(
    (
        "organization_id",
        "published_snapshot_set_id",
        "source_run_id",
        "generated_at",
        "published_at",
        "created_at",
        "updated_at",
    )
)


@dataclass(frozen=True)
class SupabaseRelatedNoticePublicationRepositoryConfig:
    base_url: str
    api_key: str
    organization_id: str
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "SupabaseRelatedNoticePublicationRepositoryConfig":
        base_url = os.getenv("SUPABASE_URL", "").strip()
        api_key = (
            os.getenv("SUPABASE_SECRET_KEY", "").strip()
            or os.getenv("SUPABASE_SECRET", "").strip()
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_ANON_KEY", "").strip()
        )
        if not base_url:
            raise RelatedNoticePublicationRepositoryConfigError("SUPABASE_URL is required")
        if not api_key:
            raise RelatedNoticePublicationRepositoryConfigError(
                "SUPABASE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_SECRET, or SUPABASE_ANON_KEY is required"
            )
        raw_timeout = os.getenv("SUPABASE_HTTP_TIMEOUT_SECONDS", "").strip()
        timeout_seconds = 10.0
        if raw_timeout:
            try:
                timeout_seconds = float(raw_timeout)
            except ValueError as exc:
                raise RelatedNoticePublicationRepositoryConfigError(
                    "SUPABASE_HTTP_TIMEOUT_SECONDS must be numeric"
                ) from exc
        identity = load_phase1_identity()
        return cls(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            organization_id=str(identity.organization_id),
            timeout_seconds=timeout_seconds,
        )


class SupabaseRelatedNoticePublicationRepository(RelatedNoticePublicationRepository):
    def __init__(self, config: SupabaseRelatedNoticePublicationRepositoryConfig) -> None:
        self._config = config
        self._rest_url = f"{config.base_url}/rest/v1"
        self._table_available = True

    def get_publication(self, *, organization_id: UUID) -> RelatedNoticePublicationRow | None:
        if not self._table_available:
            return None
        try:
            rows, _headers = request_json(
                rest_url=self._rest_url,
                api_key=self._config.api_key,
                timeout_seconds=self._config.timeout_seconds,
                method="GET",
                path="/related_notice_publications",
                query=[
                    ("select", RELATED_NOTICE_PUBLICATION_SELECT),
                    ("organization_id", f"eq.{organization_id}"),
                    ("limit", "1"),
                ],
                error_cls=RelatedNoticePublicationRepositoryError,
            )
        except RelatedNoticePublicationRepositoryError as exc:
            if self._is_missing_table_error(str(exc)):
                self._table_available = False
                return None
            raise
        if not isinstance(rows, list) or not rows:
            return None
        return self._normalize_publication_row(dict(rows[0]))

    def upsert_publication(
        self,
        *,
        organization_id: UUID,
        published_snapshot_set_id: str,
        source_run_id: UUID,
        generated_at: object,
        published_at: object,
    ) -> RelatedNoticePublicationRow:
        if not self._table_available:
            raise RelatedNoticePublicationRepositoryError("related_notice_publications table is unavailable")
        payload = {
            "organization_id": str(organization_id),
            "published_snapshot_set_id": str(published_snapshot_set_id or ""),
            "source_run_id": str(source_run_id),
            "generated_at": self._serialize_timestamp(generated_at),
            "published_at": self._serialize_timestamp(published_at),
        }
        try:
            rows, _headers = request_json(
                rest_url=self._rest_url,
                api_key=self._config.api_key,
                timeout_seconds=self._config.timeout_seconds,
                method="POST",
                path="/related_notice_publications",
                query=[("select", RELATED_NOTICE_PUBLICATION_SELECT), ("on_conflict", "organization_id")],
                headers={"Prefer": "resolution=merge-duplicates,return=representation"},
                payload=payload,
                allow_retry=True,
                error_cls=RelatedNoticePublicationRepositoryError,
            )
        except RelatedNoticePublicationRepositoryError as exc:
            if self._is_missing_table_error(str(exc)):
                self._table_available = False
                raise RelatedNoticePublicationRepositoryError("missing related_notice_publications table") from exc
            raise
        if not isinstance(rows, list) or not rows:
            raise RelatedNoticePublicationRepositoryError(
                "Supabase did not return the upserted related notice publication row"
            )
        return self._normalize_publication_row(dict(rows[0]))

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
        if not self._table_available:
            raise RelatedNoticePublicationRepositoryError("related_notice_publications table is unavailable")
        expected_updated_at_value = self._serialize_timestamp(expected_updated_at)
        payload = {
            "organization_id": str(organization_id),
            "published_snapshot_set_id": str(published_snapshot_set_id or ""),
            "source_run_id": str(source_run_id),
            "generated_at": self._serialize_timestamp(generated_at),
            "published_at": self._serialize_timestamp(published_at),
        }
        try:
            rows, _headers = request_json(
                rest_url=self._rest_url,
                api_key=self._config.api_key,
                timeout_seconds=self._config.timeout_seconds,
                method="PATCH",
                path="/related_notice_publications",
                query=[
                    ("select", RELATED_NOTICE_PUBLICATION_SELECT),
                    ("organization_id", f"eq.{organization_id}"),
                    ("updated_at", f"eq.{expected_updated_at_value}"),
                ],
                headers={"Prefer": "return=representation"},
                payload=payload,
                allow_retry=True,
                error_cls=RelatedNoticePublicationRepositoryError,
            )
        except RelatedNoticePublicationRepositoryError as exc:
            if self._is_missing_table_error(str(exc)):
                self._table_available = False
                raise RelatedNoticePublicationRepositoryError("missing related_notice_publications table") from exc
            raise
        if isinstance(rows, list) and rows:
            return self._normalize_publication_row(dict(rows[0]))
        current = self.get_publication(organization_id=organization_id)
        if current is not None:
            return current
        raise RelatedNoticePublicationRepositoryError("Supabase did not return the guarded related notice publication row")

    @staticmethod
    def _is_missing_table_error(message: str) -> bool:
        text = str(message or "").lower()
        if "related_notice_publications" not in text:
            return False
        return (
            "does not exist" in text
            or "not found" in text
            or "could not find the table" in text
            or "schema cache" in text
            or "pgrst" in text
            or "relation" in text
        )

    @staticmethod
    def _serialize_timestamp(value: object) -> object:
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    @staticmethod
    def _normalize_publication_row(row: dict[str, object]) -> RelatedNoticePublicationRow:
        normalized = dict(row)
        normalized["organization_id"] = UUID(str(normalized["organization_id"]))
        normalized["source_run_id"] = UUID(str(normalized["source_run_id"]))
        normalized["published_snapshot_set_id"] = str(normalized.get("published_snapshot_set_id") or "")
        normalized["generated_at"] = SupabaseRelatedNoticePublicationRepository._parse_datetime(normalized.get("generated_at"))
        normalized["published_at"] = SupabaseRelatedNoticePublicationRepository._parse_datetime(normalized.get("published_at"))
        normalized["created_at"] = SupabaseRelatedNoticePublicationRepository._parse_datetime(normalized.get("created_at"))
        normalized["updated_at"] = SupabaseRelatedNoticePublicationRepository._parse_datetime(normalized.get("updated_at"))
        return normalized

    @staticmethod
    def _parse_datetime(value: object) -> datetime:
        if isinstance(value, datetime):
            parsed = value
        else:
            parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
