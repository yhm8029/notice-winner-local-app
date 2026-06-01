from __future__ import annotations

import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from pathlib import Path

from .native_contract_lookup_eais_runtime import _extract_contract_amount_int
from .native_contract_lookup_eais_runtime import _extract_duration_days
from .native_contract_lookup_eais_runtime import _normalize_eais_amount
from .native_contract_lookup_eais_runtime import _parse_corp_list_company
from .native_contract_lookup_eais_runtime import _parse_ymd_flexible
from .native_contract_lookup_eais_runtime import _post_eais_json
from .native_contract_lookup_eais_runtime import _resolve_eais_winner_name
from .native_contract_lookup_hub_runtime import _get_hub_result_candidates_via_powershell as _get_hub_result_candidates_via_powershell_impl
from .native_contract_lookup_lofin_runtime import _extract_lofin_openapi_error as _extract_lofin_openapi_error_impl
from .native_contract_lookup_lofin_runtime import _extract_lofin_openapi_rows as _extract_lofin_openapi_rows_impl
from .native_contract_lookup_lofin_runtime import _is_lofin_success_code as _is_lofin_success_code_impl
from .native_contract_lookup_lofin_runtime import _normalize_lofin_openapi_row as _normalize_lofin_openapi_row_impl
from .native_contract_lookup_match_runtime import _contract_target_match_score as _contract_target_match_score_impl
from .native_contract_lookup_match_runtime import _norm_bid_token as _norm_bid_token_impl
from .native_contract_lookup_match_runtime import _norm_text as _norm_text_impl
from .native_contract_lookup_match_runtime import _normalize_hub_result_candidates
from .native_contract_lookup_match_runtime import _pick_best_g2b_contract_hit as _pick_best_g2b_contract_hit_impl
from .native_contract_lookup_match_runtime import _pick_best_g2b_contract_hit_by_bid_no as _pick_best_g2b_contract_hit_by_bid_no_impl
from .native_contract_lookup_match_runtime import _pick_best_lofin_hit as _pick_best_lofin_hit_impl
from .native_contract_lookup_match_runtime import _repair_utf8_mojibake as _repair_utf8_mojibake_impl
from .native_contract_lookup_match_runtime import _text_overlap_ratio as _text_overlap_ratio_impl
from .native_contract_lookup_match_runtime import _to_lookup_result as _to_lookup_result_impl
from .native_contract_lookup_provider_runtime import _append_rows as _append_rows_impl
from .native_contract_lookup_provider_runtime import _extract_g2b_items as _extract_g2b_items_impl
from .native_contract_lookup_provider_runtime import _fetch_eais_best_candidate_for_query_year as _fetch_eais_best_candidate_for_query_year_impl
from .native_contract_lookup_provider_runtime import _fetch_lofin_contract_rows as _fetch_lofin_contract_rows_impl
from .native_contract_lookup_provider_runtime import _get_json_via_powershell as _get_json_via_powershell_impl
from .native_contract_lookup_provider_runtime import _request_contract_payload as _request_contract_payload_impl
from .native_contract_lookup_provider_runtime import _resolve_lofin_openapi_key as _resolve_lofin_openapi_key_impl
from .native_contract_lookup_provider_runtime import _search_hub_result_candidates as _search_hub_result_candidates_impl
from .native_contract_lookup_query_helpers_runtime import _build_core_project_queries
from .native_contract_lookup_query_helpers_runtime import _build_hub_project_queries
from .native_contract_lookup_query_helpers_runtime import _build_lofin_query_variants
from .native_contract_lookup_query_helpers_runtime import _build_query_variants
from .native_contract_lookup_query_helpers_runtime import _strip_project_suffix_noise
from .native_contract_lookup_query_runtime import _build_lofin_date_hints
from .native_contract_lookup_query_runtime import _is_education_org_name
from .native_contract_lookup_query_runtime import _is_generic_project_term
from .native_contract_lookup_query_runtime import _is_local_government_org_name
from .native_contract_lookup_query_runtime import _is_yyyymmdd
from .native_contract_lookup_query_runtime import _resolve_date_window
from .native_contract_lookup_query_runtime import _should_run_query_sweep
from .native_contract_lookup_core_runtime_state import ContractLookupMeta
from .native_contract_lookup_core_runtime_state import ContractLookupResult
from .native_contract_lookup_core_runtime_state import EAIS_BASE_URL
from .native_contract_lookup_core_runtime_state import EAIS_DETAIL_API_URL
from .native_contract_lookup_core_runtime_state import EAIS_LIST_API_URL
from .native_contract_lookup_core_runtime_state import EAIS_LIST_MAX_WORKERS
from .native_contract_lookup_core_runtime_state import EAIS_LIST_REFERER
from .native_contract_lookup_core_runtime_state import EAIS_PARTICIPANT_API_URL
from .native_contract_lookup_core_runtime_state import EAIS_VIEW_REFERER
from .native_contract_lookup_core_runtime_state import G2B_CONTRACT_ENDPOINTS
from .native_contract_lookup_core_runtime_state import HUB_AWARD_LIST_URL
from .native_contract_lookup_core_runtime_state import HUB_LIST_URL
from .native_contract_lookup_core_runtime_state import HUB_MAX_SEARCH_RESULTS
from .native_contract_lookup_core_runtime_state import HUB_RESULT_SCHDL_SN
from .native_contract_lookup_core_runtime_state import HUB_RESULT_TAB_NO
from .native_contract_lookup_core_runtime_state import LOFIN_CONTRACT_KIND_NAME
from .native_contract_lookup_core_runtime_state import LOFIN_CONTRACT_OPENAPI_URL
from .native_contract_lookup_core_runtime_state import LOFIN_DATE_SWEEP_MAX_WORKERS
from .native_contract_lookup_core_runtime_state import LOFIN_GLOBAL_MAX_CONCURRENCY
from .native_contract_lookup_core_runtime_state import LOFIN_OPENAPI_KEY_ENV_NAMES
from .native_contract_lookup_core_runtime_state import LOFIN_TOTAL_SWEEP_TIMEOUT_SEC
from .native_contract_lookup_core_runtime_state import _LOFIN_GLOBAL_SEMAPHORE
from .native_contract_lookup_core_runtime_state import _LofinRuntimeStats
from .native_contract_lookup_core_runtime_state import _merge_contract_lookup_meta
from .native_contract_lookup_core_runtime_state import get_last_contract_lookup_meta
from .native_contract_lookup_core_runtime_state import _set_last_contract_lookup_meta
from .native_contract_lookup_resolution_runtime import resolve_ordered_contract_lookup_fallbacks
from .native_seed_backend import resolve_service_key

