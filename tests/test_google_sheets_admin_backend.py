from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

import pytest

from backend.services.google_sheets_admin_backend import (
    GoogleSheetsAdminConfig,
    build_google_sheet_admin_tab_key,
    fetch_google_sheet_grid_data,
    fetch_google_sheet_values,
    fetch_google_sheets_admin_metadata,
    load_google_sheets_admin_config,
    normalize_google_sheet_display_title,
    refresh_google_sheets_admin_access_token,
    trim_google_sheet_cell_rows,
    trim_google_sheet_values,
)
from backend.services.google_sheets_admin_store import sync_google_sheets_admin_snapshot_once


def test_normalize_google_sheet_display_title_applies_known_mappings():
    assert normalize_google_sheet_display_title("lost") == "LOST"
    assert normalize_google_sheet_display_title("*발주예정*") == "발주예정"


def test_normalize_google_sheet_display_title_falls_back_to_normalized_title():
    assert normalize_google_sheet_display_title("  Unknown   Sheet  ") == "Unknown Sheet"


def test_build_google_sheet_admin_tab_key_uses_sheet_id():
    assert build_google_sheet_admin_tab_key(1664606955) == "sheet-1664606955"


def test_trim_google_sheet_values_uses_first_non_empty_row_as_headers():
    headers, rows = trim_google_sheet_values(
        [
            [],
            ["status", "project", ""],
            ["open", "library", ""],
            ["", "", ""],
        ]
    )

    assert headers == ["status", "project"]
    assert rows == [["open", "library"]]


def test_load_google_sheets_admin_config_returns_none_without_required_env(monkeypatch):
    for key in (
        "GOOGLE_SHEETS_ADMIN_SPREADSHEET_ID",
        "GOOGLE_SHEETS_ADMIN_CLIENT_ID",
        "GOOGLE_SHEETS_ADMIN_CLIENT_SECRET",
        "GOOGLE_SHEETS_ADMIN_REFRESH_TOKEN",
    ):
        monkeypatch.delenv(key, raising=False)

    assert load_google_sheets_admin_config() is None


def test_load_google_sheets_admin_config_uses_default_interval_and_snapshot_path_when_optional_env_is_missing_or_blank(
    monkeypatch,
):
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_SPREADSHEET_ID", "spreadsheet-1")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_CLIENT_ID", "client-1")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_CLIENT_SECRET", "secret-1")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_REFRESH_TOKEN", "refresh-1")

    monkeypatch.delenv("GOOGLE_SHEETS_ADMIN_SYNC_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("GOOGLE_SHEETS_ADMIN_SNAPSHOT_PATH", raising=False)

    config = load_google_sheets_admin_config()

    assert config == GoogleSheetsAdminConfig(
        spreadsheet_id="spreadsheet-1",
        client_id="client-1",
        client_secret="secret-1",
        refresh_token="refresh-1",
        sync_interval_seconds=300,
        snapshot_path=Path("output/google_sheets_admin_snapshot.json"),
    )

    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_SYNC_INTERVAL_SECONDS", "   ")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_SNAPSHOT_PATH", "   ")

    blank_config = load_google_sheets_admin_config()

    assert blank_config == GoogleSheetsAdminConfig(
        spreadsheet_id="spreadsheet-1",
        client_id="client-1",
        client_secret="secret-1",
        refresh_token="refresh-1",
        sync_interval_seconds=300,
        snapshot_path=Path("output/google_sheets_admin_snapshot.json"),
    )


def test_trim_google_sheet_values_preserves_interior_blank_rows():
    headers, rows = trim_google_sheet_values(
        [
            ["status", "project"],
            ["open", "library"],
            [],
            ["closed", "city hall"],
            [],
        ]
    )

    assert headers == ["status", "project"]
    assert rows == [["open", "library"], ["", ""], ["closed", "city hall"]]


