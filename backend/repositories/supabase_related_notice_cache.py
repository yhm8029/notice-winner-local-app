from __future__ import annotations

import os
from dataclasses import dataclass

from backend.phase1_defaults import load_phase1_identity

from .related_notice_cache import RelatedNoticeCacheRepository
from .related_notice_cache import RelatedNoticeCacheRepositoryConfigError
from .related_notice_cache import RelatedNoticeCacheRepositoryError
from .related_notice_cache import RelatedNoticeCacheRow
from .supabase_http import request_json

RELATED_NOTICE_CACHE_SELECT = ",".join(
    (
        "id",
        "organization_id",
        "project_key",
        "snapshot_set_id",
        "project_name",
        "project_search_name",
        "issuer_name",
        "status",
        "source",
        "algorithm_version",
        "item_count",
        "error",
        "payload_json",
        "source_run_id",
        "generated_at",
        "created_at",
        "updated_at",
    )
)

RELATED_NOTICE_CACHE_SELECT_LEGACY = ",".join(
    (
        "id",
        "organization_id",
        "project_key",
        "project_name",
        "project_search_name",
        "issuer_name",
        "status",
        "source",
        "algorithm_version",
        "item_count",
        "error",
        "payload_json",
        "source_run_id",
        "generated_at",
        "created_at",
        "updated_at",
    )
)


@dataclass(frozen=True)
class SupabaseRelatedNoticeCacheRepositoryConfig:
    base_url: str
    api_key: str
    organization_id: str
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "SupabaseRelatedNoticeCacheRepositoryConfig":
        base_url = os.getenv("SUPABASE_URL", "").strip()
        api_key = (
            os.getenv("SUPABASE_SECRET_KEY", "").strip()
            or os.getenv("SUPABASE_SECRET", "").strip()
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_ANON_KEY", "").strip()
        )
        if not base_url:
            raise RelatedNoticeCacheRepositoryConfigError("SUPABASE_URL is required")
        if not api_key:
            raise RelatedNoticeCacheRepositoryConfigError(
                "SUPABASE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_SECRET, or SUPABASE_ANON_KEY is required"
            )
        raw_timeout = os.getenv("SUPABASE_HTTP_TIMEOUT_SECONDS", "").strip()
        timeout_seconds = 10.0
        if raw_timeout:
            try:
                timeout_seconds = float(raw_timeout)
            except ValueError as exc:
                raise RelatedNoticeCacheRepositoryConfigError(
                    "SUPABASE_HTTP_TIMEOUT_SECONDS must be numeric"
                ) from exc
        identity = load_phase1_identity()
        return cls(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            organization_id=str(identity.organization_id),
            timeout_seconds=timeout_seconds,
        )


