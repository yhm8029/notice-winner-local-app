import unittest
from concurrent.futures import TimeoutError as FuturesTimeoutError
from types import SimpleNamespace
from unittest.mock import Mock
from unittest.mock import patch
from uuid import uuid4

from backend.api import app as phase1_app
from backend.repositories.in_memory_related_notice_cache import InMemoryRelatedNoticeCacheRepository
from backend.repositories.in_memory_related_notice_publications import InMemoryRelatedNoticePublicationRepository
from backend.services import run_execution
from backend.services.run_execution import _build_related_notice_artifact_payload


class _CompletedFuture:
    def __init__(self, value) -> None:  # type: ignore[no-untyped-def]
        self._value = value

    def result(self, timeout=None):  # type: ignore[no-untyped-def]
        return self._value


class _BlockedFuture:
    def result(self, timeout=None):  # type: ignore[no-untyped-def]
        if timeout is None:
            raise AssertionError("blocked related-notice collect future was awaited without a timeout")
        raise FuturesTimeoutError()


class _FakeThreadPoolExecutor:
    def __init__(self, *, completed_value) -> None:  # type: ignore[no-untyped-def]
        self._completed_value = completed_value
        self._submit_calls = 0

    def __enter__(self):  # type: ignore[no-untyped-def]
        return self

    def __exit__(self, exc_type, exc, tb):  # type: ignore[no-untyped-def]
        return False

    def submit(self, fn, recipe_index, params):  # type: ignore[no-untyped-def]
        del fn, recipe_index, params
        self._submit_calls += 1
        if self._submit_calls == 1:
            return _CompletedFuture(self._completed_value)
        return _BlockedFuture()

    def shutdown(self, wait=True, cancel_futures=False):  # type: ignore[no-untyped-def]
        self.shutdown_args = (wait, cancel_futures)


