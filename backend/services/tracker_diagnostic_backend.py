from __future__ import annotations

import csv
from datetime import datetime, timezone
import re
from typing import Any
from uuid import UUID

from backend.repositories import ArtifactRepositoryError
from backend.repositories import ArtifactRepositoryConfigError
from backend.services.tracker_field_provenance import TRACKER_CONTRACT_SOURCE_LABELS
from backend.services.tracker_field_provenance import TRACKER_MISSING_REASON_EXPLAINERS
from backend.services.tracker_field_provenance import TRACKER_SOURCE_REASON_LABELS
from backend.services.tracker_field_provenance import TRACKER_TRUSTED_SOURCE_TYPES
from backend.services.tracker_field_provenance import build_tracker_field_diagnostic
from backend.services.tracker_field_provenance import classify_tracker_field_missing as _classify_tracker_field_missing
from backend.services.tracker_field_provenance import _humanize_contract_source_type
from backend.services.tracker_field_provenance import _humanize_tracker_source_label
from backend.services.tracker_field_provenance import _humanize_tracker_source_reason
from backend.services.tracker_field_provenance import _is_expected_blank_tracker_field
from backend.services.tracker_field_provenance import _winner_row_has_allowed_source_signal


def normalize_tracker_bid_ord(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "000"
    if raw.isdigit():
        return f"{int(raw):03d}"
    return raw


def derive_tracker_entry_bid_identity(entry: dict[str, Any]) -> tuple[str, str]:
    bid_no = str(entry.get("source_bid_no") or "").strip().upper()
    bid_ord_raw = entry.get("source_bid_ord") or "000"
    if not bid_no:
        entry_key = str(entry.get("entry_key") or "").strip()
        bid_part, sep, remainder = entry_key.partition("|")
        if sep and bid_part.strip():
            bid_no = bid_part.strip().upper()
            ord_part, sep2, _ = remainder.partition("|")
            if sep2 and ord_part.strip():
                bid_ord_raw = ord_part.strip()
    return bid_no, normalize_tracker_bid_ord(bid_ord_raw)


def tracker_entry_missing_key(entry: dict[str, Any]) -> tuple[str, str, str]:
    bid_no, bid_ord = derive_tracker_entry_bid_identity(entry)
    return (
        bid_no,
        bid_ord,
        str(entry.get("source_project_name_norm") or "").strip().lower(),
    )


def tracker_entry_updated_key(entry: dict[str, Any]) -> tuple[str, str]:
    return (
        str(entry.get("updated_at") or "").strip(),
        str(entry.get("created_at") or "").strip(),
    )


def is_tracker_value_blank(value: Any) -> bool:
    text = str(value or "").strip()
    return not text or text == "-"


def humanize_tracker_source_reason(
    *,
    field_key: str,
    winner_row: dict[str, str] | None,
    source_field_name: str,
) -> str:
    return _humanize_tracker_source_reason(
        field_key=field_key,
        winner_row=winner_row,
        source_field_name=source_field_name,
    )


def humanize_tracker_source_label(source_key: str) -> str:
    return _humanize_tracker_source_label(source_key)


def humanize_contract_source_type(source_type: str) -> str:
    return _humanize_contract_source_type(source_type)


def winner_row_has_allowed_source_signal(winner_row: dict[str, str] | None) -> bool:
    return _winner_row_has_allowed_source_signal(winner_row)


def is_expected_blank_tracker_field(field_key: str, project_name: str) -> bool:
    return _is_expected_blank_tracker_field(field_key, project_name)


def classify_tracker_missing_field(
    *,
    field_key: str,
    project_name: str,
    winner_row: dict[str, str] | None,
    source_field_name: str,
) -> tuple[str, str]:
    return _classify_tracker_field_missing(
        field_key=field_key,
        project_name=project_name,
        winner_row=winner_row,
        source_field_name=source_field_name,
    )


def load_seed_rows_from_artifact_path(storage_path: str) -> list[dict[str, str]]:
    from backend.services.artifact_files import resolve_artifact_path

    artifact_path = resolve_artifact_path(storage_path)
    if not artifact_path.exists():
        return []
    with artifact_path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        return [{key: str(value or "").strip() for key, value in row.items()} for row in reader]


def load_csv_rows_from_artifact_path(storage_path: str) -> list[dict[str, str]]:
    from backend.services.artifact_files import resolve_artifact_path

    artifact_path = resolve_artifact_path(storage_path)
    if not artifact_path.exists():
        return []
    with artifact_path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        return [{key: str(value or "").strip() for key, value in row.items()} for row in reader]


def load_winner_index_by_run(
    *,
    run_id: UUID,
    get_artifact_repository: Any,
) -> tuple[dict[tuple[str, str, str], dict[str, str]], dict[tuple[str, str], dict[str, str]]]:
    try:
        artifact_repository = get_artifact_repository()
    except ArtifactRepositoryConfigError:
        return {}, {}

    try:
        artifacts = artifact_repository.list_artifacts(run_id=run_id)
    except ArtifactRepositoryError:
        return {}, {}

    winner_artifact = next(
        (
            item for item in artifacts
            if str(item.get("artifact_type") or "").strip() == "winner_csv"
            or str(item.get("file_name") or "").strip() == "project_tracker_posts_files_v1_1.csv"
        ),
        None,
    )
    if winner_artifact is None:
        return {}, {}

    storage_path = str(winner_artifact.get("storage_path") or "").strip()
    if not storage_path:
        return {}, {}

    exact: dict[tuple[str, str, str], dict[str, str]] = {}
    coarse: dict[tuple[str, str], dict[str, str]] = {}
    for row in load_csv_rows_from_artifact_path(storage_path):
        bid_no = str(row.get("bid_no") or "").strip().upper()
        bid_ord = normalize_tracker_bid_ord(row.get("bid_ord") or "000")
        project_name_norm = str(row.get("project_name_norm") or "").strip().lower()
        if not bid_no:
            continue
        exact[(bid_no, bid_ord, project_name_norm)] = row
        coarse.setdefault((bid_no, bid_ord), row)
    return exact, coarse


def lookup_winner_row_for_entry(
    entry: dict[str, Any],
    cache: dict[UUID, tuple[dict[tuple[str, str, str], dict[str, str]], dict[tuple[str, str], dict[str, str]]]],
    *,
    load_winner_index_by_run_fn: Any,
    coerce_uuid_or_none: Any,
) -> dict[str, str] | None:
    source_run_id = coerce_uuid_or_none(entry.get("source_run_id"))
    if source_run_id is None:
        return None
    if source_run_id not in cache:
        cache[source_run_id] = load_winner_index_by_run_fn(run_id=source_run_id)
    exact, coarse = cache[source_run_id]
    bid_no, bid_ord, project_name_norm = tracker_entry_missing_key(entry)
    if not bid_no:
        return None
    return exact.get((bid_no, bid_ord, project_name_norm)) or coarse.get((bid_no, bid_ord))


def build_tracker_entry_field_diagnostics(
    entry: dict[str, Any],
    winner_row: dict[str, str] | None,
    *,
    field_specs: tuple[tuple[str, str, str], ...],
) -> list[dict[str, str]]:
    raw_source_type = str((winner_row or {}).get("source_type") or "").strip()
    raw_reason_code = str((winner_row or {}).get("reason_code") or "").strip()
    raw_evidence_source = str((winner_row or {}).get("evidence_source") or "").strip()
    winner_name = str((winner_row or {}).get("winner_name") or "").strip()
    overridden_fields = set(entry.get("overridden_fields") or [])

    diagnostics: list[dict[str, str]] = []
    for field_key, field_label, source_field_name in field_specs:
        source_key = (
            "manual_override"
            if field_key in overridden_fields
            else str((winner_row or {}).get(source_field_name) or "").strip()
        )
        source_reason = (
            "수동 보정이 현재 적용 중입니다."
            if source_key == "manual_override"
            else _humanize_tracker_source_reason(
                field_key=field_key,
                winner_row=winner_row,
                source_field_name=source_field_name,
            )
        )
        evidence_parts: list[str] = []
        if raw_evidence_source:
            evidence_parts.append(raw_evidence_source)
        raw_field_name = "notice_construction_cost" if field_key == "construction_cost" else field_key
        raw_field_value = str((winner_row or {}).get(raw_field_name) or "").strip()
        if raw_field_value:
            evidence_parts.append(f"value={raw_field_value}")
        if field_key == "architect_office" and winner_name:
            evidence_parts.append(f"winner_name={winner_name}")
        evidence_preview = " | ".join(part for part in evidence_parts if part)
        diagnostics.append(
            {
                "field_key": field_key,
                "field_label": field_label,
                "source_key": source_key,
                "source_label": _humanize_tracker_source_label(source_key),
                "source_type": raw_source_type,
                "source_type_label": _humanize_contract_source_type(raw_source_type),
                "reason_code": raw_reason_code,
                "source_reason": source_reason,
                "evidence_preview": evidence_preview,
            }
        )
    return diagnostics


def annotate_tracker_entries_with_field_diagnostics(
    rows: list[dict[str, Any]],
    *,
    load_winner_index_by_run_fn: Any,
    coerce_uuid_or_none: Any,
    field_specs: tuple[tuple[str, str, str], ...],
    build_tracker_field_diagnostic_fn: Any = build_tracker_field_diagnostic,
) -> list[dict[str, Any]]:
    winner_cache: dict[UUID, tuple[dict[tuple[str, str, str], dict[str, str]], dict[tuple[str, str], dict[str, str]]]] = {}
    enriched: list[dict[str, Any]] = []
    for row in rows:
        entry = dict(row)
        winner_row = lookup_winner_row_for_entry(
            entry,
            winner_cache,
            load_winner_index_by_run_fn=load_winner_index_by_run_fn,
            coerce_uuid_or_none=coerce_uuid_or_none,
        )
        entry["source_type"] = str((winner_row or {}).get("source_type") or "").strip()
        entry["reason_code"] = str((winner_row or {}).get("reason_code") or "").strip()
        entry["evidence_source"] = str((winner_row or {}).get("evidence_source") or "").strip()
        entry["gross_area_scale_source"] = str((winner_row or {}).get("gross_area_scale_source") or "").strip()
        entry["construction_cost_source"] = str((winner_row or {}).get("notice_construction_cost_source") or "").strip()
        entry["demand_contact_source"] = str((winner_row or {}).get("demand_contact_source") or "").strip()
        entry["architect_office_source"] = str((winner_row or {}).get("architect_office_source") or "").strip()
        entry["field_diagnostics"] = [
            build_tracker_field_diagnostic_fn(
                entry=entry,
                winner_row=winner_row,
                field_key=field_key,
                field_label=field_label,
                source_field_name=source_field_name,
            )
            for field_key, field_label, source_field_name in field_specs
        ]
        enriched.append(entry)
    return enriched


def build_tracker_missing_report(
    *,
    limit: int,
    collect_all_tracker_entries: Any,
    load_winner_index_by_run_fn: Any,
    coerce_uuid_or_none: Any,
    tracker_missing_field_specs: tuple[tuple[str, str, str], ...],
    tracker_missing_reason_explainers: dict[str, str],
) -> tuple[TrackerMissingReportSummary, list[TrackerMissingReportItem]]:
    from backend.api.schemas import TrackerMissingFieldItem
    from backend.api.schemas import TrackerMissingReportItem
    from backend.api.schemas import TrackerMissingReportSummary

    entries = collect_all_tracker_entries()
    deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for entry in entries:
        key = tracker_entry_missing_key(entry)
        current = deduped.get(key)
        if current is None or tracker_entry_updated_key(entry) >= tracker_entry_updated_key(current):
            deduped[key] = entry

    preview_specs: list[tuple[dict[str, Any], list[tuple[str, str, str]]]] = []
    missing_entries = 0
    contact_missing = 0
    architect_missing = 0
    area_missing = 0

    for entry in sorted(deduped.values(), key=tracker_entry_updated_key, reverse=True):
        missing_specs: list[tuple[str, str, str]] = []
        for field_key, field_label, source_field_name in tracker_missing_field_specs:
            if not is_tracker_value_blank(entry.get(field_key)):
                continue
            if field_key == "demand_contact":
                contact_missing += 1
            elif field_key == "architect_office":
                architect_missing += 1
            elif field_key == "gross_area_scale":
                area_missing += 1
            missing_specs.append((field_key, field_label, source_field_name))
        if not missing_specs:
            continue
        missing_entries += 1
        if len(preview_specs) < limit:
            preview_specs.append((entry, missing_specs))

    winner_cache: dict[UUID, tuple[dict[tuple[str, str, str], dict[str, str]], dict[tuple[str, str], dict[str, str]]]] = {}
    items: list[TrackerMissingReportItem] = []
    for entry, missing_specs in preview_specs:
        winner_row = lookup_winner_row_for_entry(
            entry,
            winner_cache,
            load_winner_index_by_run_fn=load_winner_index_by_run_fn,
            coerce_uuid_or_none=coerce_uuid_or_none,
        )
        missing_fields: list[TrackerMissingFieldItem] = []
        for field_key, field_label, source_field_name in missing_specs:
            reason_group, reason_explainer = classify_tracker_missing_field(
                field_key=field_key,
                project_name=str(entry.get("project_name") or "").strip(),
                winner_row=winner_row,
                source_field_name=source_field_name,
            )
            missing_fields.append(
                TrackerMissingFieldItem(
                    field_key=field_key,
                    field_label=field_label,
                    source_reason=_humanize_tracker_source_reason(
                        field_key=field_key,
                        winner_row=winner_row,
                        source_field_name=source_field_name,
                    ),
                    reason_group=reason_group,
                    reason_explainer=reason_explainer,
                )
            )
        items.append(
            TrackerMissingReportItem(
                entry_id=UUID(str(entry.get("id"))),
                source_run_id=coerce_uuid_or_none(entry.get("source_run_id")),
                source_tracker_run_id=coerce_uuid_or_none(entry.get("source_tracker_run_id")),
                project_name=str(entry.get("project_name") or "").strip(),
                bid_no=str(entry.get("source_bid_no") or "").strip(),
                bid_ord=str(entry.get("source_bid_ord") or "").strip(),
                demand_org_name=str(entry.get("demand_org_name") or "").strip(),
                missing_fields=missing_fields,
                updated_at=entry.get("updated_at"),
            )
        )

    summary = TrackerMissingReportSummary(
        total_entries=len(deduped),
        missing_entries=missing_entries,
        contact_missing=contact_missing,
        architect_missing=architect_missing,
        area_missing=area_missing,
    )
    return summary, items


def flatten_tracker_missing_report_rows(
    *,
    summary: TrackerMissingReportSummary,
    items: list[TrackerMissingReportItem],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    for item in items:
        missing_fields = list(item.missing_fields or [])
        if not missing_fields:
            rows.append(
                {
                    "generated_at": generated_at,
                    "project_name": item.project_name,
                    "bid_no": item.bid_no,
                    "bid_ord": item.bid_ord,
                    "demand_org_name": item.demand_org_name,
                    "missing_field_key": "",
                    "missing_field_label": "",
                    "source_reason": "",
                    "reason_group": "",
                    "reason_explainer": "",
                    "source_run_id": str(item.source_run_id or ""),
                    "source_tracker_run_id": str(item.source_tracker_run_id or ""),
                    "updated_at": item.updated_at.isoformat() if item.updated_at else "",
                    "summary_total_entries": str(summary.total_entries),
                    "summary_missing_entries": str(summary.missing_entries),
                    "summary_contact_missing": str(summary.contact_missing),
                    "summary_architect_missing": str(summary.architect_missing),
                    "summary_area_missing": str(summary.area_missing),
                }
            )
            continue
        for field in missing_fields:
            rows.append(
                {
                    "generated_at": generated_at,
                    "project_name": item.project_name,
                    "bid_no": item.bid_no,
                    "bid_ord": item.bid_ord,
                    "demand_org_name": item.demand_org_name,
                    "missing_field_key": field.field_key,
                    "missing_field_label": field.field_label,
                    "source_reason": field.source_reason,
                    "reason_group": field.reason_group,
                    "reason_explainer": field.reason_explainer,
                    "source_run_id": str(item.source_run_id or ""),
                    "source_tracker_run_id": str(item.source_tracker_run_id or ""),
                    "updated_at": item.updated_at.isoformat() if item.updated_at else "",
                    "summary_total_entries": str(summary.total_entries),
                    "summary_missing_entries": str(summary.missing_entries),
                    "summary_contact_missing": str(summary.contact_missing),
                    "summary_architect_missing": str(summary.architect_missing),
                    "summary_area_missing": str(summary.area_missing),
                }
            )
    return rows
