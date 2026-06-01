from __future__ import annotations

import re
from typing import Any
from .related_notice_query_runtime_query_source_runtime import coerce_project_query_source as _coerce_project_query_source_impl


PROJECT_TOKEN_STOPWORDS = frozenset(
    {
        "설계",
        "공모",
        "용역",
        "구매",
        "관급자재",
        "물품",
        "제작",
        "공사",
        "건축",
        "기본",
        "실시",
        "및",
        "입찰",
        "재공고",
        "정정",
        "긴급",
    }
)
PROJECT_MATCH_TOKEN_STOPWORDS = PROJECT_TOKEN_STOPWORDS | frozenset(
    {"건립사업", "건설사업", "조성사업", "신축사업", "증축공사", "개선사업", "리모델링사업"}
)
PROJECT_CORE_HINT_RE = re.compile(r"(사업|건립|신축|증축|개축|조성|개선|이전|리모델링|정비|설치|구축)")
PROJECT_NOTICE_SUFFIX_RE = re.compile(
    r"(?:\s*[-_/|,]?\s*(?:"
    r"기본\s*및\s*실시설계\s*용역\s*설계\s*공모(?:\s*공고)?|"
    r"기본\s*및\s*실시설계\s*용역\s*설계공모(?:\s*공고)?|"
    r"기본\s*및\s*실시설계\s*공모(?:\s*공고)?|"
    r"기본\s*및\s*실시설계\s*용역|"
    r"기본\s*및\s*실시설계|"
    r"실시설계\s*용역|"
    r"국제\s*설계\s*공모(?:\s*공고)?|"
    r"국제설계\s*공모(?:\s*공고)?|"
    r"건축\s*설계\s*공모(?:\s*공고)?|"
    r"건축설계\s*공모(?:\s*공고)?|"
    r"설계\s*공모(?:\s*공고)?|"
    r"설계공모(?:\s*공고)?|"
    r"설계\s*용역|"
    r"설계용역|"
    r"제안\s*공모|"
    r"제안공모|"
    r"입찰대행|"
    r"건축"
    r"))+\s*$",
    flags=re.IGNORECASE,
)
PROJECT_TRAILING_NOTICE_WORD_RE = re.compile(r"(?:\s*[-_/|,]?\s*(?:공고|입찰대행))+\s*$", flags=re.IGNORECASE)
PROJECT_LEADING_YEAR_RE = re.compile(r"^\s*(?:19|20)\d{2}\s*년\s+")
PROJECT_LEADING_GACHING_RE = re.compile(r"^\s*[\(\[]?\s*가칭\s*[\)\]]?\s*")
RELATED_NOTICE_LIVE_REQUEST_TIMEOUT_SEC = 6
RELATED_NOTICE_LIVE_DEADLINE_SEC = 30
RELATED_NOTICE_PRIMARY_REQUEST_TIMEOUT_SEC = 8
RELATED_NOTICE_ALGORITHM_VERSION = 14
RELATED_NOTICE_PRIMARY_SCOPE_TARGET_ITEMS = 5
RELATED_NOTICE_PRIMARY_ACCEPTABLE_MIN_ITEMS = 2
RELATED_NOTICE_PRIMARY_MAX_VARIANTS = 4
RELATED_NOTICE_LIVE_MAX_VARIANTS = 2
RELATED_NOTICE_COLLECT_MAX_QUERIES = 6
RELATED_NOTICE_LIVE_ROWS_PER_PAGE = 100
RELATED_NOTICE_LIVE_MAX_PAGES = 1
RELATED_NOTICE_PRIMARY_MAX_PAGES = 3
RELATED_NOTICE_LIVE_MAX_COLLECTED_ROWS = 80
RELATED_NOTICE_RECIPE_MAX_WORKERS = 3
RELATED_NOTICE_TARGET_MIN_ITEMS = 4
RELATED_NOTICE_BROAD_RETRY_FOUND_THRESHOLD = 3
RELATED_NOTICE_LIVE_EARLY_STOP_AT = 0
RELATED_NOTICE_PRECOMPUTE_STALE_SEC = 300
RELATED_NOTICE_SERVICE_HINT_TOKENS = frozenset(
    {
        "설계",
        "감리",
        "용역",
        "조사",
        "평가",
        "검토",
        "ve",
        "경제성",
    }
)
RELATED_NOTICE_CONSTRUCTION_HINT_TOKENS = frozenset(
    {
        "공사",
        "건립공사",
        "신축공사",
        "증축공사",
        "전기",
        "소방",
        "통신",
        "기계",
        "토목",
        "철거",
    }
)
RELATED_NOTICE_GOODS_HINT_TOKENS = frozenset(
    {
        "관급자재",
        "구매",
        "제작",
        "설치",
        "납품",
        "자재",
    }
)

