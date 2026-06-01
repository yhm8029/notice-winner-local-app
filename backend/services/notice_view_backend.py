from __future__ import annotations

import re
from urllib.parse import urlparse

from .notice_file_view_backend import load_notice_seed_row_by_bid
from .native_export_backend import _collect_attachment_documents
from .native_export_backend import _fetch_page_documents
from .native_export_backend import _fetch_attachment_texts
from .native_export_backend import _pick_primary_document
from .seed_collect import collect_seed_rows_with_params

ALLOWED_NOTICE_VIEW_HOST_SUFFIXES = ("g2b.go.kr",)


def is_allowed_notice_view_url(url: str) -> bool:
    raw = str(url or "").strip()
    if not raw:
        return False
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = str(parsed.hostname or "").strip().lower()
    if not host:
        return False
    return any(host == suffix or host.endswith(f".{suffix}") for suffix in ALLOWED_NOTICE_VIEW_HOST_SUFFIXES)


def build_notice_view_payload(
    *,
    notice_detail_url: str,
    notice_url: str,
    project_name: str = "",
    bid_no: str = "",
    bid_ord: str = "",
    seed_row: dict[str, str] | None = None,
) -> dict[str, object]:
    bid_no_text = str(bid_no or "").strip()
    ordered_urls: list[tuple[str, str]] = []
    seen_urls: set[str] = set()
    for source_label, raw_url in (
        ("detail", notice_detail_url),
        ("base", notice_url),
    ):
        url = str(raw_url or "").strip()
        if not url or url in seen_urls:
            continue
        if not is_allowed_notice_view_url(url):
            raise ValueError("notice viewer only supports g2b.go.kr notice URLs")
        seen_urls.add(url)
        ordered_urls.append((source_label, url))
    if not ordered_urls and not bid_no_text:
        raise ValueError("notice_detail_url, notice_url, or bid_no is required")

    source_map = {url: source_label for source_label, url in ordered_urls}
    fetched_documents = _fetch_page_documents([url for _, url in ordered_urls]) if ordered_urls else []
    primary_document = _pick_primary_document(fetched_documents)

    documents: list[dict[str, object]] = []
    seen_documents: set[tuple[str, str]] = set()
    for document in fetched_documents:
        title = str(document.title or "").strip()
        text = str(document.text or "").strip()
        dedupe_key = (title, text)
        if dedupe_key in seen_documents:
            continue
        seen_documents.add(dedupe_key)
        documents.append(
            {
                "source_label": source_map.get(str(document.url or "").strip(), "notice"),
                "url": str(document.url or "").strip(),
                "title": title,
                "text": text,
                "is_primary": False,
            }
        )

    if len(str(primary_document.text or "").strip()) < 120:
        attachment_document = (
            _build_attachment_notice_document_from_row(seed_row)
            if seed_row is not None
            else _build_attachment_notice_document(bid_no=bid_no_text, bid_ord=bid_ord)
        )
        if attachment_document is not None:
            dedupe_key = (
                str(attachment_document.get("title") or "").strip(),
                str(attachment_document.get("text") or "").strip(),
            )
            if dedupe_key not in seen_documents:
                seen_documents.add(dedupe_key)
                documents.append(attachment_document)

    primary_document_payload = _pick_primary_document_payload(documents)
    primary_key = (
        str(primary_document_payload.get("title") or "").strip(),
        str(primary_document_payload.get("text") or "").strip(),
    )
    for document in documents:
        document["is_primary"] = (
            str(document.get("title") or "").strip(),
            str(document.get("text") or "").strip(),
        ) == primary_key

    primary_source_label = str(primary_document_payload.get("source_label") or "").strip()
    primary_title = (
        str(project_name or "").strip()
        if primary_source_label == "attachment" and str(project_name or "").strip()
        else str(primary_document_payload.get("title") or "").strip()
    )
    if not primary_title:
        primary_title = str(project_name or "").strip() or str(bid_no or "").strip()
    primary_text = str(primary_document_payload.get("text") or "").strip()
    primary_url = str(primary_document_payload.get("url") or "").strip()
    return {
        "project_name": str(project_name or "").strip(),
        "bid_no": bid_no_text,
        "bid_ord": str(bid_ord or "").strip(),
        "requested_urls": [url for _, url in ordered_urls],
        "document_count": len(documents),
        "title": primary_title,
        "used_url": primary_url,
        "text": primary_text,
        "documents": documents,
    }


def _pick_primary_document_payload(documents: list[dict[str, object]]) -> dict[str, object]:
    if not documents:
        return {"source_label": "notice", "url": "", "title": "", "text": "", "is_primary": True}
    ranked = sorted(
        documents,
        key=lambda item: (
            0 if str(item.get("text") or "").strip() else 1,
            -len(str(item.get("text") or "").strip()),
            0 if str(item.get("source_label") or "").strip() == "attachment" else 1,
        ),
    )
    return dict(ranked[0])


def _build_attachment_notice_document(*, bid_no: str, bid_ord: str) -> dict[str, object] | None:
    matched_row = load_notice_seed_row_by_bid(bid_no=bid_no, bid_ord=bid_ord)
    if matched_row is None:
        return None
    return _build_attachment_notice_document_from_row(matched_row)


def _build_attachment_notice_document_from_row(row: dict[str, str] | None) -> dict[str, object] | None:
    if not row:
        return None
    attachment_documents = _collect_attachment_documents(
        row,
        spec_doc_url=str(row.get("spec_doc_url") or "").strip(),
        spec_doc_file_name=str(row.get("spec_doc_file_name") or "").strip(),
    )
    if not attachment_documents:
        return None
    attachment_payload = _fetch_attachment_texts(attachment_documents)
    attachment_text = str(attachment_payload.announcement_text or attachment_payload.all_text or "").strip()
    if not attachment_text:
        return None
    title = ", ".join(
        file_name
        for file_name in [str(document.file_name or "").strip() for document in attachment_documents]
        if file_name
    )
    return {
        "source_label": "attachment",
        "url": str(attachment_documents[0].url or "").strip(),
        "title": title or "attachment",
        "text": attachment_text,
        "is_primary": False,
    }


def _normalize_bid_ord(value: object) -> str:
    raw = re.sub(r"[^0-9]", "", str(value or "").strip())
    if not raw:
        return "000"
    return f"{int(raw):03d}"
