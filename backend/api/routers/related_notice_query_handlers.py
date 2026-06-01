from __future__ import annotations

from typing import Any

from backend.api.routers import related_notice_query_support as support
from backend.services.related_notice_collect_backend import build_related_notice_collect_queries as _build_related_notice_collect_queries_impl
from backend.services.related_notice_collect_backend import build_related_notice_collect_recipes as _build_related_notice_collect_recipes_impl
from backend.services.related_notice_collect_backend import build_related_notice_search_window as _build_related_notice_search_window_impl
from backend.services.related_notice_collect_backend import coerce_related_notice_limit as _coerce_related_notice_limit_impl


def _build_related_notice_search_window(project: dict[str, Any]) -> tuple[str, str]:
    app_module = support._app_module()
    return _build_related_notice_search_window_impl(
        project,
        collect_all_runs_fn=app_module._collect_all_runs,
        parse_yyyymmdd_fn=app_module._parse_yyyymmdd,
        format_yyyymmdd_fn=app_module._format_yyyymmdd,
        now_fn=app_module.datetime.now,
    )


def _coerce_related_notice_limit(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    return _coerce_related_notice_limit_impl(value, default=default, minimum=minimum, maximum=maximum)


def _build_related_notice_collect_queries(
    project: dict[str, Any],
    source_runs: list[dict[str, Any]],
) -> list[str]:
    app_module = support._app_module()
    return _build_related_notice_collect_queries_impl(
        project,
        source_runs,
        build_related_notice_query_variants_fn=app_module._build_related_notice_query_variants,
        norm_text_fn=app_module._norm_text,
        collect_max_queries=app_module.RELATED_NOTICE_COLLECT_MAX_QUERIES,
    )


def _build_related_notice_collect_recipes(project: dict[str, Any]) -> list[dict[str, Any]]:
    app_module = support._app_module()
    source_runs = app_module._project_source_runs(project)
    return _build_related_notice_collect_recipes_impl(
        project,
        source_runs=source_runs,
        build_related_notice_search_window_fn=app_module._build_related_notice_search_window,
        build_related_notice_query_variants_fn=app_module._build_related_notice_query_variants,
        norm_text_fn=app_module._norm_text,
        collect_max_queries=app_module.RELATED_NOTICE_COLLECT_MAX_QUERIES,
        default_rows_per_page=app_module.RELATED_NOTICE_LIVE_ROWS_PER_PAGE,
        default_max_pages=app_module.RELATED_NOTICE_LIVE_MAX_PAGES,
    )
