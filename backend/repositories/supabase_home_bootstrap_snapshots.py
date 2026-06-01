from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from uuid import UUID

from .home_bootstrap_snapshots import HomeBootstrapSnapshotRepository
from .home_bootstrap_snapshots import HomeBootstrapSnapshotRepositoryConfigError
from .home_bootstrap_snapshots import HomeBootstrapSnapshotRepositoryError
from .home_bootstrap_snapshots import HomeBootstrapSnapshotRow
from .supabase_http import request_json

HOME_BOOTSTRAP_SNAPSHOT_SELECT = ",".join(
    (
        "organization_id",
        "snapshot_version",
        "payload_json",
        "generated_at",
        "invalidated_at",
        "created_at",
        "updated_at",
    )
)


@dataclass(frozen=True)
class SupabaseHomeBootstrapSnapshotRepositoryConfig:
    base_url: str
    api_key: str
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "SupabaseHomeBootstrapSnapshotRepositoryConfig":
        base_url = os.getenv("SUPABASE_URL", "").strip()
        api_key = (
            os.getenv("SUPABASE_SECRET_KEY", "").strip()
            or os.getenv("SUPABASE_SECRET", "").strip()
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_ANON_KEY", "").strip()
        )
        if not base_url:
            raise HomeBootstrapSnapshotRepositoryConfigError("SUPABASE_URL is required")
        if not api_key:
            raise HomeBootstrapSnapshotRepositoryConfigError(
                "SUPABASE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_SECRET, or SUPABASE_ANON_KEY is required"
            )
        raw_timeout = os.getenv("SUPABASE_HTTP_TIMEOUT_SECONDS", "").strip()
        timeout_seconds = 10.0
        if raw_timeout:
            try:
                timeout_seconds = float(raw_timeout)
            except ValueError as exc:
                raise HomeBootstrapSnapshotRepositoryConfigError(
                    "SUPABASE_HTTP_TIMEOUT_SECONDS must be numeric"
                ) from exc
        return cls(base_url=base_url.rstrip("/"), api_key=api_key, timeout_seconds=timeout_seconds)


class SupabaseHomeBootstrapSnapshotRepository(HomeBootstrapSnapshotRepository):
    def __init__(self, config: SupabaseHomeBootstrapSnapshotRepositoryConfig) -> None:
        self._config = config
        self._rest_url = f"{config.base_url}/rest/v1"
        self._table_available = True

    def get_snapshot(
        self,
        *,
        organization_id: UUID,
    ) -> HomeBootstrapSnapshotRow | None:
        if not self._table_available:
            return None
        try:
            rows, _headers = request_json(
                rest_url=self._rest_url,
                api_key=self._config.api_key,
                timeout_seconds=self._config.timeout_seconds,
                method="GET",
                path="/home_bootstrap_snapshots",
                query=[
                    ("select", HOME_BOOTSTRAP_SNAPSHOT_SELECT),
                    ("organization_id", f"eq.{organization_id}"),
                    ("limit", "1"),
                ],
                error_cls=HomeBootstrapSnapshotRepositoryError,
            )
        except HomeBootstrapSnapshotRepositoryError as exc:
            if self._is_missing_table_error(str(exc)):
                self._table_available = False
                return None
            raise
        if not isinstance(rows, list) or not rows:
            return None
        return dict(rows[0])

    def upsert_snapshot(
        self,
        *,
        organization_id: UUID,
        snapshot_version: int,
        payload_json: dict[str, object],
        generated_at: object,
    ) -> HomeBootstrapSnapshotRow | None:
        if not self._table_available:
            return None
        serialized_generated_at = self._serialize_timestamp(generated_at)
        payload = {
            "organization_id": str(organization_id),
            "snapshot_version": int(snapshot_version or 0),
            "payload_json": dict(payload_json or {}),
            "generated_at": serialized_generated_at,
            "invalidated_at": None,
            "updated_at": serialized_generated_at,
        }
        try:
            rows, _headers = request_json(
                rest_url=self._rest_url,
                api_key=self._config.api_key,
                timeout_seconds=self._config.timeout_seconds,
                method="POST",
                path="/home_bootstrap_snapshots",
                query=[("select", HOME_BOOTSTRAP_SNAPSHOT_SELECT), ("on_conflict", "organization_id")],
                headers={"Prefer": "resolution=merge-duplicates,return=representation"},
                payload=payload,
                allow_retry=True,
                error_cls=HomeBootstrapSnapshotRepositoryError,
            )
        except HomeBootstrapSnapshotRepositoryError as exc:
            if self._is_missing_table_error(str(exc)):
                self._table_available = False
                return None
            raise
        if not isinstance(rows, list) or not rows:
            return None
        return dict(rows[0])

    def invalidate_snapshot(
        self,
        *,
        organization_id: UUID,
    ) -> None:
        if not self._table_available:
            return
        now = datetime.now(timezone.utc).isoformat()
        try:
            request_json(
                rest_url=self._rest_url,
                api_key=self._config.api_key,
                timeout_seconds=self._config.timeout_seconds,
                method="PATCH",
                path="/home_bootstrap_snapshots",
                query=[("organization_id", f"eq.{organization_id}")],
                headers={"Prefer": "return=minimal"},
                payload={"invalidated_at": now, "updated_at": now},
                error_cls=HomeBootstrapSnapshotRepositoryError,
            )
        except HomeBootstrapSnapshotRepositoryError as exc:
            if self._is_missing_table_error(str(exc)):
                self._table_available = False
                return
            raise

    @staticmethod
    def _is_missing_table_error(message: str) -> bool:
        text = str(message or "").lower()
        if "home_bootstrap_snapshots" not in text:
            return False
        return (
            "does not exist" in text
            or "not found" in text
            or "pgrst" in text
            or "relation" in text
        )

    @staticmethod
    def _serialize_timestamp(value: object) -> object:
        if isinstance(value, datetime):
            return value.isoformat()
        return value
