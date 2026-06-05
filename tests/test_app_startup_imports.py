from __future__ import annotations

import json
import subprocess
import sys
import unittest


class AppStartupImportTests(unittest.TestCase):
    def test_backend_services_module_does_not_export_pipeline_execution_helpers(self) -> None:
        import backend.services as services

        self.assertFalse(hasattr(services, "safely_execute_project_tracker"))
        self.assertFalse(hasattr(services, "queue_tracker_export_run_for_parent"))
        self.assertFalse(hasattr(services, "synthetic_debug_enabled"))
        self.assertFalse(hasattr(services, "resolve_artifact_path"))

    def test_native_tracker_backend_does_not_eagerly_import_workbook_reader(self) -> None:
        import backend.services.native_tracker_backend as native_tracker_backend

        self.assertFalse(hasattr(native_tracker_backend, "read_tracking_workbook_rows"))

    def test_tracker_diagnostic_backend_does_not_eagerly_import_artifact_path_helper(self) -> None:
        import backend.services.tracker_diagnostic_backend as tracker_diagnostic_backend

        self.assertFalse(hasattr(tracker_diagnostic_backend, "resolve_artifact_path"))

    def test_tracker_diagnostic_backend_does_not_eagerly_import_report_schema_models(self) -> None:
        import backend.services.tracker_diagnostic_backend as tracker_diagnostic_backend

        self.assertFalse(hasattr(tracker_diagnostic_backend, "TrackerMissingFieldItem"))
        self.assertFalse(hasattr(tracker_diagnostic_backend, "TrackerMissingReportItem"))
        self.assertFalse(hasattr(tracker_diagnostic_backend, "TrackerMissingReportSummary"))

    def test_app_exposes_lazy_openpyxl_loader(self) -> None:
        from backend.api import app as app_module

        workbook_cls = app_module._load_openpyxl_workbook_class()

        self.assertEqual(workbook_cls.__name__, "Workbook")

    def test_app_exposes_lazy_run_execution_loader(self) -> None:
        from backend.api import app as app_module

        queue_fn, execute_fn = app_module._load_run_execution_helpers()

        self.assertEqual(queue_fn.__name__, "queue_tracker_export_run_for_parent")
        self.assertEqual(execute_fn.__name__, "safely_execute_project_tracker")

    def test_app_exposes_lazy_notice_view_loader(self) -> None:
        from backend.api import app as app_module

        helpers = app_module._load_notice_view_helpers()

        self.assertEqual(helpers["build_notice_view_payload"].__name__, "build_notice_view_payload")
        self.assertEqual(helpers["download_notice_attachment"].__name__, "download_notice_attachment")
        self.assertEqual(helpers["render_hwp_notice_html"].__name__, "render_hwp_notice_html")

    def test_backfill_conflicts_router_import_does_not_eagerly_load_app(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json, sys; "
                    "from backend.api.routers import backfill_conflicts; "
                    "print(json.dumps({"
                    '"backend.api.app": "backend.api.app" in sys.modules, '
                    '"backend.api.routers.backfill_conflicts": "backend.api.routers.backfill_conflicts" in sys.modules'
                    "}))"
                ),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        loaded_modules = json.loads(result.stdout)

        self.assertFalse(loaded_modules["backend.api.app"])
        self.assertTrue(loaded_modules["backend.api.routers.backfill_conflicts"])

    def test_runs_and_reports_router_imports_do_not_eagerly_load_app(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json, sys; "
                    "from backend.api.routers import reports, runs; "
                    "print(json.dumps({"
                    '"backend.api.app": "backend.api.app" in sys.modules, '
                    '"backend.api.routers.runs": "backend.api.routers.runs" in sys.modules, '
                    '"backend.api.routers.reports": "backend.api.routers.reports" in sys.modules'
                    "}))"
                ),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        loaded_modules = json.loads(result.stdout)

        self.assertFalse(loaded_modules["backend.api.app"])
        self.assertTrue(loaded_modules["backend.api.routers.runs"])
        self.assertTrue(loaded_modules["backend.api.routers.reports"])

    def test_core_router_import_does_not_eagerly_load_app(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json, sys; "
                    "from backend.api.routers import core; "
                    "print(json.dumps({"
                    '"backend.api.app": "backend.api.app" in sys.modules, '
                    '"backend.api.routers.core": "backend.api.routers.core" in sys.modules'
                    "}))"
                ),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        loaded_modules = json.loads(result.stdout)

        self.assertFalse(loaded_modules["backend.api.app"])
        self.assertTrue(loaded_modules["backend.api.routers.core"])

    def test_sales_claims_router_import_does_not_eagerly_load_app(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json, sys; "
                    "from backend.api.routers import sales_claims; "
                    "print(json.dumps({"
                    '"backend.api.app": "backend.api.app" in sys.modules, '
                    '"backend.api.routers.sales_claims": "backend.api.routers.sales_claims" in sys.modules'
                    "}))"
                ),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        loaded_modules = json.loads(result.stdout)

        self.assertFalse(loaded_modules["backend.api.app"])
        self.assertTrue(loaded_modules["backend.api.routers.sales_claims"])

    def test_app_exposes_lazy_artifact_file_helpers(self) -> None:
        from backend.api import app as app_module

        helpers = app_module._load_artifact_file_helpers()

        self.assertEqual(helpers["resolve_artifact_path"].__name__, "resolve_artifact_path")
        self.assertEqual(helpers["build_tracking_download_workbook_bytes"].__name__, "build_tracking_download_workbook_bytes")
        self.assertIn("tracking_export_fieldnames", helpers)
        self.assertEqual(app_module.build_tracking_download_workbook_bytes.__name__, "build_tracking_download_workbook_bytes")

    def test_app_exposes_lazy_artifact_preview_helpers(self) -> None:
        from backend.api import app as app_module

        helpers = app_module._load_artifact_preview_helpers()

        self.assertEqual(helpers["build_artifact_item_payload"].__name__, "build_artifact_item_payload")
        self.assertEqual(
            helpers["build_artifact_preview_payload_for_artifact_row"].__name__,
            "build_artifact_preview_payload_for_artifact_row",
        )
        self.assertEqual(
            helpers["build_artifact_preview_payload"].__name__,
            "build_artifact_preview_payload",
        )

    def test_app_preserves_legacy_backend_api_exports_after_modularization(self) -> None:
        from backend.api import app as app_module

        expected_exports = (
            "_build_tracker_download_job_cache_key",
            "_get_snapshot_project_aggregate",
            "_json_safe_copy",
        )

        for export_name in expected_exports:
            self.assertTrue(
                hasattr(app_module, export_name),
                msg=f"backend.api.app should continue exposing {export_name}",
            )
