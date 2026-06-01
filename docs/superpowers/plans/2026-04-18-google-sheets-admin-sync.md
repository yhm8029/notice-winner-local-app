# Google Sheets Admin Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a cached Google Sheets sync path that reads one private spreadsheet, discovers visible sheets automatically, and renders them as read-only admin tabs inside SPMS.

**Architecture:** Keep Google Sheets as the edit source of truth and SPMS as the cached read-only viewer. Use backend REST calls to Google Sheets plus a persisted snapshot store, then expose admin-only API endpoints that the existing SPA can render through a new runtime helper. Keep `프로젝트 현황` fixed and represent dynamic sheet tabs through the existing `admin_tab` URL state instead of generating new static routes for every sheet.

**Tech Stack:** FastAPI, Pydantic, `requests`, Python file-backed cache/store, vanilla JS SPA, static HTML/CSS, Node frontend tests, pytest

---

## File Map

- Create: `backend/services/google_sheets_admin_backend.py`
  - Google Sheets config loading, title normalization, tab-key generation, matrix trimming, OAuth refresh, Google metadata/value fetch helpers
- Create: `backend/services/google_sheets_admin_store.py`
  - in-memory + file-backed snapshot store, stale checks, lazy-start background sync worker, manual sync trigger
- Modify: `backend/api/schemas.py`
  - admin Google Sheets response/request models
- Modify: `backend/api/app.py`
  - bridge helpers used by `admin.py`, admin auth checks, service wiring, optional lightweight response caching helpers
- Modify: `backend/api/routers/admin.py`
  - admin Google Sheets bootstrap, sheet payload, manual sync routes
- Create: `tests/test_google_sheets_admin_backend.py`
  - unit tests for config parsing, label normalization, matrix trimming, Google API payload shaping
- Create: `tests/test_google_sheets_admin_store.py`
  - snapshot persistence and background sync orchestration tests
- Modify: `tests/test_api_router_registration.py`
  - assert new admin routes belong to `backend.api.routers.admin`
- Modify: `tests/api/test_phase1_api.py`
  - API tests for bootstrap, sheet payload, manual sync, auth failure cases
- Create: `frontend/admin-google-sheets-runtime.js`
  - pure frontend helpers for tab metadata, status rendering, and HTML table rendering
- Modify: `frontend/index.html`
  - include new runtime asset and replace iframe-only admin embed area with status + table containers
- Modify: `frontend/styles.css`
  - styles for sync status chips, table wrapper, sticky headers, empty/error states
- Modify: `frontend/app.js`
  - dynamic admin tab resolution, `admin_tab` query support, bootstrap/payload loading, render integration, periodic refresh
- Modify: `frontend/vercel.json`
  - expose new runtime asset under `/app/admin-google-sheets-runtime.js`
- Create: `tests/frontend/test_admin_google_sheets_runtime.mjs`
  - unit tests for the new runtime helpers
- Modify: `tests/frontend/test_admin_tabs_app_integration.mjs`
  - assert query-based admin tab handling and runtime integration
- Modify: `tests/frontend/test_admin_routes_vercel_integration.mjs`
  - assert the new runtime asset rewrite exists

### URL Strategy

- Keep legacy admin path aliases such as `/app/design-list` and `/app/planned-orders` working as read aliases.
- Generate all new admin tab links as `/app/project-status?admin_tab=<tab-key>`.
- Use `project-status` as the fixed default tab key.
- Use `sheet-<gid>` for Google-backed dynamic tab keys so renaming a sheet does not break the selected tab key.

### Environment Variables

- `GOOGLE_SHEETS_ADMIN_SPREADSHEET_ID`
- `GOOGLE_SHEETS_ADMIN_CLIENT_ID`
- `GOOGLE_SHEETS_ADMIN_CLIENT_SECRET`
- `GOOGLE_SHEETS_ADMIN_REFRESH_TOKEN`
- `GOOGLE_SHEETS_ADMIN_SYNC_INTERVAL_SECONDS`
- `GOOGLE_SHEETS_ADMIN_SNAPSHOT_PATH`

If any required Google variable is missing, admin Google Sheets bootstrap should return `enabled=false` and no dynamic tabs instead of failing the whole admin console.

---

### Task 1: Build pure backend helpers for config, names, keys, and trimmed sheet payloads

**Files:**
- Create: `backend/services/google_sheets_admin_backend.py`
- Create: `tests/test_google_sheets_admin_backend.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from backend.services.google_sheets_admin_backend import (
    GoogleSheetsAdminConfig,
    build_google_sheet_admin_tab_key,
    load_google_sheets_admin_config,
    normalize_google_sheet_display_title,
    trim_google_sheet_values,
)


def test_normalize_google_sheet_display_title_applies_known_mappings():
    assert normalize_google_sheet_display_title("설계List") == "설계리스트"
    assert normalize_google_sheet_display_title("*발주예정*") == "발주예정"
    assert normalize_google_sheet_display_title("경상남도 영업List") == "경상남도 영업 리스트"


def test_build_google_sheet_admin_tab_key_uses_sheet_id():
    assert build_google_sheet_admin_tab_key(1664606955) == "sheet-1664606955"


def test_trim_google_sheet_values_uses_first_non_empty_row_as_headers():
    headers, rows = trim_google_sheet_values(
        [
            [],
            ["상태", "공사명", ""],
            ["영업진행", "부산광역시 도서관", ""],
            ["", "", ""],
        ]
    )

    assert headers == ["상태", "공사명"]
    assert rows == [["영업진행", "부산광역시 도서관"]]


def test_load_google_sheets_admin_config_returns_none_without_required_env(monkeypatch):
    for key in (
        "GOOGLE_SHEETS_ADMIN_SPREADSHEET_ID",
        "GOOGLE_SHEETS_ADMIN_CLIENT_ID",
        "GOOGLE_SHEETS_ADMIN_CLIENT_SECRET",
        "GOOGLE_SHEETS_ADMIN_REFRESH_TOKEN",
    ):
        monkeypatch.delenv(key, raising=False)

    assert load_google_sheets_admin_config() is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_google_sheets_admin_backend.py -q`
