from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import datetime
from datetime import timedelta
from typing import Any
from uuid import UUID
from uuid import uuid4
from zoneinfo import ZoneInfo

import requests

from backend.api.schemas import RelatedNoticeItem
from backend.api.schemas import RelatedNoticeListResponse
from backend.api.support.runtime_common import _backend_api_app
from backend.api.support.runtime_common import _not_found
from backend.api.support.runtime_common import _validation_error
from backend.services.notice_view_backend import build_notice_view_payload as _build_notice_view_payload_impl
from backend.services.related_notice_classification import classify_related_notice_item
from backend.services.related_notice_collect_backend import build_related_notice_collect_queries as _build_related_notice_collect_queries_impl
from backend.services.related_notice_collect_backend import build_related_notice_collect_recipes as _build_related_notice_collect_recipes_impl
from backend.services.related_notice_collect_backend import build_related_notice_search_window as _build_related_notice_search_window_impl
from backend.services.related_notice_query_runtime import RELATED_NOTICE_COLLECT_MAX_QUERIES
from backend.services.related_notice_query_runtime import RELATED_NOTICE_LIVE_DEADLINE_SEC
from backend.services.related_notice_query_runtime import RELATED_NOTICE_LIVE_MAX_COLLECTED_ROWS
from backend.services.related_notice_query_runtime import RELATED_NOTICE_LIVE_MAX_PAGES
from backend.services.related_notice_query_runtime import RELATED_NOTICE_LIVE_REQUEST_TIMEOUT_SEC
from backend.services.related_notice_query_runtime import RELATED_NOTICE_LIVE_ROWS_PER_PAGE
from backend.services.related_notice_query_runtime import RELATED_NOTICE_RECIPE_MAX_WORKERS
from backend.services.related_notice_query_runtime import _build_related_notice_query_variants
from backend.services.related_notice_query_runtime import _dedupe_related_notice_payload_items
from backend.services.related_notice_query_runtime import _norm_text
from backend.services.related_notice_query_runtime import _project_match_key
from backend.services.related_notice_query_runtime import _project_search_name
from backend.services.related_notice_query_runtime import _score_related_notice_match
from backend.services.seed_collect import collect_seed_rows_with_params
from backend.services.seed_collect import resolve_native_service_key
from backend.services.native_seed_backend import fetch_seed_rows_with_diagnostics
from backend.services.native_seed_backend import API_ENDPOINTS_SEARCH
from backend.services.native_seed_backend import _api_header as _native_api_header
from backend.services.native_seed_backend import _extract_items as _native_extract_items
from backend.services.native_seed_backend import _seed_row_from_item as _native_seed_row_from_item
from backend.services.related_notice_read_model_backend import dedupe_related_notice_rows as _dedupe_related_notice_rows_impl
from backend.services.related_notice_read_model_backend import filter_self_related_notice_payload_items as _filter_self_related_notice_payload_items_impl
from backend.services.related_notice_read_model_backend import is_related_notice_payload_entry_precomputed as _is_related_notice_payload_entry_precomputed_impl
from backend.services.related_notice_read_model_backend import precomputed_related_notice_items as _precomputed_related_notice_items_impl
from backend.services.related_notice_read_model_backend import project_source_notice_keys as _project_source_notice_keys_impl
from backend.services.related_notice_read_model_backend import project_source_runs as _project_source_runs_impl
from backend.services.related_notice_read_model_backend import seed_related_notice_items as _seed_related_notice_items_impl
from backend.services.related_notice_read_model_backend import select_project_source_notice_row as _select_project_source_notice_row_impl
from backend.services.related_notice_response_backend import get_related_notice_project_precompute_state as _get_related_notice_project_precompute_state_impl
from backend.services.related_notice_response_backend import is_related_notice_precompute_stale as _is_related_notice_precompute_stale_impl
from backend.services.related_notice_response_backend import related_notice_response_without_live as _related_notice_response_without_live_impl


def _build_project_notice_view_payload(project_id: UUID) -> dict[str, object]:
    project = _backend_api_app._get_project_aggregate(project_id)
    source_json = dict(project.get("source_json") or {})
    source_row = _select_project_source_notice_row(project)
    bid_no = str((source_row or {}).get("bid_no") or source_json.get("source_bid_no") or "").strip()
    bid_ord = str((source_row or {}).get("bid_ord") or source_json.get("source_bid_ord") or "").strip()
    notice_url = str((source_row or {}).get("bid_ntce_url") or "").strip()
    notice_detail_url = str((source_row or {}).get("bid_ntce_dtl_url") or "").strip()
    if not (notice_detail_url or notice_url or bid_no):
        _not_found(f"project notice source not found: {project_id}")
    try:
        return _build_notice_view_payload_impl(
            notice_detail_url=notice_detail_url,
            notice_url=notice_url,
            project_name=str(project.get("project_name") or "").strip(),
            bid_no=bid_no,
            bid_ord=bid_ord,
            seed_row=source_row,
        )
    except ValueError as exc:
        _validation_error(str(exc))


