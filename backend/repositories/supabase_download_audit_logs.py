from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from .download_audit_logs import DownloadAuditLogRepository
from .download_audit_logs import DownloadAuditLogRepositoryConfigError
from .download_audit_logs import DownloadAuditLogRepositoryError
from .download_audit_logs import DownloadAuditLogRow
from .download_audit_logs import DownloadFormat
from .download_audit_logs import DownloadScope
from .download_audit_logs import DownloadSourcePage
from .supabase_http import request_json

DOWNLOAD_AUDIT_LOG_SELECT = ",".join(
    (
        "id",
        "organization_id",
        "user_id",
        "user_email",
        "user_role",
        "download_scope",
        "download_format",
        "source_page",
        "file_name",
        "created_at",
    )
)


@dataclass(frozen=True)
class SupabaseDownloadAuditLogRepositoryConfig:
    base_url: str
    api_key: str
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "SupabaseDownloadAuditLogRepositoryConfig":
        base_url = os.getenv("SUPABASE_URL", "").strip()
        api_key = (
            os.getenv("SUPABASE_SECRET_KEY", "").strip()
            or os.getenv("SUPABASE_SECRET", "").strip()
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_ANON_KEY", "").strip()
        )
        if not base_url:
            raise DownloadAuditLogRepositoryConfigError("SUPABASE_URL is required")
        if not api_key:
            raise DownloadAuditLogRepositoryConfigError(
                "SUPABASE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_SECRET, or SUPABASE_ANON_KEY is required"
            )
        raw_timeout = os.getenv("SUPABASE_HTTP_TIMEOUT_SECONDS", "").strip()
        timeout_seconds = 10.0
        if raw_timeout:
            try:
                timeout_seconds = float(raw_timeout)
            except ValueError as exc:
                raise DownloadAuditLogRepositoryConfigError(
                    "SUPABASE_HTTP_TIMEOUT_SECONDS must be numeric"
                ) from exc
        return cls(base_url=base_url.rstrip("/"), api_key=api_key, timeout_seconds=timeout_seconds)


class SupabaseDownloadAuditLogRepository(DownloadAuditLogRepository):
    def __init__(self, config: SupabaseDownloadAuditLogRepositoryConfig) -> None:
        self._config = config
        self._rest_url = f"{config.base_url}/rest/v1"

    def create_log(
        self,
        *,
        organization_id: UUID,
        user_id: UUID | None,
        user_email: str,
        user_role: str,
        download_scope: DownloadScope,
        download_format: DownloadFormat,
        source_page: DownloadSourcePage,
        file_name: str,
    ) -> DownloadAuditLogRow:
        rows, _headers = self._request_json(
            method="POST",
            path="/download_audit_logs",
            headers={"Prefer": "return=representation"},
            payload={
                "organization_id": str(organization_id),
                "user_id": str(user_id) if user_id is not None else None,
                "user_email": user_email,
                "user_role": user_role,
                "download_scope": download_scope,
                "download_format": download_format,
                "source_page": source_page,
                "file_name": file_name,
            },
        )
        if not isinstance(rows, list) or not rows:
            raise DownloadAuditLogRepositoryError("Supabase did not return the created audit log")
        return dict(rows[0])

    def list_logs(
        self,
        *,
        organization_id: UUID,
        limit: int,
    ) -> list[DownloadAuditLogRow]:
        rows, _headers = self._request_json(
            method="GET",
            path="/download_audit_logs",
            query=[
                ("select", DOWNLOAD_AUDIT_LOG_SELECT),
                ("organization_id", f"eq.{organization_id}"),
                ("order", "created_at.desc"),
                ("limit", str(limit)),
            ],
        )
        return [dict(row) for row in list(rows or [])]

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
            error_cls=DownloadAuditLogRepositoryError,
        )
