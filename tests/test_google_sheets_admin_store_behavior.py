import threading
from pathlib import Path

import pytest

import backend.services.google_sheets_admin_store as store
from backend.services.google_sheets_admin_backend import GoogleSheetsAdminConfig
from backend.services.google_sheets_admin_store import (
    load_google_sheets_admin_snapshot,
    persist_google_sheets_admin_snapshot,
)

SYNC_FAILURE_MESSAGE = "Google Sheets sync failed."
PERSISTENCE_FAILURE_MESSAGE = "Snapshot persistence failed."


@pytest.fixture(autouse=True)
def reset_google_sheets_admin_store_state():
    store._GOOGLE_SHEETS_ADMIN_FILE_LOCKS = {}
    store._GOOGLE_SHEETS_ADMIN_SNAPSHOTS = {}
    store._GOOGLE_SHEETS_ADMIN_SNAPSHOT_PATHS = {}
    store._GOOGLE_SHEETS_ADMIN_SNAPSHOT_FILE_STATE = {}
    store._GOOGLE_SHEETS_ADMIN_SYNC_LOCKS = {}
    store._GOOGLE_SHEETS_ADMIN_WORKERS = {}
    store._GOOGLE_SHEETS_ADMIN_STOP = threading.Event()
    store._GOOGLE_SHEETS_ADMIN_WORKER_STARTING = set()
    store._GOOGLE_SHEETS_ADMIN_MANUAL_SYNC_IN_FLIGHT = set()
    yield
    store._GOOGLE_SHEETS_ADMIN_FILE_LOCKS = {}
    store._GOOGLE_SHEETS_ADMIN_SNAPSHOTS = {}
    store._GOOGLE_SHEETS_ADMIN_SNAPSHOT_PATHS = {}
    store._GOOGLE_SHEETS_ADMIN_SNAPSHOT_FILE_STATE = {}
    store._GOOGLE_SHEETS_ADMIN_SYNC_LOCKS = {}
    store._GOOGLE_SHEETS_ADMIN_WORKERS = {}
    store._GOOGLE_SHEETS_ADMIN_STOP = threading.Event()
    store._GOOGLE_SHEETS_ADMIN_WORKER_STARTING = set()
    store._GOOGLE_SHEETS_ADMIN_MANUAL_SYNC_IN_FLIGHT = set()


def build_config(tmp_path):
    return GoogleSheetsAdminConfig(
        spreadsheet_id="spreadsheet-123",
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        sync_interval_seconds=300,
        snapshot_path=tmp_path / "snapshot.json",
    )


def build_config_with_name(tmp_path, name):
    return GoogleSheetsAdminConfig(
        spreadsheet_id=f"spreadsheet-{name}",
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        sync_interval_seconds=300,
        snapshot_path=tmp_path / f"{name}.json",
    )


def test_persist_google_sheets_admin_snapshot_round_trips(tmp_path):
    path = tmp_path / "snapshot.json"
    payload = {"version": 3, "tabs": [{"key": "sheet-1"}]}

    persist_google_sheets_admin_snapshot(path=path, snapshot=payload)

    assert load_google_sheets_admin_snapshot(path=path) == payload
    assert not [item for item in tmp_path.glob("snapshot.json.*") if item.suffix != ".lock"]


