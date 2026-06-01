from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.artifact_files import read_tracking_workbook_rows
from gui_compare_loader import load_gui_backend_module
from gui_compare_loader import load_internal_nav_module
from gui_compare_loader import load_post_collect_module
from gui_compare_loader import load_search_collect_module
from backend.services.pipeline_stage_outputs import run_export_stage_for_run
from backend.services.pipeline_stage_outputs import run_filter_stage_for_run
from backend.services.pipeline_stage_outputs import run_rescan_stage_for_run
from backend.services.run_workspace import collect_candidates_csv_path_for_run
from backend.services.run_workspace import internal_nav_csv_path_for_run
from backend.services.run_workspace import post_collect_csv_path_for_run
from backend.services.run_workspace import seed_csv_path_for_run
from backend.services.tracker_export_stage import prepare_tracker_export_for_run

SEED_HEADERS = ("bid_no", "bid_ord", "project_name", "org_name", "announce_date", "g2b_verified")
DIFF_LIMIT = 5


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw or raw.startswith("export "):
            continue
        key, value = raw.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


@contextmanager
def patched_env(values: dict[str, str]):
    previous: dict[str, str | None] = {}
    try:
        for key, value in values.items():
            previous[key] = os.environ.get(key)
            os.environ[key] = value
        yield
    finally:
        for key, previous_value in previous.items():
            if previous_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous_value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare direct GUI outputs with web pipeline stage outputs.")
    parser.add_argument("--gui-source-root", default="", help="Local GUI source root.")
    parser.add_argument("--seed-csv", default="", help="Optional seed CSV to reuse for both sides.")
    parser.add_argument("--output", default="", help="Optional JSON report path.")
    parser.add_argument("--start-date", default="20250101")
    parser.add_argument("--end-date", default="20250131")
    parser.add_argument("--contract-date-hint", default="")
    parser.add_argument("--notice-title", default="")
    parser.add_argument("--bid-no", default="")
    parser.add_argument("--demand-org", default="")
    parser.add_argument("--rows-per-page", type=int, default=30)
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--api-scope", default="construction")
    parser.add_argument("--seed-limit", type=int, default=0, help="Optional limit for seed rows.")
    return parser.parse_args()


def build_params(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "start_date": str(args.start_date).strip(),
        "end_date": str(args.end_date).strip(),
        "contract_date_hint": str(args.contract_date_hint).strip(),
        "notice_title": str(args.notice_title).strip(),
        "bid_no": str(args.bid_no).strip(),
        "demand_org": str(args.demand_org).strip(),
        "rows_per_page": int(args.rows_per_page),
        "max_pages": int(args.max_pages),
        "api_scope": str(args.api_scope).strip() or "construction",
        "_advanced_options": {"collect_mode": "gui_seed"},
    }


def ensure_inputs(args: argparse.Namespace) -> None:
    if args.seed_csv:
        return
    if args.bid_no.strip() or args.notice_title.strip() or args.demand_org.strip():
        return
    raise SystemExit("Either --seed-csv or one of --bid-no/--notice-title/--demand-org is required.")


def normalize_seed_row(row: dict[str, Any]) -> dict[str, str]:
    return {header: normalize_scalar(row.get(header, "")) for header in SEED_HEADERS}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        return [normalize_row(dict(row or {})) for row in reader]


def normalize_row(row: dict[str, Any]) -> dict[str, str]:
    return {str(key): normalize_scalar(value) for key, value in sorted((row or {}).items())}


def normalize_scalar(value: Any) -> str:
    return str(value or "").strip()


def normalized_digest(rows: list[dict[str, str]]) -> str:
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_row_diff(web_rows: list[dict[str, str]], gui_rows: list[dict[str, str]]) -> dict[str, Any]:
    diffs: list[dict[str, Any]] = []
    max_len = max(len(web_rows), len(gui_rows))
    for index in range(max_len):
        web_row = web_rows[index] if index < len(web_rows) else None
        gui_row = gui_rows[index] if index < len(gui_rows) else None
        if web_row == gui_row:
            continue
        diffs.append(
            {
                "row_index": index,
                "web": web_row,
                "gui": gui_row,
            }
        )
        if len(diffs) >= DIFF_LIMIT:
            break
    return {
        "match": web_rows == gui_rows,
        "web_row_count": len(web_rows),
        "gui_row_count": len(gui_rows),
        "web_digest": normalized_digest(web_rows),
        "gui_digest": normalized_digest(gui_rows),
        "sample_diffs": diffs,
    }


