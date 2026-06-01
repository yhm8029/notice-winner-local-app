from __future__ import annotations

import re


def _slugify(value: str) -> str:
    compact = "-".join(part for part in str(value or "").strip().lower().replace("/", " ").split() if part)
    return compact or "project"


def _norm_text(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", str(value or "")).lower()


PROJECT_TOKEN_STOPWORDS = frozenset(
    {
        "설계공모",
        "공모",
        "입찰공고",
        "결과공고",
        "용역",
        "사업",
        "공사",
        "신축",
        "증축",
        "개축",
        "리모델링",
    }
)
PROJECT_MATCH_TOKEN_STOPWORDS = PROJECT_TOKEN_STOPWORDS | frozenset({"기본및실시설계", "설계용역", "건축설계", "실시설계", "건립사업"})


def _is_generic_project_term(text: str) -> bool:
    norm = _norm_text(text)
    generic = {
        _norm_text("설계공모"),
        _norm_text("공모"),
        _norm_text("입찰공고"),
        _norm_text("결과공고"),
        _norm_text("용역"),
        _norm_text("사업"),
        _norm_text("공사"),
        _norm_text("신축"),
        _norm_text("증축"),
        _norm_text("개축"),
        _norm_text("리모델링"),
    }
    return (not norm) or (norm in generic)


def _has_generic_project_tail_token(text: str) -> bool:
    norm = _norm_text(text)
    if not norm:
        return False
    tail_terms = (
        "건축설계",
        "건축공사",
        "설계용역",
        "실시설계",
        "기본및실시설계",
        "기본설계",
        "실시설계용역",
        "공모",
        "입찰공고",
        "결과공고",
    )
    return any(norm.endswith(_norm_text(value)) for value in tail_terms)


RELATED_NOTICE_GENERIC_QUERY_TOKEN_NORMS = frozenset(
    _norm_text(value)
    for value in (
        "학교",
        "시청",
        "센터",
        "시설",
        "주차장",
        "체험관",
        "박물관",
        "도서관",
        "체육관",
        "건물",
        "건축",
        "설계",
        "신축",
        "증축",
        "개축",
        "리모델링",
        "용역",
        "공사",
        "사업",
        "공모",
        "입찰공고",
        "결과공고",
    )
)
