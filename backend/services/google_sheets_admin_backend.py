from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from urllib.parse import quote

import requests


@dataclass(frozen=True)
class GoogleSheetsAdminConfig:
    spreadsheet_id: str
    client_id: str
    client_secret: str
    refresh_token: str
    sync_interval_seconds: int
    snapshot_path: Path


_KNOWN_SHEET_DISPLAY_NAMES = {
    "설계list": "설계리스트",
    "발주예정": "발주예정",
    "lost": "LOST",
    "경상남도 영업list": "경상남도 영업 리스트",
    "대리점 리스트": "대리점 리스트",
}


def _parse_google_sheets_admin_sync_interval_seconds(raw_interval: str) -> int:
    try:
        parsed_interval = int(str(raw_interval or "300").strip() or "300")
    except (TypeError, ValueError):
        parsed_interval = 300
    return max(300, min(600, parsed_interval))


def _is_syncable_google_sheet(properties: dict) -> bool:
    return str(properties.get("sheetType") or "GRID").strip().upper() == "GRID"


def load_google_sheets_admin_config() -> GoogleSheetsAdminConfig | None:
    spreadsheet_id = str(os.getenv("GOOGLE_SHEETS_ADMIN_SPREADSHEET_ID") or "").strip()
    client_id = str(os.getenv("GOOGLE_SHEETS_ADMIN_CLIENT_ID") or "").strip()
    client_secret = str(os.getenv("GOOGLE_SHEETS_ADMIN_CLIENT_SECRET") or "").strip()
    refresh_token = str(os.getenv("GOOGLE_SHEETS_ADMIN_REFRESH_TOKEN") or "").strip()
    if not all((spreadsheet_id, client_id, client_secret, refresh_token)):
        return None
    raw_interval = str(os.getenv("GOOGLE_SHEETS_ADMIN_SYNC_INTERVAL_SECONDS") or "300").strip()
    sync_interval_seconds = _parse_google_sheets_admin_sync_interval_seconds(raw_interval)
    raw_path = str(os.getenv("GOOGLE_SHEETS_ADMIN_SNAPSHOT_PATH") or "").strip()
    snapshot_path = Path(raw_path or "output/google_sheets_admin_snapshot.json")
    return GoogleSheetsAdminConfig(
        spreadsheet_id=spreadsheet_id,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        sync_interval_seconds=sync_interval_seconds,
        snapshot_path=snapshot_path,
    )


def normalize_google_sheet_display_title(raw_title: str) -> str:
    stripped = re.sub(r"^\*+|\*+$", "", str(raw_title or "").strip())
    collapsed = re.sub(r"\s+", " ", stripped)
    key = collapsed.lower()
    return _KNOWN_SHEET_DISPLAY_NAMES.get(key, collapsed)


def build_google_sheet_admin_tab_key(sheet_id: int | str) -> str:
    return f"sheet-{int(str(sheet_id).strip() or '0')}"


def trim_google_sheet_values(values: list[list[str]]) -> tuple[list[str], list[list[str]]]:
    normalized = [[str(cell or "").strip() for cell in row] for row in values]
    first_content_index = next((idx for idx, row in enumerate(normalized) if any(row)), None)
    if first_content_index is None:
        return [], []
    materialized = normalized[first_content_index:]
    last_content_index = max(
        idx for idx, row in enumerate(materialized) if any(cell for cell in row)
    )
    content_rows = materialized[: last_content_index + 1]
    max_width = max(
        (max((idx for idx, cell in enumerate(row) if cell), default=-1) + 1 for row in content_rows),
        default=0,
    )
    trimmed = [
        row[:max_width] + [""] * max(0, max_width - len(row))
        if any(row)
        else [""] * max_width
        for row in content_rows
    ]
    headers = trimmed[0] if trimmed else []
    rows = trimmed[1:] if len(trimmed) > 1 else []
    return headers, rows


def _normalize_google_sheet_cell(cell: dict | None) -> dict[str, str]:
    source = dict(cell or {})
    text = str(source.get("formattedValue") or "").strip()
    hyperlink = str(source.get("hyperlink") or "").strip()
    if _is_safe_google_sheet_href(hyperlink):
        return {"text": text, "href": hyperlink}

    for run in source.get("chipRuns") or []:
        chip = dict((run or {}).get("chip") or {})
        rich_link_properties = dict(chip.get("richLinkProperties") or {})
        uri = str(rich_link_properties.get("uri") or "").strip()
        if _is_safe_google_sheet_href(uri):
            return {"text": text, "href": uri}
    return {"text": text, "href": ""}


