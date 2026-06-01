from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import html
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import time
from xml.etree import ElementTree as ET
import re
import zipfile
import zlib

import requests

try:
    import olefile
except Exception:  # pragma: no cover - optional dependency
    olefile = None

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency
    PdfReader = None

try:
    import fitz
except Exception:  # pragma: no cover - optional dependency
    fitz = None

ATTACHMENT_TIMEOUT_SEC = 30
ATTACHMENT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
ZIP_MEMBER_LIMIT = 6
ZIP_MEMBER_MAX_BYTES = 20 * 1024 * 1024
POPPLER_PDFTOTEXT = Path(r"C:\poppler\Library\bin\pdftotext.exe")
HWP5TXT_CANDIDATES = (
    "hwp5txt.exe",
    str(Path.home() / "AppData" / "Local" / "Python" / "pythoncore-3.14-64" / "Scripts" / "hwp5txt.exe"),
)
HWP5HTML_CANDIDATES = (
    "hwp5html.exe",
    str(Path.home() / "AppData" / "Local" / "Python" / "pythoncore-3.14-64" / "Scripts" / "hwp5html.exe"),
)
RESULT_HINTS = (
    "??",
    "???",
    "???",
    "??",
    "?????",
    "??????",
    "??",
    "???",
    "?????",
)
AREA_HINTS = (
    "???",
    "??",
    "?",
    "m?",
    "m2",
)
COST_HINTS = (
    "???",
    "????",
    "????",
    "????",
    "????",
    "???",
)


@dataclass(frozen=True)
class AttachmentTextLoadResult:
    text: str = ""
    download_ms: int = 0
    parse_ms: int = 0


def download_attachment_text(
    *,
    url: str,
    file_name: str = "",
    session: requests.Session | None = None,
) -> str:
    return download_attachment_text_with_timing(
        url=url,
        file_name=file_name,
        session=session,
    ).text


