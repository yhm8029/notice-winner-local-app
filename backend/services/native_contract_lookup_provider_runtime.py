from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlencode

import requests


def _extract_g2b_items(payload: dict) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    if "nkoneps.com.response.ResponseError" in payload:
        return []
    response = payload.get("response") if isinstance(payload, dict) else {}
    body = response.get("body") if isinstance(response, dict) else {}
    items = body.get("items") if isinstance(body, dict) else None
    if isinstance(items, dict):
        items = items.get("item")
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _append_rows(*, rows: list[dict], seen: set[str], payload: dict) -> None:
    for row in _extract_g2b_items(payload):
        dedupe_key = "|".join(
            [
                str(row.get("dcsnCntrctNo") or ""),
                str(row.get("untyCntrctNo") or ""),
                str(row.get("cntrctNm") or row.get("cnstwkNm") or ""),
                str(row.get("corpList") or ""),
                str(row.get("cntrctDate") or row.get("cntrctCnclsDate") or ""),
            ]
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        rows.append(dict(row))


def _request_contract_payload(*, endpoint_url: str, params: dict[str, object], timeout_sec: float) -> dict:
    try:
        response = requests.get(endpoint_url, params=params, timeout=timeout_sec)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}


def _resolve_lofin_openapi_key(
    *,
    explicit_key: str = "",
    env_names: tuple[str, ...],
) -> str:
    key = str(explicit_key or "").strip()
    if key:
        return key
    for env_name in env_names:
        env_val = str(os.getenv(env_name) or "").strip()
        if env_val:
            return env_val
    return ""


def _fetch_eais_best_candidate_for_query_year(
    *,
    project_name_norm: str,
    query: str,
    year: str,
    timeout_sec: float,
    post_eais_json_fn,
    list_api_url: str,
    referer: str,
    eais_base_url: str,
    score_fn,
) -> tuple[dict | None, float, str]:
    best_row: dict | None = None
    best_score = 0.0
    best_target = ""
    for page in range(0, 3):
        payload = {
            "pssrpPblancSidoCd": "",
            "pssrpPblancMthdCd": "",
            "pssrpKikTypeCd": "",
            "pssrpPblancPrposCd": "",
            "pssrpPblancScale": "",
            "pssrpDsgnAmt": "",
            "pssrpBildngTypeCd": "",
            "pssrpPblancRegYear": year,
            "pssrpPblancType": "pssrpPblancNm",
            "condition": query,
            "pssrpProgStatNm": "finJudgeRegist",
            "currentPage": page,
            "countPerPage": 15,
            "searchActiveYn": "Y",
            "gubun": "",
        }
        data = post_eais_json_fn(
            list_api_url,
            payload,
            referer=referer,
            timeout_sec=timeout_sec,
            eais_base_url=eais_base_url,
        )
        rows = data.get("dataList") if isinstance(data, dict) else []
        if not isinstance(rows, list):
            rows = []
        if not rows:
            if page > 0:
                break
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            target = str(row.get("pssrpPblancNm") or "").strip()
            if not target:
                continue
            score = score_fn(project_name_norm, target, row=row)
            if score > best_score:
                best_row = row
                best_score = score
                best_target = target
        if best_score >= 0.85:
            break
    return best_row, best_score, best_target


def _search_hub_result_candidates(
    *,
    query: str,
    timeout_sec: float,
    get_hub_result_candidates_fn,
) -> list[dict]:
    q = str(query or "").strip()
    if not q:
        return []
    return get_hub_result_candidates_fn(query=q, timeout_sec=timeout_sec) or []


