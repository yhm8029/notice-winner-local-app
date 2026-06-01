from __future__ import annotations

from typing import Any
from typing import Protocol
from uuid import UUID

RunRow = dict[str, Any]


class RunRepositoryError(RuntimeError):
    pass


class RunRepositoryConfigError(RunRepositoryError):
    pass


class RunRepository(Protocol):
    def create_run(self, row: RunRow) -> RunRow: ...

    def get_run(self, run_id: UUID) -> RunRow | None: ...

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
    ) -> tuple[list[RunRow], int]: ...

    def update_run(self, run_id: UUID, fields: dict[str, Any]) -> RunRow | None: ...

    def delete_run(self, run_id: UUID) -> bool: ...
