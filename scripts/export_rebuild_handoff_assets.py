from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "docs" / "rebuild_handoff_package"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _evidence_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in [
        "SUPABASE_URL",
        "SUPABASE_SECRET_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SECRET",
    ]:
        env[key] = ""
    env.update(
        {
            "PHASE2_AUTH_ENABLED": "0",
            "PHASE2_AUTH_DELIVER_INVITE_EMAILS": "0",
            "TRACKER_REPOSITORY_BACKEND": "in_memory",
            "RUN_REPOSITORY_BACKEND": "in_memory",
            "ARTIFACT_REPOSITORY_BACKEND": "in_memory",
            "RUN_LOG_REPOSITORY_BACKEND": "in_memory",
            "TRACKER_CHANGE_EVENT_REPOSITORY_BACKEND": "in_memory",
            "BACKFILL_CONFLICT_REPOSITORY_BACKEND": "in_memory",
            "DOWNLOAD_AUDIT_LOG_REPOSITORY_BACKEND": "in_memory",
            "SALES_CLAIM_REPOSITORY_BACKEND": "in_memory",
            "RELATED_NOTICE_PUBLICATION_REPOSITORY_BACKEND": "in_memory",
            "HOME_BOOTSTRAP_SNAPSHOT_REPOSITORY_BACKEND": "in_memory",
            "PROJECT_TRACKER_ENABLE_SYNTHETIC_DEBUG": "1",
            "PROJECT_TRACKER_COLLECT_MODE": "synthetic",
            "ARTIFACTS_ROOT": str(ROOT / ".tmp-rebuild-evidence-artifacts"),
            "TRACKER_DOWNLOAD_JOB_ROOT": str(ROOT / ".tmp-rebuild-evidence-download-jobs"),
        }
    )
    return env


