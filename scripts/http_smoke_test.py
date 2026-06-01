from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error
from urllib import parse
from urllib import request
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def supabase_request(
    method: str,
    path: str,
    *,
    query: list[tuple[str, str]] | None = None,
    payload: dict[str, Any] | None = None,
) -> Any:
    base_url = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1"
    api_key = (
        os.environ.get("SUPABASE_SECRET_KEY", "").strip()
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    url = base_url + path
    if query:
        url += "?" + parse.urlencode(query, doseq=True, safe="(),.*")

    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        headers["Prefer"] = "return=representation"
        data = json.dumps(payload).encode("utf-8")

    req = request.Request(url, data=data, headers=headers, method=method)
    with request.urlopen(req, timeout=15) as response:
        body = response.read().decode("utf-8").strip()
        return json.loads(body) if body else None


def has_supabase_rest_config() -> bool:
    base_url = os.environ.get("SUPABASE_URL", "").strip()
    api_key = (
        os.environ.get("SUPABASE_SECRET_KEY", "").strip()
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    return bool(base_url and api_key)


def record_artifact_cleanup_metadata(
    artifacts: list[dict[str, Any]],
    artifact_ids: list[str],
    artifact_storage_paths: list[str],
) -> None:
    for item in artifacts:
        artifact_id = str(item.get("id") or "").strip()
        if artifact_id:
            artifact_ids.append(artifact_id)
        storage_path = str(item.get("storage_path") or "").strip()
        if storage_path:
            artifact_storage_paths.append(storage_path)


def api_request(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
) -> Any:
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers=headers, method=method)
    with request.urlopen(req, timeout=15) as response:
        body = response.read().decode("utf-8").strip()
        return json.loads(body) if body else None


def http_status(url: str) -> int:
    req = request.Request(url, headers={"Accept": "*/*"}, method="GET")
    with request.urlopen(req, timeout=15) as response:
        response.read()
        return response.status


def wait_for_health(base_api_url: str, process: subprocess.Popen[str]) -> None:
    health_url = f"{base_api_url}/health"
    deadline = time.time() + 20
    while time.time() < deadline:
        if process.poll() is not None:
            output = ""
            if process.stdout is not None:
                output = process.stdout.read()
            raise RuntimeError(f"uvicorn exited early.\n{output}")
        try:
            payload = api_request("GET", health_url)
        except Exception:
            time.sleep(0.5)
            continue
        if payload == {"status": "ok"}:
            return
        time.sleep(0.5)
    raise RuntimeError("Timed out waiting for /health")


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_run(
    base_api_url: str,
    run_id: str,
    process: subprocess.Popen[str],
    *,
    target_statuses: set[str] | None = None,
) -> Any:
    detail_url = f"{base_api_url}/api/runs/{run_id}"
    targets = target_statuses or {"success"}
    deadline = time.time() + 20
    while time.time() < deadline:
        if process.poll() is not None:
            output = ""
            if process.stdout is not None:
                output = process.stdout.read()
            raise RuntimeError(f"uvicorn exited early.\n{output}")
        payload = api_request("GET", detail_url)
        status_value = payload["status"]
        if status_value in targets:
            return payload
        if status_value == "failed":
            raise RuntimeError(f"run failed: {json.dumps(payload, ensure_ascii=False)}")
        time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for run {run_id}")


def main() -> int:
    load_env_file(ROOT / ".env")

    from backend.phase1_defaults import load_phase1_identity

    identity = load_phase1_identity()
    org_id = str(identity.organization_id)

    port = find_free_port()
    base_api_url = f"http://127.0.0.1:{port}"

    parent_run_id = None
    child_run_id = None
    cancel_run_id = None
    entry_ids: list[str] = []
    artifact_ids: list[str] = []
    artifact_storage_paths: list[str] = []
    process: subprocess.Popen[str] | None = None

    try:
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
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        wait_for_health(base_api_url, process)

        create_response = api_request(
            "POST",
            f"{base_api_url}/api/runs",
            payload={
                "run_type": "project_tracker",
                "advanced_options": {"collect_mode": "synthetic"},
                "params": {
                    "start_date": "20250101",
                    "end_date": "20250131",
                    "notice_title": f"HTTP smoke {uuid4().hex[:8]}",
                    "bid_no": f"HTTPSMOKE{uuid4().hex[:8].upper()}",
                    "demand_org": "Smoke Test Org",
                    "rows_per_page": 50,
                    "max_pages": 2,
                    "api_scope": "construction",
                },
            },
        )
        parent_run_id = create_response["id"]
        parent_detail = wait_for_run(base_api_url, parent_run_id, process)
        parent_logs = api_request(
            "GET",
            f"{base_api_url}/api/runs/{parent_run_id}/logs?limit=20",
        )
        parent_artifacts = api_request(
            "GET",
            f"{base_api_url}/api/runs/{parent_run_id}/artifacts",
        )
        record_artifact_cleanup_metadata(parent_artifacts["items"], artifact_ids, artifact_storage_paths)
        winner_csv_artifact = next(
            item for item in parent_artifacts["items"] if item["artifact_type"] == "winner_csv"
        )
        winner_csv_download_status = http_status(winner_csv_artifact["download_url"])

        tracker_export_response = api_request(
            "POST",
            f"{base_api_url}/api/runs/{parent_run_id}/tracker-export",
        )
        child_run_id = tracker_export_response["id"]
        child_detail = wait_for_run(base_api_url, child_run_id, process)
        child_logs = api_request(
            "GET",
            f"{base_api_url}/api/runs/{child_run_id}/logs?limit=20",
        )
        child_artifacts = api_request(
            "GET",
            f"{base_api_url}/api/runs/{child_run_id}/artifacts",
        )
        record_artifact_cleanup_metadata(child_artifacts["items"], artifact_ids, artifact_storage_paths)
        tracking_excel_artifact = next(
            item for item in child_artifacts["items"] if item["artifact_type"] == "tracking_excel"
        )
        tracking_excel_download_status = http_status(tracking_excel_artifact["download_url"])

        run_list_response = api_request(
            "GET",
            f"{base_api_url}/api/runs?run_type=tracker_export&page=1&page_size=20",
        )

        list_response = api_request(
            "GET",
            f"{base_api_url}/api/tracker-entries?source_tracker_run_id={child_run_id}&page=1&page_size=20",
        )
        entry_id = list_response["items"][0]["id"]
        entry_ids = [item["id"] for item in list_response["items"]]
        patch_response = api_request(
            "PATCH",
            f"{base_api_url}/api/tracker-entries/{entry_id}",
            payload={
                "field_name": "project_name",
                "value": "Project Name Final",
                "actor_label": "hyunmo",
                "change_source": "web",
            },
        )
        audit_response = api_request(
            "GET",
            f"{base_api_url}/api/tracker-entries/{entry_id}/audit-logs?limit=10",
        )
        cancel_create_response = api_request(
            "POST",
            f"{base_api_url}/api/runs",
            payload={
                "run_type": "project_tracker",
                "advanced_options": {
                    "collect_mode": "synthetic",
                    "simulate_stage_delay_ms": 250,
                },
                "params": {
                    "start_date": "20250101",
                    "end_date": "20250131",
                    "notice_title": f"HTTP cancel {uuid4().hex[:8]}",
                    "bid_no": f"HTTPCANCEL{uuid4().hex[:8].upper()}",
                    "demand_org": "Smoke Test Org",
                    "rows_per_page": 50,
                    "max_pages": 2,
                    "api_scope": "construction",
                },
            },
        )
        cancel_run_id = cancel_create_response["id"]
        cancel_response = api_request(
            "POST",
            f"{base_api_url}/api/runs/{cancel_run_id}/cancel",
        )
        cancelled_detail = wait_for_run(
            base_api_url,
            cancel_run_id,
            process,
            target_statuses={"cancelled"},
        )
        cancelled_logs = api_request(
            "GET",
            f"{base_api_url}/api/runs/{cancel_run_id}/logs?limit=20",
        )

        print(
            json.dumps(
                {
                    "health": "ok",
                    "parent_status": parent_detail["status"],
                    "parent_collect_backend": parent_detail["summary"]["output"]["collect_backend"],
                    "parent_filter_backend": parent_detail["summary"]["output"]["filter_backend"],
                    "parent_rescan_backend": parent_detail["summary"]["output"]["rescan_backend"],
                    "parent_export_backend": parent_detail["summary"]["output"]["export_backend"],
                    "parent_seed_rows": parent_detail["summary"]["output"]["seed_rows"],
                    "parent_candidate_rows": parent_detail["summary"]["output"]["candidate_rows"],
                    "parent_internal_nav_rows": parent_detail["summary"]["output"]["internal_nav_rows"],
                    "parent_post_collect_rows": parent_detail["summary"]["output"]["post_collect_rows"],
                    "parent_summary_rows": parent_detail["summary"]["output"]["winner_csv_rows"],
                    "parent_log_count": len(parent_logs["items"]),
                    "parent_artifact_count": len(parent_artifacts["items"]),
                    "parent_artifact_checksum": winner_csv_artifact["checksum"],
                    "parent_artifact_meta_rows": winner_csv_artifact["meta"]["rows"],
                    "winner_csv_download_status": winner_csv_download_status,
                    "child_status": child_detail["status"],
                    "child_tracker_rows": child_detail["summary"]["output"]["tracker_entry_rows"],
                    "child_log_count": len(child_logs["items"]),
                    "child_artifact_count": len(child_artifacts["items"]),
                    "child_artifact_checksum": tracking_excel_artifact["checksum"],
                    "child_artifact_meta_rows": tracking_excel_artifact["meta"]["rows"],
                    "tracking_excel_download_status": tracking_excel_download_status,
                    "run_list_total": run_list_response["total"],
                    "list_total": list_response["total"],
                    "list_items": len(list_response["items"]),
                    "patched_changed": patch_response["changed"],
                    "patched_project_name": patch_response["entry"]["project_name"],
                    "patched_overridden_fields": patch_response["entry"]["overridden_fields"],
                    "audit_log_count": len(audit_response["items"]),
                    "latest_audit_field": (
                        audit_response["items"][0]["field_name"] if audit_response["items"] else None
                    ),
                    "cancel_response_status": cancel_response["status"],
                    "cancel_requested_flag": cancel_response["cancel_requested"],
                    "cancelled_status": cancelled_detail["status"],
                    "cancelled_log_count": len(cancelled_logs["items"]),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    finally:
        run_ids = [run_id for run_id in [parent_run_id, child_run_id, cancel_run_id] if run_id is not None]
        if has_supabase_rest_config():
            if child_run_id is not None:
                existing_entries = supabase_request(
                    "GET",
                    "/tracker_entries",
                    query=[
                        ("select", "id"),
                        ("organization_id", f"eq.{org_id}"),
                        ("source_tracker_run_id", f"eq.{child_run_id}"),
                    ],
                ) or []
                entry_ids.extend(row["id"] for row in existing_entries)
            if run_ids:
                clauses = []
                for run_id in run_ids:
                    clauses.append(f"run_id.eq.{run_id}")
                if clauses:
                    or_filter = "(" + ",".join(clauses) + ")"
                    existing_artifacts = supabase_request(
                        "GET",
                        "/run_artifacts",
                        query=[
                            ("select", "id,storage_path"),
                            ("organization_id", f"eq.{org_id}"),
                            ("or", or_filter),
                        ],
                    ) or []
                    artifact_ids.extend(row["id"] for row in existing_artifacts)
                    artifact_storage_paths.extend(row["storage_path"] for row in existing_artifacts)
            for entry_id in sorted(set(entry_ids)):
                supabase_request("DELETE", "/tracker_entries", query=[("id", f"eq.{entry_id}")])
            for artifact_id in sorted(set(artifact_ids)):
                supabase_request("DELETE", "/run_artifacts", query=[("id", f"eq.{artifact_id}")])
        for storage_path in sorted(set(artifact_storage_paths)):
            path = ROOT / storage_path
            if path.exists():
                path.unlink()
        artifacts_root = ROOT / "output" / "artifacts"
        for run_id in run_ids:
            run_dir = artifacts_root / run_id
            if run_dir.exists():
                shutil.rmtree(run_dir, ignore_errors=True)
            legacy_dir = ROOT / run_id
            if legacy_dir.exists():
                shutil.rmtree(legacy_dir, ignore_errors=True)
        if has_supabase_rest_config():
            for run_id in reversed(run_ids):
                supabase_request("DELETE", "/pipeline_runs", query=[("id", f"eq.{run_id}")])
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(body)
        raise
