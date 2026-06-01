from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from uuid import UUID
from uuid import uuid4

from backend.phase1_defaults import DEFAULT_PHASE1_ORGANIZATION_ID
from backend.repositories.factory import describe_repository_backends
from backend.repositories.factory import get_artifact_repository
from backend.repositories.factory import get_download_audit_log_repository
from backend.repositories.factory import get_login_audit_log_repository
from backend.repositories.factory import get_run_log_repository
from backend.repositories.factory import get_run_repository
from backend.repositories.factory import get_tracker_entry_repository
from backend.repositories.factory import reset_artifact_repository
from backend.repositories.factory import reset_download_audit_log_repository
from backend.repositories.factory import reset_login_audit_log_repository
from backend.repositories.factory import reset_run_log_repository
from backend.repositories.factory import reset_run_repository
from backend.repositories.factory import reset_tracker_entry_repository


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
"""


class SqliteRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "local.sqlite3"
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(SCHEMA_SQL)
        finally:
            conn.close()

    def tearDown(self) -> None:
        reset_run_repository()
        reset_run_log_repository()
        reset_artifact_repository()
        reset_download_audit_log_repository()
        reset_login_audit_log_repository()
        reset_tracker_entry_repository()
        self._tmp.cleanup()

    def _env(self) -> dict[str, str]:
        return {
            "LOCAL_SQLITE_PATH": str(self.db_path),
            "TRACKER_REPOSITORY_BACKEND": "in_memory",
            "RUN_REPOSITORY_BACKEND": "sqlite",
            "ARTIFACT_REPOSITORY_BACKEND": "sqlite",
            "RUN_LOG_REPOSITORY_BACKEND": "sqlite",
            "DOWNLOAD_AUDIT_LOG_REPOSITORY_BACKEND": "sqlite",
            "LOGIN_AUDIT_LOG_REPOSITORY_BACKEND": "sqlite",
            "RELATED_NOTICE_CACHE_REPOSITORY_BACKEND": "",
            "RELATED_NOTICE_PUBLICATION_REPOSITORY_BACKEND": "",
            "SALES_CLAIM_REPOSITORY_BACKEND": "",
            "TRACKER_CHANGE_EVENT_REPOSITORY_BACKEND": "",
            "TRACKER_ENTRY_SNAPSHOT_REPOSITORY_BACKEND": "",
            "HOME_BOOTSTRAP_SNAPSHOT_REPOSITORY_BACKEND": "",
            "BACKFILL_CONFLICT_REPOSITORY_BACKEND": "",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SECRET_KEY": "sb_secret_example",
        }

    def test_factory_selects_sqlite_backend_without_supabase_connections(self) -> None:
        with patch.dict(os.environ, self._env(), clear=False):
            summary = describe_repository_backends()

        self.assertEqual(summary["runs"], "sqlite")
        self.assertEqual(summary["artifacts"], "sqlite")
        self.assertEqual(summary["logs"], "sqlite")
        self.assertEqual(summary["download_audit_logs"], "sqlite")
        self.assertEqual(summary["login_audit_logs"], "sqlite")
        self.assertEqual(summary["artifact_metadata_persistent"], True)
        self.assertEqual(summary["related_notice_cache"], "in_memory")
        self.assertEqual(summary["sales_claims"], "in_memory")

    def test_sqlite_tracker_repository_getter_is_supported(self) -> None:
        env = self._env()
        env["TRACKER_REPOSITORY_BACKEND"] = "sqlite"
        env["RUN_REPOSITORY_BACKEND"] = "in_memory"
        with patch.dict(os.environ, env, clear=False):
            reset_tracker_entry_repository()
            repository = get_tracker_entry_repository()

        self.assertIsNotNone(repository)

    def test_sqlite_run_repository_persists_and_filters_runs(self) -> None:
        with patch.dict(os.environ, self._env(), clear=False):
            reset_run_repository()
            repository = get_run_repository()
            first = repository.create_run(
                {
                    "organization_id": str(DEFAULT_PHASE1_ORGANIZATION_ID),
                    "requested_by": "user-1",
                    "parent_run_id": None,
                    "status": "running",
                    "run_type": "winner_search",
                    "source_mode": "real",
                    "params_json": {"month": "202605"},
                    "summary_json": {},
                    "error_json": None,
                    "progress_stage": "collect",
                    "progress_current": 1,
                    "progress_total": 3,
                    "cancel_requested": False,
                }
            )
            second = repository.create_run(
                {
                    "organization_id": str(DEFAULT_PHASE1_ORGANIZATION_ID),
                    "requested_by": "user-1",
                    "parent_run_id": str(first["id"]),
                    "status": "completed",
                    "run_type": "tracker_export",
                    "source_mode": "real",
                    "params_json": {},
                    "summary_json": {"ok": True},
                    "error_json": None,
                    "progress_stage": "done",
                    "progress_current": 1,
                    "progress_total": 1,
                    "cancel_requested": False,
                }
            )

            reloaded = get_run_repository()
            updated = reloaded.update_run(UUID(str(first["id"])), {"status": "completed"})
            rows, total = reloaded.list_runs(
                page=1,
                page_size=10,
                status="completed",
                run_type="",
                parent_run_id=None,
                date_from="",
                date_to="",
            )

        self.assertEqual(updated["status"], "completed")
        self.assertEqual(total, 2)
        self.assertEqual({str(row["id"]) for row in rows}, {str(first["id"]), str(second["id"])})
        self.assertEqual(str(reloaded.get_run(UUID(str(first["id"])))["id"]), str(first["id"]))

    def test_sqlite_run_repository_scopes_reads_and_mutations_to_local_organization(self) -> None:
        other_org_run_id = uuid4()
        with patch.dict(os.environ, self._env(), clear=False):
            reset_run_repository()
            repository = get_run_repository()
            repository.create_run(
                {
                    "id": str(other_org_run_id),
                    "organization_id": str(uuid4()),
                    "requested_by": "user-1",
                    "parent_run_id": None,
                    "status": "completed",
                    "run_type": "winner_search",
                    "source_mode": "real",
                    "params_json": {},
                    "summary_json": {},
                    "error_json": None,
                    "progress_stage": "done",
                    "progress_current": 1,
                    "progress_total": 1,
                    "cancel_requested": False,
                }
            )

            self.assertIsNone(repository.get_run(other_org_run_id))
            self.assertIsNone(repository.update_run(other_org_run_id, {"status": "failed"}))
            self.assertFalse(repository.delete_run(other_org_run_id))
            rows, total = repository.list_runs(
                page=1,
                page_size=10,
                status="",
                run_type="",
                parent_run_id=None,
                date_from="",
                date_to="",
            )

        self.assertEqual(rows, [])
        self.assertEqual(total, 0)

    def test_sqlite_artifact_repository_scopes_reads_and_deletes_to_local_organization(self) -> None:
        run_id = uuid4()
        artifact_id = uuid4()
        with patch.dict(os.environ, self._env(), clear=False):
            reset_artifact_repository()
            repository = get_artifact_repository()
            repository.create_artifact(
                {
                    "id": str(artifact_id),
                    "run_id": str(run_id),
                    "organization_id": str(uuid4()),
                    "artifact_type": "xlsx",
                    "storage_path": "output/artifacts/other.xlsx",
                    "file_name": "other.xlsx",
                    "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "size_bytes": 12,
                    "checksum": "abc",
                    "meta_json": {},
                }
            )

            self.assertEqual(repository.list_artifacts(run_id=run_id), [])
            self.assertIsNone(repository.get_artifact(artifact_id))
            self.assertEqual(repository.delete_artifacts_for_run(run_id), 0)

    def test_sqlite_log_repository_uses_numeric_cursor_and_deletes_by_run(self) -> None:
        run_id = uuid4()
        with patch.dict(os.environ, self._env(), clear=False):
            reset_run_log_repository()
            repository = get_run_log_repository()
            first = repository.create_log(
                {
                    "run_id": str(run_id),
                    "organization_id": str(DEFAULT_PHASE1_ORGANIZATION_ID),
                    "level": "info",
                    "stage": "collect",
                    "message": "first",
                    "meta_json": {},
                }
            )
            second = repository.create_log(
                {
                    "run_id": str(run_id),
                    "organization_id": str(DEFAULT_PHASE1_ORGANIZATION_ID),
                    "level": "info",
                    "stage": "collect",
                    "message": "second",
                    "meta_json": {},
                }
            )
            rows, cursor = repository.list_logs(run_id=run_id, cursor=None, limit=1)
            next_rows, next_cursor = repository.list_logs(run_id=run_id, cursor=cursor, limit=10)
            deleted = repository.delete_logs_for_run(run_id)

        self.assertEqual(first["id"], 1)
        self.assertEqual(second["id"], 2)
        self.assertEqual([row["message"] for row in rows], ["second"])
        self.assertEqual(cursor, 2)
        self.assertEqual([row["message"] for row in next_rows], ["first"])
        self.assertIsNone(next_cursor)
        self.assertEqual(deleted, 2)

    def test_sqlite_log_repository_allocates_unique_ids_for_concurrent_writes(self) -> None:
        run_id = uuid4()
        with patch.dict(os.environ, self._env(), clear=False):
            reset_run_log_repository()
            repository = get_run_log_repository()

            def create_one(index: int) -> int:
                row = repository.create_log(
                    {
                        "run_id": str(run_id),
                        "organization_id": str(DEFAULT_PHASE1_ORGANIZATION_ID),
                        "level": "info",
                        "stage": "collect",
                        "message": f"log-{index}",
                        "meta_json": {},
                    }
                )
                return int(row["id"])

            with ThreadPoolExecutor(max_workers=8) as executor:
                ids = list(executor.map(create_one, range(40)))
            rows, _cursor = repository.list_logs(run_id=run_id, cursor=None, limit=100)

        self.assertEqual(len(set(ids)), 40)
        self.assertEqual(len(rows), 40)

    def test_sqlite_artifact_repository_persists_artifacts_by_run(self) -> None:
        run_id = uuid4()
        other_run_id = uuid4()
        with patch.dict(os.environ, self._env(), clear=False):
            reset_artifact_repository()
            repository = get_artifact_repository()
            created = repository.create_artifact(
                {
                    "run_id": str(run_id),
                    "organization_id": str(DEFAULT_PHASE1_ORGANIZATION_ID),
                    "artifact_type": "xlsx",
                    "storage_path": "output/artifacts/report.xlsx",
                    "file_name": "report.xlsx",
                    "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "size_bytes": 12,
                    "checksum": "abc",
                    "meta_json": {"scope": "global"},
                }
            )
            repository.create_artifact(
                {
                    "run_id": str(other_run_id),
                    "organization_id": str(DEFAULT_PHASE1_ORGANIZATION_ID),
                    "artifact_type": "csv",
                    "storage_path": "output/artifacts/other.csv",
                    "file_name": "other.csv",
                    "mime_type": "text/csv",
                    "size_bytes": 3,
                    "checksum": "def",
                    "meta_json": {},
                }
            )
            rows = repository.list_artifacts(run_id=run_id)
            loaded = repository.get_artifact(UUID(str(created["id"])))
            deleted = repository.delete_artifacts_for_run(run_id)

        self.assertEqual([row["file_name"] for row in rows], ["report.xlsx"])
        self.assertEqual(loaded["meta_json"], {"scope": "global"})
        self.assertEqual(deleted, 1)

    def test_sqlite_audit_repositories_list_newest_by_organization(self) -> None:
        org_id = uuid4()
        other_org_id = uuid4()
        user_id = uuid4()
        with patch.dict(os.environ, self._env(), clear=False):
            reset_download_audit_log_repository()
            reset_login_audit_log_repository()
            download_repository = get_download_audit_log_repository()
            login_repository = get_login_audit_log_repository()

            download_repository.create_log(
                organization_id=org_id,
                user_id=user_id,
                user_email="one@example.com",
                user_role="user",
                download_scope="global",
                download_format="xlsx",
                source_page="tracker_entries",
                file_name="one.xlsx",
            )
            download_repository.create_log(
                organization_id=other_org_id,
                user_id=user_id,
                user_email="other@example.com",
                user_role="user",
                download_scope="global",
                download_format="xlsx",
                source_page="tracker_entries",
                file_name="other.xlsx",
            )
            download_repository.create_log(
                organization_id=org_id,
                user_id=None,
                user_email="two@example.com",
                user_role="admin",
                download_scope="company",
                download_format="csv",
                source_page="company_active_sales",
                file_name="two.csv",
            )
            login_repository.create_log(
                organization_id=org_id,
                user_id=user_id,
                user_email="login@example.com",
                user_role="platform_admin",
                ip_address="127.0.0.1",
                user_agent="test",
            )

            download_rows = download_repository.list_logs(organization_id=org_id, limit=5)
            login_rows = login_repository.list_logs(organization_id=org_id, limit=5)

        self.assertEqual([row["file_name"] for row in download_rows], ["two.csv", "one.xlsx"])
        self.assertEqual(login_rows[0]["user_email"], "login@example.com")
