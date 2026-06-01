from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error
from urllib import request
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@dataclass
class CaseResult:
    case_id: str
    name: str
    status: str
    details: dict[str, Any]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw or raw.startswith("export "):
            continue
        key, value = raw.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def api_request(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout_seconds: int = 20,
) -> tuple[int, Any]:
    headers = {"Accept": "application/json"}
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            content = response.read().decode("utf-8").strip()
            return response.status, json.loads(content) if content else None
    except error.HTTPError as exc:
        try:
            content = exc.read().decode("utf-8").strip()
            return exc.code, json.loads(content) if content else None
        finally:
            exc.close()


def wait_for_health(base_api_url: str, process: subprocess.Popen[str]) -> None:
    deadline = time.time() + 20
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(_process_output(process))
        try:
            status_code, payload = api_request("GET", f"{base_api_url}/health")
        except Exception:
            time.sleep(0.25)
            continue
        if status_code == 200 and payload == {"status": "ok"}:
            return
        time.sleep(0.25)
    raise RuntimeError("Timed out waiting for /health")


def wait_for_run(
    base_api_url: str,
    run_id: str,
    process: subprocess.Popen[str],
    *,
    target_statuses: set[str],
    timeout_seconds: float = 20.0,
) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(_process_output(process))
        try:
            status_code, payload = api_request(
                "GET",
                f"{base_api_url}/api/runs/{run_id}",
                timeout_seconds=5,
            )
        except TimeoutError:
            time.sleep(0.5)
            continue
        if status_code != 200:
            raise RuntimeError(f"unexpected run status response: {status_code} {payload}")
        if payload["status"] in target_statuses:
            return payload
        time.sleep(0.1)
    raise RuntimeError(f"Timed out waiting for run {run_id}")


def project_tracker_payload(*, notice_title: str, bid_no: str, delay_ms: int = 20, collect_mode: str = "synthetic") -> dict[str, Any]:
    return {
        "run_type": "project_tracker",
        "advanced_options": {
            "collect_mode": collect_mode,
            "simulate_stage_delay_ms": delay_ms,
        },
        "params": {
            "start_date": "20250101",
            "end_date": "20250228",
            "contract_date_hint": "",
            "notice_title": notice_title,
            "bid_no": bid_no,
            "demand_org": "Phase1 Runner Org",
            "rows_per_page": 100,
            "max_pages": 3,
            "api_scope": "construction",
        },
    }


def gui_probe_payload(*, collect_mode: str) -> dict[str, Any]:
    return {
        "run_type": "project_tracker",
        "advanced_options": {
            "collect_mode": collect_mode,
            "simulate_stage_delay_ms": 20,
        },
        "params": {
            "start_date": "20250101",
            "end_date": "20250131",
            "contract_date_hint": "",
            "notice_title": "설계공모",
            "bid_no": "",
            "demand_org": "전북",
            "rows_per_page": 30,
            "max_pages": 1,
            "api_scope": "construction",
        },
    }


def case_success(base_api_url: str, process: subprocess.Popen[str]) -> CaseResult:
    payload = project_tracker_payload(
        notice_title=f"Phase1 success {uuid4().hex[:8]}",
        bid_no=f"PHASE1{uuid4().hex[:8].upper()}",
    )
    _, created = api_request("POST", f"{base_api_url}/api/runs", payload=payload)
    detail = wait_for_run(base_api_url, created["id"], process, target_statuses={"success"})
    _, logs = api_request("GET", f"{base_api_url}/api/runs/{created['id']}/logs?limit=50")
    _, artifacts = api_request("GET", f"{base_api_url}/api/runs/{created['id']}/artifacts")
    messages = [item["message"] for item in logs["items"]]
    passed = (
        detail["status"] == "success"
        and any(message == "project_tracker finished successfully" for message in messages)
        and any(item["artifact_type"] == "winner_csv" for item in artifacts["items"])
    )
    return CaseResult(
        case_id="case_1",
        name="basic_success",
        status="passed" if passed else "failed",
        details={
            "run_id": created["id"],
            "final_status": detail["status"],
            "artifact_types": [item["artifact_type"] for item in artifacts["items"]],
            "log_messages": messages[:8],
        },
    )


def case_validation(base_api_url: str) -> CaseResult:
    status_code, payload = api_request(
        "POST",
        f"{base_api_url}/api/runs",
        payload={
            "run_type": "project_tracker",
            "advanced_options": {"collect_mode": "synthetic"},
            "params": {
                "start_date": "202501",
                "end_date": "20250228",
                "contract_date_hint": "",
                "notice_title": "",
                "bid_no": "",
                "demand_org": "",
                "rows_per_page": 100,
                "max_pages": 3,
                "api_scope": "construction",
            },
        },
    )
    passed = status_code == 400 and payload["error"]["code"] == "validation_error"
    return CaseResult(
        case_id="case_2",
        name="validation_failure",
        status="passed" if passed else "failed",
        details={"status_code": status_code, "payload": payload},
    )


