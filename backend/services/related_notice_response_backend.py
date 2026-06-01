from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import UUID

from backend.api.schemas import RelatedNoticeItem
from backend.api.schemas import RelatedNoticeListResponse


def _safe_parse_iso_datetime(value: Any, *, parse_iso_datetime_fn: Any) -> datetime | None:
    try:
        return parse_iso_datetime_fn(value)
    except Exception:
        return None


def is_related_notice_precompute_stale(
    run_row: dict[str, Any],
    precompute_status: str,
    *,
    updated_at: Any = None,
    parse_iso_datetime_fn: Any,
    stale_sec: int,
) -> bool:
    if str(precompute_status or "").strip() not in {"queued", "running"}:
        return False
    status_updated_at = _safe_parse_iso_datetime(updated_at, parse_iso_datetime_fn=parse_iso_datetime_fn)
    if status_updated_at is None:
        status_updated_at = _safe_parse_iso_datetime(
            run_row.get("updated_at") or run_row.get("created_at"),
            parse_iso_datetime_fn=parse_iso_datetime_fn,
        )
    if status_updated_at is None:
        return False
    return (datetime.now(timezone.utc) - status_updated_at).total_seconds() >= int(stale_sec)


def get_related_notice_project_precompute_state(
    summary_output: dict[str, Any],
    project_key: str,
) -> tuple[str, str, Any, bool]:
    if not project_key:
        return "", "", None, False
    statuses = dict(summary_output.get("related_notice_project_statuses") or {})
    entry = dict(statuses.get(project_key) or {})
    if not entry:
        return "", "", None, False
    return (
        str(entry.get("status") or "").strip(),
        str(entry.get("error") or "").strip(),
        entry.get("updated_at"),
        True,
    )


def _build_related_notice_response(
    *,
    project: dict[str, Any],
    project_id: UUID,
    status: str,
    source: str,
    message: str,
    precomputed: bool,
    items: list[RelatedNoticeItem],
    groups: dict[str, Any] | None = None,
    stats: dict[str, Any] | None = None,
) -> RelatedNoticeListResponse:
    response_groups: dict[str, list[RelatedNoticeItem]] = {}
    for key, values in dict(groups or {}).items():
        response_groups[str(key)] = [
            item if isinstance(item, RelatedNoticeItem) else RelatedNoticeItem(**dict(item))
            for item in list(values or [])
            if isinstance(item, dict) or isinstance(item, RelatedNoticeItem)
        ]
    response_stats: dict[str, int] = {}
    for key, value in dict(stats or {}).items():
        try:
            response_stats[str(key)] = int(value or 0)
        except (TypeError, ValueError):
            response_stats[str(key)] = 0
    return RelatedNoticeListResponse(
        project_id=project_id,
        project_name=str(project.get("project_name") or ""),
        project_search_name=str(project.get("project_search_name") or ""),
        status=status,
        source=source,
        message=message,
        precomputed=precomputed,
        items=items,
        groups=response_groups,
        stats=response_stats,
    )