def _slugify(value: str) -> str:
    compact = "-".join(part for part in str(value or "").strip().lower().replace("/", " ").split() if part)
    return compact or "project"


def _norm_text(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", str(value or "")).lower()


PROJECT_PAREN_DROP_TOKENS = frozenset(
    {
        _norm_text(value)
        for value in [
            "전기",
            "소방",
            "통신",
            "건축",
            "기계",
            "토목",
            "조경",
            "감리",
            "1차분",
            "2차분",
            "총괄분",
            "입찰대행",
            "제안공모",
            "제안",
            "공고",
        ]
    }
)


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
        "건립사업",
        "건설사업",
        "조성사업",
        "신축사업",
        "증축공사",
        "건립공사",
        "신축공사",
        "조성공사",
        "공사",
        "용역",
        "설계공모",
    )
    return any(norm.endswith(_norm_text(value)) for value in tail_terms)


PROJECT_STEM_ACTION_TOKENS = frozenset(
    {"건립", "건설", "신축", "증축", "개축", "조성", "개선", "이전", "리모델링", "정비", "설치", "구축"}
)
PROJECT_STEM_SUFFIX_ACTION_MAP = {
    "건립공사": "건립",
    "건립사업": "건립",
    "건설사업": "건설",
    "신축공사": "신축",
    "신축사업": "신축",
    "증축공사": "증축",
    "증축사업": "증축",
    "개축공사": "개축",
    "개축사업": "개축",
    "조성사업": "조성",
    "조성공사": "조성",
    "개선사업": "개선",
    "개선공사": "개선",
    "이전사업": "이전",
    "이전공사": "이전",
    "구축공사": "구축",
    "구축사업": "구축",
}
PROJECT_DISCIPLINE_TOKENS = frozenset(
    {"건축", "전기", "통신", "소방", "기계", "토목", "조경", "상수도", "가스", "냉난방", "정보통신"}
)
PROJECT_FOLLOWUP_TOKENS = frozenset({"공사", "용역", "구매", "감리", "관급자재", "자재", "폐기물"})
PROJECT_STEM_ACTION_TOKEN_NORMS = {_norm_text(value): value for value in PROJECT_STEM_ACTION_TOKENS}
PROJECT_STEM_SUFFIX_ACTION_NORMS = {
    _norm_text(key): value for key, value in PROJECT_STEM_SUFFIX_ACTION_MAP.items()
}
PROJECT_DISCIPLINE_TOKEN_NORMS = frozenset(_norm_text(value) for value in PROJECT_DISCIPLINE_TOKENS)
PROJECT_FOLLOWUP_TOKEN_NORMS = frozenset(_norm_text(value) for value in PROJECT_FOLLOWUP_TOKENS)
RELATED_NOTICE_GENERIC_QUERY_TOKEN_NORMS = frozenset(
    _norm_text(value)
    for value in (
        "교사",
        "학교",
        "센터",
        "시설",
        "회관",
        "청사",
        "기숙사",
        "도서관",
        "체험관",
        "건립",
        "신축",
        "증축",
        "개축",
        "조성",
        "개선",
        "리모델링",
        "구축",
        "공사",
        "용역",
        "사업",
        "설계",
        "설계공모",
    )
)


