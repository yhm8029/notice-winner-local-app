from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.services.native_contract_lookup import _build_lofin_query_variants
from backend.services.native_contract_lookup import _build_lofin_date_hints
from backend.services.native_contract_lookup import _fetch_lofin_contract_rows
from backend.services.native_contract_lookup import _resolve_lofin_contract_hit
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


class NativeContractLookupMetaTests(unittest.TestCase):
    def test_build_lofin_query_variants_prefers_core_query(self) -> None:
        variants = _build_lofin_query_variants(
            "혁신도시 아동종합지원센터 건립사업 설계공모(제안공모)"
        )

        self.assertEqual(
            variants[:2],
            [
                "혁신도시 아동종합지원센터 건립",
                "혁신도시 아동종합지원센터",
            ],
        )

    def test_build_lofin_query_variants_compacts_ascii_spacing(self) -> None:
        variants = _build_lofin_query_variants("매우봄돌봄 생활 SOC 건립 설계공모")

        self.assertIn("매우봄돌봄 생활SOC 건립", variants)
        self.assertIn("매우봄돌봄 생활SOC", variants)

    def test_build_lofin_date_hints_is_ascending(self) -> None:
        date_hints = _build_lofin_date_hints("20250106")
        self.assertTrue(date_hints)
        self.assertEqual(date_hints[0], "20250205")
        self.assertEqual(date_hints[1], "20250206")
        self.assertGreater(date_hints[-1], date_hints[0])

    def test_fetch_lofin_contract_rows_adds_contract_kind_param(self) -> None:
        captured_params: list[dict[str, object]] = []

        def _fake_get(url: str, params: dict[str, object], timeout: float, headers=None):
            captured_params.append(dict(params))
            return _FakeResponse({"RESULT": {"CODE": "INFO-000", "MESSAGE": "OK"}, "data": []})

        with patch.dict(
            "os.environ",
            {"LOFIN_OPENAPI_KEY": "fake-lofin-key"},
            clear=False,
        ), patch(
            "backend.services.native_contract_lookup._LOFIN_FORCE_POWERSHELL_GET",
            False,
        ), patch(
            "backend.services.native_contract_lookup.requests.get",
            side_effect=_fake_get,
        ):
            rows = _fetch_lofin_contract_rows(
                query="테스트 문화센터",
                contract_date_hint="20250324",
                timeout_sec=5.0,
            )

        self.assertEqual(rows, [])
        self.assertTrue(captured_params)
        self.assertEqual(captured_params[0]["ctrt_knd_nm"], "용역")

    def test_query_lookup_is_disabled_by_default(self) -> None:
        calls: list[dict[str, object]] = []

        def _fake_get(url: str, params: dict[str, object], timeout: float):
            calls.append(dict(params))
            return _FakeResponse({"response": {"body": {"items": []}}})

        with patch(
            "backend.services.native_contract_lookup.resolve_service_key",
            return_value="fake-key",
        ), patch(
            "backend.services.native_contract_lookup.requests.get",
            side_effect=_fake_get,
        ):
            result = resolve_contract_by_bid_no(
                bid_no="R25BK00569527",
                project_name_norm="양산농업인교육관건립건축설계공모",
                announce_date="20250115",
                org_name="경상남도 양산시청",
            )

        self.assertIsNone(result)
        search_calls = [call for call in calls if str(call.get("inqryDiv") or "") == "1"]
        self.assertEqual(search_calls, [])
        meta = get_last_contract_lookup_meta()
        self.assertEqual(meta.contract_lookup_path, "no_hit")
        self.assertFalse(meta.query_sweep_used)
        self.assertFalse(meta.query_sweep_hit)

    def test_query_lookup_uses_documented_inqry_dt_params_when_enabled(self) -> None:
        calls: list[dict[str, object]] = []

        def _fake_get(url: str, params: dict[str, object], timeout: float):
            calls.append(dict(params))
            return _FakeResponse({"response": {"body": {"items": []}}})

        with patch(
            "backend.services.native_contract_lookup.resolve_service_key",
            return_value="fake-key",
        ), patch(
            "backend.services.native_contract_lookup.requests.get",
            side_effect=_fake_get,
        ):
            resolve_contract_by_bid_no(
                bid_no="R25BK00569527",
                project_name_norm="양산농업인교육관건립건축설계공모",
                announce_date="20250115",
                org_name="경상남도 양산시청",
                enable_query_sweep=True,
            )

        search_calls = [call for call in calls if str(call.get("inqryDiv") or "") == "1"]
        self.assertTrue(search_calls)
        self.assertTrue(all("inqryBgnDt" in call for call in search_calls))
        self.assertTrue(all("inqryEndDt" in call for call in search_calls))
        self.assertTrue(all("inqryBgnDate" not in call for call in search_calls))
        self.assertTrue(all("inqryEndDate" not in call for call in search_calls))
        meta = get_last_contract_lookup_meta()
        self.assertEqual(meta.contract_lookup_path, "no_hit")
        self.assertTrue(meta.query_sweep_used)
        self.assertFalse(meta.query_sweep_hit)

    def test_lofin_meta_fields_are_populated_for_lofin_hit(self) -> None:
        g2b_empty = {"response": {"body": {"items": []}}}
        lofin_payload = {
            "dsList": [
                {
                    "ctrtLdgrMngNo": "L-1",
                    "ctrtTrgtNm": "부산박물관 시설개선사업",
                    "cltNm": "테스트건축사사무소",
                    "smzCtrtYmd": "20250324",
                }
            ]
        }
        request_dates: list[str] = []

        def _fake_get(url: str, params: dict[str, object], timeout: float, headers=None):
            if "lofin365.go.kr" in url:
                request_dates.append(str(params.get("smz_ctrt_ymd") or ""))
                return _FakeResponse(lofin_payload)
            return _FakeResponse(g2b_empty)

        def _fake_post(url: str, headers: dict[str, str], data: str, timeout: float):
            return _FakeResponse({"dataList": []})

        with patch(
            "backend.services.native_contract_lookup.resolve_service_key",
            return_value="fake-key",
        ), patch.dict(
            "os.environ",
            {"LOFIN_OPENAPI_KEY": "fake-lofin-key"},
            clear=False,
        ), patch(
            "backend.services.native_contract_lookup._LOFIN_FORCE_POWERSHELL_GET",
            False,
        ), patch(
            "backend.services.native_contract_lookup.requests.get",
            side_effect=_fake_get,
        ), patch(
            "backend.services.native_contract_lookup.requests.post",
            side_effect=_fake_post,
        ):
            result = resolve_contract_by_bid_no(
                bid_no="R25BK00555367",
                project_name_norm="부산박물관 시설개선사업",
                announce_date="20250106",
                org_name="부산광역시 건설본부",
            )

        self.assertIsNotNone(result)
        meta = get_last_contract_lookup_meta()
        self.assertEqual(meta.contract_lookup_path, "lofin_hit")
        self.assertEqual(meta.lofin_date_workers, 3)
        self.assertEqual(meta.lofin_global_semaphore_limit, 4)
        self.assertGreater(meta.lofin_dates_examined, 0)
        self.assertGreater(meta.lofin_requests_total, 0)
        self.assertGreater(meta.lofin_pages_fetched_total, 0)
        self.assertEqual(meta.lofin_first_nonempty_date, request_dates[0])
        self.assertEqual(meta.lofin_hit_date, "20250324")
        self.assertGreater(meta.lofin_best_score, 0.0)

    def test_lofin_budget_exhausted_meta_is_recorded(self) -> None:
        monotonic_values = iter([0.0, 1.0, 2.0, 40.0, 41.0, 42.0])

        with patch.dict(
            "os.environ",
            {"LOFIN_OPENAPI_KEY": "fake-lofin-key"},
            clear=False,
        ), patch(
            "backend.services.native_contract_lookup.time.monotonic",
            side_effect=lambda: next(monotonic_values),
        ), patch(
            "backend.services.native_contract_lookup._build_lofin_date_hints",
            return_value=["20250309", "20250310", "20250311"],
        ), patch(
            "backend.services.native_contract_lookup._build_lofin_query_variants",
            return_value=["테스트 프로젝트"],
        ), patch(
            "backend.services.native_contract_lookup._fetch_lofin_contract_rows",
            return_value=[],
        ) as fetch_rows:
            result = _resolve_lofin_contract_hit(
                project_name_norm="테스트 프로젝트",
                announce_date="20250207",
                timeout_sec=20.0,
            )

        self.assertIsNone(result)
        self.assertEqual(fetch_rows.call_count, 1)
        meta = get_last_contract_lookup_meta()
        self.assertTrue(meta.lofin_budget_exhausted)
        self.assertGreater(meta.lofin_budget_seconds, 0.0)
