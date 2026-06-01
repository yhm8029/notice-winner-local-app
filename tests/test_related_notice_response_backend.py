from __future__ import annotations

import unittest
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from uuid import uuid4

from backend.api.schemas import RelatedNoticeItem
from backend.services.related_notice_response_backend import get_related_notice_project_precompute_state
from backend.services.related_notice_response_backend import is_related_notice_precompute_stale
from backend.services.related_notice_response_backend import related_notice_response_without_live


class RelatedNoticeResponseBackendTests(unittest.TestCase):
    def test_get_related_notice_project_precompute_state_returns_empty_when_missing(self) -> None:
        state = get_related_notice_project_precompute_state({}, "project-key")

        self.assertEqual(state, ("", "", None, False))

    def test_is_related_notice_precompute_stale_detects_old_pending_state(self) -> None:
        now = datetime.now(timezone.utc)
        stale_row = {"updated_at": (now - timedelta(minutes=10)).isoformat()}
        fresh_row = {"updated_at": (now - timedelta(seconds=30)).isoformat()}

        self.assertTrue(
            is_related_notice_precompute_stale(
                stale_row,
                "queued",
                updated_at=None,
                parse_iso_datetime_fn=lambda value: datetime.fromisoformat(str(value).replace("Z", "+00:00")),
                stale_sec=120,
            )
        )
        self.assertFalse(
            is_related_notice_precompute_stale(
                fresh_row,
                "running",
                updated_at=None,
                parse_iso_datetime_fn=lambda value: datetime.fromisoformat(str(value).replace("Z", "+00:00")),
                stale_sec=120,
            )
        )

    def test_related_notice_response_without_live_returns_pending_without_seed_fallback_while_cache_running(self) -> None:
        project_id = uuid4()
        project = {
            "project_name": "demo project",
            "project_search_name": "demo project",
            "_project_match_key": "demoproject",
            "issuer_name": "issuer",
            "source_json": {"run_ids": ["00000000-0000-0000-0000-000000000001"]},
        }
        run_row = {
            "id": "00000000-0000-0000-0000-000000000001",
            "status": "success",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "summary_json": {"output": {}},
        }
        cache_row = {
            "status": "running",
            "source": "precompute",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "error": "",
            "payload_json": {},
        }

        response = related_notice_response_without_live(
            project=project,
            project_id=project_id,
            trace_id=None,
            project_source_runs_fn=lambda project: [run_row],
            get_related_notice_cache_fn=lambda project_key: cache_row,
            is_missing_related_notice_cache_table_error_fn=lambda message: False,
            repository_error_fn=lambda message: (_ for _ in ()).throw(AssertionError(message)),
            is_related_notice_precompute_stale_fn=lambda run_row, status, updated_at=None: False,
            is_related_notice_payload_entry_precomputed_fn=lambda payload: False,
            filter_self_related_notice_payload_items_fn=lambda project, items: items,
            dedupe_related_notice_payload_items_fn=lambda items: items,
            seed_related_notice_items_fn=lambda project, trace_id=None, project_id=None: (_ for _ in ()).throw(
                AssertionError("seed fallback should not run on request path")
            ),
            append_related_notice_trace_fn=lambda **kwargs: None,
            get_run_repository_fn=lambda: None,
            queue_related_notice_precompute_for_run_fn=lambda run_id, project_key=None: True,
            upsert_related_notice_cache_fn=lambda row: row,
            get_related_notice_project_precompute_state_fn=get_related_notice_project_precompute_state,
            related_notice_algorithm_version=1,
        )

        self.assertEqual(response.status, "pending")
        self.assertEqual(response.source, "precompute")
        self.assertEqual(len(response.items), 0)

    def test_related_notice_response_without_live_queues_precompute_without_seed_fallback_and_records_project_status(self) -> None:
        project_id = uuid4()
        project = {
            "project_name": "demo project",
            "project_search_name": "demo project",
            "_project_match_key": "demoproject",
            "issuer_name": "issuer",
            "source_json": {"run_ids": ["00000000-0000-0000-0000-000000000002"]},
        }
        run_row = {
            "id": "00000000-0000-0000-0000-000000000002",
            "status": "success",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "summary_json": {"output": {}},
        }
        updates: list[tuple[str, dict[str, object]]] = []
        cached_rows: list[dict[str, object]] = []

        class FakeRunRepo:
            def update_run(self, run_id, fields):
                updates.append((str(run_id), fields))

        response = related_notice_response_without_live(
            project=project,
            project_id=project_id,
            trace_id=None,
            project_source_runs_fn=lambda project: [run_row],
            get_related_notice_cache_fn=lambda project_key: None,
            is_missing_related_notice_cache_table_error_fn=lambda message: False,
            repository_error_fn=lambda message: (_ for _ in ()).throw(AssertionError(message)),
            is_related_notice_precompute_stale_fn=lambda run_row, status, updated_at=None: False,
            is_related_notice_payload_entry_precomputed_fn=lambda payload: False,
            filter_self_related_notice_payload_items_fn=lambda project, items: items,
            dedupe_related_notice_payload_items_fn=lambda items: items,
            seed_related_notice_items_fn=lambda project, trace_id=None, project_id=None: (_ for _ in ()).throw(
                AssertionError("seed fallback should not run on request path")
            ),
            append_related_notice_trace_fn=lambda **kwargs: None,
            get_run_repository_fn=lambda: FakeRunRepo(),
            queue_related_notice_precompute_for_run_fn=lambda run_id, project_key=None: True,
            upsert_related_notice_cache_fn=lambda row: cached_rows.append(row) or row,
            get_related_notice_project_precompute_state_fn=get_related_notice_project_precompute_state,
            related_notice_algorithm_version=7,
        )

        self.assertEqual(response.status, "pending")
        self.assertEqual(response.source, "precompute")
        self.assertEqual(len(response.items), 0)
        self.assertEqual(len(updates), 1)
        self.assertEqual(len(cached_rows), 1)
        project_statuses = dict(updates[0][1]["summary_json"]["output"]["related_notice_project_statuses"])
        self.assertEqual(project_statuses["demoproject"]["status"], "queued")
        self.assertEqual(cached_rows[0]["status"], "queued")
        self.assertEqual(cached_rows[0]["algorithm_version"], 7)


if __name__ == "__main__":
    unittest.main()
