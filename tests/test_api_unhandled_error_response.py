from __future__ import annotations

import logging

from starlette.datastructures import URL

from backend.api.support.app_http_support import handle_unhandled_error


class _RequestStub:
    method = "GET"
    url = URL("http://testserver/api/__test_unhandled_error_response")


def test_unhandled_api_error_logs_and_exposes_detail_when_enabled(monkeypatch, caplog) -> None:
    monkeypatch.setenv("LOCAL_APP_EXPOSE_INTERNAL_ERRORS", "1")

    with caplog.at_level(logging.ERROR, logger="backend.api.errors"):
        response = handle_unhandled_error(_RequestStub(), RuntimeError("desktop diagnostic failure"))

    assert response.status_code == 500
    assert response.body
    assert b"internal_server_error" in response.body
    assert b"desktop diagnostic failure" in response.body
    assert any("Unhandled API error" in record.message for record in caplog.records)
