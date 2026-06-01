from __future__ import annotations

from datetime import datetime
from typing import Literal
from typing import Protocol
from typing import TypedDict
from uuid import UUID


class LoginAuditLogRow(TypedDict):
    id: UUID | str
    organization_id: UUID | str
    user_id: UUID | str
    user_email: str
    user_role: str
    ip_address: str
    user_agent: str
    created_at: datetime | str


class LoginAuditLogRepositoryError(RuntimeError):
    pass


class LoginAuditLogRepositoryConfigError(LoginAuditLogRepositoryError):
    pass


class LoginAuditLogRepository(Protocol):
    def create_log(
        self,
        *,
        organization_id: UUID,
        user_id: UUID,
        user_email: str,
        user_role: str,
        ip_address: str,
        user_agent: str,
    ) -> LoginAuditLogRow: ...

    def list_logs(
        self,
        *,
        organization_id: UUID,
        limit: int,
    ) -> list[LoginAuditLogRow]: ...