class RelatedNoticeDebugLoggingTests(unittest.TestCase):
    def test_artifact_payload_includes_search_debug(self) -> None:
        run_id = uuid4()
        params = {
            "notice_title": "Doctor housing construction",
            "demand_org": "Gangjin Medical Center",
            "end_date": "20240331",
        }
        seed_rows = [
            {
                "project_name": "Doctor housing construction design competition notice",
                "org_name": "Gangjin Medical Center",
                "announce_date": "20240110",
                "bid_no": "20240108577",
                "bid_ord": "000",
            }
        ]
        fake_live_items = [
            {
                "id": "20240108577::000::doctor-housing",
                "project_name": "Doctor housing construction design competition notice",
                "project_search_name": "Doctor housing construction",
                "issuer_name": "Gangjin Medical Center",
                "announce_date": "20240110",
                "bid_no": "20240108577",
                "bid_ord": "000",
                "g2b_verified": "Y",
                "notice_url": "",
                "notice_detail_url": "",
                "match_score": 144,
                "match_reason": "same_search_name",
            }
        ]
        fake_debug = {
            "project_name": "Doctor housing construction design competition notice",
            "project_search_name": "Doctor housing construction",
            "attempts": [
                {
                    "query": "Doctor housing construction",
                    "endpoint_mode": "service",
                    "row_count": 1,
                }
            ],
            "deduped_row_count": 1,
            "final_item_count": 1,
        }

        with patch(
            "backend.api.app._live_related_notice_search",
            return_value=(
                [
                    type(
                        "FakeItem",
                        (),
                        {"model_dump": lambda self, mode="json": dict(fake_live_items[0])},
                    )()
                ],
                fake_debug,
            ),
        ):
            payload = _build_related_notice_artifact_payload(
                run_id=run_id,
                params=params,
                seed_rows=seed_rows,
            )

        self.assertGreaterEqual(payload["project_count"], 1)
        project_entry = next(
            entry
            for entry in payload["projects"]
            if entry["project_search_name"] == "Doctor housing construction"
        )
        self.assertEqual(project_entry["source"], "live")
        self.assertEqual(project_entry["search_debug"]["final_item_count"], 1)
        self.assertEqual(project_entry["search_debug"]["attempts"][0]["query"], "Doctor housing construction")

    def test_artifact_payload_reuses_published_cache_before_live_search(self) -> None:
        run_id = uuid4()
        params = {
            "notice_title": "Doctor housing construction",
            "demand_org": "Gangjin Medical Center",
            "end_date": "20240331",
        }
        seed_rows = [
            {
                "project_name": "Doctor housing construction design competition notice",
                "org_name": "Gangjin Medical Center",
                "announce_date": "20240110",
                "bid_no": "20240108577",
                "bid_ord": "000",
            }
        ]
        cache_repository = InMemoryRelatedNoticeCacheRepository()
        organization_id = uuid4()
        publication_repository = InMemoryRelatedNoticePublicationRepository()
        publication_repository.upsert_publication(
            organization_id=organization_id,
            published_snapshot_set_id="snapshot-live-001",
            source_run_id=uuid4(),
            generated_at="2026-04-09T11:00:00+00:00",
            published_at="2026-04-09T11:00:00+00:00",
        )
        cache_repository.upsert_cache(
            {
                "organization_id": "ignored",
                "project_key": "doctor-housing-construction",
                "snapshot_set_id": "snapshot-live-001",
                "status": "success",
                "source": "live",
                "algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
                "item_count": 1,
                "payload_json": {
                    "project_key": "doctor-housing-construction",
                    "project_name": "Doctor housing construction design competition notice",
                    "project_search_name": "Doctor housing construction",
                    "issuer_name": "Gangjin Medical Center",
                    "source": "live",
                    "algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
                    "items": [
                        {
                            "id": "cached-1",
                            "project_name": "Doctor housing construction design competition notice",
                            "project_search_name": "Doctor housing construction",
                            "issuer_name": "Gangjin Medical Center",
                            "announce_date": "20240110",
                            "bid_no": "20240108577",
                            "bid_ord": "000",
                            "g2b_verified": "Y",
                            "notice_url": "",
                            "notice_detail_url": "",
                            "match_score": 144,
                            "match_reason": "same_search_name",
                        }
                    ],
                },
            }
        )

        with patch("backend.api.app._project_search_name", side_effect=lambda value: str(value).strip()), patch(
            "backend.api.app._project_match_key",
            side_effect=lambda value: str(value).strip().lower().replace(" ", "-"),
        ), patch("backend.api.app._better_project_label", side_effect=lambda current, new: new or current), patch(
            "backend.api.app._is_generic_project_term",
            return_value=False,
        ), patch(
            "backend.services.run_execution.get_related_notice_cache_repository",
            return_value=cache_repository,
        ), patch(
            "backend.services.run_execution.get_related_notice_publication_repository",
            return_value=publication_repository,
        ), patch(
            "backend.services.run_execution.load_phase1_identity",
            return_value=SimpleNamespace(organization_id=organization_id),
        ), patch(
            "backend.api.app._live_related_notice_search",
            side_effect=AssertionError("live search should not run when reusable cache exists"),
        ):
            payload = _build_related_notice_artifact_payload(
                run_id=run_id,
                params=params,
                seed_rows=seed_rows,
            )

        project_entry = next(
            entry
            for entry in payload["projects"]
            if entry["project_key"] == "doctor-housing-construction"
        )
        self.assertEqual(project_entry["items"][0]["id"], "cached-1")
        self.assertEqual(project_entry["search_debug"]["cache_reused"], True)
        self.assertEqual(project_entry["search_debug"]["reused_snapshot_set_id"], "snapshot-live-001")

    def test_artifact_payload_uses_seed_fallback_for_full_publish_cache_miss_without_live_search(self) -> None:
        run_id = uuid4()
        params = {
            "notice_title": "Doctor housing construction",
            "demand_org": "Gangjin Medical Center",
            "end_date": "20240331",
        }
        seed_rows = [
            {
                "project_name": "Doctor housing construction design competition notice",
                "org_name": "Gangjin Medical Center",
                "announce_date": "20240110",
                "bid_no": "20240108577",
                "bid_ord": "000",
                "g2b_verified": "Y",
                "bid_ntce_url": "https://example.test/notice",
                "bid_ntce_dtl_url": "https://example.test/notice/detail",
            }
        ]

        live_search_mock = Mock(
            return_value=(
                [
                    type(
                        "FakeItem",
                        (),
                        {
                            "model_dump": lambda self, mode="json": {
                                "id": "live-1",
                                "project_name": "Doctor housing construction design competition notice",
                                "project_search_name": "Doctor housing construction",
                                "issuer_name": "Gangjin Medical Center",
                                "announce_date": "20240110",
                                "bid_no": "LIVE001",
                                "bid_ord": "000",
                                "g2b_verified": "Y",
                                "notice_url": "",
                                "notice_detail_url": "",
                                "match_score": 144,
                                "match_reason": "same_search_name",
                            }
                        },
                    )()
                ],
                {"final_item_count": 1},
            )
        )

        with patch("backend.api.app._project_search_name", side_effect=lambda value: str(value).strip()), patch(
            "backend.api.app._project_match_key",
            side_effect=lambda value: str(value).strip().lower().replace(" ", "-"),
        ), patch("backend.api.app._better_project_label", side_effect=lambda current, new: new or current), patch(
            "backend.api.app._is_generic_project_term",
            return_value=False,
        ), patch(
            "backend.services.run_execution.get_related_notice_publication_repository",
            return_value=InMemoryRelatedNoticePublicationRepository(),
        ), patch(
            "backend.services.run_execution.get_related_notice_cache_repository",
            return_value=InMemoryRelatedNoticeCacheRepository(),
        ), patch(
            "backend.services.run_execution.load_phase1_identity",
            return_value=SimpleNamespace(organization_id=uuid4()),
        ), patch(
            "backend.api.app._live_related_notice_search",
            live_search_mock,
        ):
            payload = _build_related_notice_artifact_payload(
                run_id=run_id,
                params=params,
                seed_rows=seed_rows,
                prefer_seed_fallback_on_cache_miss=True,
            )

        project_entry = next(
            entry
            for entry in payload["projects"]
            if entry["project_key"] == "doctor-housing-construction"
        )
        self.assertEqual(project_entry["source"], "seed_fallback")
        self.assertEqual(project_entry["item_count"], 1)
        self.assertEqual(project_entry["items"][0]["bid_no"], "20240108577")
        self.assertEqual(project_entry["search_debug"]["seed_fallback"]["used"], True)
        self.assertEqual(project_entry["search_debug"]["seed_fallback"]["item_count"], 1)
        live_search_mock.assert_not_called()

    def test_collect_related_notice_rows_with_debug_does_not_block_on_stuck_parallel_attempt(self) -> None:
        completed_attempt = (
            {
                "recipe_index": 0,
                "query_index": 0,
                "query": "Alpha",
                "api_scope": "service",
                "demand_org": "",
                "start_date": "20240101",
                "end_date": "20240131",
                "rows_per_page": 100,
                "max_pages": 3,
                "row_count": 1,
            },
            [
                {
                    "bid_no": "20240100001",
                    "bid_ord": "000",
                    "project_name": "Alpha Project",
                    "org_name": "City Hall",
                    "announce_date": "20240110",
                }
            ],
            False,
        )
        fake_executor = _FakeThreadPoolExecutor(completed_value=completed_attempt)
        recipes = [
            {
                "notice_title": "Alpha",
                "api_scope": "service",
                "start_date": "20240101",
                "end_date": "20240131",
                "rows_per_page": 100,
                "max_pages": 3,
            },
            {
                "notice_title": "Beta",
                "api_scope": "service",
                "start_date": "20240101",
                "end_date": "20240131",
                "rows_per_page": 100,
                "max_pages": 3,
            },
        ]

        with patch.object(phase1_app, "_build_related_notice_collect_recipes", return_value=recipes), patch.object(
            phase1_app,
            "ThreadPoolExecutor",
            return_value=fake_executor,
        ), patch.object(phase1_app, "_dedupe_related_notice_rows", side_effect=lambda rows: list(rows)):
            rows, debug = phase1_app._collect_related_notice_rows_with_debug(
                {"project_name": "Alpha Project", "project_search_name": "Alpha"},
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["bid_no"], "20240100001")
        self.assertEqual(len(debug["attempts"]), 2)
        self.assertIn("timed out", str(debug["attempts"][1].get("error") or ""))


if __name__ == "__main__":
    unittest.main()
