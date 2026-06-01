from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from uuid import UUID

from .backfill_conflicts import BackfillConflictRepository
from .backfill_conflicts import BackfillConflictRepositoryConfigError
from .backfill_conflicts import BackfillConflictRepositoryError
from .backfill_conflicts import BackfillConflictRow
from .supabase_http import request_json

BACKFILL_CONFLICT_SELECT = ",".join(
    (
        "id",
        "organization_id",
        "tracker_entry_id",
        "field_name",
        "current_value",
        "candidate_value",
        "current_value_norm",
        "candidate_value_norm",
        "reason_code",
        "source_kind",
        "source_ref",
        "source_run_id",
        "extractor_version",
        "detected_at",
        "resolved_at",
        "resolution",
        "conflict_key",
    )
)


@dataclass(frozen=True)
class SupabaseBackfillConflictRepositoryConfig:
    base_url: str
    api_key: str
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "SupabaseBackfillConflictRepositoryConfig":
        base_url = os.getenv("SUPABASE_URL", "").strip()
        api_key = (
            os.getenv("SUPABASE_SECRET_KEY", "").strip()
            or os.getenv("SUPABASE_SECRET", "").strip()
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_ANON_KEY", "").strip()
        )
        if not base_url:
            raise BackfillConflictRepositoryConfigError("SUPABASE_URL is required")
        if not api_key:
            raise BackfillConflictRepositoryConfigError(
                "SUPABASE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_SECRET, or SUPABASE_ANON_KEY is required"
            )
        raw_timeout = os.getenv("SUPABASE_HTTP_TIMEOUT_SECONDS", "").strip()
        timeout_seconds = 10.0
        if raw_timeout:
            try:
                timeout_seconds = float(raw_timeout)
            except ValueError as exc:
                raise BackfillConflictRepositoryConfigError(
                    "SUPABASE_HTTP_TIMEOUT_SECONDS must be numeric"
                ) from exc
        return cls(base_url=base_url.rstrip("/"), api_key=api_key, timeout_seconds=timeout_seconds)


class SupabaseBackfillConflictRepository(BackfillConflictRepository):
    def __init__(self, config: SupabaseBackfillConflictRepositoryConfig) -> None:
        self._config = config
        self._rest_url = f"{config.base_url}/rest/v1"

    def upsert_conflicts(self, *, organization_id: UUID, conflicts: list[dict[str, object]]) -> list[BackfillConflictRow]:
        if not conflicts:
            return []
        payload = []
        for item in conflicts:
            payload.append(
                {
                    "organization_id": str(organization_id),
                    "tracker_entry_id": str(item.get("tracker_entry_id") or ""),
                    "field_name": str(item.get("field_name") or "").strip(),
                    "current_value": str(item.get("current_value") or ""),
                    "candidate_value": str(item.get("candidate_value") or ""),
                    "current_value_norm": str(item.get("current_value_norm") or "").strip() or None,
                    "candidate_value_norm": str(item.get("candidate_value_norm") or "").strip() or None,
                    "reason_code": str(item.get("reason_code") or "").strip(),
                    "source_kind": str(item.get("source_kind") or "").strip(),
                    "source_ref": str(item.get("source_ref") or "").strip() or None,
                    "source_run_id": str(item.get("source_run_id") or "").strip() or None,
                    "extractor_version": str(item.get("extractor_version") or "").strip() or None,
                    "resolution": str(item.get("resolution") or "").strip() or None,
                    "conflict_key": str(item.get("conflict_key") or "").strip(),
                }
            )
        rows, _headers = request_json(
            rest_url=self._rest_url,
            api_key=self._config.api_key,
            timeout_seconds=self._config.timeout_seconds,
            method="POST",
            path="/backfill_conflicts",
            query=[("select", BACKFILL_CONFLICT_SELECT), ("on_conflict", "conflict_key")],
            headers={"Prefer": "resolution=merge-duplicates,return=representation"},
            payload=payload,
            allow_retry=True,
            error_cls=BackfillConflictRepositoryError,
        )
        return [dict(item) for item in list(rows or [])]

    def list_conflicts(
        self,
        *,
        organization_id: UUID,
        limit: int,
        tracker_entry_id: UUID | None = None,
        source_run_id: UUID | None = None,
        include_resolved: bool = False,
    ) -> list[BackfillConflictRow]:
        query: list[tuple[str, str]] = [
            ("select", BACKFILL_CONFLICT_SELECT),
            ("organization_id", f"eq.{organization_id}"),
            ("order", "detected_at.desc"),
            ("limit", str(limit)),
        ]
        if tracker_entry_id is not None:
            query.append(("tracker_entry_id", f"eq.{tracker_entry_id}"))
        if source_run_id is not None:
            query.append(("source_run_id", f"eq.{source_run_id}"))
        if not include_resolved:
            query.append(("resolved_at", "is.null"))
        rows, _headers = request_json(
            rest_url=self._rest_url,
            api_key=self._config.api_key,
            timeout_seconds=self._config.timeout_seconds,
            method="GET",
            path="/backfill_conflicts",
            query=query,
            allow_retry=True,
            error_cls=BackfillConflictRepositoryError,
        )
        return [dict(item) for item in list(rows or [])]

    def resolve_conflict(
        self,
        *,
        organization_id: UUID,
        conflict_id: UUID,
        resolution: str,
    ) -> BackfillConflictRow | None:
        rows, _headers = request_json(
            rest_url=self._rest_url,
            api_key=self._config.api_key,
            timeout_seconds=self._config.timeout_seconds,
            method="PATCH",
            path="/backfill_conflicts",
            query=[
                ("select", BACKFILL_CONFLICT_SELECT),
                ("id", f"eq.{conflict_id}"),
                ("organization_id", f"eq.{organization_id}"),
            ],
            payload={
                "resolution": str(resolution).strip(),
                "resolved_at": datetime.now(timezone.utc).isoformat(),
            },
            headers={"Prefer": "return=representation"},
            allow_retry=True,
            error_cls=BackfillConflictRepositoryError,
        )
        items = list(rows or [])
        if not items:
            return None
        return dict(items[0])
