from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from backend.phase1_defaults import build_phase1_run_row
from backend.phase1_defaults import load_phase1_identity
from backend.repositories.in_memory_artifacts import InMemoryArtifactRepository
from backend.repositories.in_memory_runs import InMemoryRunRepository
from backend.services.run_execution_lifecycle_runtime import summary_json_preserving_related_notice_state
from backend.services.run_execution_seed_runtime import build_tracker_seed_entries
from backend.services.run_execution_seed_runtime import stage_delay_seconds
from backend.services.run_execution_seed_runtime import to_storage_path
from backend.services.run_execution_support_runtime import create_artifact_record
from backend.services.run_execution_support_runtime import merge_run_summary_output
from backend.services.run_execution_support_runtime import update_related_notice_summary


def test_summary_json_preserving_related_notice_state_keeps_success_output() -> None:
    run_repository = InMemoryRunRepository()
    stored = run_repository.create_run(
        {
            **build_phase1_run_row(run_type="project_tracker", params={}),
            "summary_json": {
                "output": {
                    "related_notice_precompute_status": "success",
                    "related_notice_precomputed": True,
                    "related_notice_cache_key": "current",
                }
            },
        }
    )

    merged = summary_json_preserving_related_notice_state(
        run_repository=run_repository,
        run_id=stored["id"],
        summary_json={"output": {"tracker_entry_rows": 10}},
    )

    assert merged["output"]["tracker_entry_rows"] == 10
    assert merged["output"]["related_notice_precompute_status"] == "success"
    assert merged["output"]["related_notice_cache_key"] == "current"


def test_build_tracker_seed_entries_normalizes_seed_rows() -> None:
    run_id = uuid4()

    entries = build_tracker_seed_entries(
        run_id=run_id,
        params={"notice_title": "Demo Project", "demand_org": "Demo Org"},
        seed_rows=[
            {
                "bid_no": "R25",
                "bid_ord": "1",
                "project_name": "Alpha Build",
                "org_name": "Alpha Org",
                "announce_date": "20250131",
                "g2b_verified": "Y",
            }
        ],
    )

    assert len(entries) == 1
    assert entries[0]["entry_key"] == "r25|001|alpha-build"
    assert entries[0]["notice_date"] == "2025-01-31"


def test_seed_runtime_helpers_handle_delay_and_storage_path() -> None:
    delay = stage_delay_seconds(
        params={"_advanced_options": {"simulate_stage_delay_ms": "bad"}},
        fallback_ms=20,
    )
    storage_path = to_storage_path(Path("C:/tmp/demo.csv"))

    assert delay == 0.02
    assert storage_path.endswith("demo.csv")


def test_update_related_notice_summary_merges_project_status_entries() -> None:
    run_repository = InMemoryRunRepository()
    stored = run_repository.create_run(
        {
            **build_phase1_run_row(run_type="project_tracker", params={}),
            "summary_json": {
                "output": {
                    "related_notice_project_statuses": {
                        "project-alpha": {
                            "status": "running",
                            "updated_at": "2026-04-24T00:00:00+00:00",
                        }
                    }
                }
            },
        }
    )

    update_related_notice_summary(
        run_repository=run_repository,
        run_id=stored["id"],
        summary_patch={
            "related_notice_precompute_status": "success",
            "related_notice_project_statuses": {
                "project-alpha": {"status": "success"},
                "project-beta": {"status": "failed", "error": "boom"},
            },
        },
    )

    refreshed = run_repository.get_run(stored["id"])
    assert refreshed is not None
    output = dict(refreshed["summary_json"]["output"])
    assert output["related_notice_precompute_status"] == "success"
    assert output["related_notice_project_statuses"]["project-alpha"]["status"] == "success"
    assert output["related_notice_project_statuses"]["project-alpha"]["updated_at"] == "2026-04-24T00:00:00+00:00"
    assert output["related_notice_project_statuses"]["project-beta"]["error"] == "boom"


def test_merge_run_summary_output_uses_best_effort_updater() -> None:
    run_repository = InMemoryRunRepository()
    stored = run_repository.create_run(
        {
            **build_phase1_run_row(run_type="project_tracker", params={}),
            "summary_json": {"output": {"existing": 1}},
        }
    )

    def _best_effort_update_run(run_id, fields, *, context):  # type: ignore[no-untyped-def]
        assert context == "unit-test"
        run_repository.update_run(run_id, fields)

    merge_run_summary_output(
        run_repository=run_repository,
        best_effort_update_run_fn=_best_effort_update_run,
        run_id=stored["id"],
        summary_patch={"next": 2},
        context="unit-test",
    )

    refreshed = run_repository.get_run(stored["id"])
    assert refreshed is not None
    assert refreshed["summary_json"]["output"] == {"existing": 1, "next": 2}


def test_create_artifact_record_uses_identity_fields() -> None:
    artifact_repository = InMemoryArtifactRepository()
    run_id = uuid4()

    create_artifact_record(
        load_phase1_identity_fn=load_phase1_identity,
        artifact_repository=artifact_repository,
        run_id=run_id,
        artifact_type="winner_csv",
        written_artifact=type(
            "WrittenArtifact",
            (),
            {
                "storage_path": "artifacts/winner.csv",
                "file_name": "winner.csv",
                "mime_type": "text/csv",
                "size_bytes": 42,
                "checksum": "abc123",
            },
        )(),
        meta={"stage": "export"},
    )

    rows = artifact_repository.list_artifacts(run_id=run_id)
    assert len(rows) == 1
    assert rows[0]["artifact_type"] == "winner_csv"
    assert rows[0]["file_name"] == "winner.csv"
    assert rows[0]["meta_json"] == {"stage": "export"}