_LOFIN_FORCE_POWERSHELL_GET = False


def resolve_contract_by_bid_no(
    *,
    bid_no: str,
    project_name_norm: str,
    announce_date: str = "",
    org_name: str = "",
    timeout_sec: float = 20.0,
    enable_query_sweep: bool = False,
) -> ContractLookupResult | None:
    global _LOFIN_FORCE_POWERSHELL_GET
    # Keep SSL fallback scoped to a single lookup so earlier failures do not
    # force later unrelated lookups into a sticky transport mode.
    _LOFIN_FORCE_POWERSHELL_GET = False
    _set_last_contract_lookup_meta(ContractLookupMeta())
    service_key = resolve_service_key()
    bid_text = str(bid_no or "").strip()
    if service_key and bid_text:
        rows: list[dict] = []
        seen: set[str] = set()
        for endpoint_name, endpoint_url, _query_param in G2B_CONTRACT_ENDPOINTS:
            _append_rows(
                rows=rows,
                seen=seen,
                payload=_request_contract_payload(
                    endpoint_url=endpoint_url,
                    params={
                        "ServiceKey": service_key,
                        "pageNo": 1,
                        "numOfRows": 50,
                        "type": "json",
                        "inqryDiv": "4",
                        "ntceNo": bid_text,
                    },
                    timeout_sec=timeout_sec,
                ),
            )
        hit = _pick_best_g2b_contract_hit_by_bid_no(rows, bid_no=bid_text, project_name_norm=project_name_norm)
        if hit is not None:
            _set_last_contract_lookup_meta(ContractLookupMeta(contract_lookup_path="direct_hit"))
            return hit

        query_sweep_used = False
        if _should_run_query_sweep(
            enable_query_sweep=enable_query_sweep,
            org_name=org_name,
            project_name_norm=project_name_norm,
        ):
            date_window = _resolve_date_window(announce_date)
            project_queries = _build_query_variants(project_name_norm)
        else:
            date_window = None
            project_queries = []
        if date_window and project_queries:
            query_sweep_used = True
            bgn_date, end_date = date_window
            for query in project_queries:
                for endpoint_name, endpoint_url, query_param in G2B_CONTRACT_ENDPOINTS:
                    _append_rows(
                        rows=rows,
                        seen=seen,
                        payload=_request_contract_payload(
                            endpoint_url=endpoint_url,
                            params={
                                "ServiceKey": service_key,
                                "pageNo": 1,
                                "numOfRows": 50,
                                "type": "json",
                                "inqryDiv": "1",
                                "inqryBgnDt": f"{bgn_date}0000",
                                "inqryEndDt": f"{end_date}2359",
                                query_param: query,
                            },
                            timeout_sec=timeout_sec,
                        ),
                    )
                hit = _pick_best_g2b_contract_hit(rows, project_name_norm=project_name_norm)
                if hit is not None:
                    _set_last_contract_lookup_meta(
                        ContractLookupMeta(
                            contract_lookup_path="query_sweep_hit",
                            query_sweep_used=True,
                            query_sweep_hit=True,
                        )
                    )
                    return hit
        if query_sweep_used:
            _set_last_contract_lookup_meta(
                ContractLookupMeta(
                    contract_lookup_path="no_hit",
                    query_sweep_used=True,
                    query_sweep_hit=False,
                )
            )

    return resolve_ordered_contract_lookup_fallbacks(
        project_name_norm=project_name_norm,
        announce_date=announce_date,
        timeout_sec=timeout_sec,
        org_name=org_name,
        resolve_eais_contract_hit_fn=_resolve_eais_contract_hit,
        resolve_hub_result_hit_fn=_resolve_hub_result_hit,
        resolve_lofin_contract_hit_fn=_resolve_lofin_contract_hit,
        is_education_org_name_fn=_is_education_org_name,
    )


