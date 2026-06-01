from __future__ import annotations

import unittest
import time
from types import SimpleNamespace
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from unittest.mock import patch
from uuid import uuid4

from backend.api.schemas import RelatedNoticeItem
from backend.api.app import _build_project_aggregates
from backend.api.app import _clear_project_aggregates_cache
from backend.api.app import _build_related_notice_primary_queries
from backend.api.app import _build_related_notice_primary_scopes
from backend.api.app import _clear_related_notice_response_cache
from backend.api.app import _annotate_tracker_entries_with_project_refs
from backend.api.app import _dedupe_related_notice_payload_items
from backend.api.app import _get_related_notice_response_cache
from backend.api.app import _get_project_aggregate
from backend.api.app import _is_related_notice_payload_entry_precomputed
from backend.api.app import _is_related_notice_precompute_stale
from backend.api.app import _list_related_notices_for_project
from backend.api.app import _parse_iso_datetime
from backend.api.app import _precomputed_related_notice_items
from backend.api.app import _force_recompute_related_notices_for_project
from backend.api.app import _get_related_notice_progress_for_project
from backend.api.app import _queue_project_aggregates_cache_warm
from backend.api.app import _related_notice_response_without_live
from backend.repositories import RelatedNoticeCacheRepositoryError
from backend.repositories import get_related_notice_cache_repository
from backend.services.related_notice_progress import clear_related_notice_progress
from backend.services.related_notice_progress import get_related_notice_progress
from backend.services.related_notice_progress import update_related_notice_progress
from backend.api.support.projects_related_notice_support import _live_related_notice_search as _support_live_related_notice_search
from backend.api.support.projects_related_notice_support import _quick_related_notice_search as _support_quick_related_notice_search
from backend.services.native_seed_backend import SeedFetchDiagnostics
from backend.services.native_seed_backend import SeedFetchResult
from backend.services import run_execution
from backend.services.run_execution import _related_notice_payload_has_project
from backend.services.run_execution import queue_related_notice_precompute_for_run
from backend.services.run_execution import RELATED_NOTICE_PRECOMPUTE_ACTIVE_STALE_SEC


