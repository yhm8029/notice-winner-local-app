from __future__ import annotations

from typing import Any
from uuid import UUID

from backend.services.project_dashboard_backend import annotate_tracker_entries_with_opening_dates as _annotate_tracker_entries_with_opening_dates_impl
from backend.services.project_dashboard_backend import annotate_tracker_entries_with_project_refs as _annotate_tracker_entries_with_project_refs_impl
from backend.services.project_dashboard_backend import build_project_aggregate_from_tracker_entries as _build_project_aggregate_from_tracker_entries_impl
from backend.services.project_dashboard_backend import build_projects_page as _build_projects_page_impl
from backend.services.project_dashboard_backend import coerce_uuid_or_none as _coerce_uuid_or_none_impl
from backend.services.project_dashboard_backend import derive_tracker_entry_project_identity as _derive_tracker_entry_project_identity_impl
from backend.services.project_dashboard_backend import normalize_tracker_bid_ord as _normalize_tracker_bid_ord_impl
from backend.services.project_dashboard_backend import to_project_item as _to_project_item_impl
from backend.services.project_dashboard_backend import upsert_project_aggregate_from_tracker_entry as _upsert_project_aggregate_from_tracker_entry_impl


def _normalize_tracker_bid_ord(value: Any) -> str:
    return _normalize_tracker_bid_ord_impl(value)


def _coerce_uuid_or_none(value: Any) -> UUID | None:
    return _coerce_uuid_or_none_impl(value)


def _derive_tracker_entry_project_identity(
    entry: dict[str, Any],
    *,
    select_project_search_name_fn: Any,
    project_match_key_fn: Any,
) -> tuple[str, str, str]:
    return _derive_tracker_entry_project_identity_impl(
        entry,
        select_project_search_name=select_project_search_name_fn,
        project_match_key=project_match_key_fn,
    )


def _upsert_project_aggregate_from_tracker_entry(
    aggregates: dict[str, dict[str, Any]],
    entry: dict[str, Any],
    *,
    project_namespace: UUID,
    derive_tracker_entry_project_identity_fn: Any,
    normalize_tracker_bid_ord_fn: Any,
    slugify: Any,
    better_project_label: Any,
    better_project_search_name: Any,
    utc_now: Any,
) -> None:
    _upsert_project_aggregate_from_tracker_entry_impl(
        aggregates,
        entry,
        project_namespace=project_namespace,
        derive_tracker_entry_project_identity_fn=derive_tracker_entry_project_identity_fn,
        normalize_tracker_bid_ord_fn=normalize_tracker_bid_ord_fn,
        slugify=slugify,
        better_project_label=better_project_label,
        better_project_search_name=better_project_search_name,
        utc_now=utc_now,
    )


def _build_project_aggregate_from_tracker_entries(
    project_id: UUID,
    *,
    collect_all_tracker_entries_fn: Any,
    upsert_project_aggregate_from_tracker_entry_fn: Any,
) -> dict[str, Any] | None:
    return _build_project_aggregate_from_tracker_entries_impl(
        project_id,
        collect_all_tracker_entries=collect_all_tracker_entries_fn,
        upsert_project_aggregate_from_tracker_entry_fn=upsert_project_aggregate_from_tracker_entry_fn,
    )


def _to_project_item(item: dict[str, Any], *, project_item_cls: Any, utc_now: Any) -> Any:
    return _to_project_item_impl(item, project_item_cls=project_item_cls, utc_now=utc_now)


def _build_projects_page(
    *,
    page: int,
    page_size: int,
    q: str,
    build_project_aggregates_fn: Any,
    norm_text: Any,
    to_project_item_fn: Any,
) -> tuple[list[Any], int]:
    return _build_projects_page_impl(
        page=page,
        page_size=page_size,
        q=q,
        build_project_aggregates_fn=build_project_aggregates_fn,
        norm_text=norm_text,
        to_project_item_fn=to_project_item_fn,
    )


def _annotate_tracker_entries_with_project_refs(
    rows: list[dict[str, Any]],
    *,
    derive_tracker_entry_project_identity_fn: Any,
    project_namespace: UUID,
) -> list[dict[str, Any]]:
    return _annotate_tracker_entries_with_project_refs_impl(
        rows,
        derive_tracker_entry_project_identity_fn=derive_tracker_entry_project_identity_fn,
        project_namespace=project_namespace,
    )


def _annotate_tracker_entries_with_opening_dates(
    rows: list[dict[str, Any]],
    *,
    get_artifact_repository: Any,
    artifact_repository_error_types: tuple[type[Exception], ...],
    load_seed_rows_from_artifact_path: Any,
    coerce_uuid_or_none_fn: Any,
    normalize_tracker_bid_ord_fn: Any,
) -> list[dict[str, Any]]:
    return _annotate_tracker_entries_with_opening_dates_impl(
        rows,
        get_artifact_repository=get_artifact_repository,
        artifact_repository_error_types=artifact_repository_error_types,
        load_seed_rows_from_artifact_path=load_seed_rows_from_artifact_path,
        coerce_uuid_or_none_fn=coerce_uuid_or_none_fn,
        normalize_tracker_bid_ord_fn=normalize_tracker_bid_ord_fn,
    )
