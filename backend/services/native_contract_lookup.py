from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

import requests

from . import native_contract_lookup_impl as _impl

_REEXPORTED_NAMES = (
    "ContractLookupMeta",
    "ContractLookupResult",
    "EAIS_BASE_URL",
    "EAIS_DETAIL_API_URL",
    "EAIS_LIST_API_URL",
    "EAIS_LIST_MAX_WORKERS",
    "EAIS_LIST_REFERER",
    "EAIS_PARTICIPANT_API_URL",
    "EAIS_VIEW_REFERER",
    "G2B_CONTRACT_ENDPOINTS",
    "LOFIN_CONTRACT_KIND_NAME",
    "LOFIN_CONTRACT_OPENAPI_URL",
    "LOFIN_DATE_SWEEP_MAX_WORKERS",
    "LOFIN_GLOBAL_MAX_CONCURRENCY",
    "LOFIN_TOTAL_SWEEP_TIMEOUT_SEC",
    "_LofinRuntimeStats",
    "_LOFIN_GLOBAL_SEMAPHORE",
    "_append_rows",
    "_build_core_project_queries",
    "_build_hub_project_queries",
    "_build_lofin_date_hints",
    "_build_lofin_query_variants",
    "_build_query_variants",
    "_extract_lofin_openapi_error",
    "_extract_lofin_openapi_rows",
    "_is_education_org_name",
    "_is_yyyymmdd",
    "_merge_contract_lookup_meta",
    "_normalize_lofin_openapi_row",
    "_norm_text",
    "_pick_best_g2b_contract_hit",
    "_pick_best_g2b_contract_hit_by_bid_no",
    "_pick_best_lofin_hit",
    "_request_contract_payload",
    "_resolve_date_window",
    "_resolve_lofin_openapi_key",
    "_set_last_contract_lookup_meta",
    "_should_run_query_sweep",
    "get_last_contract_lookup_meta",
    "resolve_service_key",
)

for _name in _REEXPORTED_NAMES:
    globals()[_name] = getattr(_impl, _name)

_LOFIN_FORCE_POWERSHELL_GET = _impl._LOFIN_FORCE_POWERSHELL_GET


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
    _LOFIN_FORCE_POWERSHELL_GET = False
    _set_last_contract_lookup_meta(ContractLookupMeta())
    service_key = resolve_service_key()
    bid_text = str(bid_no or "").strip()
    if service_key and bid_text:
        rows: list[dict] = []
        seen: set[str] = set()
        for _endpoint_name, endpoint_url, _query_param in G2B_CONTRACT_ENDPOINTS:
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
                for _endpoint_name, endpoint_url, query_param in G2B_CONTRACT_ENDPOINTS:
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

    eais_hit = _resolve_eais_contract_hit(
        project_name_norm=project_name_norm,
        announce_date=announce_date,
        timeout_sec=timeout_sec,
    )
    if eais_hit is not None:
        previous = get_last_contract_lookup_meta()
        _set_last_contract_lookup_meta(_merge_contract_lookup_meta(previous, contract_lookup_path="eais_hit"))
        return eais_hit

    previous = get_last_contract_lookup_meta()
    hub_hit = _resolve_hub_result_hit(
        project_name_norm=project_name_norm,
        timeout_sec=timeout_sec,
    )
    if hub_hit is not None:
        _set_last_contract_lookup_meta(_merge_contract_lookup_meta(previous, contract_lookup_path="hub_hit"))
        return hub_hit

    if _is_education_org_name(org_name):
        previous = get_last_contract_lookup_meta()
        _set_last_contract_lookup_meta(_merge_contract_lookup_meta(previous, contract_lookup_path="no_hit"))
        return None

    previous = get_last_contract_lookup_meta()
    lofin_hit = _resolve_lofin_contract_hit(
        project_name_norm=project_name_norm,
        announce_date=announce_date,
        timeout_sec=timeout_sec,
    )
    lofin_meta = get_last_contract_lookup_meta()
    _set_last_contract_lookup_meta(
        _merge_contract_lookup_meta(
            previous,
            extra=lofin_meta,
            contract_lookup_path="lofin_hit" if lofin_hit is not None else "no_hit",
        )
    )
    return lofin_hit


