from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Callable
from urllib.parse import parse_qs
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

import requests

SYNAP_THUMBNAIL_XML_URL = "https://www.g2b.go.kr/SynapDocViewServer/thumbnailxml/{viewer_key}/{page_no}?dpi=96&"
SYNAP_MAX_PAGE_COUNT = 200
SYNAP_TIMEOUT_SEC = 30
SYNAP_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class SynapTextLayerResult:
    text: str = ""
    viewer_url: str = ""
    viewer_key: str = ""
    page_count: int = 0


def extract_synap_viewer_key(viewer_url: str) -> str:
    target = str(viewer_url or "").strip()
    if not target:
        return ""
    parsed = urlparse(target)
    return str((parse_qs(parsed.query).get("key") or [""])[0] or "").strip()


def extract_synap_page_text(xml_text: str) -> str:
    raw_xml = str(xml_text or "").strip()
    if not raw_xml or "<page" not in raw_xml:
        return ""
    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError:
        return ""
    page = root.find(".//page")
    if page is None:
        return ""

    blocks: list[str] = []
    for paragraph in page.iterfind(".//paragraph"):
        block = _normalize_synap_block("".join(str(node.text or "") for node in paragraph.iterfind(".//text")))
        if block:
            blocks.append(block)
    if not blocks:
        block = _normalize_synap_block("".join(str(node.text or "") for node in page.iterfind(".//text")))
        if block:
            blocks.append(block)
    return _normalize_synap_text("\n".join(blocks))


def download_synap_viewer_text(
    viewer_url: str,
    *,
    session: requests.Session | None = None,
    max_pages: int = SYNAP_MAX_PAGE_COUNT,
) -> SynapTextLayerResult:
    target_url = str(viewer_url or "").strip()
    viewer_key = extract_synap_viewer_key(target_url)
    if not target_url or not viewer_key:
        return SynapTextLayerResult(viewer_url=target_url, viewer_key=viewer_key)

    getter: Callable[..., requests.Response] = session.get if session is not None else requests.get
    page_chunks: list[str] = []
    fetched_pages = 0
    for page_no in range(1, max(1, int(max_pages)) + 1):
        page_url = SYNAP_THUMBNAIL_XML_URL.format(viewer_key=viewer_key, page_no=page_no)
        try:
            response = getter(
                page_url,
                timeout=SYNAP_TIMEOUT_SEC,
                headers={"User-Agent": SYNAP_USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7"},
            )
        except Exception:
            break
        if response.status_code != 200:
            break
        page_text = extract_synap_page_text(response.text)
        if not page_text and not _looks_like_synap_page_xml(response.text):
            break
        fetched_pages += 1
        if page_text:
            page_chunks.append(page_text)

    return SynapTextLayerResult(
        text=_normalize_synap_text("\n\n".join(chunk for chunk in page_chunks if chunk)),
        viewer_url=target_url,
        viewer_key=viewer_key,
        page_count=fetched_pages,
    )


def download_notice_attachment_text_via_synap(
    *,
    bid_no: str,
    bid_ord: str,
    attachment_url: str,
    unty_atch_file_no: str = "",
    session: requests.Session | None = None,
    max_pages: int = SYNAP_MAX_PAGE_COUNT,
) -> SynapTextLayerResult:
    from .notice_file_view_backend import resolve_notice_viewer_url

    try:
        viewer_url = resolve_notice_viewer_url(
            bid_no=str(bid_no or "").strip(),
            bid_ord=str(bid_ord or "").strip() or "000",
            attachment_url=str(attachment_url or "").strip(),
            unty_atch_file_no=str(unty_atch_file_no or "").strip(),
        )
    except Exception:
        viewer_url = ""
    if not viewer_url:
        return SynapTextLayerResult()
    return download_synap_viewer_text(viewer_url, session=session, max_pages=max_pages)


def _looks_like_synap_page_xml(value: str) -> bool:
    text = str(value or "").strip()
    return text.startswith("<?xml") and "<page" in text and "</page>" in text


def _normalize_synap_block(value: str) -> str:
    text = str(value or "").replace("\xa0", " ")
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _normalize_synap_text(value: str) -> str:
    text = str(value or "").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
