from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from backend.api.routers import tracker_export_handlers
from backend.services.tracker_download_job_store import find_reusable_tracker_download_job
from backend.services.tracker_download_job_store import store_tracker_download_job


def _job(cache_key: str, status: str) -> dict[str, object]:
    return {
        "id": uuid4(),
        "status": status,
        "format": "xlsx",
        "cache_key": cache_key,
        "output_path": "",
        "file_name": "project_status_test.xlsx",
        "created_at": datetime(2026, 5, 1),
        "started_at": None,
        "finished_at": None,
        "error": "",
        "reused_existing": False,
        "summary": {},
    }


def test_find_reusable_tracker_download_job_reuses_in_flight_job() -> None:
    cache_key = f"cache-{uuid4()}"
    stored = store_tracker_download_job(_job(cache_key, "queued"))

    reusable = find_reusable_tracker_download_job(cache_key)

    assert reusable is not None
    assert reusable["id"] == stored["id"]


def test_find_reusable_tracker_download_job_reuses_successful_workbook_for_same_cache_key(tmp_path) -> None:
    cache_key = f"cache-{uuid4()}"
    workbook_path = tmp_path / "cached.xlsx"
    workbook_path.write_bytes(b"xlsx")
    stored = store_tracker_download_job(
        {
            **_job(cache_key, "success"),
            "output_path": str(workbook_path),
        }
    )

    reusable = find_reusable_tracker_download_job(cache_key)

    assert reusable is not None
    assert reusable["id"] == stored["id"]


def test_download_job_file_uses_download_time_filename(tmp_path, monkeypatch) -> None:
    job_id = uuid4()
    workbook_path = tmp_path / "cached.xlsx"
    workbook_path.write_bytes(b"xlsx")
    audit_file_names: list[str] = []

    class FixedDateTime:
        @classmethod
        def now(cls, tz=None) -> datetime:
            assert getattr(tz, "key", "") == "Asia/Seoul"
            return datetime(2026, 5, 1, 12, 34, 56)

    monkeypatch.setattr(tracker_export_handlers, "datetime", FixedDateTime)
    monkeypatch.setattr(
        tracker_export_handlers.support,
        "get_stored_tracker_download_job",
        lambda requested_id: {
            **_job("cache", "success"),
            "id": requested_id,
            "output_path": str(workbook_path),
            "file_name": "project_status_20260429_001844.xlsx",
        },
    )
    monkeypatch.setattr(tracker_export_handlers.support, "_resolve_sales_actor", lambda _request: None)

    def record_download_audit_log(**kwargs: object) -> None:
        audit_file_names.append(str(kwargs["file_name"]))

    monkeypatch.setattr(
        tracker_export_handlers.support,
        "_record_download_audit_log",
        record_download_audit_log,
    )

    response = tracker_export_handlers.download_tracker_entry_summary_download_job_file(object(), job_id)

    assert response.path == Path(workbook_path)
    assert audit_file_names == ["project_status_20260501_123456.xlsx"]
    assert 'filename="project_status_20260501_123456.xlsx"' in response.headers["content-disposition"]


def test_data_version_lookup_failure_disables_reuse(monkeypatch) -> None:
    class FixedDateTime:
        @classmethod
        def now(cls, tz=None) -> datetime:
            assert getattr(tz, "key", "") == "Asia/Seoul"
            return datetime(2026, 5, 1, 12, 34, 56, 789)

    class FailingRepository:
        def get_entries_data_version(self) -> str:
            raise RuntimeError("db unavailable")

    monkeypatch.setattr(tracker_export_handlers, "datetime", FixedDateTime)
    monkeypatch.setattr(
        tracker_export_handlers.support,
        "_get_tracker_repository",
        lambda: FailingRepository(),
    )

    assert tracker_export_handlers._get_tracker_entries_data_version() == "lookup_failed=20260501_123456_000789"
