from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.api.schemas import ReportJobCreateRequest
from backend.services import related_notice_query_runtime as runtime
from backend.services import related_notice_query_runtime_impl as impl


class RelatedNoticeQueryRuntimeServiceTests(unittest.TestCase):
    def test_project_search_name_strips_design_suffix(self) -> None:
        self.assertEqual(
            runtime._project_search_name(
                "\ubaa9\uc7ac\ub204\ub9ac\uc13c\ud130 \uac74\ub9bd\uc0ac\uc5c5 \uae30\ubcf8 \ubc0f \uc2e4\uc2dc\uc124\uacc4 \uacf5\ubaa8(\uc81c\uc548)"
            ),
            "\ubaa9\uc7ac\ub204\ub9ac\uc13c\ud130 \uac74\ub9bd\uc0ac\uc5c5",
        )

    def test_query_variants_include_stem_and_head(self) -> None:
        variants = runtime._build_related_notice_query_variants(
            "\uc758\uc0ac\uc219\uc18c \uc2e0\ucd95\uacf5\uc0ac \uc124\uacc4\uacf5\ubaa8 \uacf5\uace0"
        )

        self.assertIn("\uc758\uc0ac\uc219\uc18c \uc2e0\ucd95\uacf5\uc0ac", variants)
        self.assertIn("\uc758\uc0ac\uc219\uc18c \uc2e0\ucd95", variants)
        self.assertIn("\uc758\uc0ac\uc219\uc18c", variants)

    def test_query_variants_expand_discipline_branch(self) -> None:
        variants = runtime._build_related_notice_query_variants(
            "\uc5ec\ud765 \ub450\ub4dc\ub9bc\uc13c\ud130 \uc870\uc131\uc0ac\uc5c5 \uac74\ucd95\uc124\uacc4\uacf5\ubaa8"
        )

        self.assertIn("\uc5ec\ud765 \ub450\ub4dc\ub9bc\uc13c\ud130 \uc870\uc131\uc0ac\uc5c5", variants)
        self.assertIn("\uc5ec\ud765 \ub450\ub4dc\ub9bc\uc13c\ud130 \uc870\uc131\uc0ac\uc5c5 \uac74\ucd95", variants)
        self.assertIn("\uc5ec\ud765 \ub450\ub4dc\ub9bc\uc13c\ud130 \uc870\uc131\uc0ac\uc5c5 \uac74\ucd95\uacf5\uc0ac", variants)

    def test_primary_queries_prefer_stem_for_construction(self) -> None:
        project = {
            "project_name": "\ub18d\uc0b0\ubb3c\uc885\ud569\uac00\uacf5\uc13c\ud130 \uac74\ub9bd\uacf5\uc0ac \uc124\uacc4\uacf5\ubaa8",
            "project_search_name": "\ub18d\uc0b0\ubb3c\uc885\ud569\uac00\uacf5\uc13c\ud130 \uac74\ub9bd\uacf5\uc0ac",
            "latest_notice_title": "\ub18d\uc0b0\ubb3c\uc885\ud569\uac00\uacf5\uc13c\ud130 \uac74\ub9bd\uacf5\uc0ac \uc124\uacc4\uacf5\ubaa8",
        }

        scopes = runtime._build_related_notice_primary_scopes(project)
        queries = runtime._build_related_notice_primary_queries(project, "construction")

        self.assertEqual(scopes[0], "construction")
        self.assertGreaterEqual(len(queries), 2)
        self.assertEqual(queries[0], "\ub18d\uc0b0\ubb3c\uc885\ud569\uac00\uacf5\uc13c\ud130 \uac74\ub9bd")
        self.assertIn("\ub18d\uc0b0\ubb3c\uc885\ud569\uac00\uacf5\uc13c\ud130", queries)

    def test_score_accepts_discipline_split_same_project(self) -> None:
        project = {
            "project_name": "\uc758\uc0ac\uc219\uc18c \uc2e0\ucd95\uacf5\uc0ac \uc124\uacc4\uacf5\ubaa8 \uacf5\uace0",
            "project_search_name": "\uc758\uc0ac\uc219\uc18c \uc2e0\ucd95\uacf5\uc0ac",
            "_project_match_key": "\uc758\uc0ac\uc219\uc18c\uc2e0\ucd95\uacf5\uc0ac",
        }
        row = {
            "project_name": "\uac15\uc9c4\uc758\ub8cc\uc6d0 \uc758\uc0ac \uc219\uc18c \uc2e0\ucd95 \uae30\uacc4\uacf5\uc0ac",
            "org_name": "\uc804\ub77c\ub0a8\ub3c4",
            "announce_date": "20250613",
            "bid_no": "R25BK00903695",
            "bid_ord": "000",
        }

        score, candidate_search_name, reason = runtime._score_related_notice_match(project, row)

        self.assertGreaterEqual(score, 20)
        self.assertTrue(candidate_search_name)
        self.assertTrue("same_stem" in reason or "stem_overlap" in reason)

    def test_report_job_command_wrapper_preserves_artifact_diff_args(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app_root = Path(tmpdir)
            frontend_dir = app_root / "frontend"
            frontend_dir.mkdir()
            script_path = app_root / "scripts" / "phase1_artifact_diff_runner.py"
            script_path.parent.mkdir(parents=True)
            script_path.write_text("print('ok')", encoding="utf-8")
            gui_root = app_root / "gui-root"
            gui_root.mkdir()
            default_seed_csv = gui_root / "tests" / "winner_pipeline_seed_input.csv"
            default_seed_csv.parent.mkdir(parents=True)
            default_seed_csv.write_text("seed", encoding="utf-8")

            impl.APP_ROOT = app_root
            impl.FRONTEND_DIR = frontend_dir
            impl.REPORT_FILES = {"phase1-artifact-diff": "phase1-artifact-diff-report.json"}
            impl.REPORT_SCRIPT_FILES = {"phase1-artifact-diff": "phase1_artifact_diff_runner.py"}
            impl.REPORT_SCRIPT_ENV_OVERRIDES = {"phase1-artifact-diff": "REPORT_SCRIPT_PHASE1_ARTIFACT_DIFF"}

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

            command, output_path, resolved_gui_root, seed_csv = impl._build_report_job_command(payload)

        self.assertEqual(output_path, app_root / "output" / "phase1-artifact-diff-report.json")
        self.assertEqual(resolved_gui_root, gui_root.resolve())
        self.assertEqual(seed_csv, str(default_seed_csv))
        self.assertIn("--gui-source-root", command)
        self.assertIn("--seed-csv", command)
        self.assertIn("--seed-limit", command)


if __name__ == "__main__":
    unittest.main()
