from __future__ import annotations

import unittest

from backend.services.native_gui_rules import ContactObservation
from backend.services.native_gui_rules import extract_contact_from_notice_text
from backend.services.native_gui_rules import extract_contact_resolution_from_notice_text
from backend.services.native_gui_rules import resolve_contact_from_observations


class ContactResolverV1Tests(unittest.TestCase):
    def test_resolve_contact_from_observations_prefers_owner_contact_over_management(self) -> None:
        observations = [
            ContactObservation(
                candidate_text="마실와이드/02-6010-1022",
                contact="마실와이드/02-6010-1022",
                dept="마실와이드",
                phone="02-6010-1022",
                phase_hint="notice",
                role_hint="entrusted_management",
                owner_side_hint="no",
                owner_side_basis_hint="unknown",
                is_anchor=True,
                score=30,
            ),
            ContactObservation(
                candidate_text="관광진흥과/054-420-6136",
                contact="관광진흥과/054-420-6136",
                dept="관광진흥과",
                phone="054-420-6136",
                phase_hint="notice",
                role_hint="owner_contact",
                owner_side_hint="yes",
                owner_side_basis_hint="explicit_owner_org_match",
                is_anchor=True,
                score=40,
            ),
        ]
        resolved = resolve_contact_from_observations(observations)

        self.assertEqual(resolved.status, "resolved")
        self.assertEqual(resolved.contact, "관광진흥과/054-420-6136")
        self.assertEqual(resolved.role, "owner_contact")
        self.assertEqual(resolved.owner_side, "yes")

    def test_resolve_contact_from_observations_marks_management_only_as_no_owner_candidate(self) -> None:
        observations = [
            ContactObservation(
                candidate_text="공모관리기관 마실/02-6010-1022",
                contact="공모관리기관 마실/02-6010-1022",
                dept="공모관리기관 마실",
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

    def test_resolve_contact_from_observations_accepts_school_admin_office_as_owner(self) -> None:
        observations = [
            ContactObservation(
                candidate_text="행정실/051-518-7923",
                contact="행정실/051-518-7923",
                dept="행정실",
                phone="051-518-7923",
                phase_hint="notice",
                role_hint="owner_contact",
                owner_side_hint="yes",
                owner_side_basis_hint="school_admin_office",
                is_anchor=True,
                score=30,
            )
        ]
        resolved = resolve_contact_from_observations(observations)

        self.assertEqual(resolved.status, "resolved")
        self.assertEqual(resolved.contact, "행정실/051-518-7923")
        self.assertEqual(resolved.owner_side_basis, "school_admin_office")

    def test_resolve_contact_from_observations_rejects_submission_only_contact(self) -> None:
        observations = [
            ContactObservation(
                candidate_text="접수처/043-201-2582",
                contact="접수처/043-201-2582",
                dept="접수처",
                phone="043-201-2582",
                phase_hint="submission",
                role_hint="submission_contact",
                owner_side_hint="uncertain",
                owner_side_basis_hint="unknown",
                is_anchor=True,
                score=40,
            )
        ]
        resolved = resolve_contact_from_observations(observations)

        self.assertEqual(resolved.status, "no_owner_candidate")
        self.assertEqual(resolved.contact, "")

    def test_extract_contact_from_notice_text_returns_blank_for_management_only(self) -> None:
        text = "\n".join(
            [
                "공모관리기관 마실와이드 02-6010-1022",
                "설계공모 홈페이지 참고",
            ]
        )

        resolved = extract_contact_resolution_from_notice_text(text, "경상남도 남해군")
        self.assertEqual(resolved.status, "review")
        self.assertEqual(resolved.contact, "")


if __name__ == "__main__":
    unittest.main()