def test_load_google_sheets_admin_snapshot_returns_none_for_corrupted_json(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text("{not-json", encoding="utf-8")

    assert load_google_sheets_admin_snapshot(path=path) is None


@pytest.mark.parametrize("raw_value", ['1', '"x"', "[1]"])
def test_load_google_sheets_admin_snapshot_returns_none_for_valid_non_dict_json(tmp_path, raw_value):
    path = tmp_path / "snapshot.json"
    path.write_text(raw_value, encoding="utf-8")

    assert load_google_sheets_admin_snapshot(path=path) is None


def test_read_google_sheets_admin_snapshot_returns_none_for_corrupted_json(tmp_path):
    config = build_config(tmp_path)
    config.snapshot_path.write_text("{not-json", encoding="utf-8")

    assert store.read_google_sheets_admin_snapshot(config=config) is None


def test_read_google_sheets_admin_snapshot_returns_none_when_snapshot_lock_path_cannot_be_prepared(
    tmp_path,
):
    blocked_parent = tmp_path / "blocked"
    blocked_parent.write_text("not-a-directory", encoding="utf-8")
    config = GoogleSheetsAdminConfig(
        spreadsheet_id="spreadsheet-123",
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        sync_interval_seconds=300,
        snapshot_path=blocked_parent / "snapshot.json",
    )

    assert store.read_google_sheets_admin_snapshot(config=config) is None


def test_read_google_sheets_admin_snapshot_returns_cached_snapshot_when_snapshot_lock_path_cannot_be_prepared(
    tmp_path,
):
    blocked_parent = tmp_path / "blocked"
    blocked_parent.write_text("not-a-directory", encoding="utf-8")
    config = GoogleSheetsAdminConfig(
        spreadsheet_id="spreadsheet-123",
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        sync_interval_seconds=300,
        snapshot_path=blocked_parent / "snapshot.json",
    )
    state_key = store._google_sheets_admin_state_key(config=config)
    cached_snapshot = {"tabs": [{"key": "sheet-1"}], "marker": "cached"}
    store._GOOGLE_SHEETS_ADMIN_SNAPSHOTS[state_key] = cached_snapshot

    assert store.read_google_sheets_admin_snapshot(config=config) == cached_snapshot


@pytest.mark.parametrize("raw_value", ['1', '"x"', "[1]"])
def test_read_google_sheets_admin_snapshot_returns_none_for_valid_non_dict_json(tmp_path, raw_value):
    config = build_config(tmp_path)
    config.snapshot_path.write_text(raw_value, encoding="utf-8")

    assert store.read_google_sheets_admin_snapshot(config=config) is None


def test_read_google_sheets_admin_snapshot_is_keyed_by_snapshot_path(tmp_path):
    config_a = build_config_with_name(tmp_path, "a")
    config_b = build_config_with_name(tmp_path, "b")
    payload_a = {"tabs": [{"key": "sheet-a"}], "marker": "A"}
    payload_b = {"tabs": [{"key": "sheet-b"}], "marker": "B"}

    persist_google_sheets_admin_snapshot(path=config_a.snapshot_path, snapshot=payload_a)
    persist_google_sheets_admin_snapshot(path=config_b.snapshot_path, snapshot=payload_b)

    assert store.read_google_sheets_admin_snapshot(config=config_a) == payload_a
    assert store.read_google_sheets_admin_snapshot(config=config_b) == payload_b


def test_read_google_sheets_admin_snapshot_returns_deep_copied_data(tmp_path):
    config = build_config(tmp_path)
    payload = {
        "tabs": [{"key": "sheet-1"}],
        "sheets": {"sheet-1": {"headers": ["status"], "rows": [["open"]]}},
    }
    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=payload)

    first = store.read_google_sheets_admin_snapshot(config=config)
    first["tabs"][0]["key"] = "mutated"
    first["sheets"]["sheet-1"]["headers"].append("project")
    first["sheets"]["sheet-1"]["rows"][0][0] = "changed"

    second = store.read_google_sheets_admin_snapshot(config=config)

    assert second == payload


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
    tmp_path,
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
        raising=False,
    )

    assert store.read_google_sheets_admin_snapshot(config=config) == payload
    assert events[-1]["event"] == "snapshot_read"
    assert events[-1]["cache_hit"] is True


def test_read_google_sheets_admin_snapshot_detects_external_file_mutation(tmp_path):
    config = build_config(tmp_path)
    first_payload = {"tabs": [{"key": "sheet-1"}], "marker": "first"}
    second_payload = {"tabs": [{"key": "sheet-2"}], "marker": "second"}

    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=first_payload)
    assert store.read_google_sheets_admin_snapshot(config=config) == first_payload

    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=second_payload)

    assert store.read_google_sheets_admin_snapshot(config=config) == second_payload


def test_read_google_sheets_admin_snapshot_returns_none_after_snapshot_file_is_deleted(
    tmp_path,
):
    config = build_config(tmp_path)
    payload = {"tabs": [{"key": "sheet-1"}], "marker": "first"}

    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=payload)
    assert store.read_google_sheets_admin_snapshot(config=config) == payload

    config.snapshot_path.unlink()

    assert store.read_google_sheets_admin_snapshot(config=config) is None
    assert store.read_google_sheets_admin_snapshot(config=config) is None


def test_read_google_sheets_admin_snapshot_returns_cached_snapshot_after_external_corruption(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)
    payload = {"tabs": [{"key": "sheet-1"}], "marker": "good"}
    load_calls = {"count": 0}
    original_load = store.load_google_sheets_admin_snapshot

    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=payload)
    assert store.read_google_sheets_admin_snapshot(config=config) == payload

    config.snapshot_path.write_text("{bad-json", encoding="utf-8")

    def counting_load(*, path):
        load_calls["count"] += 1
        return original_load(path=path)

    monkeypatch.setattr(store, "load_google_sheets_admin_snapshot", counting_load)

    assert store.read_google_sheets_admin_snapshot(config=config) == payload
    assert store.read_google_sheets_admin_snapshot(config=config) == payload
    assert load_calls["count"] == 1


def test_read_google_sheets_admin_snapshot_uses_stable_absolute_path_for_relative_snapshot_paths(
    tmp_path, monkeypatch
):
    workspace_a = tmp_path / "workspace-a"
    workspace_b = tmp_path / "workspace-b"
    workspace_a.mkdir()
    workspace_b.mkdir()
    relative_snapshot_path = "snapshots/google-admin.json"
    config = GoogleSheetsAdminConfig(
        spreadsheet_id="spreadsheet-123",
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        sync_interval_seconds=300,
        snapshot_path=relative_snapshot_path,
    )
    payload = {"tabs": [{"key": "sheet-1"}], "marker": "stable"}

    class FakeResponse:
        def __init__(self, response_payload):
            self._response_payload = response_payload

        def json(self):
            return self._response_payload

        def raise_for_status(self):
            return None

    def fake_post(url, data, timeout):
        return FakeResponse({"access_token": "access-token"})

    def fake_get(url, headers=None, params=None, timeout=15):
        if url.endswith("/v4/spreadsheets/spreadsheet-123"):
            return FakeResponse(
                {
                    "properties": {"title": "@source"},
                    "sheets": [{"properties": {"sheetId": 1, "title": "Sheet 1", "index": 0}}],
                }
            )
        return FakeResponse({"values": [["marker"], [payload["marker"]]]})

    monkeypatch.chdir(workspace_a)
    store.run_google_sheets_admin_sync(
        config=config,
        request_post_fn=fake_post,
        request_get_fn=fake_get,
    )

    monkeypatch.chdir(workspace_b)

    assert store.read_google_sheets_admin_snapshot(config=config)["sheets"]["sheet-1"]["rows"] == [
        [payload["marker"]]
    ]