def _build_related_notice_search_window(project: dict[str, Any]) -> tuple[str, str]:
    backend_api_app = _backend_api_app
    return _build_related_notice_search_window_impl(
        project,
        collect_all_runs_fn=backend_api_app._collect_all_runs,
        parse_yyyymmdd_fn=backend_api_app._parse_yyyymmdd,
        format_yyyymmdd_fn=backend_api_app._format_yyyymmdd,
        now_fn=backend_api_app.datetime.now,
    )


def _build_related_notice_collect_queries(
    project: dict[str, Any],
    source_runs: list[dict[str, Any]],
) -> list[str]:
    return _build_related_notice_collect_queries_impl(
        project,
        source_runs,
        build_related_notice_query_variants_fn=_build_related_notice_query_variants,
        norm_text_fn=_norm_text,
        collect_max_queries=RELATED_NOTICE_COLLECT_MAX_QUERIES,
    )


def _build_related_notice_collect_recipes(project: dict[str, Any]) -> list[dict[str, Any]]:
    source_runs = _backend_api_app._project_source_runs(project)
    return _build_related_notice_collect_recipes_impl(
        project,
        source_runs=source_runs,
        build_related_notice_search_window_fn=_build_related_notice_search_window,
        build_related_notice_query_variants_fn=_build_related_notice_query_variants,
        norm_text_fn=_norm_text,
        collect_max_queries=RELATED_NOTICE_COLLECT_MAX_QUERIES,
        default_rows_per_page=RELATED_NOTICE_LIVE_ROWS_PER_PAGE,
        default_max_pages=RELATED_NOTICE_LIVE_MAX_PAGES,
    )


