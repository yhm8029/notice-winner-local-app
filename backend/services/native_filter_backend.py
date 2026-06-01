from __future__ import annotations

import csv
import os
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from pathlib import Path
from typing import Callable
from backend.services import native_filter_search_runtime
from backend.services.native_gui_rules import is_auxiliary_service_project
from backend.services.native_filter_search_runtime import build_early_stop_log
from backend.services.native_filter_search_runtime import is_official_domain
from backend.services.native_filter_search_runtime import merge_candidate_lists
from backend.services.native_filter_search_runtime import score_candidate
from backend.services.native_filter_search_runtime import stage_1_results_are_sufficient

OFFICIAL_DOMAINS = ("go.kr", "or.kr", "re.kr", "seoul.kr", "busan.kr")
WINNER_KEYS = ("당선", "당선작", "당선자", "최우수", "선정", "수상자")
CONTEXT_KEYS = ("설계공모", "심사결과", "공모결과", "발표", "결과", "설계경기")
STOPWORDS = ("설계공모", "관리용역", "제안서평가", "공모", "용역", "(긴급)", "긴급", "(일반)")
SPECIAL_CHARS = re.compile(r"[「」『』【】〔〕〈〉《》\[\]\"'·…—–―]")
MULTI_SPACE = re.compile(r"\s{2,}")
ATTACHMENT_FIELD_COUNT = 10
FILTER_ROW_MAX_WORKERS = max(1, int(str(os.getenv("WINNER_PIPELINE_FILTER_ROW_WORKERS") or "8").strip() or "8"))
STAGE_1_QUERY_COUNT = 3
EARLY_STOP_ENABLED = True


SearchResult = native_filter_search_runtime.SearchResult


def search_results_without_cache(query: str, num: int) -> list[SearchResult]:
    return native_filter_search_runtime.search_results_without_cache(query, num)


def _make_query_cache_search_provider() -> tuple[Callable[[str, int], list[SearchResult]], dict[str, int]]:
    return native_filter_search_runtime.make_query_cache_search_provider(search_fn=search_results_without_cache)


def _attachment_fields(prefix: str) -> list[str]:
    fields: list[str] = []
    for index in range(1, ATTACHMENT_FIELD_COUNT + 1):
        fields.extend((f"{prefix}_url_{index}", f"{prefix}_file_name_{index}"))
    return fields


def run_collect_native(
    input_csv: Path,
    out_csv: Path,
    *,
    advanced_options: dict[str, object] | None = None,
    progress_cb: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> None:
    with input_csv.open("r", encoding="utf-8-sig", newline="") as fp:
        input_rows = list(csv.DictReader(fp))

    out_rows: list[dict[str, object]] = []
    candidate_rows_total = 0
    direct_url_fast_path_used_count = 0
    direct_url_skipped_query_count_total = 0
    early_stop_used_count = 0
    worker_count = _resolve_filter_worker_count(
        advanced_options=advanced_options or {},
        input_row_count=len(input_rows),
    )
    search_provider, query_cache_stats = _make_query_cache_search_provider()
    if should_stop is not None and should_stop():
        raise InterruptedError("Stopped by user.")
    ordered_results: dict[int, tuple[list[dict[str, object]], str, int, bool, int, list[str]]] = {}
    next_emit_index = 0
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(
                _build_candidate_rows_for_seed_row,
                row,
                should_stop=should_stop,
                search_provider=search_provider,
            ): index
            for index, row in enumerate(input_rows)
        }
        try:
            for future in as_completed(futures):
                if should_stop is not None and should_stop():
                    _cancel_pending_futures(futures)
                    raise InterruptedError("Stopped by user.")
                index = futures[future]
                try:
                    rows, bid_no, candidate_count, used_direct_fast_path, skipped_queries, debug_messages = future.result()
                except Exception as exc:
                    if progress_cb is not None:
                        failed_bid_no = str((input_rows[index] or {}).get("bid_no") or "").strip() or f"row[{index}]"
                        progress_cb(f"{failed_bid_no}: row_error={type(exc).__name__}: {exc}")
                    raise
                ordered_results[index] = (
                    rows,
                    bid_no,
                    candidate_count,
                    used_direct_fast_path,
                    skipped_queries,
                    debug_messages,
                )
                while next_emit_index in ordered_results:
                    rows, bid_no, candidate_count, used_direct_fast_path, skipped_queries, debug_messages = ordered_results.pop(
                        next_emit_index
                    )
                    out_rows.extend(rows)
                    candidate_rows_total += candidate_count
                    if used_direct_fast_path:
                        direct_url_fast_path_used_count += 1
                        direct_url_skipped_query_count_total += skipped_queries
                    early_stop_used_count += sum(1 for message in debug_messages if message.startswith("early_stop:"))
                    next_emit_index += 1
                    if should_stop is not None and should_stop():
                        _cancel_pending_futures(futures)
                        raise InterruptedError("Stopped by user.")
        except Exception:
            _cancel_pending_futures(futures)
            raise

    if progress_cb is not None:
        progress_cb(
            "filter_summary: "
            f"seed_rows={len(input_rows)} "
            f"candidate_rows_total={candidate_rows_total} "
            f"direct_url_fast_path_used={direct_url_fast_path_used_count} "
            f"skipped_queries={direct_url_skipped_query_count_total} "
            f"early_stop_used={early_stop_used_count} "
            f"hits={query_cache_stats['hits']} "
            f"misses={query_cache_stats['misses']} "
            f"unique_queries={query_cache_stats['unique_queries']}"
        )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=[
                "bid_no",
                "bid_ord",
                "project_name_norm",
                "g2b_verified",
                "query",
                "source_type",
                "candidate_rank",
                "candidate_score",
                "url",
                "title",
                "snippet",
                "parser_version",
                "run_mode",
                "status",
                "search_fail",
                "parse_fail",
                "date_anomaly",
                "fallback_flag",
                "filter_result",
                "filter_reason",
                "notice_url",
                "spec_doc_url",
                "spec_doc_file_name",
                *_attachment_fields("spec_doc"),
                "presmpt_prce",
                "officer_name",
                "officer_tel",
                "org_name",
                "announce_date",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)


