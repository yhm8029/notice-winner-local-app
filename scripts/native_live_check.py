from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests

ROOT_DIR = Path(__file__).resolve().parents[1]


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class LocalApiHarness:
    def __init__(self) -> None:
        self._port = _find_free_port()
        self._tmp_root = ROOT_DIR / ".tmp-live-check" / uuid4().hex
        self._process: subprocess.Popen[str] | None = None
        self.base_url = f"http://127.0.0.1:{self._port}"

    def __enter__(self) -> "LocalApiHarness":
        (self._tmp_root / "artifacts").mkdir(parents=True, exist_ok=True)
        (self._tmp_root / "workspace").mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update(
            {
                "PYTHONPATH": str(ROOT_DIR),
                "TRACKER_REPOSITORY_BACKEND": "in_memory",
                "RUN_REPOSITORY_BACKEND": "in_memory",
                "ARTIFACT_REPOSITORY_BACKEND": "in_memory",
                "RUN_LOG_REPOSITORY_BACKEND": "in_memory",
                "ARTIFACTS_ROOT": str(self._tmp_root / "artifacts"),
                "RUN_WORKSPACE_ROOT": str(self._tmp_root / "workspace"),
                "TRACKER_TEMPLATE_PATH": str(ROOT_DIR / "assets" / "project_tracker_template.xlsx"),
            }
        )
        self._process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.api.app:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(self._port),
            ],
            cwd=str(ROOT_DIR),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self._wait_for_health()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._process is not None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
        shutil.rmtree(self._tmp_root, ignore_errors=True)

    def request_json(self, method: str, path: str, *, payload: dict[str, Any] | None = None, timeout: float = 30.0):
        response = requests.request(
            method,
            f"{self.base_url}{path}",
            json=payload,
            timeout=timeout,
            headers={"Accept": "application/json"},
        )
        try:
            return response.status_code, response.json()
        except Exception:
            return response.status_code, {}

    def wait_for_run(self, run_id: str, *, timeout_seconds: float, request_timeout_seconds: float = 180.0) -> dict[str, Any]:
        deadline = time.time() + timeout_seconds
        last_payload: dict[str, Any] = {}
        while time.time() < deadline:
            status_code, payload = self.request_json("GET", f"/api/runs/{run_id}", timeout=request_timeout_seconds)
            if status_code != 200:
                raise RuntimeError(f"run poll failed: {status_code} {payload}")
            last_payload = payload
            if payload.get("status") in {"success", "failed", "cancelled"}:
                return payload
            time.sleep(1.0)
        raise TimeoutError(f"timed out waiting for run {run_id}: {last_payload}")

    def _wait_for_health(self) -> None:
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    return
            except Exception:
                time.sleep(0.2)
                continue
        raise TimeoutError("timed out waiting for local API health check")


def _project_tracker_payload(
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
    return {
        "run_type": "project_tracker",
        "advanced_options": {
            "collect_mode": "native",
            "llm_correct": llm_correct,
            "anthropic_key": anthropic_key,
            "llm_model": llm_model,
            "llm_max_rows": llm_max_rows,
        },
        "params": {
            "start_date": start_date,
            "end_date": end_date,
            "notice_title": "",
            "bid_no": bid_no,
            "demand_org": "",
            "rows_per_page": 20,
            "max_pages": 1,
            "api_scope": api_scope,
        },
    }


def _select_tracker_view(entry: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "project_name",
        "gross_area_scale",
        "construction_cost",
        "demand_org_name",
        "demand_contact",
        "client_location",
        "site_location_1",
        "architect_office",
        "construction_start_date",
        "progress_note",
    ]
    return {key: entry.get(key, "") for key in keys}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bid-no", action="append", required=True, help="나라장터 공고번호. 여러 번 지정 가능")
    parser.add_argument("--start-date", default="20250101")
    parser.add_argument("--end-date", default="20250131")
    parser.add_argument("--api-scope", default="all")
    parser.add_argument("--winner-timeout", type=int, default=120)
    parser.add_argument("--tracker-timeout", type=int, default=90)
    parser.add_argument(
        "--llm-correct",
        action="store_true",
        default=str(os.getenv("TRACKER_LLM_CORRECT", "")).strip().lower() in {"1", "true", "y", "yes"},
    )
    parser.add_argument("--anthropic-key", type=str, default=(os.getenv("ANTHROPIC_API_KEY") or "").strip())
    parser.add_argument("--llm-model", type=str, default=(os.getenv("TRACKER_LLM_MODEL") or "claude-haiku-4-5-20251001").strip())
    parser.add_argument("--llm-max-rows", type=int, default=int(str(os.getenv("TRACKER_LLM_MAX_ROWS") or "20").strip() or "20"))
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    report: list[dict[str, Any]] = []
    with LocalApiHarness() as api:
        for bid_no in args.bid_no:
            status_code, created = api.request_json(
                "POST",
                "/api/runs",
                payload=_project_tracker_payload(
                    bid_no=str(bid_no).strip(),
                    start_date=args.start_date,
                    end_date=args.end_date,
                    api_scope=args.api_scope,
                    llm_correct=bool(args.llm_correct),
                    anthropic_key=str(args.anthropic_key or "").strip(),
                    llm_model=str(args.llm_model or "").strip(),
                    llm_max_rows=int(args.llm_max_rows or 0),
                ),
            )
            if status_code != 201:
                report.append({"bid_no": bid_no, "create_status": status_code, "create_payload": created})
                continue

            winner_detail = api.wait_for_run(created["id"], timeout_seconds=float(args.winner_timeout))
            winner_logs_status, winner_logs = api.request_json("GET", f"/api/runs/{created['id']}/logs?limit=50")
            tracker_result: dict[str, Any] = {}

            if winner_detail.get("status") == "success":
                tracker_create_status, tracker_created = api.request_json("POST", f"/api/runs/{created['id']}/tracker-export")
                tracker_result["create_status"] = tracker_create_status
                tracker_result["create_payload"] = tracker_created
                if tracker_create_status == 202:
                    tracker_detail = api.wait_for_run(tracker_created["id"], timeout_seconds=float(args.tracker_timeout))
                    tracker_entries_status, tracker_entries = api.request_json(
                        "GET",
                        f"/api/tracker-entries?source_tracker_run_id={tracker_created['id']}&page=1&page_size=5",
                    )
                    tracker_result["detail"] = tracker_detail
                    tracker_result["entries_status"] = tracker_entries_status
                    tracker_result["entries"] = [_select_tracker_view(item) for item in tracker_entries.get("items", [])]

            item = {
                "bid_no": bid_no,
                "winner_run": {
                    "id": created["id"],
                    "status": winner_detail.get("status"),
                    "summary": (winner_detail.get("summary") or {}).get("output", {}),
                    "error": winner_detail.get("error", {}),
                    "logs": winner_logs.get("items", []) if winner_logs_status == 200 else [],
                },
                "tracker_run": tracker_result,
            }
            report.append(item)
            print(json.dumps(item, ensure_ascii=False, indent=2))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
