from __future__ import annotations

import threading
from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import UUID
from unittest.mock import Mock

from backend.api.schemas import TrackerMissingReportItem
from backend.api.schemas import TrackerMissingReportSummary
from backend.api.support import tracker_read_export_runtime
from backend.api.support import tracker_read_support_runtime
from backend.api.support.run_support import _utc_now
from backend.api.support.runtime_common import _get_artifact_repository
from backend.api.support.runtime_common import _get_tracker_repository
from backend.api.support.runtime_common import _repository_error
from backend.api.support.runtime_common import _validation_error
from backend.api.support.sales_support import _resolve_sales_actor as _resolve_sales_actor_impl
from backend.api.support.sales_support import _record_download_audit_log as _record_download_audit_log_impl
from backend.api.support.tracker_support import _to_tracker_entry_model
from backend.api.support.tracker_support import _to_tracker_entry_summary_model
from backend.phase1_defaults import load_phase1_identity
from backend.repositories import ArtifactRepositoryConfigError
from backend.repositories import ArtifactRepositoryError
from backend.repositories import TrackerEntrySnapshotRepositoryConfigError
from backend.repositories import get_tracker_entry_snapshot_repository
from backend.repositories.tracker_entries import tracker_entry_matches_region
from backend.repositories.tracker_entries import tracker_entry_matches_title_visibility
from backend.services.api_response_model_backend import model_to_json_dict as _model_to_json_dict_impl
from backend.services.artifact_files import TRACKING_EXPORT_FIELDNAMES
from backend.services.artifact_files import build_tracking_download_workbook_bytes as _build_tracking_download_workbook_bytes_impl
from backend.services.project_dashboard_backend import annotate_tracker_entries_with_opening_dates as _annotate_tracker_entries_with_opening_dates_impl
from backend.services.project_dashboard_backend import annotate_tracker_entries_with_project_refs as _annotate_tracker_entries_with_project_refs_impl
from backend.services.project_dashboard_backend import coerce_uuid_or_none as _coerce_uuid_or_none_impl
from backend.services.project_dashboard_backend import derive_tracker_entry_bid_identity as _derive_tracker_entry_bid_identity_dashboard_impl
from backend.services.project_dashboard_backend import derive_tracker_entry_project_identity as _derive_tracker_entry_project_identity_impl
from backend.services.project_dashboard_backend import normalize_tracker_bid_ord as _normalize_tracker_bid_ord_impl
from backend.services import related_notice_read_model_backend as _related_notice_read_model_backend
from backend.services.related_notice_query_runtime import _better_project_label
from backend.services.related_notice_query_runtime import _norm_text
from backend.services.related_notice_query_runtime import _project_match_key
from backend.services.related_notice_query_runtime import _select_project_search_name
from backend.services.tracker_diagnostic_backend import annotate_tracker_entries_with_field_diagnostics as _annotate_tracker_entries_with_field_diagnostics_impl
from backend.services.tracker_diagnostic_backend import build_tracker_entry_field_diagnostics as _build_tracker_entry_field_diagnostics_impl
from backend.services.tracker_diagnostic_backend import build_tracker_missing_report as _build_tracker_missing_report_impl
from backend.services.tracker_diagnostic_backend import build_tracker_field_diagnostic
from backend.services.tracker_diagnostic_backend import classify_tracker_missing_field as _classify_tracker_missing_field_impl
from backend.services.tracker_diagnostic_backend import flatten_tracker_missing_report_rows as _flatten_tracker_missing_report_rows_impl
from backend.services.tracker_diagnostic_backend import humanize_tracker_source_reason as _humanize_tracker_source_reason_impl
from backend.services.tracker_diagnostic_backend import is_tracker_value_blank as _is_tracker_value_blank_impl
from backend.services.tracker_diagnostic_backend import load_seed_rows_from_artifact_path as _load_seed_rows_from_artifact_path_impl
from backend.services.tracker_diagnostic_backend import load_winner_index_by_run as _load_winner_index_by_run_impl
from backend.services.tracker_diagnostic_backend import tracker_entry_missing_key as _tracker_entry_missing_key_impl
from backend.services.tracker_diagnostic_backend import tracker_entry_updated_key as _tracker_entry_updated_key_impl
from backend.services.tracker_entry_snapshot_backend import hydrate_tracker_entry_detail_row as _hydrate_tracker_entry_detail_row_impl
from backend.services.tracker_entry_snapshot_backend import hydrate_tracker_entry_export_rows as _hydrate_tracker_entry_export_rows_impl
from backend.services.tracker_entry_snapshot_backend import hydrate_tracker_entry_summary_rows as _hydrate_tracker_entry_summary_rows_impl
from backend.services.tracker_entry_snapshot_backend import is_tracker_entry_snapshot_fresh as _is_tracker_entry_snapshot_fresh_impl
from backend.services.tracker_entry_snapshot_backend import load_tracker_entry_snapshot_map as _load_tracker_entry_snapshot_map_impl
from backend.services.tracker_entry_snapshot_backend import materialize_tracker_entry_snapshot_views as _materialize_tracker_entry_snapshot_views_impl
from backend.services.tracker_entry_snapshot_backend import normalize_tracker_entry_presentation as _normalize_tracker_entry_presentation_impl
from backend.services.tracker_entry_snapshot_backend import normalize_tracker_rows_for_presentation as _normalize_tracker_rows_for_presentation_impl
from backend.services.tracker_entry_snapshot_backend import upsert_tracker_entry_snapshots_best_effort as _upsert_tracker_entry_snapshots_best_effort_impl
from backend.services.tracker_export_workbook_backend import build_tracker_export_workbook_cache_key as _build_tracker_export_workbook_cache_key_impl
from backend.services.tracker_export_workbook_backend import can_cache_tracker_export_workbook as _can_cache_tracker_export_workbook_impl
from backend.services.tracker_export_workbook_backend import get_or_build_cached_tracker_export_workbook_bytes as _get_or_build_cached_tracker_export_workbook_bytes_impl
from backend.services.tracker_export_workbook_backend import warm_default_user_tracker_export_workbook as _warm_default_user_tracker_export_workbook_impl
from backend.services.tracker_field_provenance import TRACKER_MISSING_REASON_EXPLAINERS