def _project_stem_parts(value: str) -> tuple[tuple[str, ...], str, str]:
    search_name = _project_search_name(value)
    tokens = tuple(token for token in re.split(r"\s+", search_name) if token)
    if not tokens:
        return (), "", ""

    for index, token in enumerate(tokens):
        token_norm = _norm_text(token)
        action = PROJECT_STEM_SUFFIX_ACTION_NORMS.get(token_norm) or PROJECT_STEM_ACTION_TOKEN_NORMS.get(token_norm, "")
        if not action or index <= 0:
            continue
        head_tokens = tokens[:index]
        stem = _clean_project_query_text(" ".join((*head_tokens, action)))
        if stem:
            return head_tokens, action, stem
    return (), "", ""


def _project_stem(value: str) -> str:
    _head_tokens, _action, stem = _project_stem_parts(value)
    return stem


def _project_stem_head_tokens(value: str) -> tuple[str, ...]:
    head_tokens, _action, _stem = _project_stem_parts(value)
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


def _project_stem_head_query(value: str) -> str:
    tokens = _project_stem_head_tokens(value)
    return _clean_project_query_text(" ".join(tokens[:2]))


def _is_overly_generic_related_notice_query(value: str) -> bool:
    cleaned = _clean_project_query_text(value)
    if not cleaned:
        return True
    tokens = [token for token in re.split(r"\s+", cleaned) if token]
    if len(tokens) < 2:
        return False

    anchor_count = 0
    for token in tokens:
        token_norm = _norm_text(token)
        if (
            not token_norm
            or token_norm in PROJECT_MATCH_TOKEN_STOPWORDS
            or token_norm in PROJECT_DISCIPLINE_TOKEN_NORMS
            or token_norm in PROJECT_FOLLOWUP_TOKEN_NORMS
            or token_norm in PROJECT_STEM_ACTION_TOKEN_NORMS
            or token_norm in RELATED_NOTICE_GENERIC_QUERY_TOKEN_NORMS
            or _is_generic_project_term(token)
        ):
            continue
        anchor_count += 1

    return len(tokens) <= 2 and anchor_count == 0


def _project_related_match_tokens(value: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in _project_tokens(value)
        if token not in PROJECT_DISCIPLINE_TOKEN_NORMS
        and token not in PROJECT_FOLLOWUP_TOKEN_NORMS
        and token not in PROJECT_STEM_ACTION_TOKEN_NORMS
    )


def _project_discipline_bridge_query(value: str) -> str:
    cleaned = _clean_project_query_text(value)
    if not cleaned:
        return ""
    base = _strip_project_notice_noise(value) or _project_search_name(value) or cleaned
    base_norm = _norm_text(base)
    text_norm = _norm_text(cleaned)
    if not base_norm or not text_norm:
        return ""

    for discipline in PROJECT_DISCIPLINE_TOKENS:
        discipline_norm = _norm_text(discipline)
        if not discipline_norm or discipline_norm in base_norm:
            continue
        if discipline_norm not in text_norm:
            continue
        return _clean_project_query_text(f"{base} {discipline}")
    return ""


def _project_discipline_branch_queries(value: str) -> tuple[str, ...]:
    cleaned = _clean_project_query_text(value)
    if not cleaned:
        return ()

    base = _strip_project_notice_noise(value) or _project_search_name(value) or cleaned
    base_norm = _norm_text(base)
    text_norm = _norm_text(cleaned)
    if not base_norm or not text_norm:
        return ()

    queries: list[str] = []
    seen: set[str] = set()

    def _add(candidate: str) -> None:
        normalized = _norm_text(candidate)
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        queries.append(candidate)

    for discipline in PROJECT_DISCIPLINE_TOKENS:
        discipline_norm = _norm_text(discipline)
        if not discipline_norm or discipline_norm in base_norm:
            continue
        if discipline_norm not in text_norm:
            continue
        bridge = _clean_project_query_text(f"{base} {discipline}")
        if not bridge:
            continue
        _add(bridge)
        _add(_clean_project_query_text(f"{base} {discipline}\uacf5\uc0ac"))
        _add(_clean_project_query_text(f"{base} {discipline}\uacf5\uc0ac \uad00\uae09\uc790\uc7ac"))

    return tuple(queries)


