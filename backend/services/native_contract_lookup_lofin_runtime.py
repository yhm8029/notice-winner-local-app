from __future__ import annotations


def _normalize_lofin_openapi_row(item: dict) -> dict:
    return {
        "ctrtLdgrMngNo": str(item.get("ctrtLdgrMngNo") or item.get("ctrt_ldgr_mng_no") or "").strip(),
        "ctrtTrgtNm": str(item.get("ctrtTrgtNm") or item.get("ctrt_trgt_nm") or "").strip(),
        "smzCtrtYmd": str(item.get("smzCtrtYmd") or item.get("smz_ctrt_ymd") or "").strip(),
        "cltNm": str(item.get("cltNm") or item.get("clt_nm") or "").strip(),
        "ctrtTotTottAmt": item.get("ctrtTotTottAmt")
        if item.get("ctrtTotTottAmt") is not None
        else item.get("ctrt_tot_tott_amt"),
        "lafNm": str(item.get("lafNm") or item.get("laf_hg_nm") or item.get("lafHgNm") or "").strip(),
        "ctrtKndNm": str(item.get("ctrtKndNm") or item.get("ctrt_knd_nm") or "").strip(),
    }


def _looks_like_lofin_contract_row(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    keys = set(item.keys())
    return bool(
        {
            "ctrt_trgt_nm",
            "smz_ctrt_ymd",
            "clt_nm",
            "ctrt_ldgr_mng_no",
            "ctrtTrgtNm",
            "smzCtrtYmd",
            "cltNm",
            "ctrtLdgrMngNo",
        }
        & keys
    )


def _extract_lofin_openapi_rows(payload: dict) -> list[dict]:
    rows: list[dict] = []

    def _walk(node: object, depth: int = 0) -> None:
        if depth > 6:
            return
        if isinstance(node, dict):
            if _looks_like_lofin_contract_row(node):
                rows.append(node)
                return
            for val in node.values():
                _walk(val, depth + 1)
        elif isinstance(node, list):
            if node and all(isinstance(x, dict) for x in node):
                if any(_looks_like_lofin_contract_row(x) for x in node):
                    rows.extend([x for x in node if isinstance(x, dict)])
                    return
            for val in node:
                _walk(val, depth + 1)

    if isinstance(payload, dict):
        _walk(payload, 0)
    return rows


def _is_lofin_success_code(code: str) -> bool:
    norm = str(code or "").strip().upper()
    return norm in {"", "INFO-000", "INFO000", "SUCCESS", "OK", "0000", "00"}


def _extract_lofin_openapi_error(payload: dict) -> tuple[str, str]:
    result = payload.get("RESULT") if isinstance(payload, dict) else None
    if isinstance(result, dict):
        code = str(result.get("CODE") or "").strip()
        msg = str(result.get("MESSAGE") or result.get("MSG") or "").strip()
        return ("", msg) if _is_lofin_success_code(code) else (code, msg)
    if isinstance(result, list) and result:
        first = result[0]
        if isinstance(first, dict):
            code = str(first.get("CODE") or "").strip()
            msg = str(first.get("MESSAGE") or first.get("MSG") or "").strip()
            return ("", msg) if _is_lofin_success_code(code) else (code, msg)
    return "", ""
