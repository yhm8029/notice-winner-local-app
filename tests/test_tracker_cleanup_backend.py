from __future__ import annotations

from unittest import TestCase
from uuid import UUID

from backend.phase1_defaults import TRACKER_EXPORT_RUN_TYPE
from backend.phase1_defaults import build_phase1_run_row
from backend.phase1_defaults import load_phase1_identity
from backend.repositories.in_memory_artifacts import InMemoryArtifactRepository
from backend.repositories.in_memory_logs import InMemoryRunLogRepository
from backend.repositories.in_memory_runs import InMemoryRunRepository
from backend.repositories.in_memory_tracker_entries import InMemoryTrackerEntryRepository
from backend.services import tracker_cleanup_backend


PARENT_RUN_ID = UUID("11111111-1111-1111-1111-111111111111")
TRACKER_RUN_ID = UUID("22222222-2222-2222-2222-222222222222")


class TrackerCleanupBackendTests(TestCase):
    def setUp(self) -> None:
        self.identity = load_phase1_identity()
        self.tracker_repository = InMemoryTrackerEntryRepository()
        self.run_repository = InMemoryRunRepository()
        self.log_repository = InMemoryRunLogRepository()
        self.artifact_repository = InMemoryArtifactRepository()

        parent = self.run_repository.create_run(build_phase1_run_row(run_type="project_tracker", params={"q": "demo"}))
        self.run_repository._runs[PARENT_RUN_ID] = {  # type: ignore[attr-defined]
            **parent,
            "id": PARENT_RUN_ID,
            "run_type": "project_tracker",
            "parent_run_id": None,
        }
        self.run_repository._runs.pop(parent["id"], None)  # type: ignore[attr-defined]

        child = self.run_repository.create_run(
            build_phase1_run_row(
                run_type=TRACKER_EXPORT_RUN_TYPE,
                params={"source_run_id": str(PARENT_RUN_ID)},
                parent_run_id=PARENT_RUN_ID,
            )
        )
        self.run_repository._runs[TRACKER_RUN_ID] = {  # type: ignore[attr-defined]
            **child,
            "id": TRACKER_RUN_ID,
            "run_type": TRACKER_EXPORT_RUN_TYPE,
            "parent_run_id": str(PARENT_RUN_ID),
        }
        self.run_repository._runs.pop(child["id"], None)  # type: ignore[attr-defined]

        self.tracker_repository.upsert_source_entries(
            source_run_id=PARENT_RUN_ID,
            source_tracker_run_id=TRACKER_RUN_ID,
            entries=[
                {
                    "entry_key": "bid-1|000|sample",
                    "row_no": 1,
                    "source_bid_no": "bid-1",
                    "source_bid_ord": "000",
                    "source_project_name_norm": "sample",
                    "project_name": "Sample Project",
                    "gross_area_scale": "1000",
                    "construction_cost": "2000",
                    "demand_org_name": "Agency",
                    "demand_contact": "Contact",
                    "client_location": "Seoul",
                    "site_location_1": "Seoul",
                    "site_location_2": "",
                    "architect_office": "Office",
                    "construction_start_date": "2026-04-01",
                    "last_checked_date": "2026-04-02",
                    "progress_note": "",
                    "notice_date": "2026-04-01",
                    "manager_name": "Kim",
                    "building_automation_estimated_amount": "1000000",
                    "sheet_name": "Sheet1",
                    "section_name": "facility_cost",
                }
            ],
        )
        self.log_repository.create_log(
            {
                "run_id": PARENT_RUN_ID,
                "organization_id": str(self.identity.organization_id),
                "level": "info",
                "stage": "collect",
                "message": "parent",
                "meta_json": {},
            }
        )
        self.log_repository.create_log(
            {
                "run_id": TRACKER_RUN_ID,
                "organization_id": str(self.identity.organization_id),
                "level": "info",
                "stage": "export",
                "message": "child",
                "meta_json": {},
            }
        )
        self.artifact_repository.create_artifact(
            {
                "run_id": PARENT_RUN_ID,
                "organization_id": str(self.identity.organization_id),
                "artifact_type": "json",
                "storage_path": "/tmp/parent.json",
                "file_name": "parent.json",
                "mime_type": "application/json",
                "size_bytes": 1,
                "checksum": "",
                "meta_json": {},
            }
        )
        self.artifact_repository.create_artifact(
            {
                "run_id": TRACKER_RUN_ID,
                "organization_id": str(self.identity.organization_id),
                "artifact_type": "xlsx",
                "storage_path": "/tmp/child.xlsx",
                "file_name": "child.xlsx",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "size_bytes": 1,
                "checksum": "",
                "meta_json": {},
            }
        )

    def test_cleanup_preview_collects_parent_child_logs_and_artifacts(self) -> None:
        preview = tracker_cleanup_backend.preview_tracker_cleanup(
            source_tracker_run_id=TRACKER_RUN_ID,
            tracker_repository=self.tracker_repository,
            run_repository=self.run_repository,
            log_repository=self.log_repository,
            artifact_repository=self.artifact_repository,
        )

        self.assertEqual(preview["source_tracker_run_id"], str(TRACKER_RUN_ID))
        self.assertEqual(preview["parent_run_id"], str(PARENT_RUN_ID))
        self.assertEqual(preview["tracker_entry_count"], 1)
        self.assertEqual(preview["child_run_count"], 1)
        self.assertEqual(preview["parent_run_count"], 1)
        self.assertEqual(preview["log_count"], 2)
        self.assertEqual(preview["artifact_count"], 2)

    def test_apply_cleanup_deletes_children_before_parent(self) -> None:
        result = tracker_cleanup_backend.apply_tracker_cleanup(
            source_tracker_run_id=TRACKER_RUN_ID,
            tracker_repository=self.tracker_repository,
            run_repository=self.run_repository,
            log_repository=self.log_repository,
            artifact_repository=self.artifact_repository,
        )

        self.assertEqual(result["deleted_tracker_entry_count"], 1)
        self.assertEqual(result["deleted_run_count"], 2)
        self.assertEqual(result["deleted_log_count"], 2)
        self.assertEqual(result["deleted_artifact_count"], 2)
        entries, total = self.tracker_repository.list_entries(
            page=1,
            page_size=50,
            q="",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
            source_run_id=None,
            source_tracker_run_id=TRACKER_RUN_ID,
            sheet_name="",
            section_name="",
        )
        self.assertEqual((entries, total), ([], 0))
        self.assertIsNone(self.run_repository.get_run(TRACKER_RUN_ID))
        self.assertIsNone(self.run_repository.get_run(PARENT_RUN_ID))

    def test_apply_cleanup_deletes_tracker_entries_before_parent_run(self) -> None:
        operations: list[str] = []

        class RecordingTrackerRepository:
            def list_entries(self, **kwargs):  # type: ignore[no-untyped-def]
                self.last_source_tracker_run_id = kwargs["source_tracker_run_id"]
                return ([{"source_run_id": str(PARENT_RUN_ID)}], 1)

            def delete_entries_by_source_tracker_run_id(self, *, source_tracker_run_id: UUID) -> int:
                operations.append(f"entries:{source_tracker_run_id}")
                return 1

        class RecordingRunRepository:
            def get_run(self, run_id: UUID | None):
                if run_id == TRACKER_RUN_ID:
                    return {"id": str(TRACKER_RUN_ID), "parent_run_id": str(PARENT_RUN_ID)}
                if run_id == PARENT_RUN_ID:
                    return {"id": str(PARENT_RUN_ID), "parent_run_id": None}
                return None

            def list_runs(self, **kwargs):  # type: ignore[no-untyped-def]
                return ([{"id": str(TRACKER_RUN_ID), "parent_run_id": str(PARENT_RUN_ID)}], 1)

            def delete_run(self, run_id: UUID) -> bool:
                operations.append(f"run:{run_id}")
                return True

        class RecordingLogRepository:
            def list_logs(self, *, run_id: UUID, cursor, limit: int):  # type: ignore[no-untyped-def]
                return ([], None)

            def delete_logs_for_run(self, run_id: UUID) -> int:
                operations.append(f"log:{run_id}")
                return 0

        class RecordingArtifactRepository:
            def list_artifacts(self, *, run_id: UUID) -> list[dict[str, str]]:
                return []

            def delete_artifacts_for_run(self, run_id: UUID) -> int:
                operations.append(f"artifact:{run_id}")
                return 0

        tracker_cleanup_backend.apply_tracker_cleanup(
            source_tracker_run_id=TRACKER_RUN_ID,
            tracker_repository=RecordingTrackerRepository(),
            run_repository=RecordingRunRepository(),
            log_repository=RecordingLogRepository(),
            artifact_repository=RecordingArtifactRepository(),
        )

        self.assertLess(
            operations.index(f"entries:{TRACKER_RUN_ID}"),
            operations.index(f"run:{PARENT_RUN_ID}"),
        )

    def test_apply_cleanup_keeps_parent_when_other_tracker_export_child_exists(self) -> None:
        sibling_run_id = UUID("33333333-3333-3333-3333-333333333333")
        sibling = self.run_repository.create_run(
            build_phase1_run_row(
                run_type=TRACKER_EXPORT_RUN_TYPE,
                params={"source_run_id": str(PARENT_RUN_ID), "auto_created": True},
                parent_run_id=PARENT_RUN_ID,
            )
        )
        self.run_repository._runs[sibling_run_id] = {  # type: ignore[attr-defined]
            **sibling,
            "id": sibling_run_id,
            "run_type": TRACKER_EXPORT_RUN_TYPE,
            "parent_run_id": str(PARENT_RUN_ID),
            "status": "success",
        }
        self.run_repository._runs.pop(sibling["id"], None)  # type: ignore[attr-defined]

        self.log_repository.create_log(
            {
                "run_id": sibling_run_id,
                "organization_id": str(self.identity.organization_id),
                "level": "info",
                "stage": "export",
                "message": "sibling",
                "meta_json": {},
            }
        )
        self.artifact_repository.create_artifact(
            {
                "run_id": sibling_run_id,
                "organization_id": str(self.identity.organization_id),
                "artifact_type": "xlsx",
                "storage_path": "/tmp/sibling.xlsx",
                "file_name": "sibling.xlsx",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "size_bytes": 1,
                "checksum": "",
                "meta_json": {},
            }
        )

        result = tracker_cleanup_backend.apply_tracker_cleanup(
            source_tracker_run_id=TRACKER_RUN_ID,
            tracker_repository=self.tracker_repository,
            run_repository=self.run_repository,
            log_repository=self.log_repository,
            artifact_repository=self.artifact_repository,
        )

        self.assertEqual(result["deleted_tracker_entry_count"], 1)
        self.assertEqual(result["deleted_run_count"], 1)
        self.assertEqual(result["deleted_log_count"], 1)
        self.assertEqual(result["deleted_artifact_count"], 1)
        self.assertIsNone(self.run_repository.get_run(TRACKER_RUN_ID))
        self.assertIsNotNone(self.run_repository.get_run(PARENT_RUN_ID))
        self.assertIsNotNone(self.run_repository.get_run(sibling_run_id))

    def test_cleanup_preview_excludes_parent_counts_when_sibling_child_exists(self) -> None:
        sibling_run_id = UUID("33333333-3333-3333-3333-333333333333")
        sibling = self.run_repository.create_run(
            build_phase1_run_row(
                run_type=TRACKER_EXPORT_RUN_TYPE,
                params={"source_run_id": str(PARENT_RUN_ID), "auto_created": True},
                parent_run_id=PARENT_RUN_ID,
            )
        )
        self.run_repository._runs[sibling_run_id] = {  # type: ignore[attr-defined]
            **sibling,
            "id": sibling_run_id,
            "run_type": TRACKER_EXPORT_RUN_TYPE,
            "parent_run_id": str(PARENT_RUN_ID),
            "status": "success",
        }
        self.run_repository._runs.pop(sibling["id"], None)  # type: ignore[attr-defined]

        preview = tracker_cleanup_backend.preview_tracker_cleanup(
            source_tracker_run_id=TRACKER_RUN_ID,
            tracker_repository=self.tracker_repository,
            run_repository=self.run_repository,
            log_repository=self.log_repository,
            artifact_repository=self.artifact_repository,
        )

        self.assertEqual(preview["child_run_count"], 1)
        self.assertEqual(preview["parent_run_count"], 0)
        self.assertEqual(preview["log_count"], 1)
        self.assertEqual(preview["artifact_count"], 1)
