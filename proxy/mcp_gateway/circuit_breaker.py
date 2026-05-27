"""
Circuit Breaker for Chronicle MCP upstream calls.

Tracks consecutive failures per client_id. After a configurable threshold,
the circuit opens and fast-fails requests instead of hitting a dead endpoint.

States:
    CLOSED  → Normal operation. Failures increment counter.
    OPEN    → Fast-fail all requests. After recovery_timeout, move to HALF_OPEN.
    HALF_OPEN → Allow one probe request. If it succeeds → CLOSED. If it fails → OPEN.

NOTE: Per-replica in-memory state is the correct pattern for circuit breakers.
Each Cloud Run instance independently tracks upstream health — a failure seen
by one replica does not necessarily affect others (different TCP connections,
possible network partitions). This is consistent with standard circuit breaker
implementations (e.g., Hystrix, resilience4j).
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class _ClientCircuit:
    """Per-client circuit state."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0


class CircuitBreaker:
    """
    Per-client circuit breaker for upstream MCP calls.

    Usage:
        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

        if not cb.allow_request(client_id):
            raise HTTPException(503, "Circuit open")

        try:
            response = await call_chronicle(...)
            cb.record_success(client_id)
        except Exception:
            cb.record_failure(client_id)
            raise
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
    ):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._circuits: dict[str, _ClientCircuit] = {}

    def _get_circuit(self, client_id: str) -> _ClientCircuit:
        if client_id not in self._circuits:
            self._circuits[client_id] = _ClientCircuit()
        return self._circuits[client_id]

    def allow_request(self, client_id: str) -> bool:
        """Check if a request to this client's endpoint should be allowed."""
        circuit = self._get_circuit(client_id)
        now = time.time()

        if circuit.state == CircuitState.CLOSED:
            return True

        if circuit.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if now - circuit.last_failure_time >= self._recovery_timeout:
                circuit.state = CircuitState.HALF_OPEN
                logger.info(
                    "Circuit half-open, allowing probe request",
                    extra={"client_id": client_id},
                )
                return True
            return False

        # HALF_OPEN: allow one probe
        return True

    def record_success(self, client_id: str) -> None:
        """Record a successful upstream call — reset the circuit."""
        circuit = self._get_circuit(client_id)
        previous_state = circuit.state

        circuit.state = CircuitState.CLOSED
        circuit.failure_count = 0
        circuit.last_success_time = time.time()

        if previous_state != CircuitState.CLOSED:
            logger.info(
                "Circuit closed after recovery",
                extra={"client_id": client_id, "previous_state": previous_state.value},
            )

    def record_failure(self, client_id: str) -> None:
        """Record a failed upstream call — may open the circuit."""
        circuit = self._get_circuit(client_id)
        circuit.failure_count += 1
        circuit.last_failure_time = time.time()

        if circuit.state == CircuitState.HALF_OPEN:
            # Probe failed, back to OPEN
            circuit.state = CircuitState.OPEN
            logger.warning(
                "Circuit re-opened after failed probe",
                extra={"client_id": client_id},
            )
        elif circuit.failure_count >= self._failure_threshold:
            circuit.state = CircuitState.OPEN
            logger.warning(
                "Circuit opened",
                extra={
                    "client_id": client_id,
                    "failure_count": circuit.failure_count,
                    "threshold": self._failure_threshold,
                },
            )

    def get_state(self, client_id: str) -> CircuitState:
        """Return current circuit state for a client."""
        return self._get_circuit(client_id).state

    def get_all_states(self) -> dict[str, dict]:
        """Return all circuit states (for health/debug endpoints)."""
        return {
            cid: {
                "state": c.state.value,
                "failure_count": c.failure_count,
                "last_failure": c.last_failure_time,
                "last_success": c.last_success_time,
            }
            for cid, c in self._circuits.items()
        }

    def reset(self, client_id: Optional[str] = None) -> None:
        """Reset circuit state for one or all clients."""
        if client_id:
            self._circuits.pop(client_id, None)
        else:
            self._circuits.clear()
