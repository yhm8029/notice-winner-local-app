from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.api.app import _filter_self_related_notice_payload_items


class RelatedNoticeSelfFilterTests(unittest.TestCase):
    def test_filter_self_related_notice_payload_items_removes_source_notice(self) -> None:
        project = {"project_name": "demo project"}
        items = [
            {
                "project_name": "demo project",
                "bid_no": "20240100912",
                "bid_ord": "000",
            },
            {
                "project_name": "demo project follow-up",
                "bid_no": "20240100913",
                "bid_ord": "000",
            },
        ]

        with patch("backend.api.app._project_source_notice_keys", return_value={("20240100912", "000")}):
            filtered = _filter_self_related_notice_payload_items(project, items)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["bid_no"], "20240100913")

    def test_filter_self_related_notice_payload_items_keeps_items_when_no_source_keys(self) -> None:
        project = {"project_name": "demo project"}
        items = [{"project_name": "demo project", "bid_no": "20240100912", "bid_ord": "000"}]

        with patch("backend.api.app._project_source_notice_keys", return_value=set()):
            filtered = _filter_self_related_notice_payload_items(project, items)

        self.assertEqual(filtered, items)


if __name__ == "__main__":
    unittest.main()
