from __future__ import annotations

import json
import sqlite3

import pytest

from scripts.local_backup_common import sha256_file
from scripts.create_local_sqlite_db import create_local_sqlite_db


def write_jsonl(path, rows):
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def fetch_rows(db_path, table_name):
    with sqlite3.connect(db_path) as conn:
        return conn.execute(
            """
            SELECT row_id, data_json, created_at, updated_at
            FROM local_rows
            WHERE table_name = ?
            ORDER BY row_id
            """,
            (table_name,),
        ).fetchall()


def fetch_metadata(db_path):
    with sqlite3.connect(db_path) as conn:
        return {
            key: json.loads(value_json)
            for key, value_json in conn.execute(
                "SELECT key, value_json FROM local_metadata ORDER BY key"
            )
        }


def test_manifest_failures_require_explicit_allow_partial(tmp_path):
    backup_dir = tmp_path / "backup"
    tables_dir = backup_dir / "tables"
    tables_dir.mkdir(parents=True)
    write_jsonl(tables_dir / "one.jsonl", [{"id": "a"}])
    (backup_dir / "manifest.json").write_text(
        json.dumps(
            {
                "tables": {
                    "one": {"status": "exported"},
                    "missing_table": {"status": "failed", "error": "404"},
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="failed table exports"):
        create_local_sqlite_db(tables_dir, tmp_path / "local.sqlite3", replace=False)

    counts = create_local_sqlite_db(
        tables_dir,
        tmp_path / "local.sqlite3",
        replace=False,
        allow_partial=True,
    )
    assert counts == {"one": 1}


def test_manifest_row_count_size_and_checksum_mismatches_fail(tmp_path):
    backup_dir = tmp_path / "backup"
    tables_dir = backup_dir / "tables"
    tables_dir.mkdir(parents=True)
    table_path = tables_dir / "one.jsonl"
    write_jsonl(table_path, [{"id": "a"}, {"id": "b"}])
    actual_size = table_path.stat().st_size
    actual_sha = sha256_file(table_path)

    for field, value, message in [
        ("row_count", 1, "row_count mismatch"),
        ("size_bytes", actual_size + 1, "size_bytes mismatch"),
        ("sha256", "0" * 64, "sha256 mismatch"),
    ]:
        (backup_dir / "manifest.json").write_text(
            json.dumps({"tables": {"one": {"status": "exported", "row_count": 2, "size_bytes": actual_size, "sha256": actual_sha} | {field: value}}}),
            encoding="utf-8",
        )

        with pytest.raises(RuntimeError, match=message):
            create_local_sqlite_db(tables_dir, tmp_path / f"{field}.sqlite3", replace=False)


def test_allow_partial_does_not_allow_manifest_integrity_mismatch(tmp_path):
    backup_dir = tmp_path / "backup"
    tables_dir = backup_dir / "tables"
    tables_dir.mkdir(parents=True)
    table_path = tables_dir / "one.jsonl"
    write_jsonl(table_path, [{"id": "a"}, {"id": "b"}])
    (backup_dir / "manifest.json").write_text(
        json.dumps(
            {
                "tables": {
                    "one": {
                        "status": "exported",
                        "row_count": 2,
                        "size_bytes": table_path.stat().st_size,
                        "sha256": "0" * 64,
                    },
                    "missing_table": {"status": "failed", "error": "404"},
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="sha256 mismatch"):
        create_local_sqlite_db(
            tables_dir,
            tmp_path / "local.sqlite3",
            replace=False,
            allow_partial=True,
        )


def test_imports_all_jsonl_files_with_counts_and_json_preservation(tmp_path):
    tables_dir = tmp_path / "tables"
    tables_dir.mkdir()
    write_jsonl(
        tables_dir / "tracker_entries.jsonl",
        [
            {
                "id": "entry-1",
                "name": "Alpha",
                "nested": {"keep": ["all", "json"]},
                "created_at": "2026-05-30T10:00:00Z",
                "updated_at": "2026-05-31T10:00:00Z",
            },
            {"id": 42, "name": "Numeric id"},
        ],
    )
    write_jsonl(tables_dir / "sales_claims.jsonl", [{"id": "claim-1", "amount": 123}])
    output = tmp_path / "local.sqlite3"

    result = create_local_sqlite_db(tables_dir, output, replace=False)

    assert result == {"sales_claims": 1, "tracker_entries": 2}
    tracker_rows = fetch_rows(output, "tracker_entries")
    assert tracker_rows[0][0] == "42"
    assert json.loads(tracker_rows[0][1]) == {"id": 42, "name": "Numeric id"}
    assert tracker_rows[1][0] == "entry-1"
    assert json.loads(tracker_rows[1][1])["nested"] == {"keep": ["all", "json"]}
    assert tracker_rows[1][2] == "2026-05-30T10:00:00Z"
    assert tracker_rows[1][3] == "2026-05-31T10:00:00Z"


def test_rows_without_id_use_stable_sequential_ids(tmp_path):
    tables_dir = tmp_path / "tables"
    tables_dir.mkdir()
    write_jsonl(
        tables_dir / "anonymous_rows.jsonl",
        [
            {"value": "first"},
            {"id": "", "value": "blank id"},
            {"value": "third"},
        ],
    )
    first_output = tmp_path / "first.sqlite3"
    second_output = tmp_path / "second.sqlite3"

    create_local_sqlite_db(tables_dir, first_output, replace=False)
    create_local_sqlite_db(tables_dir, second_output, replace=False)

    assert [row[0] for row in fetch_rows(first_output, "anonymous_rows")] == [
        "__row_000000000001",
        "__row_000000000002",
        "__row_000000000003",
    ]
    assert fetch_rows(first_output, "anonymous_rows") == fetch_rows(
        second_output, "anonymous_rows"
    )


def test_metadata_records_source_counts_and_created_timestamp(tmp_path):
    tables_dir = tmp_path / "tables"
    tables_dir.mkdir()
    write_jsonl(tables_dir / "one.jsonl", [{"id": "a"}, {"id": "b"}])
    write_jsonl(tables_dir / "empty.jsonl", [])
    output = tmp_path / "local.sqlite3"

    create_local_sqlite_db(tables_dir, output, replace=False)

    metadata = fetch_metadata(output)
    assert metadata["source_path"] == str(tables_dir.resolve())
    assert metadata["kind"] == "supabase_jsonl_staging"
    assert metadata["table_row_counts"] == {"empty": 0, "one": 2}
    assert isinstance(metadata["created_at"], str)
    assert metadata["created_at"].endswith("Z")


def test_existing_output_requires_replace(tmp_path):
    tables_dir = tmp_path / "tables"
    tables_dir.mkdir()
    write_jsonl(tables_dir / "one.jsonl", [{"id": "a"}])
    output = tmp_path / "local.sqlite3"
    output.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError):
        create_local_sqlite_db(tables_dir, output, replace=False)

    assert output.read_text(encoding="utf-8") == "existing"

    create_local_sqlite_db(tables_dir, output, replace=True)

    assert fetch_rows(output, "one")[0][0] == "a"


def test_replace_preserves_existing_database_when_import_fails(tmp_path):
    tables_dir = tmp_path / "tables"
    tables_dir.mkdir()
    (tables_dir / "broken.jsonl").write_text('{"id":"a"}\nnot json\n', encoding="utf-8")
    output = tmp_path / "local.sqlite3"
    output.write_text("existing", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        create_local_sqlite_db(tables_dir, output, replace=True)

    assert output.read_text(encoding="utf-8") == "existing"
