from __future__ import annotations

from datetime import datetime
from datetime import timezone
from uuid import UUID

from .logs import RunLogRepository
from .logs import RunLogRow


class InMemoryRunLogRepository(RunLogRepository):
    def __init__(self) -> None:
        self._logs_by_run: dict[UUID, list[RunLogRow]] = {}
        self._next_id = 1

    def create_log(self, row: RunLogRow) -> RunLogRow:
        created_at = row.get("created_at") or datetime.now(timezone.utc)
        stored: RunLogRow = {
            "id": self._next_id,
            **row,
            "created_at": created_at,
        }
        self._next_id += 1
        run_id = UUID(str(stored["run_id"]))
        self._logs_by_run.setdefault(run_id, []).append(stored)
        return dict(stored)

    def list_logs(
        self,
        *,
        run_id: UUID,
        cursor: int | None,
        limit: int,
    ) -> tuple[list[RunLogRow], int | None]:
        items = sorted(
            self._logs_by_run.get(run_id, []),
            key=lambda item: int(item["id"]),
            reverse=True,
        )
        if cursor is not None:
            items = [item for item in items if int(item["id"]) < cursor]

        page_items = items[:limit]
        next_cursor = int(page_items[-1]["id"]) if len(items) > limit and page_items else None
        return [dict(item) for item in page_items], next_cursor

    def delete_logs_for_run(self, run_id: UUID) -> int:
        items = self._logs_by_run.pop(run_id, [])
        return len(items)