def related_notice_response_without_live(
    *,
    project: dict[str, Any],
    project_id: UUID,
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
    seed_items_cache: list[RelatedNoticeItem] | None = None

    def seed_fallback_items() -> list[RelatedNoticeItem]:
        nonlocal seed_items_cache
        if seed_items_cache is None:
            seed_items_cache = seed_related_notice_items_fn(project, trace_id=trace_id, project_id=project_id)
        return seed_items_cache

    def seed_fallback_response(message: str, *, source: str = "seed_fallback") -> RelatedNoticeListResponse | None:
        if not allow_seed_fallback:
            return None
        items = seed_fallback_items()
        if not items:
            return None
        if trace_id:
            append_related_notice_trace_fn(
                trace_id=trace_id,
                event="seed_fallback_response",
                project_id=project_id,
                project=project,
                payload={"source": source, "message": message, "item_count": len(items)},
            )
        return _build_related_notice_response(
            project=project,
            project_id=project_id,
            status="ready",
            source=source,
            message=message,
            precomputed=False,
            items=items,
        )

    run_rows = project_source_runs_fn(project)
    if not run_rows:
        if trace_id:
            append_related_notice_trace_fn(
                trace_id=trace_id,
                event="response_without_live_missing_run",
                project_id=project_id,
                project=project,
                payload={},
            )
        return _build_related_notice_response(
            project=project,
            project_id=project_id,
            status="missing",
            source="none",
            message="연관 공고 원본 실행을 찾지 못했습니다.",
            precomputed=False,
            items=[],
        )

    latest_success_run = next((row for row in run_rows if str(row.get("status") or "").strip() == "success"), None)
    reference_run = latest_success_run or run_rows[0]
    summary_output = dict((reference_run.get("summary_json") or {}).get("output") or {})
    project_key = str(project.get("_project_match_key") or "").strip()

    cache_row = None
    if project_key:
        try:
            cache_row = get_related_notice_cache_fn(project_key)
        except Exception as exc:
            if is_missing_related_notice_cache_table_error_fn(str(exc)):
                cache_row = None
            else:
                repository_error_fn(str(exc))

    if cache_row is not None:
        cache_payload = dict(cache_row.get("payload_json") or {})
        cache_status = str(cache_row.get("status") or "").strip()
        cache_updated_at = cache_row.get("updated_at")
        cache_error = str(cache_row.get("error") or "").strip()
        cache_stale = is_related_notice_precompute_stale_fn(
            {"updated_at": cache_updated_at},
            cache_status,
            updated_at=cache_updated_at,
        )
        if is_related_notice_payload_entry_precomputed_fn(cache_payload):
            items = [
                RelatedNoticeItem(**dict(item))
                for item in filter_self_related_notice_payload_items_fn(
                    project,
                    dedupe_related_notice_payload_items_fn(list(cache_payload.get("items") or [])),
                )
            ]
            return _build_related_notice_response(
                project=project,
                project_id=project_id,
                status="ready",
                source=str(cache_row.get("source") or "cache"),
                message="",
                precomputed=True,
                items=items,
                groups=dict(cache_payload.get("groups") or {}),
                stats=dict(cache_payload.get("stats") or {}),
            )
        if cache_status == "failed" and not cache_stale:
            fallback_response = seed_fallback_response("같이 수집된 연관 공고를 표시합니다.")
            if fallback_response is not None:
                return fallback_response
            return _build_related_notice_response(
                project=project,
                project_id=project_id,
                status="failed",
                source="precompute",
                message=cache_error or "연관 공고 준비에 실패했습니다.",
                precomputed=False,
                items=[],
            )
        if cache_status in {"queued", "running"} and not cache_stale:
            fallback_response = seed_fallback_response("연관 공고를 준비 중입니다. 잠시 후 다시 열어주세요.")
            if fallback_response is not None:
                return fallback_response
            return _build_related_notice_response(
                project=project,
                project_id=project_id,
                status="pending",
                source="precompute",
                message="연관 공고를 준비 중입니다. 잠시 후 다시 열어주세요.",
                precomputed=False,
                items=[],
            )

    run_precompute_status = str(summary_output.get("related_notice_precompute_status") or "").strip()
    run_precompute_error = str(summary_output.get("related_notice_precompute_error") or "").strip()
    (
        project_precompute_status,
        project_precompute_error,
        project_precompute_updated_at,
        has_project_precompute_state,
    ) = get_related_notice_project_precompute_state_fn(summary_output, project_key)
    precompute_status = project_precompute_status if has_project_precompute_state else ""
    precompute_error = project_precompute_error if has_project_precompute_state else ""
    run_status = str(reference_run.get("status") or "").strip()
    precompute_stale = is_related_notice_precompute_stale_fn(
        reference_run,
        precompute_status,
        updated_at=project_precompute_updated_at,
    )

    if trace_id:
        append_related_notice_trace_fn(
            trace_id=trace_id,
            event="response_without_live_state",
            project_id=project_id,
            project=project,
            payload={
                "reference_run_id": str(reference_run.get("id") or ""),
                "reference_run_status": run_status,
                "precompute_status": precompute_status,
                "precompute_stale": precompute_stale,
                "precompute_error": precompute_error,
                "has_project_precompute_state": has_project_precompute_state,
                "run_precompute_status": run_precompute_status,
                "run_precompute_error": run_precompute_error,
            },
        )

    if precompute_status == "failed":
        fallback_response = seed_fallback_response("연관 공고 저장본 준비에 실패해 같이 수집된 연관 공고를 표시합니다.")
        if fallback_response is not None:
            return fallback_response
        return _build_related_notice_response(
            project=project,
            project_id=project_id,
            status="failed",
            source="precompute",
            message=precompute_error or "연관 공고 사전 준비에 실패했습니다.",
            precomputed=False,
            items=[],
        )

    if has_project_precompute_state and precompute_status in {"queued", "running"} and not precompute_stale:
        if trace_id:
            append_related_notice_trace_fn(
                trace_id=trace_id,
                event="precompute_in_progress",
                project_id=project_id,
                project=project,
                payload={
                    "run_id": str(latest_success_run["id"] or "") if latest_success_run is not None else "",
                    "precompute_status": precompute_status,
                },
            )
        fallback_response = seed_fallback_response("연관 공고를 준비 중입니다. 현재는 같이 수집된 연관 공고를 표시합니다.")
        if fallback_response is not None:
            return fallback_response
        return _build_related_notice_response(
            project=project,
            project_id=project_id,
            status="pending",
            source="precompute",
            message="연관 공고를 준비 중입니다. 잠시 후 다시 열어주세요.",
            precomputed=False,
            items=[],
        )

    if latest_success_run is not None:
        run_id = UUID(str(latest_success_run["id"]))
        run_repository = get_run_repository_fn()
        summary_json = dict(latest_success_run.get("summary_json") or {})
        output = dict(summary_json.get("output") or {})
        if project_key:
            project_statuses = dict(output.get("related_notice_project_statuses") or {})
            project_statuses[project_key] = {
                "status": "queued",
                "error": "",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            output["related_notice_project_statuses"] = project_statuses
        summary_json["output"] = output
        try:
            run_repository.update_run(run_id, {"summary_json": summary_json})
        except Exception as exc:
            repository_error_fn(str(exc))
        if project_key:
            try:
                upsert_related_notice_cache_fn(
                    {
                        "project_key": project_key,
                        "project_name": str(project.get("project_name") or ""),
                        "project_search_name": str(project.get("project_search_name") or ""),
                        "issuer_name": str(project.get("issuer_name") or ""),
                        "status": "queued",
                        "source": "precompute",
                        "algorithm_version": related_notice_algorithm_version,
                        "item_count": 0,
                        "error": "",
                        "payload_json": {},
                        "source_run_id": str(run_id),
                        "generated_at": None,
                    }
                )
            except Exception as exc:
                if not is_missing_related_notice_cache_table_error_fn(str(exc)):
                    repository_error_fn(str(exc))
        queued = queue_related_notice_precompute_for_run_fn(run_id, project_key=project_key)
        if trace_id:
            append_related_notice_trace_fn(
                trace_id=trace_id,
                event="precompute_queued",
                project_id=project_id,
                project=project,
                payload={"run_id": str(run_id), "queued": queued, "precompute_stale": precompute_stale},
            )
        fallback_response = seed_fallback_response(
            "연관 공고 저장본을 준비 중입니다. 현재는 같이 수집된 연관 공고를 표시합니다."
            if queued
            else "연관 공고 저장본 준비를 시작하지 못해 같이 수집된 연관 공고를 표시합니다."
        )
        if fallback_response is not None:
            return fallback_response
        return _build_related_notice_response(
            project=project,
            project_id=project_id,
            status="pending" if queued else "failed",
            source="precompute",
            message=(
                "연관 공고를 다시 준비 중입니다. 잠시 후 다시 열어주세요."
                if precompute_stale and queued
                else "연관 공고를 준비 중입니다. 잠시 후 다시 열어주세요."
                if queued
                else "연관 공고 준비를 시작하지 못했습니다."
            ),
            precomputed=False,
            items=[],
        )

    if run_status in {"queued", "running"}:
        return _build_related_notice_response(
            project=project,
            project_id=project_id,
            status="pending",
            source="run",
            message="프로젝트 실행이 아직 진행 중입니다.",
            precomputed=False,
            items=[],
        )

    fallback_response = seed_fallback_response("같이 수집된 연관 공고를 표시합니다.")
    if fallback_response is not None:
        return fallback_response

    return _build_related_notice_response(
        project=project,
        project_id=project_id,
        status="missing",
        source="none",
        message="연관 공고 저장본이 아직 없습니다.",
        precomputed=False,
        items=[],
    )
