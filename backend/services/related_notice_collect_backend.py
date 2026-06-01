from __future__ import annotations

from datetime import datetime
from typing import Any


def format_yyyymmdd(value: datetime) -> str:
    return value.strftime("%Y%m%d")


def coerce_related_notice_limit(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(str(value or "").strip() or str(default))
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def build_related_notice_search_window(
    project: dict[str, Any],
    *,
    collect_all_runs_fn: Any,
    parse_yyyymmdd_fn: Any,
    format_yyyymmdd_fn: Any = format_yyyymmdd,
    now_fn: Any = datetime.now,
) -> tuple[str, str]:
    run_map = {str(run.get("id") or ""): run for run in collect_all_runs_fn()}
    start_candidates: list[datetime] = []
    for run_id in project.get("source_json", {}).get("run_ids") or []:
        run = run_map.get(str(run_id))
        if not run:
            continue
        params = dict(run.get("params_json") or {})
        start_dt = parse_yyyymmdd_fn(str(params.get("start_date") or "").strip())
        if start_dt:
            start_candidates.append(start_dt)
    first_notice_dt = parse_yyyymmdd_fn(str(project.get("first_notice_date") or "").strip())
    if first_notice_dt:
        start_candidates.append(first_notice_dt)
    latest_notice_dt = parse_yyyymmdd_fn(str(project.get("latest_notice_date") or "").strip())
    if latest_notice_dt:
        start_candidates.append(latest_notice_dt)

    end_dt = now_fn()
    if not start_candidates:
        start_candidates.append(end_dt)

    start_dt = min(start_candidates)
    return format_yyyymmdd_fn(start_dt), format_yyyymmdd_fn(end_dt)


def build_related_notice_collect_queries(
    project: dict[str, Any],
    source_runs: list[dict[str, Any]],
    *,
    build_related_notice_query_variants_fn: Any,
    norm_text_fn: Any,
    collect_max_queries: int,
) -> list[str]:
    candidates: list[str] = []
    for run_row in source_runs:
        params = dict(run_row.get("params_json") or {})
        notice_title = str(params.get("notice_title") or "").strip()
        if notice_title:
            candidates.append(notice_title)
    candidates.extend(
        filter(
            None,
            (
                str(project.get("project_name") or "").strip(),
                str(project.get("latest_notice_title") or "").strip(),
                str(project.get("project_search_name") or "").strip(),
            ),
        )
    )

    queries: list[str] = []
    seen: set[str] = set()
    max_queries = max(1, int(collect_max_queries))
    for candidate in candidates:
        for value in build_related_notice_query_variants_fn(candidate):
            key = norm_text_fn(value)
            if not key or key in seen:
                continue
            seen.add(key)
            queries.append(value)
            if len(queries) >= max_queries:
                return queries
    return queries


def build_related_notice_collect_recipes(
    project: dict[str, Any],
    *,
    source_runs: list[dict[str, Any]],
    build_related_notice_search_window_fn: Any,
    build_related_notice_query_variants_fn: Any,
    norm_text_fn: Any,
    collect_max_queries: int,
    default_rows_per_page: int,
    default_max_pages: int,
) -> list[dict[str, Any]]:
    start_date, end_date = build_related_notice_search_window_fn(project)
    queries = build_related_notice_collect_queries(
        project,
        source_runs,
        build_related_notice_query_variants_fn=build_related_notice_query_variants_fn,
        norm_text_fn=norm_text_fn,
        collect_max_queries=collect_max_queries,
    )
    if not queries:
        return []

    rows_per_page = max(
        [
            coerce_related_notice_limit(
                dict(run_row.get("params_json") or {}).get("rows_per_page"),
                default=default_rows_per_page,
                minimum=10,
                maximum=999,
            )
            for run_row in source_runs
        ]
        or [default_rows_per_page]
    )
    max_pages = max(
        [
            coerce_related_notice_limit(
                dict(run_row.get("params_json") or {}).get("max_pages"),
                default=default_max_pages,
                minimum=1,
                maximum=15,
            )
            for run_row in source_runs
        ]
        or [default_max_pages]
    )
    return [
        {
            "start_date": start_date,
            "end_date": end_date,
            "bid_no": "",
            "notice_title": query,
            "demand_org": "",
            "rows_per_page": rows_per_page,
            "max_pages": max_pages,
            "api_scope": "all",
        }
        for query in queries
    ]
