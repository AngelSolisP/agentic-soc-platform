"""Tests for the per-client circuit breaker."""

import time
from unittest.mock import patch

from proxy.mcp_gateway.circuit_breaker import CircuitBreaker, CircuitState


def test_closed_allows_requests():
    cb = CircuitBreaker(failure_threshold=3)
    assert cb.allow_request("client-a") is True
    assert cb.get_state("client-a") == CircuitState.CLOSED


def test_opens_after_threshold():
    cb = CircuitBreaker(failure_threshold=3)
    for _ in range(3):
        cb.record_failure("client-a")
    assert cb.get_state("client-a") == CircuitState.OPEN
    assert cb.allow_request("client-a") is False


def test_does_not_open_below_threshold():
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure("client-a")
    cb.record_failure("client-a")
    assert cb.get_state("client-a") == CircuitState.CLOSED
    assert cb.allow_request("client-a") is True


def test_half_open_after_recovery_timeout():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
    cb.record_failure("client-a")
    cb.record_failure("client-a")
    assert cb.get_state("client-a") == CircuitState.OPEN

    # Simulate time passing
    with patch("proxy.mcp_gateway.circuit_breaker.time") as mock_time:
        mock_time.time.return_value = time.time() + 2
        assert cb.allow_request("client-a") is True
        assert cb.get_state("client-a") == CircuitState.HALF_OPEN


def test_half_open_success_closes_circuit():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
    cb.record_failure("client-a")
    assert cb.get_state("client-a") == CircuitState.OPEN

    # Recovery timeout = 0, so next allow_request transitions to HALF_OPEN
    cb.allow_request("client-a")
    assert cb.get_state("client-a") == CircuitState.HALF_OPEN

    cb.record_success("client-a")
    assert cb.get_state("client-a") == CircuitState.CLOSED
    assert cb.allow_request("client-a") is True


def test_half_open_failure_reopens_circuit():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
    cb.record_failure("client-a")
    cb.allow_request("client-a")  # transitions to HALF_OPEN
    assert cb.get_state("client-a") == CircuitState.HALF_OPEN

    cb.record_failure("client-a")
    assert cb.get_state("client-a") == CircuitState.OPEN


def test_per_client_isolation():
    cb = CircuitBreaker(failure_threshold=2)
    cb.record_failure("client-a")
    cb.record_failure("client-a")
    assert cb.get_state("client-a") == CircuitState.OPEN
    assert cb.get_state("client-b") == CircuitState.CLOSED
    assert cb.allow_request("client-b") is True


def test_success_resets_failure_count():
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure("client-a")
    cb.record_failure("client-a")
    cb.record_success("client-a")
    # After success, failure count resets — need 3 more failures to open
    cb.record_failure("client-a")
    assert cb.get_state("client-a") == CircuitState.CLOSED


def test_get_all_states():
    cb = CircuitBreaker(failure_threshold=1)
    cb.record_failure("client-a")
    cb.record_success("client-b")
    states = cb.get_all_states()
    assert "client-a" in states
    assert "client-b" in states
    assert states["client-a"]["state"] == "OPEN"
    assert states["client-b"]["state"] == "CLOSED"


def test_reset_single_client():
    cb = CircuitBreaker(failure_threshold=1)
    cb.record_failure("client-a")
    cb.record_failure("client-b")
    cb.reset("client-a")
    assert cb.get_state("client-a") == CircuitState.CLOSED  # fresh state
    assert cb.get_state("client-b") == CircuitState.OPEN


def test_reset_all():
    cb = CircuitBreaker(failure_threshold=1)
    cb.record_failure("client-a")
    cb.record_failure("client-b")
    cb.reset()
    assert cb.get_all_states() == {}
