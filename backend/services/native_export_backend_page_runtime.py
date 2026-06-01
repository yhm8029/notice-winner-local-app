from __future__ import annotations

from typing import Any
from typing import Callable


def build_page_fetch_urls(*, notice_url: str, base_url: str, search_url: str) -> list[str]:
    ordered: list[str] = []
    for value in [notice_url, base_url, search_url]:
        url = str(value or "").strip()
        if url and url not in ordered:
            ordered.append(url)
    return ordered


def fetch_page_documents(
    urls: list[str],
    *,
    fetch_page_text_fn,
    raise_if_stop_requested_fn,
    page_document_cls,
    should_stop: Callable[[], bool] | None = None,
) -> list[Any]:
    documents: list[Any] = []
    seen: set[str] = set()
    for value in urls:
        raise_if_stop_requested_fn(should_stop)
        url = str(value or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        title, text = fetch_page_text_fn(url)
        documents.append(page_document_cls(url=url, title=title, text=text))
    return documents


def pick_primary_document(documents: list[Any], *, page_document_cls) -> Any:
    if not documents:
        return page_document_cls(url="", title="", text="")
    ranked = sorted(
        documents,
        key=lambda item: (
            0 if item.text else 1,
            -(len(item.text or "")),
            -(len(item.title or "")),
        ),
    )
    return ranked[0]
