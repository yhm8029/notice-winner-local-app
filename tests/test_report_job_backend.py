from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.api.schemas import ReportJobCreateRequest
from backend.services.report_job_backend import build_report_job_command
from backend.services.report_job_backend import discover_gui_source_root
from backend.services.report_job_backend import resolve_report_script_path
from backend.services.report_job_backend import resolve_reports_root
from backend.services.report_job_backend import trim_log_excerpt


class ReportJobBackendTests(unittest.TestCase):
    def test_resolve_reports_root_uses_relative_env_under_app_root(self) -> None:
        app_root = Path("C:/workspace/app")

        resolved = resolve_reports_root(raw_root="output-reports", app_root=app_root)

        self.assertEqual(resolved, app_root / "output-reports")

    def test_resolve_report_script_path_prefers_existing_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app_root = Path(tmpdir)
            override_path = app_root / "custom_runner.py"
            override_path.write_text("print('ok')", encoding="utf-8")

            resolved = resolve_report_script_path(
                report_name="phase1-equivalence",
                app_root=app_root,
                report_script_files={"phase1-equivalence": "phase1_equivalence_runner.py"},
                report_script_env_overrides={"phase1-equivalence": "REPORT_SCRIPT_PHASE1_EQUIVALENCE"},
                env_get_fn=lambda name: str(override_path) if name == "REPORT_SCRIPT_PHASE1_EQUIVALENCE" else "",
                not_found_fn=lambda message: (_ for _ in ()).throw(AssertionError(message)),
            )

        self.assertEqual(resolved, override_path)

    def test_discover_gui_source_root_prefers_explicit_existing_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app_root = Path(tmpdir)
            explicit = app_root / "gui-root"
            explicit.mkdir()

            resolved = discover_gui_source_root(
                explicit=str(explicit),
                app_root=app_root,
                env_get_fn=lambda name: "",
            )

        self.assertEqual(resolved, explicit.resolve())

    def test_trim_log_excerpt_keeps_tail(self) -> None:
        self.assertEqual(trim_log_excerpt("abcdef", max_chars=4), "cdef")

    def test_build_report_job_command_includes_artifact_diff_args(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app_root = Path(tmpdir)
            reports_root = app_root / "output"
            script_path = app_root / "scripts" / "phase1_artifact_diff_runner.py"
            script_path.parent.mkdir(parents=True)
            script_path.write_text("print('ok')", encoding="utf-8")
            gui_root = app_root / "gui-root"
            gui_root.mkdir()
            default_seed_csv = gui_root / "tests" / "winner_pipeline_seed_input.csv"
            default_seed_csv.parent.mkdir(parents=True)
            default_seed_csv.write_text("seed", encoding="utf-8")

            payload = ReportJobCreateRequest(
                report_name="phase1-artifact-diff",
                gui_source_root=str(gui_root),
                seed_csv="",
                seed_limit=5,
                start_date="20250101",
                end_date="20250131",
                contract_date_hint="20250115",
                bid_no="BID-1",
                notice_title="demo notice",
                demand_org="demo org",
                rows_per_page=50,
                max_pages=2,
                api_scope="service",
            )

            command, output_path, resolved_gui_root, seed_csv = build_report_job_command(
                payload,
                sys_executable="python",
                app_root=app_root,
                report_files={"phase1-artifact-diff": "phase1-artifact-diff-report.json"},
                resolve_reports_root_fn=lambda: reports_root,
                resolve_report_script_path_fn=lambda report_name: script_path,
                discover_gui_source_root_fn=lambda explicit: gui_root,
                validation_error_fn=lambda message: (_ for _ in ()).throw(AssertionError(message)),
            )

        self.assertEqual(output_path, reports_root / "phase1-artifact-diff-report.json")
        self.assertEqual(resolved_gui_root, gui_root)
        self.assertEqual(seed_csv, str(default_seed_csv))
        self.assertIn("--gui-source-root", command)
        self.assertIn("--seed-csv", command)
        self.assertIn("--seed-limit", command)
        self.assertIn("--api-scope", command)


if __name__ == "__main__":
    unittest.main()
