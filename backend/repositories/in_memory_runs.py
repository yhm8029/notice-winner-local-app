from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import UUID
from uuid import uuid4

from .runs import RunRepository
from .runs import RunRow


class InMemoryRunRepository(RunRepository):
    def __init__(self) -> None:
        self._runs: dict[UUID, RunRow] = {}

    def create_run(self, row: RunRow) -> RunRow:
        run_id = uuid4()
        created_at = datetime.now(timezone.utc)
        stored: RunRow = {
            "id": run_id,
            **row,
            "created_at": created_at,
            "updated_at": created_at,
            "started_at": None,
            "finished_at": None,
        }
        self._runs[run_id] = stored
        return stored

    def get_run(self, run_id: UUID) -> RunRow | None:
        row = self._runs.get(run_id)
        if row is None:
            return None
        return dict(row)

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
    ) -> tuple[list[RunRow], int]:
        rows = []
        for row in self._runs.values():
            if status and row["status"] != status:
                continue
            if run_type and row["run_type"] != run_type:
                continue
            if parent_run_id is not None and row.get("parent_run_id") != str(parent_run_id):
                continue
            created_at = row["created_at"]
            if date_from and created_at.strftime("%Y-%m-%d") < date_from:
                continue
            if date_to and created_at.strftime("%Y-%m-%d") > date_to:
                continue
            rows.append(dict(row))

        rows.sort(key=lambda item: item["created_at"], reverse=True)
        total = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        return rows[start:end], total

    def update_run(self, run_id: UUID, fields: dict[str, Any]) -> RunRow | None:
        row = self._runs.get(run_id)
        if row is None:
            return None
        row.update(fields)
        row["updated_at"] = datetime.now(timezone.utc)
        return dict(row)

    def delete_run(self, run_id: UUID) -> bool:
        return self._runs.pop(run_id, None) is not None