def _cancel_pending_futures(futures: dict[object, int]) -> None:
    for future in futures:
        if not future.done():
            future.cancel()


def _resolve_filter_worker_count(*, advanced_options: dict[str, object], input_row_count: int) -> int:
    worker_count = FILTER_ROW_MAX_WORKERS
    raw_value = str(advanced_options.get("filter_row_workers") or "").strip()
    if raw_value:
        try:
            worker_count = int(raw_value)
        except ValueError:
            worker_count = FILTER_ROW_MAX_WORKERS
    return min(max(1, worker_count), max(1, input_row_count))


def _build_candidate_rows_for_seed_row(
    row: dict[str, str],
    *,
    should_stop: Callable[[], bool] | None = None,
    search_provider: Callable[[str, int], list[SearchResult]] | None = None,
) -> tuple[list[dict[str, object]], str, int, bool, int, list[str]]:
    bid_no = str(row.get("bid_no") or "").strip()
    bid_ord = str(row.get("bid_ord") or "").strip() or "000"
    project_name = str(row.get("project_name") or "").strip()
    org_name = str(row.get("org_name") or "").strip()
    g2b_verified = str(row.get("g2b_verified") or "N").strip().upper() or "N"
    project_name_norm = normalize_project_name_text(project_name)
    direct_notice_url = str(row.get("bid_ntce_dtl_url") or row.get("bid_ntce_url") or "").strip()
    officer_name = str(row.get("demand_officer_name") or row.get("notice_officer_name") or "").strip()
    officer_tel = str(row.get("notice_officer_tel") or "").strip()
    presmpt_prce = str(row.get("presmpt_prce") or "").strip()
    attachment_payload = {}
    for index in range(1, ATTACHMENT_FIELD_COUNT + 1):
        attachment_payload[f"spec_doc_url_{index}"] = str(row.get(f"spec_doc_url_{index}") or "").strip()
        attachment_payload[f"spec_doc_file_name_{index}"] = str(row.get(f"spec_doc_file_name_{index}") or "").strip()
    spec_doc_url = attachment_payload.get("spec_doc_url_1", "")
    spec_doc_file_name = attachment_payload.get("spec_doc_file_name_1", "")
    announce_date = str(row.get("announce_date") or "").strip()
    debug_messages: list[str] = []

    queries = build_queries(project_name=project_name, org_name=org_name, bid_no=bid_no)
    if _seed_row_is_auxiliary_service_project(
        project_name=project_name,
        project_name_norm=project_name_norm,
        attachment_payload=attachment_payload,
    ):
        excluded_candidate = {
            "query": bid_no or project_name_norm,
            "url": direct_notice_url,
            "title": project_name,
            "snippet": " | ".join(part for part in [org_name, officer_name, officer_tel] if part),
            "candidate_score": 0,
            "source_type": "g2b_api" if direct_notice_url else "seed",
            "status": "EXCLUDED",
            "filter_result": "EXCLUDED",
            "filter_reason": "auxiliary_service_project",
            "notice_url": direct_notice_url,
            "spec_doc_url": spec_doc_url,
            "spec_doc_file_name": spec_doc_file_name,
            "presmpt_prce": presmpt_prce,
            "officer_name": officer_name,
            "officer_tel": officer_tel,
            "announce_date": announce_date,
            **attachment_payload,
        }
        return (
            [_build_output_row(
                bid_no=bid_no,
                bid_ord=bid_ord,
                project_name_norm=project_name_norm,
                g2b_verified=g2b_verified,
                direct_notice_url=direct_notice_url,
                spec_doc_url=spec_doc_url,
                spec_doc_file_name=spec_doc_file_name,
                presmpt_prce=presmpt_prce,
                officer_name=officer_name,
                officer_tel=officer_tel,
                org_name=org_name,
                announce_date=announce_date,
                attachment_payload=attachment_payload,
                candidate=excluded_candidate,
                candidate_rank=0,
            )],
            bid_no,
            0,
            bool(direct_notice_url),
            len(queries) if direct_notice_url else 0,
            debug_messages,
        )
    if direct_notice_url:
        direct_candidate = {
            "query": bid_no or project_name_norm,
            "url": direct_notice_url,
            "title": project_name,
            "snippet": " | ".join(part for part in [org_name, officer_name, officer_tel] if part),
            "candidate_score": 1.25,
            "source_type": "g2b_api",
            "filter_result": "PASS",
            "filter_reason": "g2b_notice_detail",
            "notice_url": direct_notice_url,
            "spec_doc_url": spec_doc_url,
            "spec_doc_file_name": spec_doc_file_name,
            "presmpt_prce": presmpt_prce,
            "officer_name": officer_name,
            "officer_tel": officer_tel,
            "announce_date": announce_date,
            **attachment_payload,
        }
        return (
            [_build_output_row(
                bid_no=bid_no,
                bid_ord=bid_ord,
                project_name_norm=project_name_norm,
                g2b_verified=g2b_verified,
                direct_notice_url=direct_notice_url,
                spec_doc_url=spec_doc_url,
                spec_doc_file_name=spec_doc_file_name,
                presmpt_prce=presmpt_prce,
                officer_name=officer_name,
                officer_tel=officer_tel,
                org_name=org_name,
                announce_date=announce_date,
                attachment_payload=attachment_payload,
                candidate=direct_candidate,
                candidate_rank=1,
            )],
            bid_no,
            1,
            True,
            len(queries),
            debug_messages,
        )

    stage_1_queries = queries[:STAGE_1_QUERY_COUNT]
    stage_2_queries = queries[STAGE_1_QUERY_COUNT:]
    stage_1_candidates = fetch_candidates_from_queries(
        bid_no=bid_no,
        queries=stage_1_queries,
        org_name=org_name,
        project_name=project_name_norm,
        should_stop=should_stop,
        search_provider=search_provider,
        progress_messages=debug_messages,
        stage=1,
        query_start_index=1,
    )
    candidates = stage_1_candidates
    if stage_2_queries and not stage_1_results_are_sufficient(stage_1_candidates):
        stage_2_candidates = fetch_candidates_from_queries(
            bid_no=bid_no,
            queries=stage_2_queries,
            org_name=org_name,
            project_name=project_name_norm,
            should_stop=should_stop,
            search_provider=search_provider,
            progress_messages=debug_messages,
            stage=2,
            query_start_index=STAGE_1_QUERY_COUNT + 1,
        )
        candidates = merge_candidate_lists(stage_1_candidates, stage_2_candidates)
    candidates = _drop_auxiliary_service_candidates(candidates)
    if not candidates:
        return (
            [
                {
                    "bid_no": bid_no,
                    "bid_ord": bid_ord,
                    "project_name_norm": project_name_norm,
                    "g2b_verified": g2b_verified,
                    "query": "",
                    "source_type": "",
                    "candidate_rank": 0,
                    "candidate_score": 0,
                    "url": "",
                    "title": "",
                    "snippet": "",
                    "parser_version": "web-native-v1",
                    "run_mode": "native",
                    "status": "NO_CANDIDATE",
                    "search_fail": "Y",
                    "parse_fail": "N",
                    "date_anomaly": "N",
                    "fallback_flag": "Y",
                    "filter_result": "",
                    "filter_reason": "",
                    "notice_url": direct_notice_url,
                    "spec_doc_url": spec_doc_url,
                    "spec_doc_file_name": spec_doc_file_name,
                    "presmpt_prce": presmpt_prce,
                    "officer_name": officer_name,
                    "officer_tel": officer_tel,
                    "org_name": org_name,
                    "announce_date": announce_date,
                    **attachment_payload,
                }
            ],
            bid_no,
            0,
            False,
            0,
            debug_messages,
        )

    out_rows: list[dict[str, object]] = []
    for index, candidate in enumerate(candidates, start=1):
        out_rows.append(
            _build_output_row(
                bid_no=bid_no,
                bid_ord=bid_ord,
                project_name_norm=project_name_norm,
                g2b_verified=g2b_verified,
                direct_notice_url=direct_notice_url,
                spec_doc_url=spec_doc_url,
                spec_doc_file_name=spec_doc_file_name,
                presmpt_prce=presmpt_prce,
                officer_name=officer_name,
                officer_tel=officer_tel,
                org_name=org_name,
                announce_date=announce_date,
                attachment_payload=attachment_payload,
                candidate=candidate,
                candidate_rank=index,
            )
        )
    return out_rows, bid_no, len(candidates), False, 0, debug_messages


