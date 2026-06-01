# Google Sheets Admin Snapshot Read Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce admin Google Sheets timeout risk by removing full-file hashing from stable snapshot reads and by adding low-noise timing logs for snapshot and route latency.

**Architecture:** Keep the existing admin Google Sheets endpoints and snapshot schema, but change the snapshot cache fast path from `mtime + size + digest` to `mtime + size`. Add a shared performance logging helper in `backend/perf_runtime.py`, then wire that helper into the snapshot store and admin routes so slow or failed reads leave actionable evidence without noisy default logs.

**Tech Stack:** Python, FastAPI, pytest, unittest.mock, existing `perf.*` logging runtime

---

## File Map

- Modify: `backend/perf_runtime.py`
  - Add the dedicated `perf.google_sheets_admin` logger and a reusable duration logging helper with debug gating.
- Modify: `backend/services/google_sheets_admin_store.py`
  - Replace digest-based snapshot file-state checks with cheap `stat()`-based validation and emit snapshot read timing logs.
- Modify: `backend/api/routers/admin.py`
  - Add route-level timing logs for bootstrap and sheet payload responses.
- Modify: `tests/test_perf_runtime.py`
  - Cover the new duration logging helper behavior.
- Modify: `tests/test_google_sheets_admin_store.py`
  - Add regression coverage for the no-hash fast path, same-size mutation detection, and snapshot timing log calls.
- Modify: `tests/api/test_phase1_api.py`
  - Verify the admin Google Sheets routes still behave the same while emitting timing helper calls.

### Task 1: Add a shared Google Sheets performance logging helper

**Files:**
- Modify: `backend/perf_runtime.py`
- Modify: `tests/test_perf_runtime.py`
- Test: `tests/test_perf_runtime.py`

- [ ] **Step 1: Write the failing perf helper tests**

```python
from backend.perf_runtime import log_google_sheets_admin_duration


class TestGoogleSheetsAdminPerfLogging:
    def test_logs_warning_for_slow_google_sheets_event(self) -> None:
        with patch("backend.perf_runtime.GOOGLE_SHEETS_ADMIN_PERF_LOGGER.warning") as warning_mock, patch(
            "backend.perf_runtime.GOOGLE_SHEETS_ADMIN_PERF_LOGGER.info"
        ) as info_mock:
            log_google_sheets_admin_duration(
                event="snapshot_read",
                duration=0.75,
                slow_threshold=0.25,
                debug_enabled=False,
                cache_hit=False,
                path="snapshot.json",
            )

        warning_mock.assert_called_once()
        info_mock.assert_not_called()

    def test_logs_info_for_fast_google_sheets_event_when_debug_enabled(self) -> None:
        with patch("backend.perf_runtime.GOOGLE_SHEETS_ADMIN_PERF_LOGGER.warning") as warning_mock, patch(
            "backend.perf_runtime.GOOGLE_SHEETS_ADMIN_PERF_LOGGER.info"
        ) as info_mock:
            log_google_sheets_admin_duration(
                event="snapshot_read",
                duration=0.05,
                slow_threshold=0.25,
                debug_enabled=True,
                cache_hit=True,
                path="snapshot.json",
            )

        info_mock.assert_called_once()
        warning_mock.assert_not_called()

    def test_skips_fast_google_sheets_event_when_debug_disabled(self) -> None:
        with patch("backend.perf_runtime.GOOGLE_SHEETS_ADMIN_PERF_LOGGER.warning") as warning_mock, patch(
            "backend.perf_runtime.GOOGLE_SHEETS_ADMIN_PERF_LOGGER.info"
        ) as info_mock:
            log_google_sheets_admin_duration(
                event="snapshot_read",
                duration=0.05,
                slow_threshold=0.25,
                debug_enabled=False,
                cache_hit=True,
                path="snapshot.json",
            )

        info_mock.assert_not_called()
        warning_mock.assert_not_called()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_perf_runtime.py -k google_sheets_admin -q`