def _fetch_lofin_contract_rows(
    *,
    query: str,
    contract_date_hint: str,
    timeout_sec: float,
    max_rows: int = 25,
    max_pages: int = 4,
    stats=None,
    force_powershell_get: bool = False,
    set_force_powershell_get_fn=None,
    resolve_lofin_openapi_key_fn,
    is_yyyymmdd_fn,
    global_semaphore,
    contract_openapi_url: str,
    contract_kind_name: str,
    get_json_via_powershell_fn,
    extract_lofin_openapi_error_fn,
    extract_lofin_openapi_rows_fn,
    normalize_lofin_openapi_row_fn,
    requests_get_fn=requests.get,
) -> list[dict]:
    q = str(query or "").strip()
    date_hint = str(contract_date_hint or "").strip()
    openapi_key = str(resolve_lofin_openapi_key_fn() or "").strip()
    if not q or not is_yyyymmdd_fn(date_hint) or not openapi_key:
        return []

    out_rows: list[dict] = []
    seen: set[str] = set()
    use_powershell = bool(force_powershell_get)
    for page_no in range(1, max_pages + 1):
        params = {
            "Key": openapi_key,
            "Type": "json",
            "pIndex": page_no,
            "pSize": max(10, min(100, max_rows)),
            "ctrt_trgt_nm": q,
            "smz_ctrt_ymd": date_hint,
            "ctrt_knd_nm": contract_kind_name,
        }
        try:
            if use_powershell:
                if stats is not None:
                    stats.note_powershell_used()
                with global_semaphore:
                    if stats is not None:
                        stats.note_request()
                        stats.begin_request()
                    try:
                        payload = get_json_via_powershell_fn(
                            contract_openapi_url,
                            params,
                            timeout_sec=timeout_sec,
                        )
                    finally:
                        if stats is not None:
                            stats.end_request()
                if not isinstance(payload, dict):
                    break
            else:
                with global_semaphore:
                    if stats is not None:
                        stats.note_request()
                        stats.begin_request()
                    try:
                        response = requests_get_fn(
                            contract_openapi_url,
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
            use_powershell = True
            if set_force_powershell_get_fn is not None:
                set_force_powershell_get_fn(True)
            if stats is not None:
                stats.note_ssl_fallback_used()
                stats.note_powershell_used()
            with global_semaphore:
                if stats is not None:
                    stats.note_request()
                    stats.begin_request()
                try:
                    payload = get_json_via_powershell_fn(
                        contract_openapi_url,
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
        err_code, _err_msg = extract_lofin_openapi_error_fn(payload if isinstance(payload, dict) else {})
        if err_code:
            break
        page_rows = extract_lofin_openapi_rows_fn(payload if isinstance(payload, dict) else {})
        if not page_rows:
            break
        if stats is not None:
            stats.note_nonempty_date(date_hint)
        before = len(out_rows)
        for row in page_rows:
            norm = normalize_lofin_openapi_row_fn(row)
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
    query = urlencode({key: "" if value is None else value for key, value in (params or {}).items()}, doseq=True)
    full_url = f"{url}?{query}" if query else url
    ps_script = rf"""
param(
    [Parameter(Mandatory=$true)][string]$Url,
    [double]$TimeoutSec = {float(timeout_sec)}
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = `
    [Net.SecurityProtocolType]::Tls12 -bor `
    [Net.SecurityProtocolType]::Tls11 -bor `
    [Net.SecurityProtocolType]::Tls
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$headers = @{{ 'User-Agent'='Mozilla/5.0'; 'Accept'='application/json' }}
$resp = Invoke-RestMethod -Uri $Url -Method Get -Headers $headers -TimeoutSec ([int][Math]::Ceiling($TimeoutSec))
$resp | ConvertTo-Json -Depth 20 -Compress
"""
    for shell_cmd in ("powershell", "pwsh"):
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                script_path = Path(temp_dir) / "lofin_get_retry.ps1"
                script_path.write_text(ps_script, encoding="utf-8-sig")
                proc = subprocess.run(
                    [
                        shell_cmd,
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(script_path),
                        "-Url",
                        full_url,
                        "-TimeoutSec",
                        str(timeout_sec),
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    timeout=max(10, int(timeout_sec) + 10),
                    check=False,
                )
        except FileNotFoundError:
            continue
        except Exception:
            continue

        if proc.returncode != 0:
            continue
        out = str(proc.stdout or "").strip()
        if not out:
            continue
        try:
            payload = json.loads(out)
        except Exception:
            start_obj = out.find("{")
            start_arr = out.find("[")
            starts = [pos for pos in (start_obj, start_arr) if pos >= 0]
            if not starts:
                continue
            start = min(starts)
            end = max(out.rfind("}"), out.rfind("]"))
            if end <= start:
                continue
            try:
                payload = json.loads(out[start : end + 1])
            except Exception:
                continue
        if isinstance(payload, dict):
            return payload
    return None