def _collect_related_notice_rows_with_debug(
    project: dict[str, Any],
    *,
    trace_id: str | None = None,
    project_id: UUID | None = None,
    progress_cb: Any | None = None,
    max_recipes: int | None = None,
    deadline_sec: float | None = None,
    request_timeout_sec: float | None = None,
    recipe_max_workers: int | None = None,
    rows_per_page: int | None = None,
    max_pages: int | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    backend_api_app = _backend_api_app
    active_deadline_sec = float(deadline_sec if deadline_sec is not None else RELATED_NOTICE_LIVE_DEADLINE_SEC)
    active_request_timeout_sec = float(
        request_timeout_sec if request_timeout_sec is not None else RELATED_NOTICE_LIVE_REQUEST_TIMEOUT_SEC
    )
    deadline = backend_api_app.time.monotonic() + active_deadline_sec
    collected: list[dict[str, str]] = []
    attempts: list[dict[str, Any]] = []
    recipes = backend_api_app._build_related_notice_collect_recipes(project)
    if max_recipes is not None:
        recipes = recipes[: max(1, int(max_recipes))]
    if rows_per_page is not None or max_pages is not None:
        adjusted_recipes: list[dict[str, Any]] = []
        for recipe in recipes:
            adjusted = dict(recipe)
            if rows_per_page is not None:
                adjusted["rows_per_page"] = max(1, int(rows_per_page))
            if max_pages is not None:
                adjusted["max_pages"] = max(1, int(max_pages))
            adjusted_recipes.append(adjusted)
        recipes = adjusted_recipes
    if trace_id:
        backend_api_app._append_related_notice_trace(
            trace_id=trace_id,
            event="collect_recipes_built",
            project_id=project_id,
            project=project,
            payload={
                "recipe_count": len(recipes),
                "queries": [str(params.get("notice_title") or "").strip() for params in recipes],
                "parallel_workers": min(
                    int(recipe_max_workers or RELATED_NOTICE_RECIPE_MAX_WORKERS),
                    max(1, len(recipes)),
                ),
            },
        )

    def _run_collect_attempt(recipe_index: int, params: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]], bool]:
        attempt: dict[str, Any] = {
            "recipe_index": recipe_index,
            "query_index": recipe_index,
            "query": str(params.get("notice_title") or "").strip(),
            "api_scope": str(params.get("api_scope") or "").strip(),
            "demand_org": str(params.get("demand_org") or "").strip(),
            "start_date": str(params.get("start_date") or "").strip(),
            "end_date": str(params.get("end_date") or "").strip(),
            "rows_per_page": int(params.get("rows_per_page") or 0),
            "max_pages": int(params.get("max_pages") or 0),
        }
        try:
            result = collect_seed_rows_with_params(params=dict(params), progress_cb=None)
        except Exception as exc:
            attempt["error"] = str(exc)
            return attempt, [], True

        diagnostics = result.diagnostics
        attempt.update(
            {
                "row_count": len(result.rows),
                "attempted_endpoints": list((diagnostics.attempted_endpoints if diagnostics else [])),
                "matched_endpoints": list((diagnostics.matched_endpoints if diagnostics else [])),
                "all_scope_retry_used": bool(diagnostics.all_scope_retry_used) if diagnostics else False,
                "direct_bid_lookup_used": bool(diagnostics.direct_bid_lookup_used) if diagnostics else False,
                "title_broad_retry_used": bool(diagnostics.title_broad_retry_used) if diagnostics else False,
                "sample_bid_nos": [
                    str(row.get("bid_no") or "").strip()
                    for row in result.rows[:5]
                    if str(row.get("bid_no") or "").strip()
                ],
            }
        )
        enriched_rows: list[dict[str, str]] = []
        for row in result.rows:
            enriched = dict(row)
            enriched["_query_index"] = str(recipe_index)
            enriched["_query_value"] = str(params.get("notice_title") or "").strip()
            enriched["_query_mode"] = str(params.get("api_scope") or "").strip()
            enriched["_query_demand_org"] = str(params.get("demand_org") or "").strip()
            enriched_rows.append(enriched)
        return attempt, enriched_rows, False

    recipe_workers = min(int(recipe_max_workers or RELATED_NOTICE_RECIPE_MAX_WORKERS), max(1, len(recipes)))
    indexed_recipes = list(enumerate(recipes))

    for batch_start in range(0, len(indexed_recipes), recipe_workers):
        if backend_api_app.time.monotonic() >= deadline:
            break
        batch = indexed_recipes[batch_start : batch_start + recipe_workers]
        batch_results: list[tuple[dict[str, Any], list[dict[str, str]], bool]] = []

        if len(batch) == 1:
            recipe_index, params = batch[0]
            batch_results.append(_run_collect_attempt(recipe_index, params))
        else:
            executor = backend_api_app.ThreadPoolExecutor(max_workers=len(batch))
            futures = [
                (recipe_index, params, executor.submit(_run_collect_attempt, recipe_index, params))
                for recipe_index, params in batch
            ]
            try:
                for recipe_index, params, future in futures:
                    remaining_sec = max(0.0, deadline - backend_api_app.time.monotonic())
                    wait_timeout_sec = min(active_request_timeout_sec, remaining_sec)
                    if wait_timeout_sec <= 0:
                        timeout_attempt = {
                            "recipe_index": recipe_index,
                            "query_index": recipe_index,
                            "query": str(params.get("notice_title") or "").strip(),
                            "api_scope": str(params.get("api_scope") or "").strip(),
                            "demand_org": str(params.get("demand_org") or "").strip(),
                            "start_date": str(params.get("start_date") or "").strip(),
                            "end_date": str(params.get("end_date") or "").strip(),
                            "rows_per_page": int(params.get("rows_per_page") or 0),
                            "max_pages": int(params.get("max_pages") or 0),
                            "error": "related notice collect timed out before batch result was ready",
                        }
                        batch_results.append((timeout_attempt, [], True))
                        continue
                    try:
                        batch_results.append(future.result(timeout=wait_timeout_sec))
                    except FuturesTimeoutError:
                        timeout_attempt = {
                            "recipe_index": recipe_index,
                            "query_index": recipe_index,
                            "query": str(params.get("notice_title") or "").strip(),
                            "api_scope": str(params.get("api_scope") or "").strip(),
                            "demand_org": str(params.get("demand_org") or "").strip(),
                            "start_date": str(params.get("start_date") or "").strip(),
                            "end_date": str(params.get("end_date") or "").strip(),
                            "rows_per_page": int(params.get("rows_per_page") or 0),
                            "max_pages": int(params.get("max_pages") or 0),
                            "error": f"related notice collect timed out after {wait_timeout_sec:.1f}s",
                        }
                        batch_results.append((timeout_attempt, [], True))
            finally:
                executor.shutdown(wait=False, cancel_futures=True)

        batch_results.sort(key=lambda item: int(item[0].get("recipe_index") or 0))

        for attempt, enriched_rows, has_error in batch_results:
            attempts.append(attempt)
            if has_error:
                if trace_id:
                    backend_api_app._append_related_notice_trace(
                        trace_id=trace_id,
                        event="collect_attempt_error",
                        project_id=project_id,
                        project=project,
                        payload=dict(attempt),
                    )
                continue
            if trace_id:
                backend_api_app._append_related_notice_trace(
                    trace_id=trace_id,
                    event="collect_attempt_result",
                    project_id=project_id,
                    project=project,
                    payload=dict(attempt),
                )
            collected.extend(enriched_rows)

        deduped = backend_api_app._dedupe_related_notice_rows(collected)
        if progress_cb is not None:
            progress_cb(deduped, {"attempts": list(attempts), "deduped_row_count": len(deduped)})
        if len(deduped) >= RELATED_NOTICE_LIVE_MAX_COLLECTED_ROWS:
            if trace_id:
                backend_api_app._append_related_notice_trace(
                    trace_id=trace_id,
                    event="collect_early_return",
                    project_id=project_id,
                    project=project,
                    payload={"deduped_row_count": len(deduped)},
                )
            return deduped, {
                "project_name": str(project.get("project_name") or ""),
                "project_search_name": str(project.get("project_search_name") or ""),
                "issuer_name": str(project.get("issuer_name") or ""),
                "deadline_sec": active_deadline_sec,
                "max_collected_rows": RELATED_NOTICE_LIVE_MAX_COLLECTED_ROWS,
                "attempts": attempts,
                "deduped_row_count": len(deduped),
            }
    deduped = _dedupe_related_notice_rows(collected)
    if trace_id:
        backend_api_app._append_related_notice_trace(
            trace_id=trace_id,
            event="collect_complete",
            project_id=project_id,
            project=project,
            payload={
                "attempt_count": len(attempts),
                "deduped_row_count": len(deduped),
                "deduped_bid_nos": [
                    str(row.get("bid_no") or "").strip()
                    for row in deduped
                    if str(row.get("bid_no") or "").strip()
                ],
            },
        )
    return deduped, {
        "project_name": str(project.get("project_name") or ""),
        "project_search_name": str(project.get("project_search_name") or ""),
        "issuer_name": str(project.get("issuer_name") or ""),
        "deadline_sec": active_deadline_sec,
        "max_collected_rows": RELATED_NOTICE_LIVE_MAX_COLLECTED_ROWS,
        "attempts": attempts,
        "deduped_row_count": len(deduped),
    }