def build_log_diff(web_messages: list[str], gui_messages: list[str]) -> dict[str, Any]:
    normalized_web = [normalize_log_message(item) for item in web_messages]
    normalized_gui = [normalize_log_message(item) for item in gui_messages]
    diffs: list[dict[str, Any]] = []
    max_len = max(len(normalized_web), len(normalized_gui))
    for index in range(max_len):
        web_item = normalized_web[index] if index < len(normalized_web) else None
        gui_item = normalized_gui[index] if index < len(normalized_gui) else None
        if web_item == gui_item:
            continue
        diffs.append({"index": index, "web": web_item, "gui": gui_item})
        if len(diffs) >= DIFF_LIMIT:
            break
    return {
        "match": normalized_web == normalized_gui,
        "web_count": len(normalized_web),
        "gui_count": len(normalized_gui),
        "web_has_fallback": any("fallback" in item.lower() for item in normalized_web),
        "gui_has_fallback": any("fallback" in item.lower() for item in normalized_gui),
        "sample_diffs": diffs,
    }


def normalize_log_message(message: str) -> str:
    normalized = normalize_scalar(message)
    normalized = re.sub(
        r"export\(gui\): g2b contract ([A-Za-z0-9_]+)\s+.*",
        r"export(gui): g2b contract \1 <volatile>",
        normalized,
    )
    normalized = re.sub(
        r"프로젝트_트랙커_채움_\d{8}_\d{6}_\d+\.xlsx",
        "프로젝트_트랙커_채움_<generated>.xlsx",
        normalized,
    )
    normalized = re.sub(
        r"[A-Za-z]:\\[^\\r\\n]*프로젝트_트랙커_채움_<generated>\.xlsx",
        r"<tracker_output_path>\\프로젝트_트랙커_채움_<generated>.xlsx",
        normalized,
    )
    return normalized


def prefixed_logger(messages: list[str], prefix: str):
    def _inner(message: str) -> None:
        messages.append(f"{prefix}: {message}")

    return _inner


def load_seed_rows(args: argparse.Namespace, params: dict[str, Any]) -> tuple[list[dict[str, str]], str]:
    if args.seed_csv:
        seed_path = Path(args.seed_csv).expanduser()
        rows = read_csv_rows(seed_path)
        normalized = [normalize_seed_row(row) for row in rows]
        if not normalized:
            raise RuntimeError(f"seed csv has no rows: {seed_path}")
        return normalized, str(seed_path.resolve())

    gui_backend = load_gui_backend_module()
    service_key = normalize_scalar(getattr(gui_backend, "_resolve_service_key")(""))
    if not service_key:
        raise RuntimeError("G2B service key not found in GUI source env")

    rows = list(
        getattr(gui_backend, "fetch_seed_rows")(
            service_key=service_key,
            start_date=params["start_date"],
            end_date=params["end_date"],
            bid_no_filter=params["bid_no"],
            title_filter=params["notice_title"],
            demand_org_filter=params["demand_org"],
            rows_per_page=params["rows_per_page"],
            max_pages=params["max_pages"],
            endpoint_mode=params["api_scope"],
            progress_cb=None,
            stop_event=None,
        )
    )
    normalized = [normalize_seed_row(row) for row in rows]
    if not normalized:
        raise RuntimeError("GUI fetch_seed_rows returned no rows")
    return normalized, "gui_fetch_seed_rows"


def apply_seed_limit(rows: list[dict[str, str]], seed_limit: int) -> list[dict[str, str]]:
    if seed_limit <= 0:
        return rows
    return rows[:seed_limit]