Expected: FAIL with `ModuleNotFoundError` or import failures because `google_sheets_admin_backend.py` does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```python
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GoogleSheetsAdminConfig:
    spreadsheet_id: str
    client_id: str
    client_secret: str
    refresh_token: str
    sync_interval_seconds: int
    snapshot_path: Path


_KNOWN_SHEET_DISPLAY_NAMES = {
    "설계list": "설계리스트",
    "발주예정": "발주예정",
    "lost": "LOST",
    "경상남도 영업list": "경상남도 영업 리스트",
    "대리점 리스트": "대리점 리스트",
}


def load_google_sheets_admin_config() -> GoogleSheetsAdminConfig | None:
    spreadsheet_id = str(os.getenv("GOOGLE_SHEETS_ADMIN_SPREADSHEET_ID") or "").strip()
    client_id = str(os.getenv("GOOGLE_SHEETS_ADMIN_CLIENT_ID") or "").strip()
    client_secret = str(os.getenv("GOOGLE_SHEETS_ADMIN_CLIENT_SECRET") or "").strip()
    refresh_token = str(os.getenv("GOOGLE_SHEETS_ADMIN_REFRESH_TOKEN") or "").strip()
    if not all((spreadsheet_id, client_id, client_secret, refresh_token)):
        return None
    raw_interval = str(os.getenv("GOOGLE_SHEETS_ADMIN_SYNC_INTERVAL_SECONDS") or "300").strip()
    sync_interval_seconds = max(300, min(600, int(raw_interval or "300")))
    raw_path = str(os.getenv("GOOGLE_SHEETS_ADMIN_SNAPSHOT_PATH") or "output/google_sheets_admin_snapshot.json").strip()
    return GoogleSheetsAdminConfig(
        spreadsheet_id=spreadsheet_id,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        sync_interval_seconds=sync_interval_seconds,
        snapshot_path=Path(raw_path),
    )


def normalize_google_sheet_display_title(raw_title: str) -> str:
    stripped = re.sub(r"^\*+|\*+$", "", str(raw_title or "").strip())
    collapsed = re.sub(r"\s+", " ", stripped)
    key = collapsed.lower()
    return _KNOWN_SHEET_DISPLAY_NAMES.get(key, collapsed)


def build_google_sheet_admin_tab_key(sheet_id: int | str) -> str:
    return f"sheet-{int(str(sheet_id).strip() or '0')}"


def trim_google_sheet_values(values: list[list[str]]) -> tuple[list[str], list[list[str]]]:
    normalized = [[str(cell or "").strip() for cell in row] for row in values]
    first_content_index = next((idx for idx, row in enumerate(normalized) if any(row)), None)
    if first_content_index is None:
        return [], []
    materialized = normalized[first_content_index:]
    max_width = max((max((idx for idx, cell in enumerate(row) if cell), default=-1) + 1 for row in materialized), default=0)
    trimmed = [row[:max_width] + [""] * max(0, max_width - len(row)) for row in materialized if any(row)]
    headers = trimmed[0] if trimmed else []
    rows = trimmed[1:] if len(trimmed) > 1 else []
    return headers, rows
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_google_sheets_admin_backend.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/google_sheets_admin_backend.py tests/test_google_sheets_admin_backend.py
git commit -m "feat: add google sheets admin helper primitives"
```

### Task 2: Add Google OAuth refresh, Google fetch helpers, and a persisted snapshot store

**Files:**
- Modify: `backend/services/google_sheets_admin_backend.py`
- Create: `backend/services/google_sheets_admin_store.py`
- Modify: `tests/test_google_sheets_admin_backend.py`
- Create: `tests/test_google_sheets_admin_store.py`

- [ ] **Step 1: Write the failing tests**

