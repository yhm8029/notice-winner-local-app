from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from uuid import UUID

from .supabase_http import request_json
from .tracker_change_events import TrackerChangeEventRepository
from .tracker_change_events import TrackerChangeEventRepositoryConfigError
from .tracker_change_events import TrackerChangeEventRepositoryError
from .tracker_change_events import TrackerChangeEventRow

TRACKER_CHANGE_EVENT_SELECT = ",".join(
    (
        "id",
        "organization_id",
        "tracker_entry_id",
        "event_type",
        "field_name",
        "old_value",
        "new_value",
        "old_value_norm",
        "new_value_norm",
        "source_run_id",
        "source_kind",
        "source_ref",
        "extractor_version",
        "reason_code",
        "batch_key",
        "dedupe_key",
        "is_silent",
        "created_at",
        "is_read",
        "read_at",
    )
)


@dataclass(frozen=True)
class SupabaseTrackerChangeEventRepositoryConfig:
    base_url: str
    api_key: str
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "SupabaseTrackerChangeEventRepositoryConfig":
        base_url = os.getenv("SUPABASE_URL", "").strip()
        api_key = (
            os.getenv("SUPABASE_SECRET_KEY", "").strip()
            or os.getenv("SUPABASE_SECRET", "").strip()
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_ANON_KEY", "").strip()
        )
        if not base_url:
            raise TrackerChangeEventRepositoryConfigError("SUPABASE_URL is required")
        if not api_key:
            raise TrackerChangeEventRepositoryConfigError(
                "SUPABASE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_SECRET, or SUPABASE_ANON_KEY is required"
            )
        raw_timeout = os.getenv("SUPABASE_HTTP_TIMEOUT_SECONDS", "").strip()
        timeout_seconds = 10.0
        if raw_timeout:
            try:
                timeout_seconds = float(raw_timeout)
            except ValueError as exc:
                raise TrackerChangeEventRepositoryConfigError(
                    "SUPABASE_HTTP_TIMEOUT_SECONDS must be numeric"
                ) from exc
        return cls(base_url=base_url.rstrip("/"), api_key=api_key, timeout_seconds=timeout_seconds)


class SupabaseTrackerChangeEventRepository(TrackerChangeEventRepository):
    def __init__(self, config: SupabaseTrackerChangeEventRepositoryConfig) -> None:
        self._config = config
        self._rest_url = f"{config.base_url}/rest/v1"

    def append_events(self, *, organization_id: UUID, events: list[dict[str, object]]) -> list[TrackerChangeEventRow]:
        if not events:
            return []
        payload = []
        for item in events:
            payload.append(
                {
                    "organization_id": str(organization_id),
                    "tracker_entry_id": str(item.get("tracker_entry_id") or ""),
                    "event_type": str(item.get("event_type") or "").strip(),
                    "field_name": str(item.get("field_name") or "").strip() or None,
                    "old_value": str(item.get("old_value") or ""),
                    "new_value": str(item.get("new_value") or ""),
                    "old_value_norm": str(item.get("old_value_norm") or "").strip() or None,
                    "new_value_norm": str(item.get("new_value_norm") or "").strip() or None,
                    "source_run_id": str(item.get("source_run_id") or "").strip() or None,
                    "source_kind": str(item.get("source_kind") or "").strip(),
                    "source_ref": str(item.get("source_ref") or "").strip() or None,
                    "extractor_version": str(item.get("extractor_version") or "").strip() or None,
                    "reason_code": str(item.get("reason_code") or "").strip() or None,
                    "batch_key": str(item.get("batch_key") or "").strip() or None,
                    "dedupe_key": str(item.get("dedupe_key") or "").strip(),
                    "is_silent": bool(item.get("is_silent")),
                    "is_read": bool(item.get("is_read")),
                }
            )
        rows, _headers = request_json(
            rest_url=self._rest_url,
            api_key=self._config.api_key,
            timeout_seconds=self._config.timeout_seconds,
            method="POST",
            path="/tracker_change_events",
            query=[("select", TRACKER_CHANGE_EVENT_SELECT), ("on_conflict", "dedupe_key")],
            headers={"Prefer": "resolution=merge-duplicates,return=representation"},
            payload=payload,
            allow_retry=True,
            error_cls=TrackerChangeEventRepositoryError,
        )
        return [dict(item) for item in list(rows or [])]

    def list_events(
        self,
        *,
        organization_id: UUID,
        limit: int,
        tracker_entry_id: UUID | None = None,
        include_silent: bool = False,
    ) -> list[TrackerChangeEventRow]:
        query: list[tuple[str, str]] = [
            ("select", TRACKER_CHANGE_EVENT_SELECT),
            ("organization_id", f"eq.{organization_id}"),
            ("order", "created_at.desc"),
            ("limit", str(limit)),
        ]
        if tracker_entry_id is not None:
            query.append(("tracker_entry_id", f"eq.{tracker_entry_id}"))
        if not include_silent:
            query.append(("is_silent", "is.false"))
        rows, _headers = request_json(
            rest_url=self._rest_url,
            api_key=self._config.api_key,
            timeout_seconds=self._config.timeout_seconds,
            method="GET",
            path="/tracker_change_events",
            query=query,
            error_cls=TrackerChangeEventRepositoryError,
        )
        return [dict(item) for item in list(rows or [])]

    def count_unread(self, *, organization_id: UUID) -> int:
        rows, headers = request_json(
            rest_url=self._rest_url,
            api_key=self._config.api_key,
            timeout_seconds=self._config.timeout_seconds,
            method="GET",
            path="/tracker_change_events",
            query=[
                ("select", "id"),
                ("organization_id", f"eq.{organization_id}"),
                ("is_read", "is.false"),
                ("is_silent", "is.false"),
                ("limit", "1"),
            ],
            headers={"Prefer": "count=exact"},
            error_cls=TrackerChangeEventRepositoryError,
        )
        _ = rows
        content_range = str(headers.get("Content-Range") or "")
        if "/" in content_range:
            try:
                return int(content_range.split("/", 1)[1])
            except Exception:
                return 0
        return 0

    def mark_read(
        self,
        *,
        organization_id: UUID,
        event_ids: list[UUID] | None = None,
        tracker_entry_id: UUID | None = None,
    ) -> int:
        query: list[tuple[str, str]] = [
            ("organization_id", f"eq.{organization_id}"),
            ("is_read", "is.false"),
        ]
        if event_ids:
            joined = ",".join(str(item) for item in event_ids)
            query.append(("id", f"in.({joined})"))
        elif tracker_entry_id is not None:
            query.append(("tracker_entry_id", f"eq.{tracker_entry_id}"))
        else:
            return 0
        rows, _headers = request_json(
            rest_url=self._rest_url,
            api_key=self._config.api_key,
            timeout_seconds=self._config.timeout_seconds,
            method="PATCH",
            path="/tracker_change_events",
            query=[("select", "id"), *query],
            headers={"Prefer": "return=representation"},
            payload={"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()},
            error_cls=TrackerChangeEventRepositoryError,
        )
        return len(list(rows or []))
