from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import UUID
from uuid import uuid4


class InMemoryRunStore:
    def __init__(self) -> None:
        self._runs: dict[UUID, dict[str, Any]] = {}

    def create_run(self, row: dict[str, Any]) -> dict[str, Any]:
        run_id = uuid4()
        created_at = datetime.now(timezone.utc)
        stored = {
            "id": run_id,
            **row,
            "created_at": created_at,
            "started_at": None,
            "finished_at": None,
        }
        self._runs[run_id] = stored
        return stored

    def get_run(self, run_id: UUID) -> dict[str, Any] | None:
        return self._runs.get(run_id)


RUN_STORE = InMemoryRunStore()