def run_web_side(params: dict[str, Any], seed_rows: list[dict[str, str]], temp_root: Path) -> dict[str, Any]:
    run_id = uuid4()
    gui_backend = load_gui_backend_module()
    messages: list[str] = []

    gui_backend.write_seed_csv(seed_rows, seed_csv_path_for_run(run_id))
    filter_output = run_filter_stage_for_run(
        run_id=run_id,
        params=params,
        collect_backend="gui_seed",
        progress_cb=messages.append,
    )
    rescan_output = run_rescan_stage_for_run(
        run_id=run_id,
        params=params,
        filter_backend=filter_output.stage_backend,
        progress_cb=messages.append,
    )
    export_output = run_export_stage_for_run(
        run_id=run_id,
        params=params,
        rescan_backend=rescan_output.stage_backend,
        progress_cb=messages.append,
    )
    tracker_output = prepare_tracker_export_for_run(
        parent_run_id=run_id,
        params={**params, "_export_summary": {"export_backend": export_output.stage_backend}},
        winner_csv_path=export_output.post_collect_csv_path,
        progress_cb=messages.append,
    )
    if tracker_output is None or tracker_output.workbook_path is None:
        raise RuntimeError("web tracker export did not produce a workbook")

    return {
        "candidate_rows": read_csv_rows(collect_candidates_csv_path_for_run(run_id)),
        "internal_nav_rows": read_csv_rows(internal_nav_csv_path_for_run(run_id)),
        "winner_rows": read_csv_rows(Path(export_output.post_collect_csv_path)),
        "tracker_rows": [normalize_row(row) for row in read_tracking_workbook_rows(tracker_output.workbook_path)],
        "log_messages": messages,
        "summary": {
            "run_id": str(run_id),
            "workspace_root": str(temp_root.resolve()),
            "filter_backend": filter_output.stage_backend,
            "rescan_backend": rescan_output.stage_backend,
            "export_backend": export_output.stage_backend,
            "tracker_backend": tracker_output.stage_backend,
            "candidate_csv_path": str(collect_candidates_csv_path_for_run(run_id).resolve()),
            "internal_nav_csv_path": str(internal_nav_csv_path_for_run(run_id).resolve()),
            "winner_csv_path": str(Path(export_output.post_collect_csv_path).resolve()),
            "tracker_workbook_path": str(tracker_output.workbook_path.resolve()),
        },
    }


def run_gui_side(params: dict[str, Any], seed_rows: list[dict[str, str]], temp_root: Path) -> dict[str, Any]:
    gui_backend = load_gui_backend_module()
    search_collect = load_search_collect_module()
    internal_nav = load_internal_nav_module()
    post_collect = load_post_collect_module()

    messages: list[str] = []
    seed_csv_path = temp_root / "project_tracker_seed_input.csv"
    candidate_csv_path = temp_root / "project_tracker_candidate_collection_v1_1.csv"
    internal_nav_csv_path = temp_root / "project_tracker_internal_search_urls_v1_1.csv"
    winner_csv_path = temp_root / "project_tracker_posts_files_v1_1.csv"

    gui_backend.write_seed_csv(seed_rows, seed_csv_path)
    search_collect.run_collect(
        seed_csv_path,
        candidate_csv_path,
        stop_event=None,
        progress_cb=prefixed_logger(messages, "filter(gui)"),
    )
    internal_nav.run_internal_nav(
        candidate_csv_path,
        internal_nav_csv_path,
        stop_event=None,
        progress_cb=prefixed_logger(messages, "rescan(gui)"),
    )

    service_key = normalize_scalar(getattr(gui_backend, "_resolve_service_key")(""))
    if not service_key:
        raise RuntimeError("G2B service key not found in GUI source env")
    lofin_api_key = normalize_scalar(getattr(gui_backend, "_resolve_lofin_openapi_key")(""))
    contract_date_hint = params["contract_date_hint"]
    if not contract_date_hint and params["start_date"] == params["end_date"]:
        contract_date_hint = params["start_date"]

    actual_winner_csv_path = Path(
        post_collect.run_post_collect(
            internal_nav_csv_path,
            winner_csv_path,
            contract_date_hint=contract_date_hint,
            lofin_api_key=lofin_api_key,
            g2b_service_key=service_key,
            g2b_inqry_bgn_date=params["start_date"],
            g2b_inqry_end_date=params["end_date"],
            stop_event=None,
            progress_cb=prefixed_logger(messages, "export(gui)"),
        )
    )
    tracker_workbook_path = Path(
        gui_backend.run_tracker_export_script(
            winner_csv=actual_winner_csv_path,
            seed_csv=seed_csv_path,
            g2b_service_key=service_key,
            demand_org_filter=params["demand_org"],
            progress_cb=prefixed_logger(messages, "tracker(gui)"),
        )
    )

    return {
        "candidate_rows": read_csv_rows(candidate_csv_path),
        "internal_nav_rows": read_csv_rows(internal_nav_csv_path),
        "winner_rows": read_csv_rows(actual_winner_csv_path),
        "tracker_rows": [normalize_row(row) for row in read_tracking_workbook_rows(tracker_workbook_path)],
        "log_messages": messages,
        "summary": {
            "workspace_root": str(temp_root.resolve()),
            "candidate_csv_path": str(candidate_csv_path.resolve()),
            "internal_nav_csv_path": str(internal_nav_csv_path.resolve()),
            "winner_csv_path": str(actual_winner_csv_path.resolve()),
            "tracker_workbook_path": str(tracker_workbook_path.resolve()),
        },
    }


