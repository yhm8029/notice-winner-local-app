from __future__ import annotations

import time
from urllib.parse import parse_qs
from urllib.parse import urlparse
from typing import Callable

from .attachment_text_extract import AttachmentTextLoadResult
from ._native_export_backend_runtime_support_models import AttachmentDocument
from ._native_export_backend_runtime_support_models import ATTACHMENT_FIELD_COUNT
from ._native_export_backend_runtime_support_models import MAX_ATTACHMENT_DOCS


def pick_best_match(rows: list[dict[str, str]]) -> dict[str, str]:
    return sorted(
        rows,
        key=lambda item: (
            0 if str(item.get("status") or "").strip() == "SEARCH_URL_BUILT" else 1,
            len(str(item.get("internal_search_url") or "")),
        ),
    )[0]


def collect_attachment_documents(
    row: dict[str, str],
    *,
    spec_doc_url: str,
    spec_doc_file_name: str,
    attachment_document_cls: type[AttachmentDocument],
    attachment_doc_score_fn: Callable[[str], int],
) -> list[AttachmentDocument]:
    seen: set[tuple[str, str]] = set()
    rows: list[AttachmentDocument] = []
    for index in range(1, ATTACHMENT_FIELD_COUNT + 1):
        file_name = str(row.get(f"spec_doc_file_name_{index}") or "").strip()
        url = str(row.get(f"spec_doc_url_{index}") or "").strip()
        if not url:
            continue
        key = (url, file_name)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            attachment_document_cls(
                url=url,
                file_name=file_name,
                score=attachment_doc_score_fn(file_name),
                is_announcement_doc="공고" in file_name,
            )
        )
    if spec_doc_url and (spec_doc_url, spec_doc_file_name) not in seen:
        seen.add((spec_doc_url, spec_doc_file_name))
        rows.append(
            attachment_document_cls(
                url=spec_doc_url,
                file_name=spec_doc_file_name,
                score=attachment_doc_score_fn(spec_doc_file_name),
                is_announcement_doc="공고" in spec_doc_file_name,
            )
        )
    if not rows:
        rows.extend(
            _build_g2b_download_fallback_documents(
                row,
                attachment_document_cls=attachment_document_cls,
            )
        )
    rows.sort(key=lambda item: (item.score, item.file_name), reverse=True)
    return rows[:MAX_ATTACHMENT_DOCS]


def _build_g2b_download_fallback_documents(
    row: dict[str, str],
    *,
    attachment_document_cls: type[AttachmentDocument],
) -> list[AttachmentDocument]:
    notice_url = str(
        row.get("notice_url")
        or row.get("bid_ntce_dtl_url")
        or row.get("bid_ntce_url")
        or row.get("base_url")
        or ""
    ).strip()
    bid_no, bid_ord, prcm_bsne_se_cd = _resolve_g2b_download_keys(row=row, notice_url=notice_url)
    if not bid_no:
        return []
    if "g2b.go.kr" not in notice_url.lower():
        return []

    base_url = "https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do"
    common = f"bidPbancNo={bid_no}&bidPbancOrd={bid_ord or '000'}"
    suffix = f"&prcmBsneSeCd={prcm_bsne_se_cd}" if prcm_bsne_se_cd else ""
    return [
        attachment_document_cls(
            url=f"{base_url}?{common}&fileSeq={seq}&fileType={suffix}",
            file_name="",
            score=-seq,
            is_announcement_doc=False,
        )
        for seq in range(1, MAX_ATTACHMENT_DOCS + 1)
    ]


def _resolve_g2b_download_keys(*, row: dict[str, str], notice_url: str) -> tuple[str, str, str]:
    query = parse_qs(urlparse(str(notice_url or "")).query)
    bid_no = str(
        row.get("bid_no")
        or _first_query_value(query, "bidPbancNo")
        or _first_query_value(query, "bidNtceNo")
        or ""
    ).strip()
    bid_ord = str(
        row.get("bid_ord")
        or _first_query_value(query, "bidPbancOrd")
        or _first_query_value(query, "bidNtceOrd")
        or "000"
    ).strip()
    prcm_bsne_se_cd = str(_first_query_value(query, "prcmBsneSeCd") or "").strip()
    return bid_no, bid_ord or "000", prcm_bsne_se_cd


def _first_query_value(query: dict[str, list[str]], key: str) -> str:
    values = query.get(key) or []
    return str(values[0] or "").strip() if values else ""


def raise_if_stop_requested(should_stop: Callable[[], bool] | None) -> None:
    if should_stop is not None and should_stop():
        raise InterruptedError("export cancelled")


def load_attachment_text_with_timing(
    *,
    url: str,
    file_name: str,
    download_attachment_text_fn: Callable[..., str],
    download_attachment_text_with_timing_fn: Callable[..., AttachmentTextLoadResult],
) -> AttachmentTextLoadResult:
    if getattr(download_attachment_text_fn, "__module__", "") != "backend.services.attachment_text_extract":
        started = time.perf_counter()
        text = download_attachment_text_fn(url=url, file_name=file_name)
        elapsed_ms = int(round((time.perf_counter() - started) * 1000))
        return AttachmentTextLoadResult(text=text, parse_ms=elapsed_ms)
    return download_attachment_text_with_timing_fn(url=url, file_name=file_name)
