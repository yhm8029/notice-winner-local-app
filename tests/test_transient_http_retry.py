from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.services.transient_http_retry import is_transient_http_status
from backend.services.transient_http_retry import run_with_transient_http_retries


class _Response:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class TransientHttpRetryTests(unittest.TestCase):
    def test_run_with_transient_http_retries_retries_gateway_error_result(self) -> None:
        responses = [_Response(502), _Response(200)]
        calls: list[int] = []

        def _action() -> _Response:
            calls.append(1)
            return responses.pop(0)

        with patch("backend.services.transient_http_retry.time.sleep") as sleep_mock:
            result = run_with_transient_http_retries(
                _action,
                should_retry_result=lambda value: is_transient_http_status(value.status_code),
            )

        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(calls), 2)
        sleep_mock.assert_called_once_with(1.0)

    def test_429_is_not_treated_as_transient_by_default(self) -> None:
        self.assertFalse(is_transient_http_status(429))


if __name__ == "__main__":
    unittest.main()
