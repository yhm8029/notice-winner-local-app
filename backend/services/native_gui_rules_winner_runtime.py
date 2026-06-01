from __future__ import annotations

import re
from dataclasses import dataclass

from .native_gui_rules_location_runtime import _decode_html_entities


WINNER_PATTERNS = [
    ("strong_tag", r"<strong>([가-힣A-Za-z0-9()\s]{2,80}(?:종합건축사사무소|건축사사무소|건축사무소|건축설계사무소))</strong>", 0.95),
    ("winner_colon", r"(?:당선자|당선작|입상작|선정업체)\s*[:：]?\s*([가-힣A-Za-z0-9()\s]{2,80}(?:종합건축사사무소|건축사사무소|건축사무소|건축설계사무소))", 0.93),
    ("plain_firm", r"([가-힣A-Za-z0-9()\s]{2,80}(?:종합건축사사무소|건축사사무소|건축사무소|건축설계사무소))", 0.75),
    ("winner_bare", r"(?:당선자|당선작|입상작|선정업체)\s*[:：]?\s*([^\n\r<]{2,80})", 0.60),
]
WINNER_NOISE_KEYWORDS = ["안내", "포털", "공고", "검색", "브라우저", "접근 가능", "유튜브", "송출", "라이브"]


@dataclass(frozen=True)
class WinnerExtraction:
    winner_name: str = ""
    confidence: float = 0.0
    pattern: str = ""


def winner_name_extractor(snippet: str, title: str) -> WinnerExtraction:
    for source_text, source_name in ((snippet, "snippet"), (title, "title")):
        cleaned = _decode_html_entities(source_text)
        if not cleaned:
            continue
        for pattern_name, pattern, confidence in WINNER_PATTERNS:
            match = re.search(pattern, cleaned, flags=re.I)
            if not match:
                continue
            candidate = _clean_winner_candidate(str(match.group(1) or ""))
            if not candidate:
                continue
            if any(noise in candidate for noise in WINNER_NOISE_KEYWORDS):
                continue
            if len(candidate) < 4:
                continue
            return WinnerExtraction(winner_name=candidate, confidence=confidence, pattern=f"{pattern_name}:{source_name}")
    return WinnerExtraction()


def _clean_winner_candidate(value: str) -> str:
    candidate = re.sub(r"\s+", " ", str(value or "")).strip(" .,:;|-/")
    candidate = re.split(r"(?:연면적|공사비|예정공사비|총사업비|위치|현장|담당부서|담당자|문의처|문의|전화)", candidate, maxsplit=1)[0]
    candidate = candidate.strip(" .,:;|-/")
    return candidate
