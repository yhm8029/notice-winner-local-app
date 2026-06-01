from __future__ import annotations

import json
import os
import re
from datetime import datetime

import requests


def _parse_corp_list_company(corp_list: str) -> str:
    text = str(corp_list or "").strip()
    if not text:
        return ""
    best_name = ""
    best_score = -1.0
    for block in re.findall(r"\[([^\[\]]+)\]", text):
        parts = [part.strip() for part in block.split("^")]
        if len(parts) < 4:
            continue
        role = parts[1] if len(parts) > 1 else ""
        company = parts[3] if len(parts) > 3 else ""
        if not company and len(parts) > 7:
            company = parts[7]
        if not company:
            continue
        share = 0.0
        share_txt = parts[6] if len(parts) > 6 else ""
        try:
            share = float(re.sub(r"[^0-9.]", "", share_txt) or 0.0)
        except Exception:
            share = 0.0
        score = share
        if "주계약업체" in role:
            score += 1000.0
        elif "단독" in role:
            score += 500.0
        if score > best_score:
            best_score = score
            best_name = company
    return best_name


def _extract_contract_amount_int(row: dict) -> int:
    for key in ("totCntrctAmt", "thtmCntrctAmt", "cntrctAmt", "cntrctAmount"):
        raw = str((row or {}).get(key) or "").replace(",", "").strip()
        if not raw:
            continue
        try:
            value = int(float(raw))
        except Exception:
            continue
        if value > 0:
            return value
    return 0


def _extract_duration_days(text: str) -> int:
    source = str(text or "")
    match = re.search(r"(\d{1,3})\s*일", source)
    if match:
        try:
            return int(match.group(1))
        except Exception:
            return 0
    match = re.search(r"(\d{1,3})\s*개월", source)
    if match:
        try:
            return int(match.group(1)) * 30
        except Exception:
            return 0
    return 0


def _build_eais_headers(referer: str, *, eais_base_url: str) -> dict[str, str]:
    unt_clsf = str(os.getenv("EAIS_UNTCLSFCD") or "1000").strip() or "1000"
    return {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": eais_base_url,
        "Referer": referer,
        "UntClsfCd": unt_clsf,
        "User-Agent": "Mozilla/5.0",
    }


def _post_eais_json(
    url: str,
    payload: dict[str, object],
    referer: str,
    timeout_sec: float,
    *,
    eais_base_url: str,
) -> dict:
    try:
        response = requests.post(
            url,
            headers=_build_eais_headers(referer, eais_base_url=eais_base_url),
            data=json.dumps(payload, ensure_ascii=False),
            timeout=timeout_sec,
        )
        if getattr(response, "status_code", 200) >= 400:
            return {}
        data = response.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _normalize_eais_amount(value: object) -> str:
    digits = re.sub(r"[^0-9]", "", str(value or ""))
    if not digits:
        return ""
    try:
        return str(int(digits))
    except Exception:
        return digits


def _parse_ymd_flexible(value: str) -> datetime | None:
    text = str(value or "").strip()
    match = re.search(r"(\d{4})[./-]?(\d{2})[./-]?(\d{2})", text)
    if not match:
        return None
    try:
        return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except Exception:
        return None


def _resolve_eais_winner_name(
    pssrp_pblanc_seqno: str,
    *,
    timeout_sec: float,
    participant_api_url: str,
    view_referer: str,
    eais_base_url: str,
) -> str:
    seq = str(pssrp_pblanc_seqno or "").strip()
    if not seq:
        return ""
    data = _post_eais_json(
        participant_api_url,
        {"pssrpPblancSeqno": seq},
        referer=view_referer,
        timeout_sec=timeout_sec,
        eais_base_url=eais_base_url,
    )
    participant_list = ((data.get("dataMap") or {}).get("pssrpPartcptnList") or []) if isinstance(data, dict) else []
    if not isinstance(participant_list, list):
        return ""

    for row in participant_list:
        if not isinstance(row, dict):
            continue
        if str(row.get("pssrpPartinWnpzCd") or "").strip() != "1":
            continue
        office = str(row.get("pssrpPartinOfficeNm") or "").strip()
        enterprise = str(row.get("pssrpPartinEntprNm") or "").strip()
        if office:
            return office
        if enterprise:
            return enterprise

    for row in participant_list:
        if not isinstance(row, dict):
            continue
        office = str(row.get("pssrpPartinOfficeNm") or "").strip()
        if office:
            return office
    return ""
