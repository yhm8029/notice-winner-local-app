from __future__ import annotations

import html
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any
from urllib.parse import parse_qs
from urllib.parse import urlparse

import requests

from .native_export_backend import _collect_attachment_documents
from .seed_collect import collect_seed_rows_with_params

ATTACHMENT_FILE_TIMEOUT_SEC = 30
G2B_TECH_ANNOUNCE_DETAIL_URL = "https://www.g2b.go.kr/pn/pnp/pnpe/TechBidPbac/selectTechAnncMngV.do"
G2B_ATTACHMENT_DOC_VIEWER_URL = "https://www.g2b.go.kr/fs/fsc/fsca/atchFileDocViewer.do"
ATTACHMENT_FILE_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
HWP5HTML_CANDIDATES = (
    "hwp5html.exe",
    str(Path.home() / "AppData" / "Local" / "Programs" / "Python" / "Python313" / "Scripts" / "hwp5html.exe"),
    str(Path.home() / "AppData" / "Local" / "Python" / "pythoncore-3.14-64" / "Scripts" / "hwp5html.exe"),
)


def load_notice_seed_row_by_bid(*, bid_no: str, bid_ord: str = "000") -> dict[str, str] | None:
    bid_no_text = str(bid_no or "").strip().upper()
    if not bid_no_text:
        return None
    try:
        output = collect_seed_rows_with_params(
            params={
                "start_date": "20230101",
                "end_date": "20271231",
                "bid_no": bid_no_text,
                "notice_title": "",
                "demand_org": "",
                "rows_per_page": 10,
                "max_pages": 1,
                "api_scope": "all",
            }
        )
    except Exception:
        return None
    rows = list(getattr(output, "rows", []) or [])
    target_bid_ord = _normalize_bid_ord(bid_ord)
    matched_row = next(
        (
            row
            for row in rows
            if str((row or {}).get("bid_no") or "").strip().upper() == bid_no_text
            and _normalize_bid_ord((row or {}).get("bid_ord") or "000") == target_bid_ord
        ),
        None,
    )
    if matched_row is None and rows:
        matched_row = rows[0]
    if matched_row is None:
        return None
    return {key: str(value or "") for key, value in dict(matched_row).items()}


def select_primary_notice_attachment(seed_row: dict[str, str] | None) -> dict[str, str]:
    row = dict(seed_row or {})
    if not row:
        return {}
    documents = _collect_attachment_documents(
        row,
        spec_doc_url=str(row.get("spec_doc_url") or "").strip(),
        spec_doc_file_name=str(row.get("spec_doc_file_name") or "").strip(),
    )
    if not documents:
        return {}
    primary = documents[0]
    return {
        "url": str(primary.url or "").strip(),
        "file_name": str(primary.file_name or "").strip(),
    }


