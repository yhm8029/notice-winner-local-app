from __future__ import annotations

from typing import Any
from typing import Protocol
from uuid import UUID

RunLogRow = dict[str, Any]


class RunLogRepositoryError(RuntimeError):
    pass


class RunLogRepositoryConfigError(RunLogRepositoryError):
    pass


class RunLogRepository(Protocol):
    def create_log(self, row: RunLogRow) -> RunLogRow: ...

    def list_logs(
        self,
        *,
        run_id: UUID,
        cursor: int | None,
        limit: int,
    ) -> tuple[list[RunLogRow], int | None]: ...

    def delete_logs_for_run(self, run_id: UUID) -> int: ...
