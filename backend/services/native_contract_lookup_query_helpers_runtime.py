from __future__ import annotations

import re

from .native_contract_lookup_query_runtime import _is_generic_project_term

LOFIN_COMPETITION_NOISE_PATTERNS = (
    r"국제\s*설계\s*공모",
    r"지명\s*설계\s*공모",
    r"건축\s*설계\s*공모",
    r"설계\s*공모",
    r"설계공모",
    r"제안\s*공모",
    r"제안공모",
    r"간이\s*공모",
    r"간이공모",
    r"공모",
)
LOFIN_SUFFIX_SIMPLIFICATIONS: tuple[tuple[str, str], ...] = (
    ("건립사업", "건립"),
    ("건립공사", "건립"),
    ("조성사업", "조성"),
    ("조성공사", "조성"),
    ("구축사업", "구축"),
    ("구축공사", "구축"),
)


def _build_lofin_query_variants(project_name: str) -> list[str]:
    return _build_core_project_queries(project_name)[:3]


def _build_query_variants(project_name: str) -> list[str]:
    return _build_core_project_queries(project_name)[:3]


def _build_core_project_queries(project_name: str) -> list[str]:
    base = _clean_project_query_text(project_name)
    if not base:
        return []
    base = _strip_lofin_competition_noise(base)
    base = _strip_project_suffix_noise(base)
    base = _simplify_lofin_project_suffixes(base)
    base = re.sub(r"(?:입찰\s*)?공고\s*$", " ", base, flags=re.IGNORECASE)
    base = re.sub(r"\s+", " ", base).strip()
    if not base:
        return []

    deduped: list[str] = []
    seen_norm: set[str] = set()

    def _add(candidate: str) -> None:
        compact = _compact_lofin_ascii_spacing(candidate)
        compact = _clean_project_query_text(compact)
        compact = re.sub(r"\s+", " ", compact).strip()
        if not compact:
            return
        compact_norm = re.sub(r"\s+", " ", compact).strip().lower()
        if not compact_norm or compact_norm in seen_norm:
            return
        if _is_generic_project_term(compact):
            return
        seen_norm.add(compact_norm)
        deduped.append(compact)

    _add(base)

    tokens = [token for token in re.split(r"\s+", base) if token]
    if len(tokens) >= 2:
        _add(" ".join(tokens[:-1]))

    if len(tokens) >= 2:
        nospace = "".join(tokens)
        if len(_norm_text(nospace)) >= 6:
            _add(nospace)

    return deduped[:3]


def _build_hub_project_queries(project_name: str) -> list[str]:
    base = _clean_project_query_text(project_name)
    if not base:
        return []
    base = _strip_hub_leading_qualifiers(base)
    base = _strip_lofin_competition_noise(base)
    base = _strip_project_suffix_noise(base)
    base = _simplify_lofin_project_suffixes(base)
    base = re.sub(r"(?:입찰\s*)?공고\s*$", " ", base, flags=re.IGNORECASE)
    base = re.sub(r"\s+", " ", base).strip()
    if not base:
        return []

    queries: list[str] = []
    seen: set[str] = set()

    def _add(candidate: str) -> None:
        value = _clean_project_query_text(candidate)
        value = re.sub(r"\s+", " ", value).strip()
        if not value:
            return
        norm = _norm_text(value)
        if not norm or norm in seen or _is_generic_project_term(value):
            return
        seen.add(norm)
        queries.append(value)

    _add(base)
    school_compact = _normalize_hub_school_name(base)
    _add(school_compact)

    tokens = [token for token in re.split(r"\s+", school_compact or base) if token]
    if len(tokens) >= 2:
        _add(" ".join(tokens[:-1]))
    if tokens:
        first = _normalize_hub_school_name(tokens[0])
        if len(_norm_text(first)) >= 4 and not re.fullmatch(r".+[시군구도]$", first):
            _add(first)
        token_norm = _norm_text(first)
        if re.fullmatch(r"[가-힣]{5,}", token_norm):
            for prefix_len in (2, 3, 4):
                if prefix_len < len(token_norm):
                    _add(token_norm[:prefix_len])
    if len(tokens) >= 2:
        _add("".join(tokens))

    return queries[:5]


def _clean_project_query_text(text: str) -> str:
    value = str(text or "")
    paren_noise = {
        _norm_text(x)
        for x in ("ve", "일반", "긴급", "변경", "수정", "재공모", "재공고", "정정", "취소", "공모", "설계공모", "")
    }

    def _paren_clean(match: re.Match[str]) -> str:
        inner = (match.group(1) or "").strip()
        if _norm_text(inner) in paren_noise:
            return " "
        return match.group(0)

    value = re.sub(r"[\(（]\s*([^()（）]*)\s*[\)）]", _paren_clean, value)
    value = re.sub(r"[\t\r\n]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value.strip(" -_|/,")


def _strip_hub_leading_qualifiers(text: str) -> str:
    value = _clean_project_query_text(text)
    if not value:
        return ""
    value = re.sub(r"^(?:[\(（][^()（）]{1,20}[\)）]\s*)+", "", value).strip()
    return value


def _normalize_hub_school_name(text: str) -> str:
    value = _clean_project_query_text(text)
    if not value:
        return ""
    replacements = (
        (r"([가-힣A-Za-z0-9]+)초등학교", r"\1초"),
        (r"([가-힣A-Za-z0-9]+)중학교", r"\1중"),
        (r"([가-힣A-Za-z0-9]+)고등학교", r"\1고"),
    )
    for pattern, repl in replacements:
        value = re.sub(pattern, repl, value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _strip_lofin_competition_noise(text: str) -> str:
    value = _clean_project_query_text(text)
    if not value:
        return ""
    for pattern in LOFIN_COMPETITION_NOISE_PATTERNS:
        value = re.sub(pattern, " ", value, flags=re.IGNORECASE)
    value = re.sub(r"[\(（]\s*[\)）]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _simplify_lofin_project_suffixes(text: str) -> str:
    value = _clean_project_query_text(text)
    if not value:
        return ""
    for before, after in LOFIN_SUFFIX_SIMPLIFICATIONS:
        value = value.replace(before, after)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _compact_lofin_ascii_spacing(text: str) -> str:
    value = _clean_project_query_text(text)
    if not value:
        return ""
    value = re.sub(r"([가-힣])\s+([A-Za-z0-9]{2,8})", r"\1\2", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _strip_project_suffix_noise(text: str) -> str:
    value = _clean_project_query_text(text)
    if not value:
        return ""
    value = re.sub(
        r"(?:\s*[-_/|,]?\s*(?:기본\s*및\s*실시설계\s*용역|기본\s*및\s*실시설계|실시설계\s*용역|건축\s*설계\s*공모|건축설계\s*공모|설계\s*공모|설계공모|설계\s*용역|설계용역))+\s*$",
        " ",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _norm_text(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip().lower()