def _dedupe_related_notice_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return _dedupe_related_notice_rows_impl(rows, norm_text_fn=_norm_text)


def _project_source_notice_keys(project: dict[str, Any]) -> set[tuple[str, str]]:
    backend_api_app = _backend_api_app
    return _project_source_notice_keys_impl(
        project,
        project_source_runs_fn=backend_api_app._project_source_runs,
        get_artifact_repository_fn=backend_api_app._get_artifact_repository,
        load_seed_rows_from_artifact_path_fn=backend_api_app._load_seed_rows_from_artifact_path,
        project_search_name_fn=_project_search_name,
        project_match_key_fn=_project_match_key,
        repository_error_fn=backend_api_app._repository_error,
    )


def _filter_self_related_notice_payload_items(project: dict[str, Any], items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    backend_api_app = _backend_api_app
    return _filter_self_related_notice_payload_items_impl(
        project,
        items,
        project_source_notice_keys_fn=backend_api_app._project_source_notice_keys,
    )


def _is_related_notice_payload_entry_precomputed(entry: dict[str, Any]) -> bool:
    return _is_related_notice_payload_entry_precomputed_impl(entry)


def _seed_related_notice_items(
    project: dict[str, Any],
    *,
    trace_id: str | None = None,
    project_id: UUID | None = None,
) -> list[RelatedNoticeItem]:
    backend_api_app = _backend_api_app
    return _seed_related_notice_items_impl(
        project,
        trace_id=trace_id,
        project_id=project_id,
        get_artifact_repository_fn=backend_api_app._get_artifact_repository,
        load_seed_rows_from_artifact_path_fn=backend_api_app._load_seed_rows_from_artifact_path,
        score_related_notice_match_fn=_score_related_notice_match,
        dedupe_related_notice_payload_items_fn=_dedupe_related_notice_payload_items,
        filter_self_related_notice_payload_items_fn=_filter_self_related_notice_payload_items,
        append_related_notice_trace_fn=backend_api_app._append_related_notice_trace,
        repository_error_fn=backend_api_app._repository_error,
        project_search_name_fn=_project_search_name,
    )


def _precomputed_related_notice_items(
    project: dict[str, Any],
    *,
    trace_id: str | None = None,
    project_id: UUID | None = None,
    allow_artifact_scan: bool = True,
) -> tuple[list[RelatedNoticeItem], bool]:
    backend_api_app = _backend_api_app
    return _precomputed_related_notice_items_impl(
        project,
        trace_id=trace_id,
        project_id=project_id,
        get_related_notice_cache_repository_fn=backend_api_app._get_related_notice_cache_repository,
        get_artifact_repository_fn=backend_api_app._get_artifact_repository,
        project_source_runs_fn=backend_api_app._project_source_runs,
        load_json_artifact_payload_fn=backend_api_app._load_json_artifact_payload,
        dedupe_related_notice_payload_items_fn=backend_api_app._dedupe_related_notice_payload_items,
        filter_self_related_notice_payload_items_fn=backend_api_app._filter_self_related_notice_payload_items,
        append_related_notice_trace_fn=backend_api_app._append_related_notice_trace,
        repository_error_fn=backend_api_app._repository_error,
        is_missing_related_notice_cache_table_error_fn=backend_api_app._is_missing_related_notice_cache_table_error,
        is_related_notice_payload_entry_precomputed_fn=backend_api_app._is_related_notice_payload_entry_precomputed,
        allow_artifact_scan=allow_artifact_scan,
    )


def _project_source_runs(project: dict[str, Any]) -> list[dict[str, Any]]:
    backend_api_app = _backend_api_app
    return _project_source_runs_impl(
        project,
        get_run_repository_fn=backend_api_app._get_run_repository,
        repository_error_fn=backend_api_app._repository_error,
    )


def _select_project_source_notice_row(project: dict[str, Any]) -> dict[str, str] | None:
    backend_api_app = _backend_api_app
    return _select_project_source_notice_row_impl(
        project,
        project_source_runs_fn=backend_api_app._project_source_runs,
        get_artifact_repository_fn=backend_api_app._get_artifact_repository,
        load_seed_rows_from_artifact_path_fn=backend_api_app._load_seed_rows_from_artifact_path,
        score_related_notice_match_fn=_score_related_notice_match,
        normalize_tracker_bid_ord_fn=backend_api_app._normalize_tracker_bid_ord,
        norm_text_fn=_norm_text,
        load_notice_seed_row_by_bid_fn=backend_api_app.load_notice_seed_row_by_bid,
        repository_error_fn=backend_api_app._repository_error,
    )


def _related_notice_response_without_live(
    project: dict[str, Any],
    project_id: UUID,
    *,
    trace_id: str | None = None,
) -> RelatedNoticeListResponse:
    backend_api_app = _backend_api_app
    cache_repository = backend_api_app._get_related_notice_cache_repository()
    return _related_notice_response_without_live_impl(
        project=project,
        project_id=project_id,
        trace_id=trace_id,
        project_source_runs_fn=backend_api_app._project_source_runs,
        get_related_notice_cache_fn=lambda project_key: cache_repository.get_cache(project_key=project_key),
        is_missing_related_notice_cache_table_error_fn=backend_api_app._is_missing_related_notice_cache_table_error,
        repository_error_fn=backend_api_app._repository_error,
        is_related_notice_precompute_stale_fn=backend_api_app._is_related_notice_precompute_stale,
        is_related_notice_payload_entry_precomputed_fn=backend_api_app._is_related_notice_payload_entry_precomputed,
        filter_self_related_notice_payload_items_fn=backend_api_app._filter_self_related_notice_payload_items,
        dedupe_related_notice_payload_items_fn=backend_api_app._dedupe_related_notice_payload_items,
        seed_related_notice_items_fn=backend_api_app._seed_related_notice_items,
        append_related_notice_trace_fn=backend_api_app._append_related_notice_trace,
        get_run_repository_fn=backend_api_app._get_run_repository,
        queue_related_notice_precompute_for_run_fn=backend_api_app.queue_related_notice_precompute_for_run,
        upsert_related_notice_cache_fn=lambda row: cache_repository.upsert_cache(row),
        get_related_notice_project_precompute_state_fn=backend_api_app._get_related_notice_project_precompute_state,
        related_notice_algorithm_version=backend_api_app.RELATED_NOTICE_ALGORITHM_VERSION,
    )


def _score_related_notice_rows(project: dict[str, Any], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in rows:
        score, candidate_search_name, reason = _score_related_notice_match(project, row)
        if score < 20:
            continue
        query_index = int(str(row.get("_query_index") or "0") or "0")
        issuer_name = str(row.get("org_name") or "").strip()
        issuer_bonus = 0
        if _norm_text(str(project.get("issuer_name") or "")) and _norm_text(
            str(project.get("issuer_name") or "")
        ) in _norm_text(issuer_name):
            issuer_bonus = 10
        items.append(
            {
                "id": "::".join(
                    (
                        str(row.get("bid_no") or "").strip(),
                        str(row.get("bid_ord") or "").strip(),
                        candidate_search_name or _project_search_name(str(row.get("project_name") or "").strip()),
                    )
                ),
                "project_name": str(row.get("project_name") or "").strip(),
                "project_search_name": candidate_search_name,
                "issuer_name": issuer_name,
                "announce_date": str(row.get("announce_date") or "").strip(),
                "bid_no": str(row.get("bid_no") or "").strip(),
                "bid_ord": str(row.get("bid_ord") or "").strip(),
                "g2b_verified": str(row.get("g2b_verified") or "").strip(),
                "notice_url": str(row.get("bid_ntce_url") or "").strip(),
                "notice_detail_url": str(row.get("bid_ntce_dtl_url") or "").strip(),
                "match_score": max(20, score + issuer_bonus + max(0, 12 - (query_index * 2))),
                "match_reason": reason or f"query:{row.get('_query_value') or ''}",
            }
        )
    filtered = _filter_self_related_notice_payload_items(project, _dedupe_related_notice_payload_items(items))
    return [classify_related_notice_item(project, item) for item in filtered]


def _live_related_notice_search(
    project: dict[str, Any],
    *,
    trace_id: str | None = None,
    project_id: UUID | None = None,
    progress_cb: Any | None = None,
) -> tuple[list[RelatedNoticeItem], dict[str, Any]]:
    backend_api_app = _backend_api_app

    def _emit_progress(rows: list[dict[str, str]], debug: dict[str, Any]) -> None:
        if progress_cb is None:
            return
        partial_items = _score_related_notice_rows(project, rows)
        if partial_items:
            progress_cb([RelatedNoticeItem(**item) for item in partial_items], debug)

    rows, collect_debug = _collect_related_notice_rows_with_debug(
        project,
        trace_id=trace_id,
        project_id=project_id,
        progress_cb=_emit_progress if progress_cb is not None else None,
    )

    items = _score_related_notice_rows(project, rows)
    if trace_id:
        backend_api_app._append_related_notice_trace(
            trace_id=trace_id,
            event="live_search_scored",
            project_id=project_id,
            project=project,
            payload={
                "row_count": len(rows),
                "scored_candidate_count": len(items),
                "final_bid_nos": [
                    str(item.get("bid_no") or "").strip()
                    for item in items
                    if str(item.get("bid_no") or "").strip()
                ],
            },
        )
    return [RelatedNoticeItem(**item) for item in items], {
        **collect_debug,
        "scored_candidate_count": len(items),
        "final_item_count": len(items),
        "final_bid_nos": [
            str(item.get("bid_no") or "").strip()
            for item in items
            if str(item.get("bid_no") or "").strip()
        ],
    }


def _related_notice_raw_row_item(
    row: dict[str, Any],
    *,
    query: str,
    index: int,
) -> dict[str, Any]:
    bid_no = str(row.get("bid_no") or "").strip()
    bid_ord = str(row.get("bid_ord") or "").strip()
    title = str(row.get("project_name") or "").strip()
    return {
        "id": "::".join(part for part in (bid_no, bid_ord, title or str(index)) if part),
        "project_name": title,
        "project_search_name": _project_search_name(title),
        "issuer_name": str(row.get("org_name") or "").strip(),
        "announce_date": str(row.get("announce_date") or "").strip(),
        "bid_no": bid_no,
        "bid_ord": bid_ord,
        "g2b_verified": str(row.get("g2b_verified") or "").strip(),
        "notice_url": str(row.get("bid_ntce_url") or "").strip(),
        "notice_detail_url": str(row.get("bid_ntce_dtl_url") or "").strip(),
        "match_score": 0,
        "match_reason": f"raw_search:{query}",
        "notice_stage": "raw_search",
        "sales_relevance": "raw",
        "exclusion_reason": "",
        "relatedness_score": 0,
        "sales_relevance_score": 0,
        "reason_codes": ["RAW_NARA_SEARCH"],
    }


def _parse_quick_related_notice_date(value: Any) -> datetime | None:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) < 8:
        return None
    try:
        return datetime.strptime(digits[:8], "%Y%m%d")
    except ValueError:
        return None


def _quick_related_notice_today() -> datetime:
    return datetime.now(ZoneInfo("Asia/Seoul")).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)


