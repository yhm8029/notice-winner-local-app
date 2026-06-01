from __future__ import annotations

import re
from dataclasses import dataclass
from threading import Event
from threading import Lock
from typing import Callable
from urllib.parse import urlparse


OFFICIAL_DOMAINS = ("go.kr", "or.kr", "re.kr", "seoul.kr", "busan.kr")
WINNER_KEYS = ("당선", "당선자", "당선작", "최우수", "선정", "수상작")
CONTEXT_KEYS = ("설계공모", "심사결과", "공모결과", "발표", "결과", "설계경기")
STAGE_1_SUFFICIENT_SCORE = 0.8
EARLY_STOP_ENABLED = True
EARLY_STOP_TOP1_SCORE = 0.9
EARLY_STOP_SCORE_MARGIN = 0.3


@dataclass
class SearchResult:
    query: str
    title: str
    url: str
    snippet: str


def search_results_without_cache(
    query: str,
    num: int,
    *,
    search_fn: Callable[[str, int], list[SearchResult]] | None = None,
) -> list[SearchResult]:
    if search_fn is None:
        return []
    return search_fn(query, num)


def make_query_cache_search_provider(
    *,
    search_fn: Callable[[str, int], list[SearchResult]] | None = None,
) -> tuple[Callable[[str, int], list[SearchResult]], dict[str, int]]:
    cache: dict[tuple[str, int], list[SearchResult]] = {}
    in_flight: dict[tuple[str, int], Event] = {}
    lock = Lock()
    stats = {"hits": 0, "misses": 0, "unique_queries": 0}
    provider = search_fn or (lambda _query, _num: [])

    def _provider(query: str, num: int) -> list[SearchResult]:
        cache_key = (query, num)
        wait_event: Event | None = None
        with lock:
            cached = cache.get(cache_key)
            if cached is not None:
                stats["hits"] += 1
                return list(cached)
            wait_event = in_flight.get(cache_key)
            if wait_event is None:
                wait_event = Event()
                in_flight[cache_key] = wait_event
                owner = True
            else:
                owner = False
        if not owner:
            wait_event.wait()
            with lock:
                cached = cache.get(cache_key, [])
                stats["hits"] += 1
                return list(cached)
        try:
            results = provider(query, num)
        except Exception:
            results = []
        with lock:
            cache[cache_key] = list(results)
            stats["misses"] += 1
            stats["unique_queries"] = len(cache)
            event = in_flight.pop(cache_key)
            event.set()
        return list(results)

    return _provider, stats


def stage_1_results_are_sufficient(candidates: list[dict[str, object]]) -> bool:
    if not candidates:
        return False
    top_candidate = candidates[0]
    top_score = float(top_candidate.get("candidate_score") or 0.0)
    top_url = str(top_candidate.get("url") or "").strip()
    return is_official_domain(top_url) and top_score >= STAGE_1_SUFFICIENT_SCORE


def merge_candidate_lists(
    first: list[dict[str, object]],
    second: list[dict[str, object]],
) -> list[dict[str, object]]:
    aggregated: dict[str, dict[str, object]] = {}
    for item in [*first, *second]:
        url = str(item.get("url") or "").strip()
        if not url:
            continue
        existing = aggregated.get(url)
        if existing is None:
            aggregated[url] = dict(item)
            continue
        existing["candidate_score"] = max(
            float(existing.get("candidate_score") or 0.0),
            float(item.get("candidate_score") or 0.0),
        )
        if len(str(item.get("title") or "")) > len(str(existing.get("title") or "")):
            existing["title"] = item.get("title", "")
        if len(str(item.get("snippet") or "")) > len(str(existing.get("snippet") or "")):
            existing["snippet"] = item.get("snippet", "")
    return sorted(aggregated.values(), key=lambda item: float(item.get("candidate_score") or 0.0), reverse=True)


def build_early_stop_log(
    *,
    bid_no: str,
    aggregated: dict[str, dict[str, object]],
    query_idx: int,
    stage: int,
) -> str | None:
    items = sorted(aggregated.values(), key=lambda item: float(item.get("candidate_score") or 0), reverse=True)
    if not items:
        return None
    top1 = items[0]
    top1_score = float(top1.get("candidate_score") or 0.0)
    top2_score = float(items[1].get("candidate_score") or 0.0) if len(items) > 1 else 0.0
    margin = top1_score - top2_score
    official = is_official_domain(str(top1.get("url") or "").strip())
    bid_no_match = classify_bid_no_match(
        bid_no=bid_no,
        url=str(top1.get("url") or ""),
        title=str(top1.get("title") or ""),
    )
    if top1_score < EARLY_STOP_TOP1_SCORE:
        return None
    if len(items) > 1 and margin < EARLY_STOP_SCORE_MARGIN:
        return None
    if not official or bid_no_match == "none":
        return None
    return (
        "early_stop: "
        f"query_idx={query_idx} "
        f"top1={top1_score:.3f} "
        f"top2={top2_score:.3f} "
        f"bid_no_match={bid_no_match} "
        f"official={official} "
        f"stage={stage}"
    )


def classify_bid_no_match(*, bid_no: str, url: str, title: str) -> str:
    token = str(bid_no or "").strip().lower()
    if not token:
        return "none"
    haystack = f"{url} {title}".lower()
    if token in haystack:
        return "exact"
    normalized_token = re.sub(r"[^a-z0-9]", "", token)
    normalized_haystack = re.sub(r"[^a-z0-9]", "", haystack)
    if normalized_token and normalized_token in normalized_haystack:
        return "partial"
    if len(normalized_token) >= 8 and normalized_token[:-3] and normalized_token[:-3] in normalized_haystack:
        return "partial"
    return "none"


def is_official_domain(url: str) -> bool:
    host = (urlparse(url or "").netloc or "").lower()
    return any(host.endswith(domain) for domain in OFFICIAL_DOMAINS)


def score_candidate(url: str, title: str, snippet: str) -> float:
    winner_hit = any(keyword in (title or "") or keyword in (snippet or "") for keyword in WINNER_KEYS)
    if not winner_hit:
        return 0.0
    score = 0.0
    if is_official_domain(url):
        score += 0.35
    if any(keyword in (title or "") for keyword in WINNER_KEYS):
        score += 0.2
    if any(keyword in (snippet or "") for keyword in WINNER_KEYS):
        score += 0.1
    if any(keyword in (title or "") for keyword in CONTEXT_KEYS):
        score += 0.07
    if any(keyword in (snippet or "") for keyword in CONTEXT_KEYS):
        score += 0.03
    if any(token in (url or "").lower() for token in ("/board/view", "/bbs/read", "/notice/view", ".pdf", ".hwp", ".hwpx")):
        score += 0.15
    return round(min(score, 1.0), 4)
