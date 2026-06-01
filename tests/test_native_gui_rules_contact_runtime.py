from __future__ import annotations

import unittest

from backend.services.native_gui_rules_contact_resolution_runtime import ContactObservation
from backend.services.native_gui_rules_contact_resolution_runtime import resolve_contact_from_observations


class NativeGuiRulesContactRuntimeTests(unittest.TestCase):
    def test_resolve_contact_from_observations_returns_review_for_tied_owner_candidates(self) -> None:
        observations = [
            ContactObservation(
                candidate_text="관광과/054-420-6136",
                contact="관광과/054-420-6136",
                dept="관광과",
                phone="054-420-6136",
                phase_hint="notice",
                role_hint="owner_contact",
                owner_side_hint="yes",
                owner_side_basis_hint="explicit_owner_org_match",
                is_anchor=True,
                score=40,
                evidence_block_index=1,
            ),
            ContactObservation(
                candidate_text="회계과/054-420-6137",
                contact="회계과/054-420-6137",
                dept="회계과",
                phone="054-420-6137",
                phase_hint="notice",
                role_hint="owner_contact",
                owner_side_hint="yes",
                owner_side_basis_hint="explicit_owner_org_match",
                is_anchor=True,
                score=40,
                evidence_block_index=2,
            ),
        ]

        resolved = resolve_contact_from_observations(observations)

        self.assertEqual(resolved.status, "review")
        self.assertEqual(resolved.reason, "auto_pick_conflict")

    def test_resolve_contact_from_observations_marks_management_only_as_no_owner_candidate(self) -> None:
        observations = [
            ContactObservation(
                candidate_text="공모관리기관/02-6010-1022",
                contact="공모관리기관/02-6010-1022",
                dept="공모관리기관",
                phone="02-6010-1022",
                phase_hint="notice",
                role_hint="entrusted_management",
                owner_side_hint="no",
                owner_side_basis_hint="unknown",
                is_anchor=True,
                score=40,
            )
        ]

        resolved = resolve_contact_from_observations(observations)

        self.assertEqual(resolved.status, "no_owner_candidate")
        self.assertEqual(resolved.contact, "")


if __name__ == "__main__":
    unittest.main()
