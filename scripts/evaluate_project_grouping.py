from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from backend.api.app import _project_match_key
from backend.api.app import _select_project_search_name
from backend.services.project_grouping_quality import GroupingAssignment
from backend.services.project_grouping_quality import evaluate_project_grouping


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _normalize_bid_ord(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    digits = "".join(ch for ch in text if ch.isdigit())
    if digits:
        return digits.zfill(3)
    return text.upper()


def _build_item_key(row: dict[str, str]) -> str:
    explicit = str(row.get("item_key") or "").strip()
    if explicit:
        return explicit
    entry_key = str(row.get("entry_key") or "").strip()
    if entry_key:
        return entry_key
    bid_no = str(row.get("source_bid_no") or row.get("bid_no") or "").strip().upper()
    bid_ord = _normalize_bid_ord(str(row.get("source_bid_ord") or row.get("bid_ord") or ""))
    if bid_no:
        return f"{bid_no}|{bid_ord}"
    project_name = str(row.get("project_name") or "").strip()
    if project_name:
        return project_name
    raise ValueError(f"cannot derive item key from row: {row}")


def _build_predicted_group_id(row: dict[str, str]) -> str:
    explicit = str(row.get("predicted_group_id") or "").strip()
    if explicit:
        return explicit
    project_name = str(row.get("project_name") or "").strip()
    source_project_name_norm = str(row.get("source_project_name_norm") or "").strip()
    project_search_name = _select_project_search_name(project_name, source_project_name_norm)
    candidate = project_search_name or project_name or source_project_name_norm
    return _project_match_key(candidate)


def _build_assignments(
    golden_rows: list[dict[str, str]],
    tracker_rows: list[dict[str, str]],
) -> list[GroupingAssignment]:
    tracker_by_item_key: dict[str, dict[str, str]] = {}
    for row in tracker_rows:
        primary_key = _build_item_key(row)
        tracker_by_item_key.setdefault(primary_key, row)
        bid_no = str(row.get("source_bid_no") or row.get("bid_no") or "").strip().upper()
        bid_ord = _normalize_bid_ord(str(row.get("source_bid_ord") or row.get("bid_ord") or ""))
        if bid_no:
            tracker_by_item_key.setdefault(f"{bid_no}|{bid_ord}", row)

    assignments: list[GroupingAssignment] = []
    missing_items: list[str] = []

    for row in golden_rows:
        item_key = _build_item_key(row)
        tracker_row = tracker_by_item_key.get(item_key)
        if tracker_row is None:
            missing_items.append(item_key)
            continue
        expected_group_id = str(row.get("expected_group_id") or "").strip()
        if not expected_group_id:
            raise ValueError(f"golden row missing expected_group_id: {row}")
        assignments.append(
            GroupingAssignment(
                item_key=item_key,
                expected_group_id=expected_group_id,
                predicted_group_id=_build_predicted_group_id(tracker_row),
                project_name=str(tracker_row.get("project_name") or "").strip(),
                bid_no=str(tracker_row.get("source_bid_no") or tracker_row.get("bid_no") or "").strip().upper(),
                bid_ord=_normalize_bid_ord(
                    str(tracker_row.get("source_bid_ord") or tracker_row.get("bid_ord") or "")
                ),
            )
        )

    if missing_items:
        raise ValueError(
            "golden set item(s) not found in tracker rows: "
            + ", ".join(sorted(missing_items)[:10])
            + (" ..." if len(missing_items) > 10 else "")
        )
    return assignments


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate project grouping quality against a golden set.")
    parser.add_argument("--golden-csv", required=True, help="CSV with item_key/entry_key/bid_no+bid_ord and expected_group_id.")
    parser.add_argument("--tracker-csv", required=True, help="CSV exported from tracker summaries or tracker entries.")
    parser.add_argument("--output-stem", required=True, help="Output stem path without extension.")
    args = parser.parse_args()

    golden_path = Path(args.golden_csv)
    tracker_path = Path(args.tracker_csv)
    output_stem = Path(args.output_stem)
    output_stem.parent.mkdir(parents=True, exist_ok=True)

    golden_rows = _load_csv_rows(golden_path)
    tracker_rows = _load_csv_rows(tracker_path)
    assignments = _build_assignments(golden_rows, tracker_rows)
    summary = evaluate_project_grouping(assignments)
    summary["golden_csv"] = str(golden_path)
    summary["tracker_csv"] = str(tracker_path)

    detail_rows = list(summary.pop("items"))
    _write_json(output_stem.with_suffix(".summary.json"), summary)
    _write_json(output_stem.with_suffix(".json"), {"items": detail_rows})
    _write_csv(output_stem.with_suffix(".csv"), detail_rows)

    print(
        json.dumps(
            {
                "output_summary_json": str(output_stem.with_suffix(".summary.json")),
                "output_json": str(output_stem.with_suffix(".json")),
                "output_csv": str(output_stem.with_suffix(".csv")),
                "pairwise_precision": summary["pairwise_precision"],
                "pairwise_recall": summary["pairwise_recall"],
                "pairwise_f1": summary["pairwise_f1"],
                "overmerged_group_count": summary["overmerged_group_count"],
                "oversplit_group_count": summary["oversplit_group_count"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
