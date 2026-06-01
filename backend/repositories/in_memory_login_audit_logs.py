from __future__ import annotations

from datetime import datetime
from datetime import timezone
from uuid import UUID
from uuid import uuid4

from .login_audit_logs import LoginAuditLogRepository
from .login_audit_logs import LoginAuditLogRow


class InMemoryLoginAuditLogRepository(LoginAuditLogRepository):
    def __init__(self) -> None:
        self._rows_by_id: dict[UUID, LoginAuditLogRow] = {}

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
        row_id = uuid4()
        created_at = datetime.now(timezone.utc)
        row: LoginAuditLogRow = {
            "id": row_id,
            "organization_id": organization_id,
            "user_id": user_id,
            "user_email": user_email,
            "user_role": user_role,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": created_at,
        }
        self._rows_by_id[row_id] = row
        return dict(row)

    def list_logs(
        self,
        *,
        organization_id: UUID,
        limit: int,
    ) -> list[LoginAuditLogRow]:
        rows = [
            dict(row)
            for row in self._rows_by_id.values()
            if row["organization_id"] == organization_id
        ]
        rows.sort(key=lambda item: (item["created_at"], str(item["id"])), reverse=True)
        return rows[:limit]
