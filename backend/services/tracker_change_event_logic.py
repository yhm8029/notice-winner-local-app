from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from uuid import UUID

from .backfill_policy import normalize_area_value
from .backfill_policy import normalize_contact_value
from .backfill_policy import normalize_cost_value


@dataclass(frozen=True)
class TrackerEventBuildInput:
    organization_id: UUID
    tracker_entry_id: UUID
    event_type: str
    field_name: str | None
    old_value: str
    new_value: str
    source_kind: str
    source_run_id: UUID | None = None
    source_ref: str = ""
    extractor_version: str = ""
    reason_code: str = ""
    batch_key: str = ""
    is_silent: bool = False


def normalize_tracker_change_value(field_name: str | None, value: Any) -> str:
    if field_name == "gross_area_scale":
        return normalize_area_value(value)
    if field_name == "construction_cost":
        return normalize_cost_value(value)
    if field_name == "demand_contact":
        return normalize_contact_value(value)
    return str(value or "").strip()


def build_tracker_change_event(input_item: TrackerEventBuildInput) -> dict[str, Any] | None:
    old_value = str(input_item.old_value or "")
    new_value = str(input_item.new_value or "")
    old_norm = normalize_tracker_change_value(input_item.field_name, old_value)
    new_norm = normalize_tracker_change_value(input_item.field_name, new_value)
    if old_norm == new_norm:
        return None
    dedupe_key = build_tracker_change_event_dedupe_key(
        tracker_entry_id=input_item.tracker_entry_id,
        event_type=input_item.event_type,
        field_name=input_item.field_name or "",
        old_value_norm=old_norm,
        new_value_norm=new_norm,
        source_kind=input_item.source_kind,
        source_run_id=input_item.source_run_id,
        source_ref=input_item.source_ref,
        batch_key=input_item.batch_key,
    )
    return {
        "organization_id": str(input_item.organization_id),
        "tracker_entry_id": input_item.tracker_entry_id,
        "event_type": input_item.event_type,
        "field_name": input_item.field_name,
        "old_value": old_value,
        "new_value": new_value,
        "old_value_norm": old_norm,
        "new_value_norm": new_norm,
        "source_run_id": input_item.source_run_id,
        "source_kind": input_item.source_kind,
        "source_ref": str(input_item.source_ref or "").strip(),
        "extractor_version": str(input_item.extractor_version or "").strip(),
        "reason_code": str(input_item.reason_code or "").strip(),
        "batch_key": str(input_item.batch_key or "").strip(),
        "dedupe_key": dedupe_key,
        "is_silent": bool(input_item.is_silent),
        "is_read": False,
    }


def build_tracker_change_event_dedupe_key(
    *,
    tracker_entry_id: UUID,
    event_type: str,
    field_name: str,
    old_value_norm: str,
    new_value_norm: str,
    source_kind: str,
    source_run_id: UUID | None,
    source_ref: str,
    batch_key: str,
) -> str:
    raw = "|".join(
        (
            str(tracker_entry_id),
            str(event_type or "").strip(),
            str(field_name or "").strip(),
            str(old_value_norm or "").strip(),
            str(new_value_norm or "").strip(),
            str(source_kind or "").strip(),
            str(source_run_id or "").strip(),
            str(source_ref or "").strip(),
            str(batch_key or "").strip(),
        )
    )
    return sha256(raw.encode("utf-8")).hexdigest()


def build_backfill_conflict_key(
    *,
    tracker_entry_id: UUID,
    field_name: str,
    current_value_norm: str,
    candidate_value_norm: str,
    source_kind: str,
    source_ref: str,
) -> str:
    raw = "|".join(
        (
            str(tracker_entry_id),
            str(field_name or "").strip(),
            str(current_value_norm or "").strip(),
            str(candidate_value_norm or "").strip(),
            str(source_kind or "").strip(),
            str(source_ref or "").strip(),
        )
    )
    return sha256(raw.encode("utf-8")).hexdigest()
