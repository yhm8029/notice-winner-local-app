from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from backend.phase1_defaults import build_phase1_run_row
from backend.phase1_defaults import PROJECT_TRACKER_RUN_TYPE
from backend.phase1_defaults import TRACKER_EXPORT_RUN_TYPE
from backend.repositories.in_memory_logs import InMemoryRunLogRepository
from backend.repositories.in_memory_runs import InMemoryRunRepository
from backend.repositories.logs import RunLogRepositoryError
from backend.services import run_execution


class _RecordingArtifactRepository:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = []

    def create_artifact(self, row):  # type: ignore[no-untyped-def]
        stored = dict(row)
        self.rows.append(stored)
        return stored

    def list_artifacts(self, *, run_id):  # type: ignore[no-untyped-def]
        del run_id
        return [dict(row) for row in self.rows]


class _FailingRunLogRepository:
    def create_log(self, row):  # type: ignore[no-untyped-def]
        del row
        raise RunLogRepositoryError("Supabase request failed: Read timed out")

    def list_logs(self, *, run_id, cursor, limit):  # type: ignore[no-untyped-def]
        del run_id, cursor, limit
        return [], None


class RunExecutionResilienceTests(unittest.TestCase):
    def test_queue_tracker_export_run_for_parent_uses_facade_patched_repositories(self) -> None:
        class FakeThread:
            instances: list["FakeThread"] = []

            def __init__(self, *, target, args, daemon) -> None:
                self.target = target
                self.args = args
                self.daemon = daemon
                self.started = False
                FakeThread.instances.append(self)

            def start(self) -> None:
                self.started = True

        run_repository = InMemoryRunRepository()
        parent = run_repository.create_run(
            build_phase1_run_row(
                run_type=PROJECT_TRACKER_RUN_TYPE,
                params={},
            )
        )
        run_repository.update_run(
            parent["id"],
            {
                "status": "success",
                "summary_json": {"output": {}},
            },
        )
        artifact_repository = _RecordingArtifactRepository()
        artifact_repository.create_artifact(
            {
                "run_id": parent["id"],
                "artifact_type": "winner_csv",
                "storage_path": "artifacts/winner.csv",
            }
        )

        with patch.object(run_execution, "get_run_repository", return_value=run_repository), patch.object(
            run_execution,
            "get_artifact_repository",
            return_value=artifact_repository,
        ), patch.object(run_execution.threading, "Thread", FakeThread), patch.object(
            run_execution,
            "safely_execute_tracker_export",
            return_value=None,
        ):
            child, created = run_execution.queue_tracker_export_run_for_parent(parent["id"])

        self.assertTrue(created)
        self.assertEqual(child["parent_run_id"], str(parent["id"]))
        self.assertEqual(len(FakeThread.instances), 1)
        self.assertTrue(FakeThread.instances[0].started)

    def _execute_project_tracker_with_related_notice_queue(self, run_repository, queue_side_effect):  # type: ignore[no-untyped-def]
        artifact_repository = _RecordingArtifactRepository()
        log_repository = InMemoryRunLogRepository()
        stored = run_repository.create_run(
            build_phase1_run_row(
                run_type=PROJECT_TRACKER_RUN_TYPE,
                params={},
            )
        )

        collect_output = SimpleNamespace(
            rows=[{"id": "seed-1"}],
            collect_backend="synthetic",
            quota_fallback_used=False,
            seed_csv_path=Path("seed.csv"),
            diagnostics=None,
        )
        filter_output = SimpleNamespace(
            row_count=1,
            stage_backend="synthetic",
            candidate_csv_path=Path("candidate.csv"),
        )
        rescan_output = SimpleNamespace(
            row_count=1,
            stage_backend="synthetic",
            internal_nav_csv_path=Path("internal.csv"),
        )
        export_output = SimpleNamespace(
            row_count=1,
            stage_backend="synthetic",
            post_collect_csv_path=Path("winner.csv"),
            primary_bid_no="BID-1",
        )

        def _fake_copy_csv_artifact(*, source_path, **_: object):  # type: ignore[no-untyped-def]
            source_name = Path(source_path).name
            return SimpleNamespace(
                file_name=source_name,
                storage_path=f"artifacts/{source_name}",
                mime_type="text/csv",
                size_bytes=1,
                checksum="abc123",
                row_count=1,
            )

        def _fake_write_json_artifact(*, file_name, **_: object):  # type: ignore[no-untyped-def]
            return SimpleNamespace(
                file_name=file_name,
                storage_path=f"artifacts/{file_name}",
                mime_type="application/json",
                size_bytes=1,
                checksum="abc123",
            )

        with patch.object(run_execution, "get_run_repository", return_value=run_repository), patch.object(
            run_execution,
            "get_artifact_repository",
            return_value=artifact_repository,
        ), patch.object(run_execution, "get_run_log_repository", return_value=log_repository), patch.object(
            run_execution,
            "collect_seed_rows_for_run",
            return_value=collect_output,
        ), patch.object(run_execution, "run_filter_stage_for_run", return_value=filter_output), patch.object(
            run_execution,
            "run_rescan_stage_for_run",
            return_value=rescan_output,
        ), patch.object(run_execution, "run_export_stage_for_run", return_value=export_output), patch.object(
            run_execution,
            "copy_csv_artifact",
            side_effect=_fake_copy_csv_artifact,
        ), patch.object(run_execution, "write_json_artifact", side_effect=_fake_write_json_artifact), patch.object(
            run_execution,
            "queue_tracker_export_run_for_parent",
            return_value=({"id": uuid4(), "status": "success"}, True),
        ), patch.object(
            run_execution,
            "queue_related_notice_precompute_for_run",
            side_effect=queue_side_effect,
        ), patch.object(run_execution, "_log_info", return_value=None), patch.object(
            run_execution,
            "_log_warning",
            return_value=None,
        ), patch.object(run_execution.time, "sleep", return_value=None):
            run_execution.execute_project_tracker(stored["id"])

        refreshed = run_repository.get_run(stored["id"])
        assert refreshed is not None
        return refreshed, stored

    def test_create_log_ignores_log_repository_timeout(self) -> None:
        run_repository = InMemoryRunRepository()
        stored = run_repository.create_run(
            build_phase1_run_row(
                run_type=PROJECT_TRACKER_RUN_TYPE,
                params={},
            )
        )

        with patch.object(run_execution, "get_run_log_repository", return_value=_FailingRunLogRepository()):
            run_execution._create_log(  # noqa: SLF001
                run_id=stored["id"],
                level="info",
                stage="collect",
                message="collect stage started",
                meta={},
            )

        refreshed = run_repository.get_run(stored["id"])
        assert refreshed is not None
        self.assertEqual(refreshed["status"], "queued")

    def test_safely_execute_project_tracker_preserves_success_after_late_exception(self) -> None:
        run_repository = InMemoryRunRepository()
        log_repository = InMemoryRunLogRepository()
        stored = run_repository.create_run(
            build_phase1_run_row(
                run_type=PROJECT_TRACKER_RUN_TYPE,
                params={},
            )
        )

        def _fake_execute(run_id):  # type: ignore[no-untyped-def]
            run_repository.update_run(run_id, {"status": "success"})
            raise RuntimeError("Supabase request failed: Read timed out")

        with patch.object(run_execution, "get_run_repository", return_value=run_repository), patch.object(
            run_execution,
            "get_run_log_repository",
            return_value=log_repository,
        ), patch.object(run_execution, "execute_project_tracker", side_effect=_fake_execute):
            run_execution.safely_execute_project_tracker(stored["id"])

        refreshed = run_repository.get_run(stored["id"])
        assert refreshed is not None
        self.assertEqual(refreshed["status"], "success")
        self.assertEqual(refreshed["error_json"], {})

    def test_safely_execute_project_tracker_marks_failed_before_terminal_status(self) -> None:
        run_repository = InMemoryRunRepository()
        log_repository = InMemoryRunLogRepository()
        stored = run_repository.create_run(
            build_phase1_run_row(
                run_type=PROJECT_TRACKER_RUN_TYPE,
                params={},
            )
        )

        with patch.object(run_execution, "get_run_repository", return_value=run_repository), patch.object(
            run_execution,
            "get_run_log_repository",
            return_value=log_repository,
        ), patch.object(
            run_execution,
            "execute_project_tracker",
            side_effect=RuntimeError("Supabase request failed: Read timed out"),
        ):
            run_execution.safely_execute_project_tracker(stored["id"])

        refreshed = run_repository.get_run(stored["id"])
        assert refreshed is not None
        self.assertEqual(refreshed["status"], "failed")
        self.assertEqual(refreshed["error_json"]["message"], "Supabase request failed: Read timed out")

    def test_execute_project_tracker_preserves_related_notice_summary_after_background_update(self) -> None:
        run_repository = InMemoryRunRepository()

        def _fake_queue_related_notice_precompute_for_run(run_id):  # type: ignore[no-untyped-def]
            run_repository.update_run(
                run_id,
                {
                    "summary_json": {
                        "output": {
                            "related_notice_file_name": "project_tracker_related_notices.json",
                            "related_notice_projects": 1,
                            "related_notice_items": 3,
                            "related_notice_precompute_enabled": True,
                            "related_notice_precompute_status": "success",
                            "related_notice_precompute_error": "",
                            "related_notice_precomputed": True,
                            "related_notice_project_statuses": {
                                "project-alpha": {
                                    "status": "success",
                                    "error": "",
                                    "updated_at": "2026-04-08T10:00:00+00:00",
                                }
                            },
                            "related_notice_snapshot_set_id": str(run_id),
                        }
                    }
                },
            )
            return True

        refreshed, stored = self._execute_project_tracker_with_related_notice_queue(
            run_repository,
            _fake_queue_related_notice_precompute_for_run,
        )
        summary_output = dict(refreshed["summary_json"]["output"])
        self.assertEqual(summary_output["related_notice_file_name"], "project_tracker_related_notices.json")
        self.assertEqual(summary_output["related_notice_projects"], 1)
        self.assertEqual(summary_output["related_notice_items"], 3)
        self.assertEqual(summary_output["related_notice_precompute_status"], "success")
        self.assertEqual(summary_output["related_notice_precompute_error"], "")
        self.assertEqual(summary_output["related_notice_precomputed"], True)
        self.assertEqual(
            summary_output["related_notice_project_statuses"],
            {
                "project-alpha": {
                    "status": "success",
                    "error": "",
                    "updated_at": "2026-04-08T10:00:00+00:00",
                }
            },
        )
        self.assertEqual(summary_output["related_notice_snapshot_set_id"], str(stored["id"]))

    def test_execute_project_tracker_keeps_skipped_when_related_notice_queue_returns_false(self) -> None:
        run_repository = InMemoryRunRepository()

        def _fake_queue_related_notice_precompute_for_run(run_id):  # type: ignore[no-untyped-def]
            run_repository.update_run(
                run_id,
                {
                    "summary_json": {
                        "output": {
                            "related_notice_file_name": "project_tracker_related_notices.json",
                            "related_notice_projects": 1,
                            "related_notice_items": 3,
                            "related_notice_precompute_enabled": True,
                            "related_notice_precompute_status": "success",
                            "related_notice_precompute_error": "",
                            "related_notice_precomputed": True,
                            "related_notice_project_statuses": {
                                "project-alpha": {
                                    "status": "success",
                                    "error": "",
                                    "updated_at": "2026-04-08T10:00:00+00:00",
                                }
                            },
                            "related_notice_snapshot_set_id": str(run_id),
                        }
                    }
                },
            )
            return False

        refreshed, _stored = self._execute_project_tracker_with_related_notice_queue(
            run_repository,
            _fake_queue_related_notice_precompute_for_run,
        )
        summary_output = dict(refreshed["summary_json"]["output"])
        self.assertEqual(summary_output["related_notice_precompute_status"], "skipped")
        self.assertEqual(summary_output["related_notice_precompute_error"], "")
        self.assertFalse(summary_output["related_notice_precomputed"])

    def test_execute_project_tracker_keeps_failed_when_related_notice_queue_raises(self) -> None:
        run_repository = InMemoryRunRepository()

        def _fake_queue_related_notice_precompute_for_run(run_id):  # type: ignore[no-untyped-def]
            run_repository.update_run(
                run_id,
                {
                    "summary_json": {
                        "output": {
                            "related_notice_file_name": "project_tracker_related_notices.json",
                            "related_notice_projects": 1,
                            "related_notice_items": 3,
                            "related_notice_precompute_enabled": True,
                            "related_notice_precompute_status": "success",
                            "related_notice_precompute_error": "",
                            "related_notice_precomputed": True,
                            "related_notice_project_statuses": {
                                "project-alpha": {
                                    "status": "success",
                                    "error": "",
                                    "updated_at": "2026-04-08T10:00:00+00:00",
                                }
                            },
                            "related_notice_snapshot_set_id": str(run_id),
                        }
                    }
                },
            )
            raise RuntimeError("Supabase request failed: timeout")

        refreshed, _stored = self._execute_project_tracker_with_related_notice_queue(
            run_repository,
            _fake_queue_related_notice_precompute_for_run,
        )
        summary_output = dict(refreshed["summary_json"]["output"])
        self.assertEqual(summary_output["related_notice_precompute_status"], "failed")
        self.assertEqual(summary_output["related_notice_precompute_error"], "Supabase request failed: timeout")
        self.assertFalse(summary_output["related_notice_precomputed"])

    def test_safely_execute_tracker_export_preserves_success_after_late_exception(self) -> None:
        run_repository = InMemoryRunRepository()
        log_repository = InMemoryRunLogRepository()
        stored = run_repository.create_run(
            build_phase1_run_row(
                run_type=TRACKER_EXPORT_RUN_TYPE,
                params={"source_run_id": "parent"},
            )
        )

        def _fake_execute(parent_run_id, child_run_id):  # type: ignore[no-untyped-def]
            del parent_run_id
            run_repository.update_run(child_run_id, {"status": "success"})
            raise RuntimeError("Supabase request failed: Read timed out")

        with patch.object(run_execution, "get_run_repository", return_value=run_repository), patch.object(
            run_execution,
            "get_run_log_repository",
            return_value=log_repository,
        ), patch.object(run_execution, "execute_tracker_export", side_effect=_fake_execute):
            run_execution.safely_execute_tracker_export(stored["id"], stored["id"])

        refreshed = run_repository.get_run(stored["id"])
        assert refreshed is not None
        self.assertEqual(refreshed["status"], "success")
        self.assertEqual(refreshed["error_json"], {})


if __name__ == "__main__":
    unittest.main()
