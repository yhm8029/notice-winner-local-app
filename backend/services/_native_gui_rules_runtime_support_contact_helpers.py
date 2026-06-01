from __future__ import annotations

import re
from typing import Callable
from typing import Pattern


def looks_like_architecture_firm_name(name: str, *, norm_space_fn: Callable[[str], str]) -> bool:
    value = norm_space_fn(name)
    if not value:
        return False
    if any(token in value for token in ("종합건축사사무소", "건축사사무소", "건축사", "건축설계사무소", "architect")):
        if any(token in value for token in ("유튜브", "영상", "연출", "라이브", "평면", "관리", "중계", "광고")):
            return False
        return True
    return False


def normalize_contact_candidate(
    contact: str,
    org_name: str,
    *,
    phone_pattern: Pattern[str],
    light_clean_contact_dept_fn: Callable[[str], str],
    clean_contact_dept_fn: Callable[[str, str], str],
    normalize_phone_fn: Callable[[str], str],
    is_noise_phone_fn: Callable[[str], bool],
    dept_pattern: Pattern[str],
) -> str:
    raw = str(contact or "").strip()
    if not raw:
        return ""
    match = phone_pattern.search(raw)
    if not match:
        return ""
    phone = normalize_phone_fn(match.group(0))
    if not phone or is_noise_phone_fn(phone):
        return ""
    left = str(raw[: match.start()] or "")
    left = re.sub(r"[☎☏()\[\]<>]", " ", left)
    left = re.sub(r"\s+", " ", left).strip(" /:-")
    parts = [part.strip() for part in left.split("/") if part and part.strip()]

    dept = ""
    for part in reversed(parts):
        candidate = light_clean_contact_dept_fn(part)
        if candidate:
            dept = candidate
            break
    if not dept:
        dept_candidates: list[str] = []
        for dept_match in dept_pattern.finditer(left):
            candidate = light_clean_contact_dept_fn(dept_match.group(1).strip())
            if candidate:
                dept_candidates.append(candidate)
        if dept_candidates:
            dept = max(dept_candidates, key=len)
    if not dept:
        return ""
    dept = clean_contact_dept_fn(dept, org_name)
    if not dept:
        return ""
    return f"{dept}/{phone}"