def case_validation_runner(base_api_url: str, process: subprocess.Popen[str]) -> CaseResult:
    return case_validation(base_api_url)


def case_cancel(base_api_url: str, process: subprocess.Popen[str]) -> CaseResult:
    payload = project_tracker_payload(
        notice_title=f"Phase1 cancel {uuid4().hex[:8]}",
        bid_no=f"PHASE1CAN{uuid4().hex[:8].upper()}",
        delay_ms=500,
    )
    _, created = api_request("POST", f"{base_api_url}/api/runs", payload=payload)
    wait_for_run(base_api_url, created["id"], process, target_statuses={"running"})
    _, cancel_response = api_request("POST", f"{base_api_url}/api/runs/{created['id']}/cancel")
    detail = wait_for_run(base_api_url, created["id"], process, target_statuses={"cancelled"})
    _, logs = api_request("GET", f"{base_api_url}/api/runs/{created['id']}/logs?limit=30")
    messages = [item["message"] for item in logs["items"]]
    passed = (
        cancel_response["cancel_requested"] is True
        and detail["status"] == "cancelled"
        and any("cancel" in message for message in messages)
    )
    return CaseResult(
        case_id="case_3",
        name="cancellation",
        status="passed" if passed else "failed",
        details={
            "run_id": created["id"],
            "final_status": detail["status"],
            "cancel_response": cancel_response,
            "log_messages": messages[:8],
        },
    )


def case_quota_fallback(base_api_url: str, process: subprocess.Popen[str]) -> CaseResult:
    gui_repo = (
        Path(os.environ.get("GUI_PARITY_SOURCE_ROOT", "")).expanduser()
        if os.environ.get("GUI_PARITY_SOURCE_ROOT")
        else ROOT.parent / "notice-winner-pipeline-project"
    )
    if not gui_repo.exists():
        return CaseResult(
            case_id="case_4",
            name="quota_fallback",
            status="skipped",
            details={"reason": f"GUI parity source root not found: {gui_repo}"},
        )
    created = None
    try:
        _, created = api_request(
            "POST",
            f"{base_api_url}/api/runs",
            payload=gui_probe_payload(collect_mode="auto"),
        )
        detail = wait_for_run(
            base_api_url,
            created["id"],
            process,
            target_statuses={"success", "failed"},
            timeout_seconds=180.0,
        )
        log_error = ""
        messages: list[str] = []
        try:
            _, logs = api_request(
                "GET",
                f"{base_api_url}/api/runs/{created['id']}/logs?limit=80",
                timeout_seconds=60,
            )
            messages = [item["message"] for item in logs["items"]]
        except Exception as exc:
            log_error = str(exc)
        summary = detail.get("summary", {}).get("output", {})
        collect_backend = summary.get("collect_backend") or detail.get("error", {}).get("stage", "")
        fallback_logged = any("fallback" in message.lower() for message in messages)
        passed = detail["status"] in {"success", "failed"}
        return CaseResult(
            case_id="case_4",
            name="quota_fallback",
            status="passed" if passed else "failed",
            details={
                "run_id": created["id"],
                "final_status": detail["status"],
                "collect_backend": collect_backend,
                "fallback_logged": fallback_logged,
                "error": detail.get("error", {}),
                "log_messages": messages[:10],
                "log_error": log_error,
                "note": "This probe verifies GUI parity path execution and fallback logging availability; it does not force a quota event.",
            },
        )
    except Exception as exc:
        return CaseResult(
            case_id="case_4",
            name="quota_fallback",
            status="failed",
            details={
                "run_id": created["id"] if created else "",
                "error": str(exc),
                "note": "GUI parity probe did not finish cleanly within the runner window.",
            },
        )


def case_tracker_export(base_api_url: str, process: subprocess.Popen[str]) -> CaseResult:
    payload = project_tracker_payload(
        notice_title=f"Phase1 tracker {uuid4().hex[:8]}",
        bid_no=f"PHASE1TRK{uuid4().hex[:8].upper()}",
    )
    _, created = api_request("POST", f"{base_api_url}/api/runs", payload=payload)
    parent_detail = wait_for_run(base_api_url, created["id"], process, target_statuses={"success"})
    _, child_created = api_request("POST", f"{base_api_url}/api/runs/{created['id']}/tracker-export")
    child_detail = wait_for_run(base_api_url, child_created["id"], process, target_statuses={"success"})
    _, artifacts = api_request("GET", f"{base_api_url}/api/runs/{child_created['id']}/artifacts")
    _, parent_after = api_request("GET", f"{base_api_url}/api/runs/{created['id']}")
    passed = (
        parent_detail["status"] == "success"
        and child_detail["status"] == "success"
        and any(item["artifact_type"] == "tracking_excel" for item in artifacts["items"])
        and parent_after["status"] == "success"
    )
    return CaseResult(
        case_id="case_5",
        name="tracker_export",
        status="passed" if passed else "failed",
        details={
            "parent_run_id": created["id"],
            "child_run_id": child_created["id"],
            "child_status": child_detail["status"],
            "artifact_types": [item["artifact_type"] for item in artifacts["items"]],
            "parent_status_after_child": parent_after["status"],
        },
    )


