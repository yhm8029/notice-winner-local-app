from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.repositories.related_notice_cache import RelatedNoticeCacheRepositoryError
from backend.repositories.supabase_related_notice_cache import SupabaseRelatedNoticeCacheRepository
from backend.repositories.supabase_related_notice_cache import SupabaseRelatedNoticeCacheRepositoryConfig


class SupabaseRelatedNoticeCacheRepositoryTests(unittest.TestCase):
    def test_get_cache_falls_back_to_legacy_schema_when_snapshot_column_missing(self) -> None:
        repository = SupabaseRelatedNoticeCacheRepository(
            SupabaseRelatedNoticeCacheRepositoryConfig(
                base_url="https://example.supabase.co",
                api_key="secret",
                organization_id="7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
            )
        )
        calls: list[dict[str, object]] = []

        def fake_request_json(**kwargs):  # type: ignore[no-untyped-def]
            calls.append(kwargs)
            query = list(kwargs.get("query") or [])
            select_value = next((value for key, value in query if key == "select"), "")
            snapshot_query = next((value for key, value in query if key == "snapshot_set_id"), None)
            if len(calls) == 1:
                self.assertIn("snapshot_set_id", select_value)
                self.assertEqual(snapshot_query, "eq.legacy")
                raise RelatedNoticeCacheRepositoryError(
                    "column project_related_notice_cache.snapshot_set_id does not exist"
                )
            self.assertNotIn("snapshot_set_id", select_value)
            self.assertIsNone(snapshot_query)
            return (
                [
                    {
                        "id": "cache-row-1",
                        "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                        "project_key": "project-alpha",
                        "project_name": "Alpha Project",
                        "project_search_name": "alpha project",
                        "issuer_name": "Issuer",
                        "status": "success",
                        "source": "legacy_cache",
                        "algorithm_version": 11,
                        "item_count": 1,
                        "error": "",
                        "payload_json": {"items": [{"id": "notice-1"}]},
                        "source_run_id": "55555555-5555-5555-5555-555555555555",
                        "generated_at": "2026-04-09T01:00:00+00:00",
                        "created_at": "2026-04-09T01:00:00+00:00",
                        "updated_at": "2026-04-09T01:00:00+00:00",
                    }
                ],
                {},
            )

        with patch("backend.repositories.supabase_related_notice_cache.request_json", side_effect=fake_request_json):
            row = repository.get_cache(project_key="project-alpha", snapshot_set_id="legacy")

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row["project_key"], "project-alpha")
        self.assertEqual(row["snapshot_set_id"], "legacy")
        self.assertEqual(row["source"], "legacy_cache")
        self.assertEqual(len(calls), 2)

    def test_upsert_cache_falls_back_when_snapshot_conflict_constraint_is_missing(self) -> None:
        repository = SupabaseRelatedNoticeCacheRepository(
            SupabaseRelatedNoticeCacheRepositoryConfig(
                base_url="https://example.supabase.co",
                api_key="secret",
                organization_id="7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
            )
        )
        calls: list[dict[str, object]] = []

        def fake_request_json(**kwargs):  # type: ignore[no-untyped-def]
            calls.append(kwargs)
            query = list(kwargs.get("query") or [])
            conflict_value = next((value for key, value in query if key == "on_conflict"), "")
            payload = dict(kwargs.get("payload") or {})
            if len(calls) == 1:
                self.assertEqual(conflict_value, "organization_id,snapshot_set_id,project_key")
                raise RelatedNoticeCacheRepositoryError(
                    "there is no unique or exclusion constraint matching the ON CONFLICT specification"
                )
            self.assertEqual(conflict_value, "organization_id,project_key")
            self.assertEqual(payload.get("snapshot_set_id"), "snapshot-live")
            return (
                [
                    {
                        "id": "cache-row-1",
                        "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                        "project_key": "project-alpha",
                        "snapshot_set_id": "snapshot-live",
                        "project_name": "Alpha Project",
                        "project_search_name": "alpha project",
                        "issuer_name": "Issuer",
                        "status": "success",
                        "source": "precompute",
                        "algorithm_version": 12,
                        "item_count": 1,
                        "error": "",
                        "payload_json": {"items": [{"id": "notice-1"}]},
                        "source_run_id": "55555555-5555-5555-5555-555555555555",
                        "generated_at": "2026-05-03T01:00:00+00:00",
                        "created_at": "2026-05-03T01:00:00+00:00",
                        "updated_at": "2026-05-03T01:00:00+00:00",
                    }
                ],
                {},
            )

        with patch("backend.repositories.supabase_related_notice_cache.request_json", side_effect=fake_request_json):
            row = repository.upsert_cache(
                {
                    "project_key": "project-alpha",
                    "snapshot_set_id": "snapshot-live",
                    "project_name": "Alpha Project",
                    "project_search_name": "alpha project",
                    "issuer_name": "Issuer",
                    "status": "success",
                    "source": "precompute",
                    "algorithm_version": 12,
                    "item_count": 1,
                    "error": "",
                    "payload_json": {"items": [{"id": "notice-1"}]},
                    "source_run_id": "55555555-5555-5555-5555-555555555555",
                    "generated_at": "2026-05-03T01:00:00+00:00",
                }
            )

        self.assertEqual(row["project_key"], "project-alpha")
        self.assertEqual(row["snapshot_set_id"], "snapshot-live")
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
