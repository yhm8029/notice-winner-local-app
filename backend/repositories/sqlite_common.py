from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from uuid import UUID


LOCAL_ROWS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS local_rows (
    table_name TEXT NOT NULL,
    row_id TEXT NOT NULL,
    data_json TEXT NOT NULL,
    created_at TEXT,
    updated_at TEXT,
    PRIMARY KEY(table_name, row_id)
);

CREATE INDEX IF NOT EXISTS idx_local_rows_table_name ON local_rows(table_name);
CREATE INDEX IF NOT EXISTS idx_local_rows_table_created_at ON local_rows(table_name, created_at);
CREATE INDEX IF NOT EXISTS idx_local_rows_table_updated_at ON local_rows(table_name, updated_at);

CREATE TABLE IF NOT EXISTS local_metadata (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class SqliteRepositoryConfig:
    database_path: Path

    @classmethod
    def from_env(cls, *, error_cls: type[Exception]) -> "SqliteRepositoryConfig":
        raw_path = (
            os.getenv("LOCAL_SQLITE_PATH", "").strip()
            or os.getenv("SQLITE_PATH", "").strip()
            or os.getenv("LOCAL_APP_SQLITE_PATH", "").strip()
        )
        if not raw_path:
            raw_path = "data/local.sqlite3"
        database_path = Path(raw_path)
        if database_path.exists() and database_path.is_dir():
            raise error_cls("LOCAL_SQLITE_PATH must point to a SQLite database file, not a directory")
        return cls(database_path=database_path)


def utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=_json_default)


def _json_default(value: Any) -> str:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def row_sort_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


class LocalRowsStore:
    def __init__(self, config: SqliteRepositoryConfig) -> None:
        self._database_path = config.database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as conn:
            conn.executescript(LOCAL_ROWS_SCHEMA_SQL)

    def get_row(self, table_name: str, row_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT data_json FROM local_rows WHERE table_name = ? AND row_id = ?",
                (table_name, row_id),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return _loads_row(row["data_json"])

    def list_rows(self, table_name: str) -> list[dict[str, Any]]:
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT data_json FROM local_rows WHERE table_name = ?",
                (table_name,),
            )
            rows = cursor.fetchall()
        return [_loads_row(row["data_json"]) for row in rows]

    def upsert_row(
        self,
        table_name: str,
        row_id: str,
        row: dict[str, Any],
        *,
        created_at: Any | None = None,
        updated_at: Any | None = None,
    ) -> dict[str, Any]:
        stored = dict(row)
        created_text = row_sort_text(created_at if created_at is not None else stored.get("created_at"))
        updated_text = row_sort_text(updated_at if updated_at is not None else stored.get("updated_at"))
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO local_rows(table_name, row_id, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(table_name, row_id) DO UPDATE SET
                    data_json = excluded.data_json,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at
                """,
                (table_name, row_id, json_dumps(stored), created_text or None, updated_text or None),
            )
        return dict(stored)

    def delete_row(self, table_name: str, row_id: str) -> bool:
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM local_rows WHERE table_name = ? AND row_id = ?",
                (table_name, row_id),
            )
            return cursor.rowcount > 0

    def delete_matching(self, table_name: str, predicate) -> int:
        matching_ids = [str(row.get("id")) for row in self.list_rows(table_name) if predicate(row)]
        if not matching_ids:
            return 0
        with self._connection() as conn:
            conn.executemany(
                "DELETE FROM local_rows WHERE table_name = ? AND row_id = ?",
                ((table_name, row_id) for row_id in matching_ids),
            )
        return len(matching_ids)

    def insert_with_next_integer_id(
        self,
        table_name: str,
        row_without_id: dict[str, Any],
        *,
        created_at: Any | None = None,
        updated_at: Any | None = None,
    ) -> dict[str, Any]:
        with self._connection(immediate=True) as conn:
            cursor = conn.execute(
                "SELECT data_json FROM local_rows WHERE table_name = ?",
                (table_name,),
            )
            max_id = 0
            for stored_row in cursor.fetchall():
                try:
                    max_id = max(max_id, int(_loads_row(stored_row["data_json"]).get("id")))
                except (TypeError, ValueError):
                    continue
            row_id = max_id + 1
            stored = {"id": row_id, **row_without_id}
            conn.execute(
                """
                INSERT INTO local_rows(table_name, row_id, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    table_name,
                    str(row_id),
                    json_dumps(stored),
                    row_sort_text(created_at if created_at is not None else stored.get("created_at")) or None,
                    row_sort_text(updated_at if updated_at is not None else stored.get("updated_at")) or None,
                ),
            )
            return dict(stored)

    @contextmanager
    def _connection(self, *, immediate: bool = False):
        conn = self._connect()
        try:
            if immediate:
                conn.execute("BEGIN IMMEDIATE")
                try:
                    yield conn
                except Exception:
                    conn.rollback()
                    raise
                else:
                    conn.commit()
            else:
                with conn:
                    yield conn
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._database_path, timeout=60.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn


def _loads_row(data_json: str) -> dict[str, Any]:
    row = json.loads(data_json)
    if not isinstance(row, dict):
        raise ValueError("local_rows.data_json must contain a JSON object")
    return row
