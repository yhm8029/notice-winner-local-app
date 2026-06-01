from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.phase1_defaults import load_phase1_identity
from backend.repositories import get_backfill_conflict_repository
from backend.repositories import get_tracker_change_event_repository
from backend.repositories import get_tracker_entry_repository
from backend.services.backfill_policy import classify_safe_backfill
from backend.services.tracker_change_event_logic import build_backfill_conflict_key
from backend.services.tracker_change_event_logic import build_tracker_change_event
from backend.services.tracker_change_event_logic import TrackerEventBuildInput
from scripts.dry_run_core_field_backfill import _resolve_apply_mode

DEFAULT_TMP_DIR = ROOT / ".tmp-core-field-backfill"
DEFAULT_ALLOWED_ACTIONS = (
    "safe_fill_blank",
    "safe_replace_implausible_current",
    "review_conflict",
)
EXTRACTOR_VERSION = "safe_backfill_mvp_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan/apply narrow safe core-field backfill actions from dry-run output.")
    parser.add_argument("--dry-run-json", required=True)
    parser.add_argument("--tmp-dir", default=str(DEFAULT_TMP_DIR))
    parser.add_argument("--output-stem", default="")
    parser.add_argument("--actions", default=",".join(DEFAULT_ALLOWED_ACTIONS))
    parser.add_argument("--entry-id", action="append", default=[])
    parser.add_argument("--field-name", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--actor-label", default="safe_backfill_mvp")
    parser.add_argument("--change-source", default="system")
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _load_rows(path: Path) -> list[dict[str, Any]]:
    return [dict(item) for item in json.loads(path.read_text(encoding="utf-8"))]


def _normalize_allowed_actions(raw: str) -> set[str]:
    return {part.strip() for part in str(raw or "").split(",") if part.strip()}


def _should_include_row(row: dict[str, Any], *, entry_ids: set[str], field_names: set[str]) -> bool:
    if entry_ids and str(row.get("entry_id") or "").strip() not in entry_ids:
        return False
    if field_names and str(row.get("field_name") or "").strip() not in field_names:
        return False
    return True


def _plan_row(row: dict[str, Any], *, allowed_actions: set[str]) -> dict[str, Any]:
    planned = dict(row)
    field_name = str(row.get("field_name") or "").strip()
    action = str(row.get("action") or "").strip()
    apply_mode = str(row.get("apply_mode") or "").strip() or _resolve_apply_mode(field_name, action)
    planned["apply_mode"] = apply_mode
    if action not in allowed_actions:
        planned["plan_status"] = "skipped"
        planned["skip_reason"] = "action_not_allowed"
        return planned
    if apply_mode not in {"override", "conflict"}:
        planned["plan_status"] = "skipped"
        planned["skip_reason"] = apply_mode or "skip"
        return planned
    planned["plan_status"] = "planned"
    planned["skip_reason"] = ""
    return planned


def _summarize_rows(rows: list[dict[str, Any]], *, counter_key: str) -> dict[str, Any]:
    return {
        "row_count": len(rows),
        f"{counter_key}_counts": dict(Counter(str(row.get(counter_key) or "") for row in rows)),
        "field_counts": dict(Counter(str(row.get("field_name") or "") for row in rows)),
    }


def _to_uuid_or_none(value: Any) -> UUID | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return UUID(text)
    except Exception:
        return None


def _append_conflict(*, organization_id: UUID, row: dict[str, Any], current_value: str | None = None) -> None:
    conflict_repository = get_backfill_conflict_repository()
    current_norm = str(row.get("current_value_norm") or "").strip()
    if current_value is not None:
        current_norm = str(current_norm or "")
    candidate_norm = str(row.get("candidate_value_norm") or "").strip()
    tracker_entry_id = _to_uuid_or_none(row.get("entry_id"))
    if tracker_entry_id is None:
        return
    conflict_repository.upsert_conflicts(
        organization_id=organization_id,
        conflicts=[
            {
                "tracker_entry_id": tracker_entry_id,
                "field_name": str(row.get("field_name") or "").strip(),
                "current_value": str(current_value if current_value is not None else row.get("current_value") or ""),
                "candidate_value": str(row.get("candidate_value") or ""),
                "current_value_norm": current_norm,
                "candidate_value_norm": candidate_norm,
                "reason_code": str(row.get("reason_code") or "").strip() or "review_conflict",
                "source_kind": str(row.get("candidate_source_kind") or "backfill").strip() or "backfill",
                "source_ref": str(row.get("candidate_source_ref") or row.get("run_id") or "").strip() or None,
                "source_run_id": _to_uuid_or_none(row.get("run_id")),
                "extractor_version": EXTRACTOR_VERSION,
                "conflict_key": build_backfill_conflict_key(
                    tracker_entry_id=tracker_entry_id,
                    field_name=str(row.get("field_name") or "").strip(),
                    current_value_norm=current_norm,
                    candidate_value_norm=candidate_norm,
                    source_kind=str(row.get("candidate_source_kind") or "backfill").strip() or "backfill",
                    source_ref=str(row.get("candidate_source_ref") or row.get("run_id") or "").strip(),
                ),
            }
        ],
    )


def _append_change_event(
    *,
    organization_id: UUID,
    tracker_entry_id: UUID,
    field_name: str,
    old_value: str,
    new_value: str,
    source_run_id: UUID | None,
    source_ref: str,
    batch_key: str,
    reason_code: str,
) -> None:
    event = build_tracker_change_event(
        TrackerEventBuildInput(
            organization_id=organization_id,
            tracker_entry_id=tracker_entry_id,
            event_type="field_filled" if not str(old_value or "").strip() else "field_updated_safe",
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            source_kind="backfill",
            source_run_id=source_run_id,
            source_ref=source_ref,
            extractor_version=EXTRACTOR_VERSION,
            reason_code=reason_code,
            batch_key=batch_key,
            is_silent=True,
        )
    )
    if event is None:
        return
    get_tracker_change_event_repository().append_events(
        organization_id=organization_id,
        events=[event],
    )


def _execute_plan(
    rows: list[dict[str, Any]],
    *,
    actor_label: str,
    change_source: str,
) -> list[dict[str, Any]]:
    repository = get_tracker_entry_repository()
    organization_id = load_phase1_identity().organization_id
    results: list[dict[str, Any]] = []
    for row in rows:
        result = dict(row)
        if str(row.get("plan_status") or "") != "planned":
            result["execute_status"] = "skipped"
            results.append(result)
            continue

        apply_mode = str(row.get("apply_mode") or "").strip()
        if apply_mode == "conflict":
            _append_conflict(organization_id=organization_id, row=row)
            result["execute_status"] = "conflict_recorded"
            results.append(result)
            continue
        if apply_mode != "override":
            result["execute_status"] = "skipped"
            results.append(result)
            continue

        entry_id = _to_uuid_or_none(row.get("entry_id"))
        field_name = str(row.get("field_name") or "").strip()
        candidate_value = str(row.get("candidate_value") or "").strip()
        if entry_id is None:
            result["execute_status"] = "invalid_entry_id"
            results.append(result)
            continue
        try:
            current_entry = repository.get_entry(entry_id)
        except Exception as exc:
            result["execute_status"] = "repository_error"
            result["execute_error"] = str(exc)
            results.append(result)
            continue
        if current_entry is None:
            result["execute_status"] = "entry_missing"
            results.append(result)
            continue

        current_live_value = str(current_entry.get(field_name) or "").strip()
        result["current_live_value"] = current_live_value
        decision = classify_safe_backfill(
            field_name,
            current_value=current_live_value,
            candidate_value=candidate_value,
            current_entry=current_entry,
            candidate_source_type=str(row.get("candidate_source_kind") or "").strip(),
            candidate_source_ref=str(row.get("candidate_source_ref") or row.get("run_id") or "").strip(),
        )
        result["live_action"] = decision.action
        result["live_reason_code"] = decision.reason_code
        result["live_current_norm"] = decision.current_norm
        result["live_candidate_norm"] = decision.candidate_norm

        if decision.action == "review_conflict":
            _append_conflict(organization_id=organization_id, row=row, current_value=current_live_value)
            result["execute_status"] = "conflict_recorded"
            results.append(result)
            continue
        if decision.action not in {"safe_fill_blank", "safe_replace_implausible_current"}:
            result["execute_status"] = "skipped_after_recheck"
            results.append(result)
            continue

        try:
            patch_result = repository.apply_override(
                entry_id=entry_id,
                field_name=field_name,
                new_value=candidate_value,
                actor_user_id=None,
                actor_label=actor_label,
                change_source=change_source,
            )
        except Exception as exc:
            result["execute_status"] = "apply_error"
            result["execute_error"] = str(exc)
            results.append(result)
            continue
        if patch_result is None:
            result["execute_status"] = "entry_missing"
            results.append(result)
            continue

        updated_value = str((patch_result.entry or {}).get(field_name) or "").strip()
        result["updated_value"] = updated_value
        result["audit_log_id"] = str(((patch_result.audit_log or {}).get("id")) or "")
        if patch_result.changed:
            try:
                from backend.api.app import _invalidate_home_bootstrap_snapshot_best_effort
                from backend.api.app import _upsert_tracker_entry_snapshots_best_effort

                _upsert_tracker_entry_snapshots_best_effort(
                    organization_id=organization_id,
                    rows=[patch_result.entry],
                )
                _invalidate_home_bootstrap_snapshot_best_effort(organization_id=organization_id)
            except Exception:
                pass
            _append_change_event(
                organization_id=organization_id,
                tracker_entry_id=entry_id,
                field_name=field_name,
                old_value=current_live_value,
                new_value=updated_value,
                source_run_id=_to_uuid_or_none(row.get("run_id")),
                source_ref=str(row.get("candidate_source_ref") or row.get("run_id") or "").strip(),
                batch_key=actor_label,
                reason_code=decision.reason_code,
            )
            result["execute_status"] = "applied"
        else:
            result["execute_status"] = "noop"
        results.append(result)
    return results


def main() -> int:
    args = parse_args()
    dry_run_rows = _load_rows(Path(args.dry_run_json))
    allowed_actions = _normalize_allowed_actions(args.actions)
    entry_ids = {item.strip() for item in args.entry_id if item.strip()}
    field_names = {item.strip() for item in args.field_name if item.strip()}
    plan_rows = [
        _plan_row(row, allowed_actions=allowed_actions)
        for row in dry_run_rows
        if _should_include_row(row, entry_ids=entry_ids, field_names=field_names)
    ]
    if args.limit > 0:
        plan_rows = plan_rows[: args.limit]

    tmp_dir = Path(args.tmp_dir)
    output_stem = args.output_stem.strip() or f"core_field_backfill_apply_plan_{Path(args.dry_run_json).stem}"
    plan_csv = tmp_dir / f"{output_stem}.csv"
    plan_json = tmp_dir / f"{output_stem}.json"
    plan_summary_json = tmp_dir / f"{output_stem}-summary.json"
    _write_csv(plan_csv, plan_rows)
    plan_json.write_text(json.dumps(plan_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    plan_summary = _summarize_rows(plan_rows, counter_key="plan_status")
    plan_summary_json.write_text(json.dumps(plan_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    payload: dict[str, Any] = {
        "plan_csv": str(plan_csv),
        "plan_json": str(plan_json),
        "plan_summary": str(plan_summary_json),
        **plan_summary,
    }
    if not args.execute:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    result_rows = _execute_plan(plan_rows, actor_label=args.actor_label, change_source=args.change_source)
    result_csv = tmp_dir / f"{output_stem}-execute.csv"
    result_json = tmp_dir / f"{output_stem}-execute.json"
    result_summary_json = tmp_dir / f"{output_stem}-execute-summary.json"
    _write_csv(result_csv, result_rows)
    result_json.write_text(json.dumps(result_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    result_summary = _summarize_rows(result_rows, counter_key="execute_status")
    result_summary_json.write_text(json.dumps(result_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    payload.update(
        {
            "execute_csv": str(result_csv),
            "execute_json": str(result_json),
            "execute_summary": str(result_summary_json),
            **result_summary,
        }
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
