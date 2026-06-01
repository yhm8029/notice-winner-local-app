from __future__ import annotations

import html
import re
from typing import Any


def fetch_page_text(
    url: str,
    *,
    requests_get_fn,
    decode_html_and_strip_fn,
    user_agent: str = "",
    request_timeout_sec: int = 12,
) -> tuple[str, str]:
    target = str(url or "").strip()
    if not target:
        return "", ""
    headers = {"User-Agent": user_agent, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7"}
    try:
        response = requests_get_fn(target, headers=headers, timeout=request_timeout_sec)
        response.raise_for_status()
    except Exception:
        return "", ""
    raw_html = str(response.text or "")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", raw_html, flags=re.I | re.S)
    title = html.unescape(re.sub(r"<[^>]+>", "", title_match.group(1)).strip()) if title_match else ""
    body = re.sub(r"(?is)<script.*?>.*?</script>", "\n", raw_html)
    body = re.sub(r"(?is)<style.*?>.*?</style>", "\n", body)
    body = re.sub(r"(?i)</(tr|p|div|br|li|td|th|h1|h2|h3|h4|h5|section|article)>", "\n", body)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    body = html.unescape(body).replace("\xa0", " ")
    lines = [re.sub(r"\s+", " ", line).strip() for line in body.splitlines()]
    text = "\n".join(line for line in lines if line)
    return decode_html_and_strip_fn(title), decode_html_and_strip_fn(text)


def clean_value(value: str, *, max_len: int) -> str:
    cleaned = re.sub(r"^[\s:\-|/]+", "", str(value or ""))
    cleaned = re.split(r"(?:\s{2,}|[|])", cleaned)[0]
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:|/\t")
    return cleaned[:max_len].strip()


def extract_labeled_value(text: str, labels: list[str], *, max_len: int = 80) -> str:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    for index, line in enumerate(lines):
        for label in labels:
            if label not in line:
                continue
            suffix = line.split(label, 1)[1]
            candidate = clean_value(suffix, max_len=max_len)
            if candidate:
                return candidate
            if index + 1 < len(lines):
                next_line = clean_value(lines[index + 1], max_len=max_len)
                if next_line:
                    return next_line
    label_pattern = "|".join(re.escape(label) for label in labels)
    inline_match = re.search(rf"(?:{label_pattern})\s*[:\-]?\s*([^\n\r]{{2,{max_len}}})", str(text or ""), flags=re.I)
    if inline_match:
        return clean_value(inline_match.group(1), max_len=max_len)
    return ""


def extract_notice_fields(
    *,
    title: str,
    text: str,
    project_name: str,
    org_name: str,
    winner_name_extractor_fn,
    extracted_notice_fields_cls,
    extract_notice_area_value_fn,
    extract_notice_cost_won_fn,
    format_won_fn,
    is_auxiliary_service_project_fn,
    extract_contact_from_notice_text_fn,
    extract_contact_resolution_from_notice_text_fn,
    extract_client_location_fn,
    extract_site_location_fn,
    extract_construction_start_date_fn,
    extract_duration_days_from_text_fn,
    extract_completion_expected_date_fn,
    extract_labeled_cost_text_fn,
) -> Any:
    extraction = winner_name_extractor_fn(text, title)
    winner_name = str(extraction.winner_name or "").strip()
    area = extract_notice_area_value_fn(text, project_name=project_name)
    construction_cost_won = extract_notice_cost_won_fn(text)
    construction_cost = format_won_fn(construction_cost_won)
    if is_auxiliary_service_project_fn(project_name) or is_auxiliary_service_project_fn(title):
        construction_cost = ""
    raw_demand_contact = extract_contact_from_notice_text_fn(text, org_name)
    contact_resolution = extract_contact_resolution_from_notice_text_fn(text, org_name)
    use_resolution_contact = bool(contact_resolution.status == "resolved" and str(contact_resolution.contact or "").strip())
    demand_contact = str(contact_resolution.contact or "").strip() if use_resolution_contact else ""
    if not demand_contact and contact_resolution.reason == "no_observations":
        demand_contact = str(raw_demand_contact or "").strip()
    client_location = extract_client_location_fn(text, org_name, project_name)
    site_location = extract_site_location_fn(text, org_name, project_name)
    architect_office = ""
    construction_start_date = extract_construction_start_date_fn(text)
    construction_duration_days_value = int(extract_duration_days_from_text_fn(text) or 0)
    start_date_duration_days = _extract_duration_days_from_period_display(construction_start_date)
    if start_date_duration_days >= 30 and construction_duration_days_value < 30:
        construction_duration_days_value = start_date_duration_days
    construction_duration_days = str(construction_duration_days_value or "")
    completion_expected_date_explicit = extract_completion_expected_date_fn(text)
    building_auto_est = extract_labeled_cost_text_fn(
        text,
        ("빌딩자동제어 추정 금액", "빌딩자동제어추정금액", "빌딩자동제어"),
    )
    review_contact = use_resolution_contact or contact_resolution.status == "review"
    return extracted_notice_fields_cls(
        winner_name=winner_name,
        winner_pattern=str(extraction.pattern or "").strip(),
        gross_area_scale=area,
        construction_cost=construction_cost,
        demand_contact=demand_contact,
        client_location=client_location,
        site_location=site_location,
        architect_office=architect_office,
        construction_start_date=construction_start_date,
        construction_duration_days=construction_duration_days,
        completion_expected_date_explicit=completion_expected_date_explicit,
        building_automation_estimated_amount=building_auto_est,
        demand_contact_resolution_status=contact_resolution.status if review_contact else "",
        demand_contact_resolution_reason=contact_resolution.reason if review_contact else "",
        demand_contact_resolution_phase=contact_resolution.phase if review_contact else "",
        demand_contact_resolution_role=contact_resolution.role if review_contact else "",
        demand_contact_resolution_owner_side=contact_resolution.owner_side if review_contact else "",
        demand_contact_resolution_owner_side_basis=contact_resolution.owner_side_basis if review_contact else "",
    )


def _extract_duration_days_from_period_display(value: str) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    month_match = re.search(r"(\d{1,3})\s*개월", text)
    if month_match:
        try:
            return int(month_match.group(1)) * 30
        except Exception:
            return 0
    day_match = re.search(r"(\d{1,4})\s*일", text)
    if day_match:
        try:
            return int(day_match.group(1))
        except Exception:
            return 0
    return 0


def has_page_enrichment_fields(extracted: Any, *, extract_area_number_fn) -> bool:
    area_value = extract_area_number_fn(extracted.gross_area_scale)
    return all([extracted.demand_contact, 50 <= area_value <= 2000000])


def has_core_export_fields(extracted: Any, winner_name: str) -> bool:
    return all([str(winner_name or "").strip(), extracted.gross_area_scale, extracted.construction_cost])


def has_attachment_enrichment_fields(extracted: Any, *, extract_area_number_fn) -> bool:
    area_value = extract_area_number_fn(extracted.gross_area_scale)
    return all([extracted.construction_cost, 50 <= area_value <= 2000000, extracted.demand_contact])


def has_attachment_skip_fields(extracted: Any, *, extract_area_number_fn) -> bool:
    return has_attachment_enrichment_fields(extracted, extract_area_number_fn=extract_area_number_fn)


def resolve_candidate_winner_name(*, contract_hit: object, extracted: Any, best_row: dict[str, str]) -> str:
    candidates = [
        getattr(contract_hit, "contract_name", "") if contract_hit else "",
        extracted.winner_name,
        str(best_row.get("winner_name") or "").strip(),
        str(best_row.get("contract_name") or "").strip(),
    ]
    for candidate in candidates:
        value = str(candidate or "").strip()
        if value:
            return value
    return ""


def should_try_attachment(*, attachment_docs: list[Any], extracted: Any, has_attachment_skip_fields_fn) -> bool:
    if not attachment_docs:
        return False
    return not has_attachment_skip_fields_fn(extracted)
