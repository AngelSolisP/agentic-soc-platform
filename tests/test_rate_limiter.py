"""Tests for the per-client token bucket rate limiter."""

import time
from unittest.mock import patch

from proxy.mcp_gateway.rate_limiter import RateLimiter


def test_allows_requests_under_limit():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    for _ in range(5):
        assert rl.allow_request("client-a") is True


def test_rejects_when_exhausted():
    rl = RateLimiter(max_tokens=2, refill_rate=0.0)  # no refill
    assert rl.allow_request("client-a") is True
    assert rl.allow_request("client-a") is True
    assert rl.allow_request("client-a") is False


def test_custom_cost():
    rl = RateLimiter(max_tokens=10, refill_rate=0.0)
    assert rl.allow_request("client-a", cost=7.0) is True
    assert rl.allow_request("client-a", cost=4.0) is False  # only 3 left
    assert rl.allow_request("client-a", cost=3.0) is True


def test_refill_over_time():
    rl = RateLimiter(max_tokens=5, refill_rate=10.0)
    # Exhaust all tokens
    for _ in range(5):
        rl.allow_request("client-a")
    assert rl.allow_request("client-a") is False

    # Simulate 1 second passing — should refill to max (5)
    with patch("proxy.mcp_gateway.rate_limiter.time") as mock_time:
        mock_time.time.return_value = time.time() + 1
        assert rl.allow_request("client-a") is True


def test_refill_caps_at_max():
    rl = RateLimiter(max_tokens=5, refill_rate=100.0)
    rl.allow_request("client-a")  # use 1 token

    with patch("proxy.mcp_gateway.rate_limiter.time") as mock_time:
        mock_time.time.return_value = time.time() + 10  # way more than enough
        remaining = rl.get_remaining("client-a")
        assert remaining <= 5.0


def test_per_client_isolation():
    rl = RateLimiter(max_tokens=2, refill_rate=0.0)
    rl.allow_request("client-a")
    rl.allow_request("client-a")
    assert rl.allow_request("client-a") is False
    assert rl.allow_request("client-b") is True  # separate bucket


def test_get_remaining():
    rl = RateLimiter(max_tokens=10, refill_rate=0.0)
    assert rl.get_remaining("client-a") == 10.0
    rl.allow_request("client-a")
    assert rl.get_remaining("client-a") == 9.0


def test_reset_single_client():
    rl = RateLimiter(max_tokens=2, refill_rate=0.0)
    rl.allow_request("client-a")
    rl.allow_request("client-a")
    assert rl.allow_request("client-a") is False
    rl.reset("client-a")
    assert rl.allow_request("client-a") is True  # fresh bucket


def test_reset_all():
    rl = RateLimiter(max_tokens=1, refill_rate=0.0)
    rl.allow_request("client-a")
    rl.allow_request("client-b")
    rl.reset()
    assert rl.allow_request("client-a") is True
    assert rl.allow_request("client-b") is True
