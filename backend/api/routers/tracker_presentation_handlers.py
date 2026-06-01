from __future__ import annotations

from typing import Any
from uuid import UUID

from backend.api.routers import tracker_presentation_support as support


def _app_module():
    from backend.api import app as tracker_presentation_app

    return tracker_presentation_app


def _to_tracker_entry_model(row: dict[str, Any]) -> Any:
    return support._to_tracker_entry_model(row)


def _to_tracker_entry_summary_model(row: dict[str, Any]) -> Any:
    return support._to_tracker_entry_summary_model(row)


def _normalize_tracker_entry_presentation(
    entry: dict[str, Any],
    *,
    winner_row: dict[str, str] | None,
) -> dict[str, Any]:
    return support._normalize_tracker_entry_presentation(entry, winner_row=winner_row)


def _normalize_tracker_rows_for_presentation(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    app_module = _app_module()
    return support._normalize_tracker_rows_for_presentation(
        rows,
        lookup_winner_row_for_entry_fn=app_module._lookup_winner_row_for_entry,
    )


def _tracker_row_merge_score(row: dict[str, Any]) -> tuple[int, int, int, int]:
    return support._tracker_row_merge_score(row)


def _tracker_row_merge_identity(row: dict[str, Any]) -> tuple[str, str, str]:
    app_module = _app_module()
    return support._tracker_row_merge_identity(
        row,
        normalize_tracker_bid_ord_fn=app_module._normalize_tracker_bid_ord,
        norm_text_fn=app_module._norm_text,
    )


def _merge_global_tracker_row_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    app_module = _app_module()
    return support._merge_global_tracker_row_group(
        rows,
        tracker_row_merge_score_fn=app_module._tracker_row_merge_score,
        tracker_row_merge_identity_fn=app_module._tracker_row_merge_identity,
        better_project_label_fn=app_module._better_project_label,
    )


def _collapse_tracker_rows_by_project(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    app_module = _app_module()
    return support._collapse_tracker_rows_by_project(
        rows,
        derive_tracker_entry_project_identity_fn=app_module._derive_tracker_entry_project_identity,
        norm_text_fn=app_module._norm_text,
        merge_global_tracker_row_group_fn=app_module._merge_global_tracker_row_group,
    )


def _filter_tracker_rows_for_global_scope(
    rows: list[dict[str, Any]],
    *,
    q: str,
    region: str,
    exclude_auxiliary_titles: bool,
    edited_only: bool,
) -> list[dict[str, Any]]:
    app_module = _app_module()
    return support._filter_tracker_rows_for_global_scope(
        rows,
        q=q,
        region=region,
        exclude_auxiliary_titles=exclude_auxiliary_titles,
        edited_only=edited_only,
        norm_text_fn=app_module._norm_text,
        tracker_entry_matches_title_visibility_fn=app_module.tracker_entry_matches_title_visibility,
        tracker_entry_matches_region_fn=app_module.tracker_entry_matches_region,
    )


def _load_all_tracker_entries_for_export(
    *,
    q: str,
    region: str,
    exclude_auxiliary_titles: bool,
    edited_only: bool,
    source_run_id: UUID | None,
    source_tracker_run_id: UUID | None,
    sheet_name: str,
    section_name: str,
) -> list[dict[str, Any]]:
    app_module = _app_module()
    tracker_repository = app_module._get_tracker_repository()
    organization_id = app_module.load_phase1_identity().organization_id
    page = 1
    page_size = 500
    rows: list[dict[str, Any]] = []
    while True:
        try:
            batch, _total = tracker_repository.list_entries_for_export(
                page=page,
                page_size=page_size,
                q=q,
                region=region,
                exclude_auxiliary_titles=exclude_auxiliary_titles,
                edited_only=edited_only,
                source_run_id=source_run_id,
                source_tracker_run_id=source_tracker_run_id,
                sheet_name=sheet_name,
                section_name=section_name,
            )
        except app_module.TrackerEntryRepositoryError as exc:
            app_module._repository_error(str(exc))
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page_size:
            break
        page += 1
    return app_module._hydrate_tracker_entry_export_rows(
        organization_id=organization_id,
        rows=rows,
    )


def _is_global_tracker_scope(
    *,
    source_run_id: UUID | None,
    source_tracker_run_id: UUID | None,
    sheet_name: str,
    section_name: str,
) -> bool:
    return support._is_global_tracker_scope(
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        sheet_name=sheet_name,
        section_name=section_name,
    )