Expected: FAIL with `ImportError` or `AttributeError` because `log_google_sheets_admin_duration` and `GOOGLE_SHEETS_ADMIN_PERF_LOGGER` do not exist yet

- [ ] **Step 3: Write the minimal perf helper implementation**

```python
GOOGLE_SHEETS_ADMIN_PERF_LOGGER = logging.getLogger("perf.google_sheets_admin")
SLOW_GOOGLE_SHEETS_ADMIN_SEC = _env_float("PERF_GOOGLE_SHEETS_ADMIN_SLOW_SEC", 0.25)


def _env_flag(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, "")).strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def log_google_sheets_admin_duration(
    *,
    event: str,
    duration: float,
    slow_threshold: float | None = None,
    debug_enabled: bool | None = None,
    **meta: Any,
) -> None:
    threshold = SLOW_GOOGLE_SHEETS_ADMIN_SEC if slow_threshold is None else float(slow_threshold)
    debug = _env_flag("GOOGLE_SHEETS_ADMIN_DEBUG_TIMING") if debug_enabled is None else bool(debug_enabled)
    if duration >= threshold:
        GOOGLE_SHEETS_ADMIN_PERF_LOGGER.warning(
            "GOOGLE_SHEETS_ADMIN_%s duration=%.3f meta=%s",
            str(event or "").upper(),
            duration,
            meta,
        )
        return
    if debug:
        GOOGLE_SHEETS_ADMIN_PERF_LOGGER.info(
            "GOOGLE_SHEETS_ADMIN_%s duration=%.3f meta=%s",
            str(event or "").upper(),
            duration,
            meta,
        )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_perf_runtime.py -k google_sheets_admin -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/perf_runtime.py tests/test_perf_runtime.py
git commit -m "feat: add google sheets perf logging helper"
```

### Task 2: Remove full-file hashing from stable snapshot reads and log snapshot timing

**Files:**
- Modify: `backend/services/google_sheets_admin_store.py`
- Modify: `tests/test_google_sheets_admin_store.py`
- Test: `tests/test_google_sheets_admin_store.py`

- [ ] **Step 1: Write the failing snapshot fast-path tests**

```python
def test_read_google_sheets_admin_snapshot_skips_full_file_scan_when_file_state_is_unchanged(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)
    payload = {"tabs": [{"key": "sheet-1"}], "marker": "stable"}
    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=payload)

    assert store.read_google_sheets_admin_snapshot(config=config) == payload

    def forbid_read_bytes(self):
        raise AssertionError("read_bytes should not run for unchanged snapshot state")

    monkeypatch.setattr(Path, "read_bytes", forbid_read_bytes)

    assert store.read_google_sheets_admin_snapshot(config=config) == payload


def test_read_google_sheets_admin_snapshot_reloads_when_file_mtime_changes_even_if_size_matches(
    tmp_path
):
    config = build_config(tmp_path)
    first_payload = {"tabs": [{"key": "sheet-1"}], "marker": "aaaaa"}
    second_payload = {"tabs": [{"key": "sheet-1"}], "marker": "bbbbb"}

    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=first_payload)
    assert store.read_google_sheets_admin_snapshot(config=config) == first_payload

    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=second_payload)

    assert store.read_google_sheets_admin_snapshot(config=config) == second_payload


def test_read_google_sheets_admin_snapshot_reports_cache_hit_timing(tmp_path, monkeypatch):
    config = build_config(tmp_path)
    payload = {"tabs": [{"key": "sheet-1"}], "marker": "stable"}
    events = []

    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=payload)
    assert store.read_google_sheets_admin_snapshot(config=config) == payload

    monkeypatch.setattr(
        store,
        "log_google_sheets_admin_duration",
        lambda **kwargs: events.append(kwargs),
    )

    assert store.read_google_sheets_admin_snapshot(config=config) == payload
    assert events[-1]["event"] == "snapshot_read"
    assert events[-1]["cache_hit"] is True
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_google_sheets_admin_store.py -k "skips_full_file_scan or mtime_changes_even_if_size_matches or reports_cache_hit_timing" -q`
Expected:
- FAIL because `_google_sheets_admin_snapshot_file_state` still calls `Path.read_bytes()`
- FAIL because the store does not call `log_google_sheets_admin_duration`

