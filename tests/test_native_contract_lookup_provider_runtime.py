from __future__ import annotations

import unittest
import requests

from backend.services.native_contract_lookup_hub_runtime import _load_hub_result_payload_text
from backend.services.native_contract_lookup_lofin_runtime import _extract_lofin_openapi_error
from backend.services.native_contract_lookup_lofin_runtime import _extract_lofin_openapi_rows
from backend.services.native_contract_lookup_lofin_runtime import _normalize_lofin_openapi_row
from backend.services.native_contract_lookup_provider_runtime import _append_rows
from backend.services.native_contract_lookup_provider_runtime import _extract_g2b_items
from backend.services.native_contract_lookup_provider_runtime import _fetch_eais_best_candidate_for_query_year
from backend.services.native_contract_lookup_provider_runtime import _fetch_lofin_contract_rows
from backend.services.native_contract_lookup_provider_runtime import _resolve_lofin_openapi_key
from backend.services.native_contract_lookup_provider_runtime import _search_hub_result_candidates


class _FakeSemaphore:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class NativeContractLookupProviderRuntimeTests(unittest.TestCase):
    def test_extract_lofin_openapi_rows_walks_nested_payload(self) -> None:
        payload = {
            "response": {
                "body": {
                    "items": [
                        {
                            "ctrt_trgt_nm": "?뚯뒪???ъ뾽",
                            "smz_ctrt_ymd": "20250401",
                            "clt_nm": "?낆껜",
                            "ctrt_ldgr_mng_no": "A-1",
                        }
                    ]
                }
            }
        }

        rows = _extract_lofin_openapi_rows(payload)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["ctrt_trgt_nm"], "?뚯뒪???ъ뾽")

    def test_normalize_lofin_openapi_row_accepts_snake_case_keys(self) -> None:
        row = _normalize_lofin_openapi_row(
            {
                "ctrt_ldgr_mng_no": "A-1",
                "ctrt_trgt_nm": "?뚯뒪???ъ뾽",
                "smz_ctrt_ymd": "20250401",
                "clt_nm": "?낆껜",
                "ctrt_tot_tott_amt": "1500000",
                "laf_hg_nm": "湲곌?",
                "ctrt_knd_nm": "?⑹뿭",
            }
        )

        self.assertEqual(row["ctrtLdgrMngNo"], "A-1")
        self.assertEqual(row["ctrtTrgtNm"], "?뚯뒪???ъ뾽")
        self.assertEqual(row["lafNm"], "湲곌?")

    def test_extract_lofin_openapi_error_treats_success_code_as_empty_error(self) -> None:
        self.assertEqual(
            _extract_lofin_openapi_error({"RESULT": {"CODE": "INFO-000", "MESSAGE": "ok"}}),
            ("", "ok"),
        )

    def test_load_hub_result_payload_text_salvages_json_with_prefix_noise(self) -> None:
        payload = _load_hub_result_payload_text("warning...\n[{\"title\":\"怨듦퀬\",\"winnerOffice\":\"湲곌?\"}]")

        self.assertEqual(payload, [{"title": "怨듦퀬", "winnerOffice": "湲곌?"}])

    def test_extract_g2b_items_accepts_single_item_shape(self) -> None:
        rows = _extract_g2b_items(
            {
                "response": {
                    "body": {
                        "items": {
                            "item": {
                                "cntrctNm": "contract",
                                "corpList": "winner",
                            }
                        }
                    }
                }
            }
        )

        self.assertEqual(rows, [{"cntrctNm": "contract", "corpList": "winner"}])

    def test_append_rows_dedupes_same_contract_payload(self) -> None:
        payload = {
            "response": {
                "body": {
                    "items": {
                        "item": [
                            {
                                "dcsnCntrctNo": "A-1",
                                "cntrctNm": "contract",
                                "corpList": "winner",
                                "cntrctDate": "2025-04-01",
                            },
                            {
                                "dcsnCntrctNo": "A-1",
                                "cntrctNm": "contract",
                                "corpList": "winner",
                                "cntrctDate": "2025-04-01",
                            },
                        ]
                    }
                }
            }
        }
        rows: list[dict] = []
        seen: set[str] = set()

        _append_rows(rows=rows, seen=seen, payload=payload)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["dcsnCntrctNo"], "A-1")

    def test_resolve_lofin_openapi_key_prefers_explicit_key(self) -> None:
        self.assertEqual(
            _resolve_lofin_openapi_key(explicit_key="manual-key", env_names=("LOFIN_OPENAPI_KEY",)),
            "manual-key",
        )

    def test_search_hub_result_candidates_skips_blank_query(self) -> None:
        calls: list[tuple[str, float]] = []

        def _fake_getter(*, query: str, timeout_sec: float) -> list[dict]:
            calls.append((query, timeout_sec))
            return [{"title": "contract"}]

        rows = _search_hub_result_candidates(
            query="   ",
            timeout_sec=2.0,
            get_hub_result_candidates_fn=_fake_getter,
        )

        self.assertEqual(rows, [])
        self.assertEqual(calls, [])

    def test_fetch_eais_best_candidate_for_query_year_picks_highest_score(self) -> None:
        calls: list[int] = []

        def _fake_post(url: str, payload: dict, *, referer: str, timeout_sec: float, eais_base_url: str) -> dict:
            calls.append(int(payload["currentPage"]))
            return {
                "dataList": [
                    {"pssrpPblancNm": "A"},
                    {"pssrpPblancNm": "B"},
                ]
            }

        def _fake_score(_project_name_norm: str, target: str, row=None) -> float:
            return {"A": 0.2, "B": 0.9}[target]

        row, score, target = _fetch_eais_best_candidate_for_query_year(
            project_name_norm="contract",
            query="contract",
            year="2025",
            timeout_sec=5.0,
            post_eais_json_fn=_fake_post,
            list_api_url="https://example.test/list",
            referer="https://example.test/ref",
            eais_base_url="https://example.test",
            score_fn=_fake_score,
        )

        self.assertEqual(calls, [0])
        self.assertEqual(target, "B")
        self.assertAlmostEqual(score, 0.9)
        self.assertEqual(row, {"pssrpPblancNm": "B"})

    def test_fetch_lofin_contract_rows_adds_contract_kind_and_dedupes_rows(self) -> None:
        captured_params: list[dict[str, object]] = []

        def _fake_get(url: str, *, params: dict[str, object], timeout: float, headers=None):
            captured_params.append(dict(params))
            return _FakeResponse({"unused": True})

        rows = _fetch_lofin_contract_rows(
            query="contract",
            contract_date_hint="20250401",
            timeout_sec=5.0,
            max_rows=10,
            max_pages=1,
            resolve_lofin_openapi_key_fn=lambda: "fake-key",
            is_yyyymmdd_fn=lambda value: value == "20250401",
            global_semaphore=_FakeSemaphore(),
            contract_openapi_url="https://example.test/lofin",
            contract_kind_name="service",
            get_json_via_powershell_fn=lambda *_args, **_kwargs: {},
            extract_lofin_openapi_error_fn=lambda _payload: ("", ""),
            extract_lofin_openapi_rows_fn=lambda _payload: [
                {
                    "ctrtLdgrMngNo": "A-1",
                    "ctrtTrgtNm": "contract",
                    "cltNm": "winner",
                    "smzCtrtYmd": "20250401",
                },
                {
                    "ctrtLdgrMngNo": "A-1",
                    "ctrtTrgtNm": "contract",
                    "cltNm": "winner",
                    "smzCtrtYmd": "20250401",
                },
            ],
            normalize_lofin_openapi_row_fn=lambda row: dict(row),
            requests_get_fn=_fake_get,
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["ctrtLdgrMngNo"], "A-1")
        self.assertEqual(captured_params[0]["ctrt_knd_nm"], "service")

    def test_fetch_lofin_contract_rows_switches_to_powershell_after_ssl_error(self) -> None:
        forced: list[bool] = []

        def _fake_get(*_args, **_kwargs):
            raise requests.exceptions.SSLError("ssl")

        rows = _fetch_lofin_contract_rows(
            query="contract",
            contract_date_hint="20250401",
            timeout_sec=5.0,
            max_rows=10,
            max_pages=1,
            stats=None,
            force_powershell_get=False,
            set_force_powershell_get_fn=forced.append,
            resolve_lofin_openapi_key_fn=lambda: "fake-key",
            is_yyyymmdd_fn=lambda _value: True,
            global_semaphore=_FakeSemaphore(),
            contract_openapi_url="https://example.test/lofin",
            contract_kind_name="service",
            get_json_via_powershell_fn=lambda *_args, **_kwargs: {"payload": True},
            extract_lofin_openapi_error_fn=lambda _payload: ("", ""),
            extract_lofin_openapi_rows_fn=lambda _payload: [
                {
                    "ctrtLdgrMngNo": "B-1",
                    "ctrtTrgtNm": "contract",
                    "cltNm": "winner",
                    "smzCtrtYmd": "20250401",
                }
            ],
            normalize_lofin_openapi_row_fn=lambda row: dict(row),
            requests_get_fn=_fake_get,
        )

        self.assertEqual(forced, [True])
        self.assertEqual(rows[0]["ctrtLdgrMngNo"], "B-1")


if __name__ == "__main__":
    unittest.main()
