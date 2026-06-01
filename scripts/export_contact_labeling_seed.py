from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEBUG_DIR = ROOT / "output" / "debug"

LABEL_COLUMNS = (
    "seed_bucket",
    "seed_hint",
    "project_name",
    "bid_no",
    "org",
    "current_contact",
    "candidate_text",
    "label_role",
    "label_phase",
    "label_owner_side",
    "label_owner_side_basis",
    "label_final_pick_for_demand_contact",
    "label_status",
    "label_reason",
    "label_evidence_block",
    "reviewer_note",
)

BUCKET_META = {
    "hard_wrong": {
        "sheet": "하드 오입력",
        "hint": "현재 연락처가 명백한 오입력 후보입니다.",
    },
    "weak_review": {
        "sheet": "약한 검토",
        "hint": "현재 연락처가 애매해서 검토가 필요합니다.",
    },
    "blank": {
        "sheet": "빈 연락처",
        "hint": "현재 연락처가 비어 있어 owner-side 후보 확인이 필요합니다.",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export manual contact labeling seed files.")
    parser.add_argument(
        "--hard-csv",
        default=str(DEFAULT_DEBUG_DIR / "contact_quality_hard_wrong_20260327.csv"),
    )
    parser.add_argument(
        "--weak-csv",
        default=str(DEFAULT_DEBUG_DIR / "contact_quality_weak_review_20260327.csv"),
    )
    parser.add_argument(
        "--blank-csv",
        default=str(DEFAULT_DEBUG_DIR / "contact_quality_blank_20260327.csv"),
    )
    parser.add_argument(
        "--output-prefix",
        default="",
        help="Optional explicit output prefix. Defaults to output/debug/contact_labeling_seed_<timestamp>",
    )
    return parser.parse_args()


def _read_bucket_rows(path: Path, bucket: str) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            current_contact = str(row.get("contact") or "").strip()
            rows.append(
                {
                    "seed_bucket": bucket,
                    "seed_hint": BUCKET_META[bucket]["hint"],
                    "project_name": str(row.get("project_name") or "").strip(),
                    "bid_no": str(row.get("bid_no") or "").strip(),
                    "org": str(row.get("org") or "").strip(),
                    "current_contact": current_contact,
                    "candidate_text": current_contact,
                    "label_role": "",
                    "label_phase": "",
                    "label_owner_side": "",
                    "label_owner_side_basis": "",
                    "label_final_pick_for_demand_contact": "",
                    "label_status": "",
                    "label_reason": "",
                    "label_evidence_block": "",
                    "reviewer_note": "",
                }
            )
    return rows


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LABEL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _write_xlsx(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws_all = wb.active
    ws_all.title = "전체"
    ws_all.append(list(LABEL_COLUMNS))
    for row in rows:
        ws_all.append([row.get(column, "") for column in LABEL_COLUMNS])

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("seed_bucket") or "")].append(row)

    for bucket in ("hard_wrong", "weak_review", "blank"):
        ws = wb.create_sheet(BUCKET_META[bucket]["sheet"])
        ws.append(list(LABEL_COLUMNS))
        for row in grouped.get(bucket, []):
            ws.append([row.get(column, "") for column in LABEL_COLUMNS])

    wb.save(path)


def main() -> None:
    args = parse_args()

    rows: list[dict[str, str]] = []
    rows.extend(_read_bucket_rows(Path(args.hard_csv), "hard_wrong"))
    rows.extend(_read_bucket_rows(Path(args.weak_csv), "weak_review"))
    rows.extend(_read_bucket_rows(Path(args.blank_csv), "blank"))

    if args.output_prefix:
        prefix = Path(args.output_prefix)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = DEFAULT_DEBUG_DIR / f"contact_labeling_seed_{timestamp}"

    csv_path = prefix.with_suffix(".csv")
    xlsx_path = prefix.with_suffix(".xlsx")
    _write_csv(csv_path, rows)
    _write_xlsx(xlsx_path, rows)

    print(f"rows={len(rows)}")
    print(f"csv={csv_path}")
    print(f"xlsx={xlsx_path}")


if __name__ == "__main__":
    main()