def test_read_google_sheets_admin_snapshot_reuses_relative_path_resolution_across_distinct_configs(
    tmp_path, monkeypatch
):
    workspace_a = tmp_path / "workspace-a"
    workspace_b = tmp_path / "workspace-b"
    workspace_a.mkdir()
    workspace_b.mkdir()
    relative_snapshot_path = "snapshots/google-admin.json"
    config_a = GoogleSheetsAdminConfig(
        spreadsheet_id="spreadsheet-a",
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        sync_interval_seconds=300,
        snapshot_path=relative_snapshot_path,
    )
    config_b = GoogleSheetsAdminConfig(
        spreadsheet_id="spreadsheet-b",
        client_id="client-id",
        client_secret="other-client-secret",
        refresh_token="other-refresh-token",
        sync_interval_seconds=300,
        snapshot_path=relative_snapshot_path,
    )
    payload = {"tabs": [{"key": "sheet-1"}], "marker": "stable-across-configs"}

    class FakeResponse:
        def __init__(self, response_payload):
            self._response_payload = response_payload

        def json(self):
            return self._response_payload

        def raise_for_status(self):
            return None

    def fake_post(url, data, timeout):
        return FakeResponse({"access_token": "access-token"})

    def fake_get(url, headers=None, params=None, timeout=15):
        if url.endswith("/v4/spreadsheets/spreadsheet-a"):
            return FakeResponse(
                {
                    "properties": {"title": "@source"},
                    "sheets": [{"properties": {"sheetId": 1, "title": "Sheet 1", "index": 0}}],
                }
            )
        return FakeResponse({"values": [["marker"], [payload["marker"]]]})

    monkeypatch.chdir(workspace_a)
    store.run_google_sheets_admin_sync(
        config=config_a,
        request_post_fn=fake_post,
        request_get_fn=fake_get,
    )

    monkeypatch.chdir(workspace_b)

    assert store.read_google_sheets_admin_snapshot(config=config_b)["sheets"]["sheet-1"]["rows"] == [
        [payload["marker"]]
    ]


def test_queue_google_sheets_admin_sync_now_records_failure_and_preserves_last_good_snapshot(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)
    good_snapshot = {
        "enabled": True,
        "source_title": "@source",
        "source_url": "https://docs.google.com/spreadsheets/d/spreadsheet-123/edit",
        "sync_status": "ready",
        "last_successful_sync_at": "2026-04-18T00:00:00+00:00",
        "tabs": [{"key": "sheet-1"}],
        "sheets": {"sheet-1": {"headers": ["status"], "rows": [["open"]]}},
    }
    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=good_snapshot)

    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target
            self._started = False

        def start(self):
            self._started = True
            self._target()

        def is_alive(self):
            return self._started

    monkeypatch.setattr(store.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        store.requests,
        "post",
        lambda url, data, timeout: (_ for _ in ()).throw(RuntimeError("token refresh failed")),
    )

    store.queue_google_sheets_admin_sync_now(config=config)

    snapshot = load_google_sheets_admin_snapshot(path=config.snapshot_path)

    assert snapshot["sync_status"] == "failed"
    assert snapshot["last_error"] == SYNC_FAILURE_MESSAGE
    assert "last_sync_attempt_at" in snapshot
    assert "last_failed_sync_at" in snapshot
    assert snapshot["last_successful_sync_at"] == "2026-04-18T00:00:00+00:00"
    assert snapshot["tabs"] == good_snapshot["tabs"]
    assert snapshot["sheets"] == good_snapshot["sheets"]


def test_queue_google_sheets_admin_sync_now_handles_corrupted_snapshot_on_failure(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)
    config.snapshot_path.write_text("{not-json", encoding="utf-8")

    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self):
            self._target()

        def is_alive(self):
            return True

    monkeypatch.setattr(store.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        store.requests,
        "post",
        lambda url, data, timeout: (_ for _ in ()).throw(RuntimeError("token refresh failed")),
    )

    store.queue_google_sheets_admin_sync_now(config=config)

    snapshot = load_google_sheets_admin_snapshot(path=config.snapshot_path)

    assert snapshot["sync_status"] == "failed"
    assert snapshot["last_error"] == SYNC_FAILURE_MESSAGE
    assert snapshot["tabs"] == []
    assert snapshot["sheets"] == {}


@pytest.mark.parametrize("raw_value", ['1', '"x"', "[1]"])
def test_queue_google_sheets_admin_sync_now_handles_non_dict_snapshot_on_failure(
    tmp_path, monkeypatch, raw_value
):
    config = build_config(tmp_path)
    config.snapshot_path.write_text(raw_value, encoding="utf-8")

    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self):
            self._target()

        def is_alive(self):
            return True

    monkeypatch.setattr(store.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        store.requests,
        "post",
        lambda url, data, timeout: (_ for _ in ()).throw(RuntimeError("token refresh failed")),
    )

    store.queue_google_sheets_admin_sync_now(config=config)

    snapshot = load_google_sheets_admin_snapshot(path=config.snapshot_path)

    assert snapshot["sync_status"] == "failed"
    assert snapshot["last_error"] == SYNC_FAILURE_MESSAGE
    assert snapshot["tabs"] == []
    assert snapshot["sheets"] == {}


