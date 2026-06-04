from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from backend.api.app import _select_project_source_notice_row
from backend.api.app import _select_tracker_entry_source_notice_row
from backend.api.routers.tracker_read_handlers import view_tracker_entry_notice_file
from backend.services.notice_file_view_backend import load_notice_seed_row_by_bid


class _EmptyArtifactRepository:
    def list_artifacts(self, *, run_id):  # type: ignore[no-untyped-def]
        return []


class _SingleEntryRepository:
    def __init__(self, entry: dict[str, object]) -> None:
        self._entry = dict(entry)

    def get_entry(self, _entry_id):  # type: ignore[no-untyped-def]
        return dict(self._entry)


class NoticeFileViewBackendTests(unittest.TestCase):
    @patch("backend.services.notice_file_view_backend.collect_seed_rows_with_params")
    def test_load_notice_seed_row_by_bid_prefers_exact_bid_ord(self, collect_seed_rows_with_params) -> None:
        collect_seed_rows_with_params.return_value = SimpleNamespace(
            rows=[
                {"bid_no": "R26BK01311027", "bid_ord": "001", "spec_doc_url": "https://example.com/other.hwp"},
                {"bid_no": "R26BK01311027", "bid_ord": "000", "spec_doc_url": "https://example.com/notice.hwp"},
            ]
        )

        row = load_notice_seed_row_by_bid(bid_no="R26BK01311027", bid_ord="000")

        self.assertIsNotNone(row)
        self.assertEqual(row["bid_ord"], "000")
        self.assertEqual(row["spec_doc_url"], "https://example.com/notice.hwp")

    @patch("backend.services.notice_file_view_backend.collect_seed_rows_with_params")
    def test_load_notice_seed_row_by_bid_falls_back_to_first_row(self, collect_seed_rows_with_params) -> None:
        collect_seed_rows_with_params.return_value = SimpleNamespace(
            rows=[{"bid_no": "R26BK01311027", "bid_ord": "001", "spec_doc_url": "https://example.com/notice.hwp"}]
        )

        row = load_notice_seed_row_by_bid(bid_no="R26BK01311027", bid_ord="000")

        self.assertIsNotNone(row)
        self.assertEqual(row["bid_ord"], "001")

    @patch("backend.api.app.load_notice_seed_row_by_bid")
    @patch("backend.api.app._get_artifact_repository", return_value=_EmptyArtifactRepository())
    def test_select_tracker_entry_source_notice_row_falls_back_without_local_artifact(
        self,
        _get_artifact_repository,
        load_notice_seed_row_by_bid_mock,
    ) -> None:
        load_notice_seed_row_by_bid_mock.return_value = {"bid_no": "R26BK01311027", "bid_ord": "000"}

        row = _select_tracker_entry_source_notice_row(
            {
                "source_run_id": str(uuid4()),
                "source_bid_no": "R26BK01311027",
                "source_bid_ord": "000",
            }
        )

        self.assertEqual(row, {"bid_no": "R26BK01311027", "bid_ord": "000"})
        load_notice_seed_row_by_bid_mock.assert_called_once_with(bid_no="R26BK01311027", bid_ord="000")

    @patch("backend.api.app.load_notice_seed_row_by_bid")
    @patch("backend.api.app._get_artifact_repository", return_value=_EmptyArtifactRepository())
    def test_select_project_source_notice_row_falls_back_without_local_artifact(
        self,
        _get_artifact_repository,
        load_notice_seed_row_by_bid_mock,
    ) -> None:
        load_notice_seed_row_by_bid_mock.return_value = {"bid_no": "R26BK01311027", "bid_ord": "000"}

        row = _select_project_source_notice_row(
            {
                "issuer_name": "제주특별자치도",
                "source_json": {
                    "run_ids": [str(uuid4())],
                    "source_bid_no": "R26BK01311027",
                    "source_bid_ord": "000",
                },
            }
        )

        self.assertEqual(row, {"bid_no": "R26BK01311027", "bid_ord": "000"})
        load_notice_seed_row_by_bid_mock.assert_called_once_with(bid_no="R26BK01311027", bid_ord="000")

    @patch("backend.api.routers.tracker_read_handlers.support._select_tracker_entry_source_notice_row", return_value=None)
    @patch("backend.api.routers.tracker_read_handlers.support._get_tracker_repository")
    @patch("backend.api.routers.tracker_read_handlers.support._load_notice_view_helpers")
    def test_view_tracker_entry_notice_file_rebuilds_g2b_source_from_entry_bid_for_synap(
        self,
        load_notice_view_helpers,
        get_tracker_repository,
        _select_tracker_entry_source_notice_row,
    ) -> None:
        entry_id = uuid4()
        get_tracker_repository.return_value = _SingleEntryRepository(
            {
                "id": str(entry_id),
                "project_name": "Synap notice fallback",
                "source_bid_no": "R26BK01434430",
                "source_bid_ord": "000",
            }
        )
        seen_rows: list[dict[str, object] | None] = []

        def _select_primary_notice_attachment(row):  # type: ignore[no-untyped-def]
            seen_rows.append(row)
            if row and row.get("bid_no") == "R26BK01434430" and "g2b.go.kr" in str(row.get("notice_url") or ""):
                return {
                    "url": (
                        "https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do"
                        "?bidPbancNo=R26BK01434430&bidPbancOrd=000&fileSeq=1&fileType="
                    ),
                    "file_name": "notice.hwp",
                }
            return {}

        def _resolve_notice_viewer_url(**kwargs):  # type: ignore[no-untyped-def]
            self.assertEqual(kwargs["bid_no"], "R26BK01434430")
            self.assertEqual(kwargs["bid_ord"], "000")
            self.assertIn("fileSeq=1", kwargs["attachment_url"])
            return "https://www.g2b.go.kr/SynapDocViewServer/viewer/doc.html?key=synap-key"

        load_notice_view_helpers.return_value = {
            "build_notice_file_fallback_html": lambda **_kwargs: "<html>fallback</html>",
            "download_notice_attachment": lambda **_kwargs: (b"", ""),
            "infer_notice_attachment_suffix": lambda **_kwargs: "",
            "render_hwp_notice_html": lambda **_kwargs: None,
            "resolve_notice_viewer_url": _resolve_notice_viewer_url,
            "select_primary_notice_attachment": _select_primary_notice_attachment,
        }

        response = view_tracker_entry_notice_file(entry_id)

        self.assertEqual(response.status_code, 307)
        self.assertEqual(
            response.headers["location"],
            "https://www.g2b.go.kr/SynapDocViewServer/viewer/doc.html?key=synap-key",
        )
        self.assertEqual(seen_rows[0]["bid_no"], "R26BK01434430")
        self.assertIn("bidPbancNo=R26BK01434430", seen_rows[0]["notice_url"])

    @patch("backend.api.routers.tracker_read_handlers.support._select_tracker_entry_source_notice_row", return_value=None)
    @patch("backend.api.routers.tracker_read_handlers.support._get_tracker_repository")
    @patch("backend.api.routers.tracker_read_handlers.support._load_notice_view_helpers")
    def test_view_tracker_entry_notice_file_can_embed_synap_viewer_locally(
        self,
        load_notice_view_helpers,
        get_tracker_repository,
        _select_tracker_entry_source_notice_row,
    ) -> None:
        entry_id = uuid4()
        get_tracker_repository.return_value = _SingleEntryRepository(
            {
                "id": str(entry_id),
                "project_name": "Synap embedded notice",
                "source_bid_no": "R26BK01434430",
                "source_bid_ord": "000",
            }
        )

        def _select_primary_notice_attachment(_row):  # type: ignore[no-untyped-def]
            return {
                "url": (
                    "https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do"
                    "?bidPbancNo=R26BK01434430&bidPbancOrd=000&fileSeq=1&fileType="
                ),
                "file_name": "notice.hwp",
            }

        load_notice_view_helpers.return_value = {
            "build_notice_file_fallback_html": lambda **_kwargs: "<html>fallback</html>",
            "download_notice_attachment": lambda **_kwargs: (b"", ""),
            "infer_notice_attachment_suffix": lambda **_kwargs: "",
            "render_hwp_notice_html": lambda **_kwargs: None,
            "resolve_notice_viewer_url": lambda **_kwargs: "https://www.g2b.go.kr/SynapDocViewServer/viewer/doc.html?key=synap-key",
            "select_primary_notice_attachment": _select_primary_notice_attachment,
            "build_synap_viewer_embed_html": lambda **kwargs: f"<html><iframe src=\"{kwargs['viewer_url']}\"></iframe></html>",
        }

        response = view_tracker_entry_notice_file(entry_id, embed=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.media_type, "text/html")
        self.assertIn("synap-key", response.body.decode("utf-8"))

    @patch("backend.api.routers.tracker_read_handlers.support._select_tracker_entry_source_notice_row", return_value=None)
    @patch("backend.api.routers.tracker_read_handlers.support._get_tracker_repository")
    @patch("backend.api.routers.tracker_read_handlers.support._load_notice_view_helpers")
    def test_view_tracker_entry_notice_file_desktop_returns_immediate_loading_page(
        self,
        load_notice_view_helpers,
        get_tracker_repository,
        _select_tracker_entry_source_notice_row,
    ) -> None:
        entry_id = uuid4()
        get_tracker_repository.return_value = _SingleEntryRepository(
            {
                "id": str(entry_id),
                "project_name": "Desktop notice",
                "source_bid_no": "R26BK01434430",
                "source_bid_ord": "000",
            }
        )
        resolve_calls: list[dict[str, object]] = []
        load_notice_view_helpers.return_value = {
            "build_notice_file_fallback_html": lambda **_kwargs: "<html>fallback</html>",
            "build_desktop_notice_loading_html": lambda **kwargs: (
                f"<html>{kwargs['title']}|{kwargs['redirect_url']}</html>"
            ),
            "download_notice_attachment": lambda **_kwargs: (b"", ""),
            "infer_notice_attachment_suffix": lambda **_kwargs: "",
            "render_hwp_notice_html": lambda **_kwargs: None,
            "resolve_notice_viewer_url": lambda **kwargs: resolve_calls.append(kwargs) or "",
            "select_primary_notice_attachment": lambda _row: {},
        }

        response = view_tracker_entry_notice_file(entry_id, desktop=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.media_type, "text/html")
        body = response.body.decode("utf-8")
        self.assertIn("Desktop notice", body)
        self.assertIn(f"/api/tracker-entries/{entry_id}/notice-file-view", body)
        self.assertEqual(resolve_calls, [])

    def test_build_desktop_notice_loading_html_returns_with_browser_history(self) -> None:
        from backend.services.notice_file_view_backend import build_desktop_notice_loading_html

        body = build_desktop_notice_loading_html(
            title="Desktop notice",
            redirect_url="/api/tracker-entries/entry-1/notice-file-view",
            app_url="/app/",
        )

        self.assertIn("앱으로 돌아가기", body)
        self.assertIn("history.back()", body)
        self.assertIn("window.location.replace", body)
        self.assertIn("/api/tracker-entries/entry-1/notice-file-view", body)

    def test_resolve_notice_viewer_url_uses_local_cache_without_g2b_request(self) -> None:
        from backend.services.notice_file_view_backend import resolve_notice_viewer_url

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "notice_viewer_cache.json"
            cache_path.write_text(
                json.dumps(
                    {
                        "R26BK01434430|000|1|": (
                            "https://www.g2b.go.kr/SynapDocViewServer/viewer/doc.html?key=cached"
                        )
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"NOTICE_VIEWER_CACHE_PATH": str(cache_path)}):
                with patch("backend.services.notice_file_view_backend.requests.post") as post:
                    viewer_url = resolve_notice_viewer_url(
                        bid_no="R26BK01434430",
                        bid_ord="000",
                        attachment_url=(
                            "https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do"
                            "?bidPbancNo=R26BK01434430&bidPbancOrd=000&fileSeq=1&fileType="
                        ),
                    )

        self.assertEqual(viewer_url, "https://www.g2b.go.kr/SynapDocViewServer/viewer/doc.html?key=cached")
        post.assert_not_called()

    @patch("backend.api.routers.tracker_read_handlers.support._load_notice_view_helpers")
    def test_open_tracker_entry_notice_file_external_opens_local_redirect_route(self, load_notice_view_helpers) -> None:
        from backend.api.routers.tracker_read_handlers import open_tracker_entry_notice_file_external

        entry_id = uuid4()
        opened_urls: list[str] = []
        load_notice_view_helpers.return_value = {
            "open_external_browser_url": lambda url: opened_urls.append(url) or True,
        }

        response = open_tracker_entry_notice_file_external(
            entry_id,
            base_url="http://127.0.0.1:8765/app/",
        )

        self.assertEqual(response["opened"], True)
        self.assertEqual(
            opened_urls,
            [f"http://127.0.0.1:8765/api/tracker-entries/{entry_id}/notice-file-view"],
        )


if __name__ == "__main__":
    unittest.main()
