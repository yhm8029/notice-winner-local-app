from __future__ import annotations

import unittest

from backend.services.native_export_backend import _extract_notice_fields


class NativeCostAuxiliaryServiceTests(unittest.TestCase):
    def test_extract_notice_fields_blanks_construction_cost_for_auxiliary_service_project(self) -> None:
        text = "\n".join(
            [
                "제6회 서울식물원 식재설계 공모전 운영 대행용역",
                "계약금액 100,000,000원",
                "문의 전시교육과 02-2104-9788",
            ]
        )

        fields = _extract_notice_fields(
            title="제6회 서울식물원 식재설계 공모전 운영 대행용역",
            text=text,
            project_name="제6회 서울식물원 식재설계 공모전 운영 대행용역",
            org_name="서울특별시 서울식물원",
        )

        self.assertEqual(fields.construction_cost, "")


if __name__ == "__main__":
    unittest.main()
