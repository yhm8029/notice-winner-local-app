from __future__ import annotations

import csv
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import unquote

import requests

from .native_seed_runtime import api_header as _api_header_impl
from .native_seed_runtime import build_seed_row_from_item as _build_seed_row_from_item_impl
from .native_seed_runtime import clean_notice_title as _clean_notice_title_impl
from .native_seed_runtime import derive_notice_status as _derive_notice_status_impl
from .native_seed_runtime import endpoint_priority as _endpoint_priority_impl
from .native_seed_runtime import expand_demand_org_aliases as _expand_demand_org_aliases_impl
from .native_seed_runtime import extract_items as _extract_items_impl
from .native_seed_runtime import extract_items_from_xml as _extract_items_from_xml_impl
from .native_seed_runtime import extract_yyyymmdd as _extract_yyyymmdd_impl
from .native_seed_runtime import iter_month_ranges as _iter_month_ranges_impl
from .native_seed_runtime import matches_demand_org_filter as _matches_demand_org_filter_impl
from .native_seed_runtime import notice_dt_sort_key as _notice_dt_sort_key_impl
from .native_seed_runtime import notice_ord_num as _notice_ord_num_impl
from .native_seed_runtime import notice_status_priority as _notice_status_priority_impl
from .native_seed_runtime import select_org_name as _select_org_name_impl
from .native_seed_runtime import should_replace_seed_notice as _should_replace_seed_notice_impl
from .native_seed_runtime import split_bid_no_ord as _split_bid_no_ord_impl
from .native_seed_runtime import split_demand_org_filter_tokens as _split_demand_org_filter_tokens_impl
from .transient_http_retry import is_transient_http_status
from .transient_http_retry import run_with_transient_http_retries

ATTACHMENT_FIELD_COUNT = 10
ATTACHMENT_SEED_HEADERS = tuple(
    field_name
    for index in range(1, ATTACHMENT_FIELD_COUNT + 1)
    for field_name in (f"spec_doc_url_{index}", f"spec_doc_file_name_{index}")
)

SEED_HEADERS = (
    "bid_no",
    "bid_ord",
    "project_name",
    "org_name",
    "announce_date",
    "opening_scheduled_date",
    "g2b_verified",
    "bid_ntce_url",
    "bid_ntce_dtl_url",
    "notice_officer_name",
    "notice_officer_tel",
    "notice_officer_email",
    "demand_officer_name",
    "demand_officer_email",
    "presmpt_prce",
    "service_name",
    "sucsfbid_method_name",
) + ATTACHMENT_SEED_HEADERS
API_ENDPOINTS_SEARCH = [
    (
        "CnstwkPPSSrch",
        "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwkPPSSrch",
    ),
    (
        "ServcPPSSrch",
        "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServcPPSSrch",
    ),
    (
        "ThngPPSSrch",
        "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoThngPPSSrch",
    ),
]
API_ENDPOINTS_ALL = [
    (
        "Cnstwk",
        "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwk",
    ),
    (
        "Servc",
        "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServc",
    ),
    (
        "Thng",
        "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoThng",
    ),
]
API_SCOPE_TO_ENDPOINTS = {
    "construction": {"search": [API_ENDPOINTS_SEARCH[0]], "all": [API_ENDPOINTS_SEARCH[0]]},
    "service": {"search": [API_ENDPOINTS_SEARCH[1]], "all": [API_ENDPOINTS_SEARCH[1]]},
    "goods": {"search": [API_ENDPOINTS_SEARCH[2]], "all": [API_ENDPOINTS_SEARCH[2]]},
    "all": {"search": API_ENDPOINTS_SEARCH, "all": API_ENDPOINTS_ALL},
}
API_SCOPE_TO_DIRECT_ENDPOINTS = {
    "construction": [API_ENDPOINTS_ALL[0]],
    "service": [API_ENDPOINTS_ALL[1]],
    "goods": [API_ENDPOINTS_ALL[2]],
    "all": API_ENDPOINTS_ALL,
}
G2B_SERVICE_KEY_ENV_NAMES = (
    "DATA_GO_KR_SERVICE_KEY",
    "PUBLIC_DATA_SERVICE_KEY",
    "G2B_SERVICE_KEY",
)
REGION_ALIAS_GROUPS = (
    ("서울", "서울특별시"),
    ("부산", "부산광역시"),
    ("대구", "대구광역시"),
    ("인천", "인천광역시"),
    ("광주", "광주광역시"),
    ("대전", "대전광역시"),
    ("울산", "울산광역시"),
    ("세종", "세종특별자치시"),
    ("경기", "경기도"),
    ("강원", "강원도", "강원특별자치도"),
    ("충북", "충청북도"),
    ("충남", "충청남도"),
    ("전북", "전라북도", "전북특별자치도"),
    ("전남", "전라남도"),
    ("경북", "경상북도"),
    ("경남", "경상남도"),
    ("제주", "제주도", "제주특별자치도"),
)
TITLE_PAREN_NOISE_TOKENS = {
    "일반",
    "긴급",
    "설계공모",
    "일반설계공모",
    "설계공모긴급",
    "긴급설계공모",
    "공고",
}
def _default_seed_page_max_workers(*, getenv_fn: Callable[[str, str], str] | None = None) -> int:
    getenv = getenv_fn or os.getenv
    raw_value = str(
        getenv("PROJECT_TRACKER_SEED_PAGE_WORKERS", "").strip()
        or getenv("WINNER_PIPELINE_SEED_PAGE_WORKERS", "4")
    ).strip() or "4"
    try:
        return max(1, int(raw_value))
    except ValueError:
        return 4


