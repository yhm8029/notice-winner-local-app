from __future__ import annotations

from uuid import UUID

from backend.phase1_defaults import load_phase1_identity

from .logs import RunLogRepository
from .logs import RunLogRepositoryConfigError
from .logs import RunLogRow
from .sqlite_common import LocalRowsStore
from .sqlite_common import SqliteRepositoryConfig
from .sqlite_common import utc_now_text

TABLE_NAME = "pipeline_logs"


class SqliteRunLogRepository(RunLogRepository):
    def __init__(self, config: SqliteRepositoryConfig | None = None) -> None:
        self._store = LocalRowsStore(config or SqliteRepositoryConfig.from_env(error_cls=RunLogRepositoryConfigError))
        self._organization_id = str(load_phase1_identity().organization_id)

    def create_log(self, row: RunLogRow) -> RunLogRow:
        if row.get("id") is not None:
            stored: RunLogRow = {
                **row,
                "id": int(row["id"]),
                "run_id": str(row.get("run_id")),
                "created_at": row.get("created_at") or utc_now_text(),
                "meta_json": dict(row.get("meta_json") or {}),
            }
            return self._normalize_row(
                self._store.upsert_row(
                    TABLE_NAME,
                    str(stored["id"]),
                    stored,
                    created_at=stored.get("created_at"),
                )
            )
        stored_without_id: RunLogRow = {
            **row,
            "run_id": str(row.get("run_id")),
            "created_at": row.get("created_at") or utc_now_text(),
            "meta_json": dict(row.get("meta_json") or {}),
        }
        return self._normalize_row(
            self._store.insert_with_next_integer_id(
                TABLE_NAME,
                stored_without_id,
                created_at=stored_without_id.get("created_at"),
            )
        )

    def list_logs(
        self,
        *,
        run_id: UUID,
        cursor: int | None,
        limit: int,
    ) -> tuple[list[RunLogRow], int | None]:
        items = [
            self._normalize_row(row)
            for row in self._store.list_rows(TABLE_NAME)
            if str(row.get("run_id")) == str(run_id)
            and self._is_local_organization(row)
        ]
        if cursor is not None:
            items = [item for item in items if int(item["id"]) < cursor]
        items.sort(key=lambda item: int(item["id"]), reverse=True)
        page_items = items[:limit]
        next_cursor = int(page_items[-1]["id"]) if len(items) > limit and page_items else None
        return [dict(item) for item in page_items], next_cursor

    def delete_logs_for_run(self, run_id: UUID) -> int:
        return self._store.delete_matching(
            TABLE_NAME,
            lambda row: str(row.get("run_id")) == str(run_id) and self._is_local_organization(row),
        )

    def _normalize_row(self, row: dict[str, object]) -> RunLogRow:
        normalized = dict(row)
        normalized["id"] = int(normalized["id"])
        normalized["meta_json"] = dict(normalized.get("meta_json") or {})
        return normalized

    def _is_local_organization(self, row: dict[str, object]) -> bool:
        return str(row.get("organization_id")) == self._organization_id
