from __future__ import annotations

import html
import re

from .korean_admin_districts import match_official_sigungu
from .korean_admin_districts import OFFICIAL_REGION_PATTERN


INVALID_CITY_LOCATION_TOKENS = (
    "재단법인",
    "사단법인",
    "학교법인",
    "의료법인",
    "사회복지법인",
    "법인",
)


def extract_construction_start_date(text: str, contract_date: str = "") -> str:
    source = str(text or "")
    explicit_date_patterns = (
        r"(?:착공일|착수일)\s*[:：]?\s*([0-9]{4}[.\-/년 ]+[0-9]{1,2}(?:[.\-/월 ]+[0-9]{1,2})?)",
    )
    for pattern in explicit_date_patterns:
        match = re.search(pattern, source, flags=re.I)
        if match:
            return str(match.group(1) or "").strip()

    contract_end_patterns = (
        (
            r"(?:수행기간|과업기간|용역기간|설계기간)[^\n\r]{0,80}"
            r"(?:계약체결일|계약일)\s*[~∼\-]\s*"
            r"([0-9]{4}\s*(?:년|[.\-/])\s*[0-9]{1,2}\s*(?:월|[.\-/])\s*[0-9]{1,2}\s*(?:일)?)",
            "계약체결일~{date}",
        ),
        (
            r"(?:설계용역기간|용역기간|과업기간)[\s\S]{0,120}"
            r"([0-9]{4}\s*(?:년|[.\-/])\s*[0-9]{1,2}\s*(?:월|[.\-/])\s*[0-9]{1,2}\s*(?:일)?)\s*까지",
            "{date}까지",
        ),
    )
    for pattern, template in contract_end_patterns:
        match = re.search(pattern, source, flags=re.I)
        if match:
            normalized = _normalize_notice_date_text(str(match.group(1) or ""))
            if normalized:
                return template.format(date=normalized)

    anchored_duration_patterns = (
        r"((?:착수일|착공일)\s*로부터\s*\d{1,3}\s*개월(?:간)?)",
        r"((?:착수일|착공일)\s*로부터\s*\d{1,4}\s*일(?:간)?)",
        r"((?:착수일|착공일)\s*[~∼\-]\s*\d{2,4}\s*일(?:간)?)",
    )
    for pattern in anchored_duration_patterns:
        match = re.search(pattern, source, flags=re.I)
        if match:
            return re.sub(r"\s+", "", str(match.group(1) or "").strip())
    return contract_date


def extract_duration_days_from_text(text: str) -> int:
    source = str(text or "")
    if not source:
        return 0
    month_patterns = (
        r"(?:용역기간|설계기간|공사기간|본\s*과업)[\s\S]{0,120}(?:착수일|착공일|계약일)\s*로부터[^0-9]{0,60}(\d{1,3})\s*개월",
        r"(?:착수일|착공일|계약일)\s*로부터\s*(\d{1,3})\s*개월",
        r"착수\s*후\s*(\d{1,3})\s*개월",
        r"(?:예정\s*)?(?:공사기간|용역기간|설계기간|공사\s*기간|용역\s*기간|설계\s*기간)[^0-9]{0,30}(\d{1,3})\s*개월",
    )
    for pattern in month_patterns:
        month_match = re.search(pattern, source, flags=re.I)
        if month_match:
            try:
                return int(month_match.group(1)) * 30
            except Exception:
                return 0
    day_patterns = (
        r"(?:용역기간|설계기간|공사기간|본\s*과업)[\s\S]{0,120}(?:착수일|착공일|계약일)\s*로부터[^0-9]{0,60}(\d{2,4})\s*일",
        r"(?:용역설계기간|용역기간|설계기간|과업기간)[\s\S]{0,80}(?:착수일|착공일|계약일)\s*[~∼\-]\s*(\d{2,4})\s*일",
        r"(?:착수일|착공일|계약일)\s*로부터\s*(\d{1,4})\s*일",
        r"(?:착수일|착공일|계약일)\s*[~∼\-]\s*(\d{2,4})\s*일",
        r"착수\s*후\s*(\d{1,4})\s*일",
        r"(?:예정\s*)?(?:공사기간|용역기간|설계기간|공사\s*기간|용역\s*기간|설계\s*기간)[^0-9]{0,30}(\d{1,4})\s*일",
    )
    for pattern in day_patterns:
        day_match = re.search(pattern, source, flags=re.I)
        if day_match:
            try:
                return int(day_match.group(1))
            except Exception:
                return 0
    return 0