def _request_contract_payload(*, endpoint_url: str, params: dict[str, object], timeout_sec: float) -> dict:
    return _request_contract_payload_impl(
        endpoint_url=endpoint_url,
        params=params,
        timeout_sec=timeout_sec,
    )


def _append_rows(*, rows: list[dict], seen: set[str], payload: dict) -> None:
    _append_rows_impl(rows=rows, seen=seen, payload=payload)


def _extract_g2b_items(payload: dict) -> list[dict]:
    return _extract_g2b_items_impl(payload)


def _resolve_lofin_openapi_key(explicit_key: str = "") -> str:
    return _resolve_lofin_openapi_key_impl(
        explicit_key=explicit_key,
        env_names=LOFIN_OPENAPI_KEY_ENV_NAMES,
    )


def _set_lofin_force_powershell_get(value: bool) -> None:
    global _LOFIN_FORCE_POWERSHELL_GET
    _LOFIN_FORCE_POWERSHELL_GET = bool(value)


def _fetch_lofin_contract_rows(
    *,
    query: str,
    contract_date_hint: str,
    timeout_sec: float,
    max_rows: int = 25,
    max_pages: int = 4,
    stats: _LofinRuntimeStats | None = None,
) -> list[dict]:
    return _fetch_lofin_contract_rows_impl(
        query=query,
        contract_date_hint=contract_date_hint,
        timeout_sec=timeout_sec,
        max_rows=max_rows,
        max_pages=max_pages,
        stats=stats,
        force_powershell_get=_LOFIN_FORCE_POWERSHELL_GET,
        set_force_powershell_get_fn=_set_lofin_force_powershell_get,
        resolve_lofin_openapi_key_fn=_resolve_lofin_openapi_key,
        is_yyyymmdd_fn=_is_yyyymmdd,
        global_semaphore=_LOFIN_GLOBAL_SEMAPHORE,
        contract_openapi_url=LOFIN_CONTRACT_OPENAPI_URL,
        contract_kind_name=LOFIN_CONTRACT_KIND_NAME,
        get_json_via_powershell_fn=_get_json_via_powershell,
        extract_lofin_openapi_error_fn=_extract_lofin_openapi_error,
        extract_lofin_openapi_rows_fn=_extract_lofin_openapi_rows,
        normalize_lofin_openapi_row_fn=_normalize_lofin_openapi_row,
    )