def _coerce_project_query_source(text: str) -> str:
    return _coerce_project_query_source_impl(text)


def _clean_project_query_text(text: str) -> str:
    cleaned = _coerce_project_query_source(text)
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
        if inner_norm in paren_noise or (inner_tokens and all(token in PROJECT_PAREN_DROP_TOKENS for token in inner_tokens)):
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


def _strip_project_notice_noise(value: str) -> str:
    cleaned = _clean_project_query_text(value)
    if not cleaned:
        return ""
    cleaned = PROJECT_NOTICE_SUFFIX_RE.sub(" ", cleaned)
    cleaned = PROJECT_TRAILING_NOTICE_WORD_RE.sub(" ", cleaned)
    year_stripped = PROJECT_LEADING_YEAR_RE.sub("", cleaned).strip()
    if year_stripped and len([token for token in re.split(r"\s+", year_stripped) if token]) >= 2:
        cleaned = year_stripped
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.strip(" -_|/,")


def _strip_project_prefix_noise(value: str) -> str:
    cleaned = _clean_project_query_text(value)
    if not cleaned:
        return ""
    stripped = PROJECT_LEADING_GACHING_RE.sub("", cleaned).strip()
    return stripped or cleaned


def _project_search_name(value: str) -> str:
    return _select_project_search_name(value)


def _project_match_key(value: str) -> str:
    search_name = _project_search_name(value)
    return _norm_text(search_name)


def _project_tokens(value: str) -> tuple[str, ...]:
    search_name = _project_search_name(value)
    tokens = []
    for token in re.split(r"[^0-9A-Za-z가-힣]+", search_name):
        normalized = token.strip().lower()
        if len(normalized) < 2 or normalized in PROJECT_MATCH_TOKEN_STOPWORDS:
            continue
        tokens.append(normalized)
    return tuple(tokens)


def _build_project_query_variants(project_name_norm: str) -> list[str]:
    base = _clean_project_query_text(project_name_norm)
    if not base:
        return []

    variants: list[str] = []
    seen_norm: set[str] = set()

    def _add(candidate: str) -> None:
        cleaned = _clean_project_query_text(candidate)
        if not cleaned:
            return
        cleaned_norm = _norm_text(cleaned)
        if not cleaned_norm or cleaned_norm in seen_norm:
            return
        if _is_generic_project_term(cleaned):
            return
        seen_norm.add(cleaned_norm)
        variants.append(cleaned)

    _add(base)
    _add(_strip_project_prefix_noise(base))

    stripped = _strip_project_notice_noise(base)
    _add(stripped)
    _add(PROJECT_LEADING_YEAR_RE.sub("", stripped or base).strip())
    _add(_strip_project_prefix_noise(stripped or base))

    split_candidates = re.split(r"\s*[-,/|]\s*", stripped or base)
    if len(split_candidates) >= 2:
        last_part = split_candidates[-1].strip()
        first_part = split_candidates[0].strip()
        if PROJECT_CORE_HINT_RE.search(last_part) and not PROJECT_CORE_HINT_RE.search(first_part):
            _add(last_part)

    noise_norm = {
        _norm_text(value)
        for value in ["기본", "및", "실시", "설계", "용역", "공모", "설계공모", "건축설계", "건축설계공모", "건축"]
    }
    tokens = [token for token in re.split(r"\s+", stripped or base) if token]
    core_tokens = [token for token in tokens if _norm_text(token) not in noise_norm]
    if len(core_tokens) >= 2:
        trailing_token = core_tokens[-1]
        if len(core_tokens) >= 3 and _has_generic_project_tail_token(trailing_token):
            _add(" ".join(core_tokens[:-1]))
        _add(" ".join(core_tokens[:8]))
        core2 = " ".join(core_tokens[:2])
        if len(_norm_text(core2)) >= 6:
            _add(core2)
        if len(core_tokens) >= 4:
            _add(" ".join(core_tokens[:2] + core_tokens[-2:]))
        elif len(core_tokens) == 3:
            _add(" ".join(core_tokens))

    return variants