SEED_PAGE_MAX_WORKERS = _default_seed_page_max_workers()


class AllEndpointsQuotaExceededError(RuntimeError):
    def __init__(self, endpoint_names: list[str]) -> None:
        self.endpoint_names = endpoint_names
        super().__init__("API quota exceeded on all attempted endpoints: " + ", ".join(endpoint_names))


@dataclass(frozen=True)
class SeedFetchDiagnostics:
    requested_endpoint_mode: str
    effective_endpoint_mode: str
    attempted_endpoints: list[str]
    matched_endpoints: list[str]
    all_scope_retry_used: bool
    direct_bid_lookup_used: bool
    title_broad_retry_used: bool
    title_broad_retry_allowed: bool
    demand_org_filter_tokens: list[str]
    demand_org_match_samples: list[dict[str, str]]


@dataclass(frozen=True)
class SeedFetchResult:
    rows: list[dict[str, str]]
    diagnostics: SeedFetchDiagnostics


def _normalize_service_key(value: str) -> str:
    key = (value or "").strip()
    if "%" in key:
        key = unquote(key)
    return key


def resolve_service_key(explicit_key: str = "") -> str:
    key = _normalize_service_key(explicit_key)
    if key:
        return key
    for env_name in G2B_SERVICE_KEY_ENV_NAMES:
        env_val = _normalize_service_key(str(os.getenv(env_name) or ""))
        if env_val:
            return env_val
    return ""


def fetch_seed_rows(
    *,
    service_key: str,
    start_date: str,
    end_date: str,
    bid_no_filter: str,
    title_filter: str,
    demand_org_filter: str,
    rows_per_page: int,
    max_pages: int,
    endpoint_mode: str = "construction",
    progress_cb: Callable[[str], None] | None = None,
    allow_title_broad_retry: bool = True,
    capture_demand_org_debug: bool = False,
    broad_retry_found_threshold: int = 1,
    early_stop_at: int = 0,
    recent_months_first: bool = False,
) -> list[dict[str, str]]:
    return fetch_seed_rows_with_diagnostics(
        service_key=service_key,
        start_date=start_date,
        end_date=end_date,
        bid_no_filter=bid_no_filter,
        title_filter=title_filter,
        demand_org_filter=demand_org_filter,
        rows_per_page=rows_per_page,
        max_pages=max_pages,
        endpoint_mode=endpoint_mode,
        progress_cb=progress_cb,
        allow_title_broad_retry=allow_title_broad_retry,
        capture_demand_org_debug=capture_demand_org_debug,
        broad_retry_found_threshold=broad_retry_found_threshold,
        early_stop_at=early_stop_at,
        recent_months_first=recent_months_first,
    ).rows