def _get_json_via_powershell(url: str, params: dict[str, object], timeout_sec: float) -> dict | None:
    return _get_json_via_powershell_impl(url, params, timeout_sec)


def _pick_best_g2b_contract_hit_by_bid_no(rows: list[dict], *, bid_no: str, project_name_norm: str) -> ContractLookupResult | None:
    return _pick_best_g2b_contract_hit_by_bid_no_impl(
        rows,
        bid_no=bid_no,
        project_name_norm=project_name_norm,
        pick_best_g2b_contract_hit_fn=lambda candidates, pname: _pick_best_g2b_contract_hit(
            candidates,
            project_name_norm=pname,
        ),
    )


def _pick_best_lofin_hit(rows: list[dict], *, project_name_norm: str) -> ContractLookupResult | None:
    return _pick_best_lofin_hit_impl(
        rows,
        project_name_norm=project_name_norm,
        is_generic_project_term_fn=_is_generic_project_term,
        result_factory=ContractLookupResult,
    )


def _pick_best_g2b_contract_hit(rows: list[dict], *, project_name_norm: str) -> ContractLookupResult | None:
    return _pick_best_g2b_contract_hit_impl(
        rows,
        project_name_norm=project_name_norm,
        is_generic_project_term_fn=_is_generic_project_term,
        contract_target_match_score_fn=lambda pname, tname, row: _contract_target_match_score(
            pname,
            tname,
            row=row,
        ),
        to_lookup_result_fn=_to_lookup_result,
    )


def _to_lookup_result(row: dict, score: float) -> ContractLookupResult:
    return _to_lookup_result_impl(
        row,
        score,
        parse_corp_list_company_fn=_parse_corp_list_company,
        extract_duration_days_fn=_extract_duration_days,
        result_factory=ContractLookupResult,
    )


def _contract_target_match_score(project_name_norm: str, target_name: str, row: dict | None = None) -> float:
    return _contract_target_match_score_impl(
        project_name_norm,
        target_name,
        row=row,
        strip_project_suffix_noise_fn=_strip_project_suffix_noise,
        extract_contract_amount_int_fn=_extract_contract_amount_int,
    )


