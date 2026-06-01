from __future__ import annotations

from uuid import UUID
from uuid import uuid4

from .login_audit_logs import LoginAuditLogRepository
from .login_audit_logs import LoginAuditLogRepositoryConfigError
from .login_audit_logs import LoginAuditLogRow
from .sqlite_common import LocalRowsStore
from .sqlite_common import SqliteRepositoryConfig
from .sqlite_common import row_sort_text
from .sqlite_common import utc_now_text

TABLE_NAME = "login_audit_logs"


class SqliteLoginAuditLogRepository(LoginAuditLogRepository):
    def __init__(self, config: SqliteRepositoryConfig | None = None) -> None:
        self._store = LocalRowsStore(
            config or SqliteRepositoryConfig.from_env(error_cls=LoginAuditLogRepositoryConfigError)
        )

    def create_log(
        self,
        *,
        organization_id: UUID,
        user_id: UUID,
        user_email: str,
        user_role: str,
        ip_address: str,
        user_agent: str,
    ) -> LoginAuditLogRow:
        row_id = str(uuid4())
        row: LoginAuditLogRow = {
            "id": row_id,
            "organization_id": str(organization_id),
            "user_id": str(user_id),
            "user_email": user_email,
            "user_role": user_role,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": utc_now_text(),
        }
        return self._store.upsert_row(TABLE_NAME, row_id, row, created_at=row["created_at"])

    def list_logs(
        self,
        *,
        organization_id: UUID,
        limit: int,
    ) -> list[LoginAuditLogRow]:
        rows = [
            dict(row)
            for row in self._store.list_rows(TABLE_NAME)
            if str(row.get("organization_id")) == str(organization_id)
        ]
        rows.sort(key=lambda item: (row_sort_text(item.get("created_at")), str(item.get("id") or "")), reverse=True)
        return rows[:limit]
