from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import UUID
from uuid import uuid4

from backend.api.schemas import RelatedNoticeItem
from backend.api.schemas import RelatedNoticeListResponse
from backend.api.support import projects_related_notice_support as projects_support
from backend.phase1_defaults import load_phase1_identity
from backend.services import related_notice_read_model_backend as read_model_backend
from backend.services.related_notice_collect_backend import build_related_notice_collect_queries as _build_related_notice_collect_queries_impl
from backend.services.related_notice_collect_backend import build_related_notice_collect_recipes as _build_related_notice_collect_recipes_impl
from backend.services.related_notice_collect_backend import build_related_notice_search_window as _build_related_notice_search_window_impl
from backend.services.related_notice_collect_backend import coerce_related_notice_limit as _coerce_related_notice_limit_impl
from backend.services.related_notice_response_backend import related_notice_response_without_live as _related_notice_response_without_live_impl
from backend.services.related_notice_response_backend import get_related_notice_project_precompute_state as _get_related_notice_project_precompute_state_impl
from backend.services.related_notice_response_backend import is_related_notice_precompute_stale as _is_related_notice_precompute_stale_impl


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


def _is_related_notice_precompute_stale(
    run_row: dict[str, Any],
    precompute_status: str,
    *,
    updated_at: Any = None,
    parse_iso_datetime_fn: Any = _parse_iso_datetime,
    stale_sec: int,
) -> bool:
    return _is_related_notice_precompute_stale_impl(
        run_row,
        precompute_status,
        updated_at=updated_at,
        parse_iso_datetime_fn=parse_iso_datetime_fn,
        stale_sec=stale_sec,
    )


def _get_related_notice_project_precompute_state(
    summary_output: dict[str, Any],
    project_key: str,
) -> tuple[str, str, Any, bool]:
    return _get_related_notice_project_precompute_state_impl(summary_output, project_key)


def _build_related_notice_collect_search_window(
    project: dict[str, Any],
    *,
    collect_all_runs_fn: Any,
    parse_yyyymmdd_fn: Any,
    format_yyyymmdd_fn: Any,
    now_fn: Any,
) -> tuple[str, str]:
    return _build_related_notice_search_window_impl(
        project,
        collect_all_runs_fn=collect_all_runs_fn,
        parse_yyyymmdd_fn=parse_yyyymmdd_fn,
        format_yyyymmdd_fn=format_yyyymmdd_fn,
        now_fn=now_fn,
    )