- [ ] **Step 3: Write the minimal snapshot fast-path implementation**

```python
from backend.perf_runtime import log_google_sheets_admin_duration


def _google_sheets_admin_snapshot_file_state(*, path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return (stat.st_mtime_ns, stat.st_size)


def read_google_sheets_admin_snapshot(*, config) -> dict | None:
    started = time.perf_counter()
    state_key = _google_sheets_admin_state_key(config=config)
    snapshot_path = _google_sheets_admin_snapshot_path(config=config)
    current_file_state = _google_sheets_admin_snapshot_file_state(path=snapshot_path)
    with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
        cached = _GOOGLE_SHEETS_ADMIN_SNAPSHOTS.get(state_key)
        cached_file_state = _GOOGLE_SHEETS_ADMIN_SNAPSHOT_FILE_STATE.get(state_key)
        if cached is not None and current_file_state is not None and cached_file_state == current_file_state:
            duration = time.perf_counter() - started
            log_google_sheets_admin_duration(
                event="snapshot_read",
                duration=duration,
                cache_hit=True,
                path=str(snapshot_path),
                file_missing=False,
                mtime_ns=current_file_state[0],
                size=current_file_state[1],
            )
            return copy.deepcopy(cached)
    try:
        reload_started = time.perf_counter()
        snapshot, _ = _load_google_sheets_admin_snapshot_and_state(config=config)
        reload_duration = time.perf_counter() - reload_started
    except OSError as error:
        duration = time.perf_counter() - started
        log_google_sheets_admin_duration(
            event="snapshot_read",
            duration=duration,
            cache_hit=False,
            path=str(snapshot_path),
            file_missing=current_file_state is None,
            error=str(error),
        )
        return _copy_google_sheets_admin_cached_snapshot(state_key=state_key)
    duration = time.perf_counter() - started
    log_google_sheets_admin_duration(
        event="snapshot_read",
        duration=duration,
        cache_hit=False,
        path=str(snapshot_path),
        file_missing=current_file_state is None,
        load_duration=reload_duration,
    )
    return copy.deepcopy(snapshot) if snapshot is not None else None
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_google_sheets_admin_store.py -k "skips_full_file_scan or mtime_changes_even_if_size_matches or reports_cache_hit_timing" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/google_sheets_admin_store.py tests/test_google_sheets_admin_store.py
git commit -m "fix: speed up google sheets snapshot reads"
```

### Task 3: Add admin route timing instrumentation without changing responses

**Files:**
- Modify: `backend/api/routers/admin.py`
- Modify: `tests/api/test_phase1_api.py`
- Test: `tests/api/test_phase1_api.py`

- [ ] **Step 1: Write the failing admin route timing tests**

