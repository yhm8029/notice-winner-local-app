from __future__ import annotations

import threading
import time
from typing import Any
from uuid import UUID

from backend.api.schemas import ProjectItem
from backend.api.support.run_support import _utc_now
from backend.api.support.runtime_common import _backend_api_app
from backend.api.support.tracker_read_support import PROJECT_NAMESPACE
from backend.api.support.tracker_read_support import _normalize_tracker_bid_ord
from backend.services.project_dashboard_backend import build_project_aggregate_from_tracker_entries as _build_project_aggregate_from_tracker_entries_impl
from backend.services.project_dashboard_backend import build_project_aggregates as _build_project_aggregates_impl
from backend.services.project_dashboard_backend import build_projects_page as _build_projects_page_impl
from backend.services.project_dashboard_backend import derive_tracker_entry_project_identity as _derive_tracker_entry_project_identity_impl
from backend.services.project_dashboard_backend import to_project_item as _to_project_item_impl
from backend.services.project_dashboard_backend import upsert_project_aggregate_from_tracker_entry as _upsert_project_aggregate_from_tracker_entry_impl
from backend.services.related_notice_query_runtime import _better_project_label
from backend.services.related_notice_query_runtime import _better_project_search_name
from backend.services.related_notice_query_runtime import _is_generic_project_term
from backend.services.related_notice_query_runtime import _norm_text
from backend.services.related_notice_query_runtime import _project_match_key
from backend.services.related_notice_query_runtime import _project_search_name
from backend.services.related_notice_query_runtime import _select_project_search_name
from backend.services.related_notice_query_runtime import _slugify

_PROJECT_AGGREGATES_CACHE_LOCK = threading.Lock()
_PROJECT_AGGREGATES_CACHE_TTL_SEC = 300.0
_PROJECT_AGGREGATES_CACHE: tuple[float, dict[str, dict[str, Any]]] | None = None
_PROJECT_AGGREGATES_WARM_LOCK = threading.Lock()
_PROJECT_AGGREGATES_WARM_ACTIVE = False


def _module_override(name: str, original: Any) -> Any | None:
    value = globals().get(name)
    if value is None or value is original:
        return None
    return value


def _clear_project_aggregates_cache() -> None:
    global _PROJECT_AGGREGATES_CACHE
    global _PROJECT_AGGREGATES_WARM_ACTIVE
    with _PROJECT_AGGREGATES_CACHE_LOCK:
        _PROJECT_AGGREGATES_CACHE = None
    with _PROJECT_AGGREGATES_WARM_LOCK:
        _PROJECT_AGGREGATES_WARM_ACTIVE = False


def _queue_project_aggregates_cache_warm() -> None:
    global _PROJECT_AGGREGATES_WARM_ACTIVE
    with _PROJECT_AGGREGATES_CACHE_LOCK:
        cached = _PROJECT_AGGREGATES_CACHE
        if cached is not None and cached[0] > time.monotonic():
            return
    with _PROJECT_AGGREGATES_WARM_LOCK:
        if _PROJECT_AGGREGATES_WARM_ACTIVE:
            return
        _PROJECT_AGGREGATES_WARM_ACTIVE = True

    def _run() -> None:
        global _PROJECT_AGGREGATES_WARM_ACTIVE
        try:
            _build_project_aggregates()
        finally:
            with _PROJECT_AGGREGATES_WARM_LOCK:
                _PROJECT_AGGREGATES_WARM_ACTIVE = False

    worker = _backend_api_app.threading.Thread(target=_run, daemon=True)
    worker.start()


def _build_project_aggregates() -> dict[str, dict[str, Any]]:
    global _PROJECT_AGGREGATES_CACHE
    backend_api_app = _backend_api_app
    now = time.monotonic()
    with _PROJECT_AGGREGATES_CACHE_LOCK:
        cached = _PROJECT_AGGREGATES_CACHE
        if cached is not None:
            expires_at, payload = cached
            if expires_at > now:
                return payload

    payload = _build_project_aggregates_impl(
        collect_all_runs=backend_api_app._collect_all_runs,
        collect_all_tracker_entries=backend_api_app._collect_all_tracker_entries,
        is_project_tracker_run_type=backend_api_app._is_project_tracker_run_type,
        project_search_name=_project_search_name,
        is_generic_project_term=_is_generic_project_term,
        project_match_key=_project_match_key,
        normalize_tracker_bid_ord_fn=_normalize_tracker_bid_ord,
        upsert_project_aggregate_from_tracker_entry_fn=backend_api_app._upsert_project_aggregate_from_tracker_entry,
        slugify=_slugify,
        better_project_label=_better_project_label,
        better_project_search_name=_better_project_search_name,
        project_namespace=PROJECT_NAMESPACE,
        utc_now=_utc_now,
    )
    with _PROJECT_AGGREGATES_CACHE_LOCK:
        _PROJECT_AGGREGATES_CACHE = (time.monotonic() + _PROJECT_AGGREGATES_CACHE_TTL_SEC, payload)
    return payload


def _derive_tracker_entry_project_identity(entry: dict[str, Any]) -> tuple[str, str, str]:
    return _derive_tracker_entry_project_identity_impl(
        entry,
        select_project_search_name=_select_project_search_name,
        project_match_key=_project_match_key,
    )


def _upsert_project_aggregate_from_tracker_entry(
    aggregates: dict[str, dict[str, Any]],
    entry: dict[str, Any],
) -> None:
    _upsert_project_aggregate_from_tracker_entry_impl(
        aggregates,
        entry,
        project_namespace=PROJECT_NAMESPACE,
        derive_tracker_entry_project_identity_fn=_derive_tracker_entry_project_identity,
        normalize_tracker_bid_ord_fn=_normalize_tracker_bid_ord,
        slugify=_slugify,
        better_project_label=_better_project_label,
        better_project_search_name=_better_project_search_name,
        utc_now=_utc_now,
    )


def _build_project_aggregate_from_tracker_entries(project_id: UUID) -> dict[str, Any] | None:
    backend_api_app = _backend_api_app
    return _build_project_aggregate_from_tracker_entries_impl(
        project_id,
        collect_all_tracker_entries=backend_api_app._collect_all_tracker_entries,
        upsert_project_aggregate_from_tracker_entry_fn=_upsert_project_aggregate_from_tracker_entry,
    )


def _to_project_item(item: dict[str, Any]) -> ProjectItem:
    return _to_project_item_impl(item, project_item_cls=ProjectItem, utc_now=_utc_now)


def _build_projects_page(*, page: int, page_size: int, q: str) -> tuple[list[ProjectItem], int]:
    override = _module_override("_build_projects_page", _BUILD_PROJECTS_PAGE_ORIGINAL)
    if override is not None:
        return override(page=page, page_size=page_size, q=q)
    return _build_projects_page_impl(
        page=page,
        page_size=page_size,
        q=q,
        build_project_aggregates_fn=_build_project_aggregates,
        norm_text=_norm_text,
        to_project_item_fn=_to_project_item,
    )


_BUILD_PROJECTS_PAGE_ORIGINAL = _build_projects_page
