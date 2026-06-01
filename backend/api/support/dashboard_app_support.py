from __future__ import annotations

from typing import Any
from uuid import UUID

from backend.api.schemas import DashboardSummaryResponse
from backend.api.support.runtime_common import ApiError
from backend.api.support.runtime_common import _backend_api_app
from backend.api.support.runtime_common import _not_found
from backend.api.support.runtime_common import _repository_error
from backend.repositories import ArtifactRepositoryConfigError
from backend.repositories import RunLogRepositoryConfigError
from backend.repositories import RunRepositoryConfigError
from backend.repositories import RunRepositoryError
from backend.repositories import TrackerEntryRepositoryConfigError
from backend.repositories import TrackerEntryRepositoryError


def _collect_all_runs() -> list[dict[str, Any]]:
    backend_api_app = _backend_api_app
    run_repository = backend_api_app._get_run_repository()
    page = 1
    page_size = 200
    items: list[dict[str, Any]] = []
    total = 0
    while True:
        try:
            batch, total = run_repository.list_runs(
                page=page,
                page_size=page_size,
                status="",
                run_type="",
                parent_run_id=None,
                date_from="",
                date_to="",
            )
        except RunRepositoryError as exc:
            if page > 1 and backend_api_app._is_range_not_satisfiable_error(str(exc)):
                return backend_api_app._filter_visible_runs(items)
            raise
        items.extend(batch)
        if not batch or len(items) >= total:
            return backend_api_app._filter_visible_runs(items)
        page += 1


def _collect_all_tracker_entries() -> list[dict[str, Any]]:
    backend_api_app = _backend_api_app
    tracker_repository = backend_api_app._get_tracker_repository()
    visible_run_ids = {
        str(row.get("id") or "")
        for row in backend_api_app._collect_all_runs()
    }
    page = 1
    page_size = 1000
    items: list[dict[str, Any]] = []
    total = 0
    while True:
        try:
            batch, total = tracker_repository.list_entries(
                page=page,
                page_size=page_size,
                q="",
                region="",
                exclude_auxiliary_titles=False,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=None,
                sheet_name="",
                section_name="",
            )
        except TrackerEntryRepositoryError as exc:
            if page > 1 and backend_api_app._is_range_not_satisfiable_error(str(exc)):
                return items
            raise
        if backend_api_app._synthetic_debug_mode_enabled():
            items.extend(batch)
        else:
            for entry in batch:
                source_run_id = str(entry.get("source_run_id") or "").strip()
                source_tracker_run_id = str(entry.get("source_tracker_run_id") or "").strip()
                if source_run_id and source_run_id not in visible_run_ids:
                    continue
                if source_tracker_run_id and source_tracker_run_id not in visible_run_ids:
                    continue
                items.append(entry)
        if not batch or len(items) >= total:
            return items
        page += 1


def _get_project_aggregate(project_id: UUID) -> dict[str, Any]:
    backend_api_app = _backend_api_app
    for item in backend_api_app._build_project_aggregates().values():
        if item["id"] == project_id:
            return item
    fallback = backend_api_app._build_project_aggregate_from_tracker_entries(project_id)
    if fallback is not None:
        return fallback
    _not_found(f"project not found: {project_id}")


def _build_dashboard_summary() -> DashboardSummaryResponse:
    backend_api_app = _backend_api_app
    try:
        backend_summary = backend_api_app.describe_repository_backends()
    except (
        ArtifactRepositoryConfigError,
        RunLogRepositoryConfigError,
        RunRepositoryConfigError,
        TrackerEntryRepositoryConfigError,
    ) as exc:
        _repository_error(str(exc))
    run_repository = backend_api_app._get_run_repository()
    tracker_repository = backend_api_app._get_tracker_repository()
    run_counts = {status_value: 0 for status_value in sorted(backend_api_app.VALID_RUN_STATUSES)}
    try:
        for status_value in run_counts:
            _items, total = run_repository.list_runs(
                page=1,
                page_size=1,
                status=status_value,
                run_type="",
                parent_run_id=None,
                date_from="",
                date_to="",
            )
            run_counts[status_value] = total
        failed_rows, _failed_total = run_repository.list_runs(
            page=1,
            page_size=5,
            status="failed",
            run_type="",
            parent_run_id=None,
            date_from="",
            date_to="",
        )
    except RunRepositoryError as exc:
        _repository_error(str(exc))

    try:
        _items, tracker_total = tracker_repository.list_entries(
            page=1,
            page_size=1,
            q="",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )
        _edited_items, tracker_edited_total = tracker_repository.list_entries(
            page=1,
            page_size=1,
            q="",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=True,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )
    except TrackerEntryRepositoryError as exc:
        _repository_error(str(exc))

    latest_reports: dict[str, Any] = {}
    for report_name in backend_api_app.REPORT_FILES:
        try:
            report_payload = backend_api_app._load_report_payload(report_name)
            latest_reports[report_name] = {
                "available": True,
                "summary": dict(report_payload.get("summary") or {}),
            }
        except (ApiError, backend_api_app.ApiError):
            latest_reports[report_name] = {
                "available": False,
                "summary": {},
            }

    active_jobs = [
        backend_api_app.to_report_job_item(item).model_dump(mode="json")
        for item in backend_api_app.list_stored_report_jobs(limit=10)
        if str(item.get("status")) in {"queued", "running"}
    ]

    return DashboardSummaryResponse(
        run_counts=run_counts,
        tracker_total=tracker_total,
        tracker_edited_total=tracker_edited_total,
        repository_backends={
            "tracker_entries": str(backend_summary["tracker_entries"]),
            "runs": str(backend_summary["runs"]),
            "artifacts": str(backend_summary["artifacts"]),
            "logs": str(backend_summary["logs"]),
        },
        artifact_metadata_persistent=bool(backend_summary["artifact_metadata_persistent"]),
        synthetic_debug_enabled=backend_api_app._synthetic_debug_mode_enabled(),
        recent_failed_runs=[
            backend_api_app._to_run_list_item(item)
            for item in backend_api_app._filter_visible_runs(failed_rows)[:5]
        ],
        latest_reports=latest_reports,
        active_report_jobs=active_jobs,
    )
