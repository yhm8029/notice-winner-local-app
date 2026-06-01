from __future__ import annotations

from typing import Any
from uuid import UUID

from backend.api.support.runtime_common import _get_tracker_repository
from backend.api.support.runtime_common import _not_found
from backend.api.support.runtime_common import _repository_error
from backend.api.support.tracker_read_support import _annotate_tracker_entries_with_opening_dates
from backend.api.support.tracker_read_support import _annotate_tracker_entries_with_project_refs
from backend.api.support.tracker_read_support import _bad_request
from backend.api.support.tracker_read_support import _flatten_tracker_missing_report_rows
from backend.api.support.tracker_read_support import _hydrate_tracker_entry_detail_row
from backend.api.support.tracker_read_support import _hydrate_tracker_entry_summary_rows
from backend.api.support.tracker_read_support import _load_notice_view_helpers
from backend.api.support.tracker_read_support import _load_openpyxl_workbook_class
from backend.api.support.tracker_read_support import _normalize_tracker_rows_for_presentation
from backend.api.support.tracker_read_support import _select_tracker_entry_source_notice_row
from backend.api.support.tracker_read_support import _warm_tracker_export_workbook_for_request
from backend.api.support.tracker_support import _to_audit_log_model
from backend.api.support.tracker_support import _to_tracker_entry_model
from backend.phase1_defaults import load_phase1_identity


def _app_module():
    from backend.api import app as app_module

    return app_module


def _dispatch_background(target: Any, *args: Any, **kwargs: Any) -> None:
    _app_module()._dispatch_background(target, *args, **kwargs)


def _is_global_tracker_scope(*args: Any, **kwargs: Any) -> Any:
    return _app_module()._is_global_tracker_scope(*args, **kwargs)


def _filter_tracker_rows_for_global_scope(*args: Any, **kwargs: Any) -> Any:
    return _app_module()._filter_tracker_rows_for_global_scope(*args, **kwargs)


def _load_global_tracker_rows(*, force_refresh: bool = False) -> Any:
    return _app_module()._load_global_tracker_rows(force_refresh=force_refresh)


def _list_tracker_entries_for_export(*args: Any, **kwargs: Any) -> Any:
    return _app_module()._list_tracker_entries_for_export(*args, **kwargs)


def _can_cache_tracker_export_workbook(*args: Any, **kwargs: Any) -> Any:
    return _app_module()._can_cache_tracker_export_workbook(*args, **kwargs)


def _get_or_build_cached_tracker_export_workbook_bytes(*args: Any, **kwargs: Any) -> Any:
    return _app_module()._get_or_build_cached_tracker_export_workbook_bytes(*args, **kwargs)


def _load_artifact_file_helpers() -> Any:
    return _app_module()._load_artifact_file_helpers()


def _resolve_sales_actor(request: Any) -> Any:
    return _app_module()._resolve_sales_actor(request)


def _record_download_audit_log(
    *,
    actor: Any,
    download_scope: str,
    download_format: str,
    source_page: str,
    file_name: str,
) -> None:
    _app_module()._record_download_audit_log(
        actor=actor,
        download_scope=download_scope,
        download_format=download_format,
        source_page=source_page,
        file_name=file_name,
    )


def _build_tracker_missing_report(*, limit: int) -> Any:
    return _app_module()._build_tracker_missing_report(limit=limit)


def _to_tracker_entry_summary_model(row: dict[str, Any]) -> Any:
    return _app_module()._to_tracker_entry_summary_model(row)


def _resolve_request_organization_id(request: Any) -> UUID:
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context is not None and auth_context.organization_id is not None:
        return auth_context.organization_id
    return load_phase1_identity().organization_id