def _coerce_related_notice_limit(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    return _coerce_related_notice_limit_impl(value, default=default, minimum=minimum, maximum=maximum)


def _build_related_notice_collect_queries(
    project: dict[str, Any],
    source_runs: list[dict[str, Any]],
    *,
    build_related_notice_query_variants_fn: Any,
    norm_text_fn: Any,
    collect_max_queries: int,
) -> list[str]:
    return _build_related_notice_collect_queries_impl(
        project,
        source_runs,
        build_related_notice_query_variants_fn=build_related_notice_query_variants_fn,
        norm_text_fn=norm_text_fn,
        collect_max_queries=collect_max_queries,
    )


def _build_related_notice_collect_recipes(
    project: dict[str, Any],
    *,
    source_runs_fn: Any,
    build_related_notice_search_window_fn: Any,
    build_related_notice_query_variants_fn: Any,
    norm_text_fn: Any,
    collect_max_queries: int,
    default_rows_per_page: int,
    default_max_pages: int,
) -> list[dict[str, Any]]:
    source_runs = source_runs_fn(project)
    return _build_related_notice_collect_recipes_impl(
        project,
        source_runs=source_runs,
        build_related_notice_search_window_fn=build_related_notice_search_window_fn,
        build_related_notice_query_variants_fn=build_related_notice_query_variants_fn,
        norm_text_fn=norm_text_fn,
        collect_max_queries=collect_max_queries,
        default_rows_per_page=default_rows_per_page,
        default_max_pages=default_max_pages,
    )


def _collect_related_notice_rows_with_debug(
    project: dict[str, Any],
    *,
    trace_id: str | None = None,
    project_id: UUID | None = None,
    build_related_notice_collect_recipes_fn: Any = projects_support._build_related_notice_collect_recipes,
    append_related_notice_trace_fn: Any = lambda **kwargs: None,
    dedupe_related_notice_rows_fn: Any = projects_support._dedupe_related_notice_rows,
    related_notice_recipe_max_workers: int = 1,
    related_notice_live_deadline_sec: int = 0,
    related_notice_live_request_timeout_sec: int = 0,
    related_notice_live_max_collected_rows: int = 0,
    collect_seed_rows_with_params_fn: Any = None,
    thread_pool_executor_cls: Any = None,
    futures_timeout_error_cls: type[BaseException] = TimeoutError,
    monotonic_fn: Any = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    return projects_support._collect_related_notice_rows_with_debug(
        project,
        trace_id=trace_id,
        project_id=project_id,
    )


def _dedupe_related_notice_rows(rows: list[dict[str, str]], *, norm_text_fn: Any) -> list[dict[str, str]]:
    return projects_support._dedupe_related_notice_rows(rows)


def _project_source_notice_keys(
    project: dict[str, Any],
    *,
    project_source_runs_fn: Any,
    get_artifact_repository_fn: Any,
    load_seed_rows_from_artifact_path_fn: Any,
    project_search_name_fn: Any,
    project_match_key_fn: Any,
    repository_error_fn: Any,
) -> set[tuple[str, str]]:
    return projects_support._project_source_notice_keys(project)


def _filter_self_related_notice_payload_items(
    project: dict[str, Any],
    items: list[dict[str, Any]],
    *,
    project_source_notice_keys_fn: Any,
) -> list[dict[str, Any]]:
    return projects_support._filter_self_related_notice_payload_items(project, items)


def _is_related_notice_payload_entry_precomputed(entry: dict[str, Any]) -> bool:
    return projects_support._is_related_notice_payload_entry_precomputed(entry)


def _seed_related_notice_items(
    project: dict[str, Any],
    *,
    trace_id: str | None = None,
    project_id: UUID | None = None,
    get_artifact_repository_fn: Any,
    load_seed_rows_from_artifact_path_fn: Any,
    score_related_notice_match_fn: Any,
    dedupe_related_notice_payload_items_fn: Any,
    filter_self_related_notice_payload_items_fn: Any,
    append_related_notice_trace_fn: Any,
    repository_error_fn: Any,
    project_search_name_fn: Any,
) -> list[RelatedNoticeItem]:
    return projects_support._seed_related_notice_items(project, trace_id=trace_id, project_id=project_id)


_RELATED_NOTICE_PUBLISHED_SNAPSHOT_SET_ID_UNSET = object()


def _precomputed_related_notice_items(
    project: dict[str, Any],
    *,
    trace_id: str | None = None,
    project_id: UUID | None = None,
    published_snapshot_set_id: str | None | object = _RELATED_NOTICE_PUBLISHED_SNAPSHOT_SET_ID_UNSET,
    get_related_notice_cache_repository_fn: Any,
    get_artifact_repository_fn: Any,
    project_source_runs_fn: Any,
    load_json_artifact_payload_fn: Any,
    dedupe_related_notice_payload_items_fn: Any,
    filter_self_related_notice_payload_items_fn: Any,
    append_related_notice_trace_fn: Any,
    repository_error_fn: Any,
    is_missing_related_notice_cache_table_error_fn: Any,
    is_related_notice_payload_entry_precomputed_fn: Any,
) -> tuple[list[RelatedNoticeItem], bool]:
    return read_model_backend._precomputed_related_notice_items(
        project,
        trace_id=trace_id,
        project_id=project_id,
        published_snapshot_set_id=published_snapshot_set_id,
        get_related_notice_cache_repository_fn=get_related_notice_cache_repository_fn,
        get_artifact_repository_fn=get_artifact_repository_fn,
        project_source_runs_fn=project_source_runs_fn,
        load_json_artifact_payload_fn=load_json_artifact_payload_fn,
        dedupe_related_notice_payload_items_fn=dedupe_related_notice_payload_items_fn,
        filter_self_related_notice_payload_items_fn=filter_self_related_notice_payload_items_fn,
        append_related_notice_trace_fn=append_related_notice_trace_fn,
        repository_error_fn=repository_error_fn,
        is_missing_related_notice_cache_table_error_fn=is_missing_related_notice_cache_table_error_fn,
        is_related_notice_payload_entry_precomputed_fn=is_related_notice_payload_entry_precomputed_fn,
    )


def _get_published_related_notice_snapshot_set_id(
    *,
    load_phase1_identity_fn: Any = load_phase1_identity,
    get_related_notice_publication_repository_fn: Any,
) -> str:
    identity = load_phase1_identity_fn()
    publication_repository = get_related_notice_publication_repository_fn()
    publication = publication_repository.get_publication(organization_id=identity.organization_id)
    return str((publication or {}).get("published_snapshot_set_id") or "").strip()


def _project_source_runs(
    project: dict[str, Any],
    *,
    get_run_repository_fn: Any,
    repository_error_fn: Any,
) -> list[dict[str, Any]]:
    return projects_support._project_source_runs(project)


def _select_project_source_notice_row(
    project: dict[str, Any],
    *,
    project_source_runs_fn: Any,
    get_artifact_repository_fn: Any,
    load_seed_rows_from_artifact_path_fn: Any,
    score_related_notice_match_fn: Any,
    normalize_tracker_bid_ord_fn: Any,
    norm_text_fn: Any,
    load_notice_seed_row_by_bid_fn: Any,
    repository_error_fn: Any,
) -> dict[str, str] | None:
    return projects_support._select_project_source_notice_row(project)


def _build_project_notice_view_payload(
    project_id: UUID,
    *,
    get_project_aggregate_fn: Any,
    select_project_source_notice_row_fn: Any,
    load_notice_view_helpers_fn: Any,
    not_found_fn: Any,
    validation_error_fn: Any,
) -> dict[str, object]:
    return projects_support._build_project_notice_view_payload(project_id)


def _select_tracker_entry_source_notice_row(
    entry: dict[str, Any],
    *,
    get_artifact_repository_fn: Any,
    load_notice_seed_row_by_bid_fn: Any,
    coerce_uuid_or_none_fn: Any,
    derive_tracker_entry_bid_identity_fn: Any,
    normalize_tracker_bid_ord_fn: Any,
    load_seed_rows_from_artifact_path_fn: Any,
    repository_error_fn: Any,
) -> dict[str, str] | None:
    return projects_support._select_tracker_entry_source_notice_row(entry)


def _related_notice_response_without_live(
    project: dict[str, Any],
    project_id: UUID,
    *,
    trace_id: str | None = None,
    project_source_runs_fn: Any,
    get_related_notice_cache_fn: Any,
    is_missing_related_notice_cache_table_error_fn: Any,
    repository_error_fn: Any,
    is_related_notice_precompute_stale_fn: Any,
    is_related_notice_payload_entry_precomputed_fn: Any,
    filter_self_related_notice_payload_items_fn: Any,
    dedupe_related_notice_payload_items_fn: Any,
    seed_related_notice_items_fn: Any,
    append_related_notice_trace_fn: Any,
    get_run_repository_fn: Any,
    queue_related_notice_precompute_for_run_fn: Any,
    upsert_related_notice_cache_fn: Any,
    get_related_notice_project_precompute_state_fn: Any,
    related_notice_algorithm_version: int,
    allow_seed_fallback: bool = False,
) -> RelatedNoticeListResponse:
    return _related_notice_response_without_live_impl(
        project=project,
        project_id=project_id,
        trace_id=trace_id,
        project_source_runs_fn=project_source_runs_fn,
        get_related_notice_cache_fn=get_related_notice_cache_fn,
        is_missing_related_notice_cache_table_error_fn=is_missing_related_notice_cache_table_error_fn,
        repository_error_fn=repository_error_fn,
        is_related_notice_precompute_stale_fn=is_related_notice_precompute_stale_fn,
        is_related_notice_payload_entry_precomputed_fn=is_related_notice_payload_entry_precomputed_fn,
        filter_self_related_notice_payload_items_fn=filter_self_related_notice_payload_items_fn,
        dedupe_related_notice_payload_items_fn=dedupe_related_notice_payload_items_fn,
        seed_related_notice_items_fn=seed_related_notice_items_fn,
        append_related_notice_trace_fn=append_related_notice_trace_fn,
        get_run_repository_fn=get_run_repository_fn,
        queue_related_notice_precompute_for_run_fn=queue_related_notice_precompute_for_run_fn,
        upsert_related_notice_cache_fn=upsert_related_notice_cache_fn,
        get_related_notice_project_precompute_state_fn=get_related_notice_project_precompute_state_fn,
        related_notice_algorithm_version=related_notice_algorithm_version,
        allow_seed_fallback=allow_seed_fallback,
    )


def _live_related_notice_search(
    project: dict[str, Any],
    *,
    trace_id: str | None = None,
    project_id: UUID | None = None,
    progress_cb: Any | None = None,
    collect_related_notice_rows_with_debug_fn: Any,
    score_related_notice_match_fn: Any,
    norm_text_fn: Any,
    project_search_name_fn: Any,
    filter_self_related_notice_payload_items_fn: Any,
    dedupe_related_notice_payload_items_fn: Any,
    append_related_notice_trace_fn: Any,
) -> tuple[list[RelatedNoticeItem], dict[str, Any]]:
    return projects_support._live_related_notice_search(
        project,
        trace_id=trace_id,
        project_id=project_id,
        progress_cb=progress_cb,
    )


def _coerce_related_notice_cache_items(items: Any) -> list[RelatedNoticeItem]:
    result: list[RelatedNoticeItem] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        try:
            result.append(RelatedNoticeItem(**dict(item)))
        except Exception:
            continue
    return result


def _related_notice_cache_status_response(
    *,
    project: dict[str, Any],
    project_id: UUID,
    published_snapshot_set_id: str | None,
    get_related_notice_cache_fn: Any,
) -> RelatedNoticeListResponse | None:
    project_key = str(project.get("_project_match_key") or "").strip()
    if not project_key or get_related_notice_cache_fn is None:
        return None
    try:
        cache_row = get_related_notice_cache_fn(
            project_key=project_key,
            snapshot_set_id=str(published_snapshot_set_id or "").strip() or None,
        )
    except TypeError:
        cache_row = get_related_notice_cache_fn(project_key=project_key)
    if not cache_row:
        return None
    status = str(cache_row.get("status") or "").strip()
    if status not in {"queued", "running", "failed"}:
        return None
    payload = dict(cache_row.get("payload_json") or {})
    items = _coerce_related_notice_cache_items(payload.get("items") or [])
    if status == "queued":
        message = "후속공고 갱신 요청이 등록되었습니다."
    elif status == "running":
        message = "후속공고 정보를 갱신 중입니다. 기존 저장본이 있으면 함께 표시합니다."
    else:
        message = str(cache_row.get("error") or payload.get("error") or "후속공고 갱신 중 오류가 발생했습니다.")
    return RelatedNoticeListResponse(
        project_id=project_id,
        project_name=str(project.get("project_name") or payload.get("project_name") or ""),
        project_search_name=str(project.get("project_search_name") or payload.get("project_search_name") or ""),
        status=status,
        source=str(cache_row.get("source") or payload.get("source") or "refresh_request"),
        message=message,
        precomputed=False,
        items=items,
    )


def _list_related_notices_for_project(
    project_id: UUID,
    *,
    force_refresh: bool = False,
    quick: bool = False,
    get_published_related_notice_snapshot_set_id_fn: Any,
    append_related_notice_trace_fn: Any,
    get_related_notice_response_cache_fn: Any,
    get_snapshot_project_aggregate_fn: Any,
    get_project_aggregate_fn: Any,
    get_related_notice_cache_fn: Any,
    quick_related_notice_search_fn: Any | None = None,
    precomputed_related_notice_items_fn: Any,
    set_related_notice_response_cache_fn: Any,
) -> RelatedNoticeListResponse:
    trace_id = uuid4().hex
    published_snapshot_set_id = get_published_related_notice_snapshot_set_id_fn()
    append_related_notice_trace_fn(
        trace_id=trace_id,
        event="request_started",
        project_id=project_id,
        payload={"published_snapshot_set_id": published_snapshot_set_id},
    )
    cached_response = None
    if published_snapshot_set_id and not force_refresh and not quick:
        cached_response = get_related_notice_response_cache_fn(project_id, published_snapshot_set_id)
    if cached_response is not None:
        append_related_notice_trace_fn(
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
    project = get_snapshot_project_aggregate_fn(project_id) if published_snapshot_set_id else None
    if project is None:
        project = get_project_aggregate_fn(project_id)
    append_related_notice_trace_fn(
        trace_id=trace_id,
        event="project_loaded",
        project_id=project_id,
        project=project,
        payload={},
    )
    if quick:
        if quick_related_notice_search_fn is None:
            items, debug = [], {"error": "quick related notice search is unavailable"}
        else:
            items, debug = quick_related_notice_search_fn(project, trace_id=trace_id, project_id=project_id)
        response = RelatedNoticeListResponse(
            project_id=project_id,
            project_name=str(project.get("project_name") or ""),
            project_search_name=str(project.get("project_search_name") or ""),
            status="ready" if items else "missing",
            source="raw_search",
            message=(
                "나라장터 키워드 빠른 검색 결과입니다. 필터링 없이 먼저 표시합니다."
                if items
                else "나라장터 빠른 검색에서 확인된 결과가 없습니다. 정밀 갱신 결과를 기다려주세요."
            ),
            precomputed=False,
            items=items,
            stats={
                "attempt_count": int(debug.get("attempt_count") or len(debug.get("attempts") or [])) if isinstance(debug, dict) else 0,
                "deduped_row_count": int(debug.get("deduped_row_count") or 0) if isinstance(debug, dict) else 0,
                "final_item_count": len(items),
            },
        )
        append_related_notice_trace_fn(
            trace_id=trace_id,
            event="quick_search_finished",
            project_id=project_id,
            project=project,
            payload={"status": response.status, "source": response.source, "item_count": len(response.items)},
        )
        return response
    cache_status_response = _related_notice_cache_status_response(
        project=project,
        project_id=project_id,
        published_snapshot_set_id=published_snapshot_set_id,
        get_related_notice_cache_fn=get_related_notice_cache_fn,
    )
    if cache_status_response is not None:
        append_related_notice_trace_fn(
            trace_id=trace_id,
            event="refresh_cache_status_hit",
            project_id=project_id,
            project=project,
            payload={
                "status": cache_status_response.status,
                "source": cache_status_response.source,
                "item_count": len(cache_status_response.items),
            },
        )
        return cache_status_response
    items, has_precomputed = precomputed_related_notice_items_fn(
        project,
        trace_id=trace_id,
        project_id=project_id,
        published_snapshot_set_id=published_snapshot_set_id,
    )
    if not has_precomputed:
        response = RelatedNoticeListResponse(
            project_id=project_id,
            project_name=str(project.get("project_name") or ""),
            project_search_name=str(project.get("project_search_name") or ""),
            status="missing",
            source="published_snapshot",
            message="저장된 후속공고 정보가 없습니다.",
            precomputed=False,
            items=[],
        )
        cached = (
            set_related_notice_response_cache_fn(project_id, response, published_snapshot_set_id)
            if published_snapshot_set_id
            else response
        )
        append_related_notice_trace_fn(
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
    cached = (
        set_related_notice_response_cache_fn(project_id, response, published_snapshot_set_id)
        if published_snapshot_set_id
        else response
    )
    append_related_notice_trace_fn(
        trace_id=trace_id,
        event="request_finished",
        project_id=project_id,
        project=project,
        payload={"status": cached.status, "source": cached.source, "item_count": len(cached.items)},
    )
    return cached