def _add_twelve_months(value: datetime) -> datetime:
    try:
        return value.replace(year=value.year + 1)
    except ValueError:
        return value.replace(year=value.year + 1, day=28)


def _quick_related_notice_start_date(project: dict[str, Any], *, today: datetime) -> datetime:
    source_json = dict(project.get("source_json") or {})
    for value in (
        project.get("first_notice_date"),
        source_json.get("first_notice_date"),
        source_json.get("source_notice_date"),
        source_json.get("notice_date"),
        source_json.get("announce_date"),
        project.get("notice_date"),
        project.get("announce_date"),
        project.get("latest_notice_date"),
        source_json.get("latest_notice_date"),
    ):
        parsed = _parse_quick_related_notice_date(value)
        if parsed is not None:
            return min(parsed, today)
    return today - timedelta(days=365)


def _build_quick_related_notice_date_ranges(project: dict[str, Any]) -> list[dict[str, str]]:
    today = _quick_related_notice_today()
    start = _quick_related_notice_start_date(project, today=today)
    first_end = min(_add_twelve_months(start), today)
    ranges = [
        {
            "label": "first_12_months_after_source_notice",
            "start_date": start.strftime("%Y%m%d"),
            "end_date": first_end.strftime("%Y%m%d"),
        }
    ]
    second_start = first_end + timedelta(days=1)
    if second_start <= today:
        ranges.append(
            {
                "label": "after_first_12_months_until_today",
                "start_date": second_start.strftime("%Y%m%d"),
                "end_date": today.strftime("%Y%m%d"),
            }
        )
    return ranges