def _build_related_notice_query_variants(project_name: str) -> list[str]:
    base = str(project_name or "").strip()
    if not base:
        return []

    variants: list[str] = []
    seen: set[str] = set()

    def _add(value: str) -> None:
        cleaned = _clean_project_query_text(value)
        if not cleaned:
            return
        if variants and _is_overly_generic_related_notice_query(cleaned):
            return
        key = _norm_text(cleaned)
        if not key or key in seen:
            return
        seen.add(key)
        variants.append(cleaned)

    for value in _build_project_query_variants(base):
        _add(value)

    stripped = _strip_project_notice_noise(base) or _clean_project_query_text(base)
    stem = _project_stem(stripped or base)
    _add(stem)
    _add(_project_stem_head_query(stem or stripped or base))
    _add(_project_discipline_bridge_query(base))
    for value in _project_discipline_branch_queries(base):
        _add(value)

    tokens = [token for token in re.split(r"\s+", stripped) if token]
    content_tokens = [token for token in tokens if _norm_text(token) not in PROJECT_TOKEN_STOPWORDS]
    anchor_tokens = [
        token
        for token in tokens
        if _norm_text(token)
        and _norm_text(token) not in PROJECT_MATCH_TOKEN_STOPWORDS
        and _norm_text(token) not in PROJECT_DISCIPLINE_TOKEN_NORMS
        and _norm_text(token) not in PROJECT_FOLLOWUP_TOKEN_NORMS
        and _norm_text(token) not in PROJECT_STEM_ACTION_TOKEN_NORMS
    ]

    if len(content_tokens) >= 2:
        _add(" ".join(content_tokens[:2]))
    if len(content_tokens) >= 3:
        _add(" ".join(content_tokens[:3]))
        _add(" ".join(content_tokens[-2:]))
    if len(content_tokens) >= 4:
        _add(" ".join(content_tokens[1:4]))

    if len(anchor_tokens) >= 2:
        phase_anchor = " ".join(anchor_tokens[:2])
        for phase_term in ("실시설계", "설계용역", "감리", "공사"):
            _add(f"{phase_anchor} {phase_term}")

    return variants


def _build_related_notice_primary_scopes(project: dict[str, Any]) -> list[str]:
    text = " ".join(
        filter(
            None,
            (
                str(project.get("project_name") or "").strip(),
                str(project.get("project_search_name") or "").strip(),
                str(project.get("latest_notice_title") or "").strip(),
            ),
        )
    )
    tokens = set(_project_tokens(text))
    scores = {
        "service": len(tokens & RELATED_NOTICE_SERVICE_HINT_TOKENS),
        "construction": len(tokens & RELATED_NOTICE_CONSTRUCTION_HINT_TOKENS),
        "goods": len(tokens & RELATED_NOTICE_GOODS_HINT_TOKENS),
    }
    priority = {
        "service": 0,
        "construction": 1,
        "goods": 2,
    }
    scopes = sorted(
        ("service", "construction", "goods"),
        key=lambda scope: (scores[scope], -priority[scope]),
        reverse=True,
    )
    return scopes