def test_queue_google_sheets_admin_sync_now_coalesces_in_flight_manual_requests(tmp_path, monkeypatch):
    config = build_config(tmp_path)
    created = []

    class IdleThread:
        def __init__(self, target, daemon=True):
            self._target = target
            self._started = False
            created.append(self)

        def start(self):
            self._started = True

        def is_alive(self):
            return self._started

    monkeypatch.setattr(store.threading, "Thread", IdleThread)

    first = store.queue_google_sheets_admin_sync_now(config=config)
    second = store.queue_google_sheets_admin_sync_now(config=config)

    assert len(created) == 1
    assert first is True
    assert second is False


def test_queue_google_sheets_admin_sync_now_rolls_back_in_flight_flag_when_thread_constructor_fails(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)

    def raising_thread(*args, **kwargs):
        raise RuntimeError("constructor failed")

    monkeypatch.setattr(store.threading, "Thread", raising_thread)

    with pytest.raises(RuntimeError, match="constructor failed"):
        store.queue_google_sheets_admin_sync_now(config=config)

    assert store._GOOGLE_SHEETS_ADMIN_MANUAL_SYNC_IN_FLIGHT == set()


def test_queue_google_sheets_admin_sync_now_rolls_back_in_flight_flag_when_thread_start_fails(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)

    class StartFailThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self):
            raise RuntimeError("start failed")

    monkeypatch.setattr(store.threading, "Thread", StartFailThread)

    with pytest.raises(RuntimeError, match="start failed"):
        store.queue_google_sheets_admin_sync_now(config=config)

    assert store._GOOGLE_SHEETS_ADMIN_MANUAL_SYNC_IN_FLIGHT == set()