def test_trim_google_sheet_cell_rows_preserves_chip_links_and_interior_blank_rows():
    headers, rows = trim_google_sheet_cell_rows(
        [
            [],
            [
                {"formattedValue": "문서"},
                {"formattedValue": "비고"},
            ],
            [
                {
                    "formattedValue": "설계서",
                    "chipRuns": [
                        {
                            "chip": {
                                "richLinkProperties": {
                                    "uri": "https://docs.google.com/document/d/design-doc/edit",
                                }
                            }
                        }
                    ],
                },
                {"formattedValue": "확인"},
            ],
            [],
            [
                {
                    "formattedValue": "시방서",
                    "hyperlink": "https://docs.google.com/document/d/spec-doc/edit",
                },
                {"formattedValue": ""},
            ],
            [],
        ]
    )

    assert headers == [
        {"text": "문서", "href": ""},
        {"text": "비고", "href": ""},
    ]
    assert rows == [
        [
            {
                "text": "설계서",
                "href": "https://docs.google.com/document/d/design-doc/edit",
            },
            {"text": "확인", "href": ""},
        ],
        [
            {"text": "", "href": ""},
            {"text": "", "href": ""},
        ],
        [
            {
                "text": "시방서",
                "href": "https://docs.google.com/document/d/spec-doc/edit",
            },
            {"text": "", "href": ""},
        ],
    ]


def test_trim_google_sheet_cell_rows_discards_unsafe_link_schemes():
    headers, rows = trim_google_sheet_cell_rows(
        [
            [{"formattedValue": "문서"}],
            [{"formattedValue": "실행", "hyperlink": "javascript:alert(1)"}],
            [
                {
                    "formattedValue": "정상 문서",
                    "chipRuns": [
                        {
                            "chip": {
                                "richLinkProperties": {
                                    "uri": "https://docs.google.com/document/d/safe-doc/edit",
                                }
                            }
                        }
                    ],
                }
            ],
        ]
    )

    assert headers == [{"text": "문서", "href": ""}]
    assert rows == [
        [{"text": "실행", "href": ""}],
        [{"text": "정상 문서", "href": "https://docs.google.com/document/d/safe-doc/edit"}],
    ]


def test_load_google_sheets_admin_config_clamps_interval_below_minimum(monkeypatch):
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_SPREADSHEET_ID", "spreadsheet-1")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_CLIENT_ID", "client-1")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_CLIENT_SECRET", "secret-1")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_REFRESH_TOKEN", "refresh-1")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_SYNC_INTERVAL_SECONDS", "299")

    config = load_google_sheets_admin_config()

    assert config is not None
    assert config.sync_interval_seconds == 300


def test_load_google_sheets_admin_config_clamps_interval_above_maximum(monkeypatch):
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_SPREADSHEET_ID", "spreadsheet-1")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_CLIENT_ID", "client-1")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_CLIENT_SECRET", "secret-1")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_REFRESH_TOKEN", "refresh-1")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_SYNC_INTERVAL_SECONDS", "601")

    config = load_google_sheets_admin_config()

    assert config is not None
    assert config.sync_interval_seconds == 600


def test_load_google_sheets_admin_config_falls_back_to_default_interval_for_invalid_values(monkeypatch):
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_SPREADSHEET_ID", "spreadsheet-1")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_CLIENT_ID", "client-1")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_CLIENT_SECRET", "secret-1")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_REFRESH_TOKEN", "refresh-1")
    monkeypatch.setenv("GOOGLE_SHEETS_ADMIN_SYNC_INTERVAL_SECONDS", "abc")

    config = load_google_sheets_admin_config()

    assert config is not None
    assert config.sync_interval_seconds == 300


