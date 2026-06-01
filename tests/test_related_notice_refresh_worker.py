from __future__ import annotations

import unittest
from uuid import uuid4

from backend.repositories.in_memory_related_notice_cache import InMemoryRelatedNoticeCacheRepository
from backend.services.related_notice_refresh_worker import _drain_once


class RelatedNoticeRefreshWorkerTests(unittest.TestCase):
    def test_drain_once_claims_queued_rows_and_runs_single_project_refresh(self) -> None:
        repository = InMemoryRelatedNoticeCacheRepository()
        run_id = uuid4()
        repository.upsert_cache(
            {
                "project_key": "project-alpha",
                "snapshot_set_id": "snapshot-live",
                "status": "queued",
                "source_run_id": str(run_id),
                "payload_json": {"refresh_status": "queued"},
            }
        )
        calls: list[tuple[object, dict[str, object]]] = []

        processed = _drain_once(
            get_related_notice_cache_repository_fn=lambda: repository,
            safely_precompute_related_notices_for_run_fn=lambda run_id, **kwargs: calls.append((run_id, kwargs)),
            limit=1,
        )

        self.assertEqual(processed, 1)
        self.assertEqual(
            calls,
            [
                (
                    run_id,
                    {
                        "project_key": "project-alpha",
                        "backfill_remaining": False,
                        "force_recompute": True,
                        "snapshot_set_id": "snapshot-live",
                    },
                )
            ],
        )
        self.assertEqual(
            repository.get_cache(project_key="project-alpha", snapshot_set_id="snapshot-live")["status"],
            "running",
        )

