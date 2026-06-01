from __future__ import annotations

import re

from . import native_gui_rules_area_runtime as _area_runtime
from . import native_gui_rules_cost_runtime as _cost_runtime
from . import native_gui_rules_winner_runtime as _winner_runtime
from .native_gui_rules_cost_runtime import extract_area_number
from .native_gui_rules_cost_runtime import extract_cost_won
from .native_gui_rules_cost_runtime import format_area_number
from .native_gui_rules_cost_runtime import format_won
from .native_gui_rules_location_runtime import _decode_html_entities
from .native_gui_rules_location_runtime import _extract_labeled_value
from .native_gui_rules_location_runtime import decode_html_and_strip
from .native_gui_rules_location_runtime import extract_client_location
from .native_gui_rules_location_runtime import extract_completion_expected_date
from .native_gui_rules_location_runtime import extract_construction_start_date
from .native_gui_rules_location_runtime import extract_duration_days_from_text
from .native_gui_rules_location_runtime import extract_site_location
from .native_gui_rules_location_runtime import infer_city_from_org_or_project
from .native_gui_rules_location_runtime import infer_region_from_org
from .native_gui_rules_location_runtime import INVALID_CITY_LOCATION_TOKENS
from .native_gui_rules_location_runtime import OFFICIAL_REGION_PATTERN
from .native_gui_rules_location_runtime import to_city_level_location
from .native_gui_rules_contact_resolution_runtime import ContactObservation
from .native_gui_rules_contact_resolution_runtime import ContactResolution
from .native_gui_rules_contact_resolution_runtime import _contact_resolution_sort_key
from .native_gui_rules_contact_resolution_runtime import resolve_contact_from_observations
from .native_gui_rules_winner_runtime import WinnerExtraction
from .native_gui_rules_winner_runtime import winner_name_extractor


from ._native_gui_rules_runtime_support_constants import ATTACHMENT_FILENAME_LINE_PAT
from ._native_gui_rules_runtime_support_constants import CONTACT_COMPANY_NOISE_PAT
from ._native_gui_rules_runtime_support_constants import CONTACT_CONTRACT_CUE_PAT
from ._native_gui_rules_runtime_support_constants import CONTACT_DEPT_PAT_LIGHT
from ._native_gui_rules_runtime_support_constants import CONTACT_DEPT_SENTENCE_NOISE_PAT
from ._native_gui_rules_runtime_support_constants import CONTACT_DEPT_SUFFIXES
from ._native_gui_rules_runtime_support_constants import CONTACT_DEPT_SUFFIX_PATTERN
from ._native_gui_rules_runtime_support_constants import CONTACT_ENTRUSTED_MANAGEMENT_CUE_PAT
from ._native_gui_rules_runtime_support_constants import CONTACT_EXPLICIT_CUE_PAT
from ._native_gui_rules_runtime_support_constants import CONTACT_EXTERNAL_PORTAL_CUE_PAT
from ._native_gui_rules_runtime_support_constants import CONTACT_EXTERNAL_PORTAL_NOISE_PHONES
from ._native_gui_rules_runtime_support_constants import CONTACT_EXTERNAL_PORTAL_PAT
from ._native_gui_rules_runtime_support_constants import CONTACT_GENERIC_DEPT_EXACT
from ._native_gui_rules_runtime_support_constants import CONTACT_GUIDELINE_CUE_PAT
from ._native_gui_rules_runtime_support_constants import CONTACT_MANAGEMENT_AGENCY_NOISE_PAT
from ._native_gui_rules_runtime_support_constants import CONTACT_OTHER_SENTENCE_FRAGMENT_PAT
from ._native_gui_rules_runtime_support_constants import CONTACT_PERSON_TITLE_PATTERN
from ._native_gui_rules_runtime_support_constants import CONTACT_RESULT_CUE_PAT
from ._native_gui_rules_runtime_support_constants import CONTACT_REVIEWER_TABLE_PAT
from ._native_gui_rules_runtime_support_constants import CONTACT_SHORT_NOISE_DEPTS
from ._native_gui_rules_runtime_support_constants import CONTACT_STRUCTURED_DEPT_PHONE_PAT
from ._native_gui_rules_runtime_support_constants import CONTACT_SUBMISSION_CUE_PAT
from ._native_gui_rules_runtime_support_constants import MANUAL_FIELD_OVERRIDES
from ._native_gui_rules_runtime_support_constants import OWNER_SUBORDINATE_DEPT_CUE_PAT
from ._native_gui_rules_runtime_support_constants import PHONE_FLEX_PAT
from ._native_gui_rules_runtime_support_constants import SCHOOL_ORG_CUE_PAT
from ._native_gui_rules_runtime_support_constants import norm_space
from ._native_gui_rules_runtime_support_contact_helpers import looks_like_architecture_firm_name as _looks_like_architecture_firm_name_impl
from ._native_gui_rules_runtime_support_contact_helpers import normalize_contact_candidate as _normalize_contact_candidate_impl

