from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.services.native_seed_backend import AllEndpointsQuotaExceededError
from backend.services.native_seed_backend import _default_seed_page_max_workers
from backend.services.native_seed_backend import fetch_seed_rows
from backend.services.native_seed_backend import fetch_seed_rows_with_diagnostics
from backend.services.native_seed_backend import _matches_demand_org_filter


class _FakeResponse:
    def __init__(self, *, status_code: int, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self) -> dict:
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class NativeSeedBackendTests(unittest.TestCase):
    def test_default_seed_page_worker_count_uses_faster_fallback(self) -> None:
        self.assertEqual(_default_seed_page_max_workers(getenv_fn=lambda _name, _default="": ""), 4)

    def test_matches_demand_org_filter_supports_comma_separated_or_aliases(self) -> None:
        self.assertTrue(
            _matches_demand_org_filter(
                "부산, 울산, 경남",
                "경상남도 하동군",
            )
        )
        self.assertTrue(
            _matches_demand_org_filter(
                "부산, 울산, 경남",
                "부산광역시교육청",
            )
        )
        self.assertFalse(
            _matches_demand_org_filter(
                "부산, 울산, 경남",
                "전라남도 강진군",
            )
        )

    def test_fetch_seed_rows_with_multi_demand_org_filter_applies_or_matching(self) -> None:
        class _FakeSession:
            def get(self, endpoint_url: str, params: dict, timeout: int) -> _FakeResponse:
                if "getBidPblancListInfoServcPPSSrch" not in endpoint_url:
                    return _FakeResponse(
                        status_code=200,
                        payload={
                            "response": {
                                "header": {"resultCode": "00", "resultMsg": "OK"},
                                "body": {"totalCount": 0, "items": {}},
                            }
                        },
                    )
                return _FakeResponse(
                    status_code=200,
                    payload={
                        "response": {
                            "header": {"resultCode": "00", "resultMsg": "OK"},
                            "body": {
                                "totalCount": 2,
                                "items": {
                                    "item": [
                                        {
                                            "bidNtceNo": "R25BK00554120",
                                            "bidNtceOrd": "000",
                                            "bidNtceNm": "Design Contest Test Notice",
                                            "dminsttNm": "경상남도 하동군",
                                            "ntceInsttNm": "경상남도 하동군",
                                            "bidNtceDt": "20250102",
                                        },
                                        {
                                            "bidNtceNo": "R25BK00554121",
                                            "bidNtceOrd": "000",
                                            "bidNtceNm": "Design Contest Test Notice",
                                            "dminsttNm": "전라남도 강진군",
                                            "ntceInsttNm": "전라남도 강진군",
                                            "bidNtceDt": "20250103",
                                        },
                                    ]
                                },
                            },
                        }
                    },
                )

        with patch("backend.services.native_seed_backend.requests.Session", return_value=_FakeSession()):
            result = fetch_seed_rows_with_diagnostics(
                service_key="fake-key",
                start_date="20250101",
                end_date="20250131",
                bid_no_filter="",
                title_filter="Design Contest",
                demand_org_filter="부산, 울산, 경남",
                rows_per_page=30,
                max_pages=1,
                endpoint_mode="service",
                progress_cb=None,
            )

        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0]["bid_no"], "R25BK00554120")

    def test_early_stop_at_skips_remaining_pages_after_enough_matches(self) -> None:
        page_calls: list[int] = []

        class _FakeSession:
            def get(self, endpoint_url: str, params: dict, timeout: int) -> _FakeResponse:
                if "getBidPblancListInfoCnstwkPPSSrch" not in endpoint_url:
                    return _FakeResponse(
                        status_code=200,
                        payload={
                            "response": {
                                "header": {"resultCode": "00", "resultMsg": "OK"},
                                "body": {"totalCount": 0, "items": {}},
                            }
                        },
                    )
                page_calls.append(int(params.get("pageNo") or 0))
                page_no = int(params.get("pageNo") or 0)
                return _FakeResponse(
                    status_code=200,
                    payload={
                        "response": {
                            "header": {"resultCode": "00", "resultMsg": "OK"},
                            "body": {
                                "totalCount": 3,
                                "items": {
                                    "item": {
                                        "bidNtceNo": f"R25BK0000000{page_no}",
                                        "bidNtceOrd": "000",
                                        "bidNtceNm": f"Alpha Project Notice {page_no}",
                                        "dminsttNm": "Alpha Org",
                                        "ntceInsttNm": "Alpha Org",
                                        "bidNtceDt": "20250325",
                                    }
                                },
                            },
                        }
                    },
                )

        with patch("backend.services.native_seed_backend.requests.Session", return_value=_FakeSession()):
            result = fetch_seed_rows_with_diagnostics(
                service_key="fake-key",
                start_date="20250301",
                end_date="20250331",
                bid_no_filter="",
                title_filter="Alpha Project Notice",
                demand_org_filter="",
                rows_per_page=1,
                max_pages=3,
                endpoint_mode="construction",
                progress_cb=None,
                early_stop_at=1,
            )

        self.assertEqual(len(result.rows), 1)
        self.assertEqual(page_calls, [1])

    def test_broad_retry_can_run_when_partial_match_count_is_below_threshold(self) -> None:
        calls: list[tuple[str, dict]] = []

        class _FakeSession:
            def get(self, endpoint_url: str, params: dict, timeout: int) -> _FakeResponse:
                calls.append((endpoint_url, dict(params)))
                if "getBidPblancListInfoCnstwkPPSSrch" not in endpoint_url:
                    return _FakeResponse(
                        status_code=200,
                        payload={
                            "response": {
                                "header": {"resultCode": "00", "resultMsg": "OK"},
                                "body": {"totalCount": 0, "items": {}},
                            }
                        },
                    )

                if "bidNtceNm" in params:
                    return _FakeResponse(
                        status_code=200,
                        payload={
                            "response": {
                                "header": {"resultCode": "00", "resultMsg": "OK"},
                                "body": {
                                    "totalCount": 1,
                                    "items": {
                                        "item": {
                                            "bidNtceNo": "R25BK00742725",
                                            "bidNtceOrd": "000",
                                            "bidNtceNm": "고군농공단지 청년문화센터 건립사업 건축 설계공모",
                                            "dminsttNm": "전라남도 진도군",
                                            "ntceInsttNm": "전라남도 진도군",
                                            "bidNtceDt": "20250325",
                                        }
                                    },
                                },
                            }
                        },
                    )

                return _FakeResponse(
                    status_code=200,
                    payload={
                        "response": {
                            "header": {"resultCode": "00", "resultMsg": "OK"},
                            "body": {
                                "totalCount": 2,
                                "items": {
                                    "item": [
                                        {
                                            "bidNtceNo": "R25BK00742725",
                                            "bidNtceOrd": "000",
                                            "bidNtceNm": "고군농공단지 청년문화센터 건립사업 건축 설계공모",
                                            "dminsttNm": "전라남도 진도군",
                                            "ntceInsttNm": "전라남도 진도군",
                                            "bidNtceDt": "20250325",
                                        },
                                        {
                                            "bidNtceNo": "R25BK00742726",
                                            "bidNtceOrd": "000",
                                            "bidNtceNm": "고군농공단지 청년문화센터 건립사업 건축공사",
                                            "dminsttNm": "전라남도 진도군",
                                            "ntceInsttNm": "전라남도 진도군",
                                            "bidNtceDt": "20250326",
                                        },
                                    ]
                                },
                            },
                        }
                    },
                )

        with patch("backend.services.native_seed_backend.requests.Session", return_value=_FakeSession()):
            default_result = fetch_seed_rows_with_diagnostics(
                service_key="fake-key",
                start_date="20250301",
                end_date="20250331",
                bid_no_filter="",
                title_filter="고군농공단지 청년문화센터 건립사업",
                demand_org_filter="",
                rows_per_page=30,
                max_pages=1,
                endpoint_mode="construction",
                progress_cb=None,
            )

        self.assertEqual(len(default_result.rows), 1)
        self.assertFalse(default_result.diagnostics.title_broad_retry_used)

        calls.clear()
        with patch("backend.services.native_seed_backend.requests.Session", return_value=_FakeSession()):
            threshold_result = fetch_seed_rows_with_diagnostics(
                service_key="fake-key",
                start_date="20250301",
                end_date="20250331",
                bid_no_filter="",
                title_filter="고군농공단지 청년문화센터 건립사업",
                demand_org_filter="",
                rows_per_page=30,
                max_pages=1,
                endpoint_mode="construction",
                progress_cb=None,
                broad_retry_found_threshold=3,
            )

        self.assertEqual(len(threshold_result.rows), 2)
        self.assertTrue(threshold_result.diagnostics.title_broad_retry_used)
        self.assertTrue(
            any("bidNtceNm" not in call[1] for call in calls if "getBidPblancListInfoCnstwkPPSSrch" in call[0])
        )

    def test_fetch_seed_rows_retries_all_endpoints_when_scoped_lookup_misses(self) -> None:
        calls: list[tuple[str, dict]] = []

        class _FakeSession:
            def get(self, endpoint_url: str, params: dict, timeout: int) -> _FakeResponse:
                calls.append((endpoint_url, dict(params)))
                if "getBidPblancListInfoCnstwk" in endpoint_url:
                    return _FakeResponse(
                        status_code=200,
                        payload={
                            "response": {
                                "header": {"resultCode": "00", "resultMsg": "OK"},
                                "body": {"totalCount": 0, "items": {}},
                            }
                        },
                    )
                if "getBidPblancListInfoServc" in endpoint_url:
                    return _FakeResponse(
                        status_code=200,
                        payload={
                            "response": {
                                "header": {"resultCode": "00", "resultMsg": "OK"},
                                "body": {
                                    "totalCount": 1,
                                    "items": {
                                        "item": {
                                            "bidNtceNo": "R25BK00554120",
                                            "bidNtceOrd": "000",
                                            "bidNtceNm": "Design Contest Test Notice",
                                            "dminsttNm": "Seoul Design Office",
                                            "ntceInsttNm": "Seoul Design Office",
                                            "bidNtceDt": "20250102",
                                        }
                                    },
                                },
                            }
                        },
                    )
                return _FakeResponse(
                    status_code=200,
                    payload={
                        "response": {
                            "header": {"resultCode": "00", "resultMsg": "OK"},
                            "body": {"totalCount": 0, "items": {}},
                        }
                    },
                )

        with patch("backend.services.native_seed_backend.requests.Session", return_value=_FakeSession()):
            result = fetch_seed_rows_with_diagnostics(
                service_key="fake-key",
                start_date="20250101",
                end_date="20250131",
                bid_no_filter="R25BK00554120",
                title_filter="",
                demand_org_filter="",
                rows_per_page=30,
                max_pages=1,
                endpoint_mode="construction",
                progress_cb=None,
            )

        rows = result.rows
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["bid_no"], "R25BK00554120")
        self.assertEqual(rows[0]["project_name"], "Design Contest Test Notice")
        self.assertEqual(result.diagnostics.requested_endpoint_mode, "construction")
        self.assertEqual(result.diagnostics.effective_endpoint_mode, "construction")
        self.assertEqual(result.diagnostics.matched_endpoints, ["Servc"])
        self.assertTrue(result.diagnostics.all_scope_retry_used)
        self.assertTrue(result.diagnostics.direct_bid_lookup_used)
        self.assertTrue(any("getBidPblancListInfoCnstwk" in call[0] for call in calls))
        self.assertTrue(any("getBidPblancListInfoServc" in call[0] for call in calls))

    def test_fetch_seed_rows_returns_direct_bid_json_rows(self) -> None:
        calls: list[tuple[str, dict]] = []

        class _FakeSession:
            def get(self, endpoint_url: str, params: dict, timeout: int) -> _FakeResponse:
                calls.append((endpoint_url, dict(params)))
                return _FakeResponse(
                    status_code=200,
                    payload={
                        "response": {
                            "header": {"resultCode": "00", "resultMsg": "OK"},
                            "body": {
                                "totalCount": 1,
                                "items": {
                                    "item": {
                                        "bidNtceNo": "R25BK00554120",
                                        "bidNtceOrd": "000",
                                        "bidNtceNm": "Design Contest Test Notice",
                                        "dminsttNm": "Seoul Design Office",
                                        "ntceInsttNm": "Seoul Design Office",
                                        "bidNtceDt": "20250102",
                                    }
                                },
                            },
                        }
                    },
                )

        with patch("backend.services.native_seed_backend.requests.Session", return_value=_FakeSession()):
            rows = fetch_seed_rows(
                service_key="fake-key",
                start_date="20250101",
                end_date="20250131",
                bid_no_filter="R25BK00554120",
                title_filter="",
                demand_org_filter="",
                rows_per_page=30,
                max_pages=1,
                endpoint_mode="all",
                progress_cb=None,
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["bid_no"], "R25BK00554120")
        self.assertEqual(rows[0]["project_name"], "Design Contest Test Notice")
        self.assertEqual(rows[0]["g2b_verified"], "Y")
        self.assertTrue(any(call[1].get("inqryDiv") == "2" for call in calls))
        self.assertTrue(any("getBidPblancListInfoServc" in call[0] for call in calls))
        self.assertFalse(any("PPSSrch" in call[0] for call in calls if call[1].get("inqryDiv") == "2"))

    def test_fetch_seed_rows_excludes_cancelled_notice_on_direct_lookup(self) -> None:
        class _FakeSession:
            def get(self, endpoint_url: str, params: dict, timeout: int) -> _FakeResponse:
                return _FakeResponse(
                    status_code=200,
                    payload={
                        "response": {
                            "header": {"resultCode": "00", "resultMsg": "OK"},
                            "body": {
                                "totalCount": 2,
                                "items": {
                                    "item": [
                                        {
                                            "bidNtceNo": "R25BK00684517",
                                            "bidNtceOrd": "000",
                                            "bidNtceNm": "Design Contest Test Notice",
                                            "ntceKindNm": "등록공고",
                                            "dminsttNm": "Seoul Design Office",
                                            "ntceInsttNm": "Seoul Design Office",
                                            "bidNtceDt": "20250304",
                                        },
                                        {
                                            "bidNtceNo": "R25BK00684517",
                                            "bidNtceOrd": "001",
                                            "bidNtceNm": "Design Contest Test Notice",
                                            "ntceKindNm": "취소공고",
                                            "dminsttNm": "Seoul Design Office",
                                            "ntceInsttNm": "Seoul Design Office",
                                            "bidNtceDt": "20250317",
                                        },
                                    ]
                                },
                            },
                        }
                    },
                )

        with patch("backend.services.native_seed_backend.requests.Session", return_value=_FakeSession()):
            rows = fetch_seed_rows(
                service_key="fake-key",
                start_date="20250301",
                end_date="20250331",
                bid_no_filter="R25BK00684517",
                title_filter="",
                demand_org_filter="",
                rows_per_page=30,
                max_pages=1,
                endpoint_mode="service",
                progress_cb=None,
            )

        self.assertEqual(rows, [])

    def test_fetch_seed_rows_prefers_latest_bid_notice_order(self) -> None:
        class _FakeSession:
            def get(self, endpoint_url: str, params: dict, timeout: int) -> _FakeResponse:
                return _FakeResponse(
                    status_code=200,
                    payload={
                        "response": {
                            "header": {"resultCode": "00", "resultMsg": "OK"},
                            "body": {
                                "totalCount": 2,
                                "items": {
                                    "item": [
                                        {
                                            "bidNtceNo": "R25BK00873206",
                                            "bidNtceOrd": "000",
                                            "bidNtceNm": "KTC 센터 설계공모",
                                            "ntceKindNm": "등록공고",
                                            "bidNtceUrl": "https://example.com/000",
                                            "bidNtceDtlUrl": "https://example.com/000",
                                            "dminsttNm": "Alpha Org",
                                            "ntceInsttNm": "Alpha Org",
                                            "bidNtceDt": "20250527",
                                        },
                                        {
                                            "bidNtceNo": "R25BK00873206",
                                            "bidNtceOrd": "001",
                                            "bidNtceNm": "KTC 센터 설계공모(변경공고)",
                                            "ntceKindNm": "변경공고",
                                            "bidNtceUrl": "https://example.com/001",
                                            "bidNtceDtlUrl": "https://example.com/001",
                                            "dminsttNm": "Alpha Org",
                                            "ntceInsttNm": "Alpha Org",
                                            "bidNtceDt": "20250528",
                                        },
                                    ]
                                },
                            },
                        }
                    },
                )

        with patch("backend.services.native_seed_backend.requests.Session", return_value=_FakeSession()):
            rows = fetch_seed_rows(
                service_key="fake-key",
                start_date="20250501",
                end_date="20250531",
                bid_no_filter="R25BK00873206",
                title_filter="",
                demand_org_filter="",
                rows_per_page=30,
                max_pages=1,
                endpoint_mode="service",
                progress_cb=None,
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["bid_ord"], "001")
        self.assertEqual(rows[0]["bid_ntce_dtl_url"], "https://example.com/001")
        self.assertEqual(rows[0]["project_name"], "KTC 센터 설계공모(변경공고)")

    def test_fetch_seed_rows_preserves_multiple_spec_docs(self) -> None:
        class _FakeSession:
            def get(self, endpoint_url: str, params: dict, timeout: int) -> _FakeResponse:
                return _FakeResponse(
                    status_code=200,
                    payload={
                        "response": {
                            "header": {"resultCode": "00", "resultMsg": "OK"},
                            "body": {
                                "totalCount": 1,
                                "items": {
                                    "item": {
                                        "bidNtceNo": "R25BK00570104",
                                        "bidNtceOrd": "000",
                                        "bidNtceNm": "Design Contest Test Notice",
                                        "dminsttNm": "Seoul Design Office",
                                        "ntceInsttNm": "Seoul Design Office",
                                        "bidNtceDt": "20250102",
                                        "ntceSpecDocUrl1": "https://example.com/doc1.hwp",
                                        "ntceSpecDocUrl2": "https://example.com/doc2.hwp",
                                        "ntceSpecDocUrl3": "https://example.com/doc3.hwp",
                                        "ntceSpecFileNm1": "공고문.hwp",
                                        "ntceSpecFileNm2": "과업지시서.hwp",
                                        "ntceSpecFileNm3": "설계지침서.hwp",
                                    }
                                },
                            },
                        }
                    },
                )

        with patch("backend.services.native_seed_backend.requests.Session", return_value=_FakeSession()):
            rows = fetch_seed_rows(
                service_key="fake-key",
                start_date="20250101",
                end_date="20250131",
                bid_no_filter="R25BK00570104",
                title_filter="",
                demand_org_filter="",
                rows_per_page=30,
                max_pages=1,
                endpoint_mode="all",
                progress_cb=None,
            )

        self.assertEqual(rows[0]["spec_doc_url_1"], "https://example.com/doc1.hwp")
        self.assertEqual(rows[0]["spec_doc_file_name_1"], "공고문.hwp")
        self.assertEqual(rows[0]["spec_doc_url_2"], "https://example.com/doc2.hwp")
        self.assertEqual(rows[0]["spec_doc_file_name_2"], "과업지시서.hwp")
        self.assertEqual(rows[0]["spec_doc_url_3"], "https://example.com/doc3.hwp")
        self.assertEqual(rows[0]["spec_doc_file_name_3"], "설계지침서.hwp")

    def test_fetch_seed_rows_raises_when_all_attempted_endpoints_are_quota_exceeded(self) -> None:
        class _FakeSession:
            def get(self, endpoint_url: str, params: dict, timeout: int) -> _FakeResponse:
                return _FakeResponse(status_code=429, text="quota")

        with patch("backend.services.native_seed_backend.requests.Session", return_value=_FakeSession()):
            with self.assertRaises(AllEndpointsQuotaExceededError):
                fetch_seed_rows(
                    service_key="fake-key",
                    start_date="20250101",
                    end_date="20250131",
                    bid_no_filter="R25BK00554120",
                    title_filter="",
                    demand_org_filter="",
                    rows_per_page=30,
                    max_pages=1,
                    endpoint_mode="all",
                    progress_cb=None,
                )

    def test_fetch_seed_rows_retries_transient_gateway_error_before_failing_run(self) -> None:
        calls: list[int] = []

        class _FakeSession:
            def get(self, endpoint_url: str, params: dict, timeout: int) -> _FakeResponse:
                calls.append(int(params.get("pageNo") or 0))
                if len(calls) == 1:
                    return _FakeResponse(status_code=502, text="<html><center>cloudflare</center></html>")
                return _FakeResponse(
                    status_code=200,
                    payload={
                        "response": {
                            "header": {"resultCode": "00", "resultMsg": "OK"},
                            "body": {
                                "totalCount": 1,
                                "items": {
                                    "item": {
                                        "bidNtceNo": "R25BK00554120",
                                        "bidNtceOrd": "000",
                                        "bidNtceNm": "Design Contest Test Notice",
                                        "dminsttNm": "Seoul Design Office",
                                        "ntceInsttNm": "Seoul Design Office",
                                        "bidNtceDt": "20250102",
                                    }
                                },
                            },
                        }
                    },
                )

        with patch("backend.services.native_seed_backend.requests.Session", return_value=_FakeSession()):
            result = fetch_seed_rows_with_diagnostics(
                service_key="fake-key",
                start_date="20250101",
                end_date="20250131",
                bid_no_filter="",
                title_filter="Design Contest",
                demand_org_filter="",
                rows_per_page=30,
                max_pages=1,
                endpoint_mode="service",
                progress_cb=None,
            )

        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0]["bid_no"], "R25BK00554120")
        self.assertEqual(calls, [1, 1])

    def test_fetch_seed_rows_falls_back_to_title_only_when_bid_no_is_stale(self) -> None:
        calls: list[dict] = []

        class _FakeSession:
            def get(self, endpoint_url: str, params: dict, timeout: int) -> _FakeResponse:
                calls.append(dict(params))
                if "bidNtceNo" in params:
                    return _FakeResponse(
                        status_code=200,
                        payload={
                            "response": {
                                "header": {"resultCode": "00", "resultMsg": "OK"},
                                "body": {"totalCount": 0, "items": {}},
                            }
                        },
                    )
                if params.get("bidNtceNm") == "Geumnam Complex Design Contest":
                    return _FakeResponse(
                        status_code=200,
                        payload={
                            "response": {
                                "header": {"resultCode": "00", "resultMsg": "OK"},
                                "body": {
                                    "totalCount": 1,
                                    "items": {
                                        "item": {
                                            "bidNtceNo": "20241207400",
                                            "bidNtceOrd": "000",
                                            "bidNtceNm": "Geumnam Complex Design Contest",
                                            "dminsttNm": "Sejong City",
                                            "ntceInsttNm": "Sejong City",
                                            "bidNtceDt": "20241204",
                                        }
                                    },
                                },
                            }
                        },
                    )
                return _FakeResponse(
                    status_code=200,
                    payload={
                        "response": {
                            "header": {"resultCode": "00", "resultMsg": "OK"},
                            "body": {"totalCount": 0, "items": {}},
                        }
                    },
                )

        with patch("backend.services.native_seed_backend.requests.Session", return_value=_FakeSession()):
            result = fetch_seed_rows_with_diagnostics(
                service_key="fake-key",
                start_date="20241204",
                end_date="20241204",
                bid_no_filter="R26BK01234567",
                title_filter="Geumnam Complex Design Contest",
                demand_org_filter="",
                rows_per_page=30,
                max_pages=1,
                endpoint_mode="service",
                progress_cb=None,
            )

        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0]["bid_no"], "20241207400")
        self.assertTrue(any(call.get("bidNtceNm") and "bidNtceNo" not in call for call in calls))
