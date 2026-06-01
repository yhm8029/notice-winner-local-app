from __future__ import annotations

from typing import Any
from uuid import UUID

from backend.api.routers import project_aggregate_support as support


def _app_module():
    from backend.api import app as project_aggregate_app

    return project_aggregate_app


def _clear_project_aggregates_cache() -> None:
    app_module = _app_module()
    with app_module._PROJECT_AGGREGATES_CACHE_LOCK:
        app_module._PROJECT_AGGREGATES_CACHE = None
    with app_module._PROJECT_AGGREGATES_WARM_LOCK:
        app_module._PROJECT_AGGREGATES_WARM_ACTIVE = False


def _queue_project_aggregates_cache_warm() -> None:
    app_module = _app_module()
    with app_module._PROJECT_AGGREGATES_CACHE_LOCK:
        cached = app_module._PROJECT_AGGREGATES_CACHE
        if cached is not None and cached[0] > app_module.time.monotonic():
            return
    with app_module._PROJECT_AGGREGATES_WARM_LOCK:
        if app_module._PROJECT_AGGREGATES_WARM_ACTIVE:
            return
        app_module._PROJECT_AGGREGATES_WARM_ACTIVE = True

    def _run() -> None:
        try:
            app_module._build_project_aggregates()
        finally:
            with app_module._PROJECT_AGGREGATES_WARM_LOCK:
                app_module._PROJECT_AGGREGATES_WARM_ACTIVE = False

    app_module.threading.Thread(target=_run, daemon=True).start()


def _build_project_aggregates() -> dict[str, dict[str, Any]]:
    app_module = _app_module()
    now = app_module.time.monotonic()
    with app_module._PROJECT_AGGREGATES_CACHE_LOCK:
        cached = app_module._PROJECT_AGGREGATES_CACHE
        if cached is not None:
            expires_at, payload = cached
            if expires_at > now:
                return payload

    payload = app_module._build_project_aggregates_impl(
        collect_all_runs=app_module._collect_all_runs,
        collect_all_tracker_entries=app_module._collect_all_tracker_entries,
        is_project_tracker_run_type=app_module._is_project_tracker_run_type,
        project_search_name=app_module._project_search_name,
        is_generic_project_term=app_module._is_generic_project_term,
        project_match_key=app_module._project_match_key,
        normalize_tracker_bid_ord_fn=app_module._normalize_tracker_bid_ord,
        upsert_project_aggregate_from_tracker_entry_fn=app_module._upsert_project_aggregate_from_tracker_entry,
        slugify=app_module._slugify,
        better_project_label=app_module._better_project_label,
        better_project_search_name=app_module._better_project_search_name,
        project_namespace=app_module.PROJECT_NAMESPACE,
        utc_now=app_module._utc_now,
    )
    with app_module._PROJECT_AGGREGATES_CACHE_LOCK:
        app_module._PROJECT_AGGREGATES_CACHE = (app_module.time.monotonic() + app_module._PROJECT_AGGREGATES_CACHE_TTL_SEC, payload)
    return payload


def _derive_tracker_entry_project_identity(entry: dict[str, Any]) -> tuple[str, str, str]:
    app_module = _app_module()
    return support._derive_tracker_entry_project_identity(
        entry,
        select_project_search_name_fn=app_module._select_project_search_name,
        project_match_key_fn=app_module._project_match_key,
    )


def _upsert_project_aggregate_from_tracker_entry(
    aggregates: dict[str, dict[str, Any]],
    entry: dict[str, Any],
) -> None:
    app_module = _app_module()
    support._upsert_project_aggregate_from_tracker_entry(
        aggregates,
        entry,
        project_namespace=app_module.PROJECT_NAMESPACE,
        derive_tracker_entry_project_identity_fn=app_module._derive_tracker_entry_project_identity,
        normalize_tracker_bid_ord_fn=app_module._normalize_tracker_bid_ord,
        slugify=app_module._slugify,
        better_project_label=app_module._better_project_label,
        better_project_search_name=app_module._better_project_search_name,
        utc_now=app_module._utc_now,
    )


def _build_project_aggregate_from_tracker_entries(project_id: UUID) -> dict[str, Any] | None:
    app_module = _app_module()
    return support._build_project_aggregate_from_tracker_entries(
        project_id,
        collect_all_tracker_entries_fn=app_module._collect_all_tracker_entries,
        upsert_project_aggregate_from_tracker_entry_fn=app_module._upsert_project_aggregate_from_tracker_entry,
    )


def _to_project_item(item: dict[str, Any]) -> Any:
    app_module = _app_module()
    return support._to_project_item(item, project_item_cls=app_module.ProjectItem, utc_now=app_module._utc_now)


def _build_projects_page(*, page: int, page_size: int, q: str) -> tuple[list[Any], int]:
    app_module = _app_module()
    return support._build_projects_page(
        page=page,
        page_size=page_size,
        q=q,
        build_project_aggregates_fn=app_module._build_project_aggregates,
        norm_text=app_module._norm_text,
        to_project_item_fn=app_module._to_project_item,
    )