def test_ensure_google_sheets_admin_sync_worker_started_retries_after_failures(tmp_path, monkeypatch):
    config = build_config(tmp_path)
    attempts = {"count": 0}

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

        def raise_for_status(self):
            return None

    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target
            self._started = False

        def start(self):
            self._started = True
            self._target()

        def is_alive(self):
            return self._started

    class FakeStopEvent:
        def __init__(self):
            self._calls = 0

        def wait(self, timeout):
            self._calls += 1
            return self._calls >= 3

    def fake_post(url, data, timeout):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary oauth failure")
        return FakeResponse({"access_token": "access-token"})

    def fake_get(url, headers=None, params=None, timeout=15):
        if url.endswith("/v4/spreadsheets/spreadsheet-123"):
            return FakeResponse(
                {
                    "properties": {"title": "@source"},
                    "sheets": [{"properties": {"sheetId": 1, "title": "Sheet 1", "index": 0}}],
                }
            )
        return FakeResponse({"values": [["status"], ["open"]]})

    monkeypatch.setattr(store.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(store.requests, "post", fake_post)
    monkeypatch.setattr(store.requests, "get", fake_get)
    monkeypatch.setattr(store, "_GOOGLE_SHEETS_ADMIN_STOP", FakeStopEvent())

    store.ensure_google_sheets_admin_sync_worker_started(config=config)

    snapshot = load_google_sheets_admin_snapshot(path=config.snapshot_path)

    assert attempts["count"] == 3
    assert snapshot["sync_status"] == "ready"
    assert snapshot["tabs"] == [
        {
            "key": "sheet-1",
            "sheet_id": 1,
            "raw_title": "Sheet 1",
            "display_title": "Sheet 1",
            "sheet_order": 0,
        }
    ]
    assert snapshot["sheets"]["sheet-1"]["rows"] == [["open"]]


def test_ensure_google_sheets_admin_sync_worker_started_runs_sync_immediately(tmp_path, monkeypatch):
    config = build_config(tmp_path)
    attempts = {"count": 0}

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

        def raise_for_status(self):
            return None

    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target
            self._started = False

        def start(self):
            self._started = True
            self._target()

        def is_alive(self):
            return self._started

    class StopImmediately:
        def wait(self, timeout):
            return True

    def fake_post(url, data, timeout):
        attempts["count"] += 1
        return FakeResponse({"access_token": "access-token"})

    def fake_get(url, headers=None, params=None, timeout=15):
        if url.endswith("/v4/spreadsheets/spreadsheet-123"):
            return FakeResponse(
                {
                    "properties": {"title": "@source"},
                    "sheets": [{"properties": {"sheetId": 1, "title": "Sheet 1", "index": 0}}],
                }
            )
        return FakeResponse({"values": [["status"], ["open"]]})

    monkeypatch.setattr(store.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(store.requests, "post", fake_post)
    monkeypatch.setattr(store.requests, "get", fake_get)
    monkeypatch.setattr(store, "_GOOGLE_SHEETS_ADMIN_STOP", StopImmediately())

    store.ensure_google_sheets_admin_sync_worker_started(config=config)

    snapshot = load_google_sheets_admin_snapshot(path=config.snapshot_path)

    assert attempts["count"] == 1
    assert snapshot["sync_status"] == "ready"


def test_ensure_google_sheets_admin_sync_worker_started_is_single_flight(tmp_path, monkeypatch):
    config = build_config(tmp_path)
    created = []
    first_constructor_ready = threading.Event()
    second_constructor_seen = threading.Event()
    real_thread = threading.Thread

    class FakeWorker:
        def __init__(self, target, daemon=True):
            self._target = target
            self._started = False
            created.append(self)
            if len(created) == 1:
                first_constructor_ready.set()
                second_constructor_seen.wait(0.2)
            else:
                second_constructor_seen.set()

        def start(self):
            self._started = True

        def is_alive(self):
            return self._started

    monkeypatch.setattr(store.threading, "Thread", FakeWorker)

    callers = [
        real_thread(
            target=store.ensure_google_sheets_admin_sync_worker_started,
            kwargs={"config": config},
        )
        for _ in range(2)
    ]

    for caller in callers:
        caller.start()
    for caller in callers:
        caller.join()

    assert first_constructor_ready.is_set()
    assert len(created) == 1


def test_ensure_google_sheets_admin_sync_worker_started_rolls_back_starting_flag_when_constructor_fails(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)

    def raising_thread(*args, **kwargs):
        raise RuntimeError("constructor failed")

    monkeypatch.setattr(store.threading, "Thread", raising_thread)

    with pytest.raises(RuntimeError, match="constructor failed"):
        store.ensure_google_sheets_admin_sync_worker_started(config=config)

    assert store._GOOGLE_SHEETS_ADMIN_WORKER_STARTING == set()


def test_ensure_google_sheets_admin_sync_worker_started_rolls_back_starting_flag_when_start_fails(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)

    class StartFailThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self):
            raise RuntimeError("start failed")

        def is_alive(self):
            return False

    monkeypatch.setattr(store.threading, "Thread", StartFailThread)

    with pytest.raises(RuntimeError, match="start failed"):
        store.ensure_google_sheets_admin_sync_worker_started(config=config)

    assert store._GOOGLE_SHEETS_ADMIN_WORKER_STARTING == set()


def test_run_google_sheets_admin_sync_does_not_globally_serialize_different_snapshot_paths(
    tmp_path, monkeypatch
):
    config_a = build_config_with_name(tmp_path, "a")
    config_b = build_config_with_name(tmp_path, "b")
    first_entered = threading.Event()
    second_entered = threading.Event()
    release_both = threading.Event()
    started = []
    finished = []

    def fake_sync(*, config, request_post_fn, request_get_fn, now_fn):
        started.append(config.snapshot_path.name)
        if config.snapshot_path.name == "a.json":
            first_entered.set()
            assert second_entered.wait(0.2)
        else:
            second_entered.set()
        assert release_both.wait(0.2)
        finished.append(config.snapshot_path.name)
        return {"snapshot": config.snapshot_path.name}

    monkeypatch.setattr(store, "sync_google_sheets_admin_snapshot_once", fake_sync)

    thread_a = threading.Thread(target=store.run_google_sheets_admin_sync, kwargs={"config": config_a})
    thread_b = threading.Thread(target=store.run_google_sheets_admin_sync, kwargs={"config": config_b})

    thread_a.start()
    assert first_entered.wait(0.2)
    thread_b.start()
    assert second_entered.wait(0.2)
    release_both.set()
    thread_a.join()
    thread_b.join()

    assert started.count("a.json") == 1
    assert started.count("b.json") == 1
    assert finished.count("a.json") == 1
    assert finished.count("b.json") == 1


def test_run_google_sheets_admin_sync_survives_persist_failure_and_preserves_last_good_data(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)
    good_snapshot = {
        "enabled": True,
        "source_title": "@source",
        "source_url": "https://docs.google.com/spreadsheets/d/spreadsheet-123/edit",
        "sync_status": "ready",
        "last_successful_sync_at": "2026-04-18T00:00:00+00:00",
        "tabs": [{"key": "sheet-1"}],
        "sheets": {"sheet-1": {"headers": ["status"], "rows": [["open"]]}} ,
    }
    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=good_snapshot)

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

        def raise_for_status(self):
            return None

    def fake_post(url, data, timeout):
        return FakeResponse({"access_token": "access-token"})

    def fake_get(url, headers=None, params=None, timeout=15):
        if url.endswith("/v4/spreadsheets/spreadsheet-123"):
            return FakeResponse(
                {
                    "properties": {"title": "@fresh"},
                    "sheets": [{"properties": {"sheetId": 2, "title": "Sheet 2", "index": 0}}],
                }
            )
        return FakeResponse({"values": [["status"], ["closed"]]})

    monkeypatch.setattr(
        store,
        "persist_google_sheets_admin_snapshot",
        lambda *,
        path,
        snapshot,
        expected_existing_state=store._GOOGLE_SHEETS_ADMIN_EXPECTED_STATE_UNSET: (_ for _ in ()).throw(
            OSError("disk full")
        ),
    )

    snapshot = store.run_google_sheets_admin_sync(
        config=config,
        request_post_fn=fake_post,
        request_get_fn=fake_get,
    )

    assert snapshot["sync_status"] == "failed"
    assert snapshot["last_error"] == PERSISTENCE_FAILURE_MESSAGE
    assert snapshot["persistence_error"] == PERSISTENCE_FAILURE_MESSAGE
    assert snapshot["tabs"] == good_snapshot["tabs"]
    assert snapshot["sheets"] == good_snapshot["sheets"]
    assert snapshot["last_successful_sync_at"] == "2026-04-18T00:00:00+00:00"