def _build_related_notice_primary_queries(project: dict[str, Any], scope: str) -> list[str]:
    canonical_query = str(project.get("project_search_name") or project.get("project_name") or "").strip()
    variants = _build_related_notice_query_variants(canonical_query)
    if not variants and canonical_query:
        variants = [canonical_query]
    if not variants:
        return []

    def _primary_query_priority(value: str) -> tuple[int, int, int, int, int, int]:
        parts = [part for part in re.split(r"\s+", str(value or "").strip()) if part]
        starts_with_gaching = 1 if PROJECT_LEADING_GACHING_RE.match(str(value or "").strip()) else 0
        trailing_is_generic = 1 if parts and _has_generic_project_tail_token(parts[-1]) else 0
        action_stem_tail = (
            1
            if scope in {"construction", "goods"} and parts and _norm_text(parts[-1]) in PROJECT_STEM_ACTION_TOKEN_NORMS
            else 0
        )
        token_count = len(_project_tokens(value))
        core_anchor_tail = 1 if scope not in {"construction", "goods"} and trailing_is_generic and len(parts) >= 2 else 0
        return (
            -starts_with_gaching,
            action_stem_tail,
            core_anchor_tail,
            -trailing_is_generic,
            token_count,
            len(_norm_text(value)),
        )

    if scope in {"construction", "goods"}:
        ordered = sorted(variants, key=_primary_query_priority, reverse=True)
        deduped: list[str] = []
        seen: set[str] = set()
        for value in ordered:
            key = _norm_text(value)
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(value)
        variants = deduped
    else:
        variants = sorted(variants, key=_primary_query_priority, reverse=True)

    return variants[:RELATED_NOTICE_PRIMARY_MAX_VARIANTS]


def _project_search_rank(candidate: str) -> tuple[int, int, int, int, int, int, int]:
    text = _clean_project_query_text(candidate)
    stripped = _strip_project_notice_noise(text)
    stripped_text = stripped or text
    normalized = _norm_text(stripped_text)
    already_stripped_bonus = 1 if normalized == _norm_text(text) else 0
    no_delimiter_noise = 1 if not re.search(r"[-,/|]", text) else 0
    has_core_hint = 1 if PROJECT_CORE_HINT_RE.search(stripped_text) else 0
    token_count = len([token for token in re.split(r"[\s\-_/|]+", stripped_text) if token])
    single_tail_penalty = 1 if token_count >= 2 else 0
    noise_tokens = ("기본", "및", "실시", "설계", "용역", "공모", "건축")
    design_noise_score = -sum(1 for token in noise_tokens if _norm_text(token) in _norm_text(text))
    yearless_bonus = 1 if not PROJECT_LEADING_YEAR_RE.match(stripped_text) else 0
    return (
        already_stripped_bonus,
        yearless_bonus,
        design_noise_score,
        single_tail_penalty,
        no_delimiter_noise,
        has_core_hint,
        token_count,
        len(normalized),
    )


def _select_project_search_name(source_value: str, *fallback_values: str) -> str:
    candidates: list[str] = []
    for raw_value in (source_value, *fallback_values):
        candidates.extend(_build_project_query_variants(raw_value))
        stripped = _strip_project_notice_noise(raw_value)
        if stripped:
            candidates.append(stripped)
        cleaned = _clean_project_query_text(raw_value)
        if cleaned:
            candidates.append(cleaned)

    unique_candidates: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        cleaned = _clean_project_query_text(candidate)
        normalized = _norm_text(cleaned)
        if not normalized or normalized in seen:
            continue
        if _is_generic_project_term(cleaned):
            continue
        seen.add(normalized)
        unique_candidates.append(cleaned)

    if not unique_candidates:
        return _strip_project_notice_noise(source_value) or _clean_project_query_text(source_value)

    unique_candidates.sort(key=lambda value: _project_search_rank(value), reverse=True)
    return unique_candidates[0]


def _better_project_label(current_value: str, candidate_value: str) -> str:
    current = str(current_value or "").strip()
    candidate = str(candidate_value or "").strip()
    if not current:
        return candidate
    if not candidate:
        return current
    current_score = (len(_project_search_name(current)), len(current))
    candidate_score = (len(_project_search_name(candidate)), len(candidate))
    if candidate_score > current_score:
        return candidate
    return current


