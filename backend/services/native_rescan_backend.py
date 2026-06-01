from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable
from urllib.parse import quote_plus
from urllib.parse import urlparse
from urllib.parse import urlunparse

ATTACHMENT_FIELD_COUNT = 10


def _attachment_fields(prefix: str) -> list[str]:
    fields: list[str] = []
    for index in range(1, ATTACHMENT_FIELD_COUNT + 1):
        fields.extend((f"{prefix}_url_{index}", f"{prefix}_file_name_{index}"))
    return fields


def run_internal_nav_native(
    candidate_csv: Path,
    out_csv: Path,
    *,
    progress_cb: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> None:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    with candidate_csv.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            filter_result = str(row.get("filter_result") or "").strip().upper()
            status = str(row.get("status") or "").strip().upper()
            if filter_result and filter_result != "PASS":
                continue
            if status == "EXCLUDED":
                continue
            bid_no = str(row.get("bid_no") or "").strip()
            bid_ord = _norm_ord(row.get("bid_ord") or "")
            grouped.setdefault((bid_no, bid_ord), []).append({key: str(value or "") for key, value in row.items()})

    out_rows: list[dict[str, str]] = []
    for (bid_no, bid_ord), rows in grouped.items():
        if should_stop is not None and should_stop():
            raise InterruptedError("Stopped by user.")
        rows_sorted = sorted(rows, key=lambda item: float(item.get("candidate_score") or 0), reverse=True)
        if not rows_sorted:
            continue
        top_row = rows_sorted[0]
        base_url = str(top_row.get("url") or top_row.get("notice_url") or "").strip()
        project_name_norm = str(top_row.get("project_name_norm") or "").strip()
        g2b_verified = str(top_row.get("g2b_verified") or "N").strip().upper() or "N"
        base_query = str(top_row.get("query") or "").strip()
        base_source_type = str(top_row.get("source_type") or "").strip()
        notice_url = str(top_row.get("notice_url") or "").strip()
        spec_doc_url = str(top_row.get("spec_doc_url") or "").strip()
        spec_doc_file_name = str(top_row.get("spec_doc_file_name") or "").strip()
        attachment_payload = {}
        for index in range(1, ATTACHMENT_FIELD_COUNT + 1):
            attachment_payload[f"spec_doc_url_{index}"] = str(top_row.get(f"spec_doc_url_{index}") or "").strip()
            attachment_payload[f"spec_doc_file_name_{index}"] = str(top_row.get(f"spec_doc_file_name_{index}") or "").strip()
        presmpt_prce = str(top_row.get("presmpt_prce") or "").strip()
        officer_name = str(top_row.get("officer_name") or "").strip()
        officer_tel = str(top_row.get("officer_tel") or "").strip()
        org_name = str(top_row.get("org_name") or "").strip()
        announce_date = str(top_row.get("announce_date") or "").strip()
        if not base_url:
            out_rows.append(
                {
                    "bid_no": bid_no,
                    "bid_ord": bid_ord,
                    "project_name_norm": project_name_norm,
                    "g2b_verified": g2b_verified,
                    "base_url": "",
                    "base_query": base_query,
                    "base_source_type": base_source_type,
                    "search_link": "",
                    "internal_search_url": "",
                    "notice_url": notice_url,
                    "spec_doc_url": spec_doc_url,
                    "spec_doc_file_name": spec_doc_file_name,
                    **attachment_payload,
                    "presmpt_prce": presmpt_prce,
                    "officer_name": officer_name,
                    "officer_tel": officer_tel,
                    "org_name": org_name,
                    "announce_date": announce_date,
                    "parser_version": "web-native-v1",
                    "run_mode": "native",
                    "status": "NO_BASE_URL",
                }
            )
            continue

        urls = _build_internal_search_urls(base_url=base_url, project_name_norm=project_name_norm)
        if not urls:
            urls = [base_url]
        for url in urls:
            if should_stop is not None and should_stop():
                raise InterruptedError("Stopped by user.")
            out_rows.append(
                {
                    "bid_no": bid_no,
                    "bid_ord": bid_ord,
                    "project_name_norm": project_name_norm,
                    "g2b_verified": g2b_verified,
                    "base_url": base_url,
                    "base_query": base_query,
                    "base_source_type": base_source_type,
                    "search_link": base_url,
                    "internal_search_url": url,
                    "notice_url": notice_url or base_url,
                    "spec_doc_url": spec_doc_url,
                    "spec_doc_file_name": spec_doc_file_name,
                    **attachment_payload,
                    "presmpt_prce": presmpt_prce,
                    "officer_name": officer_name,
                    "officer_tel": officer_tel,
                    "org_name": org_name,
                    "announce_date": announce_date,
                    "parser_version": "web-native-v1",
                    "run_mode": "native",
                    "status": "SEARCH_URL_BUILT",
                }
            )
        if progress_cb is not None:
            progress_cb(f"{bid_no}: internal_urls={len(urls)}")

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=[
                "bid_no",
                "bid_ord",
                "project_name_norm",
                "g2b_verified",
                "base_url",
                "base_query",
                "base_source_type",
                "search_link",
                "internal_search_url",
                "notice_url",
                "spec_doc_url",
                "spec_doc_file_name",
                *_attachment_fields("spec_doc"),
                "presmpt_prce",
                "officer_name",
                "officer_tel",
                "org_name",
                "announce_date",
                "parser_version",
                "run_mode",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)


def _build_internal_search_urls(*, base_url: str, project_name_norm: str) -> list[str]:
    url = str(base_url or "").strip()
    if not url:
        return []
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return []
    keyword = quote_plus(project_name_norm or "")
    roots = _dedupe(
        [
            url,
            urlunparse((parsed.scheme, parsed.netloc, parsed.path or "/", "", "", "")),
            urlunparse((parsed.scheme, parsed.netloc, "/", "", "", "")),
        ]
    )
    if not keyword:
        return roots[:3]
    rows: list[str] = []
    for root in roots[:3]:
        rows.extend(
            [
                root,
                f"{root}?q={keyword}",
                f"{root}?query={keyword}",
                f"{root}?search={keyword}",
                f"{root}?keyword={keyword}",
            ]
        )
    return _dedupe(rows)[:10]


def _norm_ord(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "000"
    if raw.isdigit():
        return f"{int(raw):03d}"
    return raw


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out