def download_attachment_text_with_timing(
    *,
    url: str,
    file_name: str = "",
    session: requests.Session | None = None,
) -> AttachmentTextLoadResult:
    target = str(url or "").strip()
    if not target:
        return AttachmentTextLoadResult()
    getter = session.get if session is not None else requests.get
    try:
        download_started = time.perf_counter()
        response = getter(
            target,
            timeout=ATTACHMENT_TIMEOUT_SEC,
            headers={"User-Agent": ATTACHMENT_USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7"},
        )
        response.raise_for_status()
        download_ms = int(round((time.perf_counter() - download_started) * 1000))
    except Exception:
        return AttachmentTextLoadResult()
    parse_started = time.perf_counter()
    text = extract_attachment_text(
        data=getattr(response, "content", b"") or b"",
        file_name=file_name,
        content_type=str(getattr(response, "headers", {}).get("content-type") or ""),
    )
    parse_ms = int(round((time.perf_counter() - parse_started) * 1000))
    return AttachmentTextLoadResult(text=text, download_ms=download_ms, parse_ms=parse_ms)


def extract_attachment_text(*, data: bytes, file_name: str = "", content_type: str = "") -> str:
    return _extract_attachment_text_internal(data=data, file_name=file_name, content_type=content_type, zip_depth=0)


def _extract_attachment_text_internal(
    *,
    data: bytes,
    file_name: str = "",
    content_type: str = "",
    zip_depth: int,
) -> str:
    suffix = _infer_suffix(file_name=file_name, content_type=content_type, data=data)
    if suffix == ".hwpx":
        return _extract_hwpx_text(data)
    if suffix == ".hwp":
        return _extract_hwp_text(data)
    if suffix == ".pdf":
        return _extract_pdf_text(data)
    if suffix == ".zip":
        return _extract_zip_text(data, zip_depth=zip_depth)
    return ""


def _infer_suffix(*, file_name: str, content_type: str, data: bytes) -> str:
    name_suffix = Path(str(file_name or "").strip()).suffix.lower()
    if name_suffix:
        return name_suffix
    lowered_type = str(content_type or "").lower()
    if "pdf" in lowered_type:
        return ".pdf"
    if "zip" in lowered_type:
        return ".zip"
    if data.startswith(b"PK\x03\x04"):
        return ".hwpx" if _looks_like_hwpx_zip(data) else ".zip"
    if data.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return ".hwp"
    return ""


def _looks_like_hwpx_zip(data: bytes) -> bool:
    try:
        with zipfile.ZipFile(BytesIO(data)) as zf:
            names = zf.namelist()
    except Exception:
        return False
    if "Preview/PrvText.txt" in names:
        return True
    return any(name.startswith("Contents/section") and name.endswith(".xml") for name in names)


def _extract_hwpx_text(data: bytes) -> str:
    try:
        with zipfile.ZipFile(BytesIO(data)) as zf:
            chunks: list[str] = []
            if "Preview/PrvText.txt" in zf.namelist():
                chunks.append(_decode_text_bytes(zf.read("Preview/PrvText.txt")))
            section_names = sorted(name for name in zf.namelist() if name.startswith("Contents/section") and name.endswith(".xml"))
            for name in section_names[:12]:
                chunks.append(_extract_hwpx_section_text(zf.read(name)))
            return _normalize_text("\n".join(chunk for chunk in chunks if chunk))
    except Exception:
        return ""


def _extract_zip_text(data: bytes, *, zip_depth: int) -> str:
    if zip_depth >= 1:
        return ""
    try:
        with zipfile.ZipFile(BytesIO(data)) as zf:
            candidates: list[tuple[int, str]] = []
            for info in zf.infolist():
                if info.is_dir():
                    continue
                member_name = str(info.filename or "").replace("\\", "/").strip()
                if not member_name or member_name.startswith("__MACOSX/"):
                    continue
                if info.file_size <= 0 or info.file_size > ZIP_MEMBER_MAX_BYTES:
                    continue
                suffix = Path(member_name).suffix.lower()
                if suffix not in {".hwp", ".hwpx", ".pdf", ".txt"}:
                    continue
                candidates.append((_zip_member_score(member_name), member_name))
            candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
            chunks: list[str] = []
            for _, member_name in candidates[:ZIP_MEMBER_LIMIT]:
                try:
                    member_data = zf.read(member_name)
                except Exception:
                    continue
                member_text = _extract_attachment_text_internal(
                    data=member_data,
                    file_name=member_name,
                    content_type="",
                    zip_depth=zip_depth + 1,
                )
                if not member_text and Path(member_name).suffix.lower() == ".txt":
                    member_text = _decode_text_bytes(member_data)
                member_text = _normalize_text(member_text)
                if not member_text:
                    continue
                chunks.append("\n".join(part for part in [Path(member_name).name, member_text] if part).strip())
            return _normalize_text("\n\n".join(chunks))
    except Exception:
        return ""


def _zip_member_score(member_name: str) -> int:
    value = Path(str(member_name or "").strip()).name
    lowered = value.lower()
    score = 0
    if "공고" in value:
        score += 10
    if "지침" in value or "과업" in value:
        score += 6
    if "제안" in value:
        score += 3
    if lowered.endswith(".hwpx"):
        score += 5
    elif lowered.endswith(".pdf"):
        score += 4
    elif lowered.endswith(".hwp"):
        score += 2
    elif lowered.endswith(".txt"):
        score += 1
    return score


def _extract_hwpx_section_text(data: bytes) -> str:
    try:
        root = ET.fromstring(data)
    except Exception:
        return ""
    texts: list[str] = []
    for node in root.iter():
        text = str(node.text or "").strip()
        if text:
            texts.append(text)
    return "\n".join(texts)


def _extract_hwp_text(data: bytes) -> str:
    txt = _normalize_text(_extract_hwp_via_hwp5txt(data))
    html = _normalize_text(_extract_hwp_via_hwp5html(data))
    merged_parts: list[str] = []
    if txt:
        merged_parts.append(txt)
    if html and html != txt:
        merged_parts.append(html)
    merged = _normalize_text("\n\n".join(merged_parts))
    if _is_good_enough_hwp_text(merged):
        return merged
    if _is_good_enough_hwp_text(txt):
        return txt

    ole = _normalize_text(_extract_hwp_via_ole(data))
    if _is_good_enough_hwp_text(ole):
        return ole

    raw = _normalize_text(_extract_hwp_via_raw_decode(data))
    return _normalize_text("\n\n".join(part for part in [merged, ole, raw] if part))


def _decode_hwp_stream(data: bytes, *, stream_name: str) -> str:
    if stream_name.startswith("BodyText/"):
        body_text = _extract_hwp_body_text_section(data)
        if body_text:
            return body_text
    encodings = ("utf-16", "utf-16le", "cp949", "utf-8")
    for encoding in encodings:
        try:
            decoded = data.decode(encoding)
        except Exception:
            continue
        cleaned = _normalize_text(decoded)
        if cleaned:
            return cleaned
    if stream_name.startswith("BodyText/"):
        return ""
    return ""


def _extract_hwp_body_text_section(data: bytes) -> str:
    payload = _maybe_decompress_hwp_section(data)
    if not payload:
        return ""
    parts: list[str] = []
    offset = 0
    while offset + 4 <= len(payload):
        header = struct.unpack_from("<I", payload, offset)[0]
        offset += 4
        tag_id = header & 0x3FF
        size = (header >> 20) & 0xFFF
        if size == 0xFFF:
            if offset + 4 > len(payload):
                break
            size = struct.unpack_from("<I", payload, offset)[0]
            offset += 4
        if size < 0 or offset + size > len(payload):
            break
        record = payload[offset : offset + size]
        offset += size
        if tag_id != 67:
            continue
        try:
            text = record.decode("utf-16le", errors="ignore")
        except Exception:
            continue
        cleaned = _clean_hwp_record_text(text)
        if cleaned:
            parts.append(cleaned)
    return _normalize_text("\n".join(parts))


def _maybe_decompress_hwp_section(data: bytes) -> bytes:
    raw = bytes(data or b"")
    if not raw:
        return b""
    for wbits in (-15, 15):
        try:
            inflated = zlib.decompress(raw, wbits)
        except Exception:
            continue
        if inflated:
            return inflated
    return raw


def _clean_hwp_record_text(text: str) -> str:
    value = str(text or "")
    value = value.replace("\x00", " ")
    value = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", " ", value)
    value = re.sub(r"[\ue000-\uf8ff]", " ", value)
    return _normalize_text(value)


def _extract_pdf_text(data: bytes) -> str:
    cli_text = _extract_pdf_text_via_cli(data)
    if cli_text:
        return cli_text
    if fitz is not None:
        try:
            pdf = fitz.open(stream=data, filetype="pdf")
        except Exception:
            pdf = None
        if pdf is not None:
            try:
                chunks: list[str] = []
                for page in pdf[:20]:
                    chunks.append(page.get_text("text") or "")
                text = _normalize_text("\n".join(chunks))
                if text:
                    return text
            finally:
                pdf.close()
    if PdfReader is None:
        return ""
    try:
        reader = PdfReader(BytesIO(data))
    except Exception:
        return ""
    chunks: list[str] = []
    for page in reader.pages[:20]:
        try:
            chunks.append(page.extract_text() or "")
        except Exception:
            continue
    return _normalize_text("\n".join(chunks))


def _decode_text_bytes(data: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "utf-16le", "cp949"):
        try:
            return data.decode(encoding)
        except Exception:
            continue
    return data.decode("utf-8", errors="ignore")


def _normalize_text(value: str) -> str:
    text = str(value or "").replace("\x00", " ")
    text = text.replace("\r", "\n")
    text = re.sub(r"[<>]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _tool_path(candidates: tuple[str, ...]) -> str:
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


def _extract_hwp_via_hwp5txt(data: bytes) -> str:
    tool = _tool_path(HWP5TXT_CANDIDATES)
    if not tool:
        return ""
    try:
        with tempfile.TemporaryDirectory(prefix="hwp5txt_") as temp_dir:
            workdir = Path(temp_dir)
            input_path = workdir / "input.hwp"
            input_path.write_bytes(data)
            proc = subprocess.run(
                [tool, str(input_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=120,
                check=False,
            )
            return _normalize_text(proc.stdout or "")
    except Exception:
        return ""


def _extract_hwp_via_hwp5html(data: bytes) -> str:
    tool = _tool_path(HWP5HTML_CANDIDATES)
    if not tool:
        return ""
    try:
        with tempfile.TemporaryDirectory(prefix="hwp5html_") as temp_dir:
            workdir = Path(temp_dir)
            input_path = workdir / "input.hwp"
            output_path = workdir / "output.html"
            input_path.write_bytes(data)
            proc = subprocess.run(
                [tool, "--html", "--output", str(output_path), str(input_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=180,
                check=False,
            )
            if proc.returncode != 0 or not output_path.exists():
                return ""
            html_text = output_path.read_text(encoding="utf-8", errors="ignore")
            html_text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html_text)
            html_text = re.sub(r"(?is)<[^>]+>", " ", html_text)
            html_text = html.unescape(html_text)
            return _normalize_text(html_text)
    except Exception:
        return ""


def _extract_hwp_via_ole(data: bytes) -> str:
    if olefile is None:
        return ""
    try:
        ole = olefile.OleFileIO(BytesIO(data))
    except Exception:
        return ""
    try:
        body_streams: list[str] = []
        for entry in ole.listdir(streams=True, storages=False):
            stream_name = "/".join(str(part) for part in entry)
            if stream_name.startswith("BodyText/Section"):
                body_streams.append(stream_name)
        def _section_sort_key(value: str) -> int:
            match = re.search(r"Section(\d+)$", value)
            return int(match.group(1)) if match else 0

        body_streams.sort(key=_section_sort_key)

        body_parts: list[str] = []
        for stream_name in body_streams:
            raw = ole.openstream(stream_name).read()
            text = _decode_hwp_stream(raw, stream_name=stream_name)
            if text:
                body_parts.append(text)
        body_text = _normalize_text("\n\n".join(body_parts))
        if body_text:
            return body_text

        if ole.exists("PrvText"):
            raw = ole.openstream("PrvText").read()
            text = _decode_hwp_stream(raw, stream_name="PrvText")
            if text:
                return _normalize_text(text)

        for stream_name in ("BodyText/Section0",):
            if not ole.exists(stream_name):
                continue
            raw = ole.openstream(stream_name).read()
            text = _decode_hwp_stream(raw, stream_name=stream_name)
            if text:
                return _normalize_text(text)
    except Exception:
        return ""
    finally:
        try:
            ole.close()
        except Exception:
            pass
    return ""


def _extract_hwp_via_raw_decode(data: bytes) -> str:
    for encoding in ("utf-16", "utf-16le", "cp949", "utf-8", "latin1"):
        try:
            decoded = data.decode(encoding, errors="ignore")
        except Exception:
            continue
        cleaned = _normalize_text(decoded)
        if _is_useful_hwp_text(cleaned):
            return cleaned
    return ""


def _extract_pdf_text_via_cli(data: bytes) -> str:
    if not POPPLER_PDFTOTEXT.exists():
        return ""
    try:
        with tempfile.TemporaryDirectory(prefix="pdftotext_") as temp_dir:
            workdir = Path(temp_dir)
            input_path = workdir / "input.pdf"
            output_path = workdir / "output.txt"
            input_path.write_bytes(data)
            proc = subprocess.run(
                [str(POPPLER_PDFTOTEXT), "-layout", str(input_path), str(output_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=120,
                check=False,
            )
            if proc.returncode != 0 or not output_path.exists():
                return ""
            return _normalize_text(output_path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return ""


def _append_useful_hwp_part(parts: list[str], text: str) -> None:
    cleaned = _normalize_text(text)
    if not _is_useful_hwp_text(cleaned):
        return
    if cleaned not in parts:
        parts.append(cleaned)


def _is_useful_hwp_text(text: str) -> bool:
    value = str(text or "").strip()
    if len(value) < 20:
        return False
    printable = len(re.findall(r"[가-힣A-Za-z0-9\s\.,:;_\-()/%㎡]", value))
    return printable / max(len(value), 1) >= 0.15


def _is_good_enough_hwp_text(text: str) -> bool:
    value = _normalize_text(text)
    if not value:
        return False
    if len(value) >= 600:
        return True
    if len(value) < 200:
        return False
    category_hits = 0
    if any(hint in value for hint in RESULT_HINTS):
        category_hits += 1
    if any(hint in value for hint in AREA_HINTS):
        category_hits += 1
    if any(hint in value for hint in COST_HINTS):
        category_hits += 1
    return category_hits >= 2


def _contains_area_hint(text: str) -> bool:
    return bool(re.search(r"(연\s*면\s*적|건축\s*연\s*면\s*적|대\s*지\s*면\s*적|㎡|m2|m²|제곱미터)", str(text or ""), re.I))
