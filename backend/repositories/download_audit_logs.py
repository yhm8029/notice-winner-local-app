from __future__ import annotations

from datetime import datetime
from typing import Literal
from typing import Protocol
from typing import TypedDict
from uuid import UUID

DownloadScope = Literal["my", "company", "global"]
DownloadFormat = Literal["xlsx", "csv"]
DownloadSourcePage = Literal["my_active_sales", "company_active_sales", "tracker_entries"]


class DownloadAuditLogRow(TypedDict):
    id: UUID | str
    organization_id: UUID | str
    user_id: UUID | str | None
    user_email: str
    user_role: str
    download_scope: DownloadScope
    download_format: DownloadFormat
    source_page: DownloadSourcePage
    file_name: str
    created_at: datetime | str


class DownloadAuditLogRepositoryError(RuntimeError):
    pass


class DownloadAuditLogRepositoryConfigError(DownloadAuditLogRepositoryError):
    pass


class DownloadAuditLogRepository(Protocol):
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
    ) -> DownloadAuditLogRow: ...

    def list_logs(
        self,
        *,
        organization_id: UUID,
        limit: int,
    ) -> list[DownloadAuditLogRow]: ...