def _build_output_row(
    *,
    bid_no: str,
    bid_ord: str,
    project_name_norm: str,
    g2b_verified: str,
    direct_notice_url: str,
    spec_doc_url: str,
    spec_doc_file_name: str,
    presmpt_prce: str,
    officer_name: str,
    officer_tel: str,
    org_name: str,
    announce_date: str,
    attachment_payload: dict[str, str],
    candidate: dict[str, object],
    candidate_rank: int,
) -> dict[str, object]:
    return {
        "bid_no": bid_no,
        "bid_ord": bid_ord,
        "project_name_norm": project_name_norm,
        "g2b_verified": g2b_verified,
        "query": candidate.get("query", ""),
        "source_type": candidate.get("source_type", "web"),
        "candidate_rank": candidate_rank,
        "candidate_score": candidate.get("candidate_score", 0),
        "url": candidate.get("url", ""),
        "title": candidate.get("title", ""),
        "snippet": candidate.get("snippet", ""),
        "parser_version": "web-native-v1",
        "run_mode": "native",
        "status": candidate.get("status", "CANDIDATE_OK"),
        "search_fail": candidate.get("search_fail", "N"),
        "parse_fail": candidate.get("parse_fail", "N"),
        "date_anomaly": candidate.get("date_anomaly", "N"),
        "fallback_flag": candidate.get("fallback_flag", "N"),
        "filter_result": candidate.get("filter_result", "PASS"),
        "filter_reason": candidate.get("filter_reason", "native_filter"),
        "notice_url": candidate.get("notice_url", direct_notice_url),
        "spec_doc_url": candidate.get("spec_doc_url", spec_doc_url),
        "spec_doc_file_name": candidate.get("spec_doc_file_name", spec_doc_file_name),
        "presmpt_prce": candidate.get("presmpt_prce", presmpt_prce),
        "officer_name": candidate.get("officer_name", officer_name),
        "officer_tel": candidate.get("officer_tel", officer_tel),
        "org_name": org_name,
        "announce_date": announce_date,
        **{
            f"spec_doc_url_{index}": str(
                candidate.get(f"spec_doc_url_{index}", attachment_payload.get(f"spec_doc_url_{index}", "")) or ""
            ).strip()
            for index in range(1, ATTACHMENT_FIELD_COUNT + 1)
        },
        **{
            f"spec_doc_file_name_{index}": str(
                candidate.get(f"spec_doc_file_name_{index}", attachment_payload.get(f"spec_doc_file_name_{index}", ""))
                or ""
            ).strip()
            for index in range(1, ATTACHMENT_FIELD_COUNT + 1)
        },
    }


