from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
import sys

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from backend.api.app import _project_match_key
from backend.api.app import _select_project_search_name


def _load_rows(path: Path) -> list[dict[str, str]]:
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


def _project_key(row: dict[str, str]) -> str:
    project_name = str(row.get("project_name") or "").strip()
    source_norm = str(row.get("source_project_name_norm") or "").strip()
    return _project_match_key(_select_project_search_name(project_name, source_norm) or project_name or source_norm)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build review candidates for project grouping golden set.")
    parser.add_argument("--tracker-csv", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--min-distinct-notices", type=int, default=2)
    parser.add_argument("--max-groups", type=int, default=20)
    args = parser.parse_args()

    rows = _load_rows(Path(args.tracker_csv))
    grouped: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)

    for row in rows:
        group_key = _project_key(row)
        if not group_key:
            continue
        bid_no = str(row.get("source_bid_no") or "").strip().upper()
        bid_ord = _normalize_bid_ord(str(row.get("source_bid_ord") or ""))
        notice_key = f"{bid_no}|{bid_ord}" if bid_no else str(row.get("entry_key") or "").strip()
        if not notice_key:
            continue
        existing = grouped[group_key].get(notice_key)
        if existing is None:
            grouped[group_key][notice_key] = row
            continue
        existing_date = str(existing.get("notice_date") or "")
        current_date = str(row.get("notice_date") or "")
        if current_date >= existing_date:
            grouped[group_key][notice_key] = row

    selected_groups = [
        (group_key, notice_map)
        for group_key, notice_map in grouped.items()
        if len(notice_map) >= args.min_distinct_notices
    ]
    selected_groups.sort(key=lambda item: (-len(item[1]), item[0]))
    selected_groups = selected_groups[: args.max_groups]

    output_rows: list[dict[str, str]] = []
    for index, (group_key, notice_map) in enumerate(selected_groups, start=1):
        expected_group_id = f"draft-group-{index:03d}"
        ordered_rows = sorted(
            notice_map.values(),
            key=lambda row: (
                str(row.get("notice_date") or ""),
                str(row.get("source_bid_no") or ""),
                str(row.get("source_bid_ord") or ""),
            ),
        )
        for row in ordered_rows:
            output_rows.append(
                {
                    "expected_group_id": expected_group_id,
                    "group_key_current": group_key,
                    "group_size_current": str(len(notice_map)),
                    "bid_no": str(row.get("source_bid_no") or "").strip().upper(),
                    "bid_ord": _normalize_bid_ord(str(row.get("source_bid_ord") or "")),
                    "entry_key": str(row.get("entry_key") or "").strip(),
                    "project_name": str(row.get("project_name") or "").strip(),
                    "notice_date": str(row.get("notice_date") or "").strip(),
                    "demand_org_name": str(row.get("demand_org_name") or "").strip(),
                    "review_status": "pending",
                    "review_note": "",
                }
            )

    output_path = Path(args.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        fieldnames = list(output_rows[0].keys()) if output_rows else [
            "expected_group_id",
            "group_key_current",
            "group_size_current",
            "bid_no",
            "bid_ord",
            "entry_key",
            "project_name",
            "notice_date",
            "demand_org_name",
            "review_status",
            "review_note",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)

    print(
        {
            "output_csv": str(output_path),
            "group_count": len(selected_groups),
            "row_count": len(output_rows),
        }
    )


if __name__ == "__main__":
    main()