def _annotate_tracker_entries_with_project_refs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    app_module = _app_module()
    return support._annotate_tracker_entries_with_project_refs(
        rows,
        derive_tracker_entry_project_identity_fn=app_module._derive_tracker_entry_project_identity,
        project_namespace=app_module.PROJECT_NAMESPACE,
    )


def _normalize_tracker_bid_ord(value: Any) -> str:
    app_module = _app_module()
    return app_module._normalize_tracker_bid_ord_dashboard_impl(value)


def _derive_tracker_entry_bid_identity(entry: dict[str, Any]) -> tuple[str, str]:
    app_module = _app_module()
    return app_module._derive_tracker_entry_bid_identity_dashboard_impl(
        entry,
        normalize_tracker_bid_ord_fn=app_module._normalize_tracker_bid_ord,
    )


def _coerce_uuid_or_none(value: Any) -> UUID | None:
    app_module = _app_module()
    return app_module._coerce_uuid_or_none_impl(value)


def _annotate_tracker_entries_with_opening_dates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    app_module = _app_module()
    return support._annotate_tracker_entries_with_opening_dates(
        rows,
        get_artifact_repository=app_module._get_artifact_repository,
        artifact_repository_error_types=(app_module.ArtifactRepositoryConfigError, app_module.ArtifactRepositoryError),
        load_seed_rows_from_artifact_path=app_module._load_seed_rows_from_artifact_path,
        coerce_uuid_or_none_fn=app_module._coerce_uuid_or_none,
        normalize_tracker_bid_ord_fn=app_module._normalize_tracker_bid_ord,
    )


def _get_project_aggregate(project_id: UUID) -> dict[str, Any]:
    app_module = _app_module()
    for item in app_module._build_project_aggregates().values():
        if item["id"] == project_id:
            return item
    fallback = app_module._build_project_aggregate_from_tracker_entries(project_id)
    if fallback is not None:
        return fallback
    app_module._not_found(f"project not found: {project_id}")


def _get_cached_project_aggregate(project_id: UUID) -> dict[str, Any] | None:
    app_module = _app_module()
    now = app_module.time.monotonic()
    with app_module._PROJECT_AGGREGATES_CACHE_LOCK:
        cached = app_module._PROJECT_AGGREGATES_CACHE
        if cached is None:
            return None
        expires_at, aggregates = cached
        if expires_at <= now:
            return None
        for item in aggregates.values():
            if item.get("id") == project_id:
                return item
    return None


def _snapshot_project_aggregate_from_tracker_row(project_id: UUID, row: dict[str, Any]) -> dict[str, Any] | None:
    app_module = _app_module()
    project_name = str(row.get("project_name") or "").strip()
    source_project_name_norm = str(row.get("source_project_name_norm") or "").strip()
    project_search_name = app_module._select_project_search_name(project_name, source_project_name_norm)
    project_key = app_module._project_match_key(project_search_name or project_name or source_project_name_norm)
    if not project_name or not project_key:
        return None
    source_bid_no = str(row.get("source_bid_no") or "").strip().upper()
    source_bid_ord = app_module._normalize_tracker_bid_ord(row.get("source_bid_ord") or "000") if source_bid_no else ""
    source_run_id = str(row.get("source_run_id") or "").strip()
    source_notice_keys = {(source_bid_no, source_bid_ord)} if source_bid_no else set()
    return {
        "id": project_id,
        "project_name": project_name,
        "project_name_norm": app_module._slugify(project_search_name or project_name),
        "project_search_name": project_search_name,
        "issuer_name": str(row.get("demand_org_name") or "").strip(),
        "latest_notice_date": str(row.get("notice_date") or "").strip(),
        "latest_notice_title": project_name,
        "source_json": {
            "run_ids": [source_run_id] if source_run_id else [],
            "winner_csv_rows": 0,
            "tracker_entry_rows": 1,
            "source_bid_no": source_bid_no,
            "source_bid_ord": source_bid_ord,
        },
        "created_at": row.get("created_at") or app_module._utc_now(),
        "updated_at": row.get("updated_at") or row.get("created_at") or app_module._utc_now(),
        "_project_match_key": project_key,
        "_source_notice_keys": source_notice_keys,
    }


def _get_snapshot_project_aggregate(project_id: UUID) -> dict[str, Any] | None:
    app_module = _app_module()
    cached_project = app_module._get_cached_project_aggregate(project_id)
    if cached_project is not None:
        return cached_project
    for row in app_module._load_global_tracker_rows():
        try:
            row_project_id = UUID(str(row.get("project_id") or ""))
        except ValueError:
            continue
        if row_project_id != project_id:
            continue
        return app_module._snapshot_project_aggregate_from_tracker_row(project_id, row)
    return None
