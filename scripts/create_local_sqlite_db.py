from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.local_backup_common import sha256_file


SCHEMA_SQL = """
CREATE TABLE local_rows (
    table_name TEXT NOT NULL,
    row_id TEXT NOT NULL,
    data_json TEXT NOT NULL,
    created_at TEXT,
    updated_at TEXT,
    PRIMARY KEY(table_name, row_id)
);

CREATE INDEX idx_local_rows_table_name ON local_rows(table_name);
CREATE INDEX idx_local_rows_table_created_at ON local_rows(table_name, created_at);
CREATE INDEX idx_local_rows_table_updated_at ON local_rows(table_name, updated_at);

CREATE TABLE local_metadata (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL
);
"""


def _json_dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _row_id_for(row, fallback_index):
    row_id = row.get("id")
    if row_id is None or row_id == "":
        return f"__row_{fallback_index:012d}"
    return str(row_id)


def _optional_text(value):
    if value is None:
        return None
    return str(value)


def _iter_jsonl_rows(path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object")
            yield row


def _validate_export_manifest(tables_path, *, allow_partial):
    manifest_path = tables_path.parent / "manifest.json"
    if not manifest_path.exists():
        return {"manifest_path": None, "failed_tables": [], "missing_exported_tables": []}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tables = manifest.get("tables") or {}
    failed_tables = sorted(
        str(table_name)
        for table_name, item in tables.items()
        if isinstance(item, dict) and item.get("status") != "exported"
    )
    missing_exported_tables = sorted(
        str(table_name)
        for table_name, item in tables.items()
        if isinstance(item, dict)
        and item.get("status") == "exported"
        and not (tables_path / f"{table_name}.jsonl").exists()
    )
    integrity_errors = []
    for table_name, item in sorted(tables.items()):
        if not isinstance(item, dict) or item.get("status") != "exported":
            continue
        table_path = tables_path / f"{table_name}.jsonl"
        if not table_path.exists():
            continue
        expected_row_count = item.get("row_count")
        expected_size_bytes = item.get("size_bytes")
        expected_sha256 = str(item.get("sha256") or "").strip()
        actual_row_count = sum(1 for _row in _iter_jsonl_rows(table_path))
        actual_size_bytes = table_path.stat().st_size
        actual_sha256 = sha256_file(table_path)
        if expected_row_count is not None and int(expected_row_count) != actual_row_count:
            integrity_errors.append(
                f"{table_name} row_count mismatch: manifest={expected_row_count} actual={actual_row_count}"
            )
        if expected_size_bytes is not None and int(expected_size_bytes) != actual_size_bytes:
            integrity_errors.append(
                f"{table_name} size_bytes mismatch: manifest={expected_size_bytes} actual={actual_size_bytes}"
            )
        if expected_sha256 and expected_sha256 != actual_sha256:
            integrity_errors.append(f"{table_name} sha256 mismatch")
    if integrity_errors or ((failed_tables or missing_exported_tables) and not allow_partial):
        details = []
        if failed_tables:
            details.append("failed table exports: " + ", ".join(failed_tables))
        if missing_exported_tables:
            details.append("missing exported table files: " + ", ".join(missing_exported_tables))
        details.extend(integrity_errors)
        raise RuntimeError("; ".join(details))
    return {
        "manifest_path": str(manifest_path.resolve()),
        "failed_tables": failed_tables,
        "missing_exported_tables": missing_exported_tables,
        "integrity_errors": integrity_errors,
    }


def _create_database_at(output_path, tables_path, *, allow_partial):
    manifest_status = _validate_export_manifest(tables_path, allow_partial=allow_partial)
    table_counts = {}
    conn = sqlite3.connect(output_path)
    try:
        conn.executescript(SCHEMA_SQL)
        for jsonl_path in sorted(tables_path.glob("*.jsonl")):
            table_name = jsonl_path.stem
            row_count = 0
            for row_count, row in enumerate(_iter_jsonl_rows(jsonl_path), start=1):
                conn.execute(
                    """
                    INSERT INTO local_rows(table_name, row_id, data_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        table_name,
                        _row_id_for(row, row_count),
                        _json_dumps(row),
                        _optional_text(row.get("created_at")),
                        _optional_text(row.get("updated_at")),
                    ),
                )
            table_counts[table_name] = row_count

        metadata = {
            "kind": "supabase_jsonl_staging",
            "source_path": str(tables_path.resolve()),
            "table_row_counts": table_counts,
            "allow_partial": bool(allow_partial),
            "manifest": manifest_status,
            "created_at": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
        }
        conn.executemany(
            "INSERT INTO local_metadata(key, value_json) VALUES (?, ?)",
            ((key, _json_dumps(value)) for key, value in metadata.items()),
        )
        conn.commit()
    finally:
        conn.close()
    return table_counts


def create_local_sqlite_db(tables_dir, output, replace=False, allow_partial=False):
    tables_path = Path(tables_dir)
    output_path = Path(output)

    if not tables_path.is_dir():
        raise NotADirectoryError(tables_path)
    if output_path.exists():
        if not replace:
            raise FileExistsError(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = output_path.with_name(f".{output_path.name}.tmp")
    if temp_path.exists():
        temp_path.unlink()
    try:
        table_counts = _create_database_at(temp_path, tables_path, allow_partial=allow_partial)
        os.replace(temp_path, output_path)
        return table_counts
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Create a local SQLite database from Supabase table JSONL exports."
    )
    parser.add_argument(
        "--tables-dir",
        required=True,
        help="Directory containing *.jsonl table exports",
    )
    parser.add_argument("--output", required=True, help="SQLite database path to create")
    parser.add_argument("--replace", action="store_true", help="Replace output if it already exists")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Allow import when the Supabase backup manifest has failed or missing table exports",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    table_counts = create_local_sqlite_db(
        args.tables_dir,
        args.output,
        replace=args.replace,
        allow_partial=args.allow_partial,
    )
    print(_json_dumps({"output": str(Path(args.output)), "table_row_counts": table_counts}))


if __name__ == "__main__":
    main()