def test_run_google_sheets_admin_sync_returns_failed_snapshot_when_snapshot_lock_path_cannot_be_prepared(
    tmp_path,
):
    blocked_parent = tmp_path / "blocked"
    blocked_parent.write_text("not-a-directory", encoding="utf-8")
    config = GoogleSheetsAdminConfig(
        spreadsheet_id="spreadsheet-123",
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        sync_interval_seconds=300,
        snapshot_path=blocked_parent / "snapshot.json",
    )

    snapshot = store.run_google_sheets_admin_sync(
        config=config,
        request_post_fn=lambda url, data, timeout: pytest.fail("request_post_fn should not be called"),
    )

    assert snapshot["sync_status"] == "failed"
    assert snapshot["last_error"] == SYNC_FAILURE_MESSAGE
    assert snapshot["persistence_error"] == PERSISTENCE_FAILURE_MESSAGE
    assert snapshot["tabs"] == []
    assert snapshot["sheets"] == {}


def test_run_google_sheets_admin_sync_preserves_sync_failure_metadata_when_failure_persist_also_fails(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)
    good_snapshot = {
        "enabled": True,
        "source_title": "@source",
        "source_url": "https://docs.google.com/spreadsheets/d/spreadsheet-123/edit",
        "sync_status": "ready",
        "last_successful_sync_at": "2026-04-18T00:00:00+00:00",
        "tabs": [{"key": "sheet-1"}],
        "sheets": {"sheet-1": {"headers": ["status"], "rows": [["open"]]}} ,
    }
    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=good_snapshot)

    monkeypatch.setattr(
        store,
        "persist_google_sheets_admin_snapshot",
        lambda *, path, snapshot, expected_existing_state=None: (_ for _ in ()).throw(
            OSError("disk full / private path")
        ),
    )

    snapshot = store.run_google_sheets_admin_sync(
        config=config,
        request_post_fn=lambda url, data, timeout: (_ for _ in ()).throw(
            RuntimeError("secret token text")
        ),
    )

    assert snapshot["sync_status"] == "failed"
    assert snapshot["last_error"] == SYNC_FAILURE_MESSAGE
    assert snapshot["persistence_error"] == PERSISTENCE_FAILURE_MESSAGE
    assert "last_sync_attempt_at" in snapshot
    assert "last_failed_sync_at" in snapshot
    assert snapshot["tabs"] == good_snapshot["tabs"]
    assert snapshot["sheets"] == good_snapshot["sheets"]
    assert snapshot["last_successful_sync_at"] == "2026-04-18T00:00:00+00:00"


def test_run_google_sheets_admin_sync_sanitizes_persisted_error_text(tmp_path, monkeypatch):
    config = build_config(tmp_path)

    snapshot = store.run_google_sheets_admin_sync(
        config=config,
        request_post_fn=lambda url, data, timeout: (_ for _ in ()).throw(
            RuntimeError("refresh token=abc123 should not be persisted")
        ),
    )

    assert snapshot["last_error"] == SYNC_FAILURE_MESSAGE
    assert "abc123" not in snapshot["last_error"]


def test_run_google_sheets_admin_sync_clears_stale_persistence_error_after_later_failure_persists(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)
    original_persist = store.persist_google_sheets_admin_snapshot
    first_attempt = {"raised": False}

    def fail_once(*, path, snapshot, expected_existing_state=None):
        if not first_attempt["raised"]:
            first_attempt["raised"] = True
            raise OSError("disk full")
        return original_persist(
            path=path,
            snapshot=snapshot,
            expected_existing_state=expected_existing_state,
        )

    monkeypatch.setattr(store, "persist_google_sheets_admin_snapshot", fail_once)

    first_snapshot = store.run_google_sheets_admin_sync(
        config=config,
        request_post_fn=lambda url, data, timeout: (_ for _ in ()).throw(
            RuntimeError("oauth secret 123")
        ),
    )

    assert first_snapshot["persistence_error"] == PERSISTENCE_FAILURE_MESSAGE

    second_snapshot = store.run_google_sheets_admin_sync(
        config=config,
        request_post_fn=lambda url, data, timeout: (_ for _ in ()).throw(
            RuntimeError("later sync failure")
        ),
    )

    assert second_snapshot["last_error"] == SYNC_FAILURE_MESSAGE
    assert "persistence_error" not in second_snapshot
    assert load_google_sheets_admin_snapshot(path=config.snapshot_path)["last_error"] == SYNC_FAILURE_MESSAGE
    assert "persistence_error" not in load_google_sheets_admin_snapshot(path=config.snapshot_path)