def _resolve_eais_contract_hit(
    *,
    project_name_norm: str,
    announce_date: str,
    timeout_sec: float,
) -> ContractLookupResult | None:
    query_variants = _build_query_variants(project_name_norm)[:3]
    if not query_variants:
        return None

    years: list[str] = [""]
    base_dt = _parse_ymd_flexible(announce_date)
    if base_dt is not None:
        years = [base_dt.strftime("%Y")]

    eais_timeout = max(10.0, float(timeout_sec))
    combos = [(query, year) for query in query_variants for year in years]
    best_row: dict | None = None
    best_score = 0.0
    best_target = ""
    worker_count = min(EAIS_LIST_MAX_WORKERS, max(1, len(combos)))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [
            executor.submit(
                _fetch_eais_best_candidate_for_query_year,
                project_name_norm=project_name_norm,
                query=query,
                year=year,
                timeout_sec=eais_timeout,
            )
            for query, year in combos
        ]
        for future in as_completed(futures):
            row, score, target = future.result()
            if row is not None and score > best_score:
                best_row = row
                best_score = score
                best_target = target

    if best_row is None or best_score < 0.45:
        return None

    seq = str(best_row.get("pssrpPblancSeqno") or "").strip()
    with ThreadPoolExecutor(max_workers=2) as executor:
        detail_future = executor.submit(
            _post_eais_json,
            EAIS_DETAIL_API_URL,
            {"pssrpPblancSeqno": seq},
            EAIS_VIEW_REFERER,
            eais_timeout,
            eais_base_url=EAIS_BASE_URL,
        )
        winner_future = executor.submit(
            _resolve_eais_winner_name,
            seq,
            timeout_sec=eais_timeout,
            participant_api_url=EAIS_PARTICIPANT_API_URL,
            view_referer=EAIS_VIEW_REFERER,
            eais_base_url=EAIS_BASE_URL,
        )
        detail = detail_future.result()
        winner_name = winner_future.result()
    detail_data = detail.get("data") if isinstance(detail, dict) else {}
    if not isinstance(detail_data, dict):
        detail_data = {}
    if not winner_name:
        winner_name = str(
            detail_data.get("winPssrpPartinOfficeNm")
            or detail_data.get("winPssrpPartinWnpzNm")
            or ""
        ).strip()
    if not winner_name:
        return None

    target_name = str(detail_data.get("pssrpPblancNm") or best_target or "").strip()
    contract_date = str(
        detail_data.get("winPrdctPresnatnDate")
        or detail_data.get("pssrpJdgmnStrtDate")
        or detail_data.get("pssrpPblancDate")
        or detail_data.get("pssrpPblancDt")
        or ""
    ).strip()
    contract_amount = _normalize_eais_amount(
        detail_data.get("pssrpCntrwkAmt")
        or detail_data.get("pssrpPrrngAmt")
        or best_row.get("pssrpCntrwkAmt")
        or best_row.get("pssrpPrrngAmt")
    )
    return ContractLookupResult(
        contract_name=winner_name,
        contract_date=contract_date,
        contract_amount=contract_amount,
        target_name=target_name,
        inst_name=str(detail_data.get("pssrpKikNm") or best_row.get("pssrpKikNm") or "").strip(),
        match_score=min(1.0, max(0.0, float(best_score))),
        source_type="eais_web",
    )


def _resolve_hub_result_hit(
    *,
    project_name_norm: str,
    timeout_sec: float,
) -> ContractLookupResult | None:
    best_office = ""
    best_title = ""
    best_score = 0.0
    for query in _build_hub_project_queries(project_name_norm):
        for candidate in _search_hub_result_candidates(query=query, timeout_sec=timeout_sec):
            title = str(candidate.get("title") or "").strip()
            office = str(candidate.get("winnerOffice") or "").strip()
            if not title or not office:
                continue
            score = _contract_target_match_score(project_name_norm, title)
            if score > best_score:
                best_office = office
                best_title = title
                best_score = score
        if best_score >= 0.82:
            break
    if not best_office or best_score < 0.45:
        return None
    return ContractLookupResult(
        contract_name=best_office,
        target_name=best_title,
        match_score=min(1.0, max(0.0, float(best_score))),
        source_type="hub_result",
    )


def _search_hub_result_candidates(*, query: str, timeout_sec: float) -> list[dict]:
    return _search_hub_result_candidates_impl(
        query=query,
        timeout_sec=timeout_sec,
        get_hub_result_candidates_fn=_get_hub_result_candidates_via_powershell,
    )


def _repair_utf8_mojibake(text: str) -> str:
    return _repair_utf8_mojibake_impl(text)


def _get_hub_result_candidates_via_powershell(query: str, timeout_sec: float) -> list[dict] | None:
    return _get_hub_result_candidates_via_powershell_impl(
        query,
        timeout_sec,
        helper_path=Path(__file__).with_name("hub_result_lookup.ps1"),
        max_results=HUB_MAX_SEARCH_RESULTS,
        normalize_candidates_fn=_normalize_hub_result_candidates,
    )


def _normalize_lofin_openapi_row(item: dict) -> dict:
    return _normalize_lofin_openapi_row_impl(item)


def _extract_lofin_openapi_rows(payload: dict) -> list[dict]:
    return _extract_lofin_openapi_rows_impl(payload)


def _extract_lofin_openapi_error(payload: dict) -> tuple[str, str]:
    return _extract_lofin_openapi_error_impl(payload)


def _is_lofin_success_code(code: str) -> bool:
    return _is_lofin_success_code_impl(code)