def _fetch_lofin_contract_rows(
    *,
    query: str,
    contract_date_hint: str,
    timeout_sec: float,
    max_rows: int = 25,
    max_pages: int = 4,
    stats: _LofinRuntimeStats | None = None,
) -> list[dict]:
    global _LOFIN_FORCE_POWERSHELL_GET
    q = str(query or "").strip()
    date_hint = str(contract_date_hint or "").strip()
    openapi_key = _resolve_lofin_openapi_key()
    if not q or not _is_yyyymmdd(date_hint) or not openapi_key:
        return []

    out_rows: list[dict] = []
    seen: set[str] = set()
    for page_no in range(1, max_pages + 1):
        params = {
            "Key": openapi_key,
            "Type": "json",
            "pIndex": page_no,
            "pSize": max(10, min(100, max_rows)),
            "ctrt_trgt_nm": q,
            "smz_ctrt_ymd": date_hint,
            "ctrt_knd_nm": LOFIN_CONTRACT_KIND_NAME,
        }
        try:
            if _LOFIN_FORCE_POWERSHELL_GET:
                if stats is not None:
                    stats.note_powershell_used()
                with _LOFIN_GLOBAL_SEMAPHORE:
                    if stats is not None:
                        stats.note_request()
                        stats.begin_request()
                    try:
                        payload = _get_json_via_powershell(
                            LOFIN_CONTRACT_OPENAPI_URL,
                            params,
                            timeout_sec=timeout_sec,
                        )
                    finally:
                        if stats is not None:
                            stats.end_request()
                if not isinstance(payload, dict):
                    break
            else:
                with _LOFIN_GLOBAL_SEMAPHORE:
                    if stats is not None:
                        stats.note_request()
                        stats.begin_request()
                    try:
                        response = requests.get(
                            LOFIN_CONTRACT_OPENAPI_URL,
                            params=params,
                            timeout=timeout_sec,
                            headers={"User-Agent": "Mozilla/5.0"},
                        )
                    finally:
                        if stats is not None:
                            stats.end_request()
                response.raise_for_status()
                payload = response.json()
        except requests.exceptions.SSLError:
            _LOFIN_FORCE_POWERSHELL_GET = True
            if stats is not None:
                stats.note_ssl_fallback_used()
                stats.note_powershell_used()
            with _LOFIN_GLOBAL_SEMAPHORE:
                if stats is not None:
                    stats.note_request()
                    stats.begin_request()
                try:
                    payload = _get_json_via_powershell(
                        LOFIN_CONTRACT_OPENAPI_URL,
                        params,
                        timeout_sec=timeout_sec,
                    )
                finally:
                    if stats is not None:
                        stats.end_request()
            if not isinstance(payload, dict):
                break
        except requests.exceptions.Timeout:
            if stats is not None:
                stats.note_timeout()
            break
        except Exception:
            break
        if stats is not None:
            stats.note_page_fetched()
        err_code, _err_msg = _extract_lofin_openapi_error(payload if isinstance(payload, dict) else {})
        if err_code:
            break
        page_rows = _extract_lofin_openapi_rows(payload if isinstance(payload, dict) else {})
        if not page_rows:
            break
        if stats is not None:
            stats.note_nonempty_date(date_hint)
        before = len(out_rows)
        for row in page_rows:
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
            out_rows.append(norm)
        if len(out_rows) >= max_rows or len(out_rows) == before:
            break
    return out_rows[:max_rows]


def _get_json_via_powershell(url: str, params: dict[str, object], timeout_sec: float) -> dict | None:
    return _impl._get_json_via_powershell(url, params, timeout_sec)


def _resolve_eais_contract_hit(
    *,
    project_name_norm: str,
    announce_date: str,
    timeout_sec: float,
) -> ContractLookupResult | None:
    return _impl._resolve_eais_contract_hit(
        project_name_norm=project_name_norm,
        announce_date=announce_date,
        timeout_sec=timeout_sec,
    )


def _resolve_hub_result_hit(
    *,
    project_name_norm: str,
    timeout_sec: float,
) -> ContractLookupResult | None:
    return _impl._resolve_hub_result_hit(
        project_name_norm=project_name_norm,
        timeout_sec=timeout_sec,
    )


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


__all__ = list(_REEXPORTED_NAMES) + [
    "_LOFIN_FORCE_POWERSHELL_GET",
    "_fetch_lofin_contract_rows",
    "_get_json_via_powershell",
    "_resolve_eais_contract_hit",
    "_resolve_hub_result_hit",
    "_resolve_lofin_contract_hit",
    "resolve_contract_by_bid_no",
]