def _quick_related_notice_request_params(
    *,
    service_key: str,
    query: str,
    start_date: str,
    end_date: str,
) -> dict[str, object]:
    return {
        "ServiceKey": service_key,
        "pageNo": 1,
        "numOfRows": 100,
        "type": "json",
        "inqryDiv": "1",
        "inqryBgnDt": f"{start_date}0000",
        "inqryEndDt": f"{end_date}2359",
        "bidNtceNm": query,
    }


def _fetch_quick_related_notice_raw_rows(
    *,
    service_key: str,
    query: str,
    date_ranges: list[dict[str, str]],
    request_timeout_sec: int = 5,
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    rows: list[dict[str, str]] = []
    attempts: list[dict[str, Any]] = []

    def _fetch_endpoint(range_info: dict[str, str], endpoint_name: str, endpoint_url: str) -> tuple[dict[str, Any], list[dict[str, str]]]:
        params = _quick_related_notice_request_params(
            service_key=service_key,
            query=query,
            start_date=range_info["start_date"],
            end_date=range_info["end_date"],
        )
        started_at = time.monotonic()
        attempt: dict[str, Any] = {
            "query": query,
            "api_scope": "quick_raw",
            "range_label": range_info["label"],
            "endpoint": endpoint_name,
            "start_date": range_info["start_date"],
            "end_date": range_info["end_date"],
            "rows_per_page": 100,
            "max_pages": 1,
        }
        try:
            response = requests.get(endpoint_url, params=params, timeout=request_timeout_sec)
            status_code = int(getattr(response, "status_code", 0) or 0)
            attempt["status_code"] = status_code
            if status_code != 200:
                attempt["error"] = str(getattr(response, "text", "") or "")[:200]
                return attempt, []
            payload = response.json()
            result_code, result_msg = _native_api_header(payload)
            attempt["result_code"] = result_code
            if result_code and result_code not in {"00", "03"}:
                attempt["error"] = f"API error {result_code}: {result_msg}"
                return attempt, []
            items, total_count = _native_extract_items(payload)
            attempt["total_count"] = total_count
            endpoint_rows: list[dict[str, str]] = []
            for item in items:
                row = _native_seed_row_from_item(item, endpoint_name=endpoint_name)
                row["_query_index"] = "0"
                row["_query_value"] = query
                row["_query_mode"] = "quick_raw"
                endpoint_rows.append(row)
            attempt["row_count"] = len(endpoint_rows)
            return attempt, endpoint_rows
        except Exception as exc:
            attempt["error"] = str(exc)
            return attempt, []
        finally:
            attempt["elapsed_ms"] = int((time.monotonic() - started_at) * 1000)

    for range_info in date_ranges:
        worker_count = min(3, max(1, len(API_ENDPOINTS_SEARCH)))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(_fetch_endpoint, range_info, endpoint_name, endpoint_url)
                for endpoint_name, endpoint_url in API_ENDPOINTS_SEARCH
            ]
            for future in futures:
                attempt, endpoint_rows = future.result()
                attempts.append(attempt)
                rows.extend(endpoint_rows)
    return _dedupe_related_notice_rows(rows), attempts