def test_run_google_sheets_admin_sync_does_not_overwrite_newer_disk_snapshot_with_stale_failure(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)
    older_snapshot = {"tabs": [{"key": "sheet-old"}], "marker": "old"}
    newer_snapshot = {
        "tabs": [{"key": "sheet-new"}],
        "marker": "new snapshot written by another process",
    }
    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=older_snapshot)
    assert store.read_google_sheets_admin_snapshot(config=config) == older_snapshot

    original_persist = store.persist_google_sheets_admin_snapshot
    persist_calls = {"count": 0}

    def racing_persist(*, path, snapshot, expected_existing_state=None):
        persist_calls["count"] += 1
        if persist_calls["count"] == 1:
            original_persist(path=path, snapshot=newer_snapshot)
        return original_persist(
            path=path,
            snapshot=snapshot,
            expected_existing_state=expected_existing_state,
        )

    monkeypatch.setattr(store, "persist_google_sheets_admin_snapshot", racing_persist)

    result = store.run_google_sheets_admin_sync(
        config=config,
        request_post_fn=lambda url, data, timeout: (_ for _ in ()).throw(
            RuntimeError("sync failed before write")
        ),
    )

    assert result == newer_snapshot
    assert load_google_sheets_admin_snapshot(path=config.snapshot_path) == newer_snapshot


def test_run_google_sheets_admin_sync_does_not_overwrite_newer_disk_snapshot_with_stale_success(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)
    older_snapshot = {"tabs": [{"key": "sheet-old"}], "marker": "old"}
    newer_snapshot = {
        "tabs": [{"key": "sheet-new"}],
        "marker": "newer snapshot already persisted",
    }
    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=older_snapshot)
    assert store.read_google_sheets_admin_snapshot(config=config) == older_snapshot

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

        def raise_for_status(self):
            return None

    def fake_post(url, data, timeout):
        return FakeResponse({"access_token": "access-token"})

    def fake_get(url, headers=None, params=None, timeout=15):
        if url.endswith("/v4/spreadsheets/spreadsheet-123"):
            return FakeResponse(
                {
                    "properties": {"title": "@fresh"},
                    "sheets": [{"properties": {"sheetId": 2, "title": "Sheet 2", "index": 0}}],
                }
            )
        return FakeResponse({"values": [["status"], ["closed"]]})

    original_persist = store.persist_google_sheets_admin_snapshot
    persist_calls = {"count": 0}

    def racing_persist(*, path, snapshot, expected_existing_state=store._GOOGLE_SHEETS_ADMIN_EXPECTED_STATE_UNSET):
        persist_calls["count"] += 1
        if persist_calls["count"] == 1:
            original_persist(path=path, snapshot=newer_snapshot)
        return original_persist(
            path=path,
            snapshot=snapshot,
            expected_existing_state=expected_existing_state,
        )

    monkeypatch.setattr(store, "persist_google_sheets_admin_snapshot", racing_persist)

    result = store.run_google_sheets_admin_sync(
        config=config,
        request_post_fn=fake_post,
        request_get_fn=fake_get,
    )

    assert result == newer_snapshot
    assert load_google_sheets_admin_snapshot(path=config.snapshot_path) == newer_snapshot


def test_run_google_sheets_admin_sync_conflict_returns_failed_snapshot_when_competing_snapshot_is_unreadable(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

        def raise_for_status(self):
            return None

    def fake_post(url, data, timeout):
        return FakeResponse({"access_token": "access-token"})

    def fake_get(url, headers=None, params=None, timeout=15):
        if url.endswith("/v4/spreadsheets/spreadsheet-123"):
            return FakeResponse(
                {
                    "properties": {"title": "@fresh"},
                    "sheets": [{"properties": {"sheetId": 2, "title": "Sheet 2", "index": 0}}],
                }
            )
        return FakeResponse({"values": [["status"], ["closed"]]})

    original_persist = store.persist_google_sheets_admin_snapshot
    persist_calls = {"count": 0}

    def racing_persist(*, path, snapshot, expected_existing_state=store._GOOGLE_SHEETS_ADMIN_EXPECTED_STATE_UNSET):
        persist_calls["count"] += 1
        if persist_calls["count"] == 1:
            path.write_text("{not-json", encoding="utf-8")
        return original_persist(
            path=path,
            snapshot=snapshot,
            expected_existing_state=expected_existing_state,
        )

    monkeypatch.setattr(store, "persist_google_sheets_admin_snapshot", racing_persist)

    result = store.run_google_sheets_admin_sync(
        config=config,
        request_post_fn=fake_post,
        request_get_fn=fake_get,
    )

    assert result["sync_status"] == "failed"
    assert result["last_error"] == PERSISTENCE_FAILURE_MESSAGE
    assert result["persistence_error"] == PERSISTENCE_FAILURE_MESSAGE
    assert load_google_sheets_admin_snapshot(path=config.snapshot_path) is None


def test_run_google_sheets_admin_sync_does_not_overwrite_newer_success_snapshot_written_before_replace(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)
    older_snapshot = {"tabs": [{"key": "sheet-old"}], "marker": "old"}
    newer_snapshot = {
        "tabs": [{"key": "sheet-new"}],
        "marker": "newer snapshot written during old writer replace window",
    }
    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=older_snapshot)

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

        def raise_for_status(self):
            return None

    def fake_post(url, data, timeout):
        return FakeResponse({"access_token": "access-token"})

    def fake_get(url, headers=None, params=None, timeout=15):
        if url.endswith("/v4/spreadsheets/spreadsheet-123"):
            return FakeResponse(
                {
                    "properties": {"title": "@fresh"},
                    "sheets": [{"properties": {"sheetId": 2, "title": "Sheet 2", "index": 0}}],
                }
            )
        return FakeResponse({"values": [["status"], ["closed"]]})

    original_persist = store.persist_google_sheets_admin_snapshot
    injected = {"done": False}
    competing_done = threading.Event()
    competing_thread = {"thread": None}

    def racing_persist(*, path, snapshot, expected_existing_state=None):
        if snapshot.get("sync_status") == "ready" and not injected["done"]:
            injected["done"] = True

            def competing_writer():
                original_persist(path=path, snapshot=newer_snapshot)
                competing_done.set()

            thread = threading.Thread(target=competing_writer)
            competing_thread["thread"] = thread
            thread.start()
        return original_persist(
            path=path,
            snapshot=snapshot,
            expected_existing_state=expected_existing_state,
        )

    monkeypatch.setattr(store, "persist_google_sheets_admin_snapshot", racing_persist)

    result = store.run_google_sheets_admin_sync(
        config=config,
        request_post_fn=fake_post,
        request_get_fn=fake_get,
    )

    if result != newer_snapshot:
        assert result["sync_status"] == "ready"
    competing_thread["thread"].join(timeout=1)
    assert competing_done.is_set()
    assert load_google_sheets_admin_snapshot(path=config.snapshot_path) == newer_snapshot