def _normalize_notice_date_text(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    match = re.search(r"(\d{4})\s*[.\-/년]\s*(\d{1,2})\s*[.\-/월]\s*(\d{1,2})", text)
    if not match:
        match = re.search(r"(\d{4})[-./](\d{2})[-./](\d{2})", text)
    if not match:
        return ""
    year, month, day = match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def extract_completion_expected_date(text: str) -> str:
    source = str(text or "")
    if not source:
        return ""
    patterns = (
        r"(?:준공예정일|완공예정일|완료예정일)\s*[:：]?\s*([0-9]{4}\s*[.\-/년]\s*[0-9]{1,2}\s*[.\-/월]\s*[0-9]{1,2})",
        r"(?:준공예정|완공예정|완료예정)\s*[:：]?\s*([0-9]{4}\s*[.\-/년]\s*[0-9]{1,2}\s*[.\-/월]\s*[0-9]{1,2})",
    )
    for pattern in patterns:
        match = re.search(pattern, source, flags=re.I)
        if not match:
            continue
        normalized = _normalize_notice_date_text(match.group(1))
        if normalized:
            return normalized
    return ""


def decode_html_and_strip(value: str) -> str:
    return _decode_html_entities(value)


def extract_client_location(text: str, org_name: str, project_name: str) -> str:
    labeled = _sanitize_location_candidate(
        _extract_labeled_value(text, ["발주처 위치", "발주기관 주소", "수요기관 주소", "수요기관 소재지", "발주처주소"])
    )
    if labeled:
        return labeled
    return ""


def extract_site_location(text: str, org_name: str, project_name: str) -> str:
    labeled = _sanitize_location_candidate(
        _extract_labeled_value(text, ["현장 위치", "현장위치", "사업 위치", "사업위치", "건립위치", "대지 위치", "대지위치"])
    )
    if labeled:
        return labeled
    inferred = _compose_inferred_location(org_name, project_name)
    if inferred:
        return inferred
    return ""


def to_city_level_location(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if re.search(r"(팩스|FAX|유튜브|라이브|송출|브라우저|안내)", text, re.I):
        return ""
    for pattern in (
        r"(서울특별시|부산광역시|대구광역시|인천광역시|광주광역시|대전광역시|울산광역시|세종특별자치시|제주특별자치도)",
        r"([가-힣A-Za-z0-9]{2,20}(?:시|군|구))",
        r"([가-힣A-Za-z0-9]{1,20}(?:읍|면|동))",
    ):
        match = re.search(pattern, text)
        if match:
            candidate = str(match.group(1) or "").strip()
            if candidate == "119구" or re.fullmatch(r"\d+구", candidate):
                continue
            if any(token in candidate for token in INVALID_CITY_LOCATION_TOKENS):
                continue
            return candidate
    return ""


def infer_city_from_org_or_project(org_name: str, project_name: str) -> str:
    for text in (org_name,):
        source = str(text or "").strip()
        if not source:
            continue
        region = infer_region_from_org(source)
        official = match_official_sigungu(source, region=region)
        if official:
            return official
    return ""


def infer_region_from_org(org_name: str) -> str:
    text = str(org_name or "").strip()
    if not text:
        return ""
    match = re.search(rf"({OFFICIAL_REGION_PATTERN})", text)
    if match:
        return str(match.group(1) or "").strip()
    return ""


def _compose_inferred_location(org_name: str, project_name: str) -> str:
    region = infer_region_from_org(org_name)
    city = infer_city_from_org_or_project(org_name, project_name)
    if region and city:
        return f"{region} {city}"
    return city or region


def _sanitize_location_candidate(value: str) -> str:
    candidate = re.sub(r"[\u25e6\u2022\xb7]", " ", str(value or "")).strip()
    candidate = re.sub(r"\s+", " ", candidate).strip(" -:|/\t")
    if not candidate:
        return ""
    if re.search(r"(용역기간|공사기간|설계기간|대지면적|연면적|공사비|사업비|담당부서|담당자|문의처|문의|연락처|전화|착공일)", candidate):
        return ""
    if re.search(r"(팩스|FAX|유튜브|라이브|송출|브라우저|안내)", candidate, re.I):
        return ""
    if re.search(
        rf"({OFFICIAL_REGION_PATTERN}|[가-힣A-Za-z0-9]{{1,12}}(?:시|군|구|읍|면|동))",
        candidate,
    ):
        return candidate[:80]
    return ""


def _decode_html_entities(text: str) -> str:
    cleaned = html.unescape(str(text or "")).replace("\xa0", " ")
    cleaned = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _extract_labeled_value(text: str, labels: list[str], max_len: int = 80) -> str:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    for index, line in enumerate(lines):
        for label in labels:
            if label not in line:
                continue
            suffix = line.split(label, 1)[1]
            candidate = re.sub(r"^[\s:：\-|/]+", "", suffix).strip()
            candidate = _truncate_at_next_field_label(candidate)
            candidate = re.sub(r"\s+", " ", candidate).strip(" -:|/\t")
            if candidate:
                return candidate[:max_len]
            if index + 1 < len(lines):
                next_line = re.sub(r"\s+", " ", lines[index + 1]).strip(" -:|/\t")
                if next_line:
                    return next_line[:max_len]
    return ""


def _truncate_at_next_field_label(value: str) -> str:
    candidate = str(value or "")
    next_label = re.search(
        r"\b(?:담당부서|주관부서|담당자|문의처|문의|연락처|전화|발주처\s*위치|발주기관\s*주소|수요기관\s*주소|현장\s*위치|현장위치|사업\s*위치|사업위치|건립위치|착공일|착수일|빌딩자동제어\s*추정\s*금액|연면적|공사비|예정공사비|총사업비)\b",
        candidate,
    )
    if next_label:
        candidate = candidate[: next_label.start()]
    return candidate