```python
from datetime import datetime, timezone

from backend.services.google_sheets_admin_store import (
    load_google_sheets_admin_snapshot,
    persist_google_sheets_admin_snapshot,
    sync_google_sheets_admin_snapshot_once,
)


def test_sync_google_sheets_admin_snapshot_once_builds_tabs_from_google_payload(tmp_path):
    from backend.services.google_sheets_admin_backend import GoogleSheetsAdminConfig

    config = GoogleSheetsAdminConfig(
        spreadsheet_id="spreadsheet-123",
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        sync_interval_seconds=300,
        snapshot_path=tmp_path / "google-sheets-admin.json",
    )

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload
            self.status_code = 200
            self.text = "ok"

        def json(self):
            return self._payload

        def raise_for_status(self):
            return None

    def fake_post(url, data, timeout):
        assert "oauth2.googleapis.com/token" in url
        return FakeResponse({"access_token": "access-token", "expires_in": 3600})

    def fake_get(url, headers=None, params=None, timeout=15):
        if url.endswith("/v4/spreadsheets/spreadsheet-123"):
            return FakeResponse(
                {
                    "properties": {"title": "@설계리스트"},
                    "sheets": [
                        {"properties": {"sheetId": 1664606955, "title": "설계List", "index": 0}},
                        {"properties": {"sheetId": 42, "title": "Hidden", "index": 1, "hidden": True}},
                    ],
                }
            )
        return FakeResponse({"values": [["상태", "공사명"], ["영업진행", "부산광역시 도서관"]]})

    snapshot = sync_google_sheets_admin_snapshot_once(
        config=config,
        request_post_fn=fake_post,
        request_get_fn=fake_get,
        now_fn=lambda: datetime(2026, 4, 18, tzinfo=timezone.utc),
    )

    assert snapshot["source_title"] == "@설계리스트"
    assert [tab["display_title"] for tab in snapshot["tabs"]] == ["설계리스트"]
    assert snapshot["sheets"]["sheet-1664606955"]["headers"] == ["상태", "공사명"]


def test_persist_google_sheets_admin_snapshot_round_trips(tmp_path):
    path = tmp_path / "snapshot.json"
    payload = {"version": 3, "tabs": [{"key": "sheet-1"}]}
    persist_google_sheets_admin_snapshot(path=path, snapshot=payload)
    assert load_google_sheets_admin_snapshot(path=path) == payload
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_google_sheets_admin_backend.py tests/test_google_sheets_admin_store.py -q`
Expected: FAIL because the sync/store functions do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```python
# backend/services/google_sheets_admin_backend.py
import requests


def refresh_google_sheets_admin_access_token(*, config: GoogleSheetsAdminConfig, request_post_fn=requests.post) -> str:
    response = request_post_fn(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "refresh_token": config.refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    return str(payload.get("access_token") or "").strip()


def fetch_google_sheets_admin_metadata(*, config: GoogleSheetsAdminConfig, access_token: str, request_get_fn=requests.get) -> dict:
    response = request_get_fn(
        f"https://sheets.googleapis.com/v4/spreadsheets/{config.spreadsheet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"fields": "properties(title),sheets(properties(sheetId,title,index,hidden))"},
        timeout=15,
    )
    response.raise_for_status()
    return dict(response.json() or {})


def fetch_google_sheet_values(*, config: GoogleSheetsAdminConfig, access_token: str, sheet_title: str, request_get_fn=requests.get) -> list[list[str]]:
    response = request_get_fn(
        f"https://sheets.googleapis.com/v4/spreadsheets/{config.spreadsheet_id}/values/{sheet_title}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"majorDimension": "ROWS", "valueRenderOption": "FORMATTED_VALUE"},
        timeout=15,
    )
    response.raise_for_status()
    return list(response.json().get("values") or [])
```

```python
# backend/services/google_sheets_admin_store.py
from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone

from backend.services.google_sheets_admin_backend import (
    build_google_sheet_admin_tab_key,
    fetch_google_sheet_values,
    fetch_google_sheets_admin_metadata,
    normalize_google_sheet_display_title,
    refresh_google_sheets_admin_access_token,
    trim_google_sheet_values,
)

_GOOGLE_SHEETS_ADMIN_STATE_LOCK = threading.Lock()
_GOOGLE_SHEETS_ADMIN_SNAPSHOT: dict | None = None
_GOOGLE_SHEETS_ADMIN_WORKER: threading.Thread | None = None
_GOOGLE_SHEETS_ADMIN_STOP = threading.Event()


def persist_google_sheets_admin_snapshot(*, path, snapshot: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")


def load_google_sheets_admin_snapshot(*, path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def sync_google_sheets_admin_snapshot_once(*, config, request_post_fn, request_get_fn, now_fn=datetime.now) -> dict:
    access_token = refresh_google_sheets_admin_access_token(config=config, request_post_fn=request_post_fn)
    metadata = fetch_google_sheets_admin_metadata(config=config, access_token=access_token, request_get_fn=request_get_fn)
    tabs = []
    sheets = {}
    for item in metadata.get("sheets") or []:
        props = dict(item.get("properties") or {})
        if props.get("hidden"):
            continue
        sheet_id = int(props.get("sheetId") or 0)
        raw_title = str(props.get("title") or "")
        key = build_google_sheet_admin_tab_key(sheet_id)
        headers, rows = trim_google_sheet_values(
            fetch_google_sheet_values(config=config, access_token=access_token, sheet_title=raw_title, request_get_fn=request_get_fn)
        )
        sheets[key] = {
            "sheet_id": sheet_id,
            "raw_title": raw_title,
            "display_title": normalize_google_sheet_display_title(raw_title),
            "headers": headers,
            "rows": rows,
            "row_count": len(rows),
            "column_count": len(headers),
        }
        tabs.append(
            {
                "key": key,
                "sheet_id": sheet_id,
                "raw_title": raw_title,
                "display_title": normalize_google_sheet_display_title(raw_title),
                "sheet_order": int(props.get("index") or 0),
            }
        )
    snapshot = {
        "enabled": True,
        "source_title": str((metadata.get("properties") or {}).get("title") or ""),
        "source_url": f"https://docs.google.com/spreadsheets/d/{config.spreadsheet_id}/edit",
        "sync_status": "ready",
        "last_successful_sync_at": now_fn(timezone.utc).isoformat(),
        "tabs": sorted(tabs, key=lambda item: item["sheet_order"]),
        "sheets": sheets,
    }
    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=snapshot)
    with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
        global _GOOGLE_SHEETS_ADMIN_SNAPSHOT
        _GOOGLE_SHEETS_ADMIN_SNAPSHOT = dict(snapshot)
    return snapshot


def read_google_sheets_admin_snapshot(*, config) -> dict | None:
    with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
        if _GOOGLE_SHEETS_ADMIN_SNAPSHOT is not None:
            return dict(_GOOGLE_SHEETS_ADMIN_SNAPSHOT)
    snapshot = load_google_sheets_admin_snapshot(path=config.snapshot_path)
    if snapshot is None:
        return None
    with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
        global _GOOGLE_SHEETS_ADMIN_SNAPSHOT
        _GOOGLE_SHEETS_ADMIN_SNAPSHOT = dict(snapshot)
    return dict(snapshot)


def queue_google_sheets_admin_sync_now(*, config) -> None:
    def _run() -> None:
        sync_google_sheets_admin_snapshot_once(config=config, request_post_fn=requests.post, request_get_fn=requests.get)

    worker = threading.Thread(target=_run, daemon=True)
    worker.start()


def ensure_google_sheets_admin_sync_worker_started(*, config) -> None:
    global _GOOGLE_SHEETS_ADMIN_WORKER
    with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
        if _GOOGLE_SHEETS_ADMIN_WORKER is not None and _GOOGLE_SHEETS_ADMIN_WORKER.is_alive():
            return

    def _loop() -> None:
        while not _GOOGLE_SHEETS_ADMIN_STOP.wait(config.sync_interval_seconds):
            sync_google_sheets_admin_snapshot_once(config=config, request_post_fn=requests.post, request_get_fn=requests.get)

    _GOOGLE_SHEETS_ADMIN_WORKER = threading.Thread(target=_loop, daemon=True)
    _GOOGLE_SHEETS_ADMIN_WORKER.start()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_google_sheets_admin_backend.py tests/test_google_sheets_admin_store.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/google_sheets_admin_backend.py backend/services/google_sheets_admin_store.py tests/test_google_sheets_admin_backend.py tests/test_google_sheets_admin_store.py
git commit -m "feat: add google sheets admin sync store"
```