def fetch_seed_rows_with_diagnostics(
    *,
    service_key: str,
    start_date: str,
    end_date: str,
    bid_no_filter: str,
    title_filter: str,
    demand_org_filter: str,
    rows_per_page: int,
    max_pages: int,
    endpoint_mode: str = "construction",
    progress_cb: Callable[[str], None] | None = None,
    request_timeout_sec: int = 30,
    allow_title_broad_retry: bool = True,
    capture_demand_org_debug: bool = False,
    broad_retry_found_threshold: int = 1,
    early_stop_at: int = 0,
    recent_months_first: bool = False,
) -> SeedFetchResult:
    session = requests.Session()
    bid_filter_norm = _norm_token(bid_no_filter)
    title_filter_norm = _norm_text(title_filter)
    demand_org_filter = str(demand_org_filter or "").strip()

    found_map: dict[str, dict[str, str]] = {}
    found_order: list[str] = []
    excluded_keys: set[str] = set()
    attempted_endpoints: set[str] = set()
    matched_endpoints: set[str] = set()
    quota_exceeded: set[str] = set()
    month_ranges = _iter_month_ranges(start_date, end_date)
    if recent_months_first:
        month_ranges = list(reversed(month_ranges))
    bid_no_exact, _bid_ord_exact = _split_bid_no_ord(bid_no_filter)
    all_scope_retry_used = False
    direct_bid_lookup_used = False
    title_broad_retry_used = False
    demand_org_filter_tokens = _split_demand_org_filter_tokens(demand_org_filter)
    demand_org_match_samples: list[dict[str, str]] = []

    def _rows() -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for unique_key in found_order:
            row = found_map.get(unique_key)
            if row is None:
                continue
            rows.append({key: str(row.get(key, "") or "") for key in SEED_HEADERS})
        return rows

    def _build_result() -> SeedFetchResult:
        return SeedFetchResult(
            rows=_rows(),
            diagnostics=SeedFetchDiagnostics(
                requested_endpoint_mode=str(endpoint_mode or "").strip() or "construction",
                effective_endpoint_mode=mode,
                attempted_endpoints=sorted(attempted_endpoints),
                matched_endpoints=sorted(endpoint for endpoint in matched_endpoints if endpoint),
                all_scope_retry_used=all_scope_retry_used,
                direct_bid_lookup_used=direct_bid_lookup_used,
                title_broad_retry_used=title_broad_retry_used,
                title_broad_retry_allowed=allow_title_broad_retry,
                demand_org_filter_tokens=demand_org_filter_tokens,
                demand_org_match_samples=demand_org_match_samples,
            ),
        )

    def _append_row_from_item(item: dict, endpoint_name: str, *, enforce_bid_filter: bool = True) -> None:
        seed_row = _seed_row_from_item(item, endpoint_name=endpoint_name)
        bid_no = str(seed_row.get("bid_no") or "").strip()
        title = str(seed_row.get("project_name") or "")
        org_name = str(seed_row.get("org_name") or "").strip()
        demand_org_name = str(seed_row.pop("_demand_org_name", "") or "").strip()
        notice_org_name = str(seed_row.pop("_notice_org_name", "") or "").strip()
        unique_key = bid_no or f"{title}|{org_name}"
        if unique_key in excluded_keys:
            return
        if enforce_bid_filter and bid_filter_norm and bid_filter_norm not in _norm_token(bid_no):
            return
        if title_filter_norm and title_filter_norm not in _norm_text(title):
            return
        demand_org_matched = _matches_demand_org_filter(
            demand_org_filter,
            demand_org_name,
            notice_org_name,
            org_name,
        )
        if capture_demand_org_debug and demand_org_filter and len(demand_org_match_samples) < 20:
            demand_org_match_samples.append(
                {
                    "title": title,
                    "bid_no": bid_no,
                    "demand_org_filter": demand_org_filter,
                    "demand_org_name": demand_org_name,
                    "notice_org_name": notice_org_name,
                    "org_name": org_name,
                    "matched": "Y" if demand_org_matched else "N",
                }
            )
        if demand_org_filter and not demand_org_matched:
            return
        if not bid_no and not title:
            return
        notice_status = _derive_notice_status(
            title=title,
            notice_kind_name=str(item.get("ntceKindNm") or ""),
        )
        seed_row["_notice_status"] = notice_status
        seed_row["_notice_kind_name"] = str(item.get("ntceKindNm") or "").strip()
        seed_row["_notice_ord_num"] = str(_notice_ord_num(seed_row.get("bid_ord", "")))
        seed_row["_notice_dt_sort"] = _notice_dt_sort_key(str(item.get("bidNtceDt") or ""))
        if notice_status == "cancelled":
            excluded_keys.add(unique_key)
            found_map.pop(unique_key, None)
            return
        matched_endpoints.add(str(seed_row.get("_matched_endpoint", "") or "").strip())
        current = found_map.get(unique_key)
        if current is None:
            found_map[unique_key] = seed_row
            found_order.append(unique_key)
            return
        if _should_replace_seed_notice(current, seed_row):
            found_map[unique_key] = seed_row

    def _build_params(
        page: int,
        bgn: str,
        end: str,
        use_server_title_filter: bool,
        include_bid_filter: bool,
    ) -> dict[str, object]:
        params: dict[str, object] = {
            "ServiceKey": service_key,
            "pageNo": page,
            "numOfRows": rows_per_page,
            "type": "json",
            "inqryDiv": "1",
            "inqryBgnDt": f"{bgn}0000",
            "inqryEndDt": f"{end}2359",
        }
        if bid_no_filter and include_bid_filter:
            params["bidNtceNo"] = bid_no_filter.strip()
        if title_filter and use_server_title_filter:
            params["bidNtceNm"] = title_filter.strip()
        return params

    def _process_page(
        *,
        endpoint_name: str,
        endpoint_url: str,
        params: dict[str, object],
        status_code: int,
        payload: dict | None,
        err_text: str,
        mode_label: str,
        include_bid_filter: bool,
    ) -> tuple[bool, int, bool]:
        if status_code == 429:
            quota_exceeded.add(endpoint_name)
            if progress_cb is not None:
                progress_cb(f"{endpoint_name} quota exceeded (429).")
            return False, 0, True
        if status_code == -1:
            raise RuntimeError(f"{endpoint_name} {err_text}")
        if status_code != 200:
            raise RuntimeError(f"{endpoint_name} HTTP error: {status_code} / {err_text}")
        if not isinstance(payload, dict):
            raise RuntimeError(f"{endpoint_name} {err_text or 'non-JSON response'}")

        result_code, result_msg = _api_header(payload)
        if result_code and result_code not in {"00", "03"}:
            raise RuntimeError(f"{endpoint_name} API error {result_code}: {result_msg}")

        items, total_count = _extract_items(payload)
        if not items and bid_no_filter and str(params.get("inqryDiv") or "") == "1":
            xml_items, xml_total = _try_xml_items_fallback(session, endpoint_url, params, timeout_sec=request_timeout_sec)
            if xml_items:
                items, total_count = xml_items, xml_total
                if progress_cb is not None:
                    progress_cb(f"{endpoint_name} xml fallback hit: rows={len(items)} totalCount={total_count}")
        if progress_cb is not None:
            progress_cb(
                f"{endpoint_name} [{mode_label}] {str(params.get('inqryBgnDt', ''))[:8]}~"
                f"{str(params.get('inqryEndDt', ''))[:8]} page {params.get('pageNo')}: "
                f"received {len(items)} items (totalCount={total_count})"
            )
        if not items:
            return False, total_count, False
        for item in items:
            _append_row_from_item(item, endpoint_name, enforce_bid_filter=include_bid_filter)
        return True, total_count, False

    def _fetch_page(
        *,
        endpoint_url: str,
        page: int,
        bgn: str,
        end: str,
        use_server_title_filter: bool,
        include_bid_filter: bool,
        use_shared_session: bool,
    ) -> tuple[dict[str, object], int, dict | None, str]:
        params = _build_params(page, bgn, end, use_server_title_filter, include_bid_filter)
        req_get = session.get if use_shared_session else requests.get
        try:
            response = run_with_transient_http_retries(
                lambda: req_get(endpoint_url, params=params, timeout=request_timeout_sec),
                should_retry_result=lambda value: is_transient_http_status(getattr(value, "status_code", 0)),
            )
        except Exception as exc:
            return params, -1, None, f"request failed: {exc}"
        if response.status_code != 200:
            return params, response.status_code, None, str(response.text[:200])
        try:
            return params, response.status_code, response.json(), ""
        except Exception:
            return params, response.status_code, None, f"non-JSON response: {response.text[:200]}"

    def _collect_direct_bid_lookup(endpoints: list[tuple[str, str]]) -> None:
        nonlocal direct_bid_lookup_used
        if not bid_no_exact:
            return
        direct_bid_lookup_used = True
        for endpoint_name, endpoint_url in endpoints:
            attempted_endpoints.add(endpoint_name)
            params = {
                "ServiceKey": service_key,
                "pageNo": 1,
                "numOfRows": rows_per_page,
                "type": "json",
                "inqryDiv": "2",
                "bidNtceNo": bid_no_exact,
            }
            try:
                response = run_with_transient_http_retries(
                    lambda: session.get(endpoint_url, params=params, timeout=request_timeout_sec),
                    should_retry_result=lambda value: is_transient_http_status(getattr(value, "status_code", 0)),
                )
            except Exception:
                continue
            if response.status_code == 429:
                quota_exceeded.add(endpoint_name)
                continue
            if response.status_code != 200:
                continue
            try:
                payload = response.json()
                items, total_count = _extract_items(payload)
            except Exception:
                items, total_count = [], 0
            if not items:
                xml_items, xml_total = _try_xml_items_fallback(session, endpoint_url, params, timeout_sec=request_timeout_sec)
                items, total_count = xml_items, xml_total
            if progress_cb is not None:
                progress_cb(
                    f"{endpoint_name} [direct-bid] bid={bid_no_exact}: "
                    f"received {len(items)} items (totalCount={total_count})"
                )
            for item in items:
                _append_row_from_item(item, endpoint_name)

    def _collect_one_pass(
        *,
        use_server_title_filter: bool,
        endpoints: list[tuple[str, str]],
        include_bid_filter: bool = True,
    ) -> None:
        mode_label = "server-title" if use_server_title_filter else "broad-local-title"
        for bgn, end in month_ranges:
            if early_stop_at > 0 and len(found_map) >= early_stop_at:
                return
            for endpoint_name, endpoint_url in endpoints:
                if early_stop_at > 0 and len(found_map) >= early_stop_at:
                    return
                attempted_endpoints.add(endpoint_name)
                first_params, first_status, first_payload, first_err = _fetch_page(
                    endpoint_url=endpoint_url,
                    page=1,
                    bgn=bgn,
                    end=end,
                    use_server_title_filter=use_server_title_filter,
                    include_bid_filter=include_bid_filter,
                    use_shared_session=True,
                )
                has_items, first_total_count, stop_endpoint = _process_page(
                    endpoint_name=endpoint_name,
                    endpoint_url=endpoint_url,
                    params=first_params,
                    status_code=first_status,
                    payload=first_payload,
                    err_text=first_err,
                    mode_label=mode_label,
                    include_bid_filter=include_bid_filter,
                )
                if stop_endpoint or not has_items:
                    continue

                page_limit = max_pages
                if first_total_count > 0:
                    page_limit = min(max_pages, max(1, (first_total_count + rows_per_page - 1) // rows_per_page))
                remaining_pages = list(range(2, page_limit + 1))
                if not remaining_pages:
                    continue

                worker_count = 1 if early_stop_at > 0 else min(SEED_PAGE_MAX_WORKERS, len(remaining_pages))
                if worker_count <= 1:
                    for page in remaining_pages:
                        if early_stop_at > 0 and len(found_map) >= early_stop_at:
                            break
                        params, status_code, payload, err_text = _fetch_page(
                            endpoint_url=endpoint_url,
                            page=page,
                            bgn=bgn,
                            end=end,
                            use_server_title_filter=use_server_title_filter,
                            include_bid_filter=include_bid_filter,
                            use_shared_session=True,
                        )
                        has_items, _, stop_endpoint = _process_page(
                            endpoint_name=endpoint_name,
                            endpoint_url=endpoint_url,
                            params=params,
                            status_code=status_code,
                            payload=payload,
                            err_text=err_text,
                            mode_label=mode_label,
                            include_bid_filter=include_bid_filter,
                        )
                        if stop_endpoint or not has_items:
                            break
                    continue

                with ThreadPoolExecutor(max_workers=worker_count) as executor:
                    futures = {
                        page: executor.submit(
                            _fetch_page,
                            endpoint_url=endpoint_url,
                            page=page,
                            bgn=bgn,
                            end=end,
                            use_server_title_filter=use_server_title_filter,
                            include_bid_filter=include_bid_filter,
                            use_shared_session=False,
                        )
                        for page in remaining_pages
                    }
                    for page in remaining_pages:
                        if early_stop_at > 0 and len(found_map) >= early_stop_at:
                            break
                        params, status_code, payload, err_text = futures[page].result()
                        has_items, _, stop_endpoint = _process_page(
                            endpoint_name=endpoint_name,
                            endpoint_url=endpoint_url,
                            params=params,
                            status_code=status_code,
                            payload=payload,
                            err_text=err_text,
                            mode_label=mode_label,
                            include_bid_filter=include_bid_filter,
                        )
                        if stop_endpoint or not has_items:
                            break

    mode = endpoint_mode if endpoint_mode in API_SCOPE_TO_ENDPOINTS else "construction"
    endpoint_set = API_SCOPE_TO_ENDPOINTS[mode]
    direct_endpoints = API_SCOPE_TO_DIRECT_ENDPOINTS[mode]
    primary_endpoints = endpoint_set["search"] if title_filter and not bid_no_filter else endpoint_set["all"]
    all_scope_endpoints = API_SCOPE_TO_ENDPOINTS["all"]
    all_scope_direct_endpoints = API_SCOPE_TO_DIRECT_ENDPOINTS["all"]

    if bid_no_filter:
        _collect_direct_bid_lookup(direct_endpoints)
        if found_map:
            return _build_result()

    _collect_one_pass(use_server_title_filter=True, endpoints=primary_endpoints)
    if bid_no_filter and title_filter and len(found_map) < broad_retry_found_threshold:
        _collect_one_pass(
            use_server_title_filter=True,
            endpoints=endpoint_set["search"],
            include_bid_filter=False,
        )
        if found_map:
            return _build_result()
    if title_filter and allow_title_broad_retry and len(found_map) < broad_retry_found_threshold:
        title_broad_retry_used = True
        if progress_cb is not None:
            progress_cb("No rows from direct title search. Retrying with broad scan + local title matching...")
        _collect_one_pass(
            use_server_title_filter=False,
            endpoints=endpoint_set["all"],
            include_bid_filter=not bid_no_filter,
        )

    if not found_map and mode != "all":
        all_scope_retry_used = True
        if progress_cb is not None:
            progress_cb("No rows from scoped endpoints. Retrying across all endpoint groups...")
        if bid_no_filter:
            _collect_direct_bid_lookup(all_scope_direct_endpoints)
            if found_map:
                return _build_result()
        fallback_primary = all_scope_endpoints["search"] if title_filter and not bid_no_filter else all_scope_endpoints["all"]
        _collect_one_pass(use_server_title_filter=True, endpoints=fallback_primary)
        if bid_no_filter and title_filter and len(found_map) < broad_retry_found_threshold:
            _collect_one_pass(
                use_server_title_filter=True,
                endpoints=all_scope_endpoints["search"],
                include_bid_filter=False,
            )
            if found_map:
                return _build_result()
        if title_filter and allow_title_broad_retry and len(found_map) < broad_retry_found_threshold:
            if progress_cb is not None:
                progress_cb("No rows from all-endpoint title search. Retrying broad scan across all endpoints...")
            _collect_one_pass(
                use_server_title_filter=False,
                endpoints=all_scope_endpoints["all"],
                include_bid_filter=not bid_no_filter,
            )

    all_attempted_quota = bool(attempted_endpoints) and attempted_endpoints.issubset(quota_exceeded)
    if not found_map and all_attempted_quota:
        raise AllEndpointsQuotaExceededError(sorted(quota_exceeded))
    return _build_result()


def write_seed_csv(rows: list[dict[str, str]], seed_path: Path) -> None:
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    with seed_path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(SEED_HEADERS))
        writer.writeheader()
        writer.writerows(rows)


def _api_header(payload: dict) -> tuple[str, str]:
    return _api_header_impl(payload)


def _extract_items(payload: dict) -> tuple[list[dict], int]:
    return _extract_items_impl(payload)


def _extract_items_from_xml(xml_text: str) -> tuple[list[dict], int]:
    return _extract_items_from_xml_impl(xml_text)


def _try_xml_items_fallback(
    session: requests.Session,
    endpoint_url: str,
    params: dict[str, object],
    timeout_sec: int,
) -> tuple[list[dict], int]:
    xml_params = dict(params)
    xml_params["type"] = "xml"
    try:
        response = run_with_transient_http_retries(
            lambda: session.get(endpoint_url, params=xml_params, timeout=timeout_sec),
            should_retry_result=lambda value: is_transient_http_status(getattr(value, "status_code", 0)),
        )
        if response.status_code != 200:
            return [], 0
        return _extract_items_from_xml(response.text)
    except Exception:
        return [], 0


def _iter_month_ranges(start_date: str, end_date: str) -> list[tuple[str, str]]:
    return _iter_month_ranges_impl(start_date, end_date)


def _split_bid_no_ord(value: str) -> tuple[str, str]:
    return _split_bid_no_ord_impl(value)


def _seed_row_from_item(item: dict, endpoint_name: str = "") -> dict[str, str]:
    return _build_seed_row_from_item_impl(
        item,
        endpoint_name=endpoint_name,
        attachment_field_count=ATTACHMENT_FIELD_COUNT,
        clean_notice_title_fn=_clean_notice_title,
        select_org_name_fn=_select_org_name,
        extract_yyyymmdd_fn=_extract_yyyymmdd,
    )


def _derive_notice_status(*, title: str, notice_kind_name: str) -> str:
    return _derive_notice_status_impl(title=title, notice_kind_name=notice_kind_name)


def _notice_ord_num(value: str | object) -> int:
    return _notice_ord_num_impl(value)


def _notice_dt_sort_key(value: str | object) -> str:
    return _notice_dt_sort_key_impl(value)


def _endpoint_priority(endpoint_name: str) -> int:
    return _endpoint_priority_impl(endpoint_name)


def _notice_status_priority(value: str | object) -> int:
    return _notice_status_priority_impl(value)


def _should_replace_seed_notice(current: dict[str, str], candidate: dict[str, str]) -> bool:
    return _should_replace_seed_notice_impl(current, candidate)


def _select_org_name(demand_org_name: str, notice_org_name: str) -> str:
    return _select_org_name_impl(demand_org_name, notice_org_name)


def _norm_token(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(value or "")).upper()


def _norm_text(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", str(value or "")).lower()


def _split_demand_org_filter_tokens(value: str) -> list[str]:
    return _split_demand_org_filter_tokens_impl(value)


def _expand_demand_org_aliases(value: str) -> set[str]:
    return _expand_demand_org_aliases_impl(value, region_alias_groups=REGION_ALIAS_GROUPS)


def _matches_demand_org_filter(filter_text: str, *org_values: str) -> bool:
    return _matches_demand_org_filter_impl(filter_text, *org_values, region_alias_groups=REGION_ALIAS_GROUPS)


def _clean_notice_title(raw_title: str) -> str:
    return _clean_notice_title_impl(raw_title, title_paren_noise_tokens=TITLE_PAREN_NOISE_TOKENS)


def _extract_yyyymmdd(*values: object) -> str:
    return _extract_yyyymmdd_impl(*values)
