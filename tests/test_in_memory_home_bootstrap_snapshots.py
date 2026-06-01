from __future__ import annotations

import unittest
from uuid import uuid4

from backend.repositories.in_memory_home_bootstrap_snapshots import InMemoryHomeBootstrapSnapshotRepository


class InMemoryHomeBootstrapSnapshotRepositoryTests(unittest.TestCase):
    def test_upsert_get_and_invalidate_roundtrip(self) -> None:
        repository = InMemoryHomeBootstrapSnapshotRepository()
        organization_id = uuid4()

        repository.upsert_snapshot(
            organization_id=organization_id,
            snapshot_version=1,
            payload_json={
                "company_items": [{"project_id": str(uuid4()), "project_name": "테스트 프로젝트"}],
                "organization_users": [],
                "tracker_first_page": {"items": [], "page": 1, "page_size": 20, "total": 0},
            },
            generated_at="2026-03-29T00:00:00+00:00",
        )

        snapshot = repository.get_snapshot(organization_id=organization_id)
        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertEqual(snapshot["snapshot_version"], 1)
        self.assertEqual(snapshot["payload_json"]["company_items"][0]["project_name"], "테스트 프로젝트")
        self.assertIsNone(snapshot.get("invalidated_at"))

        repository.invalidate_snapshot(organization_id=organization_id)
        invalidated = repository.get_snapshot(organization_id=organization_id)
        self.assertIsNotNone(invalidated)
        assert invalidated is not None
        self.assertIsNotNone(invalidated.get("invalidated_at"))


if __name__ == "__main__":
    unittest.main()
