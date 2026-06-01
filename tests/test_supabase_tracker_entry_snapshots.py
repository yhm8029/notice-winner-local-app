from __future__ import annotations

import unittest
from unittest.mock import patch
from uuid import uuid4

from backend.repositories.supabase_tracker_entry_snapshots import (
    SupabaseTrackerEntrySnapshotRepository,
    SupabaseTrackerEntrySnapshotRepositoryConfig,
)


class SupabaseTrackerEntrySnapshotRepositoryTests(unittest.TestCase):
    def test_get_snapshots_chunks_large_in_queries(self) -> None:
        repository = SupabaseTrackerEntrySnapshotRepository(
            SupabaseTrackerEntrySnapshotRepositoryConfig(
                base_url="https://example.supabase.co",
                api_key="test-key",
            )
        )
        organization_id = uuid4()
        tracker_entry_ids = [uuid4() for _ in range(205)]
        seen_batches: list[list[str]] = []

        def fake_request_json(**kwargs):
            query = kwargs.get("query") or []
            tracker_query = next(value for key, value in query if key == "tracker_entry_id")
            self.assertTrue(str(kwargs.get("path") or "").endswith("/tracker_entry_snapshots"))
            batch_ids = [item for item in tracker_query.removeprefix("in.(").removesuffix(")").split(",") if item]
            seen_batches.append(batch_ids)
            rows = [
                {
                    "tracker_entry_id": item,
                    "organization_id": str(organization_id),
                    "summary_json": {"id": item},
                    "detail_json": {"id": item},
                    "export_json": {"id": item},
                    "updated_at": "2026-03-29T00:00:00+00:00",
                }
                for item in batch_ids
            ]
            return rows, {}

        with patch("backend.repositories.supabase_tracker_entry_snapshots.request_json", side_effect=fake_request_json):
            rows = repository.get_snapshots(
                organization_id=organization_id,
                tracker_entry_ids=tracker_entry_ids,
            )

        self.assertEqual(len(seen_batches), 3)
        self.assertEqual([len(batch) for batch in seen_batches], [100, 100, 5])
        self.assertEqual(len(rows), 205)


if __name__ == "__main__":
    unittest.main()
