from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from backend.services.related_notice_query_runtime import PROJECT_CORE_HINT_RE
from backend.services.related_notice_query_runtime import PROJECT_DISCIPLINE_TOKENS
from backend.services.related_notice_query_runtime import PROJECT_DISCIPLINE_TOKEN_NORMS
from backend.services.related_notice_query_runtime import PROJECT_FOLLOWUP_TOKEN_NORMS
from backend.services.related_notice_query_runtime import PROJECT_LEADING_GACHING_RE
from backend.services.related_notice_query_runtime import PROJECT_LEADING_YEAR_RE
from backend.services.related_notice_query_runtime import PROJECT_MATCH_TOKEN_STOPWORDS
from backend.services.related_notice_query_runtime import PROJECT_NOTICE_SUFFIX_RE
from backend.services.related_notice_query_runtime import PROJECT_PAREN_DROP_TOKENS
from backend.services.related_notice_query_runtime import PROJECT_STEM_ACTION_TOKEN_NORMS
from backend.services.related_notice_query_runtime import PROJECT_STEM_SUFFIX_ACTION_NORMS
from backend.services.related_notice_query_runtime import PROJECT_TRAILING_NOTICE_WORD_RE
from backend.services.related_notice_query_runtime import RELATED_NOTICE_GENERIC_QUERY_TOKEN_NORMS
from backend.services.related_notice_query_runtime import _clean_project_query_text as _runtime_clean_project_query_text
from backend.services.related_notice_query_runtime import _coerce_project_query_source as _runtime_coerce_project_query_source
from backend.services.related_notice_query_runtime import _has_generic_project_tail_token
from backend.services.related_notice_query_runtime import _is_generic_project_term
from backend.services.related_notice_query_runtime import _norm_text
from backend.services.related_notice_query_runtime import _project_search_name
from backend.services.related_notice_query_runtime import _project_tokens

PROJECT_QUERY_SLUG_RE = re.compile(r"^[0-9A-Za-z가-힣]+(?:[-_][0-9A-Za-z가-힣]+){2,}$")


def _app_module():
    from backend.api import app as related_notice_app

    return related_notice_app


def _coerce_project_query_source(
    text: str,
    *,
    project_query_slug_re: re.Pattern[str] = PROJECT_QUERY_SLUG_RE,
) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    if " " not in value and project_query_slug_re.fullmatch(value):
        value = re.sub(r"[-_]+", " ", value)
    return value


