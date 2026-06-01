from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from backend.services.artifact_files import read_tracking_workbook_rows
from tests.api.test_phase1_api_behavior import _project_tracker_run_payload
from tests.api.test_phase1_api_behavior import ApiServer


class SalesClaimApiTests(unittest.TestCase):
    def test_sales_claim_export_downloads_my_scope_workbook(self) -> None:
        with ApiServer() as server:
            create_status, create_payload = server.request_json("POST", "/api/runs", payload=_project_tracker_run_payload())
            self.assertEqual(create_status, 201)

            parent_run = server.wait_for_run(create_payload["id"], target_statuses={"success"})
            self.assertEqual(parent_run["status"], "success")

            tracker_status, tracker_payload = server.request_json(
                "POST",
                f"/api/runs/{create_payload['id']}/tracker-export",
            )
            self.assertEqual(tracker_status, 202)

            tracker_run = server.wait_for_run(tracker_payload["id"], target_statuses={"success"})
            self.assertEqual(tracker_run["status"], "success")

            summaries_status, summaries_payload = server.request_json(
                "GET",
                f"/api/tracker-entry-summaries?source_tracker_run_id={tracker_payload['id']}&page=1&page_size=20",
            )
            self.assertEqual(summaries_status, 200)
            entry = next((item for item in summaries_payload["items"] if item.get("project_id")), None)
            self.assertIsNotNone(entry)
            assert entry is not None

            claim_status, claim_payload = server.request_json(
                "POST",
                f"/api/sales-claims/projects/{entry['project_id']}/claim",
                payload={
                    "source_entry_id": entry["id"],
                    "source_run_id": tracker_payload["id"],
                    "project_name": entry["project_name"],
                    "estimated_amount_text": entry["building_automation_estimated_amount"],
                },
            )
            self.assertEqual(claim_status, 200)

            patch_status, patch_payload = server.request_json(
                "PATCH",
                f"/api/sales-claims/projects/{entry['project_id']}",
                payload={"sales_note": "follow up complete"},
            )
            self.assertEqual(patch_status, 200)
            self.assertEqual(patch_payload["claim"]["sales_note"], "follow up complete")

            export_status, export_body, export_headers = server.request_bytes(
                "GET",
                "/api/sales-claims/export?scope=my",
            )
            self.assertEqual(export_status, 200)
            self.assertIn(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                export_headers.get("content-type", ""),
            )
            self.assertIn("my_active_sales.xlsx", export_headers.get("content-disposition", ""))

            with tempfile.TemporaryDirectory() as tmp_dir:
                workbook_path = Path(tmp_dir) / "sales-claims.xlsx"
                workbook_path.write_bytes(export_body)
                rows = read_tracking_workbook_rows(workbook_path)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["project_name"], entry["project_name"])
            self.assertEqual(rows[0]["progress_note"], "follow up complete")
            self.assertEqual(
                rows[0]["building_automation_estimated_amount"],
                entry["building_automation_estimated_amount"],
            )
            self.assertEqual(
                rows[0]["manager_name"],
                claim_payload["claim"]["owner_display_name"] or claim_payload["claim"]["owner_email"],
            )

    def test_home_bootstrap_returns_sales_and_tracker_first_page(self) -> None:
        with ApiServer() as server:
            create_status, create_payload = server.request_json("POST", "/api/runs", payload=_project_tracker_run_payload())
            self.assertEqual(create_status, 201)

            parent_run = server.wait_for_run(create_payload["id"], target_statuses={"success"})
            self.assertEqual(parent_run["status"], "success")

            tracker_status, tracker_payload = server.request_json(
                "POST",
                f"/api/runs/{create_payload['id']}/tracker-export",
            )
            self.assertEqual(tracker_status, 202)

            tracker_run = server.wait_for_run(tracker_payload["id"], target_statuses={"success"})
            self.assertEqual(tracker_run["status"], "success")

            summaries_status, summaries_payload = server.request_json(
                "GET",
                f"/api/tracker-entry-summaries?source_tracker_run_id={tracker_payload['id']}&page=1&page_size=20",
            )
            self.assertEqual(summaries_status, 200)
            entry = next((item for item in summaries_payload["items"] if item.get("project_id")), None)
            self.assertIsNotNone(entry)
            assert entry is not None

            claim_status, _claim_payload = server.request_json(
                "POST",
                f"/api/sales-claims/projects/{entry['project_id']}/claim",
                payload={
                    "source_entry_id": entry["id"],
                    "source_run_id": tracker_payload["id"],
                    "project_name": entry["project_name"],
                    "estimated_amount_text": entry["building_automation_estimated_amount"],
                },
            )
            self.assertEqual(claim_status, 200)

            bootstrap_status, bootstrap_payload = server.request_json(
                "GET",
                "/api/home-bootstrap",
            )
            self.assertEqual(bootstrap_status, 200)
            self.assertEqual(len(bootstrap_payload["company_items"]), 1)
            self.assertEqual(len(bootstrap_payload["my_items"]), 1)
            self.assertGreaterEqual(bootstrap_payload["tracker_first_page"]["total"], 1)
            self.assertEqual(bootstrap_payload["tracker_first_page"]["page"], 1)
            self.assertEqual(bootstrap_payload["tracker_first_page"]["page_size"], 20)
            self.assertTrue(bootstrap_payload["tracker_first_page"]["items"])

    def test_sales_claim_overview_returns_my_and_company_items(self) -> None:
        with ApiServer() as server:
            create_status, create_payload = server.request_json("POST", "/api/runs", payload=_project_tracker_run_payload())
            self.assertEqual(create_status, 201)

            parent_run = server.wait_for_run(create_payload["id"], target_statuses={"success"})
            self.assertEqual(parent_run["status"], "success")

            tracker_status, tracker_payload = server.request_json(
                "POST",
                f"/api/runs/{create_payload['id']}/tracker-export",
            )
            self.assertEqual(tracker_status, 202)

            tracker_run = server.wait_for_run(tracker_payload["id"], target_statuses={"success"})
            self.assertEqual(tracker_run["status"], "success")

            summaries_status, summaries_payload = server.request_json(
                "GET",
                f"/api/tracker-entry-summaries?source_tracker_run_id={tracker_payload['id']}&page=1&page_size=20",
            )
            self.assertEqual(summaries_status, 200)
            entry = next((item for item in summaries_payload["items"] if item.get("project_id")), None)
            self.assertIsNotNone(entry)
            assert entry is not None

            claim_status, claim_payload = server.request_json(
                "POST",
                f"/api/sales-claims/projects/{entry['project_id']}/claim",
                payload={
                    "source_entry_id": entry["id"],
                    "source_run_id": tracker_payload["id"],
                    "project_name": entry["project_name"],
                    "estimated_amount_text": entry["building_automation_estimated_amount"],
                },
            )
            self.assertEqual(claim_status, 200)

            overview_status, overview_payload = server.request_json(
                "GET",
                "/api/sales-claims/overview",
            )
            self.assertEqual(overview_status, 200)
            self.assertEqual(len(overview_payload["company_items"]), 1)
            self.assertEqual(len(overview_payload["my_items"]), 1)
            self.assertEqual(overview_payload["company_items"][0]["project_id"], entry["project_id"])
            self.assertEqual(overview_payload["organization_users"], [])

    def test_close_won_requires_contract_amount_text(self) -> None:
        with ApiServer() as server:
            create_status, create_payload = server.request_json("POST", "/api/runs", payload=_project_tracker_run_payload())
            self.assertEqual(create_status, 201)

            parent_run = server.wait_for_run(create_payload["id"], target_statuses={"success"})
            self.assertEqual(parent_run["status"], "success")

            tracker_status, tracker_payload = server.request_json(
                "POST",
                f"/api/runs/{create_payload['id']}/tracker-export",
            )
            self.assertEqual(tracker_status, 202)

            tracker_run = server.wait_for_run(tracker_payload["id"], target_statuses={"success"})
            self.assertEqual(tracker_run["status"], "success")

            summaries_status, summaries_payload = server.request_json(
                "GET",
                f"/api/tracker-entry-summaries?source_tracker_run_id={tracker_payload['id']}&page=1&page_size=20",
            )
            self.assertEqual(summaries_status, 200)
            entry = next((item for item in summaries_payload["items"] if item.get("project_id")), None)
            self.assertIsNotNone(entry)
            assert entry is not None

            claim_status, _claim_payload = server.request_json(
                "POST",
                f"/api/sales-claims/projects/{entry['project_id']}/claim",
                payload={
                    "source_entry_id": entry["id"],
                    "source_run_id": tracker_payload["id"],
                    "project_name": entry["project_name"],
                    "estimated_amount_text": entry["building_automation_estimated_amount"],
                },
            )
            self.assertEqual(claim_status, 200)

            missing_amount_status, missing_amount_payload = server.request_json(
                "POST",
                f"/api/sales-claims/projects/{entry['project_id']}/close",
                payload={"outcome": "won", "contract_amount_text": "", "force": False},
            )
            self.assertEqual(missing_amount_status, 400)
            self.assertIn("contract_amount_text", str(missing_amount_payload))

            won_status, won_payload = server.request_json(
                "POST",
                f"/api/sales-claims/projects/{entry['project_id']}/close",
                payload={"outcome": "won", "contract_amount_text": "1.2억원", "force": False},
            )
            self.assertEqual(won_status, 200)
            self.assertEqual(won_payload["claim"]["claim_status"], "won")
            self.assertIn("계약금액 1.2억원", won_payload["claim"]["sales_note"])

    def test_sales_claim_lifecycle(self) -> None:
        with ApiServer() as server:
            create_status, create_payload = server.request_json("POST", "/api/runs", payload=_project_tracker_run_payload())
            self.assertEqual(create_status, 201)

            parent_run = server.wait_for_run(create_payload["id"], target_statuses={"success"})
            self.assertEqual(parent_run["status"], "success")

            tracker_status, tracker_payload = server.request_json(
                "POST",
                f"/api/runs/{create_payload['id']}/tracker-export",
            )
            self.assertEqual(tracker_status, 202)

            tracker_run = server.wait_for_run(tracker_payload["id"], target_statuses={"success"})
            self.assertEqual(tracker_run["status"], "success")

            summaries_status, summaries_payload = server.request_json(
                "GET",
                f"/api/tracker-entry-summaries?source_tracker_run_id={tracker_payload['id']}&page=1&page_size=20",
            )
            self.assertEqual(summaries_status, 200)
            self.assertGreaterEqual(summaries_payload["total"], 1)

            entry = next((item for item in summaries_payload["items"] if item.get("project_id")), None)
            self.assertIsNotNone(entry)
            assert entry is not None

            claim_status, claim_payload = server.request_json(
                "POST",
                f"/api/sales-claims/projects/{entry['project_id']}/claim",
                payload={
                    "source_entry_id": entry["id"],
                    "source_run_id": tracker_payload["id"],
                    "project_name": entry["project_name"],
                    "estimated_amount_text": entry["building_automation_estimated_amount"],
                },
            )
            self.assertEqual(claim_status, 200)
            self.assertTrue(claim_payload["changed"])
            self.assertEqual(claim_payload["claim"]["project_id"], entry["project_id"])

            same_claim_status, same_claim_payload = server.request_json(
                "POST",
                f"/api/sales-claims/projects/{entry['project_id']}/claim",
                payload={
                    "source_entry_id": entry["id"],
                    "source_run_id": tracker_payload["id"],
                    "project_name": entry["project_name"],
                    "estimated_amount_text": entry["building_automation_estimated_amount"],
                },
            )
            self.assertEqual(same_claim_status, 200)
            self.assertFalse(same_claim_payload["changed"])

            list_status, list_payload = server.request_json(
                "GET",
                f"/api/sales-claims?project_id={entry['project_id']}",
            )
            self.assertEqual(list_status, 200)
            self.assertEqual(len(list_payload["items"]), 1)

            patch_status, patch_payload = server.request_json(
                "PATCH",
                f"/api/sales-claims/projects/{entry['project_id']}",
                payload={"sales_note": "첫 통화 완료"},
            )
            self.assertEqual(patch_status, 200)
            self.assertEqual(patch_payload["claim"]["sales_note"], "첫 통화 완료")

            summary_status, summary_payload = server.request_json("GET", "/api/sales-claims/summary-by-user")
            self.assertEqual(summary_status, 200)
            self.assertEqual(len(summary_payload["items"]), 1)
            self.assertEqual(summary_payload["items"][0]["active_project_count"], 1)
            self.assertEqual(summary_payload["items"][0]["projects"][0]["sales_note"], "첫 통화 완료")

            admin_delete_status, admin_delete_payload = server.request_json(
                "PATCH",
                f"/api/sales-claims/projects/{entry['project_id']}",
                payload={"sales_note": "", "force_admin_override": True},
            )
            self.assertEqual(admin_delete_status, 200)
            self.assertEqual(admin_delete_payload["claim"]["sales_note"], "")

            close_status, close_payload = server.request_json(
                "POST",
                f"/api/sales-claims/projects/{entry['project_id']}/close",
                payload={"outcome": "lost", "force": False},
            )
            self.assertEqual(close_status, 200)
            self.assertEqual(close_payload["claim"]["claim_status"], "lost")
            self.assertIsNotNone(close_payload["claim"]["closed_at"])

            summary_after_close_status, summary_after_close_payload = server.request_json(
                "GET",
                "/api/sales-claims/summary-by-user",
            )
            self.assertEqual(summary_after_close_status, 200)
            self.assertEqual(summary_after_close_payload["items"], [])

            release_status, release_payload = server.request_json(
                "POST",
                f"/api/sales-claims/projects/{entry['project_id']}/release",
                payload={"force": False},
            )
            self.assertEqual(release_status, 200)
            self.assertFalse(release_payload["claim"]["is_active"])

            list_status_after, list_payload_after = server.request_json(
                "GET",
                f"/api/sales-claims?project_id={entry['project_id']}",
            )
            self.assertEqual(list_status_after, 200)
            self.assertEqual(list_payload_after["items"], [])
