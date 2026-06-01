from __future__ import annotations

import unittest
from unittest.mock import patch

import requests

from backend.services.native_contract_lookup import get_last_contract_lookup_meta
from backend.services.native_contract_lookup import resolve_contract_by_bid_no


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class NativeContractLookupTests(unittest.TestCase):
    def test_to_lookup_result_prefers_documented_contract_fields(self) -> None:
        payload = {
            "response": {
                "body": {
                    "items": {
                        "item": {
                            "ntceNo": "R25BK00569527",
                            "cntrctNm": "함양소방서 산악구조대 신축사업 설계공모",
                            "corpList": "[1^주계약업체^단독^핀건축사사무소^대표^대한민국^100^채권자^담당자^1234567890]",
                            "cntrctDate": "2025-04-07",
                            "cntrctDeptNm": "소방예산장비과",
                            "cntrctDeptTelNo": "055-211-5695",
                            "cntrctOfclNm": "홍길동",
                            "thtmCntrctAmt": "199100000",
                            "cntrctBgnDate": "2025-04-07",
                            "cntrctEndDate": "2025-11-03",
                        }
                    }
                }
            }
        }

        with patch("backend.services.native_contract_lookup.resolve_service_key", return_value="fake-key"), patch(
            "backend.services.native_contract_lookup.requests.get",
            return_value=_FakeResponse(payload),
        ):
            result = resolve_contract_by_bid_no(
                bid_no="R25BK00569527",
                project_name_norm="함양소방서 산악구조대 신축사업 설계공모",
                announce_date="20250115",
            )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.contract_name, "핀건축사사무소")
        self.assertEqual(result.contract_date, "2025-04-07")
        self.assertEqual(result.contract_amount, "199100000")
        self.assertEqual(result.dept_name, "소방예산장비과")
        self.assertEqual(result.officer_name, "홍길동")
        self.assertEqual(result.officer_tel, "055-211-5695")
        self.assertEqual(result.contract_period_text, "2025-04-07 ~ 2025-11-03")

    def test_resolve_contract_by_bid_no_falls_back_to_lofin(self) -> None:
        g2b_empty = {"response": {"body": {"items": []}}}
        lofin_payload = {
            "RESULT": {"CODE": "INFO-000", "MESSAGE": "OK"},
            "data": [
                {
                    "ctrtLdgrMngNo": "L-1",
                    "ctrtTrgtNm": "경상남도교육청 함양도서관 이전 신축 설계공모",
                    "smzCtrtYmd": "20250324",
                    "cltNm": "주식회사 와이피디자인그룹건축사사무소",
                    "ctrtTotTottAmt": "547520000",
                    "lafNm": "경상남도교육청",
                }
            ],
        }

        def _fake_get(url: str, params: dict[str, object], timeout: float, headers=None):
            if "lofin365.go.kr" in url:
                return _FakeResponse(lofin_payload)
            return _FakeResponse(g2b_empty)

        def _fake_post(url: str, headers: dict[str, str], data: str, timeout: float):
            return _FakeResponse({"dataList": []})

        with patch("backend.services.native_contract_lookup.resolve_service_key", return_value="fake-g2b-key"), patch.dict(
            "os.environ",
            {"LOFIN_OPENAPI_KEY": "fake-lofin-key"},
            clear=False,
        ), patch(
            "backend.services.native_contract_lookup._resolve_hub_result_hit",
            return_value=None,
        ), patch(
            "backend.services.native_contract_lookup.requests.get",
            side_effect=_fake_get,
        ), patch(
            "backend.services.native_contract_lookup.requests.post",
            side_effect=_fake_post,
        ):
            result = resolve_contract_by_bid_no(
                bid_no="R25BK00554120",
                project_name_norm="경상남도교육청 함양도서관 이전 신축 설계공모",
                announce_date="20250106",
            )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.contract_name, "주식회사 와이피디자인그룹건축사사무소")
        self.assertEqual(result.contract_date, "20250324")
        self.assertEqual(result.contract_amount, "547520000")
        self.assertEqual(result.source_type, "lofin_api")

    def test_resolve_contract_by_bid_no_falls_back_to_eais_for_general_org(self) -> None:
        g2b_empty = {"response": {"body": {"items": []}}}
        eais_list = {
            "dataList": [
                {
                    "pssrpPblancSeqno": "A-1",
                    "pssrpPblancNm": "양산소방서 119구조대 신축사업 설계공모",
                    "pssrpCntrwkAmt": "3838000000",
                    "pssrpKikNm": "경상남도",
                }
            ]
        }
        eais_detail = {
            "data": {
                "pssrpPblancNm": "양산소방서 119구조대 신축사업 설계공모",
                "winPrdctPresnatnDate": "2025-03-25",
                "pssrpCntrwkAmt": "3838000000",
                "pssrpKikNm": "경상남도",
            }
        }
        eais_participants = {
            "dataMap": {
                "pssrpPartcptnList": [
                    {
                        "pssrpPartinWnpzCd": "1",
                        "pssrpPartinOfficeNm": "어반차건축사사무소&에스에이건축사사무소",
                    }
                ]
            }
        }

        def _fake_get(url: str, params: dict[str, object], timeout: float, headers=None):
            return _FakeResponse(g2b_empty)

        def _fake_post(url: str, headers: dict[str, str], data: str, timeout: float):
            if url.endswith("AWPAIA01R02"):
                return _FakeResponse(eais_list)
            if url.endswith("AWPAIA01R03"):
                return _FakeResponse(eais_detail)
            if url.endswith("AWPAIA01R05"):
                return _FakeResponse(eais_participants)
            return _FakeResponse({}, status_code=404)

        with patch("backend.services.native_contract_lookup.resolve_service_key", return_value="fake-g2b-key"), patch.dict(
            "os.environ",
            {"LOFIN_OPENAPI_KEY": ""},
            clear=False,
        ), patch(
            "backend.services.native_contract_lookup.requests.get",
            side_effect=_fake_get,
        ), patch(
            "backend.services.native_contract_lookup.requests.post",
            side_effect=_fake_post,
        ):
            result = resolve_contract_by_bid_no(
                bid_no="R25BK00555555",
                project_name_norm="양산소방서 119구조대 신축사업 설계공모",
                announce_date="20250115",
                org_name="경상남도",
            )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.contract_name, "어반차건축사사무소&에스에이건축사사무소")
        self.assertEqual(result.contract_date, "2025-03-25")
        self.assertEqual(result.contract_amount, "3838000000")
        self.assertEqual(result.source_type, "eais_web")

    def test_resolve_contract_by_bid_no_uses_powershell_fallback_on_lofin_ssl_error(self) -> None:
        g2b_empty = {"response": {"body": {"items": []}}}
        lofin_payload = {
            "RESULT": {"CODE": "INFO-000", "MESSAGE": "OK"},
            "data": [
                {
                    "ctrtLdgrMngNo": "L-2",
                    "ctrtTrgtNm": "경상남도교육청 함양도서관 이전 신축 설계공모",
                    "smzCtrtYmd": "20250324",
                    "cltNm": "주식회사 와이피디자인그룹건축사사무소",
                    "ctrtTotTottAmt": "547520000",
                    "lafNm": "경상남도교육청",
                }
            ],
        }

        def _fake_get(url: str, params: dict[str, object], timeout: float, headers=None):
            if "lofin365.go.kr" in url:
                raise requests.exceptions.SSLError("handshake failure")
            return _FakeResponse(g2b_empty)

        def _fake_post(url: str, headers: dict[str, str], data: str, timeout: float):
            return _FakeResponse({"dataList": []})

        with patch("backend.services.native_contract_lookup.resolve_service_key", return_value="fake-g2b-key"), patch.dict(
            "os.environ",
            {"LOFIN_OPENAPI_KEY": "fake-lofin-key"},
            clear=False,
        ), patch(
            "backend.services.native_contract_lookup._resolve_hub_result_hit",
            return_value=None,
        ), patch(
            "backend.services.native_contract_lookup.requests.get",
            side_effect=_fake_get,
        ), patch(
            "backend.services.native_contract_lookup._get_json_via_powershell",
            return_value=lofin_payload,
        ), patch(
            "backend.services.native_contract_lookup.requests.post",
            side_effect=_fake_post,
        ) as ps_fallback:
            result = resolve_contract_by_bid_no(
                bid_no="R25BK00554120",
                project_name_norm="경상남도교육청 함양도서관 이전 신축 설계공모",
                announce_date="20250106",
            )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.contract_name, "주식회사 와이피디자인그룹건축사사무소")
        self.assertEqual(result.source_type, "lofin_api")
        ps_fallback.assert_called()

    def test_resolve_contract_by_bid_no_prefers_eais_before_lofin_for_education_org(self) -> None:
        eais_result = object()

        with patch(
            "backend.services.native_contract_lookup._resolve_eais_contract_hit",
            return_value=eais_result,
        ) as eais_hit, patch(
            "backend.services.native_contract_lookup._resolve_lofin_contract_hit",
            side_effect=AssertionError("education org should not call lofin first"),
        ), patch(
            "backend.services.native_contract_lookup.resolve_service_key",
            return_value="fake-g2b-key",
        ), patch(
            "backend.services.native_contract_lookup.requests.get",
            return_value=_FakeResponse({"response": {"body": {"items": []}}}),
        ):
            result = resolve_contract_by_bid_no(
                bid_no="R25BK00554120",
                project_name_norm="경상남도교육청 함양도서관 이전 신축 설계공모",
                announce_date="20250106",
                org_name="경상남도교육청 경상남도함양교육지원청",
            )

        self.assertIs(result, eais_result)
        eais_hit.assert_called_once()

    def test_resolve_contract_by_bid_no_prefers_eais_before_lofin_for_general_org(self) -> None:
        eais_result = object()

        with patch(
            "backend.services.native_contract_lookup._resolve_eais_contract_hit",
            return_value=eais_result,
        ) as eais_hit, patch(
            "backend.services.native_contract_lookup._resolve_lofin_contract_hit",
            side_effect=AssertionError("general org should not call lofin when eais already matched"),
        ), patch(
            "backend.services.native_contract_lookup.resolve_service_key",
            return_value="fake-g2b-key",
        ), patch(
            "backend.services.native_contract_lookup.requests.get",
            return_value=_FakeResponse({"response": {"body": {"items": []}}}),
        ):
            result = resolve_contract_by_bid_no(
                bid_no="R25BK00555367",
                project_name_norm="부산박물관 시설개선사업",
                announce_date="20250106",
                org_name="부산광역시 건설본부",
            )

        self.assertIs(result, eais_result)
        eais_hit.assert_called_once()

    def test_resolve_contract_by_bid_no_falls_back_to_hub_result_before_lofin(self) -> None:
        hub_result = object()

        with patch(
            "backend.services.native_contract_lookup._resolve_eais_contract_hit",
            return_value=None,
        ), patch(
            "backend.services.native_contract_lookup._resolve_hub_result_hit",
            return_value=hub_result,
        ) as hub_hit, patch(
            "backend.services.native_contract_lookup._resolve_lofin_contract_hit",
            side_effect=AssertionError("hub hit should short-circuit before lofin"),
        ), patch(
            "backend.services.native_contract_lookup.resolve_service_key",
            return_value="fake-g2b-key",
        ), patch(
            "backend.services.native_contract_lookup.requests.get",
            return_value=_FakeResponse({"response": {"body": {"items": []}}}),
        ):
            result = resolve_contract_by_bid_no(
                bid_no="R25BK00937321",
                project_name_norm="(집행대행)(가칭) 구미늘품뜰 거점형 늘봄센터 신축공사 설계공모",
                announce_date="20250702",
                org_name="경상북도교육청",
            )

        self.assertIs(result, hub_result)
        hub_hit.assert_called_once()
