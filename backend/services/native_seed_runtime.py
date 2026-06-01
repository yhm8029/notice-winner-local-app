from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from datetime import timedelta


def api_header(payload: dict) -> tuple[str, str]:
    header = (payload.get("response") or {}).get("header") or {}
    if not header:
        header = (payload.get("nkoneps.com.response.ResponseError") or {}).get("header") or {}
    return str(header.get("resultCode") or ""), str(header.get("resultMsg") or "")


def extract_items(payload: dict) -> tuple[list[dict], int]:
    response = payload.get("response") if isinstance(payload, dict) else {}
    body = response.get("body") if isinstance(response, dict) else {}
    total_count = int(body.get("totalCount") or 0) if isinstance(body, dict) else 0
    items = body.get("items") if isinstance(body, dict) else None
    if isinstance(items, dict):
        items = items.get("item")
    if isinstance(items, dict):
        return [items], total_count
    if isinstance(items, list):
        return items, total_count
    return [], total_count


def extract_items_from_xml(xml_text: str) -> tuple[list[dict], int]:
    text = str(xml_text or "").strip()
    if not text:
        return [], 0
    try:
        root = ET.fromstring(text)
    except Exception:
        return [], 0
    total_count = 0
    tc_node = root.find(".//totalCount")
    if tc_node is not None:
        try:
            total_count = int(str(tc_node.text or "0").strip() or "0")
        except Exception:
            total_count = 0
    rows: list[dict] = []
    for item in root.findall(".//item"):
        row: dict[str, str] = {}
        for child in list(item):
            row[str(child.tag or "").strip()] = str(child.text or "").strip()
        if row:
            rows.append(row)
    return rows, total_count