def _quick_related_notice_search(
    project: dict[str, Any],
    *,
    trace_id: str | None = None,
    project_id: UUID | None = None,
) -> tuple[list[RelatedNoticeItem], dict[str, Any]]:
    backend_api_app = _backend_api_app
    source_runs = backend_api_app._project_source_runs(project)
    queries = _build_related_notice_collect_queries(project, source_runs)
    query = next((str(value or "").strip() for value in queries if str(value or "").strip()), "")
    if not query:
        query = str(project.get("project_search_name") or project.get("project_name") or "").strip()
    date_ranges = _build_quick_related_notice_date_ranges(project)
    start_date = date_ranges[0]["start_date"]
    end_date = date_ranges[-1]["end_date"]
    service_key = resolve_native_service_key("")
    if not service_key or not query:
        return [], {
            "source": "raw_nara_search",
            "query": query,
            "date_ranges": date_ranges,
            "error": "service key or query is missing",
            "attempt_count": 0,
            "deduped_row_count": 0,
            "final_item_count": 0,
        }
    try:
        rows, attempts = _fetch_quick_related_notice_raw_rows(
            service_key=service_key,
            query=query,
            date_ranges=date_ranges,
            request_timeout_sec=5,
        )
    except Exception as exc:
        rows = []
        attempts = [{"query": query, "api_scope": "all", "error": str(exc)}]
    items = [_related_notice_raw_row_item(row, query=query, index=index) for index, row in enumerate(rows)]
    if trace_id:
        backend_api_app._append_related_notice_trace(
            trace_id=trace_id,
            event="quick_raw_search_finished",
            project_id=project_id,
            project=project,
            payload={
                "query": query,
                "row_count": len(rows),
                "final_bid_nos": [
                    str(item.get("bid_no") or "").strip()
                    for item in items
                    if str(item.get("bid_no") or "").strip()
                ],
            },
        )
    return [RelatedNoticeItem(**item) for item in items], {
        "source": "raw_nara_search",
        "mode": "quick_raw",
        "query": query,
        "start_date": start_date,
        "end_date": end_date,
        "date_ranges": date_ranges,
        "attempts": attempts,
        "attempt_count": len(attempts),
        "deduped_row_count": len(rows),
        "final_item_count": len(items),
        "final_bid_nos": [
            str(item.get("bid_no") or "").strip()
            for item in items
            if str(item.get("bid_no") or "").strip()
        ],
    }


