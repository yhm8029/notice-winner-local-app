from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from backend.phase1_defaults import load_phase1_identity

from .artifacts import ArtifactRepository
from .artifacts import ArtifactRepositoryConfigError
from .artifacts import ArtifactRepositoryError
from .artifacts import RunArtifactRow
from .supabase_http import request_json

ARTIFACT_SELECT = ",".join(
    (
        "id",
        "run_id",
        "organization_id",
        "artifact_type",
        "storage_path",
        "file_name",
        "mime_type",
        "size_bytes",
        "checksum",
        "meta_json",
        "created_at",
    )
)


@dataclass(frozen=True)
class SupabaseArtifactRepositoryConfig:
    base_url: str
    api_key: str
    organization_id: UUID
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "SupabaseArtifactRepositoryConfig":
        base_url = os.getenv("SUPABASE_URL", "").strip()
        api_key = (
            os.getenv("SUPABASE_SECRET_KEY", "").strip()
            or os.getenv("SUPABASE_SECRET", "").strip()
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_ANON_KEY", "").strip()
        )
        if not base_url:
            raise ArtifactRepositoryConfigError("SUPABASE_URL is required")
        if not api_key:
            raise ArtifactRepositoryConfigError(
                "SUPABASE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_SECRET, or SUPABASE_ANON_KEY is required"
            )

        raw_timeout = os.getenv("SUPABASE_HTTP_TIMEOUT_SECONDS", "").strip()
        timeout_seconds = 10.0
        if raw_timeout:
            try:
                timeout_seconds = float(raw_timeout)
            except ValueError as exc:
                raise ArtifactRepositoryConfigError(
                    "SUPABASE_HTTP_TIMEOUT_SECONDS must be numeric"
                ) from exc

        identity = load_phase1_identity()
        return cls(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            organization_id=identity.organization_id,
            timeout_seconds=timeout_seconds,
        )


class SupabaseArtifactRepository(ArtifactRepository):
    def __init__(self, config: SupabaseArtifactRepositoryConfig) -> None:
        self._config = config
        self._rest_url = f"{config.base_url}/rest/v1"

    def create_artifact(self, row: RunArtifactRow) -> RunArtifactRow:
        rows, _headers = self._request_json(
            method="POST",
            path="/run_artifacts",
            headers={"Prefer": "return=representation"},
            payload=row,
        )
        if not isinstance(rows, list) or not rows:
            raise ArtifactRepositoryError("Supabase did not return the created artifact")
        return dict(rows[0])

    def list_artifacts(self, *, run_id: UUID) -> list[RunArtifactRow]:
        rows, _headers = self._request_json(
            method="GET",
            path="/run_artifacts",
            query=[
                ("select", ARTIFACT_SELECT),
                ("organization_id", f"eq.{self._config.organization_id}"),
                ("run_id", f"eq.{run_id}"),
                ("order", "created_at.desc"),
            ],
        )
        return [dict(row) for row in rows]

    def get_artifact(self, artifact_id: UUID) -> RunArtifactRow | None:
        rows, _headers = self._request_json(
            method="GET",
            path="/run_artifacts",
            query=[
                ("select", ARTIFACT_SELECT),
                ("organization_id", f"eq.{self._config.organization_id}"),
                ("id", f"eq.{artifact_id}"),
                ("limit", "1"),
            ],
        )
        if not rows:
            return None
        return dict(rows[0])

    def delete_artifacts_for_run(self, run_id: UUID) -> int:
        rows, _headers = self._request_json(
            method="DELETE",
            path="/run_artifacts",
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
            error_cls=ArtifactRepositoryError,
        )