def iter_month_ranges(start_date: str, end_date: str) -> list[tuple[str, str]]:
    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    rows: list[tuple[str, str]] = []
    current = start
    while current <= end:
        month_end = (current.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        window_end = min(month_end, end)
        rows.append((current.strftime("%Y%m%d"), window_end.strftime("%Y%m%d")))
        current = window_end + timedelta(days=1)
    return rows


def split_bid_no_ord(value: str) -> tuple[str, str]:
    raw = str(value or "").strip()
    if not raw:
        return "", "000"
    match = re.match(r"^([A-Za-z0-9]+)\s*[-_/]\s*([0-9]{1,3})$", raw)
    if match:
        return match.group(1).upper(), match.group(2).zfill(3)
    return raw.upper(), "000"


def extract_yyyymmdd(*values: object) -> str:
    for raw in values:
        text = str(raw or "").strip()
        if not text:
            continue
        digits = re.sub(r"[^0-9]", "", text)
        if len(digits) < 8:
            continue
        candidate = digits[:8]
        try:
            datetime.strptime(candidate, "%Y%m%d")
            return candidate
        except ValueError:
            continue
    return ""


def select_org_name(demand_org_name: str, notice_org_name: str) -> str:
    edu_candidates = [name for name in (demand_org_name, notice_org_name) if "교육" in str(name or "")]
    if edu_candidates:
        return max(edu_candidates, key=len)
    return demand_org_name or notice_org_name


def derive_notice_status(*, title: str, notice_kind_name: str) -> str:
    combined = f"{str(notice_kind_name or '')} {str(title or '')}"
    if "취소공고" in combined:
        return "cancelled"
    if "변경공고" in combined or "정정공고" in combined:
        return "amended"
    return "regular"


def notice_ord_num(value: str | object) -> int:
    digits = re.sub(r"[^0-9]", "", str(value or ""))
    if not digits:
        return 0
    try:
        return int(digits)
    except Exception:
        return 0


def notice_dt_sort_key(value: str | object) -> str:
    return re.sub(r"[^0-9]", "", str(value or ""))


def endpoint_priority(endpoint_name: str) -> int:
    return 1 if "PPSSrch" in str(endpoint_name or "") else 2


def notice_status_priority(value: str | object) -> int:
    status = str(value or "")
    if status == "amended":
        return 2
    if status == "regular":
        return 1
    return 0


def should_replace_seed_notice(current: dict[str, str], candidate: dict[str, str]) -> bool:
    current_ord = notice_ord_num(current.get("_notice_ord_num", current.get("bid_ord", "")))
    candidate_ord = notice_ord_num(candidate.get("_notice_ord_num", candidate.get("bid_ord", "")))
    if candidate_ord != current_ord:
        return candidate_ord > current_ord

    current_status = notice_status_priority(current.get("_notice_status", ""))
    candidate_status = notice_status_priority(candidate.get("_notice_status", ""))
    if candidate_status != current_status:
        return candidate_status > current_status

    current_dt = notice_dt_sort_key(current.get("_notice_dt_sort", current.get("announce_date", "")))
    candidate_dt = notice_dt_sort_key(candidate.get("_notice_dt_sort", candidate.get("announce_date", "")))
    if candidate_dt != current_dt:
        return candidate_dt > current_dt

    current_endpoint = endpoint_priority(current.get("_matched_endpoint", ""))
    candidate_endpoint = endpoint_priority(candidate.get("_matched_endpoint", ""))
    return candidate_endpoint > current_endpoint


def norm_text(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", str(value or "")).lower()


def split_demand_org_filter_tokens(value: str) -> list[str]:
    raw = str(value or "").strip()
    if not raw:
        return []
    parts = [part.strip() for part in re.split(r"[,\n;|]+", raw) if part and part.strip()]
    return parts or [raw]


def expand_demand_org_aliases(value: str, *, region_alias_groups: tuple[tuple[str, ...], ...]) -> set[str]:
    base = str(value or "").strip()
    if not base:
        return set()
    variants: set[str] = {base}
    for group in region_alias_groups:
        names = [name for name in group if name]
        for alias in names:
            if alias and alias in base:
                for alt in names:
                    variants.add(base.replace(alias, alt))
    return {variant.strip() for variant in variants if variant and variant.strip()}


def matches_demand_org_filter(
    filter_text: str,
    *org_values: str,
    region_alias_groups: tuple[tuple[str, ...], ...],
) -> bool:
    raw = str(filter_text or "").strip()
    if not raw:
        return True
    haystack = " ".join(str(value or "") for value in org_values if str(value or "").strip())
    hay_norm = norm_text(haystack)
    if not hay_norm:
        return False
    for token in split_demand_org_filter_tokens(raw):
        for candidate in expand_demand_org_aliases(token, region_alias_groups=region_alias_groups):
            candidate_norm = norm_text(candidate)
            if candidate_norm and candidate_norm in hay_norm:
                return True
    return False


def clean_notice_title(raw_title: str, *, title_paren_noise_tokens: set[str]) -> str:
    title = re.sub(r"\s+", " ", str(raw_title or "")).strip()
    title = re.sub(r"\s*[-|]\s*(?:.*(?:go\.kr|or\.kr|re\.kr).*)$", "", title, flags=re.I)

    def _clean_parenthetical(match: re.Match[str]) -> str:
        inner = match.group(1) or ""
        inner_norm = norm_text(re.sub(r"\s+", "", inner))
        if not inner_norm:
            return " "
        if inner_norm in {norm_text(token) for token in title_paren_noise_tokens}:
            return " "
        return match.group(0)

    title = re.sub(r"[\(（]\s*([^()（）]*)\s*[\)）]", _clean_parenthetical, title)
    title = re.sub(r"\s+", " ", title).strip()
    return title.strip(" -|")


def build_seed_row_from_item(
    item: dict,
    *,
    endpoint_name: str = "",
    attachment_field_count: int,
    clean_notice_title_fn,
    select_org_name_fn,
    extract_yyyymmdd_fn,
) -> dict[str, str]:
    bid_no = str(item.get("bidNtceNo") or "").strip()
    bid_ord = str(item.get("bidNtceOrd") or item.get("bidNtceOrdNo") or item.get("bidNtceOrdNum") or "").strip()
    title = clean_notice_title_fn(str(item.get("bidNtceNm") or ""))
    demand_org_name = str(item.get("dminsttNm") or item.get("dmndInsttNm") or "").strip()
    notice_org_name = str(item.get("ntceInsttNm") or "").strip()
    org_name = select_org_name_fn(demand_org_name, notice_org_name)
    announce_date = extract_yyyymmdd_fn(
        item.get("bidNtceDt"),
        item.get("bidNtceDate"),
        item.get("ntceDt"),
        item.get("ntceDate"),
        item.get("rgstDt"),
    )
    row = {
        "bid_no": bid_no,
        "bid_ord": bid_ord,
        "project_name": title,
        "org_name": org_name,
        "announce_date": announce_date,
        "opening_scheduled_date": extract_yyyymmdd_fn(
            item.get("opengDt"),
            item.get("opengDate"),
        ),
        "g2b_verified": "Y",
        "bid_ntce_url": str(item.get("bidNtceUrl") or "").strip(),
        "bid_ntce_dtl_url": str(item.get("bidNtceDtlUrl") or "").strip(),
        "notice_officer_name": str(item.get("ntceInsttOfclNm") or "").strip(),
        "notice_officer_tel": str(item.get("ntceInsttOfclTelNo") or "").strip(),
        "notice_officer_email": str(item.get("ntceInsttOfclEmailAdrs") or "").strip(),
        "demand_officer_name": str(item.get("exctvNm") or "").strip(),
        "demand_officer_email": str(item.get("dminsttOfclEmailAdrs") or "").strip(),
        "presmpt_prce": str(item.get("presmptPrce") or "").strip(),
        "service_name": str(item.get("srvceDivNm") or item.get("pubPrcrmntClsfcNm") or "").strip(),
        "sucsfbid_method_name": str(item.get("sucsfbidMthdNm") or "").strip(),
        "_demand_org_name": demand_org_name,
        "_notice_org_name": notice_org_name,
        "_matched_endpoint": endpoint_name,
    }
    for index in range(1, attachment_field_count + 1):
        row[f"spec_doc_url_{index}"] = str(
            item.get(f"ntceSpecDocUrl{index}")
            or (item.get("stdNtceDocUrl") if index == 1 else "")
            or ""
        ).strip()
        row[f"spec_doc_file_name_{index}"] = str(item.get(f"ntceSpecFileNm{index}") or "").strip()
    return row