PROJECT_NAMESPACE = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
TRACKER_MISSING_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("demand_contact", "연락처", "demand_contact_source"),
    ("architect_office", "당선사", "architect_office_source"),
    ("gross_area_scale", "연면적", "gross_area_scale_source"),
)
TRACKER_DIAGNOSTIC_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("architect_office", "당선사", "architect_office_source"),
    ("gross_area_scale", "연면적", "gross_area_scale_source"),
    ("construction_cost", "공사비", "notice_construction_cost_source"),
    ("demand_contact", "연락처", "demand_contact_source"),
)
_TRACKER_GLOBAL_ROWS_CACHE_LOCK = threading.Lock()
_TRACKER_GLOBAL_ROWS_CACHE: tuple[float, list[dict[str, Any]]] | None = None
_TRACKER_GLOBAL_ROWS_CACHE_BUILD_EVENT: threading.Event | None = None
_TRACKER_GLOBAL_ROWS_CACHE_SERIAL = 0
TRACKER_GLOBAL_ROWS_CACHE_TTL_SEC = 300.0
TRACKER_GLOBAL_ROWS_CACHE_WAIT_TIMEOUT_SEC = 90.0
_TRACKER_EXPORT_WORKBOOK_CACHE_LOCK = threading.Lock()
_TRACKER_EXPORT_WORKBOOK_CACHE: dict[str, tuple[float, bytes]] = {}
_TRACKER_EXPORT_WORKBOOK_CACHE_BUILD_EVENTS: dict[str, threading.Event] = {}
_TRACKER_EXPORT_WORKBOOK_CACHE_SERIAL = 0
TRACKER_EXPORT_WORKBOOK_CACHE_TTL_SEC = 900.0
TRACKER_EXPORT_WORKBOOK_CACHE_WAIT_TIMEOUT_SEC = 90.0
TRACKER_EXPORT_WORKBOOK_CACHE_MAX_ENTRIES = 32


def _set_global_rows_cache(value: tuple[float, list[dict[str, Any]]] | None) -> None:
    global _TRACKER_GLOBAL_ROWS_CACHE; _TRACKER_GLOBAL_ROWS_CACHE = value
def _set_global_rows_cache_build_event(value: threading.Event | None) -> None:
    global _TRACKER_GLOBAL_ROWS_CACHE_BUILD_EVENT; _TRACKER_GLOBAL_ROWS_CACHE_BUILD_EVENT = value
def _increment_global_rows_cache_serial() -> None:
    global _TRACKER_GLOBAL_ROWS_CACHE_SERIAL; _TRACKER_GLOBAL_ROWS_CACHE_SERIAL += 1
