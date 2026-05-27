"""Self-healing plugin for Chronicle MCP tool errors.

Chronicle MCP sometimes returns HTTP 200 with error JSON in the response body
(e.g., {"error": "PERMISSION_DENIED", "message": "..."}). The base
ReflectAndRetryToolPlugin only catches exceptions — this subclass detects
those soft errors and triggers intelligent retry with reflection guidance.
"""

import logging
from typing import Optional

from google.adk.plugins import ReflectAndRetryToolPlugin

logger = logging.getLogger(__name__)

# Errors that indicate a real API problem (worth retrying with different args)
_RETRYABLE_ERROR_KEYS = frozenset({
    "INVALID_ARGUMENT",
    "NOT_FOUND",
    "FAILED_PRECONDITION",
    "DEADLINE_EXCEEDED",
    "INTERNAL",
    "UNAVAILABLE",
})

# Errors that should NOT be retried (intentional blocks, auth issues)
_NON_RETRYABLE_PATTERNS = frozenset({
    "BLOCKED_BY_HITL_GUARD",
    "PERMISSION_DENIED",
    "UNAUTHENTICATED",
})


class ChronicleRetryPlugin(ReflectAndRetryToolPlugin):
    """Detect Chronicle MCP soft errors and trigger reflection-guided retry."""

    def __init__(self, max_retries: int = 2):
        super().__init__(
            name="chronicle_retry_plugin",
            max_retries=max_retries,
            throw_exception_if_retry_exceeded=False,
        )

    async def extract_error_from_result(
        self, *, tool, tool_args, tool_context, result,
    ) -> Optional[Exception]:
        """Detect error responses embedded in successful tool results."""
        error_str = None

        if isinstance(result, dict):
            err = result.get("error", "")
            err_str = str(err)

            # Skip intentional blocks (HITL guard, auth)
            for pattern in _NON_RETRYABLE_PATTERNS:
                if pattern in err_str:
                    return None

            if err:
                detail = result.get("detail", result.get("message", ""))
                error_str = f"Chronicle API error: {err_str}: {detail}"

        elif isinstance(result, str) and '"error"' in result:
            # Skip non-retryable patterns in string results
            for pattern in _NON_RETRYABLE_PATTERNS:
                if pattern in result:
                    return None
            error_str = f"Chronicle API returned error: {result[:500]}"

        if error_str:
            logger.info(
                "ChronicleRetryPlugin detected soft error",
                extra={"tool": getattr(tool, "name", ""), "error": error_str},
            )
            return Exception(error_str)

        return None
