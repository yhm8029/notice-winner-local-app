from __future__ import annotations

from datetime import datetime
from datetime import timezone
from uuid import uuid4
import unittest
from unittest.mock import Mock

from backend.api.app import _describe_home_bootstrap_snapshot_state
from backend.api.app import _json_safe_copy
from backend.services.home_bootstrap_backend import build_home_bootstrap_tracker_first_page
from backend.repositories.supabase_home_bootstrap_snapshots import SupabaseHomeBootstrapSnapshotRepository


class HomeBootstrapPayloadTests(unittest.TestCase):
    def test_json_safe_copy_serializes_nested_datetime_and_uuid(self) -> None:
        payload = {
            "generated_at": datetime(2026, 3, 29, 8, 0, tzinfo=timezone.utc),
            "tracker_first_page": {
                "items": [
                    {
                        "id": uuid4(),
                        "updated_at": datetime(2026, 3, 29, 8, 1, tzinfo=timezone.utc),
                    }
                ]
            },
        }

        encoded = _json_safe_copy(payload)

        self.assertIsInstance(encoded["generated_at"], str)
        self.assertIsInstance(encoded["tracker_first_page"]["items"][0]["id"], str)
        self.assertIsInstance(encoded["tracker_first_page"]["items"][0]["updated_at"], str)

    def test_home_bootstrap_snapshot_repository_serializes_datetime_timestamp(self) -> None:
        raw = datetime(2026, 3, 29, 8, 0, tzinfo=timezone.utc)
        encoded = SupabaseHomeBootstrapSnapshotRepository._serialize_timestamp(raw)
        self.assertIsInstance(encoded, str)

    def test_describe_home_bootstrap_snapshot_state_rejects_malformed_payload(self) -> None:
        snapshot = {
            "snapshot_version": 3,
            "generated_at": "2026-03-29T00:00:00+00:00",
            "payload_json": {
                "snapshot_version": 3,
                "generated_at": "2026-03-29T00:00:00+00:00",
                "company_items": [{"x": 1}],
                "organization_users": [],
                "tracker_first_page": {
                    "items": [{"id": "1"}],
                    "page": 1,
                    "page_size": 20,
                    "total": 1,
                    "sort_contract": {"mode": "default", "order_by": ["updated_at_desc", "id_desc"]},
                },
            },
        }

        self.assertEqual(_describe_home_bootstrap_snapshot_state(snapshot), "payload_invalid")

    def test_describe_home_bootstrap_snapshot_state_rejects_stale_tracker_sort_contract(self) -> None:
        snapshot = {
            "snapshot_version": 3,
            "generated_at": "2026-03-29T00:00:00+00:00",
            "payload_json": {
                "snapshot_version": 3,
                "generated_at": "2026-03-29T00:00:00+00:00",
                "company_items": [],
                "organization_users": [],
                "tracker_first_page": {
                    "items": [{"id": "1", "project_name": "First Project"}],
                    "page": 1,
                    "page_size": 20,
                    "total": 1,
                    "sort_contract": {
                        "mode": "default",
                        "order_by": ["updated_at_desc", "id_desc"],
                    },
                },
            },
        }

        self.assertEqual(_describe_home_bootstrap_snapshot_state(snapshot), "payload_invalid")

    def test_build_home_bootstrap_tracker_first_page_uses_opening_scheduled_date_desc_default_sort_contract(self) -> None:
        rows = [
            {
                "id": "third",
                "project_name": "Third Project",
                "opening_scheduled_date": "",
                "updated_at": "2026-04-14T03:00:00+00:00",
            },
            {
                "id": "second",
                "project_name": "Second Project",
                "opening_scheduled_date": "2026-03-02",
                "updated_at": "2026-04-14T03:00:00+00:00",
            },
            {
                "id": "first",
                "project_name": "First Project",
                "opening_scheduled_date": "2026-04-01",
                "updated_at": "2026-04-14T01:00:00+00:00",
            },
        ]
        load_global_tracker_rows = Mock(return_value=rows)
        filtered_rows = [
            {
                "id": "first",
                "project_name": "First Project",
                "opening_scheduled_date": "2026-04-01",
                "updated_at": "2026-04-14T01:00:00+00:00",
            },
            {
                "id": "second",
                "project_name": "Second Project",
                "opening_scheduled_date": "2026-03-02",
                "updated_at": "2026-04-14T03:00:00+00:00",
            },
            {
                "id": "third",
                "project_name": "Third Project",
                "opening_scheduled_date": "",
                "updated_at": "2026-04-14T03:00:00+00:00",
            },
        ]
        filter_tracker_rows_for_global_scope = Mock(return_value=filtered_rows)

        page = build_home_bootstrap_tracker_first_page(
            load_global_tracker_rows=load_global_tracker_rows,
            filter_tracker_rows_for_global_scope=filter_tracker_rows_for_global_scope,
            page_size=2,
            model_to_json_dict=lambda item: item,
            to_tracker_entry_summary_model=lambda item: item,
        )

        filter_tracker_rows_for_global_scope.assert_called_once_with(
            rows,
            q="",
            region="",
            exclude_auxiliary_titles=True,
            edited_only=False,
        )
        self.assertEqual([item["id"] for item in page["items"]], ["first", "second"])
        self.assertEqual(
            page["sort_contract"]["order_by"],
            ["opening_scheduled_date_desc", "updated_at_desc", "id_desc"],
        )