def _better_project_search_name(current_value: str, candidate_value: str) -> str:
    current = str(current_value or "").strip()
    candidate = str(candidate_value or "").strip()
    if not current:
        return candidate
    if not candidate:
        return current
    current_rank = _project_search_rank(current)
    candidate_rank = _project_search_rank(candidate)
    if candidate_rank > current_rank:
        return candidate
    return current

def _score_related_notice_match(project: dict[str, Any], row: dict[str, str]) -> tuple[int, str, str]:
    title = str(row.get("project_name") or "").strip()
    if not title:
        return 0, "", ""

    target_search_name = str(project.get("project_search_name") or project.get("project_name") or "").strip()
    candidate_search_name = _project_search_name(title)
    target_key = str(project.get("_project_match_key") or "").strip()
    candidate_key = _project_match_key(candidate_search_name or title)
    if not target_key or not candidate_key:
        return 0, candidate_search_name, ""

    score = 0
    reasons: list[str] = []
    if candidate_key == target_key:
        score += 100
        reasons.append("same_search_name")
    elif candidate_key in target_key or target_key in candidate_key:
        score += 72
        reasons.append("search_name_overlap")

    target_stem = _project_stem(target_search_name)
    candidate_stem = _project_stem(candidate_search_name or title)
    target_stem_key = _norm_text(target_stem)
    candidate_stem_key = _norm_text(candidate_stem)
    target_head_key = _norm_text(_project_stem_head_query(target_search_name))
    candidate_stem_text = _norm_text(candidate_stem or candidate_search_name or title)
    stem_head_match = bool(
        target_head_key and candidate_stem_text and (target_head_key in candidate_stem_text or candidate_stem_text in target_head_key)
    )
    if target_stem_key and candidate_stem_key and stem_head_match:
        if candidate_stem_key == target_stem_key:
            score += 84
            reasons.append("same_stem")
        elif candidate_stem_key in target_stem_key or target_stem_key in candidate_stem_key:
            score += 54
            reasons.append("stem_overlap")

    target_tokens = set(_project_related_match_tokens(target_search_name))
    candidate_tokens = set(_project_related_match_tokens(candidate_search_name))
    shared_tokens = sorted(target_tokens & candidate_tokens)
    if shared_tokens:
        score += min(36, len(shared_tokens) * 12)
        reasons.append(f"shared_tokens:{','.join(shared_tokens[:3])}")

    if score < 20:
        return score, candidate_search_name, ",".join(reasons)
    return score, candidate_search_name, ",".join(reasons)

def _related_notice_item_rank(item: dict[str, Any]) -> tuple[int, int, int, int]:
    return (
        int(item.get("match_score") or 0),
        1 if str(item.get("notice_detail_url") or "").strip() else 0,
        1 if str(item.get("notice_url") or "").strip() else 0,
        len(str(item.get("project_search_name") or item.get("project_name") or "")),
    )


def _dedupe_related_notice_payload_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for raw_item in items:
        item = dict(raw_item)
        title_key = _norm_text(str(item.get("project_name") or "").strip())
        issuer_key = _norm_text(str(item.get("issuer_name") or "").strip())
        announce_date = str(item.get("announce_date") or "").strip()
        bid_no = str(item.get("bid_no") or "").strip()
        bid_ord = str(item.get("bid_ord") or "").strip()
        dedupe_key = "::".join((title_key, issuer_key, announce_date))
        if not dedupe_key.strip(":"):
            dedupe_key = "::".join((title_key, issuer_key, announce_date, bid_no, bid_ord))
        current = deduped.get(dedupe_key)
        if current is None or _related_notice_item_rank(item) > _related_notice_item_rank(current):
            deduped[dedupe_key] = item

    items = list(deduped.values())
    items.sort(
        key=lambda item: (
            int(item.get("match_score") or 0),
            str(item.get("announce_date") or ""),
            str(item.get("project_name") or ""),
        ),
        reverse=True,
    )
    return items


__all__ = [
    name
    for name in globals()
    if not name.startswith("__") and (name.startswith("_") or name.isupper())
]
