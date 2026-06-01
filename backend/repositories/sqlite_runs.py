from __future__ import annotations

from datetime import date
from uuid import UUID
from uuid import uuid4

from backend.phase1_defaults import load_phase1_identity

from .runs import RunRepository
from .runs import RunRepositoryConfigError
from .runs import RunRepositoryError
from .runs import RunRow
from .sqlite_common import LocalRowsStore
from .sqlite_common import SqliteRepositoryConfig
from .sqlite_common import row_sort_text
from .sqlite_common import utc_now_text

TABLE_NAME = "pipeline_runs"


class SqliteRunRepository(RunRepository):
    def __init__(self, config: SqliteRepositoryConfig | None = None) -> None:
        self._store = LocalRowsStore(config or SqliteRepositoryConfig.from_env(error_cls=RunRepositoryConfigError))
        self._organization_id = str(load_phase1_identity().organization_id)

    def create_run(self, row: RunRow) -> RunRow:
        now = utc_now_text()
        run_id = str(row.get("id") or uuid4())
        stored: RunRow = {
            "id": run_id,
            **row,
            "created_at": row.get("created_at") or now,
            "updated_at": row.get("updated_at") or now,
            "started_at": row.get("started_at"),
            "finished_at": row.get("finished_at"),
        }
        stored["id"] = run_id
        return self._store.upsert_row(
            TABLE_NAME,
            run_id,
            stored,
            created_at=stored.get("created_at"),
            updated_at=stored.get("updated_at"),
        )

    def get_run(self, run_id: UUID) -> RunRow | None:
        row = self._store.get_row(TABLE_NAME, str(run_id))
        if row is None or not self._is_local_organization(row):
            return None
        return row

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
        rows: list[RunRow] = []
        parent_text = str(parent_run_id) if parent_run_id is not None else None
        for row in self._store.list_rows(TABLE_NAME):
            if not self._is_local_organization(row):
                continue
            if status and row.get("status") != status:
                continue
            if run_type and row.get("run_type") != run_type:
                continue
            if parent_text is not None and str(row.get("parent_run_id")) != parent_text:
                continue
            created_day = _created_day(row.get("created_at"))
            if date_from and created_day < _normalize_date(date_from):
                continue
            if date_to and created_day > _normalize_date(date_to):
                continue
            rows.append(dict(row))
        rows.sort(key=lambda item: (row_sort_text(item.get("created_at")), str(item.get("id") or "")), reverse=True)
        total = len(rows)
        start = max(page - 1, 0) * page_size
        return rows[start : start + page_size], total

    def update_run(self, run_id: UUID, fields: dict[str, object]) -> RunRow | None:
        row = self.get_run(run_id)
        if row is None:
            return None
        row.update(fields)
        row["updated_at"] = utc_now_text()
        return self._store.upsert_row(
            TABLE_NAME,
            str(run_id),
            row,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def delete_run(self, run_id: UUID) -> bool:
        if self.get_run(run_id) is None:
            return False
        return self._store.delete_row(TABLE_NAME, str(run_id))

    def _is_local_organization(self, row: dict[str, object]) -> bool:
        return str(row.get("organization_id")) == self._organization_id


def _normalize_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise RunRepositoryError("date filters must be YYYY-MM-DD") from exc


def _created_day(value: object) -> str:
    text = row_sort_text(value)
    if len(text) >= 10:
        return text[:10]
    return ""
