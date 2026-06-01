from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from collections import defaultdict
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.backfill_policy import classify_safe_backfill
from backend.services.backfill_policy import SAFE_BACKFILL_FIELDS
from backend.services.native_export_backend import run_post_collect_native
from backend.services.native_tracker_backend import build_tracker_entries_from_winner_csv

DEFAULT_BASELINE_JSON = ROOT / ".tmp-recent-100-core-field-rerun-no-contract-20260323_223119.json"
DEFAULT_CURRENT_SUMMARY_CSV = ROOT / "._tmp_tracker_entry_summaries.csv"
DEFAULT_TMP_DIR = ROOT / ".tmp-core-field-backfill"

FIELD_KEYS = tuple(SAFE_BACKFILL_FIELDS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run safe tracker field backfill for a narrow field set.")
    parser.add_argument("--baseline-json", default=str(DEFAULT_BASELINE_JSON))
    parser.add_argument("--current-summary-csv", default=str(DEFAULT_CURRENT_SUMMARY_CSV))
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--tmp-dir", default=str(DEFAULT_TMP_DIR))
    parser.add_argument("--output-stem", default="")
    return parser.parse_args()


def _norm_bid_ord(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "000"
    if raw.isdigit():
        return f"{int(raw):03d}"
    return raw


def _norm_text(value: str) -> str:
    return "".join(str(value or "").lower().split())


def _is_blank(value: Any) -> bool:
    return not str(value or "").strip() or str(value or "").strip() == "-"


def _pick_by_project_name(rows: list[dict[str, Any]], project_name: str, field_name: str) -> dict[str, Any] | None:
    if not rows:
        return None
    target = _norm_text(project_name)
    best_row = rows[0]
    best_score: tuple[int, int] | None = None
    for row in rows:
        candidate = _norm_text(str(row.get(field_name) or ""))
        if not candidate:
            continue
        if candidate == target:
            return row
        overlap = 0
        if target in candidate or candidate in target:
            overlap = max(len(candidate), len(target))
        score = (0 if overlap else 1, abs(len(candidate) - len(target)))
        if best_score is None or score < best_score:
            best_score = score
            best_row = row
    return best_row


def _load_baseline_rows(path: Path, limit: int) -> list[dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if limit > 0:
        rows = rows[:limit]
    return [dict(item) for item in rows]


def _load_current_summary_index(path: Path) -> dict[tuple[str, str], list[dict[str, str]]]:
    index: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    if not path.exists():
        return index
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        for row in csv.DictReader(fp):
            bid_no = str(row.get("source_bid_no") or "").strip().upper()
            bid_ord = _norm_bid_ord(row.get("source_bid_ord") or "000")
            if not bid_no:
                continue
            index[(bid_no, bid_ord)].append({key: str(value or "").strip() for key, value in row.items()})
    return index


def _build_run_index(runs_root: Path) -> dict[tuple[str, str], list[dict[str, Any]]]:
    index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    if not runs_root.exists():
        return index
    for run_dir in sorted(runs_root.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
        if not run_dir.is_dir():
            continue
        seed_csv = run_dir / "project_tracker_seed_input.csv"
        internal_nav_csv = run_dir / "project_tracker_internal_search_urls_v1_1.csv"
        if not seed_csv.exists() or not internal_nav_csv.exists():
            continue
        try:
            with seed_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                for row in csv.DictReader(fp):
                    bid_no = str(row.get("bid_no") or "").strip().upper()
                    bid_ord = _norm_bid_ord(row.get("bid_ord") or "000")
                    if not bid_no:
                        continue
                    index[(bid_no, bid_ord)].append(
                        {
                            "run_id": run_dir.name,
                            "run_dir": run_dir,
                            "seed_csv": seed_csv,
                            "internal_nav_csv": internal_nav_csv,
                            "project_name": str(row.get("project_name") or "").strip(),
                        }
                    )
        except Exception:
            continue
    return index


def _pick_run_for_row(run_candidates: list[dict[str, Any]], project_name: str) -> dict[str, Any] | None:
    if not run_candidates:
        return None
    return _pick_by_project_name(run_candidates, project_name, "project_name") or run_candidates[0]


def _filter_internal_nav(source_csv: Path, out_csv: Path, wanted_keys: set[tuple[str, str]]) -> int:
    with source_csv.open("r", encoding="utf-8-sig", newline="") as src_fp:
        reader = csv.DictReader(src_fp)
        fieldnames = list(reader.fieldnames or [])
        rows = [
            row
            for row in reader
            if (str(row.get("bid_no") or "").strip().upper(), _norm_bid_ord(row.get("bid_ord") or "000")) in wanted_keys
        ]
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8-sig", newline="") as out_fp:
        writer = csv.DictWriter(out_fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def _load_tracker_rows(path: Path, seed_csv: Path) -> dict[tuple[str, str], list[dict[str, Any]]]:
    tracker_rows = build_tracker_entries_from_winner_csv(winner_csv_path=path, seed_csv_path=seed_csv)
    index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in tracker_rows:
        bid_no = str(row.get("source_bid_no") or "").strip().upper()
        bid_ord = _norm_bid_ord(row.get("source_bid_ord") or "000")
        index[(bid_no, bid_ord)].append(row)
    return index


def _resolve_apply_mode(field_name: str, action: str) -> str:
    if action in {"safe_fill_blank", "safe_replace_implausible_current"} and field_name in FIELD_KEYS:
        return "override"
    if action == "review_conflict" and field_name in FIELD_KEYS:
        return "conflict"
    return "skip"


def _build_current_entry_context(current_row: dict[str, Any] | None) -> dict[str, Any]:
    if not current_row:
        return {"overridden_fields": []}
    raw = str(current_row.get("overridden_fields") or "").strip()
    overridden_fields = [item.strip() for item in raw.split(",") if item.strip()]
    return {"overridden_fields": overridden_fields}


def _compare_row(
    *,
    baseline_row: dict[str, Any],
    current_row: dict[str, Any] | None,
    candidate_row: dict[str, Any] | None,
    run_id: str,
    run_lookup_status: str,
) -> list[dict[str, Any]]:
    project_name = str(baseline_row.get("project_name") or "").strip()
    bid_no = str(baseline_row.get("bid_no") or "").strip().upper()
    bid_ord = _norm_bid_ord(baseline_row.get("bid_ord") or "000")
    current_values = {
        "gross_area_scale": str(
            baseline_row.get("current_area")
            or ((current_row or {}).get("gross_area_scale") or "")
        ).strip(),
        "construction_cost": str(
            baseline_row.get("current_cost")
            or ((current_row or {}).get("construction_cost") or "")
        ).strip(),
        "demand_contact": str((current_row or {}).get("demand_contact") or "").strip(),
    }
    candidate_values = {
        field_name: str((candidate_row or {}).get(field_name) or "").strip()
        for field_name in FIELD_KEYS
    }
    current_entry = _build_current_entry_context(current_row)
    rows: list[dict[str, Any]] = []
    for field_name in FIELD_KEYS:
        current_value = current_values[field_name]
        candidate_value = candidate_values[field_name]
        decision = classify_safe_backfill(
            field_name,
            current_value=current_value,
            candidate_value=candidate_value,
            current_entry=current_entry,
            candidate_source_type="tracker_export" if candidate_value else "",
            candidate_source_ref=run_id if candidate_value else "",
        )
        rows.append(
            {
                "entry_id": str(baseline_row.get("entry_id") or "").strip(),
                "bid_no": bid_no,
                "bid_ord": bid_ord,
                "project_name": project_name,
                "run_id": run_id,
                "run_lookup_status": run_lookup_status,
                "field_name": field_name,
                "current_value": current_value,
                "candidate_value": candidate_value,
                "current_value_norm": decision.current_norm,
                "candidate_value_norm": decision.candidate_norm,
                "changed": current_value != candidate_value,
                "action": decision.action,
                "reason_code": decision.reason_code,
                "apply_mode": _resolve_apply_mode(field_name, decision.action),
                "candidate_source_kind": "tracker_export" if candidate_value else "",
                "candidate_source_ref": run_id if candidate_value else "",
                "target_flags": ",".join(baseline_row.get("target_flags") or []),
                "attachment_note": str(baseline_row.get("attachment_note") or "").strip(),
                "synap_note": str(baseline_row.get("synap_note") or "").strip(),
            }
        )
    return rows


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "row_count": len(rows),
        "field_summary": {},
        "action_counts": dict(Counter(str(row.get("action") or "") for row in rows)),
        "apply_mode_counts": dict(Counter(str(row.get("apply_mode") or "") for row in rows)),
    }
    for field_name in FIELD_KEYS:
        field_rows = [row for row in rows if row["field_name"] == field_name]
        summary["field_summary"][field_name] = {
            "target_count": len(field_rows),
            "current_nonblank": sum(0 if _is_blank(row["current_value"]) else 1 for row in field_rows),
            "candidate_nonblank": sum(0 if _is_blank(row["candidate_value"]) else 1 for row in field_rows),
            "improved": sum(
                1
                for row in field_rows
                if _is_blank(row["current_value"]) and not _is_blank(row["candidate_value"])
            ),
            "regressed": sum(
                1
                for row in field_rows
                if not _is_blank(row["current_value"]) and _is_blank(row["candidate_value"])
            ),
            "review_conflict": sum(1 for row in field_rows if row["action"] == "review_conflict"),
        }
    return summary


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _winner_csv_ready(path: Path) -> bool:
    if not path.exists() or path.stat().st_size <= 0:
        return False
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as fp:
            reader = csv.DictReader(fp)
            fieldnames = list(reader.fieldnames or [])
        return "bid_no" in fieldnames and "bid_ord" in fieldnames
    except Exception:
        return False


def _write_checkpoint(*, tmp_dir: Path, output_stem: str, rows: list[dict[str, Any]]) -> None:
    summary = _summarize(rows)
    json_path = tmp_dir / f"{output_stem}.json"
    csv_path = tmp_dir / f"{output_stem}.csv"
    summary_path = tmp_dir / f"{output_stem}-summary.json"
    _write_csv(csv_path, rows)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    baseline_rows = _load_baseline_rows(Path(args.baseline_json), args.limit)
    current_index = _load_current_summary_index(Path(args.current_summary_csv))
    run_index = _build_run_index(ROOT / "output" / "runs")
    tmp_dir = Path(args.tmp_dir)
    output_stem = args.output_stem.strip() or f"core_field_backfill_dry_run_{Path(args.baseline_json).stem}"

    baseline_by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    missing_run_rows: list[dict[str, Any]] = []
    for row in baseline_rows:
        bid_no = str(row.get("bid_no") or "").strip().upper()
        bid_ord = _norm_bid_ord(row.get("bid_ord") or "000")
        project_name = str(row.get("project_name") or "").strip()
        run_meta = _pick_run_for_row(run_index.get((bid_no, bid_ord), []), project_name)
        if run_meta is None:
            missing_run_rows.append(row)
            continue
        baseline_by_run[str(run_meta["run_id"])].append(row)

    compared_rows: list[dict[str, Any]] = []
    all_run_candidates = [item for item_list in run_index.values() for item in item_list]
    for run_id, rows in sorted(baseline_by_run.items()):
        run_meta = _pick_run_for_row(
            [item for item in all_run_candidates if str(item["run_id"]) == run_id],
            str(rows[0].get("project_name") or ""),
        )
        if run_meta is None:
            continue
        wanted_keys = {
            (str(row.get("bid_no") or "").strip().upper(), _norm_bid_ord(row.get("bid_ord") or "000"))
            for row in rows
        }
        run_tmp = tmp_dir / run_id
        filtered_nav_csv = run_tmp / "filtered_internal_nav.csv"
        current_winner_csv = run_tmp / "winner_current.csv"
        nav_count = _filter_internal_nav(Path(run_meta["internal_nav_csv"]), filtered_nav_csv, wanted_keys)
        if nav_count <= 0:
            for row in rows:
                current_rows = current_index.get(
                    (str(row.get("bid_no") or "").strip().upper(), _norm_bid_ord(row.get("bid_ord") or "000")),
                    [],
                )
                current_row = _pick_by_project_name(current_rows, str(row.get("project_name") or ""), "project_name")
                compared_rows.extend(
                    _compare_row(
                        baseline_row=row,
                        current_row=current_row,
                        candidate_row=None,
                        run_id=run_id,
                        run_lookup_status="internal_nav_missing",
                    )
                )
            continue
        if not _winner_csv_ready(current_winner_csv):
            run_post_collect_native(
                filtered_nav_csv,
                current_winner_csv,
                params={"_advanced_options": {"export_row_workers": "8"}},
                progress_cb=None,
            )
        candidate_index = _load_tracker_rows(current_winner_csv, Path(run_meta["seed_csv"]))
        for row in rows:
            bid_key = (str(row.get("bid_no") or "").strip().upper(), _norm_bid_ord(row.get("bid_ord") or "000"))
            current_rows = current_index.get(bid_key, [])
            current_row = _pick_by_project_name(current_rows, str(row.get("project_name") or ""), "project_name")
            candidate_rows = candidate_index.get(bid_key, [])
            candidate_row = _pick_by_project_name(candidate_rows, str(row.get("project_name") or ""), "project_name")
            compared_rows.extend(
                _compare_row(
                    baseline_row=row,
                    current_row=current_row,
                    candidate_row=candidate_row,
                    run_id=run_id,
                    run_lookup_status="ok",
                )
            )
        _write_checkpoint(tmp_dir=tmp_dir, output_stem=output_stem, rows=compared_rows)

    for row in missing_run_rows:
        bid_key = (str(row.get("bid_no") or "").strip().upper(), _norm_bid_ord(row.get("bid_ord") or "000"))
        current_rows = current_index.get(bid_key, [])
        current_row = _pick_by_project_name(current_rows, str(row.get("project_name") or ""), "project_name")
        compared_rows.extend(
            _compare_row(
                baseline_row=row,
                current_row=current_row,
                candidate_row=None,
                run_id="",
                run_lookup_status="run_not_found",
            )
        )

    _write_checkpoint(tmp_dir=tmp_dir, output_stem=output_stem, rows=compared_rows)
    summary = _summarize(compared_rows)
    json_path = tmp_dir / f"{output_stem}.json"
    csv_path = tmp_dir / f"{output_stem}.csv"
    summary_path = tmp_dir / f"{output_stem}-summary.json"
    print(json.dumps({"csv": str(csv_path), "json": str(json_path), "summary": str(summary_path), **summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
