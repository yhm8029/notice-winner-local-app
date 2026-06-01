from __future__ import annotations

import re


CONTACT_PROMPT_PREFIX_PATTERN = re.compile(
    r"^.*?(?:문의(?:는)?|문의사항은|문의처는|담당자는|담당자\s*[:：]?)\s+",
    re.I,
)


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


def normalize_tracker_contact_person_only(
    value: str,
    *,
    dept_sentence_noise_pat,
    other_sentence_fragment_pat,
) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if dept_sentence_noise_pat.search(raw) or other_sentence_fragment_pat.search(raw):
        return ""
    stripped = CONTACT_PROMPT_PREFIX_PATTERN.sub("", raw).strip()
    person = stripped.split("/")[-1].strip()
    if not re.fullmatch(r"[가-힣]{2,4}", person):
        return ""
    return person


def extract_tracker_contact_dept(value: str, *, dept_suffixes) -> str:
    source = str(value or "").strip()
    if not source:
        return ""
    candidates: list[str] = []
    parts = [part.strip() for part in re.split(r"/", source) if part.strip()]
    search_space = parts if parts else [source]
    for part in search_space:
        tokens = [token.strip() for token in part.split() if token.strip()]
        for token in reversed(tokens):
            if token.endswith(dept_suffixes) and token not in {"소방본부"}:
                candidates.append(token)
                break
        else:
            if part.endswith(dept_suffixes) and part not in {"소방본부"}:
                candidates.append(part)
    if candidates:
        return candidates[-1]
    return ""


def normalize_tracker_contact(
    value: str,
    *,
    allow_person_only: bool = False,
    normalize_contact_candidate_fn,
    dept_suffixes,
    dept_sentence_noise_pat,
    other_sentence_fragment_pat,
) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    normalized = normalize_contact_candidate_fn(raw, "")
    if normalized:
        return normalized
    phone_match = re.search(r"(0\d{1,2}-\d{3,4}-\d{4}|0\d{1,2}\d{7,8})", raw)
    if not phone_match:
        return raw
    phone = normalize_phone(phone_match.group(1))
    if not phone:
        return ""
    left = re.sub(r"[()\\[\\]<>]", " ", raw[: phone_match.start()])
    left = re.sub(r"\s+", " ", left).strip(" /:-")
    dept = extract_tracker_contact_dept(left, dept_suffixes=dept_suffixes)
    if dept:
        normalized_dept_contact = normalize_contact_candidate_fn(f"{dept}/{phone}", "")
        if normalized_dept_contact:
            return normalized_dept_contact
        return ""
    if allow_person_only and left:
        person = normalize_tracker_contact_person_only(
            left,
            dept_sentence_noise_pat=dept_sentence_noise_pat,
            other_sentence_fragment_pat=other_sentence_fragment_pat,
        )
        if person:
            return f"{person}/{phone}"
    return ""