def _clean_project_query_text(
    text: str,
    *,
    coerce_project_query_source_fn: Callable[[str], str] = _coerce_project_query_source,
    project_paren_drop_tokens: frozenset[str] = PROJECT_PAREN_DROP_TOKENS,
) -> str:
    cleaned = coerce_project_query_source_fn(text)
    paren_noise = {
        _norm_text(value)
        for value in [
            "ve",
            "일반",
            "긴급",
            "변경",
            "수정",
            "재공모",
            "재공고",
            "정정",
            "취소",
            "공모",
            "설계공모",
            "제안",
            "제안공모",
            "입찰대행",
            "",
        ]
    }

    def _paren_clean(match: re.Match[str]) -> str:
        inner = (match.group(1) or "").strip()
        inner_norm = _norm_text(inner)
        inner_tokens = [_norm_text(part) for part in re.split(r"[,/·\s]+", inner) if _norm_text(part)]
        if inner_norm in paren_noise or (inner_tokens and all(token in project_paren_drop_tokens for token in inner_tokens)):
            return " "
        return f" {inner} "

    cleaned = cleaned.replace("「", " ").replace("」", " ")
    cleaned = cleaned.replace("『", " ").replace("』", " ")
    cleaned = cleaned.replace("[", " ").replace("]", " ")
    cleaned = cleaned.replace("【", " ").replace("】", " ")
    cleaned = re.sub(r"[\(（]\s*([^()（）]*)\s*[\)）]", _paren_clean, cleaned)
    cleaned = re.sub(r"[\t\r\n]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.strip(" -_|/,")


def _strip_project_notice_noise(
    value: str,
    *,
    clean_project_query_text_fn: Callable[[str], str] = _clean_project_query_text,
) -> str:
    cleaned = clean_project_query_text_fn(value)
    if not cleaned:
        return ""
    cleaned = PROJECT_NOTICE_SUFFIX_RE.sub(" ", cleaned)
    cleaned = PROJECT_TRAILING_NOTICE_WORD_RE.sub(" ", cleaned)
    year_stripped = PROJECT_LEADING_YEAR_RE.sub("", cleaned).strip()
    if year_stripped and len([token for token in re.split(r"\s+", year_stripped) if token]) >= 2:
        cleaned = year_stripped
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.strip(" -_|/,")


def _project_stem_parts(
    value: str,
    *,
    project_search_name_fn: Callable[[str], str] = _project_search_name,
    clean_project_query_text_fn: Callable[[str], str] = _clean_project_query_text,
) -> tuple[tuple[str, ...], str, str]:
    search_name = project_search_name_fn(value)
    tokens = tuple(token for token in re.split(r"\s+", search_name) if token)
    if not tokens:
        return (), "", ""

    for index, token in enumerate(tokens):
        token_norm = _norm_text(token)
        action = PROJECT_STEM_SUFFIX_ACTION_NORMS.get(token_norm) or PROJECT_STEM_ACTION_TOKEN_NORMS.get(token_norm, "")
        if not action or index <= 0:
            continue
        head_tokens = tokens[:index]
        stem = clean_project_query_text_fn(" ".join((*head_tokens, action)))
        if stem:
            return head_tokens, action, stem
    return (), "", ""


def _project_stem(
    value: str,
    *,
    project_stem_parts_fn: Callable[[str], tuple[tuple[str, ...], str, str]] = _project_stem_parts,
) -> str:
    _head_tokens, _action, stem = project_stem_parts_fn(value)
    return stem


def _project_stem_head_tokens(
    value: str,
    *,
    project_stem_parts_fn: Callable[[str], tuple[tuple[str, ...], str, str]] = _project_stem_parts,
) -> tuple[str, ...]:
    head_tokens, _action, _stem = project_stem_parts_fn(value)
    filtered: list[str] = []
    for token in head_tokens:
        token_norm = _norm_text(token)
        if (
            not token_norm
            or token_norm in PROJECT_MATCH_TOKEN_STOPWORDS
            or token_norm in PROJECT_DISCIPLINE_TOKEN_NORMS
            or token_norm in PROJECT_FOLLOWUP_TOKEN_NORMS
        ):
            continue
        filtered.append(token)
    return tuple(filtered or head_tokens)


def _project_stem_head_query(
    value: str,
    *,
    project_stem_head_tokens_fn: Callable[[str], tuple[str, ...]] = _project_stem_head_tokens,
    clean_project_query_text_fn: Callable[[str], str] = _clean_project_query_text,
) -> str:
    tokens = project_stem_head_tokens_fn(value)
    return clean_project_query_text_fn(" ".join(tokens[:2]))


def _is_overly_generic_related_notice_query(
    value: str,
    *,
    norm_text_fn: Callable[[str], str] = _norm_text,
    clean_project_query_text_fn: Callable[[str], str] = _clean_project_query_text,
    is_generic_project_term_fn: Callable[[str], bool] = _is_generic_project_term,
) -> bool:
    cleaned = clean_project_query_text_fn(value)
    if not cleaned:
        return True
    tokens = [token for token in re.split(r"\s+", cleaned) if token]
    if len(tokens) < 2:
        return False

    anchor_count = 0
    for token in tokens:
        token_norm = norm_text_fn(token)
        if (
            not token_norm
            or token_norm in PROJECT_MATCH_TOKEN_STOPWORDS
            or token_norm in PROJECT_DISCIPLINE_TOKEN_NORMS
            or token_norm in PROJECT_FOLLOWUP_TOKEN_NORMS
            or token_norm in PROJECT_STEM_ACTION_TOKEN_NORMS
            or token_norm in RELATED_NOTICE_GENERIC_QUERY_TOKEN_NORMS
            or is_generic_project_term_fn(token)
        ):
            continue
        anchor_count += 1

    return len(tokens) <= 2 and anchor_count == 0


def _project_related_match_tokens(
    value: str,
    *,
    project_tokens_fn: Callable[[str], tuple[str, ...]] = _project_tokens,
) -> tuple[str, ...]:
    return tuple(
        token
        for token in project_tokens_fn(value)
        if token not in PROJECT_DISCIPLINE_TOKEN_NORMS
        and token not in PROJECT_FOLLOWUP_TOKEN_NORMS
        and token not in PROJECT_STEM_ACTION_TOKEN_NORMS
    )


def _project_discipline_bridge_query(
    value: str,
    *,
    norm_text_fn: Callable[[str], str] = _norm_text,
    clean_project_query_text_fn: Callable[[str], str] = _clean_project_query_text,
    strip_project_notice_noise_fn: Callable[[str], str] = _strip_project_notice_noise,
    project_search_name_fn: Callable[[str], str] = _project_search_name,
    project_discipline_tokens: frozenset[str] = PROJECT_DISCIPLINE_TOKENS,
) -> str:
    cleaned = clean_project_query_text_fn(value)
    if not cleaned:
        return ""
    base = strip_project_notice_noise_fn(value) or project_search_name_fn(value) or cleaned
    base_norm = norm_text_fn(base)
    text_norm = norm_text_fn(cleaned)
    if not base_norm or not text_norm:
        return ""

    for discipline in project_discipline_tokens:
        discipline_norm = norm_text_fn(discipline)
        if not discipline_norm or discipline_norm in base_norm:
            continue
        if discipline_norm not in text_norm:
            continue
        return clean_project_query_text_fn(f"{base} {discipline}")
    return ""


def _project_discipline_branch_queries(
    value: str,
    *,
    norm_text_fn: Callable[[str], str] = _norm_text,
    clean_project_query_text_fn: Callable[[str], str] = _clean_project_query_text,
    strip_project_notice_noise_fn: Callable[[str], str] = _strip_project_notice_noise,
    project_search_name_fn: Callable[[str], str] = _project_search_name,
    project_discipline_tokens: frozenset[str] = PROJECT_DISCIPLINE_TOKENS,
) -> tuple[str, ...]:
    cleaned = clean_project_query_text_fn(value)
    if not cleaned:
        return ()

    base = strip_project_notice_noise_fn(value) or project_search_name_fn(value) or cleaned
    base_norm = norm_text_fn(base)
    text_norm = norm_text_fn(cleaned)
    if not base_norm or not text_norm:
        return ()

    queries: list[str] = []
    seen: set[str] = set()

    def _add(candidate: str) -> None:
        normalized = norm_text_fn(candidate)
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        queries.append(candidate)

    for discipline in project_discipline_tokens:
        discipline_norm = norm_text_fn(discipline)
        if not discipline_norm or discipline_norm in base_norm:
            continue
        if discipline_norm not in text_norm:
            continue
        bridge = clean_project_query_text_fn(f"{base} {discipline}")
        if not bridge:
            continue
        _add(bridge)
        _add(clean_project_query_text_fn(f"{base} {discipline}\uacf5\uc0ac"))
        _add(clean_project_query_text_fn(f"{base} {discipline}\uacf5\uc0ac \uad00\uae09\uc790\uc7ac"))

    return tuple(queries)
