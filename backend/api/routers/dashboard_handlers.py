from __future__ import annotations

from backend.api.routers import dashboard_support as support
from backend.api.schemas import DashboardSummaryResponse


def _app_module():
    return support._app_module()


def _get_cached_dashboard_summary() -> DashboardSummaryResponse:
    app_module = _app_module()
    now = support.time.monotonic()
    with app_module._DASHBOARD_SUMMARY_CACHE_LOCK:
        cached_entry = app_module._DASHBOARD_SUMMARY_CACHE
        if cached_entry is not None:
            expires_at, payload = cached_entry
            if expires_at > now:
                return DashboardSummaryResponse.model_validate(support._copy_response_model(payload))
            app_module._DASHBOARD_SUMMARY_CACHE = None

    summary = support._build_dashboard_summary()
    with app_module._DASHBOARD_SUMMARY_CACHE_LOCK:
        app_module._DASHBOARD_SUMMARY_CACHE = (
            support.time.monotonic() + app_module._DASHBOARD_SUMMARY_CACHE_TTL_SEC,
            support._copy_response_model(summary),
        )
    return DashboardSummaryResponse.model_validate(summary)


def _clear_dashboard_summary_cache() -> None:
    app_module = _app_module()
    with app_module._DASHBOARD_SUMMARY_CACHE_LOCK:
        app_module._DASHBOARD_SUMMARY_CACHE = None


def _build_dashboard_summary() -> DashboardSummaryResponse:
    try:
        backend_summary = support.describe_repository_backends()
    except (
        support.ArtifactRepositoryConfigError,
        support.RunLogRepositoryConfigError,
        support.RunRepositoryConfigError,
        support.TrackerEntryRepositoryConfigError,
    ) as exc:
        support._repository_error(str(exc))
    run_repository = support._get_run_repository()
    tracker_repository = support._get_tracker_repository()
    run_counts = {status_value: 0 for status_value in sorted(support.VALID_RUN_STATUSES)}
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
    except support.RunRepositoryError as exc:
        support._repository_error(str(exc))

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
    except support.TrackerEntryRepositoryError as exc:
        support._repository_error(str(exc))

    latest_reports: dict[str, object] = {}
    for report_name in support.REPORT_FILES:
        try:
            report_payload = support._load_report_payload(report_name)
            latest_reports[report_name] = {
                "available": True,
                "summary": dict(report_payload.get("summary") or {}),
            }
        except support.ApiError:
            latest_reports[report_name] = {
                "available": False,
                "summary": {},
            }

    active_jobs = [
        support.to_report_job_item(item).model_dump(mode="json")
        for item in support.list_stored_report_jobs(limit=10)
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
        synthetic_debug_enabled=support._synthetic_debug_mode_enabled(),
        recent_failed_runs=[support._to_run_list_item(item) for item in support._filter_visible_runs(failed_rows)[:5]],
        latest_reports=latest_reports,
        active_report_jobs=active_jobs,
    )