### Task 3: Add admin API schemas and routes for bootstrap, sheet payload, and manual sync

**Files:**
- Modify: `backend/api/schemas.py`
- Modify: `backend/api/app.py`
- Modify: `backend/api/routers/admin.py`
- Modify: `tests/test_api_router_registration.py`
- Modify: `tests/api/test_phase1_api.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_admin_google_sheets_bootstrap_returns_dynamic_tabs(self) -> None:
    from backend.api import app as app_module

    actor = SalesActor(
        organization_id=uuid4(),
        user_id=uuid4(),
        email="admin@example.com",
        display_name="Admin",
        role="platform_admin",
    )
    snapshot = {
        "enabled": True,
        "source_title": "@설계리스트",
        "source_url": "https://docs.google.com/spreadsheets/d/spreadsheet-123/edit",
        "sync_status": "ready",
        "last_successful_sync_at": "2026-04-18T00:00:00+00:00",
        "tabs": [
            {
                "key": "sheet-1664606955",
                "sheet_id": 1664606955,
                "raw_title": "설계List",
                "display_title": "설계리스트",
                "sheet_order": 0,
            }
        ],
        "sheets": {
            "sheet-1664606955": {
                "sheet_id": 1664606955,
                "raw_title": "설계List",
                "display_title": "설계리스트",
                "headers": ["상태", "공사명"],
                "rows": [["영업진행", "부산광역시 도서관"]],
                "row_count": 1,
                "column_count": 2,
            }
        },
    }

    with (
        patch.object(app_module, "_resolve_sales_actor", return_value=actor),
        patch.object(app_module, "load_google_sheets_admin_config", return_value=object()),
        patch.object(app_module, "ensure_google_sheets_admin_sync_worker_started", return_value=None),
        patch.object(app_module, "read_google_sheets_admin_snapshot", return_value=snapshot),
        TestClient(app_module.app) as client,
    ):
        response = client.get("/api/admin/google-sheets/bootstrap")

    assert response.status_code == 200
    payload = response.json()
    assert payload["tabs"][0]["display_title"] == "설계리스트"


def test_admin_google_sheet_payload_returns_rows(self) -> None:
    from backend.api import app as app_module

    actor = SalesActor(
        organization_id=uuid4(),
        user_id=uuid4(),
        email="admin@example.com",
        display_name="Admin",
        role="platform_admin",
    )
    snapshot = {
        "enabled": True,
        "sync_status": "ready",
        "last_successful_sync_at": "2026-04-18T00:00:00+00:00",
        "tabs": [],
        "sheets": {
            "sheet-1664606955": {
                "sheet_id": 1664606955,
                "raw_title": "설계List",
                "display_title": "설계리스트",
                "headers": ["상태", "공사명"],
                "rows": [["영업진행", "부산광역시 도서관"]],
                "row_count": 1,
                "column_count": 2,
            }
        },
    }

    with (
        patch.object(app_module, "_resolve_sales_actor", return_value=actor),
        patch.object(app_module, "load_google_sheets_admin_config", return_value=object()),
        patch.object(app_module, "read_google_sheets_admin_snapshot", return_value=snapshot),
        TestClient(app_module.app) as client,
    ):
        response = client.get("/api/admin/google-sheets/sheets/sheet-1664606955")

    assert response.status_code == 200
    payload = response.json()
    assert payload["headers"] == ["상태", "공사명"]
    assert payload["rows"][0][1] == "부산광역시 도서관"


def test_admin_google_sheets_sync_rejects_non_admin(self) -> None:
    from backend.api import app as app_module

    actor = SalesActor(
        organization_id=uuid4(),
        user_id=uuid4(),
        email="member@example.com",
        display_name="Member",
        role="org_member",
    )

    with (
        patch.object(app_module, "_resolve_sales_actor", return_value=actor),
        TestClient(app_module.app) as client,
    ):
        response = client.post("/api/admin/google-sheets/sync")

    assert response.status_code == 403
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_api_router_registration.py tests/api/test_phase1_api.py -k "google_sheets or admin_router_owns_admin_paths" -q`
Expected: FAIL because the schemas and routes do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```python
# backend/api/schemas.py
class AdminGoogleSheetTabItem(BaseModel):
    key: str
    sheet_id: int
    raw_title: str = ""
    display_title: str = ""
    sheet_order: int = 0
    row_count: int = 0
    column_count: int = 0


class AdminGoogleSheetsBootstrapResponse(BaseModel):
    enabled: bool = False
    source_title: str = ""
    source_url: str = ""
    sync_status: str = "not_configured"
    last_successful_sync_at: datetime | None = None
    last_failed_sync_at: datetime | None = None
    last_error: str = ""
    tabs: list[AdminGoogleSheetTabItem] = Field(default_factory=list)


class AdminGoogleSheetPayloadResponse(BaseModel):
    key: str
    sheet_id: int
    raw_title: str = ""
    display_title: str = ""
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    row_count: int = 0
    column_count: int = 0
    synced_at: datetime | None = None


class AdminGoogleSheetsSyncResponse(BaseModel):
    started: bool = False
    sync_status: str = ""
    message: str = ""
```