def test_fetch_google_sheets_admin_metadata_requests_sheet_type(tmp_path):
    config = GoogleSheetsAdminConfig(
        spreadsheet_id="spreadsheet-123",
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        sync_interval_seconds=300,
        snapshot_path=tmp_path / "google-sheets-admin.json",
    )
    captured = {}

    class FakeResponse:
        def json(self):
            return {"properties": {"title": "@source"}, "sheets": []}

        def raise_for_status(self):
            return None

    def fake_get(url, headers=None, params=None, timeout=15):
        captured["url"] = url
        captured["headers"] = headers
        captured["params"] = params
        captured["timeout"] = timeout
        return FakeResponse()

    metadata = fetch_google_sheets_admin_metadata(
        config=config,
        access_token="access-token",
        request_get_fn=fake_get,
    )

    assert metadata == {"properties": {"title": "@source"}, "sheets": []}
    assert captured["url"].endswith("/v4/spreadsheets/spreadsheet-123")
    assert captured["headers"] == {"Authorization": "Bearer access-token"}
    assert captured["params"] == {
        "fields": "properties(title),sheets(properties(sheetId,title,index,hidden,sheetType))"
    }
    assert captured["timeout"] == 15


def test_sync_google_sheets_admin_snapshot_once_builds_tabs_from_google_payload(tmp_path):
    config = GoogleSheetsAdminConfig(
        spreadsheet_id="spreadsheet-123",
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        sync_interval_seconds=300,
        snapshot_path=tmp_path / "google-sheets-admin.json",
    )

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload
            self.status_code = 200
            self.text = "ok"

        def json(self):
            return self._payload

        def raise_for_status(self):
            return None

    def fake_post(url, data, timeout):
        assert "oauth2.googleapis.com/token" in url
        return FakeResponse({"access_token": "access-token", "expires_in": 3600})

    def fake_get(url, headers=None, params=None, timeout=15):
        if url.endswith("/v4/spreadsheets/spreadsheet-123"):
            if params == {
                "fields": "properties(title),sheets(properties(sheetId,title,index,hidden,sheetType))"
            }:
                return FakeResponse(
                    {
                        "properties": {"title": "@source"},
                        "sheets": [
                            {
                                "properties": {
                                    "sheetId": 1664606955,
                                    "title": "lost",
                                    "index": 0,
                                    "sheetType": "GRID",
                                }
                            },
                            {
                                "properties": {
                                    "sheetId": 7,
                                    "title": "Objects",
                                    "index": 1,
                                    "sheetType": "OBJECT",
                                }
                            },
                            {
                                "properties": {
                                    "sheetId": 42,
                                    "title": "Hidden",
                                    "index": 2,
                                    "hidden": True,
                                    "sheetType": "GRID",
                                }
                            },
                        ],
                    }
                )
            return FakeResponse(
                {
                    "sheets": [
                        {
                            "data": [
                                {
                                    "rowData": [
                                        {
                                            "values": [
                                                {"formattedValue": "문서"},
                                                {"formattedValue": "상태"},
                                            ]
                                        },
                                        {
                                            "values": [
                                                {
                                                    "formattedValue": "설계서",
                                                    "chipRuns": [
                                                        {
                                                            "chip": {
                                                                "richLinkProperties": {
                                                                    "uri": "https://docs.google.com/document/d/design-doc/edit"
                                                                }
                                                            }
                                                        }
                                                    ],
                                                },
                                                {"formattedValue": "open"},
                                            ]
                                        },
                                    ]
                                }
                            ]
                        }
                    ]
                }
            )
        if unquote(url.split("/values/", 1)[1]) == "'Objects'":
            pytest.fail("Visible non-GRID sheets should be skipped during snapshot sync")
        return FakeResponse({"values": [["status", "project"], ["open", "library"]]})

    snapshot = sync_google_sheets_admin_snapshot_once(
        config=config,
        request_post_fn=fake_post,
        request_get_fn=fake_get,
        now_fn=lambda tz=timezone.utc: datetime(2026, 4, 18, tzinfo=tz),
    )

    assert snapshot["source_title"] == "@source"
    assert [tab["display_title"] for tab in snapshot["tabs"]] == ["LOST"]
    assert snapshot["sheets"]["sheet-1664606955"]["headers"] == ["문서", "상태"]
    assert snapshot["sheets"]["sheet-1664606955"]["rows"] == [["설계서", "open"]]
    assert snapshot["sheets"]["sheet-1664606955"]["row_cells"][0][0] == {
        "text": "설계서",
        "href": "https://docs.google.com/document/d/design-doc/edit",
    }


