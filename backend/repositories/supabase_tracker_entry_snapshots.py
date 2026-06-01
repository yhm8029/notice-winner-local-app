from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import UUID

from .supabase_http import request_json
from .tracker_entry_snapshots import TrackerEntrySnapshotRepository
from .tracker_entry_snapshots import TrackerEntrySnapshotRepositoryConfigError
from .tracker_entry_snapshots import TrackerEntrySnapshotRepositoryError
from .tracker_entry_snapshots import TrackerEntrySnapshotRow

TRACKER_ENTRY_SNAPSHOT_SELECT = ",".join(
    (
        "tracker_entry_id",
        "organization_id",
        "summary_json",
        "detail_json",
        "export_json",
        "updated_at",
    )
)
TRACKER_ENTRY_SNAPSHOT_GET_BATCH_SIZE = 100


@dataclass(frozen=True)
class SupabaseTrackerEntrySnapshotRepositoryConfig:
    base_url: str
    api_key: str
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "SupabaseTrackerEntrySnapshotRepositoryConfig":
        base_url = os.getenv("SUPABASE_URL", "").strip()
        api_key = (
            os.getenv("SUPABASE_SECRET_KEY", "").strip()
            or os.getenv("SUPABASE_SECRET", "").strip()
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_ANON_KEY", "").strip()
        )
        if not base_url:
            raise TrackerEntrySnapshotRepositoryConfigError("SUPABASE_URL is required")
        if not api_key:
            raise TrackerEntrySnapshotRepositoryConfigError(
                "SUPABASE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_SECRET, or SUPABASE_ANON_KEY is required"
            )
        raw_timeout = os.getenv("SUPABASE_HTTP_TIMEOUT_SECONDS", "").strip()
        timeout_seconds = 10.0
        if raw_timeout:
            try:
                timeout_seconds = float(raw_timeout)
            except ValueError as exc:
                raise TrackerEntrySnapshotRepositoryConfigError(
                    "SUPABASE_HTTP_TIMEOUT_SECONDS must be numeric"
                ) from exc
        return cls(base_url=base_url.rstrip("/"), api_key=api_key, timeout_seconds=timeout_seconds)


class SupabaseTrackerEntrySnapshotRepository(TrackerEntrySnapshotRepository):
    def __init__(self, config: SupabaseTrackerEntrySnapshotRepositoryConfig) -> None:
        self._config = config
        self._rest_url = f"{config.base_url}/rest/v1"
        self._table_available = True

    def upsert_snapshots(
        self,
        *,
        organization_id: UUID,
        snapshots: list[dict[str, object]],
    ) -> list[TrackerEntrySnapshotRow]:
        if not snapshots or not self._table_available:
            return []
        payload = []
        for item in snapshots:
            tracker_entry_id = item.get("tracker_entry_id")
            if not tracker_entry_id:
                continue
            payload.append(
                {
                    "tracker_entry_id": str(tracker_entry_id),
                    "organization_id": str(organization_id),
                    "summary_json": dict(item.get("summary_json") or {}),
                    "detail_json": dict(item.get("detail_json") or {}),
                    "export_json": dict(item.get("export_json") or {}),
                    "updated_at": item.get("updated_at"),
                }
            )
        if not payload:
            return []
        try:
            rows, _headers = request_json(
                rest_url=self._rest_url,
                api_key=self._config.api_key,
                timeout_seconds=self._config.timeout_seconds,
                method="POST",
                path="/tracker_entry_snapshots",
                query=[("select", TRACKER_ENTRY_SNAPSHOT_SELECT), ("on_conflict", "tracker_entry_id")],
                headers={"Prefer": "resolution=merge-duplicates,return=representation"},
                payload=payload,
                allow_retry=True,
                error_cls=TrackerEntrySnapshotRepositoryError,
            )
        except TrackerEntrySnapshotRepositoryError as exc:
            if self._is_missing_table_error(str(exc)):
                self._table_available = False
                return []
            raise
        return [dict(item) for item in list(rows or [])]

    def get_snapshots(
        self,
        *,
        organization_id: UUID,
        tracker_entry_ids: list[UUID],
    ) -> list[TrackerEntrySnapshotRow]:
        if not tracker_entry_ids or not self._table_available:
            return []
        rows: list[TrackerEntrySnapshotRow] = []
        for start in range(0, len(tracker_entry_ids), TRACKER_ENTRY_SNAPSHOT_GET_BATCH_SIZE):
            batch = tracker_entry_ids[start:start + TRACKER_ENTRY_SNAPSHOT_GET_BATCH_SIZE]
            joined = ",".join(str(item) for item in batch)
            try:
                batch_rows, _headers = request_json(
                    rest_url=self._rest_url,
                    api_key=self._config.api_key,
                    timeout_seconds=self._config.timeout_seconds,
                    method="GET",
                    path="/tracker_entry_snapshots",
                    query=[
                        ("select", TRACKER_ENTRY_SNAPSHOT_SELECT),
                        ("organization_id", f"eq.{organization_id}"),
                        ("tracker_entry_id", f"in.({joined})"),
                    ],
                    error_cls=TrackerEntrySnapshotRepositoryError,
                )
            except TrackerEntrySnapshotRepositoryError as exc:
                if self._is_missing_table_error(str(exc)):
                    self._table_available = False
                    return []
                raise
            rows.extend(dict(item) for item in list(batch_rows or []))
        return rows

    @staticmethod
    def _is_missing_table_error(message: str) -> bool:
        text = str(message or "").lower()
        if "tracker_entry_snapshots" not in text:
            return False
        return (
            "does not exist" in text
            or "not found" in text
            or "pgrst" in text
            or "relation" in text
        )