```python
# backend/api/app.py
from backend.services.google_sheets_admin_backend import load_google_sheets_admin_config
from backend.services.google_sheets_admin_store import (
    ensure_google_sheets_admin_sync_worker_started,
    queue_google_sheets_admin_sync_now,
    read_google_sheets_admin_snapshot,
)


def get_admin_google_sheets_bootstrap(request: Request) -> AdminGoogleSheetsBootstrapResponse:
    actor = _resolve_sales_actor(request)
    if not actor.is_admin:
        raise ApiError(status_code=403, code="auth_forbidden", message="관리자만 구글 시트 현황을 볼 수 있습니다.")
    config = load_google_sheets_admin_config()
    if config is None:
        return AdminGoogleSheetsBootstrapResponse(enabled=False)
    ensure_google_sheets_admin_sync_worker_started(config=config)
    snapshot = read_google_sheets_admin_snapshot(config=config) or {}
    return AdminGoogleSheetsBootstrapResponse.model_validate(
        {
            "enabled": True,
            "source_title": snapshot.get("source_title", ""),
            "source_url": snapshot.get("source_url", ""),
            "sync_status": snapshot.get("sync_status", "loading"),
            "last_successful_sync_at": snapshot.get("last_successful_sync_at"),
            "last_failed_sync_at": snapshot.get("last_failed_sync_at"),
            "last_error": snapshot.get("last_error", ""),
            "tabs": [
                {
                    **tab,
                    "row_count": int((snapshot.get("sheets") or {}).get(tab["key"], {}).get("row_count") or 0),
                    "column_count": int((snapshot.get("sheets") or {}).get(tab["key"], {}).get("column_count") or 0),
                }
                for tab in list(snapshot.get("tabs") or [])
            ],
        }
    )


def get_admin_google_sheet_payload(request: Request, sheet_key: str) -> AdminGoogleSheetPayloadResponse:
    actor = _resolve_sales_actor(request)
    if not actor.is_admin:
        raise ApiError(status_code=403, code="auth_forbidden", message="관리자만 구글 시트 현황을 볼 수 있습니다.")
    config = load_google_sheets_admin_config()
    if config is None:
        raise ApiError(status_code=404, code="google_sheets_not_configured", message="구글 시트 연동이 설정되지 않았습니다.")
    snapshot = read_google_sheets_admin_snapshot(config=config) or {}
    sheet = dict((snapshot.get("sheets") or {}).get(sheet_key) or {})
    if not sheet:
        raise ApiError(status_code=404, code="google_sheet_not_found", message="선택한 시트 탭을 찾을 수 없습니다.")
    return AdminGoogleSheetPayloadResponse.model_validate({**sheet, "key": sheet_key, "synced_at": snapshot.get("last_successful_sync_at")})


def post_admin_google_sheets_sync(request: Request) -> AdminGoogleSheetsSyncResponse:
    actor = _resolve_sales_actor(request)
    if not actor.is_admin:
        raise ApiError(status_code=403, code="auth_forbidden", message="관리자만 구글 시트 동기화를 실행할 수 있습니다.")
    config = load_google_sheets_admin_config()
    if config is None:
        return AdminGoogleSheetsSyncResponse(started=False, sync_status="not_configured", message="Google Sheets config missing")
    queue_google_sheets_admin_sync_now(config=config)
    return AdminGoogleSheetsSyncResponse(started=True, sync_status="queued", message="Google Sheets sync queued")
```

