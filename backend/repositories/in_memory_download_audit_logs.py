from __future__ import annotations

from datetime import datetime
from datetime import timezone
from uuid import UUID
from uuid import uuid4

from .download_audit_logs import DownloadAuditLogRepository
from .download_audit_logs import DownloadAuditLogRow
from .download_audit_logs import DownloadFormat
from .download_audit_logs import DownloadScope
from .download_audit_logs import DownloadSourcePage


class InMemoryDownloadAuditLogRepository(DownloadAuditLogRepository):
    def __init__(self) -> None:
        self._rows_by_id: dict[UUID, DownloadAuditLogRow] = {}
        self._row_order_by_id: dict[UUID, int] = {}
        self._next_row_order = 0

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
        row_id = uuid4()
        created_at = datetime.now(timezone.utc)
        row: DownloadAuditLogRow = {
            "id": row_id,
            "organization_id": organization_id,
            "user_id": user_id,
            "user_email": user_email,
            "user_role": user_role,
            "download_scope": download_scope,
            "download_format": download_format,
            "source_page": source_page,
            "file_name": file_name,
            "created_at": created_at,
        }
        self._rows_by_id[row_id] = row
        self._row_order_by_id[row_id] = self._next_row_order
        self._next_row_order += 1
        return dict(row)

    def list_logs(
        self,
        *,
        organization_id: UUID,
        limit: int,
    ) -> list[DownloadAuditLogRow]:
        rows = [
            dict(row)
            for row in self._rows_by_id.values()
            if row["organization_id"] == organization_id
        ]
        rows.sort(key=lambda item: (item["created_at"], self._row_order_by_id.get(item["id"], -1)), reverse=True)
        return rows[:limit]
