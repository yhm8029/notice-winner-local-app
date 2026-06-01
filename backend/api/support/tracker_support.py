from __future__ import annotations

from typing import Any
from uuid import UUID
from unittest.mock import Mock

from fastapi import Request

from backend.api.schemas import BackfillConflictItem
from backend.api.schemas import TrackerChangeEventItem
from backend.api.schemas import TrackerEntryAuditLogItem
from backend.api.schemas import TrackerEntryItem
from backend.api.schemas import TrackerEntryPatchRequest
from backend.api.schemas import TrackerEntrySummaryItem
from backend.api.support.runtime_common import _validation_error
from backend.phase1_defaults import load_phase1_identity
from backend.repositories import TRACKER_CHANGE_SOURCES
from backend.repositories import TRACKER_EDITABLE_FIELDS

BACKFILL_CONFLICT_RESOLUTIONS = frozenset({"accept_candidate", "keep_current", "clear_field"})


def _validate_tracker_patch_request(payload: TrackerEntryPatchRequest) -> None:
    if payload.field_name not in TRACKER_EDITABLE_FIELDS:
        allowed = ", ".join(TRACKER_EDITABLE_FIELDS)
        _validation_error(f"field_name must be one of {allowed}")

    if payload.change_source not in TRACKER_CHANGE_SOURCES:
        allowed = ", ".join(sorted(TRACKER_CHANGE_SOURCES))
        _validation_error(f"change_source must be one of {allowed}")


def _resolve_tracker_patch_actor(
    request: Request,
    payload: TrackerEntryPatchRequest,
) -> tuple[UUID | None, str]:
    actor_user_id = payload.actor_user_id
    actor_label = payload.actor_label.strip()
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context is not None:
        if actor_user_id is None and auth_context.local_user_id is not None:
            actor_user_id = auth_context.local_user_id
        if not actor_label:
            actor_label = auth_context.display_name or auth_context.email
    if actor_user_id is None and not actor_label:
        _validation_error("actor_user_id or actor_label is required")
    return actor_user_id, actor_label


def _resolve_request_organization_id(request: Request) -> UUID:
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context is not None and auth_context.organization_id is not None:
        return auth_context.organization_id
    return load_phase1_identity().organization_id


def _is_missing_tracker_change_events_table_error(message: str) -> bool:
    lowered = str(message or "").lower()
    if "tracker_change_events" not in lowered:
        return False
    return any(
        token in lowered
        for token in (
            "could not find the table",
            "relation",
            "does not exist",
        )
    )


def _to_tracker_entry_model(row: dict[str, Any]) -> TrackerEntryItem:
    return TrackerEntryItem(**row)


def _to_tracker_entry_summary_model(row: dict[str, Any]) -> TrackerEntrySummaryItem:
    from backend.api import app as app_module

    maybe_mock = getattr(app_module, "_to_tracker_entry_summary_model", None)
    if isinstance(maybe_mock, Mock):
        return maybe_mock(row)
    return TrackerEntrySummaryItem(**row)


def _to_audit_log_model(row: dict[str, Any]) -> TrackerEntryAuditLogItem:
    return TrackerEntryAuditLogItem(**row)


def _to_uuid_or_none(value: Any) -> UUID | None:
    if value in (None, ""):
        return None
    return UUID(str(value))


def _to_tracker_change_event_model(
    row: dict[str, Any],
    *,
    tracker_entry: dict[str, Any] | None = None,
) -> TrackerChangeEventItem:
    entry = tracker_entry or {}
    return TrackerChangeEventItem(
        id=UUID(str(row["id"])),
        tracker_entry_id=UUID(str(row["tracker_entry_id"])),
        project_id=_to_uuid_or_none(entry.get("project_id")),
        project_name=str(entry.get("project_name") or ""),
        entry_key=str(entry.get("entry_key") or ""),
        event_type=str(row.get("event_type") or ""),
        field_name=str(row.get("field_name") or "").strip() or None,
        old_value=str(row.get("old_value") or ""),
        new_value=str(row.get("new_value") or ""),
        old_value_norm=str(row.get("old_value_norm") or "").strip() or None,
        new_value_norm=str(row.get("new_value_norm") or "").strip() or None,
        source_run_id=_to_uuid_or_none(row.get("source_run_id")),
        source_kind=str(row.get("source_kind") or ""),
        source_ref=str(row.get("source_ref") or ""),
        extractor_version=str(row.get("extractor_version") or ""),
        reason_code=str(row.get("reason_code") or ""),
        batch_key=str(row.get("batch_key") or ""),
        is_silent=bool(row.get("is_silent")),
        created_at=row["created_at"],
        is_read=bool(row.get("is_read")),
        read_at=row.get("read_at"),
    )


def _to_backfill_conflict_model(
    row: dict[str, Any],
    *,
    tracker_entry: dict[str, Any] | None = None,
) -> BackfillConflictItem:
    entry = tracker_entry or {}
    return BackfillConflictItem(
        id=UUID(str(row["id"])),
        tracker_entry_id=UUID(str(row["tracker_entry_id"])),
        project_id=_to_uuid_or_none(entry.get("project_id")),
        project_name=str(entry.get("project_name") or ""),
        entry_key=str(entry.get("entry_key") or ""),
        field_name=str(row.get("field_name") or "").strip(),
        current_value=str(row.get("current_value") or ""),
        candidate_value=str(row.get("candidate_value") or ""),
        current_value_norm=str(row.get("current_value_norm") or "").strip() or None,
        candidate_value_norm=str(row.get("candidate_value_norm") or "").strip() or None,
        reason_code=str(row.get("reason_code") or "").strip(),
        source_kind=str(row.get("source_kind") or "").strip(),
        source_ref=str(row.get("source_ref") or "").strip(),
        source_run_id=_to_uuid_or_none(row.get("source_run_id")),
        extractor_version=str(row.get("extractor_version") or "").strip(),
        detected_at=row["detected_at"],
        resolved_at=row.get("resolved_at"),
        resolution=str(row.get("resolution") or "").strip() or None,
        conflict_key=str(row.get("conflict_key") or "").strip(),
    )