def test_fetch_google_sheet_values_quotes_and_escapes_user_editable_sheet_titles(tmp_path):
    config = GoogleSheetsAdminConfig(
        spreadsheet_id="spreadsheet-123",
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        sync_interval_seconds=300,
        snapshot_path=tmp_path / "google-sheets-admin.json",
    )
    captured = {}

    class FakeResponse:
        def json(self):
            return {"values": [["status"]]}

        def raise_for_status(self):
            return None

    def fake_get(url, headers=None, params=None, timeout=15):
        captured["url"] = url
        captured["headers"] = headers
        captured["params"] = params
        captured["timeout"] = timeout
        return FakeResponse()

    values = fetch_google_sheet_values(
        config=config,
        access_token="access-token",
        sheet_title="Ops/QA ? # \"A\" O'Brien",
        request_get_fn=fake_get,
    )

    assert values == [["status"]]
    assert unquote(captured["url"].split("/values/", 1)[1]) == "'Ops/QA ? # \"A\" O''Brien'"
    assert captured["headers"] == {"Authorization": "Bearer access-token"}
    assert captured["params"] == {
        "majorDimension": "ROWS",
        "valueRenderOption": "FORMATTED_VALUE",
    }
    assert captured["timeout"] == 15


def test_fetch_google_sheet_grid_data_quotes_and_requests_grid_cell_fields(tmp_path):
    config = GoogleSheetsAdminConfig(
        spreadsheet_id="spreadsheet-123",
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        sync_interval_seconds=300,
        snapshot_path=tmp_path / "google-sheets-admin.json",
    )
    captured = {}

    class FakeResponse:
        def json(self):
            return {
                "sheets": [
                    {
                        "data": [
                            {
                                "rowData": [
                                    {
                                        "values": [
                                            {
                                                "formattedValue": "설계서",
                                                "hyperlink": "https://docs.google.com/document/d/design-doc/edit",
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }

        def raise_for_status(self):
            return None

    def fake_get(url, headers=None, params=None, timeout=15):
        captured["url"] = url
        captured["headers"] = headers
        captured["params"] = params
        captured["timeout"] = timeout
        return FakeResponse()

    rows = fetch_google_sheet_grid_data(
        config=config,
        access_token="access-token",
        sheet_title="Ops/QA ? # \"A\" O'Brien",
        request_get_fn=fake_get,
    )

    assert rows == [
        [
            {
                "formattedValue": "설계서",
                "hyperlink": "https://docs.google.com/document/d/design-doc/edit",
            }
        ]
    ]
    assert captured["url"].endswith("/v4/spreadsheets/spreadsheet-123")
    assert captured["headers"] == {"Authorization": "Bearer access-token"}
    assert captured["params"] == {
        "ranges": "'Ops/QA ? # \"A\" O''Brien'",
        "includeGridData": "true",
        "fields": "sheets(data.rowData.values(formattedValue,hyperlink,chipRuns),properties(sheetId,title,index,hidden,sheetType))",
    }
    assert captured["timeout"] == 15


def test_refresh_google_sheets_admin_access_token_fails_fast_without_access_token(tmp_path):
    config = GoogleSheetsAdminConfig(
        spreadsheet_id="spreadsheet-123",
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        sync_interval_seconds=300,
        snapshot_path=tmp_path / "google-sheets-admin.json",
    )

    class FakeResponse:
        def json(self):
            return {"expires_in": 3600}

        def raise_for_status(self):
            return None

    with pytest.raises(ValueError, match="access_token"):
        refresh_google_sheets_admin_access_token(
            config=config,
            request_post_fn=lambda url, data, timeout: FakeResponse(),
        )
