from __future__ import annotations

import os
from pathlib import Path


def test_load_desktop_env_files_reads_writable_root_env(tmp_path: Path) -> None:
    from desktop.launcher import load_desktop_env_files

    writable_root = tmp_path / "app"
    writable_root.mkdir()
    (writable_root / ".env").write_text(
        "G2B_SERVICE_KEY=local-key\n"
        "DATA_GO_KR_SERVICE_KEY=should-not-override\n",
        encoding="utf-8",
    )

    env = load_desktop_env_files(
        bundle_root=tmp_path / "bundle",
        writable_root=writable_root,
        current_env={"DATA_GO_KR_SERVICE_KEY": "explicit-key"},
    )

    assert env["G2B_SERVICE_KEY"] == "local-key"
    assert env["DATA_GO_KR_SERVICE_KEY"] == "explicit-key"


def test_build_desktop_environment_sets_utf8_and_run_workspace(tmp_path: Path) -> None:
    from desktop.launcher import build_desktop_environment

    env = build_desktop_environment(
        bundle_root=tmp_path / "bundle",
        writable_root=tmp_path / "app",
        current_env={},
    )

    assert env["PYTHONUTF8"] == "1"
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert env["RUN_WORKSPACE_ROOT"] == str(tmp_path / "app" / "output" / "runs")
    assert env["LOCAL_APP_EXPOSE_INTERNAL_ERRORS"] == "1"


def test_desktop_requirements_include_windows_timezone_data() -> None:
    requirements = Path("requirements-desktop.txt").read_text(encoding="utf-8")

    assert "tzdata" in requirements


def test_build_app_url_points_to_frontend_app_root() -> None:
    from desktop.launcher import build_app_url

    assert build_app_url("127.0.0.1", 8765) == "http://127.0.0.1:8765/app/"


def test_build_desktop_return_button_script_links_back_to_app() -> None:
    from desktop.launcher import build_desktop_return_button_script

    script = build_desktop_return_button_script("http://127.0.0.1:8765/app/")

    assert "앱으로 돌아가기" in script
    assert "SynapDocViewServer" in script
    assert "http://127.0.0.1:8765/app/" in script
    assert "history.back()" in script
    assert "location.href" in script
    assert "notice-winner-return-button" in script


def test_inject_desktop_return_button_uses_window_evaluate_js() -> None:
    from desktop.launcher import inject_desktop_return_button

    calls: list[str] = []

    class FakeWindow:
        def evaluate_js(self, script: str) -> None:
            calls.append(script)

    inject_desktop_return_button(FakeWindow(), "http://127.0.0.1:8765/app/")

    assert len(calls) == 1
    assert "앱으로 돌아가기" in calls[0]


def test_build_desktop_environment_defaults_to_local_sqlite(tmp_path: Path) -> None:
    from desktop.launcher import build_desktop_environment

    bundle_root = tmp_path / "bundle"
    writable_root = tmp_path / "app"
    (bundle_root / "assets").mkdir(parents=True)
    (bundle_root / "assets" / "project_tracker_template.xlsx").write_bytes(b"template")

    env = build_desktop_environment(
        bundle_root=bundle_root,
        writable_root=writable_root,
        current_env={},
    )

    assert env["TRACKER_REPOSITORY_BACKEND"] == "sqlite"
    assert env["RUN_REPOSITORY_BACKEND"] == "sqlite"
    assert env["ARTIFACT_REPOSITORY_BACKEND"] == "sqlite"
    assert env["LOCAL_SQLITE_PATH"] == str(writable_root / "data" / "local.sqlite3")
    assert env["ARTIFACTS_ROOT"] == str(writable_root / "output" / "artifacts")
    assert env["TRACKER_TEMPLATE_PATH"] == str(
        bundle_root / "assets" / "project_tracker_template.xlsx"
    )


def test_build_desktop_environment_preserves_explicit_overrides(tmp_path: Path) -> None:
    from desktop.launcher import build_desktop_environment

    env = build_desktop_environment(
        bundle_root=tmp_path / "bundle",
        writable_root=tmp_path / "app",
        current_env={
            "LOCAL_SQLITE_PATH": "D:\\custom\\local.sqlite3",
            "TRACKER_REPOSITORY_BACKEND": "in_memory",
        },
    )

    assert env["LOCAL_SQLITE_PATH"] == "D:\\custom\\local.sqlite3"
    assert env["TRACKER_REPOSITORY_BACKEND"] == "in_memory"
    assert env["RUN_REPOSITORY_BACKEND"] == "sqlite"


def test_ensure_runtime_directories_creates_writable_storage(tmp_path: Path) -> None:
    from desktop.launcher import ensure_runtime_directories

    ensure_runtime_directories(tmp_path)

    assert (tmp_path / "data").is_dir()
    assert (tmp_path / "output" / "artifacts").is_dir()
    assert (tmp_path / "logs").is_dir()


def test_configure_desktop_logging_writes_to_server_log(tmp_path: Path, monkeypatch) -> None:
    from desktop.launcher import configure_desktop_logging

    monkeypatch.delenv("DESKTOP_SERVER_LOG_PATH", raising=False)

    log_path = configure_desktop_logging(tmp_path)

    assert log_path == tmp_path / "logs" / "server.log"
    assert log_path.parent.is_dir()
    assert log_path.exists()
    assert os.environ["DESKTOP_SERVER_LOG_PATH"] == str(log_path)
