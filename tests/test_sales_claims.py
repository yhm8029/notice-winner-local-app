from __future__ import annotations

import unittest
from uuid import UUID
from uuid import uuid4

from backend.sales_claims import InMemorySalesClaimStore
from backend.sales_claims import SalesActor
from backend.sales_claims import SalesClaimConflictError
from backend.sales_claims import SalesClaimInvalidTransitionError
from backend.sales_claims import SalesClaimPermissionError
from backend.sales_claims import SALES_CLAIM_STATUS_LOST


ORGANIZATION_ID = UUID("7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001")


class SalesClaimStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = InMemorySalesClaimStore()
        self.project_id = uuid4()
        self.entry_id = uuid4()
        self.run_id = uuid4()
        self.owner = SalesActor(
            organization_id=ORGANIZATION_ID,
            user_id=uuid4(),
            email="user1@example.com",
            display_name="User 1",
            role="org_member",
        )
        self.other_user = SalesActor(
            organization_id=ORGANIZATION_ID,
            user_id=uuid4(),
            email="user2@example.com",
            display_name="User 2",
            role="org_member",
        )
        self.admin = SalesActor(
            organization_id=ORGANIZATION_ID,
            user_id=uuid4(),
            email="admin@example.com",
            display_name="Admin",
            role="org_admin",
        )

    def test_claim_project_conflicts_for_other_user(self) -> None:
        changed, first_claim = self.store.claim_project(
            actor=self.owner,
            project_id=self.project_id,
            source_entry_id=self.entry_id,
            source_run_id=self.run_id,
            project_name="Alpha Project",
            estimated_amount_text="1.00억원~1.50억원",
        )

        self.assertTrue(changed)
        self.assertEqual(first_claim.owner_email, "user1@example.com")

        with self.assertRaises(SalesClaimConflictError):
            self.store.claim_project(
                actor=self.other_user,
                project_id=self.project_id,
                source_entry_id=self.entry_id,
                source_run_id=self.run_id,
                project_name="Alpha Project",
                estimated_amount_text="1.00억원~1.50억원",
            )

    def test_same_owner_reclaim_is_idempotent(self) -> None:
        first_changed, first_claim = self.store.claim_project(
            actor=self.owner,
            project_id=self.project_id,
            source_entry_id=self.entry_id,
            source_run_id=self.run_id,
            project_name="Alpha Project",
            estimated_amount_text="0.50억원~0.80억원",
        )
        second_changed, second_claim = self.store.claim_project(
            actor=self.owner,
            project_id=self.project_id,
            source_entry_id=self.entry_id,
            source_run_id=self.run_id,
            project_name="Alpha Project",
            estimated_amount_text="0.50억원~0.80억원",
        )

        self.assertTrue(first_changed)
        self.assertFalse(second_changed)
        self.assertEqual(first_claim.claimed_at, second_claim.claimed_at)

    def test_only_owner_can_update_sales_note(self) -> None:
        self.store.claim_project(
            actor=self.owner,
            project_id=self.project_id,
            source_entry_id=self.entry_id,
            source_run_id=self.run_id,
            project_name="Alpha Project",
            estimated_amount_text="1.00억원~1.50억원",
        )

        updated = self.store.update_sales_note(
            actor=self.owner,
            project_id=self.project_id,
            sales_note="Phone verification complete",
        )
        self.assertEqual(updated.sales_note, "Phone verification complete")

        with self.assertRaises(SalesClaimPermissionError):
            self.store.update_sales_note(
                actor=self.other_user,
                project_id=self.project_id,
                sales_note="Attempted overwrite",
            )

    def test_admin_can_force_override_sales_note(self) -> None:
        self.store.claim_project(
            actor=self.owner,
            project_id=self.project_id,
            source_entry_id=self.entry_id,
            source_run_id=self.run_id,
            project_name="Alpha Project",
            estimated_amount_text="1.00억원~1.50억원",
        )

        updated = self.store.update_sales_note(
            actor=self.admin,
            project_id=self.project_id,
            sales_note="Admin cleanup",
            force_admin_override=True,
        )

        self.assertEqual(updated.sales_note, "Admin cleanup")

    def test_owner_or_admin_can_release(self) -> None:
        self.store.claim_project(
            actor=self.owner,
            project_id=self.project_id,
            source_entry_id=self.entry_id,
            source_run_id=self.run_id,
            project_name="Alpha Project",
            estimated_amount_text="1.00억원~1.50억원",
        )

        with self.assertRaises(SalesClaimPermissionError):
            self.store.release_project(
                actor=self.other_user,
                project_id=self.project_id,
            )

        released = self.store.release_project(
            actor=self.admin,
            project_id=self.project_id,
            force=True,
        )
        self.assertFalse(released.is_active)
        self.assertIsNotNone(released.released_at)

    def test_summary_by_user_aggregates_amounts(self) -> None:
        self.store.claim_project(
            actor=self.owner,
            project_id=self.project_id,
            source_entry_id=self.entry_id,
            source_run_id=self.run_id,
            project_name="Alpha Project",
            estimated_amount_text="1.00억원~1.50억원",
        )
        self.store.claim_project(
            actor=self.owner,
            project_id=uuid4(),
            source_entry_id=uuid4(),
            source_run_id=self.run_id,
            project_name="Beta Project",
            estimated_amount_text="0.50억원~0.80억원",
        )

        summary = self.store.summarize_by_user(organization_id=ORGANIZATION_ID)

        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["user_email"], "user1@example.com")
        self.assertEqual(summary[0]["active_project_count"], 2)
        self.assertEqual(summary[0]["total_low_krw"], 150000000)
        self.assertEqual(summary[0]["total_high_krw"], 230000000)
        self.assertEqual(len(summary[0]["projects"]), 2)

    def test_transfer_moves_project_to_new_owner(self) -> None:
        _, first_claim = self.store.claim_project(
            actor=self.owner,
            project_id=self.project_id,
            source_entry_id=self.entry_id,
            source_run_id=self.run_id,
            project_name="Alpha Project",
            estimated_amount_text="1.00억원~1.50억원",
        )

        transferred = self.store.transfer_project(
            actor=self.owner,
            project_id=self.project_id,
            target_user_id=self.other_user.user_id,
            target_email=self.other_user.email,
            target_display_name=self.other_user.display_name,
        )

        self.assertEqual(transferred.owner_email, self.other_user.email)
        self.assertEqual(transferred.owner_display_name, self.other_user.display_name)
        self.assertGreaterEqual(transferred.current_owner_assigned_at, first_claim.claimed_at)
        self.assertIn("이관", transferred.sales_note)

        summary = self.store.summarize_by_user(organization_id=ORGANIZATION_ID)
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["user_email"], self.other_user.email)
        self.assertEqual(summary[0]["projects"][0]["owner_elapsed_days"], 0)

    def test_closed_claim_is_excluded_from_active_summary(self) -> None:
        self.store.claim_project(
            actor=self.owner,
            project_id=self.project_id,
            source_entry_id=self.entry_id,
            source_run_id=self.run_id,
            project_name="Alpha Project",
            estimated_amount_text="1.00억원~1.50억원",
        )

        closed = self.store.close_project(
            actor=self.owner,
            project_id=self.project_id,
            outcome="lost",
        )

        self.assertEqual(closed.claim_status, SALES_CLAIM_STATUS_LOST)
        self.assertIsNotNone(closed.closed_at)
        self.assertIn("영업 종료 처리", closed.sales_note)

        with self.assertRaises(SalesClaimInvalidTransitionError):
            self.store.update_sales_note(
                actor=self.owner,
                project_id=self.project_id,
                sales_note="추가 메모",
            )

        summary = self.store.summarize_by_user(organization_id=ORGANIZATION_ID)
        self.assertEqual(summary, [])

    def test_won_close_records_contract_amount_in_sales_note(self) -> None:
        self.store.claim_project(
            actor=self.owner,
            project_id=self.project_id,
            source_entry_id=self.entry_id,
            source_run_id=self.run_id,
            project_name="Alpha Project",
            estimated_amount_text="1.00억원~1.50억원",
        )

        closed = self.store.close_project(
            actor=self.owner,
            project_id=self.project_id,
            outcome="won",
            contract_amount_text="1.3억원",
        )

        self.assertEqual(closed.claim_status, "won")
        self.assertIn("계약 완료 처리", closed.sales_note)
        self.assertIn("계약금액 1.3억원", closed.sales_note)

    def test_single_value_estimate_is_preserved_as_same_low_high(self) -> None:
        changed, claim = self.store.claim_project(
            actor=self.owner,
            project_id=self.project_id,
            source_entry_id=self.entry_id,
            source_run_id=self.run_id,
            project_name="Alpha Project",
            estimated_amount_text="12억원",
        )

        self.assertTrue(changed)
        self.assertEqual(claim.estimated_amount_low_krw, 1200000000)
        self.assertEqual(claim.estimated_amount_high_krw, 1200000000)