def test_run_google_sheets_admin_sync_failure_uses_same_protected_load_and_state_capture(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)
    older_snapshot = {"tabs": [{"key": "sheet-old"}], "marker": "old"}
    newer_snapshot = {
        "tabs": [{"key": "sheet-new"}],
        "marker": "newer snapshot written between failure load and state capture",
    }
    original_load = store.load_google_sheets_admin_snapshot
    original_persist = store.persist_google_sheets_admin_snapshot
    injected = {"done": False}
    load_calls = {"count": 0}
    competing_thread = {"thread": None}
    competing_done = threading.Event()

    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=older_snapshot)

    def racing_load(*, path):
        load_calls["count"] += 1
        snapshot = original_load(path=path)
        if load_calls["count"] == 2 and not injected["done"]:
            injected["done"] = True

            def competing_writer():
                store.persist_google_sheets_admin_snapshot(path=path, snapshot=newer_snapshot)
                competing_done.set()

            thread = threading.Thread(target=competing_writer)
            competing_thread["thread"] = thread
            thread.start()
            thread.join(timeout=0.1)
        return snapshot

    monkeypatch.setattr(store, "load_google_sheets_admin_snapshot", racing_load)

    result = store.run_google_sheets_admin_sync(
        config=config,
        request_post_fn=lambda url, data, timeout: (_ for _ in ()).throw(
            RuntimeError("sync failed before write")
        ),
    )

    assert injected["done"] is True
    if result != newer_snapshot:
        assert result["marker"] in {older_snapshot["marker"], newer_snapshot["marker"]}
        assert result["tabs"] in (older_snapshot["tabs"], newer_snapshot["tabs"])
        assert result["sync_status"] == "failed"
        assert result["last_error"] == SYNC_FAILURE_MESSAGE
        assert "last_sync_attempt_at" in result
        assert "last_failed_sync_at" in result
    competing_thread["thread"].join(timeout=1)
    assert competing_done.is_set()
    assert load_google_sheets_admin_snapshot(path=config.snapshot_path) == newer_snapshot


def test_run_google_sheets_admin_sync_conflict_prefers_cached_snapshot_when_competing_snapshot_is_deleted(
    tmp_path, monkeypatch
):
    config = build_config(tmp_path)
    older_snapshot = {"tabs": [{"key": "sheet-old"}], "marker": "old"}
    persist_google_sheets_admin_snapshot(path=config.snapshot_path, snapshot=older_snapshot)
    assert store.read_google_sheets_admin_snapshot(config=config) == older_snapshot

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

        def raise_for_status(self):
            return None

    def fake_post(url, data, timeout):
        return FakeResponse({"access_token": "access-token"})

    def fake_get(url, headers=None, params=None, timeout=15):
        if url.endswith("/v4/spreadsheets/spreadsheet-123"):
            return FakeResponse(
                {
                    "properties": {"title": "@fresh"},
                    "sheets": [{"properties": {"sheetId": 2, "title": "Sheet 2", "index": 0}}],
                }
            )
        return FakeResponse({"values": [["status"], ["closed"]]})

    original_persist = store.persist_google_sheets_admin_snapshot
    persist_calls = {"count": 0}

    def racing_persist(*, path, snapshot, expected_existing_state=store._GOOGLE_SHEETS_ADMIN_EXPECTED_STATE_UNSET):
        persist_calls["count"] += 1
        if persist_calls["count"] == 1 and path.exists():
            path.unlink()
        return original_persist(
            path=path,
            snapshot=snapshot,
            expected_existing_state=expected_existing_state,
        )

    monkeypatch.setattr(store, "persist_google_sheets_admin_snapshot", racing_persist)

    result = store.run_google_sheets_admin_sync(
        config=config,
        request_post_fn=fake_post,
        request_get_fn=fake_get,
    )

    assert result == older_snapshot
    assert store.read_google_sheets_admin_snapshot(config=config) is None