def _is_safe_google_sheet_href(raw_href: str) -> bool:
    href = str(raw_href or "").strip()
    if not href:
        return False
    parsed = urlparse(href)
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def trim_google_sheet_cell_rows(
    values: list[list[dict]] | list[list[dict | None]] | None,
) -> tuple[list[dict[str, str]], list[list[dict[str, str]]]]:
    normalized = [
        [_normalize_google_sheet_cell(cell) for cell in (row or [])]
        for row in (values or [])
    ]
    first_content_index = next(
        (
            idx
            for idx, row in enumerate(normalized)
            if any(cell.get("text") or cell.get("href") for cell in row)
        ),
        None,
    )
    if first_content_index is None:
        return [], []
    materialized = normalized[first_content_index:]
    last_content_index = max(
        idx
        for idx, row in enumerate(materialized)
        if any(cell.get("text") or cell.get("href") for cell in row)
    )
    content_rows = materialized[: last_content_index + 1]
    max_width = max(
        (
            max(
                (
                    idx
                    for idx, cell in enumerate(row)
                    if cell.get("text") or cell.get("href")
                ),
                default=-1,
            )
            + 1
            for row in content_rows
        ),
        default=0,
    )
    empty_cell = {"text": "", "href": ""}
    trimmed = [
        row[:max_width] + [dict(empty_cell) for _ in range(max(0, max_width - len(row)))]
        if any(cell.get("text") or cell.get("href") for cell in row)
        else [dict(empty_cell) for _ in range(max_width)]
        for row in content_rows
    ]
    headers = trimmed[0] if trimmed else []
    rows = trimmed[1:] if len(trimmed) > 1 else []
    return headers, rows


def refresh_google_sheets_admin_access_token(
    *, config: GoogleSheetsAdminConfig, request_post_fn=requests.post
) -> str:
    response = request_post_fn(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "refresh_token": config.refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    access_token = str(payload.get("access_token") or "").strip()
    if not access_token:
        raise ValueError("Google Sheets admin OAuth refresh response missing access_token")
    return access_token


def fetch_google_sheets_admin_metadata(
    *, config: GoogleSheetsAdminConfig, access_token: str, request_get_fn=requests.get
) -> dict:
    response = request_get_fn(
        f"https://sheets.googleapis.com/v4/spreadsheets/{config.spreadsheet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={
            "fields": "properties(title),sheets(properties(sheetId,title,index,hidden,sheetType))"
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = dict(response.json() or {})
    payload["sheets"] = [
        item
        for item in (payload.get("sheets") or [])
        if _is_syncable_google_sheet(dict((item or {}).get("properties") or {}))
    ]
    return payload


def fetch_google_sheet_values(
    *,
    config: GoogleSheetsAdminConfig,
    access_token: str,
    sheet_title: str,
    request_get_fn=requests.get,
) -> list[list[str]]:
    escaped_title = str(sheet_title or "").replace("'", "''")
    encoded_range = quote(f"'{escaped_title}'", safe="")
    response = request_get_fn(
        f"https://sheets.googleapis.com/v4/spreadsheets/{config.spreadsheet_id}/values/{encoded_range}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"majorDimension": "ROWS", "valueRenderOption": "FORMATTED_VALUE"},
        timeout=15,
    )
    response.raise_for_status()
    return list(response.json().get("values") or [])


def fetch_google_sheet_grid_data(
    *,
    config: GoogleSheetsAdminConfig,
    access_token: str,
    sheet_title: str,
    request_get_fn=requests.get,
) -> list[list[dict]]:
    escaped_title = str(sheet_title or "").replace("'", "''")
    response = request_get_fn(
        f"https://sheets.googleapis.com/v4/spreadsheets/{config.spreadsheet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={
            "ranges": f"'{escaped_title}'",
            "includeGridData": "true",
            "fields": "sheets(data.rowData.values(formattedValue,hyperlink,chipRuns),properties(sheetId,title,index,hidden,sheetType))",
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = dict(response.json() or {})
    if isinstance(payload.get("values"), list):
        return [
            [
                {"formattedValue": str(cell or "").strip()}
                for cell in (row or [])
            ]
            for row in list(payload.get("values") or [])
        ]
    sheets = list(payload.get("sheets") or [])
    first_sheet = dict(sheets[0] or {}) if sheets else {}
    sheet_data = list(first_sheet.get("data") or [])
    first_data_block = dict(sheet_data[0] or {}) if sheet_data else {}
    row_data = list(first_data_block.get("rowData") or [])
    if row_data:
        return [list(dict(item or {}).get("values") or []) for item in row_data]

    fallback_values = fetch_google_sheet_values(
        config=config,
        access_token=access_token,
        sheet_title=sheet_title,
        request_get_fn=request_get_fn,
    )
    return [
        [{"formattedValue": str(cell or "").strip()} for cell in row]
        for row in fallback_values
    ]
