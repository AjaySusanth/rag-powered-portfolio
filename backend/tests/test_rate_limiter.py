import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from src.api.rate_limiter import RateLimiter


def make_mock_request(ip: str) -> Request:
    """Helper to create a mocked FastAPI Request object with a specific client IP."""
    request = MagicMock(spec=Request)
    request.client = MagicMock()
    request.client.host = ip
    return request


def test_rate_limiter_allow_requests() -> None:
    """Verifies that requests within the rate limit are allowed to pass."""
    limiter = RateLimiter()
    request = make_mock_request("192.168.1.1")

    # Override settings contextually for the test
    with patch("src.api.rate_limiter.settings") as mock_settings:
        mock_settings.RATE_LIMIT_REQUESTS = 3
        mock_settings.RATE_LIMIT_WINDOW_SECONDS = 10

        # First 3 requests should succeed
        limiter(request)
        limiter(request)
        limiter(request)


def test_rate_limiter_block_on_limit() -> None:
    """Verifies that the N+1 request triggers HTTP 429 and returns a Retry-After header."""
    limiter = RateLimiter()
    request = make_mock_request("192.168.1.1")

    with patch("src.api.rate_limiter.settings") as mock_settings:
        mock_settings.RATE_LIMIT_REQUESTS = 2
        mock_settings.RATE_LIMIT_WINDOW_SECONDS = 60

        # First 2 succeed
        limiter(request)
        limiter(request)

        # 3rd should raise HTTP 429
        with pytest.raises(HTTPException) as exc_info:
            limiter(request)

        assert exc_info.value.status_code == 429
        assert "Retry-After" in exc_info.value.headers
        assert int(exc_info.value.headers["Retry-After"]) > 0


def test_rate_limiter_window_expiry() -> None:
    """Verifies that the rate limit resets after the time window expires."""
    limiter = RateLimiter()
    request = make_mock_request("192.168.1.1")

    with patch("src.api.rate_limiter.settings") as mock_settings:
        mock_settings.RATE_LIMIT_REQUESTS = 1
        mock_settings.RATE_LIMIT_WINDOW_SECONDS = 10

        # Initial request
        limiter(request)

        # Next immediate request is blocked
        with pytest.raises(HTTPException):
            limiter(request)

        # Mock time forward by 11 seconds
        future_time = time.time() + 11
        with patch("time.time", return_value=future_time):
            # Request should now succeed as window reset
            limiter(request)


def test_rate_limiter_client_isolation() -> None:
    """Verifies that rate limiting limits are tracked independently for different client IPs."""
    limiter = RateLimiter()
    req_a = make_mock_request("1.1.1.1")
    req_b = make_mock_request("2.2.2.2")

    with patch("src.api.rate_limiter.settings") as mock_settings:
        mock_settings.RATE_LIMIT_REQUESTS = 1
        mock_settings.RATE_LIMIT_WINDOW_SECONDS = 10

        # Client A makes a request
        limiter(req_a)

        # Client A's next request is blocked
        with pytest.raises(HTTPException):
            limiter(req_a)

        # Client B's request succeeds independently
        limiter(req_b)

        # Client B's next request is blocked
        with pytest.raises(HTTPException):
            limiter(req_b)