```python
    def test_admin_google_sheets_bootstrap_reports_route_timing(self) -> None:
        from backend.api import app as app_module

        actor = SalesActor(
            organization_id=DEFAULT_PHASE1_ORGANIZATION_ID,
            user_id=DEFAULT_PHASE1_INTERNAL_USER_ID,
            email="admin@example.com",
            display_name="Admin",
            role="platform_admin",
        )
        config = {"spreadsheet_id": "spreadsheet-1"}
        snapshot = {"enabled": True, "tabs": [], "sheets": {}, "sync_status": "idle"}

        with (
            patch.object(app_module, "_resolve_sales_actor", return_value=actor),
            patch.object(app_module, "load_google_sheets_admin_config", return_value=config, create=True),
            patch.object(app_module, "ensure_google_sheets_admin_sync_worker_started", create=True),
            patch.object(app_module, "read_google_sheets_admin_snapshot", return_value=snapshot, create=True),
            patch("backend.api.routers.admin.log_google_sheets_admin_duration") as log_mock,
            TestClient(app_module.app) as client,
        ):
            response = client.get("/api/admin/google-sheets/bootstrap")

        self.assertEqual(response.status_code, 200, response.text)
        log_mock.assert_called()
        self.assertEqual(log_mock.call_args.kwargs["event"], "admin_bootstrap_route")

    def test_admin_google_sheets_sheet_payload_reports_route_timing(self) -> None:
        from backend.api import app as app_module

        actor = SalesActor(
            organization_id=DEFAULT_PHASE1_ORGANIZATION_ID,
            user_id=DEFAULT_PHASE1_INTERNAL_USER_ID,
            email="admin@example.com",
            display_name="Admin",
            role="platform_admin",
        )
        config = {"spreadsheet_id": "spreadsheet-1"}
        snapshot = {
            "last_successful_sync_at": datetime(2026, 4, 8, 0, 1, tzinfo=timezone.utc),
            "sheets": {
                "tab-1": {
                    "sheet_id": 101,
                    "raw_title": "Raw 1",
                    "display_title": "Tab 1",
                    "headers": ["name"],
                    "header_cells": [{"text": "name", "href": ""}],
                    "rows": [["a"]],
                    "row_cells": [[{"text": "a", "href": ""}]],
                    "row_count": 1,
                    "column_count": 1,
                }
            },
        }

        with (
            patch.object(app_module, "_resolve_sales_actor", return_value=actor),
            patch.object(app_module, "load_google_sheets_admin_config", return_value=config, create=True),
            patch.object(app_module, "ensure_google_sheets_admin_sync_worker_started", create=True),
            patch.object(app_module, "read_google_sheets_admin_snapshot", return_value=snapshot, create=True),
            patch("backend.api.routers.admin.log_google_sheets_admin_duration") as log_mock,
            TestClient(app_module.app) as client,
        ):
            response = client.get("/api/admin/google-sheets/sheets/tab-1")

        self.assertEqual(response.status_code, 200, response.text)
        log_mock.assert_called()
        self.assertEqual(log_mock.call_args.kwargs["event"], "admin_sheet_payload_route")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/api/test_phase1_api.py -k "reports_route_timing and google_sheets" -q`
Expected: FAIL because `backend.api.routers.admin` does not yet call `log_google_sheets_admin_duration`

- [ ] **Step 3: Write the minimal route timing implementation**

```python
from backend.perf_runtime import log_google_sheets_admin_duration


@router.get("/api/admin/google-sheets/bootstrap", response_model=AdminGoogleSheetsBootstrapResponse, responses={403: {"model": ErrorResponse}})
def get_admin_google_sheets_bootstrap(request: Request) -> AdminGoogleSheetsBootstrapResponse:
    started = time.perf_counter()
    try:
        admin_app = _app_module()
        actor = admin_app._resolve_sales_actor(request)
        if not actor.is_admin:
            raise admin_app.ApiError(
                status_code=status.HTTP_403_FORBIDDEN,
                code="auth_forbidden",
                message="관리자만 Google Sheets 상태를 조회할 수 있습니다.",
            )
        config = admin_app.load_google_sheets_admin_config()
        if not config:
            return AdminGoogleSheetsBootstrapResponse(enabled=False, sync_status="not_configured", tabs=[])
        admin_app.ensure_google_sheets_admin_sync_worker_started(config=config)
        snapshot = admin_app.read_google_sheets_admin_snapshot(config=config) or {}
        sheets = dict(snapshot.get("sheets") or {})
        tabs = [
            AdminGoogleSheetTabItem(
                key=str((tab or {}).get("key") or "").strip(),
                sheet_id=(tab or {}).get("sheet_id"),
                raw_title=str((tab or {}).get("raw_title") or ""),
                display_title=str((tab or {}).get("display_title") or ""),
                sheet_order=int((tab or {}).get("sheet_order") or 0),
                row_count=int(dict(sheets.get(str((tab or {}).get("key") or "").strip()) or {}).get("row_count") or 0),
                column_count=int(dict(sheets.get(str((tab or {}).get("key") or "").strip()) or {}).get("column_count") or 0),
            )
            for tab in list(snapshot.get("tabs") or [])
        ]
        return AdminGoogleSheetsBootstrapResponse(
            enabled=bool(snapshot.get("enabled", True)),
            source_title=str(snapshot.get("source_title") or ""),
            source_url=str(snapshot.get("source_url") or ""),
            sync_status=str(snapshot.get("sync_status") or "initializing"),
            last_successful_sync_at=snapshot.get("last_successful_sync_at"),
            last_failed_sync_at=snapshot.get("last_failed_sync_at"),
            last_error=str(snapshot.get("last_error") or ""),
            tabs=tabs,
        )
    finally:
        log_google_sheets_admin_duration(
            event="admin_bootstrap_route",
            duration=time.perf_counter() - started,
            path="/api/admin/google-sheets/bootstrap",
        )
```