def _increment_tracker_export_workbook_cache_serial() -> None:
    global _TRACKER_EXPORT_WORKBOOK_CACHE_SERIAL; _TRACKER_EXPORT_WORKBOOK_CACHE_SERIAL += 1


def _app_module():
    from backend.api import app as app_module

    return app_module


def _app_mock(name: str) -> Mock | None:
    value = getattr(_app_module(), name, None)
    return value if isinstance(value, Mock) else None


def _app_override(name: str, original: Any) -> Any | None:
    value = getattr(_app_module(), name, None)
    if value is None or value is original:
        return None
    return value


def _app_dependency(name: str, fallback: Any) -> Any:
    return getattr(_app_module(), name, fallback)


def _bad_request(message: str) -> None:
    _validation_error(message)


def _resolve_sales_actor(request: Any) -> Any:
    return _resolve_sales_actor_impl(request)


def _record_download_audit_log(**kwargs: Any) -> Any:
    kwargs.pop("get_download_audit_log_repository", None)
    return _record_download_audit_log_impl(**kwargs)


def _resolve_request_organization_id(request: Any) -> UUID:
    return _app_module()._resolve_request_organization_id(request)


def _load_artifact_file_helpers() -> Any:
    return _app_module()._load_artifact_file_helpers()


def _load_notice_view_helpers() -> Any:
    return _app_module()._load_notice_view_helpers()


def _load_openpyxl_workbook_class() -> Any:
    return _app_module()._load_openpyxl_workbook_class()


def _derive_tracker_entry_bid_identity(entry: dict[str, Any]) -> tuple[str, str]:
    return _derive_tracker_entry_bid_identity_dashboard_impl(
        entry,
        normalize_tracker_bid_ord_fn=_normalize_tracker_bid_ord,
    )


def _tracker_entry_missing_key(entry: dict[str, Any]) -> tuple[str, str, str]:
    return _tracker_entry_missing_key_impl(entry)


def _tracker_entry_updated_key(entry: dict[str, Any]) -> tuple[str, str]:
    return _tracker_entry_updated_key_impl(entry)


def _is_tracker_value_blank(value: Any) -> bool:
    return _is_tracker_value_blank_impl(value)


def _humanize_tracker_source_reason(field_key: str, winner_row: dict[str, str] | None, source_field_name: str) -> str:
    return _humanize_tracker_source_reason_impl(
        field_key=field_key,
        winner_row=winner_row,
        source_field_name=source_field_name,
    )


def _classify_tracker_missing_field(
    *,
    field_key: str,
    project_name: str,
    winner_row: dict[str, str] | None,
    source_field_name: str,
) -> tuple[str, str]:
    return _classify_tracker_missing_field_impl(
        field_key=field_key,
        project_name=project_name,
        winner_row=winner_row,
        source_field_name=source_field_name,
    )


def _build_tracker_entry_field_diagnostics(entry: dict[str, Any], winner_row: dict[str, str] | None) -> list[dict[str, str]]:
    return _build_tracker_entry_field_diagnostics_impl(
        entry,
        winner_row,
        field_specs=TRACKER_DIAGNOSTIC_FIELD_SPECS,
    )


def _select_tracker_entry_source_notice_row(entry: dict[str, Any]) -> dict[str, str] | None:
    load_notice_seed_row_by_bid_fn = _app_dependency(
        "load_notice_seed_row_by_bid",
        _load_notice_view_helpers()["load_notice_seed_row_by_bid"],
    )
    return _related_notice_read_model_backend._select_tracker_entry_source_notice_row(
        entry,
        get_artifact_repository_fn=_app_dependency("_get_artifact_repository", _get_artifact_repository),
        load_notice_seed_row_by_bid_fn=load_notice_seed_row_by_bid_fn,
        coerce_uuid_or_none_fn=_coerce_uuid_or_none,
        derive_tracker_entry_bid_identity_fn=_derive_tracker_entry_bid_identity,
        normalize_tracker_bid_ord_fn=_normalize_tracker_bid_ord,
        load_seed_rows_from_artifact_path_fn=_load_seed_rows_from_artifact_path,
        repository_error_fn=_repository_error,
    )


def _normalize_tracker_bid_ord(value: Any) -> str:
    return _normalize_tracker_bid_ord_impl(value)


