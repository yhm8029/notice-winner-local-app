from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from backend.phase1_defaults import load_phase1_identity

from .logs import RunLogRepository
from .logs import RunLogRepositoryConfigError
from .logs import RunLogRepositoryError
from .logs import RunLogRow
from .supabase_http import request_json

RUN_LOG_SELECT = ",".join(
    (
        "id",
        "run_id",
        "organization_id",
        "level",
        "stage",
        "message",
        "meta_json",
        "created_at",
    )
)


@dataclass(frozen=True)
class SupabaseRunLogRepositoryConfig:
    base_url: str
    api_key: str
    organization_id: UUID
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "SupabaseRunLogRepositoryConfig":
        base_url = os.getenv("SUPABASE_URL", "").strip()
        api_key = (
            os.getenv("SUPABASE_SECRET_KEY", "").strip()
            or os.getenv("SUPABASE_SECRET", "").strip()
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_ANON_KEY", "").strip()
        )
        if not base_url:
            raise RunLogRepositoryConfigError("SUPABASE_URL is required")
        if not api_key:
            raise RunLogRepositoryConfigError(
                "SUPABASE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_SECRET, or SUPABASE_ANON_KEY is required"
            )

        raw_timeout = os.getenv("SUPABASE_HTTP_TIMEOUT_SECONDS", "").strip()
        timeout_seconds = 10.0
        if raw_timeout:
            try:
                timeout_seconds = float(raw_timeout)
            except ValueError as exc:
                raise RunLogRepositoryConfigError(
                    "SUPABASE_HTTP_TIMEOUT_SECONDS must be numeric"
                ) from exc

        identity = load_phase1_identity()
        return cls(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            organization_id=identity.organization_id,
            timeout_seconds=timeout_seconds,
        )


class SupabaseRunLogRepository(RunLogRepository):
    def __init__(self, config: SupabaseRunLogRepositoryConfig) -> None:
        self._config = config
        self._rest_url = f"{config.base_url}/rest/v1"

    def create_log(self, row: RunLogRow) -> RunLogRow:
        rows, _headers = self._request_json(
            method="POST",
            path="/pipeline_logs",
            headers={"Prefer": "return=representation"},
            payload=row,
        )
        if not isinstance(rows, list) or not rows:
            raise RunLogRepositoryError("Supabase did not return the created log")
        return self._normalize_row(rows[0])

    def list_logs(
        self,
        *,
        run_id: UUID,
        cursor: int | None,
        limit: int,
    ) -> tuple[list[RunLogRow], int | None]:
        query: list[tuple[str, str]] = [
            ("select", RUN_LOG_SELECT),
            ("organization_id", f"eq.{self._config.organization_id}"),
            ("run_id", f"eq.{run_id}"),
            ("order", "id.desc"),
            ("limit", str(limit + 1)),
        ]
        if cursor is not None:
            query.append(("id", f"lt.{cursor}"))

        rows, _headers = self._request_json(
            method="GET",
            path="/pipeline_logs",
            query=query,
        )
        page_items = rows[:limit]
        next_cursor = int(page_items[-1]["id"]) if len(rows) > limit and page_items else None
        return [self._normalize_row(row) for row in page_items], next_cursor

    def delete_logs_for_run(self, run_id: UUID) -> int:
        rows, _headers = self._request_json(
            method="DELETE",
            path="/pipeline_logs",
            query=[
                ("organization_id", f"eq.{self._config.organization_id}"),
                ("run_id", f"eq.{run_id}"),
            ],
            headers={"Prefer": "return=representation"},
        )
        return len(rows)

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        query: list[tuple[str, str]] | None = None,
        headers: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]] | dict[str, Any], dict[str, str]]:
        return request_json(
            rest_url=self._rest_url,
            api_key=self._config.api_key,
            timeout_seconds=self._config.timeout_seconds,
            method=method,
            path=path,
            query=query,
            headers=headers,
            payload=payload,
            error_cls=RunLogRepositoryError,
        )

    def _normalize_row(self, row: dict[str, Any]) -> RunLogRow:
        normalized = dict(row)
        normalized["id"] = int(normalized["id"])
        normalized["meta_json"] = dict(normalized.get("meta_json") or {})
        return normalized