def build_report(
    *,
    gui_source_root: str,
    seed_source: str,
    params: dict[str, Any],
    seed_rows: list[dict[str, str]],
    web_result: dict[str, Any],
    gui_result: dict[str, Any],
) -> dict[str, Any]:
    comparisons = {
        "candidate_csv": build_row_diff(web_result["candidate_rows"], gui_result["candidate_rows"]),
        "internal_nav_csv": build_row_diff(web_result["internal_nav_rows"], gui_result["internal_nav_rows"]),
        "winner_csv": build_row_diff(web_result["winner_rows"], gui_result["winner_rows"]),
        "tracking_excel": build_row_diff(web_result["tracker_rows"], gui_result["tracker_rows"]),
        "logs": build_log_diff(web_result["log_messages"], gui_result["log_messages"]),
    }
    all_match = all(item["match"] for item in comparisons.values())
    return {
        "summary": {
            "all_match": all_match,
            "comparison_count": len(comparisons),
            "matched_count": sum(1 for item in comparisons.values() if item["match"]),
            "mismatched_count": sum(1 for item in comparisons.values() if not item["match"]),
        },
        "config": {
            "gui_source_root": gui_source_root,
            "seed_source": seed_source,
            "params": {key: value for key, value in params.items() if not key.startswith("_")},
        },
        "seed": {
            "row_count": len(seed_rows),
            "sample_rows": seed_rows[: min(3, len(seed_rows))],
        },
        "web": web_result["summary"],
        "gui": gui_result["summary"],
        "comparisons": comparisons,
    }


def main() -> int:
    args = parse_args()
    ensure_inputs(args)
    load_env_file(ROOT / ".env")

    gui_source_root = args.gui_source_root.strip()
    if gui_source_root:
        os.environ["GUI_PARITY_SOURCE_ROOT"] = gui_source_root
    else:
        gui_source_root = os.environ.get("GUI_PARITY_SOURCE_ROOT", "").strip()

    params = build_params(args)
    base_tmp = ROOT / ".tmp-test-runs"
    base_tmp.mkdir(parents=True, exist_ok=True)
    web_temp_root = Path(tempfile.mkdtemp(prefix="artifact-diff-web-", dir=str(base_tmp)))
    gui_temp_root = Path(tempfile.mkdtemp(prefix="artifact-diff-gui-", dir=str(base_tmp)))

    try:
        seed_rows, seed_source = load_seed_rows(args, params)
        seed_rows = apply_seed_limit(seed_rows, int(args.seed_limit))
        if not seed_rows:
            raise RuntimeError("seed row set is empty after applying --seed-limit")
        with patched_env(
            {
                "RUN_WORKSPACE_ROOT": str(web_temp_root / "workspace"),
                "TRACKER_TEMPLATE_PATH": str(ROOT / "assets" / "project_tracker_template.xlsx"),
            }
        ):
            web_result = run_web_side(params, seed_rows, web_temp_root)
        gui_result = run_gui_side(params, seed_rows, gui_temp_root)
        report = build_report(
            gui_source_root=gui_source_root,
            seed_source=seed_source,
            params=params,
            seed_rows=seed_rows,
            web_result=web_result,
            gui_result=gui_result,
        )
        if args.output:
            output_path = Path(args.output)
            if not output_path.is_absolute():
                output_path = ROOT / output_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["summary"]["all_match"] else 1
    finally:
        shutil.rmtree(web_temp_root, ignore_errors=True)
        shutil.rmtree(gui_temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
