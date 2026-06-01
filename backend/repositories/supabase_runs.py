from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID

from backend.phase1_defaults import load_phase1_identity

from .runs import RunRepository
from .runs import RunRepositoryConfigError
from .runs import RunRepositoryError
from .runs import RunRow
from .supabase_http import request_json

RUN_SELECT = ",".join(
    (
        "id",
        "organization_id",
        "requested_by",
        "parent_run_id",
        "status",
        "run_type",
        "source_mode",
        "started_at",
        "finished_at",
        "params_json",
        "summary_json",
        "error_json",
        "progress_stage",
        "progress_current",
        "progress_total",
        "cancel_requested",
        "created_at",
        "updated_at",
    )
)


@dataclass(frozen=True)
class SupabaseRunRepositoryConfig:
    base_url: str
    api_key: str
    organization_id: UUID
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "SupabaseRunRepositoryConfig":
        base_url = os.getenv("SUPABASE_URL", "").strip()
        api_key = (
            os.getenv("SUPABASE_SECRET_KEY", "").strip()
            or os.getenv("SUPABASE_SECRET", "").strip()
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_ANON_KEY", "").strip()
        )
        if not base_url:
            raise RunRepositoryConfigError("SUPABASE_URL is required")
        if not api_key:
            raise RunRepositoryConfigError(
                "SUPABASE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_SECRET, or SUPABASE_ANON_KEY is required"
            )

        raw_timeout = os.getenv("SUPABASE_HTTP_TIMEOUT_SECONDS", "").strip()
        timeout_seconds = 10.0
        if raw_timeout:
            try:
                timeout_seconds = float(raw_timeout)
            except ValueError as exc:
                raise RunRepositoryConfigError(
                    "SUPABASE_HTTP_TIMEOUT_SECONDS must be numeric"
                ) from exc

        identity = load_phase1_identity()
        return cls(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            organization_id=identity.organization_id,
            timeout_seconds=timeout_seconds,
        )


class SupabaseRunRepository(RunRepository):
    def __init__(self, config: SupabaseRunRepositoryConfig) -> None:
        self._config = config
        self._rest_url = f"{config.base_url}/rest/v1"

    def create_run(self, row: RunRow) -> RunRow:
        rows, _headers = self._request_json(
            method="POST",
            path="/pipeline_runs",
            headers={"Prefer": "return=representation"},
            payload=row,
        )
        if not isinstance(rows, list) or not rows:
            raise RunRepositoryError("Supabase did not return the created run")
        return dict(rows[0])

    def get_run(self, run_id: UUID) -> RunRow | None:
        rows, _headers = self._request_json(
            method="GET",
            path="/pipeline_runs",
            query=[
                ("select", RUN_SELECT),
                ("organization_id", f"eq.{self._config.organization_id}"),
                ("id", f"eq.{run_id}"),
                ("limit", "1"),
            ],
        )
        if not rows:
            return None
        return dict(rows[0])

    def list_runs(
        self,
        *,
        page: int,
        page_size: int,
        status: str,
        run_type: str,
        parent_run_id: UUID | None,
        date_from: str,
        date_to: str,
    ) -> tuple[list[RunRow], int]:
        query: list[tuple[str, str]] = [
            ("select", RUN_SELECT),
            ("organization_id", f"eq.{self._config.organization_id}"),
            ("order", "created_at.desc"),
            ("order", "id.desc"),
            ("limit", str(page_size)),
            ("offset", str((page - 1) * page_size)),
        ]
        if status:
            query.append(("status", f"eq.{status}"))
        if run_type:
            query.append(("run_type", f"eq.{run_type}"))
        if parent_run_id is not None:
            query.append(("parent_run_id", f"eq.{parent_run_id}"))
        if date_from:
            start = self._normalize_date(date_from)
            query.append(("created_at", f"gte.{start}T00:00:00Z"))
        if date_to:
            end = self._normalize_date(date_to)
            query.append(("created_at", f"lte.{end}T23:59:59.999999Z"))

        rows, headers = self._request_json(
            method="GET",
            path="/pipeline_runs",
            query=query,
            headers={"Prefer": "count=exact"},
        )
        total = self._parse_total_count(headers, fallback=len(rows))
        return [dict(row) for row in rows], total

    def update_run(self, run_id: UUID, fields: dict[str, Any]) -> RunRow | None:
        rows, _headers = self._request_json(
            method="PATCH",
            path="/pipeline_runs",
            query=[
                ("organization_id", f"eq.{self._config.organization_id}"),
                ("id", f"eq.{run_id}"),
            ],
            headers={"Prefer": "return=representation"},
            payload=fields,
        )
        if not rows:
            return None
        return dict(rows[0])

    def delete_run(self, run_id: UUID) -> bool:
        rows, _headers = self._request_json(
            method="DELETE",
            path="/pipeline_runs",
            query=[
                ("organization_id", f"eq.{self._config.organization_id}"),
                ("id", f"eq.{run_id}"),
            ],
            headers={"Prefer": "return=representation"},
        )
        return bool(rows)

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
            error_cls=RunRepositoryError,
        )

    def _parse_total_count(self, headers: dict[str, str], *, fallback: int) -> int:
        content_range = headers.get("Content-Range", "")
        if "/" not in content_range:
            return fallback
        total = content_range.rsplit("/", 1)[-1].strip()
        if not total or total == "*":
            return fallback
        try:
            return int(total)
        except ValueError:
            return fallback

    def _normalize_date(self, value: str) -> str:
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError as exc:
            raise RunRepositoryError("date filters must be YYYY-MM-DD") from exc
