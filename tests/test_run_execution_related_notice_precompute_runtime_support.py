import unittest
from types import SimpleNamespace
from uuid import uuid4

from backend.services.run_execution_related_notice_precompute_runtime_support import resolve_existing_related_notice_artifact_state
from backend.services.run_execution_related_notice_precompute_runtime_support import validate_related_notice_precompute_run
from backend.services.run_execution_related_notice_precompute_runtime_support import write_related_notice_precompute_artifact


RELATED_NOTICE_ALGORITHM_VERSION = 11
RELATED_NOTICE_ARTIFACT_FILE_NAME = "project_tracker_related_notices.json"
RELATED_NOTICE_ARTIFACT_TYPE = "related_notices_json"


class RunExecutionRelatedNoticePrecomputeRuntimeSupportTests(unittest.TestCase):
    def test_validate_related_notice_precompute_run_rejects_failed_run(self) -> None:
        run_id = uuid4()

        with self.assertRaisesRegex(Exception, f"related notice precompute requires a successful run: {run_id}"):
            validate_related_notice_precompute_run(
                run_id=run_id,
                run={"run_type": "project_tracker", "status": "failed"},
                run_repository_error_cls=RuntimeError,
            )

    def test_resolve_existing_related_notice_artifact_state_short_circuits_for_matching_project(self) -> None:
        run_id = uuid4()
        existing_artifact = {
            "artifact_type": RELATED_NOTICE_ARTIFACT_TYPE,
            "storage_path": "artifacts/project_tracker_related_notices.json",
        }
        existing_payload = {
            "projects": [
                {
                    "project_key": "project-alpha",
                    "algorithm_version": RELATED_NOTICE_ALGORITHM_VERSION,
                    "items": [{"id": "one"}],
                }
            ]
        }

        resolved_artifact, resolved_payload, should_skip = resolve_existing_related_notice_artifact_state(
            artifacts=[existing_artifact],
            related_notice_artifact_type=RELATED_NOTICE_ARTIFACT_TYPE,
            project_key="project-alpha",
            force_recompute=False,
            load_existing_related_notice_payload_fn=lambda storage_path: existing_payload if storage_path else None,
            should_skip_related_notice_project_recompute_fn=lambda **kwargs: bool(
                kwargs.get("existing_payload")
                and kwargs.get("project_key") == "project-alpha"
                and not kwargs.get("force_recompute")
            ),
        )

        self.assertEqual(resolved_artifact, existing_artifact)
        self.assertEqual(resolved_payload, existing_payload)
        self.assertTrue(should_skip)

        resolved_artifact, resolved_payload, should_skip = resolve_existing_related_notice_artifact_state(
            artifacts=[existing_artifact],
            related_notice_artifact_type=RELATED_NOTICE_ARTIFACT_TYPE,
            project_key="project-beta",
            force_recompute=False,
            load_existing_related_notice_payload_fn=lambda storage_path: existing_payload if storage_path else None,
            should_skip_related_notice_project_recompute_fn=lambda **kwargs: bool(
                kwargs.get("existing_payload")
                and kwargs.get("project_key") == "project-alpha"
                and not kwargs.get("force_recompute")
            ),
        )

        self.assertEqual(resolved_artifact, existing_artifact)
        self.assertEqual(resolved_payload, existing_payload)
        self.assertFalse(should_skip)

    def test_write_related_notice_precompute_artifact_creates_record_and_updates_summary(self) -> None:
        run_id = uuid4()
        artifact_repository = object()
        created_records: list[dict[str, object]] = []
        summary_patches: list[dict[str, object]] = []
        info_events: list[dict[str, object]] = []

        def _write_json_artifact_fn(*, run_id, file_name, payload):  # type: ignore[no-untyped-def]
            del run_id, payload
            return SimpleNamespace(
                file_name=file_name,
                storage_path=f"artifacts/{file_name}",
                mime_type="application/json",
                size_bytes=42,
                checksum="abc123",
            )

        def _create_artifact_record_fn(**kwargs):  # type: ignore[no-untyped-def]
            created_records.append(dict(kwargs))

        def _update_related_notice_summary_fn(**kwargs):  # type: ignore[no-untyped-def]
            summary_patches.append(dict(kwargs))

        def _build_related_notice_project_status_patch_fn(project_keys, *, status, error=""):  # type: ignore[no-untyped-def]
            return {
                key: {"status": status, "error": error, "updated_at": "2026-04-25T00:00:00+00:00"}
                for key in project_keys
            }

        def _log_info_fn(**kwargs):  # type: ignore[no-untyped-def]
            info_events.append(dict(kwargs))

        payload = {
            "project_count": 2,
            "item_count": 5,
            "projects": [
                {"project_key": "project-alpha"},
                {"project_key": "project-beta"},
            ],
        }

        written_artifact, project_keys = write_related_notice_precompute_artifact(
            run_id=run_id,
            artifact_repository=artifact_repository,
            existing_related_artifact=None,
            related_notice_payload=payload,
            related_notice_artifact_file_name=RELATED_NOTICE_ARTIFACT_FILE_NAME,
            related_notice_artifact_type=RELATED_NOTICE_ARTIFACT_TYPE,
            write_json_artifact_fn=_write_json_artifact_fn,
            create_artifact_record_fn=_create_artifact_record_fn,
            update_related_notice_summary_fn=_update_related_notice_summary_fn,
            build_related_notice_project_status_patch_fn=_build_related_notice_project_status_patch_fn,
            log_info_fn=_log_info_fn,
        )

        self.assertEqual(written_artifact.file_name, RELATED_NOTICE_ARTIFACT_FILE_NAME)
        self.assertEqual(project_keys, ["project-alpha", "project-beta"])
        self.assertEqual(len(created_records), 1)
        self.assertEqual(created_records[0]["artifact_repository"], artifact_repository)
        self.assertEqual(created_records[0]["artifact_type"], RELATED_NOTICE_ARTIFACT_TYPE)
        self.assertEqual(created_records[0]["meta"]["backend"], "precomputed")
        self.assertEqual(len(summary_patches), 1)
        self.assertEqual(summary_patches[0]["summary_patch"]["related_notice_file_name"], RELATED_NOTICE_ARTIFACT_FILE_NAME)
        self.assertEqual(
            summary_patches[0]["summary_patch"]["related_notice_project_statuses"],
            {
                "project-alpha": {
                    "status": "success",
                    "error": "",
                    "updated_at": "2026-04-25T00:00:00+00:00",
                },
                "project-beta": {
                    "status": "success",
                    "error": "",
                    "updated_at": "2026-04-25T00:00:00+00:00",
                },
            },
        )
        self.assertEqual(len(info_events), 1)
        self.assertEqual(info_events[0]["message"], "related notices precomputed")


if __name__ == "__main__":
    unittest.main()
