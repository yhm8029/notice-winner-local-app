from __future__ import annotations

import unittest
from unittest.mock import Mock
from unittest.mock import patch

import requests

from backend.repositories.supabase_http import request_json


class _RepositoryError(Exception):
    pass


class SupabaseHttpRetryTests(unittest.TestCase):
    def test_request_json_logs_slow_supabase_call(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.status_code = 200
        response.text = '[{"id": "run-1"}]'
        response.headers = {"Content-Range": "0-0/1"}
        response.json.return_value = [{"id": "run-1"}]

        with patch("backend.repositories.supabase_http.requests.request", return_value=response), patch(
            "backend.repositories.supabase_http.time.perf_counter",
            side_effect=[10.0, 10.5],
        ), patch("backend.repositories.supabase_http.SUPABASE_PERF_LOGGER.warning") as warning_mock:
            payload, headers = request_json(
                rest_url="https://example.supabase.co/rest/v1",
                api_key="secret",
                timeout_seconds=10.0,
                method="GET",
                path="/pipeline_runs",
                error_cls=_RepositoryError,
            )

        self.assertEqual(payload, [{"id": "run-1"}])
        self.assertEqual(headers, {"Content-Range": "0-0/1"})
        warning_mock.assert_called_once()

    def test_request_json_retries_get_timeout_and_succeeds(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.text = '[{"id": "run-1"}]'
        response.headers = {"Content-Range": "0-0/1"}
        response.json.return_value = [{"id": "run-1"}]

        with patch("backend.repositories.supabase_http.requests.request") as request_mock, patch(
            "backend.repositories.supabase_http.time.sleep"
        ) as sleep_mock:
            request_mock.side_effect = [requests.ConnectTimeout("timed out"), response]

            payload, headers = request_json(
                rest_url="https://example.supabase.co/rest/v1",
                api_key="secret",
                timeout_seconds=10.0,
                method="GET",
                path="/pipeline_runs",
                error_cls=_RepositoryError,
            )

        self.assertEqual(payload, [{"id": "run-1"}])
        self.assertEqual(headers, {"Content-Range": "0-0/1"})
        self.assertEqual(request_mock.call_count, 2)
        sleep_mock.assert_called_once_with(0.5)

    def test_request_json_retries_patch_connection_error_until_exhausted(self) -> None:
        error = requests.ConnectionError("network down")

        with patch("backend.repositories.supabase_http.requests.request", side_effect=error) as request_mock, patch(
            "backend.repositories.supabase_http.time.sleep"
        ) as sleep_mock:
            with self.assertRaisesRegex(_RepositoryError, "Supabase request failed: network down"):
                request_json(
                    rest_url="https://example.supabase.co/rest/v1",
                    api_key="secret",
                    timeout_seconds=10.0,
                    method="PATCH",
                    path="/pipeline_runs",
                    error_cls=_RepositoryError,
                )

        self.assertEqual(request_mock.call_count, 3)
        self.assertEqual(sleep_mock.call_count, 2)

    def test_request_json_does_not_retry_post_timeout(self) -> None:
        error = requests.ConnectTimeout("timed out")

        with patch("backend.repositories.supabase_http.requests.request", side_effect=error) as request_mock, patch(
            "backend.repositories.supabase_http.time.sleep"
        ) as sleep_mock:
            with self.assertRaisesRegex(_RepositoryError, "Supabase request failed: timed out"):
                request_json(
                    rest_url="https://example.supabase.co/rest/v1",
                    api_key="secret",
                    timeout_seconds=10.0,
                    method="POST",
                    path="/pipeline_runs",
                    error_cls=_RepositoryError,
                )

        self.assertEqual(request_mock.call_count, 1)
        sleep_mock.assert_not_called()

    def test_request_json_retries_post_timeout_when_allow_retry_enabled(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.text = '[{"id": "entry-1"}]'
        response.headers = {}
        response.json.return_value = [{"id": "entry-1"}]

        with patch("backend.repositories.supabase_http.requests.request") as request_mock, patch(
            "backend.repositories.supabase_http.time.sleep"
        ) as sleep_mock:
            request_mock.side_effect = [requests.ConnectTimeout("timed out"), response]

            payload, headers = request_json(
                rest_url="https://example.supabase.co/rest/v1",
                api_key="secret",
                timeout_seconds=10.0,
                method="POST",
                path="/tracker_entries",
                payload=[{"entry_key": "entry-1"}],
                allow_retry=True,
                error_cls=_RepositoryError,
            )

        self.assertEqual(payload, [{"id": "entry-1"}])
        self.assertEqual(headers, {})
        self.assertEqual(request_mock.call_count, 2)
        sleep_mock.assert_called_once_with(0.5)

    def test_request_json_retries_get_http_502_and_succeeds(self) -> None:
        failed_response = Mock()
        failed_response.status_code = 502
        failed_response.text = "<html><center>cloudflare</center></html>"
        failed_http_error = requests.HTTPError(response=failed_response)

        failed = Mock()
        failed.raise_for_status.side_effect = failed_http_error

        response = Mock()
        response.raise_for_status.return_value = None
        response.text = '[{"id": "run-1"}]'
        response.headers = {}
        response.json.return_value = [{"id": "run-1"}]

        with patch("backend.repositories.supabase_http.requests.request") as request_mock, patch(
            "backend.repositories.supabase_http.time.sleep"
        ) as sleep_mock:
            request_mock.side_effect = [failed, response]

            payload, headers = request_json(
                rest_url="https://example.supabase.co/rest/v1",
                api_key="secret",
                timeout_seconds=10.0,
                method="GET",
                path="/pipeline_runs",
                error_cls=_RepositoryError,
            )

        self.assertEqual(payload, [{"id": "run-1"}])
        self.assertEqual(headers, {})
        self.assertEqual(request_mock.call_count, 2)
        sleep_mock.assert_called_once_with(0.5)

    def test_request_json_preserves_http_error_behavior(self) -> None:
        response = Mock()
        response.status_code = 404
        response.text = '{"message":"not found"}'
        http_error = requests.HTTPError(response=response)

        failed = Mock()
        failed.raise_for_status.side_effect = http_error

        with patch("backend.repositories.supabase_http.requests.request", return_value=failed) as request_mock, patch(
            "backend.repositories.supabase_http.time.sleep"
        ) as sleep_mock:
            with self.assertRaisesRegex(_RepositoryError, "not found"):
                request_json(
                    rest_url="https://example.supabase.co/rest/v1",
                    api_key="secret",
                    timeout_seconds=10.0,
                    method="GET",
                    path="/pipeline_runs",
                    error_cls=_RepositoryError,
                )

        self.assertEqual(request_mock.call_count, 1)
        sleep_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