def normalize_project_name_text(title: str) -> str:
    text = unicodedata.normalize("NFC", (title or "").strip())
    normalized = SPECIAL_CHARS.sub("", text)
    for word in STOPWORDS:
        normalized = normalized.replace(word, " ")
    normalized = re.sub(r"\[[^\]]*\]", " ", normalized)
    normalized = MULTI_SPACE.sub(" ", normalized).strip(" -_/\u3000")
    return normalized


def build_queries(project_name: str, org_name: str = "", bid_no: str = "") -> list[str]:
    base = normalize_project_name_text(project_name)
    parts = [part for part in (base, org_name.strip(), bid_no.strip()) if part]
    if not parts:
        return []
    queries: list[str] = []
    if bid_no:
        queries.append(f'"{bid_no}" "당선"')
        queries.append(f'"{bid_no}" "심사결과"')
    if base:
        queries.append(f'"{base}" "당선"')
        queries.append(f'"{base}" "심사결과"')
    if base and org_name:
        queries.append(f'"{base}" "{org_name.strip()}" "당선"')
        queries.append(f'"{base}" "{org_name.strip()}" "심사결과"')
    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        compact = query.strip()
        if not compact or compact in seen:
            continue
        seen.add(compact)
        deduped.append(compact)
    return deduped[:6]


