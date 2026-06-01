from __future__ import annotations

import unittest
from datetime import datetime
from datetime import timezone
from types import SimpleNamespace
from uuid import uuid4

from backend.repositories import RelatedNoticeCacheRepositoryError
from backend.services import run_execution
from backend.services.related_notice_read_model_backend import dedupe_related_notice_rows
from backend.services.related_notice_read_model_backend import filter_self_related_notice_payload_items
from backend.services.related_notice_read_model_backend import is_related_notice_payload_entry_precomputed
from backend.services.related_notice_read_model_backend import precomputed_related_notice_items
from backend.services.related_notice_read_model_backend import project_source_notice_keys
from backend.services.related_notice_read_model_backend import project_source_runs
from backend.services.related_notice_read_model_backend import select_tracker_entry_source_notice_row


class RelatedNoticeReadModelBackendTests(unittest.TestCase):
    def test_dedupe_related_notice_rows_collapses_same_bid_identity(self) -> None:
        rows = [
            {"bid_no": "R26BK0001", "bid_ord": "000", "project_name": "Demo Project"},
            {"bid_no": "R26BK0001", "bid_ord": "000", "project_name": "Demo Project"},
            {"bid_no": "R26BK0002", "bid_ord": "000", "project_name": "Other Project"},
        ]

        deduped = dedupe_related_notice_rows(rows, norm_text_fn=lambda value: str(value).lower())

        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0]["bid_no"], "R26BK0001")
        self.assertEqual(deduped[1]["bid_no"], "R26BK0002")

    def test_project_source_runs_dedupes_invalid_ids_and_sorts_recent_first(self) -> None:
        run_id_old = uuid4()
        run_id_new = uuid4()
        run_rows = {
            str(run_id_old): {"id": str(run_id_old), "updated_at": "2026-03-29T08:00:00+00:00"},
            str(run_id_new): {"id": str(run_id_new), "updated_at": "2026-03-29T09:00:00+00:00"},
        }

        class FakeRunRepository:
            def get_run(self, run_id):  # type: ignore[no-untyped-def]
                return run_rows.get(str(run_id))

        rows = project_source_runs(
            {
                "source_json": {
                    "run_ids": [str(run_id_old), "not-a-uuid", str(run_id_new), str(run_id_old)],
                }
            },
            get_run_repository_fn=lambda: FakeRunRepository(),
            repository_error_fn=lambda message: (_ for _ in ()).throw(RuntimeError(message)),
        )

        self.assertEqual([str(row["id"]) for row in rows], [str(run_id_new), str(run_id_old)])

    def test_project_source_notice_keys_uses_seed_csv_for_matching_project_only(self) -> None:
        run_id = uuid4()

        class FakeArtifactRepository:
            def list_artifacts(self, *, run_id):  # type: ignore[no-untyped-def]
                return [
                    {"artifact_type": "seed_csv", "storage_path": "output/seed.csv"},
                    {"artifact_type": "related_notices_json", "storage_path": "output/related.json"},
                ]

        keys = project_source_notice_keys(
            {
                "_project_match_key": "demoproject",
                "source_json": {"run_ids": [str(run_id)]},
            },
            get_artifact_repository_fn=lambda: FakeArtifactRepository(),
            project_source_runs_fn=lambda project: [{"id": str(run_id)}],
            load_seed_rows_from_artifact_path_fn=lambda path: [
                {"bid_no": "R26BK0001", "bid_ord": "000", "project_name": "Demo Project"},
                {"bid_no": "R26BK0002", "bid_ord": "000", "project_name": "Other Project"},
            ],
            project_search_name_fn=lambda project_name: str(project_name).strip(),
            project_match_key_fn=lambda value: str(value).replace(" ", "").lower(),
            repository_error_fn=lambda message: (_ for _ in ()).throw(RuntimeError(message)),
        )

        self.assertEqual(keys, {("R26BK0001", "000")})

    def test_filter_self_related_notice_payload_items_removes_source_notices(self) -> None:
        filtered = filter_self_related_notice_payload_items(
            {"project_name": "demo"},
            [
                {"bid_no": "R26BK0001", "bid_ord": "000"},
                {"bid_no": "R26BK0002", "bid_ord": "000"},
            ],
            project_source_notice_keys_fn=lambda project: {("R26BK0001", "000")},
        )

        self.assertEqual(filtered, [{"bid_no": "R26BK0002", "bid_ord": "000"}])

    def test_is_related_notice_payload_entry_precomputed_requires_current_algorithm_and_items(self) -> None:
        self.assertTrue(
            is_related_notice_payload_entry_precomputed(
                {
                    "algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
                    "items": [{"id": "1"}],
                },
                related_notice_algorithm_version=run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
            )
        )
        self.assertFalse(
            is_related_notice_payload_entry_precomputed(
                {"algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION - 1, "items": [{"id": "1"}]},
                related_notice_algorithm_version=run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
            )
        )

    def test_precomputed_related_notice_items_prefers_cache_and_filters_self_items(self) -> None:
        project = {
            "_project_match_key": "demoproject",
            "project_name": "Demo Project",
            "project_search_name": "Demo Project",
            "issuer_name": "Demo Issuer",
        }
        published_snapshot_set_id = "snapshot-live"
        test_case = self

        class FakeCacheRepository:
            def get_cache(self, *, project_key, snapshot_set_id=None):  # type: ignore[no-untyped-def]
                test_case.assertEqual(project_key, "demoproject")
                test_case.assertEqual(snapshot_set_id, published_snapshot_set_id)
                return {
                    "project_key": project_key,
                    "snapshot_set_id": snapshot_set_id,
                    "source": "live",
                    "algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
                    "payload_json": {
                        "project_key": project_key,
                        "snapshot_set_id": snapshot_set_id,
                        "algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
                        "items": [
                            {
                                "id": "source",
                                "project_name": "Demo Project",
                                "project_search_name": "Demo Project",
                                "issuer_name": "Demo Issuer",
                                "announce_date": "20260329",
                                "bid_no": "R26BK0001",
                                "bid_ord": "000",
                            },
                            {
                                "id": "other",
                                "project_name": "Demo Project 2",
                                "project_search_name": "Demo Project 2",
                                "issuer_name": "Demo Issuer",
                                "announce_date": "20260329",
                                "bid_no": "R26BK0002",
                                "bid_ord": "000",
                            },
                        ],
                    },
                }

            def upsert_cache(self, row):  # type: ignore[no-untyped-def]
                return row

        items, has_precomputed = precomputed_related_notice_items(
            project,
            project_id=uuid4(),
            trace_id=None,
            published_snapshot_set_id=published_snapshot_set_id,
            get_related_notice_cache_repository_fn=lambda: FakeCacheRepository(),
            is_missing_related_notice_cache_table_error_fn=lambda message: False,
            repository_error_fn=lambda message: (_ for _ in ()).throw(RuntimeError(message)),
            filter_self_related_notice_payload_items_fn=lambda project, items: [
                dict(item) for item in items if str(item.get("bid_no")) != "R26BK0001"
            ],
            dedupe_related_notice_payload_items_fn=lambda items: list(items),
            project_source_runs_fn=lambda project: [],
            get_artifact_repository_fn=lambda: None,
            load_json_artifact_payload_fn=lambda path: {},
            append_related_notice_trace_fn=lambda **kwargs: None,
            is_related_notice_payload_entry_precomputed_fn=is_related_notice_payload_entry_precomputed,
        )

        self.assertTrue(has_precomputed)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].bid_no, "R26BK0002")

    def test_precomputed_related_notice_items_reads_only_currently_published_snapshot_set(self) -> None:
        project = {
            "_project_match_key": "demoproject",
            "project_name": "Demo Project",
            "project_search_name": "Demo Project",
            "issuer_name": "Demo Issuer",
        }
        published_snapshot_set_id = "snapshot-2026-04-09"
        test_case = self

        class FakeCacheRepository:
            def get_cache(self, *, project_key, snapshot_set_id=None):  # type: ignore[no-untyped-def]
                test_case.assertEqual(project_key, "demoproject")
                test_case.assertEqual(snapshot_set_id, published_snapshot_set_id)
                return {
                    "project_key": project_key,
                    "snapshot_set_id": snapshot_set_id,
                    "source": "published_snapshot",
                    "algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
                    "payload_json": {
                        "project_key": project_key,
                        "snapshot_set_id": snapshot_set_id,
                        "source": "published_snapshot",
                        "algorithm_version": run_execution.RELATED_NOTICE_ALGORITHM_VERSION,
                        "items": [
                            {
                                "id": "published",
                                "project_name": "Demo Project",
                                "project_search_name": "Demo Project",
                                "issuer_name": "Demo Issuer",
                                "announce_date": "20260329",
                                "bid_no": "R26BK0004",
                                "bid_ord": "000",
                            }
                        ],
                    },
                }

        items, has_precomputed = precomputed_related_notice_items(
            project,
            project_id=uuid4(),
            trace_id=None,
            published_snapshot_set_id=published_snapshot_set_id,
            get_related_notice_cache_repository_fn=lambda: FakeCacheRepository(),
            is_missing_related_notice_cache_table_error_fn=lambda message: False,
            repository_error_fn=lambda message: (_ for _ in ()).throw(RuntimeError(message)),
            filter_self_related_notice_payload_items_fn=lambda project, items: list(items),
            dedupe_related_notice_payload_items_fn=lambda items: list(items),
            project_source_runs_fn=lambda project: (_ for _ in ()).throw(AssertionError("run lookup should not happen")),
            get_artifact_repository_fn=lambda: (_ for _ in ()).throw(AssertionError("artifact lookup should not happen")),
            load_json_artifact_payload_fn=lambda path: (_ for _ in ()).throw(AssertionError("artifact load should not happen")),
            append_related_notice_trace_fn=lambda **kwargs: None,
            is_related_notice_payload_entry_precomputed_fn=is_related_notice_payload_entry_precomputed,
        )

        self.assertTrue(has_precomputed)
        self.assertEqual([item.bid_no for item in items], ["R26BK0004"])

    def test_precomputed_related_notice_items_returns_empty_when_published_snapshot_cache_missing(self) -> None:
        project = {
            "_project_match_key": "demoproject",
            "project_name": "Demo Project",
            "project_search_name": "Demo Project",
            "issuer_name": "Demo Issuer",
        }
        test_case = self

        class MissingSnapshotCacheRepository:
            def get_cache(self, *, project_key, snapshot_set_id=None):  # type: ignore[no-untyped-def]
                test_case.assertEqual(project_key, "demoproject")
                test_case.assertEqual(snapshot_set_id, "snapshot-live")
                return None

        items, has_precomputed = precomputed_related_notice_items(
            project,
            project_id=uuid4(),
            trace_id=None,
            published_snapshot_set_id="snapshot-live",
            get_related_notice_cache_repository_fn=lambda: MissingSnapshotCacheRepository(),
            is_missing_related_notice_cache_table_error_fn=lambda message: False,
            repository_error_fn=lambda message: (_ for _ in ()).throw(RuntimeError(message)),
            filter_self_related_notice_payload_items_fn=lambda project, items: list(items),
            dedupe_related_notice_payload_items_fn=lambda items: list(items),
            project_source_runs_fn=lambda project: (_ for _ in ()).throw(AssertionError("run lookup should not happen")),
            get_artifact_repository_fn=lambda: (_ for _ in ()).throw(AssertionError("artifact lookup should not happen")),
            load_json_artifact_payload_fn=lambda path: (_ for _ in ()).throw(AssertionError("artifact load should not happen")),
            append_related_notice_trace_fn=lambda **kwargs: None,
            is_related_notice_payload_entry_precomputed_fn=is_related_notice_payload_entry_precomputed,
        )

        self.assertFalse(has_precomputed)
        self.assertEqual(items, [])

    def test_precomputed_related_notice_items_can_skip_artifact_scan_on_request_path(self) -> None:
        run_id = uuid4()
        project = {
            "_project_match_key": "demoproject",
            "project_name": "Demo Project",
            "project_search_name": "Demo Project",
            "issuer_name": "Demo Issuer",
            "source_json": {"run_ids": [str(run_id)]},
        }

        class EmptyCacheRepository:
            def get_cache(self, *, project_key):  # type: ignore[no-untyped-def]
                return None

            def upsert_cache(self, row):  # type: ignore[no-untyped-def]
                return row

        class FakeArtifactRepository:
            def list_artifacts(self, *, run_id):  # type: ignore[no-untyped-def]
                raise AssertionError("artifact scan should not run on request path")

        items, has_precomputed = precomputed_related_notice_items(
            project,
            project_id=uuid4(),
            trace_id=None,
            get_related_notice_cache_repository_fn=lambda: EmptyCacheRepository(),
            is_missing_related_notice_cache_table_error_fn=lambda message: False,
            repository_error_fn=lambda message: (_ for _ in ()).throw(RuntimeError(message)),
            filter_self_related_notice_payload_items_fn=lambda project, items: list(items),
            dedupe_related_notice_payload_items_fn=lambda items: list(items),
            project_source_runs_fn=lambda project: [{"id": str(run_id), "updated_at": datetime.now(timezone.utc).isoformat()}],
            get_artifact_repository_fn=lambda: FakeArtifactRepository(),
            load_json_artifact_payload_fn=lambda path: {},
            append_related_notice_trace_fn=lambda **kwargs: None,
            is_related_notice_payload_entry_precomputed_fn=is_related_notice_payload_entry_precomputed,
            allow_artifact_scan=False,
        )

        self.assertFalse(has_precomputed)
        self.assertEqual(items, [])

    def test_precomputed_related_notice_items_can_skip_artifact_scan_on_request_path(self) -> None:
        run_id = uuid4()
        project = {
            "_project_match_key": "demoproject",
            "project_name": "Demo Project",
            "project_search_name": "Demo Project",
            "issuer_name": "Demo Issuer",
            "source_json": {"run_ids": [str(run_id)]},
        }

        class EmptyCacheRepository:
            def get_cache(self, *, project_key):  # type: ignore[no-untyped-def]
                return None

            def upsert_cache(self, row):  # type: ignore[no-untyped-def]
                return row

        class FakeArtifactRepository:
            def list_artifacts(self, *, run_id):  # type: ignore[no-untyped-def]
                raise AssertionError("artifact scan should not run on request path")

        items, has_precomputed = precomputed_related_notice_items(
            project,
            project_id=uuid4(),
            trace_id=None,
            get_related_notice_cache_repository_fn=lambda: EmptyCacheRepository(),
            is_missing_related_notice_cache_table_error_fn=lambda message: False,
            repository_error_fn=lambda message: (_ for _ in ()).throw(RuntimeError(message)),
            filter_self_related_notice_payload_items_fn=lambda project, items: list(items),
            dedupe_related_notice_payload_items_fn=lambda items: list(items),
            project_source_runs_fn=lambda project: [{"id": str(run_id), "updated_at": datetime.now(timezone.utc).isoformat()}],
            get_artifact_repository_fn=lambda: FakeArtifactRepository(),
            load_json_artifact_payload_fn=lambda path: {},
            append_related_notice_trace_fn=lambda **kwargs: None,
            is_related_notice_payload_entry_precomputed_fn=is_related_notice_payload_entry_precomputed,
            allow_artifact_scan=False,
        )

        self.assertFalse(has_precomputed)
        self.assertEqual(items, [])

    def test_select_tracker_entry_source_notice_row_prefers_artifact_row_then_falls_back(self) -> None:
        source_run_id = uuid4()

        class FakeArtifactRepository:
            def list_artifacts(self, *, run_id):  # type: ignore[no-untyped-def]
                return [{"artifact_type": "seed_csv", "storage_path": "output/seed.csv"}]

        row = select_tracker_entry_source_notice_row(
            {"source_run_id": str(source_run_id), "source_bid_no": "R26BK0001", "source_bid_ord": "000"},
            coerce_uuid_or_none_fn=lambda value: source_run_id,
            derive_tracker_entry_bid_identity_fn=lambda entry: ("R26BK0001", "000"),
            get_artifact_repository_fn=lambda: FakeArtifactRepository(),
            load_seed_rows_from_artifact_path_fn=lambda path: [
                {"bid_no": "R26BK0001", "bid_ord": "001"},
                {"bid_no": "R26BK0001", "bid_ord": "000", "spec_doc_url": "https://example.com/seed.hwp"},
            ],
            normalize_tracker_bid_ord_fn=lambda value: str(value).zfill(3),
            load_notice_seed_row_by_bid_fn=lambda **kwargs: {"bid_no": "fallback"},
            repository_error_fn=lambda message: (_ for _ in ()).throw(RuntimeError(message)),
        )

        self.assertEqual(row["spec_doc_url"], "https://example.com/seed.hwp")


if __name__ == "__main__":
    unittest.main()
