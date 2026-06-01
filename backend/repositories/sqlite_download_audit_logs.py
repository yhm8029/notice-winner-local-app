from __future__ import annotations

from uuid import UUID
from uuid import uuid4

from .download_audit_logs import DownloadAuditLogRepository
from .download_audit_logs import DownloadAuditLogRepositoryConfigError
from .download_audit_logs import DownloadAuditLogRow
from .download_audit_logs import DownloadFormat
from .download_audit_logs import DownloadScope
from .download_audit_logs import DownloadSourcePage
from .sqlite_common import LocalRowsStore
from .sqlite_common import SqliteRepositoryConfig
from .sqlite_common import row_sort_text
from .sqlite_common import utc_now_text

TABLE_NAME = "download_audit_logs"


class SqliteDownloadAuditLogRepository(DownloadAuditLogRepository):
    def __init__(self, config: SqliteRepositoryConfig | None = None) -> None:
        self._store = LocalRowsStore(
            config or SqliteRepositoryConfig.from_env(error_cls=DownloadAuditLogRepositoryConfigError)
        )

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
        row_id = str(uuid4())
        row: DownloadAuditLogRow = {
            "id": row_id,
            "organization_id": str(organization_id),
            "user_id": str(user_id) if user_id is not None else None,
            "user_email": user_email,
            "user_role": user_role,
            "download_scope": download_scope,
            "download_format": download_format,
            "source_page": source_page,
            "file_name": file_name,
            "created_at": utc_now_text(),
        }
        return self._store.upsert_row(TABLE_NAME, row_id, row, created_at=row["created_at"])

    def list_logs(
        self,
        *,
        organization_id: UUID,
        limit: int,
    ) -> list[DownloadAuditLogRow]:
        rows = [
            dict(row)
            for row in self._store.list_rows(TABLE_NAME)
            if str(row.get("organization_id")) == str(organization_id)
        ]
        rows.sort(key=lambda item: (row_sort_text(item.get("created_at")), str(item.get("id") or "")), reverse=True)
        return rows[:limit]