```python
# backend/api/routers/admin.py
@router.get("/api/admin/google-sheets/bootstrap", response_model=AdminGoogleSheetsBootstrapResponse)
def get_admin_google_sheets_bootstrap_route(request: Request) -> AdminGoogleSheetsBootstrapResponse:
    admin_app = _app_module()
    return admin_app.get_admin_google_sheets_bootstrap(request)


@router.get("/api/admin/google-sheets/sheets/{sheet_key}", response_model=AdminGoogleSheetPayloadResponse)
def get_admin_google_sheet_payload_route(request: Request, sheet_key: str) -> AdminGoogleSheetPayloadResponse:
    admin_app = _app_module()
    return admin_app.get_admin_google_sheet_payload(request, sheet_key)


@router.post("/api/admin/google-sheets/sync", response_model=AdminGoogleSheetsSyncResponse)
def post_admin_google_sheets_sync_route(request: Request) -> AdminGoogleSheetsSyncResponse:
    admin_app = _app_module()
    return admin_app.post_admin_google_sheets_sync(request)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_api_router_registration.py tests/api/test_phase1_api.py -k "google_sheets or admin_router_owns_admin_paths" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/schemas.py backend/api/app.py backend/api/routers/admin.py tests/test_api_router_registration.py tests/api/test_phase1_api.py
git commit -m "feat: add admin google sheets api routes"
```

### Task 4: Add a pure frontend runtime for dynamic sheet tabs, status, and table markup

**Files:**
- Create: `frontend/admin-google-sheets-runtime.js`
- Create: `tests/frontend/test_admin_google_sheets_runtime.mjs`

- [ ] **Step 1: Write the failing tests**

