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
    assert audit_file_names == ["SPMS_20260501.xlsx"]
    assert 'filename="SPMS_20260501.xlsx"' in response.headers["content-disposition"]


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


def test_direct_tracker_download_bypasses_workbook_cache(monkeypatch) -> None:
    listed_rows: list[dict[str, object]] = [{"project_name": "A"}]
    cache_calls: list[str] = []
    audit_file_names: list[str] = []

    monkeypatch.setattr(tracker_export_handlers.support, "_resolve_sales_actor", lambda _request: None)
    monkeypatch.setattr(
        tracker_export_handlers.support,
        "_can_cache_tracker_export_workbook",
        lambda **_kwargs: True,
    )

    def fail_if_cache_used(**_kwargs: object) -> bytes:
        cache_calls.append("called")
        raise AssertionError("direct tracker downloads must not wait on the workbook cache")

    monkeypatch.setattr(
        tracker_export_handlers.support,
        "_get_or_build_cached_tracker_export_workbook_bytes",
        fail_if_cache_used,
    )
    monkeypatch.setattr(
        tracker_export_handlers,
        "_list_tracker_entries_for_export",
        lambda **_kwargs: listed_rows,
    )
    monkeypatch.setattr(
        tracker_export_handlers.support,
        "build_tracking_download_workbook_bytes",
        lambda *, rows, selected_regions=None: b"xlsx-bytes",
    )

    def record_download_audit_log(**kwargs: object) -> None:
        audit_file_names.append(str(kwargs["file_name"]))

    monkeypatch.setattr(
        tracker_export_handlers.support,
        "_record_download_audit_log",
        record_download_audit_log,
    )

    response = tracker_export_handlers.download_tracker_entry_summaries(object(), format="xlsx")

    assert cache_calls == []
    assert response.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert audit_file_names and audit_file_names[0].startswith("SPMS_")


def test_export_rows_bypass_global_cache_loader_for_global_scope(monkeypatch) -> None:
    raw_rows = [{"project_name": "A", "notice_date": "2026-01-02"}]
    collapsed_rows = [{"project_name": "A", "notice_date": "2026-01-02", "collapsed": True}]
    normalized_rows = [{"project_name": "A", "notice_date": "2026-01-02", "normalized": True}]

    monkeypatch.setattr(
        tracker_export_handlers.support,
        "_is_global_tracker_scope",
        lambda **_kwargs: True,
    )
    monkeypatch.setattr(
        tracker_export_handlers.support,
        "_load_global_tracker_rows",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("global cache loader must not be used for export")),
    )
    monkeypatch.setattr(
        tracker_export_handlers.support,
        "_load_all_tracker_entries_for_global_summary",
        lambda: raw_rows,
    )
    monkeypatch.setattr(
        tracker_export_handlers.support,
        "_collapse_tracker_rows_by_project",
        lambda rows: collapsed_rows if rows == raw_rows else rows,
    )
    monkeypatch.setattr(
        tracker_export_handlers.support,
        "_filter_tracker_rows_for_global_scope",
        lambda rows, **_kwargs: rows,
    )
    monkeypatch.setattr(
        tracker_export_handlers.support,
        "_normalize_tracker_rows_for_presentation",
        lambda rows: normalized_rows if rows == collapsed_rows else rows,
    )

    rows = tracker_export_handlers._list_tracker_entries_for_export(
        q="",
        region="",
        notice_year="2026",
        exclude_auxiliary_titles=True,
        edited_only=False,
        source_run_id=None,
        source_tracker_run_id=None,
        sheet_name="",
        section_name="",
    )

    assert rows == normalized_rows
