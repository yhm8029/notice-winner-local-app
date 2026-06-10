from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from backend.phase1_defaults import DEFAULT_PHASE1_ORGANIZATION_ID
from backend.repositories import factory
from backend.repositories.sqlite_common import LocalRowsStore
from backend.repositories.sqlite_common import SqliteRepositoryConfig


SQLITE_BACKEND_ENV = {
    "TRACKER_REPOSITORY_BACKEND": "sqlite",
    "RUN_REPOSITORY_BACKEND": "sqlite",
    "ARTIFACT_REPOSITORY_BACKEND": "sqlite",
    "RUN_LOG_REPOSITORY_BACKEND": "sqlite",
    "RELATED_NOTICE_CACHE_REPOSITORY_BACKEND": "sqlite",
    "RELATED_NOTICE_PUBLICATION_REPOSITORY_BACKEND": "sqlite",
    "SALES_CLAIM_REPOSITORY_BACKEND": "sqlite",
    "TRACKER_CHANGE_EVENT_REPOSITORY_BACKEND": "sqlite",
    "DOWNLOAD_AUDIT_LOG_REPOSITORY_BACKEND": "sqlite",
    "LOGIN_AUDIT_LOG_REPOSITORY_BACKEND": "sqlite",
    "TRACKER_ENTRY_SNAPSHOT_REPOSITORY_BACKEND": "sqlite",
    "HOME_BOOTSTRAP_SNAPSHOT_REPOSITORY_BACKEND": "sqlite",
    "BACKFILL_CONFLICT_REPOSITORY_BACKEND": "sqlite",
    "SUPABASE_URL": "",
    "SUPABASE_SECRET_KEY": "",
    "SUPABASE_SECRET": "",
    "SUPABASE_SERVICE_ROLE_KEY": "",
    "SUPABASE_ANON_KEY": "",
}


class SqliteLocalDataRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "local.sqlite3"
        self.store = LocalRowsStore(SqliteRepositoryConfig(database_path=self.db_path))
        self.env = {**SQLITE_BACKEND_ENV, "LOCAL_SQLITE_PATH": str(self.db_path)}
        factory.reset_tracker_entry_repository()
        factory.reset_related_notice_cache_repository()
        factory.reset_related_notice_publication_repository()
        factory.reset_sales_claim_repository()
        factory.reset_tracker_change_event_repository()
        factory.reset_tracker_entry_snapshot_repository()
        factory.reset_home_bootstrap_snapshot_repository()
        factory.reset_backfill_conflict_repository()

    def tearDown(self) -> None:
        factory.reset_tracker_entry_repository()
        factory.reset_related_notice_cache_repository()
        factory.reset_related_notice_publication_repository()
        factory.reset_sales_claim_repository()
        factory.reset_tracker_change_event_repository()
        factory.reset_tracker_entry_snapshot_repository()
        factory.reset_home_bootstrap_snapshot_repository()
        factory.reset_backfill_conflict_repository()
        self._tmp.cleanup()

    def test_local_rows_store_enables_wal_and_long_busy_timeout(self) -> None:
        with self.store._connection() as conn:
            journal_mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()
            busy_timeout = int(conn.execute("PRAGMA busy_timeout").fetchone()[0])

        self.assertEqual(journal_mode, "wal")
        self.assertGreaterEqual(busy_timeout, 30000)

    def test_factory_supports_sqlite_for_all_local_data_repositories(self) -> None:
        with patch.dict(os.environ, self.env, clear=False):
            backend_summary = factory.describe_repository_backends()
            repositories = [
                factory.get_tracker_entry_repository(),
                factory.get_related_notice_cache_repository(),
                factory.get_related_notice_publication_repository(),
                factory.get_sales_claim_repository(),
                factory.get_tracker_change_event_repository(),
                factory.get_tracker_entry_snapshot_repository(),
                factory.get_home_bootstrap_snapshot_repository(),
                factory.get_backfill_conflict_repository(),
            ]

        self.assertEqual(backend_summary["tracker_entries"], "sqlite")
        self.assertEqual(backend_summary["related_notice_cache"], "sqlite")
        self.assertEqual(backend_summary["related_notice_publications"], "sqlite")
        self.assertEqual(backend_summary["sales_claims"], "sqlite")
        self.assertEqual(backend_summary["tracker_entry_snapshots"], "sqlite")
        self.assertEqual(backend_summary["home_bootstrap_snapshots"], "sqlite")
        self.assertTrue(all(repository is not None for repository in repositories))

    def test_sqlite_tracker_entries_read_exported_rows_and_write_overrides(self) -> None:
        entry_id = uuid4()
        self.store.upsert_row(
            "tracker_entries",
            str(entry_id),
            {
                "id": str(entry_id),
                "organization_id": str(DEFAULT_PHASE1_ORGANIZATION_ID),
                "source_run_id": str(uuid4()),
                "source_tracker_run_id": str(uuid4()),
                "entry_key": "entry-key-1",
                "sheet_name": "Sheet1",
                "section_name": "facility_cost",
                "row_no": 7,
                "source_bid_no": "R26BK00000001",
                "source_bid_ord": "000",
                "source_project_name_norm": "alpha-project",
                "project_name_source": "Alpha Project",
                "project_name_override": None,
                "gross_area_scale_source": "",
                "gross_area_scale_override": None,
                "construction_cost_source": "",
                "construction_cost_override": None,
                "demand_org_name_source": "",
                "demand_org_name_override": None,
                "demand_contact_source": "",
                "demand_contact_override": None,
                "client_location_source": "",
                "client_location_override": None,
                "site_location_1_source": "Seoul",
                "site_location_1_override": None,
                "site_location_2_source": "",
                "site_location_2_override": None,
                "architect_office_source": "",
                "architect_office_override": None,
                "opening_scheduled_date_source": "",
                "contract_date_source": "",
                "construction_duration_days_source": "",
                "completion_expected_date_explicit_source": "",
                "completion_expected_date_computed_source": "",
                "construction_start_date_source": "",
                "construction_start_date_override": None,
                "last_checked_date_source": "",
                "last_checked_date_override": None,
                "progress_note_source": "",
                "progress_note_override": None,
                "notice_date_source": "",
                "notice_date_override": None,
                "manager_name_source": "",
                "manager_name_override": None,
                "building_automation_estimated_amount_source": "",
                "building_automation_estimated_amount_override": None,
                "last_edited_at": None,
                "last_edited_by": None,
                "last_edited_by_label": "",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            },
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
        )

        with patch.dict(os.environ, self.env, clear=False):
            repository = factory.get_tracker_entry_repository()
            rows, total = repository.list_entries(
                page=1,
                page_size=20,
                q="alpha",
                region="",
                exclude_auxiliary_titles=False,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=None,
                sheet_name="",
                section_name="",
            )
            result = repository.apply_override(
                entry_id=entry_id,
                field_name="project_name",
                new_value="Alpha Project Local",
                actor_user_id=None,
                actor_label="local-admin",
                change_source="web",
            )

        self.assertEqual(total, 1)
        self.assertEqual(rows[0]["project_name"], "Alpha Project")
        self.assertIsNotNone(result)
        self.assertTrue(result.changed)
        self.assertEqual(result.entry["project_name"], "Alpha Project Local")
        stored = self.store.get_row("tracker_entries", str(entry_id))
        self.assertEqual(stored["project_name_override"], "Alpha Project Local")


if __name__ == "__main__":
    unittest.main()
