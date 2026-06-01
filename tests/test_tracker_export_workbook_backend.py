from __future__ import annotations

import unittest
import threading
from uuid import uuid4

from backend.services.tracker_export_workbook_backend import can_cache_tracker_export_workbook
from backend.services.tracker_export_workbook_backend import get_or_build_cached_tracker_export_workbook_bytes
from backend.services.tracker_export_workbook_backend import list_tracker_entries_for_export
from backend.services.tracker_export_workbook_backend import warm_default_user_tracker_export_workbook


class TrackerExportWorkbookBackendTests(unittest.TestCase):
    def test_list_tracker_entries_for_export_uses_global_scope_dependencies(self) -> None:
        calls: list[tuple[str, object]] = []

        def is_global_tracker_scope_fn(**kwargs: object) -> bool:
            calls.append(("scope", kwargs))
            return True

        def filter_tracker_rows_for_global_scope_fn(rows: object, **kwargs: object) -> list[dict[str, str]]:
            calls.append(("filter", (rows, kwargs)))
            return [{"progress_note": "filtered"}]

        def load_global_tracker_rows_fn() -> list[dict[str, str]]:
            calls.append(("load_global", None))
            return [{"progress_note": "raw"}]

        def normalize_tracker_rows_for_presentation_fn(rows: object) -> list[dict[str, str]]:
            calls.append(("normalize", rows))
            return [{"progress_note": str(rows[0]["progress_note"]).upper()}]  # type: ignore[index]

        def load_all_tracker_entries_for_export_fn(**_: object) -> list[dict[str, str]]:
            raise AssertionError("non-global loader should not be used")

        rows = list_tracker_entries_for_export(
            q="query",
            region="seoul",
            exclude_auxiliary_titles=True,
            edited_only=True,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
            is_global_tracker_scope_fn=is_global_tracker_scope_fn,
            filter_tracker_rows_for_global_scope_fn=filter_tracker_rows_for_global_scope_fn,
            load_global_tracker_rows_fn=load_global_tracker_rows_fn,
            normalize_tracker_rows_for_presentation_fn=normalize_tracker_rows_for_presentation_fn,
            load_all_tracker_entries_for_export_fn=load_all_tracker_entries_for_export_fn,
        )

        self.assertEqual(rows, [{"progress_note": "FILTERED"}])
        self.assertEqual([entry[0] for entry in calls], ["scope", "load_global", "filter", "normalize"])

    def test_list_tracker_entries_for_export_uses_non_global_loader(self) -> None:
        calls: list[tuple[str, object]] = []

        def normalize_tracker_rows_for_presentation_fn(rows: object) -> list[dict[str, str]]:
            calls.append(("normalize", rows))
            return [{"progress_note": str(rows[0]["progress_note"]).upper()}]  # type: ignore[index]

        def load_all_tracker_entries_for_export_fn(**kwargs: object) -> list[dict[str, str]]:
            calls.append(("load_all", kwargs))
            return [{"progress_note": "loaded"}]

        rows = list_tracker_entries_for_export(
            q="query",
            region="busan",
            exclude_auxiliary_titles=False,
            edited_only=False,
            source_run_id=uuid4(),
            source_tracker_run_id=None,
            sheet_name="Sheet 1",
            section_name="Section A",
            is_global_tracker_scope_fn=lambda **_: False,
            filter_tracker_rows_for_global_scope_fn=lambda *_args, **_kwargs: [],
            load_global_tracker_rows_fn=lambda: [],
            normalize_tracker_rows_for_presentation_fn=normalize_tracker_rows_for_presentation_fn,
            load_all_tracker_entries_for_export_fn=load_all_tracker_entries_for_export_fn,
        )

        self.assertEqual(rows, [{"progress_note": "LOADED"}])
        self.assertEqual([entry[0] for entry in calls], ["load_all", "normalize"])

    def test_can_cache_tracker_export_workbook_only_for_global_xlsx_scope(self) -> None:
        self.assertTrue(
            can_cache_tracker_export_workbook(
                format="xlsx",
                q="search text",
                region="seoul",
                edited_only=True,
                source_run_id=None,
                source_tracker_run_id=None,
                sheet_name="",
                section_name="",
            )
        )
        self.assertFalse(
            can_cache_tracker_export_workbook(
                format="csv",
                q="",
                region="",
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=None,
                sheet_name="",
                section_name="",
            )
        )
        self.assertFalse(
            can_cache_tracker_export_workbook(
                format="xlsx",
                q="",
                region="",
                edited_only=False,
                source_run_id=uuid4(),
                source_tracker_run_id=None,
                sheet_name="",
                section_name="",
            )
        )

    def test_can_cache_tracker_export_workbook_treats_whitespace_only_sheet_scope_as_global(self) -> None:
        self.assertTrue(
            can_cache_tracker_export_workbook(
                format="xlsx",
                q="",
                region="",
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=None,
                sheet_name="   ",
                section_name="\t",
            )
        )

    def test_get_or_build_cached_tracker_export_workbook_retries_with_live_cache_serial(self) -> None:
        cache: dict[str, tuple[float, bytes]] = {}
        cache_build_events: dict[str, threading.Event] = {}
        serial_state = {"value": 0}
        calls = {"count": 0}

        def list_rows(**_: object) -> list[dict[str, str]]:
            calls["count"] += 1
            if calls["count"] == 1:
                serial_state["value"] = 1
            return [{"progress_note": f"row-{calls['count']}"}]

        payload = get_or_build_cached_tracker_export_workbook_bytes(
            q="",
            region="",
            exclude_auxiliary_titles=True,
            edited_only=False,
            blank_progress_note=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
            cache_lock=threading.Lock(),
            cache=cache,
            cache_build_events=cache_build_events,
            cache_serial_fn=lambda: serial_state["value"],
            cache_ttl_sec=60.0,
            cache_wait_timeout_sec=0.01,
            cache_max_entries=4,
            list_tracker_entries_for_export_fn=list_rows,
            build_tracking_download_workbook_bytes_fn=lambda *, rows: str(rows[0]["progress_note"]).encode("utf-8"),
        )

        self.assertEqual(payload, b"row-2")
        self.assertEqual(calls["count"], 2)

    def test_can_cache_tracker_export_workbook_uses_injected_global_scope_fn(self) -> None:
        scope_calls: list[dict[str, object]] = []

        def is_global_tracker_scope_fn(**kwargs: object) -> bool:
            scope_calls.append(kwargs)
            return True

        self.assertTrue(
            can_cache_tracker_export_workbook(
                format="xlsx",
                q="query",
                region="region",
                edited_only=True,
                source_run_id=uuid4(),
                source_tracker_run_id=None,
                sheet_name="sheet",
                section_name="section",
                is_global_tracker_scope_fn=is_global_tracker_scope_fn,
            )
        )
        self.assertEqual(len(scope_calls), 1)
        self.assertEqual(scope_calls[0]["sheet_name"], "sheet")

    def test_warm_default_user_tracker_export_workbook_swallow_exceptions(self) -> None:
        messages: list[str] = []

        class StubLogger:
            def exception(self, message: str) -> None:
                messages.append(message)

        def raise_error(**_: object) -> bytes:
            raise RuntimeError("boom")

        warm_default_user_tracker_export_workbook(
            get_or_build_cached_tracker_export_workbook_bytes_fn=raise_error,
            logger=StubLogger(),
        )

        self.assertEqual(messages, ["tracker export workbook warm failed"])
