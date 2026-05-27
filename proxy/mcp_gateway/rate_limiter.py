"""
Per-client token bucket rate limiter for the MCP Gateway.

Limits the number of requests per client per time window to prevent
a single tenant from exhausting shared resources.

NOTE: This rate limiter is in-memory (per Cloud Run replica). With
max_instances=N, the effective burst capacity is N × max_tokens.
This is acceptable for MVP (max_instances=3 → 300 burst).
For production at scale, layer Cloud Armor rate limiting in front
(global, at the load balancer) or use Memorystore (Redis) for
shared state across replicas.
"""

import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class _Bucket:
    """Token bucket state for a single client."""
    tokens: float
    last_refill: float


class RateLimiter:
    """
    Token bucket rate limiter keyed by client_id.

    Each client gets `max_tokens` tokens. Tokens are consumed on each request
    and refilled at `refill_rate` tokens per second. When tokens are exhausted,
    requests are rejected with 429.

    Args:
        max_tokens: Maximum tokens per client (burst capacity).
        refill_rate: Tokens added per second.
    """

    def __init__(self, max_tokens: int = 100, refill_rate: float = 10.0):
        self._max_tokens = max_tokens
        self._refill_rate = refill_rate
        self._buckets: dict[str, _Bucket] = {}

    def _get_bucket(self, client_id: str) -> _Bucket:
        now = time.time()
        if client_id not in self._buckets:
            self._buckets[client_id] = _Bucket(
                tokens=float(self._max_tokens), last_refill=now
            )
        bucket = self._buckets[client_id]

        # Refill tokens based on elapsed time
        elapsed = now - bucket.last_refill
        if elapsed > 0:
            bucket.tokens = min(
                self._max_tokens, bucket.tokens + elapsed * self._refill_rate
            )
            bucket.last_refill = now

        return bucket

    def allow_request(self, client_id: str, cost: float = 1.0) -> bool:
        """
        Check if a request should be allowed.

        Returns True and consumes a token if allowed.
        Returns False if rate limit exceeded.
        """
        bucket = self._get_bucket(client_id)

        if bucket.tokens >= cost:
            bucket.tokens -= cost
            return True

        logger.warning(
            "Rate limit exceeded",
            extra={
                "client_id": client_id,
                "tokens_remaining": round(bucket.tokens, 2),
                "max_tokens": self._max_tokens,
            },
        )
        return False

    def get_remaining(self, client_id: str) -> float:
        """Return remaining tokens for a client."""
        bucket = self._get_bucket(client_id)
        return round(bucket.tokens, 2)

    def reset(self, client_id: str = None) -> None:
        """Reset rate limit for one or all clients."""
        if client_id:
            self._buckets.pop(client_id, None)
        else:
            self._buckets.clear()
