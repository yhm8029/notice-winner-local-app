from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path
import sys
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.artifact_files import read_tracking_workbook_rows
from backend.services.native_seed_backend import fetch_seed_rows_with_diagnostics
from backend.services.native_seed_backend import resolve_service_key
from backend.services.native_tracker_backend import build_tracker_entries_from_winner_csv
from backend.services.pipeline_stage_outputs import run_export_stage_for_run
from backend.services.pipeline_stage_outputs import run_filter_stage_for_run
from backend.services.pipeline_stage_outputs import run_rescan_stage_for_run
from backend.services.run_workspace import seed_csv_path_for_run

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare web-native output against local GUI winner/tracker outputs.")
    parser.add_argument("--gui-source-root", required=True)
    parser.add_argument("--gui-winner-csv", default="")
    parser.add_argument("--gui-tracker-xlsx", default="")
    parser.add_argument("--bid-no", action="append", default=[])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--start-date", default="20250101")
    parser.add_argument("--end-date", default="20250131")
    parser.add_argument("--api-scope", default="all")
    parser.add_argument(
        "--llm-correct",
        action="store_true",
        default=str((os.getenv("TRACKER_LLM_CORRECT") or "")).strip().lower() in {"1", "true", "y", "yes"},
    )
    parser.add_argument("--anthropic-key", default=(os.getenv("ANTHROPIC_API_KEY") or "").strip())
    parser.add_argument("--llm-model", default=(os.getenv("TRACKER_LLM_MODEL") or "claude-haiku-4-5-20251001").strip())
    parser.add_argument("--llm-max-rows", type=int, default=int(str((os.getenv("TRACKER_LLM_MAX_ROWS") or "20")).strip() or "20"))
    parser.add_argument("--output", default="")
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        return [{str(k): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(fp)]


def pick_default_winner_csv(gui_root: Path) -> Path:
    direct = gui_root / "output" / "winner_pipeline_posts_files_v1_1.csv"
    if direct.exists():
        return direct
    matches = sorted((gui_root / "output").glob("winner_pipeline*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError("GUI winner csv not found")
    return matches[0]


def pick_default_tracker_xlsx(gui_root: Path) -> Path:
    preferred = sorted((gui_root / "output").glob("프로젝트_트랙커_2025_*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    if preferred:
        return preferred[0]
    matches = sorted((gui_root / "output").glob("프로젝트_트랙커_*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError("GUI tracker workbook not found")
    return matches[0]


def normalize_text(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", str(value or "")).lower()


def overlap_score(left: str, right: str) -> float:
    a = normalize_text(left)
    b = normalize_text(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    grams_a = {a[i : i + 2] for i in range(len(a) - 1)} or {a}
    grams_b = {b[i : i + 2] for i in range(len(b) - 1)} or {b}
    return len(grams_a & grams_b) / float(max(1, min(len(grams_a), len(grams_b))))


def write_seed_csv(run_id: Any, rows: list[dict[str, str]]) -> Path:
    seed_path = seed_csv_path_for_run(run_id)
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    with seed_path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return seed_path


def run_web_pipeline_for_bid(
    *,
    bid_no: str,
    start_date: str,
    end_date: str,
    api_scope: str,
    llm_correct: bool,
    anthropic_key: str,
    llm_model: str,
    llm_max_rows: int,
) -> dict[str, Any]:
    service_key = resolve_service_key()
    seed_rows = fetch_seed_rows_with_diagnostics(
        service_key=service_key,
        start_date=start_date,
        end_date=end_date,
        bid_no_filter=bid_no,
        title_filter="",
        demand_org_filter="",
        rows_per_page=20,
        max_pages=1,
        endpoint_mode=api_scope,
    ).rows
    if not seed_rows:
        return {"bid_no": bid_no, "error": "seed_rows_empty"}
    run_id = uuid4()
    seed_path = write_seed_csv(run_id, seed_rows)
    params = {
        "_advanced_options": {
            "llm_correct": bool(llm_correct),
            "anthropic_key": str(anthropic_key or "").strip(),
            "llm_model": str(llm_model or "").strip(),
            "llm_max_rows": int(llm_max_rows or 0),
        }
    }
    filter_out = run_filter_stage_for_run(run_id=run_id, params=params, collect_backend="native_api")
    rescan_out = run_rescan_stage_for_run(run_id=run_id, params=params, filter_backend=filter_out.stage_backend)
    export_out = run_export_stage_for_run(run_id=run_id, params=params, rescan_backend=rescan_out.stage_backend)
    with export_out.post_collect_csv_path.open("r", encoding="utf-8-sig", newline="") as fp:
        winner_row = next(csv.DictReader(fp), {})
    tracker_rows = build_tracker_entries_from_winner_csv(winner_csv_path=export_out.post_collect_csv_path, seed_csv_path=seed_path)
    return {
        "bid_no": bid_no,
        "seed": seed_rows[0],
        "winner_row": winner_row,
        "tracker_row": tracker_rows[0] if tracker_rows else {},
    }


def select_bid_nos(gui_winner_rows: list[dict[str, str]], explicit: list[str], limit: int) -> list[str]:
    if explicit:
        return [item.strip() for item in explicit if item.strip()]
    bid_nos: list[str] = []
    for row in gui_winner_rows:
        bid_no = str(row.get("bid_no") or "").strip()
        if bid_no and bid_no not in bid_nos:
            bid_nos.append(bid_no)
        if len(bid_nos) >= limit:
            break
    return bid_nos


def find_gui_tracker_row(project_name: str, gui_tracker_rows: list[dict[str, Any]]) -> dict[str, Any]:
    best_row: dict[str, Any] = {}
    best_score = -1.0
    for row in gui_tracker_rows:
        score = overlap_score(project_name, str(row.get("project_name") or ""))
        if score > best_score:
            best_score = score
            best_row = row
    return best_row if best_score >= 0.45 else {}


def compare_fields(web_row: dict[str, Any], gui_row: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for field in fields:
        web_value = str(web_row.get(field) or "").strip()
        gui_value = str(gui_row.get(field) or "").strip()
        if field.endswith("_amount") or field in {"construction_cost"}:
            web_norm = normalize_amount_text(web_value)
            gui_norm = normalize_amount_text(gui_value)
        else:
            web_norm = normalize_text(web_value)
            gui_norm = normalize_text(gui_value)
        out[field] = {
            "web": web_value,
            "gui": gui_value,
            "match": web_norm == gui_norm,
        }
    return out


def normalize_amount_text(value: str) -> str:
    digits = re.sub(r"[^0-9]", "", str(value or ""))
    return digits.lstrip("0") or "0"


def main() -> int:
    args = parse_args()
    gui_root = Path(args.gui_source_root).expanduser()
    gui_winner_csv = Path(args.gui_winner_csv).expanduser() if args.gui_winner_csv else pick_default_winner_csv(gui_root)
    gui_tracker_xlsx = Path(args.gui_tracker_xlsx).expanduser() if args.gui_tracker_xlsx else pick_default_tracker_xlsx(gui_root)

    gui_winner_rows = read_csv_rows(gui_winner_csv)
    gui_winner_by_bid = {str(row.get("bid_no") or "").strip(): row for row in gui_winner_rows}
    gui_tracker_rows = read_tracking_workbook_rows(gui_tracker_xlsx)
    bid_nos = select_bid_nos(gui_winner_rows, args.bid_no, args.limit)

    report: list[dict[str, Any]] = []
    for bid_no in bid_nos:
        web_result = run_web_pipeline_for_bid(
            bid_no=bid_no,
            start_date=args.start_date,
            end_date=args.end_date,
            api_scope=args.api_scope,
            llm_correct=bool(args.llm_correct),
            anthropic_key=str(args.anthropic_key or "").strip(),
            llm_model=str(args.llm_model or "").strip(),
            llm_max_rows=int(args.llm_max_rows or 0),
        )
        gui_winner_row = gui_winner_by_bid.get(bid_no, {})
        gui_tracker_row = find_gui_tracker_row(str(web_result.get("tracker_row", {}).get("project_name") or ""), gui_tracker_rows)
        report.append(
            {
                "bid_no": bid_no,
                "project_name": str(web_result.get("tracker_row", {}).get("project_name") or web_result.get("seed", {}).get("project_name") or ""),
                "winner_compare": compare_fields(
                    web_result.get("winner_row", {}),
                    gui_winner_row,
                    ["winner_name", "contract_amount", "contract_date", "source_type", "reason_code"],
                ),
                "tracker_compare": compare_fields(
                    web_result.get("tracker_row", {}),
                    gui_tracker_row,
                    [
                        "project_name",
                        "gross_area_scale",
                        "construction_cost",
                        "demand_org_name",
                        "demand_contact",
                        "client_location",
                        "site_location_1",
                        "architect_office",
                        "construction_start_date",
                        "building_automation_estimated_amount",
                    ],
                ),
            }
        )

    payload = {
        "gui_winner_csv": str(gui_winner_csv),
        "gui_tracker_xlsx": str(gui_tracker_xlsx),
        "items": report,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