def _json_request(method: str, url: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8").strip()
            return response.status, json.loads(text) if text else None
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace").strip()
        try:
            body: Any = json.loads(text) if text else None
        except json.JSONDecodeError:
            body = {"raw": text}
        return exc.code, body
    except urllib.error.URLError as exc:
        return 0, {"error": str(exc.reason)}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_health(base_url: str, process: subprocess.Popen[str]) -> None:
    deadline = time.time() + 40
    while time.time() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout is not None else ""
            raise RuntimeError(f"evidence server exited early\n{output}")
        status, payload = _json_request("GET", f"{base_url}/health")
        if status == 200 and payload == {"status": "ok"}:
            return
        time.sleep(0.5)
    raise TimeoutError("timed out waiting for evidence server")


def _wait_for_run(base_url: str, run_id: str) -> dict[str, Any]:
    deadline = time.time() + 40
    last_payload: dict[str, Any] = {}
    while time.time() < deadline:
        status, payload = _json_request("GET", f"{base_url}/api/runs/{run_id}")
        if status == 200 and isinstance(payload, dict):
            last_payload = payload
            if payload.get("status") in {"success", "failed", "canceled", "cancelled"}:
                return payload
        time.sleep(0.5)
    return last_payload


def _capture_screenshot(chrome_path: str, url: str, output_path: Path, *, height: int = 1200) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    user_data_dir = ROOT / ".tmp-rebuild-evidence-chrome"
    if user_data_dir.exists():
        shutil.rmtree(user_data_dir)
    command = [
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--hide-scrollbars",
        f"--user-data-dir={user_data_dir}",
        "--window-size=1440," + str(height),
        "--virtual-time-budget=7000",
        f"--screenshot={output_path}",
        url,
    ]
    result = subprocess.run(command, cwd=str(ROOT), text=True, capture_output=True, timeout=45)
    return {
        "url": url,
        "path": str(output_path.relative_to(ROOT)),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "exists": output_path.exists(),
        "bytes": output_path.stat().st_size if output_path.exists() else 0,
    }


def _chrome_path() -> str | None:
    candidates = [
        Path(os.environ.get("PROGRAMFILES", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def _capture_screenshots_with_playwright(chrome_path: str, base_url: str) -> list[dict[str, Any]]:
    from playwright.sync_api import sync_playwright

    screenshot_dir = OUTPUT_ROOT / "screenshots"
    video_dir = OUTPUT_ROOT / "user-flow"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome_path, headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 1200},
            record_video_dir=str(video_dir),
            record_video_size={"width": 1440, "height": 1200},
        )
        page = context.new_page()
        page.goto(f"{base_url}/?mode=user", wait_until="domcontentloaded")
        page.wait_for_timeout(3500)
        user_path = screenshot_dir / "01_user_home.png"
        page.screenshot(path=str(user_path), full_page=True)
        results.append({"path": str(user_path.relative_to(ROOT)), "exists": user_path.exists(), "bytes": user_path.stat().st_size})

        try:
            page.click("#mode-toggle-button", timeout=5000)
        except Exception:
            page.click("text=운영자 모드", timeout=5000)
        page.wait_for_timeout(3000)
        admin_path = screenshot_dir / "02_admin_project_status.png"
        page.screenshot(path=str(admin_path), full_page=True)
        results.append({"path": str(admin_path.relative_to(ROOT)), "exists": admin_path.exists(), "bytes": admin_path.stat().st_size})


        page.close()
        context.close()

        nojs_context = browser.new_context(viewport={"width": 1440, "height": 1200}, java_script_enabled=False)
        nojs_page = nojs_context.new_page()
        nojs_page.goto(f"{base_url}/?invite_token=synthetic-preview-token", wait_until="domcontentloaded")
        nojs_page.wait_for_timeout(500)
        login_path = screenshot_dir / "04_login_invite_preview_shell.png"
        nojs_page.screenshot(path=str(login_path), full_page=True)
        results.append({"path": str(login_path.relative_to(ROOT)), "exists": login_path.exists(), "bytes": login_path.stat().st_size})
        nojs_context.close()
        browser.close()

    videos = sorted(video_dir.glob("*.webm"), key=lambda item: item.stat().st_mtime, reverse=True)
    if videos:
        target = video_dir / "current_app_flow.webm"
        if target.exists():
            target.unlink()
        videos[0].replace(target)
        for extra in videos[1:]:
            try:
                extra.unlink()
            except OSError:
                pass
        results.append({"path": str(target.relative_to(ROOT)), "exists": target.exists(), "bytes": target.stat().st_size})
    return results


def _api_samples(base_url: str) -> dict[str, Any]:
    api_dir = OUTPUT_ROOT / "api-samples"
    sample_dir = OUTPUT_ROOT / "sample-data"
    summary: dict[str, Any] = {}

    endpoints = [
        ("00_health", "GET", "/health", None),
        ("01_dashboard_summary", "GET", "/api/dashboard/summary", None),
        ("02_home_bootstrap", "GET", "/api/home-bootstrap", None),
        ("03_tracker_entries", "GET", "/api/tracker-entries", None),
        ("04_sales_claims", "GET", "/api/sales-claims", None),
        ("05_sales_claim_overview", "GET", "/api/sales-claims/overview", None),
        ("06_sales_claim_summary_by_user", "GET", "/api/sales-claims/summary-by-user", None),
        ("07_admin_organization_bootstrap", "GET", "/api/admin/organization-panel-bootstrap", None),
        ("09_tracker_missing_report", "GET", "/api/tracker-entries/missing-report", None),
    ]
    for name, method, path, payload in endpoints:
        status, body = _json_request(method, base_url + path, payload)
        _write_json(api_dir / f"{name}.json", {"method": method, "path": path, "status": status, "body": body})
        summary[name] = {"status": status, "path": path}

    run_payload = {
        "run_type": "project_tracker",
        "advanced_options": {"collect_mode": "synthetic"},
        "params": {
            "start_date": "20250101",
            "end_date": "20250131",
            "notice_title": f"rebuild handoff {uuid4().hex[:8]}",
            "bid_no": f"REBUILD{uuid4().hex[:8].upper()}",
            "demand_org": "Synthetic Rebuild Org",
            "rows_per_page": 50,
            "max_pages": 2,
            "api_scope": "construction",
        },
    }
    status, run_create = _json_request("POST", base_url + "/api/runs", run_payload)
    _write_json(api_dir / "10_run_create_request_response.json", {"request": run_payload, "status": status, "body": run_create})
    run_id = str((run_create or {}).get("id") or (run_create or {}).get("run_id") or "")
    if run_id:
        run_detail = _wait_for_run(base_url, run_id)
        _write_json(api_dir / "11_run_detail_after_completion.json", run_detail)
        for name, path in [
            ("12_run_logs", f"/api/runs/{run_id}/logs"),
            ("13_run_artifacts", f"/api/runs/{run_id}/artifacts"),
        ]:
            sample_status, sample_body = _json_request("GET", base_url + path)
            _write_json(api_dir / f"{name}.json", {"method": "GET", "path": path, "status": sample_status, "body": sample_body})
        export_status, export_body = _json_request("POST", f"{base_url}/api/runs/{run_id}/tracker-export")
        _write_json(
            api_dir / "14_tracker_export_request_response.json",
            {"method": "POST", "path": f"/api/runs/{run_id}/tracker-export", "status": export_status, "body": export_body},
        )
        export_id = str((export_body or {}).get("id") or (export_body or {}).get("run_id") or "")
        if export_id:
            export_detail = _wait_for_run(base_url, export_id)
            _write_json(api_dir / "15_tracker_export_detail_after_completion.json", export_detail)

    status, tracker_entries = _json_request("GET", base_url + "/api/tracker-entries")
    body = tracker_entries if status == 200 else {}
    entries = []
    if isinstance(body, dict):
        entries = list(body.get("items") or [])
    elif isinstance(body, list):
        entries = body
    _write_json(
        sample_dir / "synthetic_tracker_entries_excerpt.json",
        {
            "source": "in_memory synthetic API",
            "status": status,
            "count": len(entries),
            "items": entries[:5],
        },
    )
    _write_json(sample_dir / "synthetic_run_create_payload.json", run_payload)
    return summary


def _write_checklist() -> None:
    _write_text(
        OUTPUT_ROOT / "checklists" / "REBUILD_ACCEPTANCE_CHECKLIST_KR.md",
        """# 재구축 검수 체크리스트

- 기준 문서: `docs/spec/REBUILD_RFP_FINAL_SPEC_KR.md`
- 목적: 새 구현팀 산출물이 현재 구현 기준 업무 흐름을 95% 이상 재현하는지 확인한다.

## 1. 인증/초대/권한

- [ ] 미인증 사용자는 로그인 화면만 본다.
- [ ] 이메일/비밀번호 로그인과 로그아웃이 동작한다.
- [ ] `org_admin`이 `org_member`를 초대할 수 있다.
- [ ] 초대 수락은 같은 이메일에서만 성공한다.
- [ ] 초대 수락 재시도는 membership을 중복 생성하지 않는다.
- [ ] 일반 사용자는 관리자 탭과 관리자 API에 접근할 수 없다.
- [ ] `platform_admin`, `org_admin`, `org_member`의 화면과 API 권한이 서버에서 재검증된다.

## 2. 실행/run/artifact

- [ ] `project_tracker` 실행을 생성할 수 있다.
- [ ] run status가 `queued`, `running`, `success`, `failed`, `canceled` 계열로 표현된다.
- [ ] 실행 로그가 조회된다.
- [ ] 성공한 `project_tracker` 뒤 `tracker_export` child run이 자동 queue 또는 재사용된다.
- [ ] 같은 parent의 `queued/running/success` export child가 있으면 새 run을 만들지 않는다.
- [ ] artifact metadata와 local file 다운로드가 연결된다.
- [ ] report job과 tracker download job의 상태가 UI/API에서 일관된다.

## 3. 트래커/관련 공고

- [ ] tracker 목록, 검색, 필터, 정렬이 동작한다.
- [ ] tracker 상세 drawer에서 원본 값, override, effective value가 구분된다.
- [ ] editable field 수정 후 목록과 상세가 같은 값을 표시한다.
- [ ] change event 또는 audit trail이 남는다.
- [ ] missing report가 표시된다.
- [ ] cleanup preview 없이 apply가 수행되지 않는다.
- [ ] related notice는 published snapshot/cache/read path 기준으로 표시된다.

## 4. 영업 파이프라인

- [ ] 미배정 프로젝트를 claim할 수 있다.
- [ ] 이미 active claim이 있는 프로젝트는 일반 사용자가 중복 claim할 수 없다.
- [ ] 메모 변경 이벤트는 `note_update`로 남는다.
- [ ] 이관은 요청/승인이 아니라 직접 `transfer`로 처리된다.
- [ ] 해제/강제 해제 이벤트는 `release`, `force_release`로 구분된다.
- [ ] 종료는 `close_won`, `close_lost`로 구분된다.
- [ ] 종료된 건은 진행 중 목록에서 빠지고 archive/종료 정리에서 보인다.

## 5. 관리자/local admin/감사

- [ ] 관리자 모드 상단 탭이 표시된다.
- [ ] 사용자/초대/소속 상태 관리가 동작한다.
- [ ] platform admin 계정 생성/비밀번호 초기화 도구가 권한 제한된다.
- [ ] local admin 관리자 화면에서 tab 목록, table, 컬럼 필터, sync 상태가 표시된다.
- [ ] 로그인, 초대, 사용자 변경, sales action, 다운로드, local admin sync가 감사 로그에 남는다.

## 6. 클린룸/IP

- [ ] 기존 소스 코드, 운영 DB, 운영 secret을 새 구현팀에 제공하지 않았다.
- [ ] 샘플 데이터는 synthetic 또는 비식별 데이터다.
- [ ] 오픈소스 라이선스 목록을 납품물에 포함했다.
- [ ] 독립 구현 확인서를 제출했다.
""",
    )


def _write_flow_script() -> None:
    _write_text(
        OUTPUT_ROOT / "user-flow" / "USER_FLOW_RECORDING_SCRIPT_KR.md",
        """# 5~10분 사용 흐름 녹화 대본

이 문서는 실제 녹화자가 화면을 열고 따라갈 순서다. 녹화에는 운영 데이터가 아니라 synthetic 또는 비식별 seed 데이터를 사용한다.

## 0. 준비

1. 브라우저에서 앱을 연다.
2. synthetic 또는 staging seed 데이터 계정으로 로그인한다.
3. 녹화 시작 전에 개발자 도구, secret, 운영 DB 화면을 닫는다.

## 1. 로그인과 사용자 모드

1. 로그인 화면을 보여준다.
2. 이메일/비밀번호로 로그인한다.
3. 사용자 모드 header, 역할 badge, 사용자 모드/관리자 모드 전환 버튼을 보여준다.
4. `내가 진행 중인 영업`, `회사 전체 진행 중인 영업`, `전체 영업 대상 프로젝트` 영역을 천천히 훑는다.

## 2. 실행과 산출물

1. `project_tracker` 실행 생성 패널을 연다.
2. synthetic 조건으로 실행을 생성한다.
3. 최근 실행에서 `queued/running/success` 흐름을 보여준다.
4. 실행 상세에서 로그, artifact, report 영역을 보여준다.
5. `tracker_export` child run이 생성 또는 재사용되는 지점을 설명한다.

## 3. 트래커와 관련 공고

1. tracker 목록을 연다.
2. 검색/필터/정렬을 적용한다.
3. 프로젝트 상세 drawer를 연다.
4. 원본 값, override, effective value를 설명한다.
5. 관련 공고 패널을 열고 snapshot/cache 기반 표시를 보여준다.
6. missing report와 cleanup preview 영역을 보여준다.

## 4. 영업 파이프라인

1. 미배정 프로젝트를 claim한다.
2. 메모를 추가한다.
3. 이관 대상자를 선택해 transfer한다.
4. release 또는 close won/lost 처리 modal을 보여준다.
5. 진행 중 목록과 archive/종료 정리에서 상태가 바뀐 것을 보여준다.

## 5. 관리자 모드

1. 관리자 모드로 전환한다.
2. 사용자/초대 관리 화면을 보여준다.
3. 초대 생성 form, 초대 링크 fallback, 사용자 목록을 보여준다.
4. 감사 로그를 조회한다.
5. local admin 관리자 탭을 열고 sheet 목록, table, 컬럼 필터, sync 버튼을 보여준다.

## 6. 마무리

1. 다운로드 job 또는 artifact 다운로드 버튼을 보여준다.
2. download audit log가 남는 것을 설명한다.
3. 로그아웃한다.

## 녹화 시 주의사항

1. 운영 secret, API key, 실제 고객명, 실제 영업 메모가 나오지 않게 한다.
2. 샘플 데이터는 synthetic 또는 비식별 데이터만 사용한다.
3. 기존 회사 소스 코드 화면은 녹화하지 않는다.
4. 기능 동작과 화면 흐름을 보여주는 것이 목적이며, 코드 구조를 설명하지 않는다.
""",
    )


def _write_readme(summary: dict[str, Any], screenshot_results: list[dict[str, Any]]) -> None:
    _write_text(
        OUTPUT_ROOT / "README_KR.md",
        f"""# 재구축 전달 보조 패키지

- 생성일: 2026-04-30
- 생성 방식: local `in_memory` repository + synthetic collect mode
- 운영 secret 사용 여부: 사용하지 않음. 추출 프로세스에서 Supabase 관련 환경변수를 빈 값으로 덮어씀.
- 기준 문서: `docs/spec/REBUILD_RFP_FINAL_SPEC_KR.md`

## 구성

1. `api-samples/`: 주요 API 요청/응답 JSON
2. `sample-data/`: synthetic 샘플 데이터 발췌
3. `screenshots/`: 로컬 synthetic 화면 캡처
4. `checklists/REBUILD_ACCEPTANCE_CHECKLIST_KR.md`: 외부 개발사 검수 체크리스트
5. `user-flow/USER_FLOW_RECORDING_SCRIPT_KR.md`: 5~10분 사용 흐름 녹화 대본

## API 샘플 추출 상태

```json
{json.dumps(summary, ensure_ascii=False, indent=2)}
```

## 스크린샷 추출 상태

```json
{json.dumps(screenshot_results, ensure_ascii=False, indent=2)}
```

## 전달 권장 순서

외부 개발사 또는 새 구현팀에는 아래 순서로 전달한다.

1. `docs/spec/REBUILD_RFP_FINAL_SPEC_KR.md`
2. `docs/spec/REBUILD_FUNCTIONAL_SPEC_KR.md`
3. `docs/spec/REBUILD_UI_UX_SPEC_KR.md`
4. `docs/spec/REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md`
5. `docs/spec/REBUILD_OPERATIONS_SECURITY_SPEC_KR.md`
6. `docs/spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md`
7. `docs/spec/IMPLEMENTED_GAP_AND_REBUILD_SPEC_KR.md`
8. 본 패키지 전체

## 제한

이 패키지는 synthetic/in-memory 기준 보조 자료다. 실제 운영 데이터, secret, 기존 소스 코드, 운영 DB dump를 포함하지 않는다.
""",
    )


def run_server(port: int) -> None:
    from fastapi.staticfiles import StaticFiles
    import uvicorn

    from backend.api.app import app

    # Evidence-only root mount. Product code still serves the normal /app mount.
    app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend-root-evidence")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def export_assets() -> None:
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = _evidence_env()
    process = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "--server", "--port", str(port)],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    screenshot_results: list[dict[str, Any]] = []
    try:
        _wait_for_health(base_url, process)
        summary = _api_samples(base_url)

        chrome = _chrome_path()
        if chrome:
            try:
                screenshot_results.extend(_capture_screenshots_with_playwright(chrome, base_url))
            except Exception as exc:
                screenshot_results.append({"playwright_error": str(exc)})
                screenshot_targets = [
                    ("01_user_home.png", f"{base_url}/?mode=user"),
                    ("02_admin_project_status.png", f"{base_url}/?mode=admin"),
                    ("04_login_invite_preview.png", f"{base_url}/?invite_token=synthetic-preview-token"),
                ]
                for file_name, url in screenshot_targets:
                    screenshot_results.append(_capture_screenshot(chrome, url, OUTPUT_ROOT / "screenshots" / file_name))
        else:
            screenshot_results.append({"error": "Chrome or Edge executable not found"})

        _write_checklist()
        _write_flow_script()
        _write_readme(summary, screenshot_results)
        _write_json(OUTPUT_ROOT / "extraction-summary.json", {"api": summary, "screenshots": screenshot_results})
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", action="store_true")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    if args.server:
        run_server(args.port)
        return 0
    export_assets()
    print(f"exported {OUTPUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