```python
@router.get("/api/admin/google-sheets/sheets/{sheet_key}", response_model=AdminGoogleSheetPayloadResponse, responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def get_admin_google_sheets_sheet_payload(request: Request, sheet_key: str) -> AdminGoogleSheetPayloadResponse:
    started = time.perf_counter()
    try:
        ...
        return AdminGoogleSheetPayloadResponse(
            key=sheet_key,
            synced_at=snapshot.get("last_successful_sync_at"),
            sheet_id=payload.get("sheet_id"),
            raw_title=str(payload.get("raw_title") or ""),
            display_title=str(payload.get("display_title") or ""),
            headers=list(payload.get("headers") or []),
            header_cells=header_cells,
            rows=list(payload.get("rows") or []),
            row_cells=row_cells,
            row_count=int(payload.get("row_count") or 0),
            column_count=int(payload.get("column_count") or 0),
        )
    finally:
        log_google_sheets_admin_duration(
            event="admin_sheet_payload_route",
            duration=time.perf_counter() - started,
            path=f"/api/admin/google-sheets/sheets/{sheet_key}",
            sheet_key=sheet_key,
        )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/api/test_phase1_api.py -k "reports_route_timing and google_sheets" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/routers/admin.py tests/api/test_phase1_api.py
git commit -m "feat: log google sheets admin route timing"
```

### Task 4: Run focused verification on the finished performance fix

**Files:**
- Verify: `backend/perf_runtime.py`
- Verify: `backend/services/google_sheets_admin_store.py`
- Verify: `backend/api/routers/admin.py`
- Verify: `tests/test_perf_runtime.py`
- Verify: `tests/test_google_sheets_admin_store.py`
- Verify: `tests/api/test_phase1_api.py`

- [ ] **Step 1: Run the focused regression suite**

Run: `pytest tests/test_perf_runtime.py tests/test_google_sheets_admin_store.py tests/api/test_phase1_api.py -k "google_sheets_admin or google_sheets" -q`
Expected: PASS

- [ ] **Step 2: Review the changed file summary**

Run: `git diff --stat HEAD~3..HEAD`
Expected: only `backend/perf_runtime.py`, `backend/services/google_sheets_admin_store.py`, `backend/api/routers/admin.py`, and the targeted tests

- [ ] **Step 3: Check git status**

Run: `git status --short --branch`
Expected: clean or only the intended Google Sheets performance files

- [ ] **Step 4: Record rollout notes**

```text
- Stable admin Google Sheets reads now reuse cached snapshots without full-file hashing.
- Slow snapshot reads and slow bootstrap/payload routes now emit `perf.google_sheets_admin` logs.
- Frontend timeout thresholds were intentionally left unchanged so backend improvement can be measured directly.
```

- [ ] **Step 5: Commit any final verification-only fix if needed**

```bash
git add backend/perf_runtime.py backend/services/google_sheets_admin_store.py backend/api/routers/admin.py tests/test_perf_runtime.py tests/test_google_sheets_admin_store.py tests/api/test_phase1_api.py
git commit -m "fix: finalize google sheets snapshot read performance"
```