def _seed_row_is_auxiliary_service_project(
    *,
    project_name: str,
    project_name_norm: str,
    attachment_payload: dict[str, str],
) -> bool:
    values = [project_name, project_name_norm]
    values.extend(value for key, value in attachment_payload.items() if key.startswith("spec_doc_file_name_"))
    return _any_auxiliary_service_text(values)


def _drop_auxiliary_service_candidates(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for candidate in candidates:
        values = [
            str(candidate.get("title") or ""),
            str(candidate.get("snippet") or ""),
            str(candidate.get("spec_doc_file_name") or ""),
        ]
        values.extend(
            str(candidate.get(f"spec_doc_file_name_{index}") or "")
            for index in range(1, ATTACHMENT_FIELD_COUNT + 1)
        )
        if _any_auxiliary_service_text(values):
            continue
        rows.append(candidate)
    return rows


def _any_auxiliary_service_text(values: list[str]) -> bool:
    return any(is_auxiliary_service_project(value) for value in values if str(value or "").strip())


def fetch_candidates_from_queries(
    *,
    bid_no: str,
    queries: list[str],
    org_name: str,
    project_name: str,
    top_n: int = 8,
    per_query_count: int = 8,
    should_stop: Callable[[], bool] | None = None,
    search_provider: Callable[[str, int], list[SearchResult]] | None = None,
    progress_messages: list[str] | None = None,
    stage: int = 1,
    query_start_index: int = 1,
) -> list[dict[str, object]]:
    aggregated: dict[str, dict[str, object]] = {}
    provider = search_provider or search_results_without_cache
    for offset, query in enumerate(queries):
        if should_stop is not None and should_stop():
            raise InterruptedError("Stopped by user.")
        try:
            results = provider(query, per_query_count)
        except Exception:
            results = []
        for result in results:
            if not is_official_domain(result.url):
                continue
            score = score_candidate(result.url, result.title, result.snippet)
            if score <= 0:
                continue
            existing = aggregated.get(result.url)
            if existing is None:
                aggregated[result.url] = {
                    "bid_no": bid_no,
                    "query": query,
                    "url": result.url,
                    "title": result.title,
                    "snippet": result.snippet,
                    "candidate_score": score,
                    "source_type": "web",
                    "filter_result": "PASS",
                    "filter_reason": "official_domain",
                }
                continue
            existing["candidate_score"] = max(float(existing["candidate_score"]), score)
            if len(result.title or "") > len(str(existing.get("title") or "")):
                existing["title"] = result.title
            if len(result.snippet or "") > len(str(existing.get("snippet") or "")):
                existing["snippet"] = result.snippet
        if EARLY_STOP_ENABLED:
            early_stop_log = build_early_stop_log(
                bid_no=bid_no,
                aggregated=aggregated,
                query_idx=query_start_index + offset,
                stage=stage,
            )
            if early_stop_log is not None:
                if progress_messages is not None:
                    progress_messages.append(early_stop_log)
                break

    items = sorted(aggregated.values(), key=lambda item: float(item.get("candidate_score") or 0), reverse=True)
    return items[: min(top_n, 12)]


