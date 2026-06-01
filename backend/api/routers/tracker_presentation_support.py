from __future__ import annotations

from typing import Any

from backend.api.schemas import TrackerEntryItem
from backend.api.schemas import TrackerEntrySummaryItem
from backend.services.tracker_entry_snapshot_backend import normalize_tracker_entry_presentation as _normalize_tracker_entry_presentation_impl
from backend.services.tracker_entry_snapshot_backend import normalize_tracker_rows_for_presentation as _normalize_tracker_rows_for_presentation_impl
from backend.services.tracker_global_summary_backend import collapse_tracker_rows_by_project as _collapse_tracker_rows_by_project_impl
from backend.services.tracker_global_summary_backend import filter_tracker_rows_for_global_scope as _filter_tracker_rows_for_global_scope_impl
from backend.services.tracker_global_summary_backend import merge_global_tracker_row_group as _merge_global_tracker_row_group_impl
from backend.services.tracker_global_summary_backend import tracker_row_merge_identity as _tracker_row_merge_identity_impl
from backend.services.tracker_global_summary_backend import tracker_row_merge_score as _tracker_row_merge_score_impl


def _to_tracker_entry_model(row: dict[str, Any]) -> TrackerEntryItem:
    return TrackerEntryItem(**row)


def _to_tracker_entry_summary_model(row: dict[str, Any]) -> TrackerEntrySummaryItem:
    return TrackerEntrySummaryItem(**row)


def _normalize_tracker_entry_presentation(
    entry: dict[str, Any],
    *,
    winner_row: dict[str, str] | None,
) -> dict[str, Any]:
    return _normalize_tracker_entry_presentation_impl(entry, winner_row=winner_row)


def _normalize_tracker_rows_for_presentation(
    rows: list[dict[str, Any]],
    *,
    lookup_winner_row_for_entry_fn: Any,
) -> list[dict[str, Any]]:
    return _normalize_tracker_rows_for_presentation_impl(
        rows,
        lookup_winner_row_for_entry_fn=lookup_winner_row_for_entry_fn,
    )


def _tracker_row_merge_score(row: dict[str, Any]) -> tuple[int, int, int, int]:
    return _tracker_row_merge_score_impl(row)


def _tracker_row_merge_identity(
    row: dict[str, Any],
    *,
    normalize_tracker_bid_ord_fn: Any,
    norm_text_fn: Any,
) -> tuple[str, str, str]:
    return _tracker_row_merge_identity_impl(
        row,
        normalize_tracker_bid_ord_fn=normalize_tracker_bid_ord_fn,
        norm_text_fn=norm_text_fn,
    )


def _merge_global_tracker_row_group(
    rows: list[dict[str, Any]],
    *,
    tracker_row_merge_score_fn: Any,
    tracker_row_merge_identity_fn: Any,
    better_project_label_fn: Any,
) -> dict[str, Any]:
    return _merge_global_tracker_row_group_impl(
        rows,
        tracker_row_merge_score_fn=tracker_row_merge_score_fn,
        tracker_row_merge_identity_fn=tracker_row_merge_identity_fn,
        better_project_label_fn=better_project_label_fn,
    )


def _collapse_tracker_rows_by_project(
    rows: list[dict[str, Any]],
    *,
    derive_tracker_entry_project_identity_fn: Any,
    norm_text_fn: Any,
    merge_global_tracker_row_group_fn: Any,
) -> list[dict[str, Any]]:
    return _collapse_tracker_rows_by_project_impl(
        rows,
        derive_tracker_entry_project_identity_fn=derive_tracker_entry_project_identity_fn,
        norm_text_fn=norm_text_fn,
        merge_global_tracker_row_group_fn=merge_global_tracker_row_group_fn,
    )


def _filter_tracker_rows_for_global_scope(
    rows: list[dict[str, Any]],
    *,
    q: str,
    region: str,
    exclude_auxiliary_titles: bool,
    edited_only: bool,
    norm_text_fn: Any,
    tracker_entry_matches_title_visibility_fn: Any,
    tracker_entry_matches_region_fn: Any,
) -> list[dict[str, Any]]:
    return _filter_tracker_rows_for_global_scope_impl(
        rows,
        q=q,
        region=region,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        edited_only=edited_only,
        norm_text_fn=norm_text_fn,
        tracker_entry_matches_title_visibility_fn=tracker_entry_matches_title_visibility_fn,
        tracker_entry_matches_region_fn=tracker_entry_matches_region_fn,
    )


def _is_global_tracker_scope(
    *,
    source_run_id: Any,
    source_tracker_run_id: Any,
    sheet_name: str,
    section_name: str,
) -> bool:
    return (
        source_run_id is None
        and source_tracker_run_id is None
        and not str(sheet_name or "").strip()
        and not str(section_name or "").strip()
    )