class SupabaseRelatedNoticeCacheRepository(RelatedNoticeCacheRepository):
    def __init__(self, config: SupabaseRelatedNoticeCacheRepositoryConfig) -> None:
        self._config = config
        self._rest_url = f"{config.base_url}/rest/v1"
        self._supports_snapshot_set_id = True

    def get_cache(self, *, project_key: str, snapshot_set_id: str | None = None) -> RelatedNoticeCacheRow | None:
        snapshot_key = str(snapshot_set_id or "legacy").strip() or "legacy"
        try:
            rows, _headers = self._request_json(
                method="GET",
                path="/project_related_notice_cache",
                query=self._build_get_cache_query(project_key=project_key, snapshot_key=snapshot_key),
            )
        except RelatedNoticeCacheRepositoryError as exc:
            if not self._is_missing_snapshot_set_id_error(str(exc)):
                raise
            self._supports_snapshot_set_id = False
            rows, _headers = self._request_json(
                method="GET",
                path="/project_related_notice_cache",
                query=self._build_legacy_get_cache_query(project_key=project_key),
            )
        if not rows:
            return None
        normalized = dict(rows[0])
        normalized["snapshot_set_id"] = str(normalized.get("snapshot_set_id") or snapshot_key).strip() or "legacy"
        return normalized

    def upsert_cache(self, row: RelatedNoticeCacheRow) -> RelatedNoticeCacheRow:
        payload = dict(row)
        payload["organization_id"] = self._config.organization_id
        payload["project_key"] = str(payload.get("project_key") or "").strip()
        payload["snapshot_set_id"] = str(payload.get("snapshot_set_id") or "legacy").strip() or "legacy"
        try:
            rows, _headers = self._request_json(
                method="POST",
                path="/project_related_notice_cache",
                query=[("on_conflict", "organization_id,snapshot_set_id,project_key")],
                headers={"Prefer": "return=representation,resolution=merge-duplicates"},
                payload=payload,
            )
        except RelatedNoticeCacheRepositoryError as exc:
            message = str(exc)
            if not (
                self._is_missing_snapshot_set_id_error(message)
                or self._is_missing_snapshot_conflict_error(message)
            ):
                raise
            legacy_payload = dict(payload)
            if self._is_missing_snapshot_set_id_error(message):
                self._supports_snapshot_set_id = False
                legacy_payload.pop("snapshot_set_id", None)
            rows, _headers = self._request_json(
                method="POST",
                path="/project_related_notice_cache",
                query=[("on_conflict", "organization_id,project_key")],
                headers={"Prefer": "return=representation,resolution=merge-duplicates"},
                payload=legacy_payload,
            )
        if not isinstance(rows, list) or not rows:
            raise RelatedNoticeCacheRepositoryError("Supabase did not return the upserted related notice cache row")
        normalized = dict(rows[0])
        normalized["snapshot_set_id"] = str(normalized.get("snapshot_set_id") or payload["snapshot_set_id"]).strip() or "legacy"
        return normalized

    def list_queued(self, *, limit: int = 5) -> list[RelatedNoticeCacheRow]:
        try:
            rows, _headers = self._request_json(
                method="GET",
                path="/project_related_notice_cache",
                query=[
                    ("select", RELATED_NOTICE_CACHE_SELECT if self._supports_snapshot_set_id else RELATED_NOTICE_CACHE_SELECT_LEGACY),
                    ("organization_id", f"eq.{self._config.organization_id}"),
                    ("status", "eq.queued"),
                    ("order", "updated_at.asc"),
                    ("limit", str(max(1, int(limit or 1)))),
                ],
            )
        except RelatedNoticeCacheRepositoryError as exc:
            if not self._is_missing_snapshot_set_id_error(str(exc)):
                raise
            self._supports_snapshot_set_id = False
            rows, _headers = self._request_json(
                method="GET",
                path="/project_related_notice_cache",
                query=[
                    ("select", RELATED_NOTICE_CACHE_SELECT_LEGACY),
                    ("organization_id", f"eq.{self._config.organization_id}"),
                    ("status", "eq.queued"),
                    ("order", "updated_at.asc"),
                    ("limit", str(max(1, int(limit or 1)))),
                ],
            )
        return [dict(row) for row in rows] if isinstance(rows, list) else []

    def claim_queued(self, *, project_key: str, snapshot_set_id: str | None = None) -> RelatedNoticeCacheRow | None:
        snapshot_key = str(snapshot_set_id or "legacy").strip() or "legacy"
        query = [
            ("organization_id", f"eq.{self._config.organization_id}"),
            ("project_key", f"eq.{str(project_key or '').strip()}"),
            ("status", "eq.queued"),
            ("limit", "1"),
        ]
        if self._supports_snapshot_set_id:
            query.insert(2, ("snapshot_set_id", f"eq.{snapshot_key}"))
        try:
            rows, _headers = self._request_json(
                method="PATCH",
                path="/project_related_notice_cache",
                query=query,
                headers={"Prefer": "return=representation"},
                payload={"status": "running"},
            )
        except RelatedNoticeCacheRepositoryError as exc:
            if not self._is_missing_snapshot_set_id_error(str(exc)):
                raise
            self._supports_snapshot_set_id = False
            rows, _headers = self._request_json(
                method="PATCH",
                path="/project_related_notice_cache",
                query=[
                    ("organization_id", f"eq.{self._config.organization_id}"),
                    ("project_key", f"eq.{str(project_key or '').strip()}"),
                    ("status", "eq.queued"),
                    ("limit", "1"),
                ],
                headers={"Prefer": "return=representation"},
                payload={"status": "running"},
            )
        if not isinstance(rows, list) or not rows:
            return None
        normalized = dict(rows[0])
        normalized["snapshot_set_id"] = str(normalized.get("snapshot_set_id") or snapshot_key).strip() or "legacy"
        return normalized

    def _build_get_cache_query(self, *, project_key: str, snapshot_key: str) -> list[tuple[str, str]]:
        if not self._supports_snapshot_set_id:
            return self._build_legacy_get_cache_query(project_key=project_key)
        return [
            ("select", RELATED_NOTICE_CACHE_SELECT),
            ("organization_id", f"eq.{self._config.organization_id}"),
            ("project_key", f"eq.{project_key.strip()}"),
            ("snapshot_set_id", f"eq.{snapshot_key}"),
            ("limit", "1"),
        ]

    def _build_legacy_get_cache_query(self, *, project_key: str) -> list[tuple[str, str]]:
        return [
            ("select", RELATED_NOTICE_CACHE_SELECT_LEGACY),
            ("organization_id", f"eq.{self._config.organization_id}"),
            ("project_key", f"eq.{project_key.strip()}"),
            ("limit", "1"),
        ]

    @staticmethod
    def _is_missing_snapshot_set_id_error(message: str) -> bool:
        lowered = str(message or "").lower()
        return "project_related_notice_cache" in lowered and "snapshot_set_id" in lowered and "does not exist" in lowered

    @staticmethod
    def _is_missing_snapshot_conflict_error(message: str) -> bool:
        lowered = str(message or "").lower()
        return (
            ("on conflict" in lowered or "conflict specification" in lowered)
            and ("constraint" in lowered or "unique" in lowered or "exclusion" in lowered)
        )

    def _request_json(self, *, method: str, path: str, query=None, headers=None, payload=None):
        return request_json(
            rest_url=self._rest_url,
            api_key=self._config.api_key,
            timeout_seconds=self._config.timeout_seconds,
            method=method,
            path=path,
            query=query,
            headers=headers,
            payload=payload,
            error_cls=RelatedNoticeCacheRepositoryError,
        )