class RelatedNoticeHelperTests(unittest.TestCase):
    def tearDown(self) -> None:
        with run_execution._PRECOMPUTE_ACTIVE_LOCK:
            run_execution._PRECOMPUTE_ACTIVE.clear()
        _clear_project_aggregates_cache()
        _clear_related_notice_response_cache()
        clear_related_notice_progress()

    def test_seed_fallback_payload_entry_with_current_algorithm_is_treated_as_completed_result(self) -> None:
        entry = {
            "project_key": "abc",
            "source": "seed_fallback",
            "algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
            "items": [{"id": "1"}],
        }

        self.assertTrue(_is_related_notice_payload_entry_precomputed(entry))
        self.assertTrue(_related_notice_payload_has_project({"projects": [entry]}, "abc"))

    def test_seed_fallback_payload_entry_without_items_is_not_treated_as_completed_result(self) -> None:
        entry = {
            "project_key": "abc",
            "source": "seed_fallback",
            "algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
            "items": [],
        }

        self.assertFalse(_is_related_notice_payload_entry_precomputed(entry))
        self.assertFalse(_related_notice_payload_has_project({"projects": [entry]}, "abc"))

    def test_precomputed_related_notice_items_prefers_global_cache(self) -> None:
        project = {
            "project_name": "Demo Project",
            "project_search_name": "Demo Project",
            "_project_match_key": "demoproject",
            "issuer_name": "Demo Issuer",
            "source_json": {"run_ids": []},
        }
        published_snapshot_set_id = "snapshot-live"
        test_case = self

        class FakePublicationRepo:
            def get_publication(self, *, organization_id):  # type: ignore[no-untyped-def]
                return {
                    "published_snapshot_set_id": published_snapshot_set_id,
                    "source_run_id": str(uuid4()),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                }

        class FakeCacheRepo:
            def get_cache(self, *, project_key, snapshot_set_id=None):  # type: ignore[no-untyped-def]
                test_case.assertEqual(project_key, "demoproject")
                test_case.assertEqual(snapshot_set_id, published_snapshot_set_id)
                return {
                    "project_key": project_key,
                    "snapshot_set_id": snapshot_set_id,
                    "status": "success",
                    "source": "live",
                    "algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
                    "payload_json": {
                        "project_key": project_key,
                        "snapshot_set_id": snapshot_set_id,
                        "source": "live",
                        "algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
                        "items": [
                            {
                                "id": "notice-1",
                                "project_name": "Demo Project",
                                "project_search_name": "Demo Project",
                                "issuer_name": "Demo Issuer",
                                "announce_date": "20250328",
                                "bid_no": "R25BK00000001",
                                "bid_ord": "000",
                                "g2b_verified": "Y",
                                "notice_url": "",
                                "notice_detail_url": "",
                                "match_score": 144,
                                "match_reason": "cache",
                            }
                        ],
                    },
                }

            def upsert_cache(self, row):
                return row

        with patch("backend.api.app._get_related_notice_publication_repository", return_value=FakePublicationRepo()), patch(
            "backend.api.app._get_related_notice_cache_repository", return_value=FakeCacheRepo()
        ):
            items, has_precomputed = _precomputed_related_notice_items(project, project_id=uuid4())

        self.assertTrue(has_precomputed)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].bid_no, "R25BK00000001")

    def test_precomputed_related_notice_items_returns_empty_when_published_snapshot_row_missing(self) -> None:
        project = {
            "project_name": "demo project",
            "project_search_name": "demo project",
            "_project_match_key": "demoproject",
            "issuer_name": "issuer",
            "source_json": {"run_ids": ["00000000-0000-0000-0000-000000000001"]},
        }
        test_case = self

        class FakePublicationRepo:
            def get_publication(self, *, organization_id):  # type: ignore[no-untyped-def]
                return {"published_snapshot_set_id": "snapshot-live"}

        class FakeCacheRepo:
            def get_cache(self, *, project_key, snapshot_set_id=None):  # type: ignore[no-untyped-def]
                test_case.assertEqual(project_key, "demoproject")
                test_case.assertEqual(snapshot_set_id, "snapshot-live")
                return None

            def upsert_cache(self, row):
                return row

        fake_artifact_repo = type(
            "FakeArtifactRepo",
            (),
            {"list_artifacts": lambda self, run_id: (_ for _ in ()).throw(AssertionError("artifact lookup should not happen"))},
        )()

        with patch("backend.api.app._get_related_notice_publication_repository", return_value=FakePublicationRepo()), patch(
            "backend.api.app._get_related_notice_cache_repository", return_value=FakeCacheRepo()
        ), patch("backend.api.app._get_artifact_repository", return_value=fake_artifact_repo), patch(
            "backend.api.app._project_source_runs", return_value=[]
        ):
            items, has_precomputed = _precomputed_related_notice_items(project, project_id=uuid4())

        self.assertFalse(has_precomputed)
        self.assertEqual(items, [])

    def test_precomputed_related_notice_items_falls_back_to_legacy_cache_when_publication_missing(self) -> None:
        project = {
            "project_name": "demo project",
            "project_search_name": "demo project",
            "_project_match_key": "demoproject",
            "issuer_name": "issuer",
            "source_json": {"run_ids": []},
        }
        test_case = self

        class FakePublicationRepo:
            def get_publication(self, *, organization_id):  # type: ignore[no-untyped-def]
                return None

        class FakeCacheRepo:
            def get_cache(self, *, project_key, snapshot_set_id=None):  # type: ignore[no-untyped-def]
                test_case.assertEqual(project_key, "demoproject")
                test_case.assertIsNone(snapshot_set_id)
                return {
                    "project_key": project_key,
                    "snapshot_set_id": "legacy",
                    "status": "success",
                    "source": "legacy_cache",
                    "algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
                    "payload_json": {
                        "project_key": project_key,
                        "snapshot_set_id": "legacy",
                        "source": "legacy_cache",
                        "algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
                        "items": [
                            {
                                "id": "notice-legacy-1",
                                "project_name": "Demo Project",
                                "project_search_name": "Demo Project",
                                "issuer_name": "Demo Issuer",
                                "announce_date": "20250328",
                                "bid_no": "R25BK00000009",
                                "bid_ord": "000",
                                "g2b_verified": "Y",
                                "notice_url": "",
                                "notice_detail_url": "",
                                "match_score": 144,
                                "match_reason": "legacy-cache",
                            }
                        ],
                    },
                }

            def upsert_cache(self, row):
                return row

        with patch("backend.api.app._get_related_notice_publication_repository", return_value=FakePublicationRepo()), patch(
            "backend.api.app._get_related_notice_cache_repository", return_value=FakeCacheRepo()
        ):
            items, has_precomputed = _precomputed_related_notice_items(project, project_id=uuid4())

        self.assertTrue(has_precomputed)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].bid_no, "R25BK00000009")

    def test_old_algorithm_payload_entry_is_not_treated_as_precomputed(self) -> None:
        entry = {
            "project_key": "abc",
            "source": "live",
            "algorithm_version": 2,
            "items": [{"id": "1"}],
        }

        self.assertFalse(_is_related_notice_payload_entry_precomputed(entry))
        self.assertFalse(_related_notice_payload_has_project({"projects": [entry]}, "abc"))

    def test_build_related_notice_primary_scopes_prioritizes_construction_for_construction_project(self) -> None:
        project = {
            "project_name": "익산시 발달장애인 평생교육센터 건립공사 설계공모",
            "project_search_name": "익산시 발달장애인 평생교육센터 건립공사",
            "latest_notice_title": "익산시 발달장애인 평생교육센터 건립공사 설계공모",
        }

        scopes = _build_related_notice_primary_scopes(project)

        self.assertEqual(scopes[0], "construction")
        self.assertEqual(set(scopes), {"construction", "service", "goods"})

    def test_build_related_notice_primary_scopes_prioritizes_service_for_service_project(self) -> None:
        project = {
            "project_name": "다목적 드론 활용센터 건립사업 기본 및 실시설계용역 설계공모",
            "project_search_name": "다목적 드론 활용센터 건립사업",
            "latest_notice_title": "다목적 드론 활용센터 건립사업 기본 및 실시설계용역 설계공모",
        }

        scopes = _build_related_notice_primary_scopes(project)

        self.assertEqual(scopes[0], "service")
        self.assertEqual(set(scopes), {"construction", "service", "goods"})

    def test_build_related_notice_primary_queries_prefers_stem_for_construction(self) -> None:
        project = {
            "project_name": "익산시 발달장애인 평생교육센터 건립공사 설계공모",
            "project_search_name": "익산시 발달장애인 평생교육센터 건립공사",
            "latest_notice_title": "익산시 발달장애인 평생교육센터 건립공사 설계공모",
        }

        queries = _build_related_notice_primary_queries(project, "construction")

        self.assertGreaterEqual(len(queries), 2)
        self.assertEqual(queries[0], "익산시 발달장애인 평생교육센터 건립")
        self.assertIn("익산시 발달장애인 평생교육센터", queries)

    def test_build_related_notice_primary_queries_keeps_non_gaching_variant_for_service(self) -> None:
        project = {
            "project_name": "(가칭)전남온라인학교 구축공사 설계 공모",
            "project_search_name": "가칭 전남온라인학교 구축공사",
            "latest_notice_title": "(가칭)전남온라인학교 구축공사 설계 공모",
        }

        queries = _build_related_notice_primary_queries(project, "service")

        self.assertGreaterEqual(len(queries), 3)
        self.assertEqual(queries[0], "전남온라인학교 구축공사")
        self.assertIn("전남온라인학교 구축공사", queries)
        self.assertTrue(any("가칭" in query for query in queries))

    def test_dedupe_related_notice_payload_items_collapses_same_title_issuer_date(self) -> None:
        items = [
            {
                "id": "a",
                "project_name": "정읍 연지유치원 식생활관 및 교실 증축 설계 공모",
                "project_search_name": "정읍 연지유치원 식생활관 교실 증축",
                "issuer_name": "전라북도교육청 전라북도정읍교육지원청",
                "announce_date": "20240116",
                "bid_no": "20240114798",
                "bid_ord": "000",
                "match_score": 144,
                "notice_detail_url": "https://example.com/a",
            },
            {
                "id": "b",
                "project_name": "정읍 연지유치원 식생활관 및 교실 증축 설계 공모",
                "project_search_name": "정읍 연지유치원 식생활관 교실 증축",
                "issuer_name": "전라북도교육청 전라북도정읍교육지원청",
                "announce_date": "20240116",
                "bid_no": "20240114377",
                "bid_ord": "000",
                "match_score": 138,
                "notice_detail_url": "",
            },
        ]

        deduped = _dedupe_related_notice_payload_items(items)

        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0]["bid_no"], "20240114798")

    def test_parse_iso_datetime_handles_z_suffix(self) -> None:
        parsed = _parse_iso_datetime("2026-03-14T12:00:00Z")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.tzinfo, timezone.utc)

    def test_related_notice_precompute_stale_detects_old_pending_state(self) -> None:
        now = datetime.now(timezone.utc)
        stale_row = {"updated_at": (now - timedelta(minutes=10)).isoformat()}
        fresh_row = {"updated_at": (now - timedelta(seconds=30)).isoformat()}

        self.assertTrue(_is_related_notice_precompute_stale(stale_row, "queued"))
        self.assertFalse(_is_related_notice_precompute_stale(fresh_row, "running"))
        self.assertFalse(_is_related_notice_precompute_stale(stale_row, "success"))

    def test_related_notice_response_returns_pending_while_precompute_pending(self) -> None:
        project = {
            "project_name": "남원시 노인복지회관 건립사업 설계공모",
            "project_search_name": "남원시 노인복지회관 건립사업",
            "_project_match_key": "남원시노인복지회관건립사업",
            "source_json": {"run_ids": ["00000000-0000-0000-0000-000000000001"]},
        }
        run_row = {
            "id": "00000000-0000-0000-0000-000000000001",
            "status": "success",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "summary_json": {
                "output": {
                    "related_notice_precompute_status": "running",
                    "related_notice_precompute_error": "",
                    "related_notice_project_statuses": {
                        "?⑥썝?쒕끂?몃났吏?뚭?嫄대┰?ъ뾽": {
                            "status": "running",
                            "error": "",
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        }
                    },
                }
            },
        }
        seed_items = [
            {
                "id": "a",
                "project_name": "남원시 노인복지회관 건립사업 설계공모",
                "project_search_name": "남원시 노인복지회관 건립사업",
                "issuer_name": "전북특별자치도 남원시",
                "announce_date": "20240115",
                "bid_no": "20240115",
                "bid_ord": "000",
                "g2b_verified": "Y",
                "notice_url": "",
                "notice_detail_url": "",
                "match_score": 166,
                "match_reason": "seed",
            }
        ]

        with patch("backend.api.app._project_source_runs", return_value=[run_row]), patch(
            "backend.api.app._seed_related_notice_items",
            side_effect=AssertionError("seed fallback should not run on request path"),
        ):
            response = _related_notice_response_without_live(project, uuid4())

        self.assertEqual(response.status, "pending")
        self.assertEqual(response.source, "precompute")
        self.assertEqual(len(response.items), 0)

    def test_related_notice_response_queues_precompute_when_missing(self) -> None:
        project = {
            "project_name": "정읍 연지유치원 식생활관 및 교실 증축 설계 공모",
            "project_search_name": "정읍 연지유치원 식생활관 교실 증축",
            "_project_match_key": "정읍연지유치원식생활관교실증축",
            "source_json": {"run_ids": ["00000000-0000-0000-0000-000000000002"]},
        }
        run_row = {
            "id": "00000000-0000-0000-0000-000000000002",
            "status": "success",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "summary_json": {"output": {}},
        }
        seed_items = [
            {
                "id": "b",
                "project_name": "정읍 연지유치원 식생활관 및 교실 증축 설계 공모",
                "project_search_name": "정읍 연지유치원 식생활관 교실 증축",
                "issuer_name": "전라북도교육청 전라북도정읍교육지원청",
                "announce_date": "20240116",
                "bid_no": "20240114798",
                "bid_ord": "000",
                "g2b_verified": "Y",
                "notice_url": "",
                "notice_detail_url": "",
                "match_score": 144,
                "match_reason": "seed",
            }
        ]

        fake_repo = type(
            "FakeRepo",
            (),
            {
                "__init__": lambda self: setattr(self, "updated", None),
                "update_run": lambda self, run_id, fields: setattr(self, "updated", (run_id, fields)),
            },
        )()

        with patch("backend.api.app._project_source_runs", return_value=[run_row]), patch(
            "backend.api.app._seed_related_notice_items",
            side_effect=AssertionError("seed fallback should not run on request path"),
        ), patch("backend.api.app._get_run_repository", return_value=fake_repo), patch(
            "backend.api.app._load_related_notice_precompute_helper",
            return_value=(lambda run_id, project_key=None: True),
        ):
            response = _related_notice_response_without_live(project, uuid4())

        self.assertEqual(response.status, "pending")
        self.assertEqual(response.source, "precompute")
        self.assertEqual(len(response.items), 0)
        self.assertIsNotNone(fake_repo.updated)
        _run_id, fields = fake_repo.updated
        statuses = dict(fields["summary_json"]["output"]["related_notice_project_statuses"])
        self.assertEqual(len(statuses), 1)
        self.assertEqual(next(iter(statuses.values()))["status"], "queued")

    def test_related_notice_response_ignores_missing_cache_table_when_queueing(self) -> None:
        project = {
            "project_name": "demo project",
            "project_search_name": "demo project",
            "_project_match_key": "demoproject",
            "source_json": {"run_ids": ["00000000-0000-0000-0000-000000000002"]},
        }
        run_row = {
            "id": "00000000-0000-0000-0000-000000000002",
            "status": "success",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "summary_json": {"output": {}},
        }
        seed_items = [
            {
                "id": "b",
                "project_name": "demo project",
                "project_search_name": "demo project",
                "issuer_name": "issuer",
                "announce_date": "20240116",
                "bid_no": "20240114798",
                "bid_ord": "000",
                "g2b_verified": "Y",
                "notice_url": "",
                "notice_detail_url": "",
                "match_score": 144,
                "match_reason": "seed",
            }
        ]

        class MissingTableCacheRepo:
            def get_cache(self, *, project_key):
                raise RelatedNoticeCacheRepositoryError(
                    "Could not find the table 'public.project_related_notice_cache' in the schema cache"
                )

            def upsert_cache(self, row):
                raise RelatedNoticeCacheRepositoryError(
                    "Could not find the table 'public.project_related_notice_cache' in the schema cache"
                )

        fake_repo = type(
            "FakeRepo",
            (),
            {
                "__init__": lambda self: setattr(self, "updated", None),
                "update_run": lambda self, run_id, fields: setattr(self, "updated", (run_id, fields)),
            },
        )()

        with patch("backend.api.app._get_related_notice_cache_repository", return_value=MissingTableCacheRepo()), patch(
            "backend.api.app._project_source_runs", return_value=[run_row]
        ), patch(
            "backend.api.app._seed_related_notice_items",
            side_effect=AssertionError("seed fallback should not run on request path"),
        ), patch(
            "backend.api.app._get_run_repository", return_value=fake_repo
        ), patch(
            "backend.api.app._load_related_notice_precompute_helper",
            return_value=(lambda run_id, project_key=None: True),
        ):
            response = _related_notice_response_without_live(project, uuid4())

        self.assertEqual(response.status, "pending")
        self.assertEqual(response.source, "precompute")
        self.assertEqual(len(response.items), 0)

    def test_queue_related_notice_precompute_blocks_duplicate_run_project_key(self) -> None:
        class FakeThread:
            instances: list["FakeThread"] = []

            def __init__(self, *, target, daemon) -> None:
                self.target = target
                self.daemon = daemon
                self.started = False
                FakeThread.instances.append(self)

            def start(self) -> None:
                self.started = True

        run_id = uuid4()

        with patch.object(run_execution, "safely_precompute_related_notices_for_run", return_value=None), patch.object(
            run_execution.threading, "Thread", FakeThread
        ):
            self.assertTrue(queue_related_notice_precompute_for_run(run_id, project_key="abc"))
            self.assertFalse(queue_related_notice_precompute_for_run(run_id, project_key="abc"))
            self.assertEqual(len(FakeThread.instances), 1)
            FakeThread.instances[0].target()
            self.assertTrue(queue_related_notice_precompute_for_run(run_id, project_key="abc"))
            self.assertEqual(len(FakeThread.instances), 2)

    def test_queue_related_notice_precompute_allows_stale_active_entry(self) -> None:
        class FakeThread:
            instances: list["FakeThread"] = []

            def __init__(self, *, target, daemon) -> None:
                self.target = target
                self.daemon = daemon
                self.started = False
                FakeThread.instances.append(self)

            def start(self) -> None:
                self.started = True

        run_id = uuid4()
        dedup_key = f"{run_id}:abc"
        with run_execution._PRECOMPUTE_ACTIVE_LOCK:
            run_execution._PRECOMPUTE_ACTIVE[dedup_key] = (
                time.monotonic() - RELATED_NOTICE_PRECOMPUTE_ACTIVE_STALE_SEC - 1,
                "old-token",
            )

        with patch.object(run_execution, "safely_precompute_related_notices_for_run", return_value=None), patch.object(
            run_execution.threading, "Thread", FakeThread
        ):
            self.assertTrue(queue_related_notice_precompute_for_run(run_id, project_key="abc"))
            self.assertEqual(len(FakeThread.instances), 1)
            with run_execution._PRECOMPUTE_ACTIVE_LOCK:
                self.assertIn(dedup_key, run_execution._PRECOMPUTE_ACTIVE)
                self.assertNotEqual(run_execution._PRECOMPUTE_ACTIVE[dedup_key][1], "old-token")

    def test_annotate_tracker_entries_with_project_refs_assigns_fallback_project_id(self) -> None:
        entry = {
            "id": str(uuid4()),
            "project_name": "정읍제일고 학교복합문화센터 건립 설계공모",
            "source_project_name_norm": "정읍제일고-학교복합문화센터-건립-설계공모",
            "source_run_id": "",
            "source_tracker_run_id": "",
            "notice_date": "20250318",
            "demand_org_name": "전북특별자치도교육청 정읍교육지원청",
        }

        with patch("backend.api.app._build_project_aggregates", return_value={}):
            rows = _annotate_tracker_entries_with_project_refs([entry])

        self.assertEqual(len(rows), 1)
        self.assertIsNotNone(rows[0]["project_id"])
        self.assertEqual(rows[0]["project_search_name"], "정읍제일고 학교복합문화센터 건립")

    def test_get_project_aggregate_falls_back_to_tracker_entries(self) -> None:
        entry = {
            "id": str(uuid4()),
            "project_name": "정읍제일고 학교복합문화센터 건립 설계공모",
            "source_project_name_norm": "정읍제일고-학교복합문화센터-건립-설계공모",
            "source_run_id": "",
            "source_tracker_run_id": "",
            "notice_date": "20250318",
            "demand_org_name": "전북특별자치도교육청 정읍교육지원청",
            "created_at": datetime(2026, 3, 20, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 3, 20, tzinfo=timezone.utc),
        }

        with patch("backend.api.app._build_project_aggregates", return_value={}):
            annotated = _annotate_tracker_entries_with_project_refs([entry])[0]
            with patch("backend.api.app._collect_all_tracker_entries", return_value=[entry]):
                aggregate = _get_project_aggregate(annotated["project_id"])

        self.assertEqual(aggregate["project_name"], "정읍제일고 학교복합문화센터 건립 설계공모")
        self.assertEqual(aggregate["project_search_name"], "정읍제일고 학교복합문화센터 건립")
        self.assertEqual(aggregate["issuer_name"], "전북특별자치도교육청 정읍교육지원청")

    def test_build_project_aggregates_reuses_process_cache_within_ttl(self) -> None:
        aggregate_payload = {
            "demo": {
                "id": uuid4(),
                "project_name": "demo project",
                "project_search_name": "demo project",
                "issuer_name": "demo issuer",
                "source_json": {"run_ids": []},
            }
        }

        with patch(
            "backend.api.app._build_project_aggregates_impl",
            side_effect=[aggregate_payload, AssertionError("project aggregates should reuse cache")],
        ):
            first = _build_project_aggregates()
            second = _build_project_aggregates()

        self.assertEqual(first, aggregate_payload)
        self.assertEqual(second, aggregate_payload)

    def test_queue_project_aggregates_cache_warm_dispatches_only_once(self) -> None:
        class FakeThread:
            instances = []

            def __init__(self, *, target=None, args=(), kwargs=None, daemon=None):  # type: ignore[no-untyped-def]
                self.target = target
                self.args = args
                self.kwargs = kwargs or {}
                self.daemon = daemon
                FakeThread.instances.append(self)

            def start(self):  # type: ignore[no-untyped-def]
                return None

        with patch("backend.api.app.threading.Thread", FakeThread):
            _queue_project_aggregates_cache_warm()
            _queue_project_aggregates_cache_warm()

        self.assertEqual(len(FakeThread.instances), 1)

    def test_build_project_aggregates_cache_survives_short_idle_gap(self) -> None:
        aggregate_payload = {
            "demo": {
                "id": uuid4(),
                "project_name": "demo project",
                "project_search_name": "demo project",
                "issuer_name": "demo issuer",
                "source_json": {"run_ids": []},
            }
        }

        with patch(
            "backend.api.app._build_project_aggregates_impl",
            side_effect=[aggregate_payload, AssertionError("project aggregates should remain warm after short idle gap")],
        ), patch(
            "backend.api.app.time.monotonic",
            side_effect=[100.0, 100.0, 120.0],
        ):
            first = _build_project_aggregates()
            second = _build_project_aggregates()

        self.assertEqual(first, aggregate_payload)
        self.assertEqual(second, aggregate_payload)

    def test_list_related_notices_for_project_reuses_response_cache(self) -> None:
        project_id = uuid4()
        published_snapshot_set_id = "snapshot-live"
        project = {
            "project_name": "demo project",
            "project_search_name": "demo project",
            "_project_match_key": "demoproject",
            "issuer_name": "issuer",
            "source_json": {"run_ids": []},
        }
        item = RelatedNoticeItem(
            id="notice-1",
            project_name="demo project",
            project_search_name="demo project",
            issuer_name="issuer",
            announce_date="20250328",
            bid_no="R25BK00000009",
            bid_ord="000",
            g2b_verified="Y",
            notice_url="",
            notice_detail_url="",
            match_score=144,
            match_reason="cache",
        )

        with patch("backend.api.app._get_published_related_notice_snapshot_set_id", return_value=published_snapshot_set_id), patch(
            "backend.api.app._get_project_aggregate", return_value=project
        ), patch(
            "backend.api.app._precomputed_related_notice_items", return_value=([item], True)
        ) as precomputed_mock:
            response = _list_related_notices_for_project(project_id)

        self.assertEqual(response.status, "ready")
        self.assertEqual(response.source, "precomputed")
        self.assertEqual(len(response.items), 1)
        self.assertEqual(precomputed_mock.call_count, 1)

        with patch("backend.api.app._get_published_related_notice_snapshot_set_id", return_value=published_snapshot_set_id), patch(
            "backend.api.app._get_project_aggregate", side_effect=AssertionError("cache miss")
        ), patch(
            "backend.api.app._precomputed_related_notice_items", side_effect=AssertionError("cache miss")
        ):
            cached_response = _list_related_notices_for_project(project_id)

        self.assertEqual(cached_response.status, "ready")
        self.assertEqual(cached_response.source, "precomputed")
        self.assertEqual(len(cached_response.items), 1)

    def test_list_related_notices_for_project_uses_snapshot_project_fast_path(self) -> None:
        project_id = uuid4()
        published_snapshot_set_id = "snapshot-live"
        project = {
            "project_name": "demo project",
            "project_search_name": "demo project",
            "_project_match_key": "demoproject",
            "issuer_name": "issuer",
            "source_json": {"run_ids": []},
        }
        item = RelatedNoticeItem(
            id="notice-1",
            project_name="demo project",
            project_search_name="demo project",
            issuer_name="issuer",
            announce_date="20250328",
            bid_no="R25BK00000009",
            bid_ord="000",
            g2b_verified="Y",
            notice_url="",
            notice_detail_url="",
            match_score=144,
            match_reason="cache",
        )

        with patch("backend.api.app._get_published_related_notice_snapshot_set_id", return_value=published_snapshot_set_id), patch(
            "backend.api.app._get_snapshot_project_aggregate", return_value=project
        ) as snapshot_project_mock, patch(
            "backend.api.app._get_project_aggregate", side_effect=AssertionError("heavy project aggregate lookup should be skipped")
        ), patch(
            "backend.api.app._precomputed_related_notice_items", return_value=([item], True)
        ):
            response = _list_related_notices_for_project(project_id)

        self.assertEqual(response.status, "ready")
        self.assertEqual(response.source, "precomputed")
        self.assertEqual(len(response.items), 1)
        snapshot_project_mock.assert_called_once_with(project_id)

    def test_list_related_notices_for_project_can_bypass_response_cache_on_refresh(self) -> None:
        project_id = uuid4()
        project = {
            "project_name": "demo project",
            "project_search_name": "demo project",
            "_project_match_key": "demoproject",
            "issuer_name": "issuer",
            "source_json": {"run_ids": []},
        }
        item = RelatedNoticeItem(
            id="notice-1",
            project_name="demo project 실시설계 용역",
            project_search_name="demo project",
            issuer_name="issuer",
            announce_date="20260503",
            bid_no="R26BK00000001",
            bid_ord="000",
            g2b_verified="",
            notice_url="",
            notice_detail_url="",
            match_score=144,
            match_reason="cache",
        )

        with patch("backend.api.app._get_published_related_notice_snapshot_set_id", return_value="snapshot-live"), patch(
            "backend.api.app._get_related_notice_response_cache",
            side_effect=AssertionError("refresh should skip the in-process response cache"),
        ), patch(
            "backend.api.app._get_snapshot_project_aggregate", return_value=project
        ), patch(
            "backend.api.app._get_project_aggregate", side_effect=AssertionError("snapshot aggregate should be used")
        ), patch(
            "backend.api.app._precomputed_related_notice_items", return_value=([item], True)
        ):
            response = _list_related_notices_for_project(project_id, force_refresh=True)

        self.assertEqual(response.status, "ready")
        self.assertEqual(response.items[0].project_name, "demo project 실시설계 용역")

    def test_list_related_notices_for_project_does_not_queue_request_time_precompute(self) -> None:
        project_id = uuid4()
        published_snapshot_set_id = "snapshot-live"
        project = {
            "project_name": "demo project",
            "project_search_name": "demo project",
            "_project_match_key": "demoproject",
            "issuer_name": "issuer",
            "source_json": {"run_ids": []},
        }

        with patch("backend.api.app._get_published_related_notice_snapshot_set_id", return_value=published_snapshot_set_id), patch(
            "backend.api.app._get_project_aggregate", return_value=project
        ), patch(
            "backend.api.app._precomputed_related_notice_items", return_value=([], False)
        ), patch(
            "backend.api.app._related_notice_response_without_live",
            side_effect=AssertionError("request-time queueing path should not run"),
        ):
            response = _list_related_notices_for_project(project_id)

        self.assertEqual(response.status, "missing")
        self.assertEqual(response.source, "published_snapshot")
        self.assertEqual(response.message, "저장된 후속공고 정보가 없습니다.")
        self.assertEqual(response.items, [])

    def test_list_related_notices_for_project_reports_queued_refresh_state(self) -> None:
        project_id = uuid4()
        published_snapshot_set_id = "snapshot-live"
        project = {
            "project_name": "demo project",
            "project_search_name": "demo project",
            "_project_match_key": "demoprojectqueued",
            "issuer_name": "issuer",
            "source_json": {"run_ids": []},
        }
        get_related_notice_cache_repository().upsert_cache(
            {
                "project_key": project["_project_match_key"],
                "snapshot_set_id": published_snapshot_set_id,
                "project_name": project["project_name"],
                "project_search_name": project["project_search_name"],
                "issuer_name": project["issuer_name"],
                "status": "queued",
                "source": "refresh_request",
                "source_run_id": str(uuid4()),
                "algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
                "payload_json": {
                    "project_key": project["_project_match_key"],
                    "project_name": project["project_name"],
                    "project_search_name": project["project_search_name"],
                    "issuer_name": project["issuer_name"],
                    "refresh_status": "queued",
                    "data_status": "empty",
                    "items": [],
                },
            }
        )

        with patch("backend.api.app._get_published_related_notice_snapshot_set_id", return_value=published_snapshot_set_id), patch(
            "backend.api.app._get_project_aggregate", return_value=project
        ), patch(
            "backend.api.app._precomputed_related_notice_items", return_value=([], False)
        ), patch(
            "backend.api.app._related_notice_response_without_live",
            side_effect=AssertionError("request-time queueing path should not run"),
        ):
            response = _list_related_notices_for_project(project_id)

        self.assertEqual(response.status, "queued")
        self.assertEqual(response.source, "refresh_request")
        self.assertEqual(response.message, "후속공고 갱신 요청이 등록되었습니다.")
        self.assertEqual(response.items, [])

    def test_list_related_notices_for_project_quick_search_bypasses_queued_state(self) -> None:
        project_id = uuid4()
        published_snapshot_set_id = "snapshot-live"
        project = {
            "project_name": "demo project",
            "project_search_name": "demo project",
            "_project_match_key": "demoquickqueued",
            "issuer_name": "issuer",
            "source_json": {"run_ids": []},
        }
        get_related_notice_cache_repository().upsert_cache(
            {
                "project_key": project["_project_match_key"],
                "snapshot_set_id": published_snapshot_set_id,
                "project_name": project["project_name"],
                "project_search_name": project["project_search_name"],
                "issuer_name": project["issuer_name"],
                "status": "queued",
                "source": "refresh_request",
                "source_run_id": str(uuid4()),
                "algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
                "payload_json": {
                    "project_key": project["_project_match_key"],
                    "items": [],
                },
            }
        )
        quick_item = RelatedNoticeItem(
            id="quick-1",
            project_name="demo project 실시설계 용역",
            project_search_name="demo project",
            issuer_name="issuer",
            announce_date="20260503",
            bid_no="R26BK00000001",
            bid_ord="000",
            g2b_verified="",
            notice_url="",
            notice_detail_url="",
            match_score=88,
            match_reason="quick",
        )

        with patch("backend.api.app._get_published_related_notice_snapshot_set_id", return_value=published_snapshot_set_id), patch(
            "backend.api.app._get_snapshot_project_aggregate", return_value=project
        ), patch(
            "backend.api.app._get_project_aggregate", side_effect=AssertionError("snapshot aggregate should be used")
        ), patch(
            "backend.api.app._quick_related_notice_search", return_value=([quick_item], {"attempt_count": 1}), create=True
        ) as quick_mock:
            response = _list_related_notices_for_project(project_id, quick=True)

        self.assertEqual(response.status, "ready")
        self.assertEqual(response.source, "raw_search")
        self.assertEqual(response.items, [quick_item])
        quick_mock.assert_called_once()

    def test_quick_related_notice_search_returns_raw_nara_rows_without_scoring_filter(self) -> None:
        project = {
            "project_name": "가덕도신공항 건설사업 여객터미널 국제설계공모",
            "project_search_name": "가덕도신공항 건설사업",
            "_project_match_key": "gadeok",
            "issuer_name": "국토교통부",
            "source_json": {"run_ids": []},
            "first_notice_date": "20240101",
            "latest_notice_date": "20240101",
        }
        raw_row = {
            "bid_no": "R26BK00000077",
            "bid_ord": "000",
            "project_name": "가덕도신공항 건설사업 관련 단순 키워드 결과",
            "org_name": "국토교통부",
            "announce_date": "20260503",
            "g2b_verified": "Y",
            "bid_ntce_url": "https://example.test/list",
            "bid_ntce_dtl_url": "https://example.test/detail",
        }
        request_calls: list[dict[str, object]] = []

        class FakeResponse:
            status_code = 200
            text = ""

            def json(self):  # type: ignore[no-untyped-def]
                return {"response": {"header": {"resultCode": "00"}, "body": {"items": []}}}

        def fake_get(_url, *, params, timeout):  # type: ignore[no-untyped-def]
            request_calls.append({"params": dict(params), "timeout": timeout})
            return FakeResponse()

        with patch("backend.api.support.projects_related_notice_support.resolve_native_service_key", return_value="service-key"), patch(
            "backend.api.support.projects_related_notice_support.fetch_seed_rows_with_diagnostics",
            side_effect=AssertionError("quick raw search must not use monthly seed collection"),
        ), patch(
            "backend.api.support.projects_related_notice_support.requests",
            SimpleNamespace(get=fake_get),
            create=True,
        ), patch(
            "backend.api.support.projects_related_notice_support._native_api_header",
            return_value=("00", ""),
            create=True,
        ), patch(
            "backend.api.support.projects_related_notice_support._native_extract_items",
            return_value=([{"raw": "item"}], 1),
            create=True,
        ), patch(
            "backend.api.support.projects_related_notice_support._native_seed_row_from_item",
            return_value=raw_row,
            create=True,
        ), patch(
            "backend.api.support.projects_related_notice_support._score_related_notice_match",
            side_effect=AssertionError("raw quick search must not score/filter rows"),
        ), patch(
            "backend.api.app._project_source_runs", return_value=[]
        ), patch(
            "backend.api.app._collect_all_runs", return_value=[]
        ):
            items, debug = _support_quick_related_notice_search(project)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].project_name, raw_row["project_name"])
        self.assertEqual(items[0].match_reason, "raw_search:가덕도신공항 건설사업")
        self.assertEqual(debug["source"], "raw_nara_search")
        self.assertEqual(debug["date_ranges"][0]["start_date"], "20240101")
        self.assertEqual(debug["date_ranges"][0]["end_date"], "20250101")
        self.assertEqual(debug["date_ranges"][1]["start_date"], "20250102")
        self.assertEqual(debug["date_ranges"][1]["end_date"], datetime.now().strftime("%Y%m%d"))
        self.assertTrue(request_calls)
        distinct_windows = {
            (
                str(call["params"].get("inqryBgnDt")),
                str(call["params"].get("inqryEndDt")),
            )
            for call in request_calls
        }
        self.assertEqual(
            distinct_windows,
            {
                ("202401010000", "202501012359"),
                ("202501020000", f"{datetime.now().strftime('%Y%m%d')}2359"),
            },
        )
        self.assertTrue(all(call["timeout"] == 5 for call in request_calls))
        self.assertTrue(all(call["params"].get("bidNtceNm") == project["project_search_name"] for call in request_calls))

    def test_force_recompute_related_notices_for_project_queues_latest_source_run_and_clears_response_cache(self) -> None:
        project_id = uuid4()
        old_run_id = uuid4()
        latest_run_id = uuid4()
        project = {
            "project_name": "?????? ???? ????? ??????",
            "project_search_name": "?????? ???? ?????",
            "_project_match_key": "???????????????",
            "issuer_name": "issuer",
            "source_json": {"run_ids": [str(old_run_id), str(latest_run_id)]},
        }
        source_runs = [
            {"id": str(old_run_id), "status": "success", "updated_at": "2026-04-01T00:00:00+00:00"},
            {"id": str(latest_run_id), "status": "success", "updated_at": "2026-05-01T00:00:00+00:00"},
        ]
        cleared: list[UUID] = []
        worker_started: list[bool] = []
        worker_woken: list[bool] = []

        with patch("backend.api.app._get_snapshot_project_aggregate", return_value=None), patch(
            "backend.api.app._get_project_aggregate", return_value=project
        ), patch(
            "backend.api.app._project_source_runs", return_value=source_runs
        ), patch(
            "backend.api.app._get_published_related_notice_snapshot_set_id", return_value="snapshot-live"
        ), patch(
            "backend.api.app.ensure_related_notice_refresh_worker_started",
            side_effect=lambda **_kwargs: worker_started.append(True),
        ), patch(
            "backend.api.app.wake_related_notice_refresh_worker",
            side_effect=lambda: worker_woken.append(True),
        ), patch(
            "backend.api.app._clear_related_notice_response_cache", side_effect=lambda target=None: cleared.append(target)
        ):
            response = _force_recompute_related_notices_for_project(project_id)

        self.assertTrue(response.queued)
        self.assertEqual(response.status, "queued")
        self.assertEqual(response.message, "후속공고 갱신 요청이 등록되었습니다.")
        self.assertEqual(response.run_id, str(latest_run_id))
        self.assertEqual(response.project_key, "???????????????")
        cache_row = get_related_notice_cache_repository().get_cache(
            project_key=project["_project_match_key"],
            snapshot_set_id="snapshot-live",
        )
        self.assertEqual(cache_row["status"], "queued")
        self.assertEqual(cache_row["source_run_id"], str(latest_run_id))
        self.assertEqual(dict(cache_row["payload_json"])["refresh_status"], "queued")
        self.assertEqual(worker_started, [True])
        self.assertEqual(worker_woken, [True])
        self.assertEqual(cleared, [project_id])
        progress = get_related_notice_progress(project_key=project["_project_match_key"])
        self.assertEqual(progress["status"], "queued")
        self.assertEqual(progress["message"], "후속공고 갱신 요청이 등록되었습니다.")
        self.assertEqual(progress["run_id"], str(latest_run_id))
        self.assertEqual(progress["items"], [])

    def test_get_related_notice_progress_for_project_returns_partial_items(self) -> None:
        project_id = uuid4()
        project = {
            "project_name": "Demo library",
            "project_search_name": "Demo library",
            "_project_match_key": "demolibrary",
            "issuer_name": "issuer",
            "source_json": {"run_ids": []},
        }
        update_related_notice_progress(
            project_key="demolibrary",
            project_name="Demo library",
            project_search_name="Demo library",
            status="running",
            message="1 related notice found.",
            items=[
                {
                    "id": "notice-1",
                    "project_name": "Demo library detailed design",
                    "project_search_name": "Demo library",
                    "issuer_name": "issuer",
                    "announce_date": "20260501",
                    "bid_no": "R26BK00000001",
                    "bid_ord": "000",
                    "g2b_verified": "Y",
                    "notice_url": "",
                    "notice_detail_url": "",
                    "match_score": 140,
                    "match_reason": "progress",
                }
            ],
        )

        with patch("backend.api.app._get_snapshot_project_aggregate", return_value=project), patch(
            "backend.api.app._get_project_aggregate", side_effect=AssertionError("snapshot aggregate should be used")
        ):
            response = _get_related_notice_progress_for_project(project_id)

        self.assertEqual(response.status, "running")
        self.assertEqual(response.message, "1 related notice found.")
        self.assertEqual(response.item_count, 1)
        self.assertEqual(response.items[0].bid_no, "R26BK00000001")

    def test_live_related_notice_search_emits_partial_progress_after_collect_batch(self) -> None:
        project = {
            "project_name": "Demo library",
            "project_search_name": "Demo library",
            "_project_match_key": "demolibrary",
            "issuer_name": "Demo issuer",
        }
        rows = [
            {
                "project_name": "Demo library detailed design",
                "org_name": "Demo issuer",
                "announce_date": "20260501",
                "bid_no": "R26BK00000002",
                "bid_ord": "000",
                "bid_ntce_url": "",
                "bid_ntce_dtl_url": "",
                "_query_index": "0",
                "_query_value": "Demo library",
            }
        ]
        progress_calls: list[list[RelatedNoticeItem]] = []

        def fake_collect(_project: dict[str, object], **kwargs: object):  # type: ignore[no-untyped-def]
            progress_cb = kwargs.get("progress_cb")
            if progress_cb is not None:
                progress_cb(rows, {"deduped_row_count": 1})
            return rows, {"deduped_row_count": 1}

        with patch(
            "backend.api.support.projects_related_notice_support._collect_related_notice_rows_with_debug",
            side_effect=fake_collect,
        ), patch(
            "backend.api.support.projects_related_notice_support._score_related_notice_match",
            return_value=(100, "Demo library", "match"),
        ):
            items, _debug = _support_live_related_notice_search(project, progress_cb=lambda partial, _debug: progress_calls.append(partial))

        self.assertEqual(len(items), 1)
        self.assertEqual(len(progress_calls), 1)
        self.assertEqual(progress_calls[0][0].bid_no, "R26BK00000002")

    def test_live_related_notice_search_classifies_sales_relevance(self) -> None:
        project = {
            "project_name": "Demo library",
            "project_search_name": "Demo library",
            "_project_match_key": "demolibrary",
            "issuer_name": "Demo issuer",
        }
        rows = [
            {
                "project_name": "Demo library 실시설계 용역",
                "org_name": "Demo issuer",
                "announce_date": "20260501",
                "bid_no": "R26BK00000003",
                "bid_ord": "000",
                "bid_ntce_url": "",
                "bid_ntce_dtl_url": "",
                "_query_index": "0",
                "_query_value": "Demo library",
            },
            {
                "project_name": "Demo library 제안서 평가용역",
                "org_name": "Demo issuer",
                "announce_date": "20260502",
                "bid_no": "R26BK00000004",
                "bid_ord": "000",
                "bid_ntce_url": "",
                "bid_ntce_dtl_url": "",
                "_query_index": "0",
                "_query_value": "Demo library",
            },
        ]

        with patch(
            "backend.api.support.projects_related_notice_support._collect_related_notice_rows_with_debug",
            return_value=(rows, {"deduped_row_count": 2}),
        ), patch(
            "backend.api.support.projects_related_notice_support._score_related_notice_match",
            return_value=(100, "Demo library", "match"),
        ):
            items, _debug = _support_live_related_notice_search(project)

        by_bid_no = {item.bid_no: item for item in items}
        self.assertEqual(by_bid_no["R26BK00000003"].sales_relevance, "sales_relevant")
        self.assertEqual(by_bid_no["R26BK00000004"].notice_stage, "ADMIN_NOISE")
        self.assertEqual(by_bid_no["R26BK00000004"].sales_relevance, "excluded")

    def test_force_recompute_related_notices_for_project_uses_latest_success_source_run(self) -> None:
        project_id = uuid4()
        success_run_id = uuid4()
        failed_run_id = uuid4()
        project = {
            "project_name": "??? ??????? ???? ???? ???? ??",
            "project_search_name": "??? ??????? ????",
            "_project_match_key": "??????????????",
            "issuer_name": "issuer",
            "source_json": {"run_ids": [str(success_run_id), str(failed_run_id)]},
        }
        source_runs = [
            {"id": str(success_run_id), "status": "success", "updated_at": "2026-05-01T00:00:00+00:00"},
            {"id": str(failed_run_id), "status": "failed", "updated_at": "2026-05-03T00:00:00+00:00"},
        ]

        with patch("backend.api.app._get_snapshot_project_aggregate", return_value=project), patch(
            "backend.api.app._get_project_aggregate", side_effect=AssertionError("snapshot aggregate should be used")
        ), patch(
            "backend.api.app._project_source_runs", return_value=source_runs
        ), patch(
            "backend.api.app._get_published_related_notice_snapshot_set_id", return_value="snapshot-live"
        ), patch(
            "backend.api.app.ensure_related_notice_refresh_worker_started"
        ), patch(
            "backend.api.app.wake_related_notice_refresh_worker"
        ), patch(
            "backend.api.app._clear_related_notice_response_cache"
        ):
            response = _force_recompute_related_notices_for_project(project_id)

        self.assertEqual(response.run_id, str(success_run_id))
        cache_row = get_related_notice_cache_repository().get_cache(
            project_key=project["_project_match_key"],
            snapshot_set_id="snapshot-live",
        )
        self.assertEqual(cache_row["status"], "queued")
        self.assertEqual(cache_row["source_run_id"], str(success_run_id))

    def test_list_related_notices_for_project_pins_empty_snapshot_identity_during_request(self) -> None:
        project_id = uuid4()
        project = {
            "project_name": "demo project",
            "project_search_name": "demo project",
            "_project_match_key": "demoproject",
            "issuer_name": "issuer",
            "source_json": {"run_ids": []},
        }
        published_snapshot_calls = {"count": 0}

        def fake_get_published_snapshot_set_id() -> str:
            published_snapshot_calls["count"] += 1
            if published_snapshot_calls["count"] == 1:
                return ""
            raise AssertionError("request should not re-read the publication pointer after start")

        def fake_precomputed(
            _project: dict[str, object],
            *,
            published_snapshot_set_id: str | None | object,
            **kwargs: object,
        ) -> tuple[list[RelatedNoticeItem], bool]:
            self.assertEqual(published_snapshot_set_id, "")
            return [], False

        with patch("backend.api.app._get_published_related_notice_snapshot_set_id", side_effect=fake_get_published_snapshot_set_id), patch(
            "backend.api.app._get_project_aggregate", return_value=project
        ), patch(
            "backend.api.app._related_notice_read_model_backend._precomputed_related_notice_items",
            side_effect=fake_precomputed,
        ):
            response = _list_related_notices_for_project(project_id)

        self.assertEqual(response.status, "missing")
        self.assertEqual(response.source, "published_snapshot")
        self.assertEqual(published_snapshot_calls["count"], 1)

    def test_list_related_notices_for_project_does_not_reuse_stale_cache_after_snapshot_rollover(self) -> None:
        project_id = uuid4()
        old_snapshot_set_id = "snapshot-old"
        new_snapshot_set_id = "snapshot-new"
        project = {
            "project_name": "demo project",
            "project_search_name": "demo project",
            "_project_match_key": "demoproject",
            "issuer_name": "issuer",
            "source_json": {"run_ids": []},
        }
        old_item = RelatedNoticeItem(
            id="notice-old",
            project_name="demo project",
            project_search_name="demo project",
            issuer_name="issuer",
            announce_date="20250328",
            bid_no="R25BK00000001",
            bid_ord="000",
            g2b_verified="Y",
            notice_url="",
            notice_detail_url="",
            match_score=144,
            match_reason="cache",
        )
        new_item = RelatedNoticeItem(
            id="notice-new",
            project_name="demo project",
            project_search_name="demo project",
            issuer_name="issuer",
            announce_date="20250329",
            bid_no="R25BK00000002",
            bid_ord="000",
            g2b_verified="Y",
            notice_url="",
            notice_detail_url="",
            match_score=145,
            match_reason="cache",
        )
        snapshot_state = {"current": old_snapshot_set_id}
        precomputed_calls = {"count": 0}

        def fake_precomputed(*args, **kwargs):  # type: ignore[no-untyped-def]
            precomputed_calls["count"] += 1
            if precomputed_calls["count"] == 1:
                snapshot_state["current"] = new_snapshot_set_id
                return ([old_item], True)
            return ([new_item], True)

        with patch("backend.api.app._get_published_related_notice_snapshot_set_id", side_effect=lambda: snapshot_state["current"]), patch(
            "backend.api.app._get_project_aggregate", return_value=project
        ), patch("backend.api.app._precomputed_related_notice_items", side_effect=fake_precomputed):
            first_response = _list_related_notices_for_project(project_id)
            second_response = _list_related_notices_for_project(project_id)

        self.assertEqual(first_response.items[0].bid_no, "R25BK00000001")
        self.assertEqual(second_response.items[0].bid_no, "R25BK00000002")
        self.assertEqual(precomputed_calls["count"], 2)
        self.assertIsNotNone(_get_related_notice_response_cache(project_id, old_snapshot_set_id))
        self.assertIsNotNone(_get_related_notice_response_cache(project_id, new_snapshot_set_id))


if __name__ == "__main__":
    unittest.main()