```javascript
test("buildAdminGoogleSheetTabs normalizes bootstrap tabs and keeps order", () => {
  const runtime = loadRuntime();
  const tabs = runtime.buildAdminGoogleSheetTabs({
    tabs: [
      { key: "sheet-1664606955", display_title: "설계리스트", raw_title: "설계List", sheet_id: 1664606955, sheet_order: 0 },
      { key: "sheet-2", display_title: "발주예정", raw_title: "*발주예정*", sheet_id: 2, sheet_order: 1 },
    ],
  });

  assert.equal(tabs[0].key, "sheet-1664606955");
  assert.equal(tabs[1].label, "발주예정");
});


test("buildAdminGoogleSheetTableView renders table markup from headers and rows", () => {
  const runtime = loadRuntime();
  const view = runtime.buildAdminGoogleSheetTableView(
    {
      headers: ["상태", "공사명"],
      rows: [["영업진행", "부산광역시 도서관"]],
    },
    { escapeHtml: (value) => String(value) },
  );

  assert.match(view.html, /<table/);
  assert.match(view.html, /부산광역시 도서관/);
});


test("isAdminGoogleSheetTabKey recognizes sheet-prefixed keys", () => {
  const runtime = loadRuntime();
  assert.equal(runtime.isAdminGoogleSheetTabKey("sheet-1664606955"), true);
  assert.equal(runtime.isAdminGoogleSheetTabKey("project-status"), false);
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `node --test tests/frontend/test_admin_google_sheets_runtime.mjs`
Expected: FAIL because the runtime file does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```javascript
(function attachAdminGoogleSheetsRuntime(global) {
  function isAdminGoogleSheetTabKey(value) {
    return /^sheet-\d+$/.test(String(value || "").trim());
  }

  function buildAdminGoogleSheetTabs(bootstrap) {
    return (Array.isArray(bootstrap?.tabs) ? bootstrap.tabs : [])
      .slice()
      .sort((left, right) => Number(left.sheet_order || 0) - Number(right.sheet_order || 0))
      .map((tab) => ({
        key: String(tab.key || ""),
        label: String(tab.display_title || tab.raw_title || ""),
        rawTitle: String(tab.raw_title || ""),
        sheetId: Number(tab.sheet_id || 0),
      }));
  }

  function buildAdminGoogleSheetStatusView(bootstrap, activeSheet) {
    const status = String(bootstrap?.sync_status || "loading");
    const syncedAt = String(bootstrap?.last_successful_sync_at || "");
    return {
      html: `
        <div class="admin-google-sheet-status-row">
          <span class="admin-google-sheet-status-chip status-${status}">${status}</span>
          <span class="mono">${syncedAt}</span>
          <span>${String(activeSheet?.label || "")}</span>
        </div>
      `,
    };
  }

  function buildAdminGoogleSheetTableView(payload, { escapeHtml }) {
    const headers = Array.isArray(payload?.headers) ? payload.headers : [];
    const rows = Array.isArray(payload?.rows) ? payload.rows : [];
    const headerHtml = headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("");
    const bodyHtml = rows.map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`).join("");
    return {
      html: `
        <div class="admin-google-sheet-table-wrap">
          <table class="admin-google-sheet-table">
            <thead><tr>${headerHtml}</tr></thead>
            <tbody>${bodyHtml}</tbody>
          </table>
        </div>
      `,
    };
  }

  global.SPMSAdminGoogleSheetsRuntime = {
    isAdminGoogleSheetTabKey,
    buildAdminGoogleSheetTabs,
    buildAdminGoogleSheetStatusView,
    buildAdminGoogleSheetTableView,
  };
})(window);
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `node --test tests/frontend/test_admin_google_sheets_runtime.mjs`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/admin-google-sheets-runtime.js tests/frontend/test_admin_google_sheets_runtime.mjs
git commit -m "feat: add admin google sheets runtime helpers"
```

### Task 5: Integrate dynamic admin tabs, query-based selection, and read-only table rendering in the SPA

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/styles.css`
- Modify: `frontend/app.js`
- Modify: `frontend/vercel.json`
- Modify: `tests/frontend/test_admin_tabs_app_integration.mjs`
- Modify: `tests/frontend/test_admin_routes_vercel_integration.mjs`

- [ ] **Step 1: Write the failing tests**

```javascript
test("admin tab state is query-backed and dynamic tabs come from bootstrap payload", () => {
  const source = readAppSource();
  assert.match(source, /params\.get\("admin_tab"\)/);
  assert.match(source, /params\.set\("admin_tab"/);
  assert.match(source, /loadAdminGoogleSheetsBootstrap/);
  assert.match(source, /loadAdminGoogleSheetPayload/);
  assert.match(source, /SPMSAdminGoogleSheetsRuntime/);
});


test("admin sheet panel markup exists in the frontend document", () => {
  const source = readHtmlSource();
  assert.match(source, /id="admin-google-sheet-status"/);
  assert.match(source, /id="admin-google-sheet-table"/);
  assert.doesNotMatch(source, /id="admin-embed-frame"/);
});


test("vercel rewrites expose the admin google sheets runtime asset", () => {
  const config = readVercelConfig();
  const sources = (Array.isArray(config.rewrites) ? config.rewrites : []).map((entry) => entry.source);
  assert.ok(sources.includes("/app/admin-google-sheets-runtime.js"));
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `node --test tests/frontend/test_admin_tabs_app_integration.mjs tests/frontend/test_admin_routes_vercel_integration.mjs`
Expected: FAIL because query-backed dynamic admin tabs and the new runtime asset are not wired in yet.

- [ ] **Step 3: Write the minimal implementation**

Extend the existing `hydrateStateFromUrl()` and `buildUrlForState()` functions instead of deleting unrelated run/tracker/report URL logic. The diff should append the `admin_tab` behavior shown below while preserving the rest of the current parameter handling.

```html
<!-- frontend/index.html -->
<script defer src="/app/admin-google-sheets-runtime.js?v=20260418a"></script>

<section id="admin-embed-panel" class="panel panel-admin-embed hidden">
  <div class="panel-heading">
    <div>
      <p class="kicker">Admin</p>
      <h2 id="admin-embed-title">-</h2>
    </div>
  </div>
  <p id="admin-embed-subtitle" class="hero-subcopy"></p>
  <div id="admin-google-sheet-status" class="admin-google-sheet-status"></div>
  <div id="admin-google-sheet-table" class="admin-google-sheet-table-panel"></div>
  <div id="admin-embed-empty" class="empty-state hidden"></div>
</section>
```

```javascript
// frontend/app.js
const ADMIN_GOOGLE_SHEETS_RUNTIME = window.SPMSAdminGoogleSheetsRuntime || null;
const DEFAULT_ADMIN_TAB = "project-status";

const STATIC_ADMIN_TABS = [
  { key: DEFAULT_ADMIN_TAB, label: "프로젝트 현황", routePath: "/app/project-status", type: "existing" },
];

state.adminTab = DEFAULT_ADMIN_TAB;
state.adminRequestedTab = DEFAULT_ADMIN_TAB;
state.adminGoogleSheetsBootstrap = null;
state.adminGoogleSheetTabs = [];
state.adminGoogleSheetPayloads = {};
dom.adminGoogleSheetStatus = document.querySelector("#admin-google-sheet-status");
dom.adminGoogleSheetTable = document.querySelector("#admin-google-sheet-table");

function getResolvedAdminTabs() {
  return STATIC_ADMIN_TABS.concat(state.adminGoogleSheetTabs);
}

function getActiveAdminTab() {
  return getResolvedAdminTabs().find((item) => item.key === state.adminTab) || STATIC_ADMIN_TABS[0];
}

function renderAdminTopNavigation() {
  if (!dom.adminTopNavList) return;
  dom.adminTopNavList.innerHTML = getResolvedAdminTabs().map((item) => `
    <a
      class="admin-top-nav-button${item.key === state.adminTab ? " is-active" : ""}"
      href="${escapeHtml(buildUrlForState({ pathname: "/app/project-status", uiMode: "admin", adminTab: item.key }))}"
      data-admin-tab="${item.key}"
    >${escapeHtml(item.label)}</a>
  `).join("");
}

function normalizeAdminTab(rawValue) {
  const candidate = String(rawValue || "").trim();
  return getResolvedAdminTabs().some((item) => item.key === candidate) ? candidate : DEFAULT_ADMIN_TAB;
}

function hydrateStateFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const routeTab = getAdminTabByPathname(window.location.pathname);
  state.adminRequestedTab = String(params.get("admin_tab") || routeTab?.key || DEFAULT_ADMIN_TAB).trim() || DEFAULT_ADMIN_TAB;
  state.adminTab = DEFAULT_ADMIN_TAB;
}

function buildUrlForState({ pathname = null, uiMode = state.uiMode, adminTab = state.adminTab } = {}) {
  const params = new URLSearchParams();
  if (uiMode === "admin" && adminTab && adminTab !== DEFAULT_ADMIN_TAB) {
    params.set("admin_tab", adminTab);
  }
  const nextPath = pathname || (uiMode === "admin" ? "/app/project-status" : resolveStatePathname());
  const next = params.toString();
  return `${nextPath}${next ? `?${next}` : ""}`;
}

async function loadAdminGoogleSheetsBootstrap({ silent = false } = {}) {
  const payload = await api("/api/admin/google-sheets/bootstrap", { timeoutMs: 15000, cacheBust: false });
  state.adminGoogleSheetsBootstrap = payload || null;
  state.adminGoogleSheetTabs = (ADMIN_GOOGLE_SHEETS_RUNTIME?.buildAdminGoogleSheetTabs(payload) || []).map((tab) => ({
    ...tab,
    routePath: "/app/project-status",
    type: "google_sheet",
  }));
  state.adminTab = normalizeAdminTab(state.adminRequestedTab);
  renderAdminTopNavigation();
  renderAdminEmbedPanel();
}

async function loadAdminGoogleSheetPayload(tabKey, { silent = false } = {}) {
  if (!ADMIN_GOOGLE_SHEETS_RUNTIME?.isAdminGoogleSheetTabKey(tabKey)) return null;
  const payload = await api(`/api/admin/google-sheets/sheets/${encodeURIComponent(tabKey)}`, { timeoutMs: 15000, cacheBust: false });
  state.adminGoogleSheetPayloads[tabKey] = payload || null;
  renderAdminEmbedPanel();
  return payload;
}

function renderAdminEmbedPanel() {
  const activeTab = getActiveAdminTab();
  const isGoogleSheetTab = ADMIN_GOOGLE_SHEETS_RUNTIME?.isAdminGoogleSheetTabKey(activeTab.key);
  if (!isGoogleSheetTab) {
    dom.adminEmbedPanel.classList.add("hidden");
    return;
  }
  dom.adminEmbedPanel.classList.remove("hidden");
  const payload = state.adminGoogleSheetPayloads[activeTab.key] || null;
  dom.adminGoogleSheetStatus.innerHTML = ADMIN_GOOGLE_SHEETS_RUNTIME.buildAdminGoogleSheetStatusView(state.adminGoogleSheetsBootstrap, activeTab).html;
  dom.adminGoogleSheetTable.innerHTML = payload
    ? ADMIN_GOOGLE_SHEETS_RUNTIME.buildAdminGoogleSheetTableView(payload, { escapeHtml }).html
    : '<div class="empty-state">시트 데이터를 불러오는 중입니다.</div>';
}
```

```css
.admin-google-sheet-status-row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 14px; }
.admin-google-sheet-status-chip { border-radius: 999px; padding: 6px 10px; font-size: 12px; text-transform: uppercase; }
.admin-google-sheet-table-wrap { overflow: auto; border: 1px solid rgba(33, 24, 19, 0.12); border-radius: 18px; background: rgba(255,255,255,0.76); }
.admin-google-sheet-table { width: 100%; border-collapse: separate; border-spacing: 0; min-width: 960px; }
.admin-google-sheet-table thead th { position: sticky; top: 0; background: #f6eadf; z-index: 1; }
.admin-google-sheet-table th, .admin-google-sheet-table td { padding: 10px 12px; border-bottom: 1px solid rgba(33, 24, 19, 0.08); text-align: left; vertical-align: top; }
```

```json
{
  "source": "/app/admin-google-sheets-runtime.js",
  "destination": "/admin-google-sheets-runtime.js"
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `node --test tests/frontend/test_admin_google_sheets_runtime.mjs tests/frontend/test_admin_tabs_app_integration.mjs tests/frontend/test_admin_routes_vercel_integration.mjs`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html frontend/styles.css frontend/app.js frontend/vercel.json frontend/admin-google-sheets-runtime.js tests/frontend/test_admin_google_sheets_runtime.mjs tests/frontend/test_admin_tabs_app_integration.mjs tests/frontend/test_admin_routes_vercel_integration.mjs
git commit -m "feat: render admin google sheets tabs in spa"
```

### Task 6: Run focused backend and frontend verification before feature work continues

**Files:**
- No new files

- [ ] **Step 1: Run backend unit and API tests**

Run:

```bash
pytest tests/test_google_sheets_admin_backend.py tests/test_google_sheets_admin_store.py tests/test_api_router_registration.py tests/api/test_phase1_api.py -k "google_sheets or admin_router_owns_admin_paths" -q
```

Expected: PASS for the new Google Sheets coverage and router ownership assertions.

- [ ] **Step 2: Run frontend runtime and integration tests**

Run:

```bash
node --test tests/frontend/test_admin_google_sheets_runtime.mjs tests/frontend/test_admin_tabs_app_integration.mjs tests/frontend/test_admin_routes_vercel_integration.mjs
```

Expected: PASS

- [ ] **Step 3: Run the previously repaired baseline smoke**

Run:

```bash
pytest tests/test_api_router_registration.py -q
node --test tests/frontend/test_admin_routes_vercel_integration.mjs
```

Expected: PASS

- [ ] **Step 4: Inspect git status before implementation handoff**

Run:

```bash
git status --short
```

Expected: clean working tree with only the intended Google Sheets feature commits on `feature/google-sheets-admin-sync`.

- [ ] **Step 5: Push the branch**

```bash
git push -u origin feature/google-sheets-admin-sync
```

---

## Notes For The Implementer

- Keep Google auth read-only. Do not request write scopes.
- Do not expose refresh tokens or raw Google credential errors to the browser.
- Use `sheet-<gid>` tab keys. Do not key dynamic tabs by sheet title.
- Preserve legacy admin path aliases as read aliases only. Generate new top-nav links with the `admin_tab` query parameter on `/app/project-status`.
- If the first admin bootstrap call happens before a snapshot exists, return `enabled=true`, `sync_status=loading`, and `tabs=[]`, then let the background worker fill the snapshot.
- If Google refresh fails after one successful sync, keep the last snapshot and surface the error in bootstrap metadata instead of clearing the tabs.