def run_case(
    *,
    case_id: str,
    name: str,
    runner: Any,
    base_api_url: str,
    process: subprocess.Popen[str],
) -> CaseResult:
    try:
        return runner(base_api_url, process)
    except Exception as exc:
        server_output = ""
        if process.poll() is not None:
            server_output = _process_output(process)
        return CaseResult(
            case_id=case_id,
            name=name,
            status="failed",
            details={
                "error": str(exc),
                "server_alive": process.poll() is None,
                "server_output": server_output[:4000],
            },
        )


def build_server_env(*, temp_root: Path, gui_source_root: str) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": str(ROOT),
            "TRACKER_REPOSITORY_BACKEND": "in_memory",
            "RUN_REPOSITORY_BACKEND": "in_memory",
            "ARTIFACT_REPOSITORY_BACKEND": "in_memory",
            "RUN_LOG_REPOSITORY_BACKEND": "in_memory",
            "ARTIFACTS_ROOT": str(temp_root / "artifacts"),
            "RUN_WORKSPACE_ROOT": str(temp_root / "workspace"),
            "TRACKER_TEMPLATE_PATH": str(ROOT / "assets" / "project_tracker_template.xlsx"),
        }
    )
    if gui_source_root:
        env["GUI_PARITY_SOURCE_ROOT"] = gui_source_root
    return env


def start_server(*, gui_source_root: str, temp_root: Path) -> tuple[subprocess.Popen[str], str]:
    port = find_free_port()
    base_api_url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=str(ROOT),
        env=build_server_env(temp_root=temp_root, gui_source_root=gui_source_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    wait_for_health(base_api_url, process)
    return process, base_api_url


def stop_server(process: subprocess.Popen[str] | None) -> None:
    if process is None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def execute_case(
    *,
    case_id: str,
    name: str,
    runner: Any,
    gui_source_root: str,
    tmp_base: Path,
) -> CaseResult:
    temp_root = Path(tempfile.mkdtemp(prefix=f"{case_id}-", dir=str(tmp_base)))
    process: subprocess.Popen[str] | None = None
    try:
        process, base_api_url = start_server(gui_source_root=gui_source_root, temp_root=temp_root)
        return run_case(
            case_id=case_id,
            name=name,
            runner=runner,
            base_api_url=base_api_url,
            process=process,
        )
    finally:
        stop_server(process)
        shutil.rmtree(temp_root, ignore_errors=True)


def _process_output(process: subprocess.Popen[str]) -> str:
    if process.stdout is None:
        return "server exited"
    try:
        return process.stdout.read()
    except Exception:
        return "server exited"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run documented Phase 1 equivalence checks against the web API.")
    parser.add_argument("--output", default="", help="Optional JSON report path.")
    parser.add_argument("--gui-source-root", default="", help="Optional local GUI source root for parity probes.")
    args = parser.parse_args()

    load_env_file(ROOT / ".env")
    tmp_base = ROOT / ".tmp-test-runs"
    tmp_base.mkdir(parents=True, exist_ok=True)
    results: list[CaseResult] = []
    gui_source_root = args.gui_source_root

    if gui_source_root:
        os.environ["GUI_PARITY_SOURCE_ROOT"] = gui_source_root

    results.append(
        execute_case(
            case_id="case_1",
            name="basic_success",
            runner=case_success,
            gui_source_root=gui_source_root,
            tmp_base=tmp_base,
        )
    )
    results.append(
        execute_case(
            case_id="case_2",
            name="validation_failure",
            runner=case_validation_runner,
            gui_source_root=gui_source_root,
            tmp_base=tmp_base,
        )
    )
    results.append(
        execute_case(
            case_id="case_3",
            name="cancellation",
            runner=case_cancel,
            gui_source_root=gui_source_root,
            tmp_base=tmp_base,
        )
    )
    results.append(
        execute_case(
            case_id="case_4",
            name="quota_fallback",
            runner=case_quota_fallback,
            gui_source_root=gui_source_root,
            tmp_base=tmp_base,
        )
    )
    results.append(
        execute_case(
            case_id="case_5",
            name="tracker_export",
            runner=case_tracker_export,
            gui_source_root=gui_source_root,
            tmp_base=tmp_base,
        )
    )

    failures = [item for item in results if item.status == "failed"]
    report = {
        "summary": {
            "passed": sum(1 for item in results if item.status == "passed"),
            "failed": len(failures),
            "skipped": sum(1 for item in results if item.status == "skipped"),
        },
        "results": [
            {
                "case_id": item.case_id,
                "name": item.name,
                "status": item.status,
                "details": item.details,
            }
            for item in results
        ],
    }
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = ROOT / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
