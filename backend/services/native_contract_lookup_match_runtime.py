from __future__ import annotations

import re
from collections.abc import Callable


def _norm_bid_token(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(value or "")).upper()


def _norm_text(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip().lower()


def _text_overlap_ratio(left: str, right: str) -> float:
    a = _norm_text(left)
    b = _norm_text(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    grams_a = {a[i : i + 2] for i in range(max(1, len(a) - 1))} or {a}
    grams_b = {b[i : i + 2] for i in range(max(1, len(b) - 1))} or {b}
    return len(grams_a & grams_b) / float(max(1, min(len(grams_a), len(grams_b))))


def _contract_target_match_score(
    project_name_norm: str,
    target_name: str,
    row: dict | None = None,
    *,
    strip_project_suffix_noise_fn: Callable[[str], str],
    extract_contract_amount_int_fn: Callable[[dict], int],
) -> float:
    pnorm = _norm_text(project_name_norm)
    tnorm = _norm_text(target_name)
    if not pnorm or not tnorm:
        return 0.0
    overlap = _text_overlap_ratio(project_name_norm, target_name)
    exact = 1.0 if pnorm == tnorm else 0.0
    contains = 0.9 if (pnorm in tnorm or tnorm in pnorm) else 0.0
    score = max(overlap, exact, contains)
    stripped = _norm_text(strip_project_suffix_noise_fn(project_name_norm))
    if stripped and stripped in tnorm:
        score += 0.20
    if any(_norm_text(token) in tnorm for token in ("기본및실시설계", "실시설계", "설계용역", "건축설계")):
        score += 0.12
    amount = extract_contract_amount_int_fn(row or {})
    if amount >= 100000000:
        score += 0.03
    if amount >= 500000000:
        score += 0.03
    return max(0.0, score)


def _to_lookup_result(
    row: dict,
    score: float,
    *,
    parse_corp_list_company_fn: Callable[[str], str],
    extract_duration_days_fn: Callable[[str], int | None],
    result_factory: Callable[..., object],
):
    contractor = parse_corp_list_company_fn(str(row.get("corpList") or ""))
    if not contractor:
        contractor = str(row.get("cntrctEntrpsNm") or row.get("cntrctrNm") or row.get("cntrctInsttNm") or "").strip()
    amount_val = row.get("totCntrctAmt")
    if amount_val is None or str(amount_val).strip() == "":
        amount_val = row.get("thtmCntrctAmt")
    contact_text = str(row.get("dminsttList") or "").strip()
    dept_name = str(
        row.get("cntrctDeptNm")
        or row.get("cntrctInsttChrgDeptNm")
        or row.get("dminsttDeptNm")
        or ""
    ).strip()
    officer_name = str(
        row.get("cntrctOfclNm")
        or row.get("cntrctInsttOfclNm")
        or row.get("dminsttOfclNm")
        or ""
    ).strip()
    officer_tel = str(
        row.get("cntrctDeptTelNo")
        or row.get("cntrctInsttOfclTelNo")
        or row.get("dminsttOfclTelNo")
        or ""
    ).strip()
    if not dept_name and contact_text:
        parts = [part.strip() for part in re.sub(r"^[\[]|[\]]$", "", contact_text).split("^") if part.strip()]
        if len(parts) >= 5:
            dept_name = parts[4]
    site_name = ""
    for key in ("cnstrtsiteRgnNm", "cnstwkLocplcAddr", "cnstrctPlace", "cnstwkPlace"):
        value = str(row.get(key) or "").strip()
        if value:
            site_name = value
            break
    period_text = str(row.get("cntrctPrd") or "").strip()
    if not period_text:
        bgn = str(row.get("cntrctBgnDate") or "").strip()
        end = str(row.get("cntrctEndDate") or "").strip()
        if bgn and end:
            period_text = f"{bgn} ~ {end}"
    return result_factory(
        contract_name=contractor,
        contract_date=str(row.get("cntrctDate") or row.get("cntrctCnclsDate") or "").strip(),
        contract_amount="" if amount_val is None else str(amount_val),
        target_name=str(row.get("cntrctNm") or row.get("cnstwkNm") or "").strip(),
        inst_name=str(row.get("cntrctInsttNm") or "").strip(),
        dept_name=dept_name,
        officer_name=officer_name,
        officer_tel=officer_tel,
        contract_period_text=period_text,
        contract_duration_days=extract_duration_days_fn(period_text),
        site_name=site_name,
        match_score=min(1.0, max(0.0, float(score))),
    )


def _pick_best_lofin_hit(
    rows: list[dict],
    *,
    project_name_norm: str,
    is_generic_project_term_fn: Callable[[str], bool],
    result_factory: Callable[..., object],
):
    if is_generic_project_term_fn(project_name_norm):
        return None
    pnorm = _norm_text(project_name_norm)
    best_row: dict | None = None
    best_score = 0.0
    for row in rows:
        target_name = str(row.get("ctrtTrgtNm") or "").strip()
        contract_name = str(row.get("cltNm") or "").strip()
        if not target_name or not contract_name:
            continue
        tnorm = _norm_text(target_name)
        if not tnorm:
            continue
        overlap = _text_overlap_ratio(project_name_norm, target_name)
        exact = 1.0 if pnorm and pnorm == tnorm else 0.0
        contains = 0.9 if pnorm and (pnorm in tnorm or tnorm in pnorm) else 0.0
        score = max(overlap, exact, contains)
        if score > best_score:
            best_score = score
            best_row = row
    if best_row is None or (pnorm and best_score < 0.45):
        return None
    amount_val = best_row.get("ctrtTotTottAmt") or best_row.get("ctrtTottAmt") or best_row.get("ctrtTotAmt")
    return result_factory(
        contract_name=str(best_row.get("cltNm") or "").strip(),
        contract_date=str(best_row.get("smzCtrtYmd") or "").strip(),
        contract_amount="" if amount_val is None else str(amount_val),
        target_name=str(best_row.get("ctrtTrgtNm") or "").strip(),
        inst_name=str(best_row.get("lafNm") or "").strip(),
        match_score=min(1.0, max(0.0, float(best_score))),
        source_type="lofin_api",
    )


def _pick_best_g2b_contract_hit(
    rows: list[dict],
    *,
    project_name_norm: str,
    is_generic_project_term_fn: Callable[[str], bool],
    contract_target_match_score_fn: Callable[[str, str, dict | None], float],
    to_lookup_result_fn: Callable[[dict, float], object],
):
    best_row: dict | None = None
    best_score = -1.0
    if project_name_norm and not is_generic_project_term_fn(project_name_norm):
        for row in rows:
            target_name = str(row.get("cntrctNm") or row.get("cnstwkNm") or "").strip()
            score = contract_target_match_score_fn(project_name_norm, target_name, row)
            if score > best_score:
                best_score = score
                best_row = row
        if best_row is None or best_score < 0.45:
            return None
    else:
        sorted_rows = sorted(rows, key=lambda x: str(x.get("cntrctDate") or x.get("cntrctCnclsDate") or "").strip(), reverse=True)
        best_row = sorted_rows[0] if sorted_rows else None
        best_score = 1.0
        if best_row is None:
            return None
    return to_lookup_result_fn(best_row, best_score)


def _pick_best_g2b_contract_hit_by_bid_no(
    rows: list[dict],
    *,
    bid_no: str,
    project_name_norm: str,
    pick_best_g2b_contract_hit_fn: Callable[[list[dict], str], object],
):
    bid_tok = _norm_bid_token(bid_no)
    if not bid_tok:
        return None
    candidates = []
    for row in rows:
        ntce_tok = _norm_bid_token(str(row.get("ntceNo") or "").strip())
        if ntce_tok == bid_tok or ntce_tok.startswith(bid_tok):
            candidates.append(row)
    if not candidates:
        return None
    return pick_best_g2b_contract_hit_fn(candidates, project_name_norm)


def _repair_utf8_mojibake(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    try:
        repaired = value.encode("latin-1").decode("utf-8")
    except Exception:
        return value
    hangul_before = sum(1 for ch in value if "\uac00" <= ch <= "\ud7a3")
    hangul_after = sum(1 for ch in repaired if "\uac00" <= ch <= "\ud7a3")
    if hangul_after > hangul_before:
        return repaired
    return value


def _normalize_hub_result_candidates(payload: object) -> list[dict]:
    if not isinstance(payload, list):
        return []
    rows: list[dict] = []
    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        norm = {
            "title": _repair_utf8_mojibake(str(item.get("title") or "").strip()),
            "winnerOffice": _repair_utf8_mojibake(str(item.get("winnerOffice") or "").strip()),
            "winnerRank": _repair_utf8_mojibake(str(item.get("winnerRank") or "").strip()),
            "designPbpNo": _repair_utf8_mojibake(str(item.get("designPbpNo") or "").strip()),
            "cycl": _repair_utf8_mojibake(str(item.get("cycl") or "").strip()),
        }
        dedupe_key = "|".join([norm["title"], norm["winnerOffice"], norm["designPbpNo"], norm["cycl"]])
        if not dedupe_key or dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        rows.append(norm)
    return rows