def _strip_contact_person_tail(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    trimmed = re.sub(
        rf"\s+[가-힣]{{2,4}}\s+(과|팀|실|국|처)\s*$",
        "",
        text,
    ).strip()
    if trimmed != text and re.search(rf"(?:{CONTACT_DEPT_SUFFIX_PATTERN})$", trimmed):
        return trimmed
    trimmed = re.sub(
        rf"\s+[가-힣]{{2,4}}\s*(?:{CONTACT_PERSON_TITLE_PATTERN})\s*$",
        "",
        text,
    ).strip()
    if trimmed != text and re.search(rf"(?:{CONTACT_DEPT_SUFFIX_PATTERN})$", trimmed):
        return trimmed
    return text


def _strip_leading_contact_clause(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    stripped = re.sub(
        rf"^.*?(?:여부는|사항은|문의는|문의처는|연락처는)\s+"
        rf"([가-힣A-Za-z0-9·\s]{{2,40}}(?:{CONTACT_DEPT_SUFFIX_PATTERN})"
        rf"(?:\s+[가-힣A-Za-z0-9·\s]{{1,20}}(?:{CONTACT_DEPT_SUFFIX_PATTERN}))?)$",
        r"\1",
        text,
        flags=re.I,
    ).strip()
    return stripped or text


def has_external_competition_portal_only_contact(text: str) -> bool:
    value = str(text or "").strip()
    if not value:
        return False
    return bool(
        CONTACT_EXTERNAL_PORTAL_PAT.search(value)
        and CONTACT_EXTERNAL_PORTAL_CUE_PAT.search(value)
    )


def is_building_like_project(project_name: str) -> bool:
    pname = str(project_name or "")
    return any(
        token in pname
        for token in (
            "설계공모",
            "설계용역",
            "기본 및 실시설계",
            "기본·실시설계",
            "건립",
            "신축",
            "증축",
            "개축",
            "리모델링",
            "복합센터",
            "도서관",
            "학교",
            "센터",
            "청사",
            "회관",
            "생활문화",
            "문화센터",
        )
    )


def is_auxiliary_service_project(project_name: str) -> bool:
    title = norm_space(project_name)
    if not title:
        return False
    return any(
        token in title
        for token in (
            "관리용역",
            "대행용역",
            "운영대행용역",
            "통합관리용역",
            "운영용역",
            "설계공모관리용역",
            "설계공모관리",
            "제안서평가",
            "평가용역",
            "유지보수",
            "공모전운영",
            "공모대전운영",
            "시상식운영",
            "심사중계",
            "송출용역",
            "매뉴얼제작",
            "심사시스템",
            "홈페이지이관",
            "재구축용역",
            "리빙랩운영",
            "운영위탁용역",
        )
    )


def looks_like_architecture_firm_name(name: str) -> bool:
    return _looks_like_architecture_firm_name_impl(name, norm_space_fn=norm_space)

def normalize_contact_candidate(contact: str, org_name: str) -> str:
    return _normalize_contact_candidate_impl(
        _sanitize_contact_value(contact),
        org_name,
        phone_pattern=PHONE_FLEX_PAT,
        light_clean_contact_dept_fn=light_clean_contact_dept,
        clean_contact_dept_fn=_clean_contact_dept,
        normalize_phone_fn=normalize_phone,
        is_noise_phone_fn=is_noise_phone,
        dept_pattern=CONTACT_DEPT_PAT_LIGHT,
    )

def extract_contact_resolution_from_notice_text(text: str, org_name: str) -> ContactResolution:
    observations = extract_contact_observations_from_notice_text(text, org_name)
    source = str(text or "").strip()
    if not observations:
        entrusted_tokens = (
            "공모관리기관",
            "공모 관리기관",
            "공모관리용역사",
            "공모 관리용역사",
            "설계공모 관리용역사",
            "관리용역사",
            "운영용역사",
            "운영업체",
            "마실와이드",
            "마실",
            "평가기관",
            "산업정책연구원",
            "한국산업정책연구원",
        )
        submission_tokens = (
            "접수처",
            "제출처",
            "접수사실",
            "질의 접수",
            "작품 접수",
            "제안서 제출처",
            "방문 접수",
            "우편 접수",
            "전자우편 접수",
        )
        if PHONE_FLEX_PAT.search(source):
            if any(token in source for token in entrusted_tokens):
                return ContactResolution(
                    status="review",
                    reason="management_or_mixed_contact_unparsed",
                    phase="notice",
                    role="entrusted_management",
                    owner_side="uncertain",
                    owner_side_basis="unknown",
                )
            if any(token in source for token in submission_tokens):
                return ContactResolution(
                    status="no_owner_candidate",
                    reason="submission_only_unparsed",
                    phase="submission",
                    role="submission_contact",
                    owner_side="uncertain",
                    owner_side_basis="unknown",
                )
    return resolve_contact_from_observations(observations)


def extract_contact_from_notice_text(text: str, org_name: str) -> str:
    observations = extract_contact_observations_from_notice_text(text, org_name)
    if observations:
        top = observations[0]
        if top.role_hint != "owner_contact":
            return ""
        return str(top.contact or "")

    dept = light_clean_contact_dept(_extract_labeled_value(text, ["담당부서", "주관부서", "문의부서"]))
    person = re.sub(r"\s+", " ", _extract_labeled_value(text, ["담당자", "문의처", "문의"])).strip()
    if person and not re.fullmatch(r"[가-힣]{2,4}", person):
        person = ""
    if dept and person:
        return f"{dept}/{person}"
    if dept:
        return dept
    return ""


def normalize_phone(value: str) -> str:
    digits = re.sub(r"[^0-9]", "", str(value or ""))
    if len(digits) == 9:
        return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"
    if len(digits) == 10:
        if digits.startswith("02"):
            return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    if len(digits) == 11:
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return str(value or "").strip()


def is_noise_phone(phone: str) -> bool:
    digits = re.sub(r"[^0-9]", "", str(phone or ""))
    if len(digits) < 9:
        return True
    if digits.endswith("0000") and len(set(digits)) <= 3:
        return True
    return False


def light_clean_contact_dept(value: str) -> str:
    dept = re.sub(r"\s+", " ", str(value or "")).strip(" /")
    if not dept:
        return ""
    dept = _strip_contact_person_tail(dept)
    dept = re.sub(r"^\s*\d+[).]\s*", "", dept).strip()
    dept = re.sub(
        r"^(?:기타\s*)?(?:문의\s*사항|문의처|문의|연락처|전화|담당자?)\s*(?:은|는)?\s*[:：]?\s*",
        "",
        dept,
        flags=re.I,
    ).strip(" :/-")
    dept = re.sub(r"^.*?(?:문의\s*사항|문의처|문의)\s*(?:은|는)?\s*[:：]?\s*", "", dept, flags=re.I).strip(" :/-")
    dept = re.sub(r"^.*?(?:기타\s*(?:자세한\s*)?사항은?)\s+", "", dept, flags=re.I).strip(" :/-")
    dept = re.sub(r"\s*(?:로)?\s*문의\s*(?:바랍니다|요망).*$", "", dept, flags=re.I).strip()
    dept = re.sub(r"(?:\s+설계공모)?\s+담당자?\s*[:：]?\s*$", "", dept).strip()
    dept = re.sub(r"^\d+\s*층\s+", "", dept).strip()
    dept = re.sub(rf"\s+[가-힣]{{2,4}}\s*(?:{CONTACT_PERSON_TITLE_PATTERN})\s*$", "", dept).strip()
    tokens = [token.strip() for token in dept.split() if token.strip()]
    if len(tokens) == 1 and tokens[0] in CONTACT_DEPT_SUFFIXES:
        return ""
    if CONTACT_COMPANY_NOISE_PAT.search(dept):
        return ""
    if CONTACT_DEPT_SENTENCE_NOISE_PAT.search(dept):
        return ""
    if CONTACT_MANAGEMENT_AGENCY_NOISE_PAT.search(dept):
        return ""
    if len(tokens) == 1 and (len(tokens[0]) <= 2 or tokens[0] in CONTACT_SHORT_NOISE_DEPTS):
        return ""
    if re.fullmatch(rf"[가-힣]{{2,4}}\s+(?:{CONTACT_DEPT_SUFFIX_PATTERN})", dept):
        return ""
    dept_norm = norm_space(dept)
    if not dept_norm or dept_norm in CONTACT_GENERIC_DEPT_EXACT:
        return ""
    if not re.search(rf"(?:{CONTACT_DEPT_SUFFIX_PATTERN})$", dept):
        return ""
    if re.search(r"(문의|문의처|연락처|전화|담당자연락처|수요기관담당자연락처|업체|평가업체|기타사항)$", dept):
        return ""
    return dept


def _prepare_contact_search_line(value: str) -> str:
    line = re.sub(r"\s+", " ", str(value or "")).strip()
    if not line:
        return ""
    if _looks_like_attachment_filename_line(line):
        return ""
    line = re.sub(r"(?:\s+설계공모)?\s+담당자?\s*$", "", line).strip()
    return line


def _looks_like_attachment_filename_line(value: str) -> bool:
    line = re.sub(r"\s+", " ", str(value or "")).strip()
    if not line:
        return False
    if not ATTACHMENT_FILENAME_LINE_PAT.search(line):
        return False
    if re.search(r"(문의|문의처|연락처|전화|담당|☎|☏|TEL|Tel|tel)", line):
        return False
    return True


def _iter_contact_phone_contexts(text: str, window_lines: int = 2) -> list[dict[str, object]]:
    source = str(text or "")
    if not source:
        return []
    lines = [str(line or "").strip() for line in re.split(r"[\r\n]+", source)]
    lines = [line for line in lines if line]
    if not lines:
        return []
    rows: list[dict[str, object]] = []
    seen: set[tuple[str, int]] = set()
    for index, line in enumerate(lines):
        if _looks_like_attachment_filename_line(line):
            continue
        for match in PHONE_FLEX_PAT.finditer(line):
            phone_raw = str(match.group(0) or "").strip()
            phone = normalize_phone(phone_raw)
            if not phone or is_noise_phone(phone):
                continue
            key = (phone, index)
            if key in seen:
                continue
            seen.add(key)
            start = max(0, index - max(0, int(window_lines)))
            end = min(len(lines), index + max(0, int(window_lines)) + 1)
            context_lines = lines[start:end]
            score = 0
            if re.search(r"(문의|담당|연락처|전화)", line):
                score += 40
            if re.search(r"(과|팀|담당|실)", line):
                score += 30
            if re.search(r"(평가\s*용역업체|평가기관|한국산업정책연구원|산업정책연구원)", line):
                score -= 70
            if re.search(r"(입찰|계약|지방계약법|계약기준)", line):
                score -= 60
            if re.search(r"(팩스|FAX)", line, re.I):
                score -= 80
            rows.append(
                {
                    "phone": phone,
                    "line": line,
                    "line_idx": index,
                    "context_start_idx": start,
                    "context_lines": context_lines,
                    "context": "\n".join(context_lines),
                    "score": score,
                }
            )
    rows.sort(key=lambda row: (int(row.get("score") or 0), -int(row.get("line_idx") or 0)), reverse=True)
    return rows


def extract_contact_observations_from_notice_text(text: str, org_name: str) -> list[ContactObservation]:
    return _extract_contact_observations_from_notice_text(text, org_name)


def _extract_contact_candidates_from_notice_text(text: str, org_name: str) -> list[dict[str, object]]:
    observations = _extract_contact_observations_from_notice_text(text, org_name)
    return [
        {
            "candidate_text": item.candidate_text,
            "contact": item.contact,
            "score": item.score,
            "is_anchor": item.is_anchor,
            "line": item.line,
            "line_idx": item.line_idx,
            "evidence_block_text": item.evidence_block_text,
            "evidence_block_type": item.evidence_block_type,
            "evidence_block_index": item.evidence_block_index,
        }
        for item in observations
    ]


def _extract_contact_observations_from_notice_text(text: str, org_name: str) -> list[ContactObservation]:
    source = str(text or "").strip()
    if not source:
        return []
    external_portal_only = has_external_competition_portal_only_contact(source)
    contexts = _iter_contact_phone_contexts(source, window_lines=2)
    if not contexts:
        return []
    person_pat = re.compile(r"(?:담당자?|담당)\s*[:：]?\s*([가-힣]{2,4})")
    rows: list[ContactObservation] = []
    for item in contexts:
        phone = str(item.get("phone") or "").strip()
        line = str(item.get("line") or "").strip()
        line_idx = int(item.get("line_idx") or 0)
        context = str(item.get("context") or "").strip()
        context_lines = item.get("context_lines") if isinstance(item.get("context_lines"), list) else []
        context_start_idx = int(item.get("context_start_idx") or max(0, line_idx - 2))
        if not phone or is_noise_phone(phone):
            continue
        if CONTACT_REVIEWER_TABLE_PAT.search(context):
            has_line_cue = bool(CONTACT_EXPLICIT_CUE_PAT.search(line))
            has_line_dept = bool(CONTACT_DEPT_PAT_LIGHT.search(line))
            if not has_line_cue and not has_line_dept:
                continue
        candidate_rows: list[dict[str, object]] = []
        order = 0
        structured_source = line
        if ":" in structured_source or "：" in structured_source:
            structured_tail = re.split(r"[:：]", structured_source, maxsplit=1)[-1].strip()
            if structured_tail:
                structured_source = structured_tail
        structured_match = CONTACT_STRUCTURED_DEPT_PHONE_PAT.search(structured_source)
        if structured_match:
            structured_dept = _clean_contact_dept(
                str(structured_match.group("dept") or structured_match.group("dept_alt") or "").strip(),
                org_name,
            )
            if structured_dept:
                candidate_rows.append(
                    {
                        "dept": structured_dept,
                        "is_anchor": True,
                        "dist": 0,
                        "order": -1,
                    }
                )
        if context_lines:
            for offset, raw_line in enumerate(context_lines):
                current = str(raw_line or "").strip()
                if not current:
                    continue
                global_idx = context_start_idx + offset
                is_anchor = bool(CONTACT_EXPLICIT_CUE_PAT.search(current))
                dist = abs(global_idx - line_idx)
                current_sources: list[str] = []
                current_for_match = _prepare_contact_search_line(current)
                if current_for_match:
                    if ":" in current_for_match or "：" in current_for_match:
                        colon_tail = re.split(r"[:：]", current_for_match, maxsplit=1)[-1].strip()
                        if colon_tail and colon_tail != current_for_match:
                            current_sources.append(colon_tail)
                    current_sources.append(current_for_match)
                for current_source in current_sources:
                    for match in CONTACT_DEPT_PAT_LIGHT.finditer(current_source):
                        dept_candidate = light_clean_contact_dept(match.group(1).strip())
                        if not dept_candidate:
                            continue
                        candidate_rows.append(
                            {
                                "dept": dept_candidate,
                                "is_anchor": is_anchor,
                                "dist": dist,
                                "order": order,
                            }
                        )
                        order += 1
        if not candidate_rows:
            is_anchor = bool(CONTACT_EXPLICIT_CUE_PAT.search(line))
            fallback_source = _prepare_contact_search_line(line or context)
            for match in CONTACT_DEPT_PAT_LIGHT.finditer(fallback_source):
                dept_candidate = light_clean_contact_dept(match.group(1).strip())
                if not dept_candidate:
                    continue
                candidate_rows.append({"dept": dept_candidate, "is_anchor": is_anchor, "dist": 0, "order": order})
                order += 1
        dept = ""
        if candidate_rows:
            anchored = [row for row in candidate_rows if row.get("is_anchor")]
            pool = anchored if anchored else candidate_rows
            pool.sort(key=lambda row: (int(row.get("dist") or 0), int(row.get("order") or 0)))
            dept = str(pool[0].get("dept") or "").strip()
        if not dept:
            continue
        person = ""
        person_match = person_pat.search(line) or person_pat.search(context)
        if person_match:
            person = str(person_match.group(1) or "").strip()
        raw_contact = f"{dept}/{person}/{phone}" if person else f"{dept}/{phone}"
        normalized = normalize_contact_candidate(raw_contact, org_name)
        if not normalized:
            continue
        normalized_phone = ""
        if "/" in normalized:
            normalized_phone = str(normalized.rsplit("/", 1)[-1] or "").strip()
        if external_portal_only and normalized_phone in CONTACT_EXTERNAL_PORTAL_NOISE_PHONES:
            continue
        phase_hint = _infer_contact_phase_hint(line=line, context=context)
        role_hint = _infer_contact_role_hint(
            candidate_text=raw_contact,
            normalized_contact=normalized,
            phone=normalized_phone or phone,
            line=line,
            context=context,
        )
        owner_side_hint, owner_side_basis_hint = _infer_contact_owner_side_hint(
            normalized_contact=normalized,
            role_hint=role_hint,
            org_name=org_name,
            line=line,
            context=context,
        )
        rows.append(
            ContactObservation(
                candidate_text=raw_contact,
                contact=normalized,
                dept=dept,
                phone=normalized_phone or phone,
                line=line,
                line_idx=line_idx,
                score=int(item.get("score") or 0),
                is_anchor=any(bool(row.get("is_anchor")) for row in candidate_rows),
                evidence_block_text=context,
                evidence_block_type="line_cluster",
                evidence_block_index=context_start_idx,
                phase_hint=phase_hint,
                role_hint=role_hint,
                owner_side_hint=owner_side_hint,
                owner_side_basis_hint=owner_side_basis_hint,
            )
        )
    deduped: dict[str, ContactObservation] = {}
    for row in rows:
        key = str(row.contact or "").strip()
        if not key:
            continue
        current = deduped.get(key)
        if current is None:
            deduped[key] = row
            continue
        if (
            bool(row.is_anchor) > bool(current.is_anchor)
            or int(row.score or 0) > int(current.score or 0)
        ):
            deduped[key] = row
    ranked = sorted(
        deduped.values(),
        key=_contact_resolution_sort_key,
        reverse=True,
    )
    return ranked


def _infer_contact_phase_hint(*, line: str, context: str) -> str:
    line_text = str(line or "")
    context_text = str(context or "")
    if CONTACT_SUBMISSION_CUE_PAT.search(line_text) or CONTACT_SUBMISSION_CUE_PAT.search(context_text):
        return "submission"
    if CONTACT_CONTRACT_CUE_PAT.search(line_text) or CONTACT_CONTRACT_CUE_PAT.search(context_text):
        return "contract"
    if CONTACT_RESULT_CUE_PAT.search(line_text) or CONTACT_RESULT_CUE_PAT.search(context_text):
        return "result_announcement"
    if CONTACT_GUIDELINE_CUE_PAT.search(line_text) or CONTACT_GUIDELINE_CUE_PAT.search(context_text):
        return "competition_guideline"
    return "notice"


def _infer_contact_role_hint(
    *,
    candidate_text: str,
    normalized_contact: str,
    phone: str,
    line: str,
    context: str,
) -> str:
    line_text = str(line or "")
    context_text = str(context or "")
    normalized = str(normalized_contact or "")
    text = "\n".join(part for part in [str(candidate_text or ""), normalized, line_text, context_text] if part)
    dept = str(normalized.split("/", 1)[0] if "/" in normalized else normalized).strip()
    dept_in_line = bool(dept and dept in line_text)
    if CONTACT_OTHER_SENTENCE_FRAGMENT_PAT.search(line_text) or CONTACT_OTHER_SENTENCE_FRAGMENT_PAT.search(text):
        return "other_notice_contact"
    if CONTACT_SUBMISSION_CUE_PAT.search(line_text):
        return "submission_contact"
    if CONTACT_ENTRUSTED_MANAGEMENT_CUE_PAT.search(line_text):
        return "entrusted_management"
    if phone in CONTACT_EXTERNAL_PORTAL_NOISE_PHONES and CONTACT_ENTRUSTED_MANAGEMENT_CUE_PAT.search(context_text):
        return "entrusted_management"
    if not dept_in_line and CONTACT_ENTRUSTED_MANAGEMENT_CUE_PAT.search(context_text):
        return "entrusted_management"
    if CONTACT_SUBMISSION_CUE_PAT.search(context_text) and not dept_in_line:
        return "submission_contact"
    if phone in CONTACT_EXTERNAL_PORTAL_NOISE_PHONES and CONTACT_EXTERNAL_PORTAL_PAT.search(text):
        return "entrusted_management"
    if CONTACT_CONTRACT_CUE_PAT.search(line_text):
        return "contract_contact"
    if CONTACT_CONTRACT_CUE_PAT.search(context_text) and not dept_in_line:
        return "contract_contact"
    return "owner_contact"


def _infer_contact_owner_side_hint(
    *,
    normalized_contact: str,
    role_hint: str,
    org_name: str,
    line: str,
    context: str,
) -> tuple[str, str]:
    if role_hint != "owner_contact":
        return "no", "unknown"

    dept = str(normalized_contact.split("/", 1)[0] if "/" in normalized_contact else normalized_contact).strip()
    org_text = str(org_name or "").strip()
    line_text = str(line or "")
    context_text = str(context or "")
    if dept == "행정실" and SCHOOL_ORG_CUE_PAT.search(org_text):
        return "yes", "school_admin_office"

    if org_text and org_text in context_text:
        return "yes", "explicit_owner_org_match"

    org_tokens = [
        token
        for token in re.split(r"\s+", org_text)
        if token and len(token) >= 2 and not token.endswith(("공사", "공단", "공사", "병원"))
    ]
    if any(token in context_text for token in org_tokens[:3]):
        return "yes", "explicit_owner_org_match"

    if OWNER_SUBORDINATE_DEPT_CUE_PAT.search(dept):
        return "yes", "owner_subordinate_org"

    if dept and dept in line_text:
        return "uncertain", "inferred_only"
    return "uncertain", "unknown"


def _sanitize_contact_value(value: str) -> str:
    cleaned = str(value or "").strip()
    cleaned = re.sub(r"[\u200b\xa0]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _sanitize_location_candidate(value: str) -> str:
    candidate = re.sub(r"[◦•·]", " ", str(value or "")).strip()
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


def _clean_contact_dept(dept: str, org_name: str) -> str:
    value = str(dept or "").strip()
    if not value:
        return ""
    value = _strip_leading_contact_clause(value)
    if value.endswith("담당자"):
        value = value[:-1]
    value = _strip_contact_person_tail(value)
    value = re.sub(r"^(?:문의처|문의사항|문의|연락처|전화|담당자?)\s*[:：\-]?\s*", "", value, flags=re.I).strip(" :/-")
    value = re.sub(r"^.*?(?:기타\s*(?:자세한\s*)?사항은?)\s+", "", value, flags=re.I).strip(" :/-")
    value = re.sub(r"(?:\s+설계공모)?\s+담당자?\s*[:：]?\s*$", "", value).strip()
    value = re.sub(r"^\d+\s*층\s+", "", value).strip()
    value = re.sub(rf"\s+[가-힣]{{2,4}}\s*(?:{CONTACT_PERSON_TITLE_PATTERN})\s*$", "", value).strip()
    tokens = [token.strip() for token in value.split() if token.strip()]
    if len(tokens) == 1 and tokens[0] in CONTACT_DEPT_SUFFIXES:
        return ""
    if CONTACT_COMPANY_NOISE_PAT.search(value):
        return ""
    if CONTACT_DEPT_SENTENCE_NOISE_PAT.search(value):
        return ""
    if CONTACT_MANAGEMENT_AGENCY_NOISE_PAT.search(value):
        return ""
    if len(tokens) == 1 and (len(tokens[0]) <= 2 or tokens[0] in CONTACT_SHORT_NOISE_DEPTS):
        return ""
    if re.fullmatch(rf"[가-힣]{{2,4}}\s+(?:{CONTACT_DEPT_SUFFIX_PATTERN})", value):
        return ""
    if org_name:
        org_text = str(org_name or "").strip()
        org_norm = norm_space(org_text)
        value_norm = norm_space(value)
        if org_norm and value_norm.startswith(org_norm) and value.startswith(org_text):
            stripped = value[len(org_text) :].strip()
            if stripped:
                value = stripped
    while True:
        trimmed = re.sub(
            r"^\s*(?:[가-힣A-Za-z0-9·\s]{0,40}(?:교육청|교육지원청|소방본부|소방서|시청|군청|구청|도청))\s*",
            "",
            value,
            count=1,
        ).strip()
        if not trimmed and re.fullmatch(rf"[가-힣A-Za-z0-9·\s]{{2,50}}(?:지원청|추진단)", value):
            break
        if trimmed == value:
            break
        value = trimmed
    value = re.sub(
        r"^\s*(?:(?:[가-힣]{2,12}(?:특별시|광역시|특별자치시|특별자치도)\s*)|(?:[가-힣]{2,12}(?:도|시|군|구)(?=\s|$)\s*))+",
        "",
        value,
    ).strip()
    match = re.search(
        rf"([가-힣A-Za-z0-9·\s]{{2,40}}(?:{CONTACT_DEPT_SUFFIX_PATTERN})"
        rf"(?:\s+[가-힣A-Za-z0-9·\s]{{1,20}}(?:{CONTACT_DEPT_SUFFIX_PATTERN}))?)",
        value,
    )
    if match:
        value = match.group(1).strip()
    segments = re.findall(rf"[가-힣A-Za-z0-9·]{{2,20}}(?:{CONTACT_DEPT_SUFFIX_PATTERN})", value)
    if len(segments) >= 2 and segments[-1].endswith(("담당", "지원청", "추진단")):
        value = segments[-1]
    if not re.search(rf"(?:{CONTACT_DEPT_SUFFIX_PATTERN})$", value):
        return ""
    if re.search(r"(문의|문의처|연락처|전화|입찰|계약|공고|심사|평가|결과|나라장터|대한민국|조달청)", value):
        return ""
    school_admin_match = re.search(r"(?:[가-힣A-Za-z0-9·\s]{2,40}(?:학교|유치원|어린이집)\s+)?(행정실)$", value)
    if school_admin_match:
        value = school_admin_match.group(1).strip()
    value = re.sub(r"\s+", " ", value).strip(" /")
    return value


def get_manual_field_overrides(bid_no: str) -> dict[str, str]:
    return dict(MANUAL_FIELD_OVERRIDES.get(str(bid_no or "").strip(), {}))


extract_notice_area_value = _area_runtime.extract_notice_area_value
extract_area_number = _cost_runtime.extract_area_number
extract_cost_won = _cost_runtime.extract_cost_won
extract_labeled_cost_text = _cost_runtime.extract_labeled_cost_text
extract_notice_cost_won = _cost_runtime.extract_notice_cost_won
format_area_number = _cost_runtime.format_area_number
format_won = _cost_runtime.format_won
extract_labeled_cost_text = _cost_runtime.extract_labeled_cost_text
extract_notice_cost_won = _cost_runtime.extract_notice_cost_won
winner_name_extractor = _winner_runtime.winner_name_extractor