def _resolve_lofin_contract_hit(*, project_name_norm: str, announce_date: str, timeout_sec: float) -> ContractLookupResult | None:
    stats = _LofinRuntimeStats(
        semaphore_limit=LOFIN_GLOBAL_MAX_CONCURRENCY,
        budget_seconds=LOFIN_TOTAL_SWEEP_TIMEOUT_SEC,
    )
    openapi_key = _resolve_lofin_openapi_key()
    if not openapi_key:
        _set_last_contract_lookup_meta(stats.to_meta())
        return None
    date_hints = _build_lofin_date_hints(announce_date)
    if not date_hints:
        _set_last_contract_lookup_meta(stats.to_meta())
        return None
    rows: list[dict] = []
    seen: set[str] = set()
    project_queries = _build_lofin_query_variants(project_name_norm)
    if not project_queries:
        _set_last_contract_lookup_meta(stats.to_meta())
        return None
    sweep_deadline = time.monotonic() + LOFIN_TOTAL_SWEEP_TIMEOUT_SEC

    def _fetch_rows_for_date(date_hint: str) -> list[dict]:
        stats.note_dates_examined(1)
        local_rows: list[dict] = []
        for query in project_queries:
            remaining = sweep_deadline - time.monotonic()
            if remaining <= 0:
                stats.note_budget_exhausted()
                return local_rows
            page_rows = _fetch_lofin_contract_rows(
                query=query,
                contract_date_hint=date_hint,
                timeout_sec=min(timeout_sec, max(1.0, remaining)),
                stats=stats,
            )
            if page_rows:
                local_rows.extend(page_rows)
        return local_rows

    worker_count = min(LOFIN_DATE_SWEEP_MAX_WORKERS, max(1, len(date_hints)))
    stats.date_workers = worker_count
    for idx in range(0, len(date_hints), worker_count):
        if time.monotonic() >= sweep_deadline:
            stats.note_budget_exhausted()
            break
        batch = date_hints[idx : idx + worker_count]
        with ThreadPoolExecutor(max_workers=len(batch)) as executor:
            futures = [executor.submit(_fetch_rows_for_date, date_hint) for date_hint in batch]
            for future in futures:
                for row in future.result():
                    norm = _normalize_lofin_openapi_row(row)
                    dedupe_key = "|".join(
                        [
                            str(norm.get("ctrtLdgrMngNo") or ""),
                            str(norm.get("ctrtTrgtNm") or ""),
                            str(norm.get("cltNm") or ""),
                            str(norm.get("smzCtrtYmd") or ""),
                        ]
                    )
                    if not dedupe_key or dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    rows.append(norm)
        hit = _pick_best_lofin_hit(rows, project_name_norm=project_name_norm)
        if hit is not None and hit.match_score >= 0.8:
            stats.note_hit(date_hint=hit.contract_date, best_score=hit.match_score)
            _set_last_contract_lookup_meta(stats.to_meta())
            return hit
    hit = _pick_best_lofin_hit(rows, project_name_norm=project_name_norm)
    if hit is not None:
        stats.note_hit(date_hint=hit.contract_date, best_score=hit.match_score)
        _set_last_contract_lookup_meta(stats.to_meta())
        return hit
    _set_last_contract_lookup_meta(stats.to_meta())
    return None


def _fetch_eais_best_candidate_for_query_year(
    *,
    project_name_norm: str,
    query: str,
    year: str,
    timeout_sec: float,
) -> tuple[dict | None, float, str]:
    return _fetch_eais_best_candidate_for_query_year_impl(
        project_name_norm=project_name_norm,
        query=query,
        year=year,
        timeout_sec=timeout_sec,
        post_eais_json_fn=_post_eais_json,
        list_api_url=EAIS_LIST_API_URL,
        referer=EAIS_LIST_REFERER,
        eais_base_url=EAIS_BASE_URL,
        score_fn=_contract_target_match_score,
    )

def _norm_bid_token(value: str) -> str:
    return _norm_bid_token_impl(value)


def _norm_text(value: str) -> str:
    return _norm_text_impl(value)


def _text_overlap_ratio(left: str, right: str) -> float:
    return _text_overlap_ratio_impl(left, right)