def _list_related_notices_for_project(project_id: UUID) -> RelatedNoticeListResponse:
    backend_api_app = _backend_api_app
    trace_id = uuid4().hex
    backend_api_app._append_related_notice_trace(
        trace_id=trace_id,
        event="request_started",
        project_id=project_id,
        payload={},
    )
    cached_response = backend_api_app._get_related_notice_response_cache(project_id)
    if cached_response is not None:
        backend_api_app._append_related_notice_trace(
            trace_id=trace_id,
            event="response_cache_hit",
            project_id=project_id,
            payload={
                "status": cached_response.status,
                "source": cached_response.source,
                "item_count": len(cached_response.items),
            },
        )
        return cached_response
    project = backend_api_app._get_project_aggregate(project_id)
    backend_api_app._append_related_notice_trace(
        trace_id=trace_id,
        event="project_loaded",
        project_id=project_id,
        project=project,
        payload={},
    )
    items, has_precomputed = backend_api_app._precomputed_related_notice_items(
        project,
        trace_id=trace_id,
        project_id=project_id,
        allow_artifact_scan=False,
    )
    if not has_precomputed:
        response = backend_api_app._related_notice_response_without_live(project, project_id, trace_id=trace_id)
        cached = backend_api_app._set_related_notice_response_cache(project_id, response)
        backend_api_app._append_related_notice_trace(
            trace_id=trace_id,
            event="request_finished",
            project_id=project_id,
            project=project,
            payload={"status": cached.status, "source": cached.source, "item_count": len(cached.items)},
        )
        return cached
    response = RelatedNoticeListResponse(
        project_id=project_id,
        project_name=str(project.get("project_name") or ""),
        project_search_name=str(project.get("project_search_name") or ""),
        status="ready",
        source="precomputed",
        message="",
        precomputed=True,
        items=items,
    )
    cached = backend_api_app._set_related_notice_response_cache(project_id, response)
    backend_api_app._append_related_notice_trace(
        trace_id=trace_id,
        event="request_finished",
        project_id=project_id,
        project=project,
        payload={"status": cached.status, "source": cached.source, "item_count": len(cached.items)},
    )
    return cached
