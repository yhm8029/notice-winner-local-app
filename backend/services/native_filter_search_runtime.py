from __future__ import annotations

import re
import time
from dataclasses import dataclass
from threading import Event
from threading import Lock
from typing import Callable
from urllib.parse import parse_qs
from urllib.parse import quote
from urllib.parse import unquote
from urllib.parse import urlparse

import requests


OFFICIAL_DOMAINS = ("go.kr", "or.kr", "re.kr", "seoul.kr", "busan.kr")
WINNER_KEYS = ("당선", "당선자", "당선작", "최우수", "선정", "수상작")
CONTEXT_KEYS = ("설계공모", "심사결과", "공모결과", "발표", "결과", "설계경기")
REQUEST_TIMEOUT_SEC = 8
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
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
    provider = search_fn or search_google_html
    return provider(query, num)


def make_query_cache_search_provider(
    *,
    search_fn: Callable[[str, int], list[SearchResult]] | None = None,
) -> tuple[Callable[[str, int], list[SearchResult]], dict[str, int]]:
    cache: dict[tuple[str, int], list[SearchResult]] = {}
    in_flight: dict[tuple[str, int], Event] = {}
    lock = Lock()
    stats = {"hits": 0, "misses": 0, "unique_queries": 0}
    provider = search_fn or search_google_html

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


def search_google_html(query: str, num: int = 10, sleep_sec: float = 0.2) -> list[SearchResult]:
    url = f"https://www.google.com/search?q={quote(query)}&num={num}&hl=ko&gl=kr"
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7"}
    results: list[SearchResult] = []
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SEC)
        response.raise_for_status()
        html = response.text
        if "unusual traffic" not in html.lower() and "detected unusual" not in html.lower():
            blocks = re.findall(r"<div class=\"tF2Cxc\".*?</div></div></div>", html, flags=re.S)
            for block in blocks:
                link_match = re.search(r"<a href=\"([^\"]+)\"", block)
                if not link_match:
                    continue
                raw = extract_real_url(link_match.group(1))
                if not raw.startswith("http") or "google.com" in raw:
                    continue
                title_match = re.search(r"<h3[^>]*>(.*?)</h3>", block, flags=re.S)
                snippet_match = re.search(r"<div class=\"VwiC3b[^\"]*\"[^>]*>(.*?)</div>", block, flags=re.S)
                results.append(
                    SearchResult(
                        query=query,
                        title=re.sub("<[^>]+>", "", title_match.group(1)).strip() if title_match else "",
                        url=raw,
                        snippet=re.sub("<[^>]+>", "", snippet_match.group(1)).strip() if snippet_match else "",
                    )
                )
                if len(results) >= num:
                    break
    except Exception:
        results = []
    if not results:
        results = search_duckduckgo_html(query, num=num)
    deduped: list[SearchResult] = []
    seen: set[str] = set()
    for item in results:
        if item.url in seen:
            continue
        seen.add(item.url)
        deduped.append(item)
    time.sleep(sleep_sec)
    return deduped[:num]


def search_duckduckgo_html(query: str, num: int = 10) -> list[SearchResult]:
    url = f"https://html.duckduckgo.com/html/?q={quote(query)}&kl=kr-ko"
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7"}
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SEC)
    response.raise_for_status()
    html = response.text
    rows: list[SearchResult] = []
    links = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, flags=re.S)
    for href, title_html in links:
        raw = extract_ddg_real_url(href)
        if raw.startswith("//"):
            raw = "https:" + raw
        if not raw.startswith("http") or "duckduckgo.com" in raw:
            continue
        rows.append(
            SearchResult(
                query=query,
                title=re.sub("<[^>]+>", "", title_html).strip(),
                url=raw,
                snippet="",
            )
        )
        if len(rows) >= num:
            break
    return rows[:num]


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


def extract_real_url(href: str) -> str:
    match = re.search(r"[?&]q=([^&]+)", href)
    if match:
        return unquote(match.group(1))
    return href


def extract_ddg_real_url(href: str) -> str:
    if "uddg=" in href:
        query = parse_qs(urlparse(href).query)
        value = (query.get("uddg") or [""])[0]
        if value:
            return unquote(value)
    return href