def _coerce_uuid_or_none(value: Any) -> UUID | None:
    return _coerce_uuid_or_none_impl(value)


def _parse_iso_datetime(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalize_tracker_entry_presentation(
    entry: dict[str, Any],
    *,
    winner_row: dict[str, str] | None,
) -> dict[str, Any]:
    return _normalize_tracker_entry_presentation_impl(entry, winner_row=winner_row)


def _derive_tracker_entry_project_identity(entry: dict[str, Any]) -> tuple[str, str, str]:
    return _derive_tracker_entry_project_identity_impl(
        entry,
        select_project_search_name=_select_project_search_name,
        project_match_key=_project_match_key,
    )


def _get_tracker_entry_snapshot_repository():
    try:
        return get_tracker_entry_snapshot_repository()
    except TrackerEntrySnapshotRepositoryConfigError as exc:
        _repository_error(str(exc))


def _load_seed_rows_from_artifact_path(storage_path: str) -> list[dict[str, str]]: return _load_seed_rows_from_artifact_path_impl(storage_path)
def _load_winner_index_by_run(run_id: UUID) -> tuple[dict[tuple[str, str, str], dict[str, str]], dict[tuple[str, str], dict[str, str]]]: return _load_winner_index_by_run_impl(run_id=run_id, get_artifact_repository=_get_artifact_repository)


def _annotate_tracker_entries_with_field_diagnostics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _annotate_tracker_entries_with_field_diagnostics_impl(
        rows,
        load_winner_index_by_run_fn=_app_dependency("_load_winner_index_by_run", _load_winner_index_by_run),
        coerce_uuid_or_none=_coerce_uuid_or_none,
        field_specs=TRACKER_DIAGNOSTIC_FIELD_SPECS,
        build_tracker_field_diagnostic_fn=build_tracker_field_diagnostic,
    )


def _annotate_tracker_entries_with_project_refs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    override = _app_override(
        "_annotate_tracker_entries_with_project_refs",
        _ANNOTATE_TRACKER_ENTRIES_WITH_PROJECT_REFS_ORIGINAL,
    )
    if override is not None:
        return override(rows)
    return _annotate_tracker_entries_with_project_refs_impl(
        rows,
        derive_tracker_entry_project_identity_fn=_derive_tracker_entry_project_identity,
        project_namespace=PROJECT_NAMESPACE,
    )


def _annotate_tracker_entries_with_opening_dates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    override = _app_override(
        "_annotate_tracker_entries_with_opening_dates",
        _ANNOTATE_TRACKER_ENTRIES_WITH_OPENING_DATES_ORIGINAL,
    )
    if override is not None:
        return override(rows)
    return _annotate_tracker_entries_with_opening_dates_impl(
        rows,
        get_artifact_repository=_app_dependency("_get_artifact_repository", _get_artifact_repository),
        artifact_repository_error_types=(ArtifactRepositoryConfigError, ArtifactRepositoryError),
        load_seed_rows_from_artifact_path=_app_dependency(
            "_load_seed_rows_from_artifact_path",
            _load_seed_rows_from_artifact_path,
        ),
        coerce_uuid_or_none_fn=_coerce_uuid_or_none,
        normalize_tracker_bid_ord_fn=_normalize_tracker_bid_ord,
    )


def _normalize_tracker_rows_for_presentation(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    override = _app_override(
        "_normalize_tracker_rows_for_presentation",
        _NORMALIZE_TRACKER_ROWS_FOR_PRESENTATION_ORIGINAL,
    )
    if override is not None:
        return override(rows)
    return _normalize_tracker_rows_for_presentation_impl(
        rows,
        lookup_winner_row_for_entry_fn=_lookup_winner_row_for_entry,
    )


def _lookup_winner_row_for_entry(
    entry: dict[str, Any],
    cache: dict[UUID, tuple[dict[tuple[str, str, str], dict[str, str]], dict[tuple[str, str], dict[str, str]]]],
) -> dict[str, str] | None:
    from backend.services.tracker_diagnostic_backend import lookup_winner_row_for_entry as _lookup_winner_row_for_entry_impl

    return _lookup_winner_row_for_entry_impl(
        entry,
        cache,
        load_winner_index_by_run_fn=_load_winner_index_by_run,
        coerce_uuid_or_none=_coerce_uuid_or_none,
    )


def _materialize_tracker_entry_snapshot_views(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return _materialize_tracker_entry_snapshot_views_impl(
        rows,
        annotate_tracker_entries_with_project_refs_fn=_annotate_tracker_entries_with_project_refs,
        annotate_tracker_entries_with_opening_dates_fn=_annotate_tracker_entries_with_opening_dates,
        annotate_tracker_entries_with_field_diagnostics_fn=_annotate_tracker_entries_with_field_diagnostics,
        normalize_tracker_rows_for_presentation_fn=_normalize_tracker_rows_for_presentation,
        coerce_uuid_or_none_fn=_coerce_uuid_or_none,
        model_to_json_dict_fn=_model_to_json_dict_impl,
        to_tracker_entry_summary_model_fn=_to_tracker_entry_summary_model,
        to_tracker_entry_model_fn=_to_tracker_entry_model,
        tracking_export_fieldnames=TRACKING_EXPORT_FIELDNAMES,
        utc_now_fn=_utc_now,
    )


def _is_tracker_entry_snapshot_fresh(snapshot: dict[str, Any], row: dict[str, Any]) -> bool:
    return _is_tracker_entry_snapshot_fresh_impl(
        snapshot,
        row,
        parse_iso_datetime_fn=_parse_iso_datetime,
    )


def _load_tracker_entry_snapshot_map(
    *,
    organization_id: UUID,
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return _load_tracker_entry_snapshot_map_impl(
        organization_id=organization_id,
        rows=rows,
        coerce_uuid_or_none_fn=_coerce_uuid_or_none,
        get_tracker_entry_snapshot_repository_fn=_get_tracker_entry_snapshot_repository,
    )


def _upsert_tracker_entry_snapshots_best_effort(
    *,
    organization_id: UUID,
    rows: list[dict[str, Any]],
    materialized: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    return _upsert_tracker_entry_snapshots_best_effort_impl(
        organization_id=organization_id,
        rows=rows,
        materialized=materialized,
        get_tracker_entry_snapshot_repository_fn=_get_tracker_entry_snapshot_repository,
        materialize_tracker_entry_snapshot_views_fn=_materialize_tracker_entry_snapshot_views,
    )


def _hydrate_tracker_entry_summary_rows(
    *,
    organization_id: UUID,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    mock = _app_mock("_hydrate_tracker_entry_summary_rows")
    if mock is not None:
        return mock(organization_id=organization_id, rows=rows)
    return _hydrate_tracker_entry_summary_rows_impl(
        organization_id=organization_id,
        rows=rows,
        load_tracker_entry_snapshot_map_fn=_load_tracker_entry_snapshot_map,
        is_tracker_entry_snapshot_fresh_fn=_is_tracker_entry_snapshot_fresh,
        upsert_tracker_entry_snapshots_best_effort_fn=_upsert_tracker_entry_snapshots_best_effort,
    )


def _hydrate_tracker_entry_export_rows(
    *,
    organization_id: UUID,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return _hydrate_tracker_entry_export_rows_impl(
        organization_id=organization_id,
        rows=rows,
        load_tracker_entry_snapshot_map_fn=_load_tracker_entry_snapshot_map,
        is_tracker_entry_snapshot_fresh_fn=_is_tracker_entry_snapshot_fresh,
        upsert_tracker_entry_snapshots_best_effort_fn=_upsert_tracker_entry_snapshots_best_effort,
    )


def _hydrate_tracker_entry_detail_row(
    *,
    organization_id: UUID,
    row: dict[str, Any],
) -> dict[str, Any]:
    return _hydrate_tracker_entry_detail_row_impl(
        organization_id=organization_id,
        row=row,
        load_tracker_entry_snapshot_map_fn=_load_tracker_entry_snapshot_map,
        is_tracker_entry_snapshot_fresh_fn=_is_tracker_entry_snapshot_fresh,
        upsert_tracker_entry_snapshots_best_effort_fn=_upsert_tracker_entry_snapshots_best_effort,
    )


def _tracker_row_merge_score(row: dict[str, Any]) -> tuple[int, int, int, int]:
    return tracker_read_support_runtime._tracker_row_merge_score(row)


def _tracker_row_merge_identity(row: dict[str, Any]) -> tuple[str, str, str]:
    return tracker_read_support_runtime._tracker_row_merge_identity(
        row,
        normalize_tracker_bid_ord_fn=_normalize_tracker_bid_ord,
        norm_text_fn=_norm_text,
    )


def _merge_global_tracker_row_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return tracker_read_support_runtime._merge_global_tracker_row_group(
        rows,
        tracker_row_merge_score_fn=_tracker_row_merge_score,
        tracker_row_merge_identity_fn=_tracker_row_merge_identity,
        better_project_label_fn=_better_project_label,
    )


def _collapse_tracker_rows_by_project(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return tracker_read_support_runtime._collapse_tracker_rows_by_project(
        rows,
        derive_tracker_entry_project_identity_fn=_derive_tracker_entry_project_identity,
        norm_text_fn=_norm_text,
        merge_global_tracker_row_group_fn=_merge_global_tracker_row_group,
    )


def _filter_tracker_rows_for_global_scope(
    rows: list[dict[str, Any]],
    *,
    q: str,
    region: str,
    exclude_auxiliary_titles: bool,
    edited_only: bool,
) -> list[dict[str, Any]]:
    mock = _app_mock("_filter_tracker_rows_for_global_scope")
    if mock is not None:
        return mock(
            rows,
            q=q,
            region=region,
            exclude_auxiliary_titles=exclude_auxiliary_titles,
            edited_only=edited_only,
        )
    return tracker_read_support_runtime._filter_tracker_rows_for_global_scope(
        rows,
        q=q,
        region=region,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        edited_only=edited_only,
        norm_text_fn=_norm_text,
        tracker_entry_matches_title_visibility_fn=tracker_entry_matches_title_visibility,
        tracker_entry_matches_region_fn=tracker_entry_matches_region,
    )


def _load_all_tracker_entries_for_export(
    *,
    q: str,
    region: str,
    exclude_auxiliary_titles: bool,
    edited_only: bool,
    source_run_id: UUID | None,
    source_tracker_run_id: UUID | None,
    sheet_name: str,
    section_name: str,
) -> list[dict[str, Any]]:
    return tracker_read_support_runtime._load_all_tracker_entries_for_export(
        q=q,
        region=region,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        edited_only=edited_only,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        get_tracker_repository_fn=_get_tracker_repository,
        load_phase1_identity_fn=load_phase1_identity,
        hydrate_tracker_entry_export_rows_fn=_hydrate_tracker_entry_export_rows,
        repository_error_fn=_repository_error,
    )


def _load_all_tracker_entries_for_global_summary() -> list[dict[str, Any]]:
    override = _app_override(
        "_load_all_tracker_entries_for_global_summary",
        _LOAD_ALL_TRACKER_ENTRIES_FOR_GLOBAL_SUMMARY_ORIGINAL,
    )
    if override is not None:
        return override()
    return tracker_read_support_runtime._load_all_tracker_entries_for_global_summary(
        get_tracker_repository_fn=_app_dependency("_get_tracker_repository", _get_tracker_repository),
        load_phase1_identity_fn=load_phase1_identity,
        hydrate_tracker_entry_summary_rows_fn=_hydrate_tracker_entry_summary_rows,
        repository_error_fn=_repository_error,
    )


def _is_global_tracker_scope(
    *,
    source_run_id: UUID | None,
    source_tracker_run_id: UUID | None,
    sheet_name: str,
    section_name: str,
) -> bool:
    return tracker_read_support_runtime._is_global_tracker_scope(
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        app_mock=_app_mock,
    )


def _load_global_tracker_rows(*, force_refresh: bool = False) -> list[dict[str, Any]]:
    return tracker_read_support_runtime._load_global_tracker_rows(
        force_refresh=force_refresh,
        app_mock=_app_mock,
        cache_lock=_TRACKER_GLOBAL_ROWS_CACHE_LOCK,
        cache_state_getter=lambda: _TRACKER_GLOBAL_ROWS_CACHE,
        cache_state_setter=lambda value: _set_global_rows_cache(value),
        cache_build_event_getter=lambda: _TRACKER_GLOBAL_ROWS_CACHE_BUILD_EVENT,
        cache_build_event_setter=lambda value: _set_global_rows_cache_build_event(value),
        cache_serial_getter=lambda: _TRACKER_GLOBAL_ROWS_CACHE_SERIAL,
        cache_ttl_sec=TRACKER_GLOBAL_ROWS_CACHE_TTL_SEC,
        cache_wait_timeout_sec=TRACKER_GLOBAL_ROWS_CACHE_WAIT_TIMEOUT_SEC,
        load_all_tracker_entries_for_global_summary_fn=_load_all_tracker_entries_for_global_summary,
        collapse_tracker_rows_by_project_fn=_collapse_tracker_rows_by_project,
    )


def _clear_global_tracker_rows_cache() -> None:
    tracker_read_support_runtime._clear_global_tracker_rows_cache(
        cache_lock=_TRACKER_GLOBAL_ROWS_CACHE_LOCK,
        clear_cache_state=lambda: _set_global_rows_cache(None),
        increment_global_serial=_increment_global_rows_cache_serial,
        workbook_cache_lock=_TRACKER_EXPORT_WORKBOOK_CACHE_LOCK,
        clear_workbook_cache=_TRACKER_EXPORT_WORKBOOK_CACHE.clear,
        increment_workbook_serial=_increment_tracker_export_workbook_cache_serial,
    )


def _list_tracker_entries_for_export(
    *,
    q: str,
    region: str,
    exclude_auxiliary_titles: bool,
    edited_only: bool,
    source_run_id: UUID | None,
    source_tracker_run_id: UUID | None,
    sheet_name: str,
    section_name: str,
) -> list[dict[str, Any]]:
    return tracker_read_support_runtime._list_tracker_entries_for_export(
        q=q,
        region=region,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        edited_only=edited_only,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        is_global_tracker_scope_fn=_is_global_tracker_scope,
        filter_tracker_rows_for_global_scope_fn=_filter_tracker_rows_for_global_scope,
        load_global_tracker_rows_fn=_load_global_tracker_rows,
        normalize_tracker_rows_for_presentation_fn=_normalize_tracker_rows_for_presentation,
        load_all_tracker_entries_for_export_fn=_load_all_tracker_entries_for_export,
    )


def _can_cache_tracker_export_workbook(
    *,
    format: str,
    q: str,
    region: str,
    edited_only: bool,
    source_run_id: UUID | None,
    source_tracker_run_id: UUID | None,
    sheet_name: str,
    section_name: str,
) -> bool:
    return tracker_read_support_runtime._can_cache_tracker_export_workbook(
        format=format,
        q=q,
        region=region,
        edited_only=edited_only,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        is_global_tracker_scope_fn=_is_global_tracker_scope,
        can_cache_tracker_export_workbook_impl_fn=_can_cache_tracker_export_workbook_impl,
    )


def _build_tracker_export_workbook_cache_key(
    *,
    q: str,
    region: str,
    edited_only: bool,
    exclude_auxiliary_titles: bool,
    blank_progress_note: bool,
) -> str:
    return tracker_read_support_runtime._build_tracker_export_workbook_cache_key(
        q=q,
        region=region,
        edited_only=edited_only,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        blank_progress_note=blank_progress_note,
        build_tracker_export_workbook_cache_key_impl_fn=_build_tracker_export_workbook_cache_key_impl,
    )


def _get_or_build_cached_tracker_export_workbook_bytes(
    *,
    q: str,
    region: str,
    exclude_auxiliary_titles: bool,
    edited_only: bool,
    blank_progress_note: bool,
    source_run_id: UUID | None,
    source_tracker_run_id: UUID | None,
    sheet_name: str,
    section_name: str,
    list_tracker_entries_for_export_fn: Any = _list_tracker_entries_for_export,
    build_tracking_download_workbook_bytes_fn: Any = _build_tracking_download_workbook_bytes_impl,
    build_tracker_export_workbook_cache_key_fn: Any = _build_tracker_export_workbook_cache_key,
) -> bytes:
    return tracker_read_support_runtime._get_or_build_cached_tracker_export_workbook_bytes(
        q=q,
        region=region,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        edited_only=edited_only,
        blank_progress_note=blank_progress_note,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        cache_lock=_TRACKER_EXPORT_WORKBOOK_CACHE_LOCK,
        cache=_TRACKER_EXPORT_WORKBOOK_CACHE,
        cache_build_events=_TRACKER_EXPORT_WORKBOOK_CACHE_BUILD_EVENTS,
        cache_serial_fn=lambda: _TRACKER_EXPORT_WORKBOOK_CACHE_SERIAL,
        cache_ttl_sec=TRACKER_EXPORT_WORKBOOK_CACHE_TTL_SEC,
        cache_wait_timeout_sec=TRACKER_EXPORT_WORKBOOK_CACHE_WAIT_TIMEOUT_SEC,
        cache_max_entries=TRACKER_EXPORT_WORKBOOK_CACHE_MAX_ENTRIES,
        list_tracker_entries_for_export_fn=list_tracker_entries_for_export_fn,
        build_tracking_download_workbook_bytes_fn=build_tracking_download_workbook_bytes_fn,
        build_tracker_export_workbook_cache_key_fn=build_tracker_export_workbook_cache_key_fn,
        get_or_build_cached_tracker_export_workbook_bytes_impl_fn=_get_or_build_cached_tracker_export_workbook_bytes_impl,
    )


def _warm_default_user_tracker_export_workbook(
    *,
    get_or_build_cached_tracker_export_workbook_bytes_fn: Any = _get_or_build_cached_tracker_export_workbook_bytes,
    logger: Any | None = None,
) -> None:
    tracker_read_support_runtime._warm_default_user_tracker_export_workbook(
        get_or_build_cached_tracker_export_workbook_bytes_fn=get_or_build_cached_tracker_export_workbook_bytes_fn,
        logger=logger,
        warm_default_user_tracker_export_workbook_impl_fn=_warm_default_user_tracker_export_workbook_impl,
    )


def _warm_tracker_export_workbook_for_request(
    *,
    q: str,
    region: str,
    edited_only: bool,
    exclude_auxiliary_titles: bool,
    blank_progress_note: bool,
    source_run_id: UUID | None,
    source_tracker_run_id: UUID | None,
    sheet_name: str,
    section_name: str,
    can_cache_tracker_export_workbook_fn: Any = _can_cache_tracker_export_workbook,
    get_or_build_cached_tracker_export_workbook_bytes_fn: Any = _get_or_build_cached_tracker_export_workbook_bytes,
    logger: Any | None = None,
) -> None:
    tracker_read_support_runtime._warm_tracker_export_workbook_for_request(
        q=q,
        region=region,
        edited_only=edited_only,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        blank_progress_note=blank_progress_note,
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
        can_cache_tracker_export_workbook_fn=can_cache_tracker_export_workbook_fn,
        get_or_build_cached_tracker_export_workbook_bytes_fn=get_or_build_cached_tracker_export_workbook_bytes_fn,
        logger=logger,
    )


def _build_tracker_missing_report(
    *,
    limit: int,
    collect_all_tracker_entries_fn: Any | None = None,
    load_winner_index_by_run_fn: Any | None = None,
) -> tuple[TrackerMissingReportSummary, list[TrackerMissingReportItem]]:
    return tracker_read_export_runtime.build_tracker_missing_report(
        limit=limit,
        app_override=_app_override,
        original_override_target=_BUILD_TRACKER_MISSING_REPORT_ORIGINAL,
        collect_all_tracker_entries_fn=collect_all_tracker_entries_fn,
        load_winner_index_by_run_fn=load_winner_index_by_run_fn,
        app_dependency=_app_dependency,
        app_module=_app_module,
        default_load_winner_index_by_run_fn=_load_winner_index_by_run,
        coerce_uuid_or_none_fn=_coerce_uuid_or_none,
        tracker_missing_field_specs=TRACKER_MISSING_FIELD_SPECS,
        tracker_missing_reason_explainers=TRACKER_MISSING_REASON_EXPLAINERS,
        build_tracker_missing_report_impl_fn=_build_tracker_missing_report_impl,
    )


def _flatten_tracker_missing_report_rows(
    *,
    summary: TrackerMissingReportSummary,
    items: list[TrackerMissingReportItem],
) -> list[dict[str, Any]]:
    return tracker_read_export_runtime.flatten_tracker_missing_report_rows(
        summary=summary,
        items=items,
        flatten_tracker_missing_report_rows_impl_fn=_flatten_tracker_missing_report_rows_impl,
    )


_ANNOTATE_TRACKER_ENTRIES_WITH_PROJECT_REFS_ORIGINAL = _annotate_tracker_entries_with_project_refs
_ANNOTATE_TRACKER_ENTRIES_WITH_OPENING_DATES_ORIGINAL = _annotate_tracker_entries_with_opening_dates
_NORMALIZE_TRACKER_ROWS_FOR_PRESENTATION_ORIGINAL = _normalize_tracker_rows_for_presentation
_LOAD_ALL_TRACKER_ENTRIES_FOR_GLOBAL_SUMMARY_ORIGINAL = _load_all_tracker_entries_for_global_summary
_BUILD_TRACKER_MISSING_REPORT_ORIGINAL = _build_tracker_missing_report