def download_notice_attachment(*, url: str) -> tuple[bytes, str]:
    target = str(url or "").strip()
    if not target:
        return b"", ""
    response = requests.get(
        target,
        timeout=ATTACHMENT_FILE_TIMEOUT_SEC,
        headers={"User-Agent": ATTACHMENT_FILE_USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7"},
    )
    response.raise_for_status()
    return response.content, str(response.headers.get("content-type") or "").strip().lower()


def resolve_notice_viewer_url(
    *,
    bid_no: str,
    bid_ord: str,
    attachment_url: str,
    unty_atch_file_no: str = "",
) -> str:
    normalized_bid_no = str(bid_no or "").strip().upper()
    normalized_bid_ord = str(bid_ord or "").strip() or "000"
    file_seq = _extract_attachment_file_seq(attachment_url)
    if not normalized_bid_no or not file_seq:
        return ""
    group_no = str(unty_atch_file_no or "").strip() or _fetch_notice_attachment_group_no(
        bid_no=normalized_bid_no,
        bid_ord=normalized_bid_ord,
    )
    if not group_no:
        return ""
    response = requests.post(
        G2B_ATTACHMENT_DOC_VIEWER_URL,
        json={
            "dlDownAtflGrpDetlM": {
                "untyAtchFileNo": group_no,
                "atchFileSqno": int(file_seq),
            }
        },
        timeout=ATTACHMENT_FILE_TIMEOUT_SEC,
        headers={"User-Agent": ATTACHMENT_FILE_USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7"},
    )
    response.raise_for_status()
    payload = response.json()
    return str((payload.get("result") or {}).get("viewUrlPath") or "").strip()


def infer_notice_attachment_suffix(*, file_name: str, content_type: str = "", data: bytes = b"") -> str:
    suffix = Path(str(file_name or "").strip()).suffix.lower()
    if suffix:
        return suffix
    lowered_type = str(content_type or "").lower()
    if "pdf" in lowered_type:
        return ".pdf"
    if data.startswith(b"PK\x03\x04"):
        return ".hwpx"
    if data.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return ".hwp"
    if lowered_type.startswith("image/"):
        return "." + lowered_type.split("/", 1)[1]
    return ""


def render_hwp_notice_html(*, data: bytes, title: str = "") -> str | None:
    tool = _resolve_tool_path(HWP5HTML_CANDIDATES)
    if not tool:
        return None
    try:
        with tempfile.TemporaryDirectory(prefix="notice_hwp_html_") as temp_dir:
            workdir = Path(temp_dir)
            input_path = workdir / "input.hwp"
            output_path = workdir / "output.html"
            css_path = workdir / "styles.css"
            input_path.write_bytes(data)
            html_proc = subprocess.run(
                [tool, "--html", "--output", str(output_path), str(input_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=180,
                check=False,
            )
            css_proc = subprocess.run(
                [tool, "--css", "--output", str(css_path), str(input_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=180,
                check=False,
            )
            if html_proc.returncode != 0 or not output_path.exists():
                return None
            output_html = output_path.read_text(encoding="utf-8", errors="ignore")
            inline_css = ""
            if css_proc.returncode == 0 and css_path.exists():
                inline_css = css_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    if not output_html.strip():
        return None
    if inline_css.strip():
        style_tag = f"<style type=\"text/css\">\n{inline_css}\n</style>"
        output_html = re.sub(r'(?i)<link[^>]+href="styles\.css"[^>]*>', style_tag, output_html, count=1)
    else:
        output_html = re.sub(r'(?i)<link[^>]+href="styles\.css"[^>]*>', "", output_html)
    if title:
        safe_title = html.escape(str(title or "").strip())
        if re.search(r"(?is)<title>.*?</title>", output_html):
            output_html = re.sub(r"(?is)<title>.*?</title>", f"<title>{safe_title}</title>", output_html, count=1)
        else:
            output_html = output_html.replace("</head>", f"<title>{safe_title}</title></head>", 1)
    if "<meta name=\"viewport\"" not in output_html.lower():
        output_html = output_html.replace(
            "</head>",
            "\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n</head>",
            1,
        )
    return output_html


def build_notice_file_fallback_html(*, title: str, message: str, file_url: str = "") -> str:
    safe_title = html.escape(str(title or "공고문").strip() or "공고문")
    safe_message = html.escape(str(message or "공고문을 표시하지 못했습니다.").strip() or "공고문을 표시하지 못했습니다.")
    link_markup = (
        f'<p><a href="{html.escape(file_url)}" target="_blank" rel="noreferrer">원본 파일 열기</a></p>'
        if str(file_url or "").strip()
        else ""
    )
    return f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{safe_title}</title>
    <style>
      body {{
        margin: 0;
        padding: 32px;
        background: #f8f2ea;
        color: #2f241d;
        font: 16px/1.6 "Malgun Gothic", sans-serif;
      }}
      main {{
        max-width: 960px;
        margin: 0 auto;
        padding: 24px 28px;
        border: 1px solid rgba(131, 101, 70, 0.18);
        border-radius: 20px;
        background: rgba(255, 251, 247, 0.94);
      }}
      a {{
        color: #aa4519;
      }}
    </style>
  </head>
  <body>
    <main>
      <h1>{safe_title}</h1>
      <p>{safe_message}</p>
      {link_markup}
    </main>
  </body>
</html>"""


def _resolve_tool_path(candidates: tuple[str, ...]) -> str:
    for candidate in candidates:
        value = str(candidate or "").strip()
        if not value:
            continue
        if os.path.isabs(value) and Path(value).exists():
            return value
        resolved = shutil.which(value)
        if resolved:
            return resolved
    return ""


def _extract_attachment_file_seq(url: str) -> str:
    target = str(url or "").strip()
    if not target:
        return ""
    parsed = urlparse(target)
    query = parse_qs(parsed.query)
    candidates = query.get("fileSeq") or query.get("atchFileSqno") or []
    for candidate in candidates:
        digits = re.sub(r"[^0-9]", "", str(candidate or ""))
        if digits:
            return digits
    return ""


def _fetch_notice_attachment_group_no(*, bid_no: str, bid_ord: str) -> str:
    response = requests.post(
        G2B_TECH_ANNOUNCE_DETAIL_URL,
        json={"dmItemMap": {"bidPbancNo": str(bid_no or "").strip(), "bidPbancOrd": str(bid_ord or "").strip() or "000"}},
        timeout=ATTACHMENT_FILE_TIMEOUT_SEC,
        headers={"User-Agent": ATTACHMENT_FILE_USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7"},
    )
    response.raise_for_status()
    payload = response.json()
    return str((payload.get("dmItemMap") or {}).get("itemPbancUntyAtchFileNo") or "").strip()


def _normalize_bid_ord(value: object) -> str:
    raw = re.sub(r"[^0-9]", "", str(value or "").strip())
    if not raw:
        return "000"
    return f"{int(raw):03d}"
