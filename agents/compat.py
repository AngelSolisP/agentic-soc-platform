"""
Python 3.11 + anyio compatibility workaround.

Problem: Python 3.11's asyncio.wait_for() creates new tasks during
cancellation/timeout handling. This violates anyio's CancelScope constraint
that enter() and __exit__() must occur in the same asyncio.Task. The MCP SDK
uses anyio internally (via task groups in streamable_http_client), causing
"Attempted to exit cancel scope in a different task" errors.

This was fixed in Python 3.12 (enhanced task context management). ADK handles
it in Runner cleanup by catching CancelledError. But the error also occurs
during MCP session creation, where ADK has no workaround.

This module patches CancelScope.__exit__ to log and swallow the cross-task
false positive. Only active on Python < 3.12.

References:
    - ADK Runner cleanup: google.adk.runners (line ~1553)
    - anyio CancelScope: anyio._backends._asyncio.CancelScope.__exit__
    - Python 3.12 changelog: bpo-45098 (task context propagation)
"""

import logging
import sys

logger = logging.getLogger(__name__)

_patched = False


def patch_anyio_cancel_scope_for_python311():
    """Apply cancel scope workaround for Python 3.11.

    Safe to call multiple times — only patches once.
    No-op on Python 3.12+ where the underlying issue is fixed.
    """
    global _patched
    if _patched:
        return

    if sys.version_info >= (3, 12):
        logger.debug("Python >= 3.12 detected, cancel scope patch not needed")
        _patched = True
        return

    try:
        from anyio._backends._asyncio import CancelScope
    except ImportError:
        logger.debug("anyio not installed, cancel scope patch not needed")
        _patched = True
        return

    original_exit = CancelScope.__exit__

    def _patched_exit(self, exc_type, exc_val, exc_tb):
        try:
            return original_exit(self, exc_type, exc_val, exc_tb)
        except RuntimeError as e:
            if "different task" in str(e):
                logger.warning(
                    "anyio cancel scope cross-task exit (Python 3.11 workaround, non-fatal): %s", e
                )
                # Return False = do not suppress the original exception.
                # The cancel scope error itself is swallowed, but any underlying
                # exception (timeout, connection error) still propagates.
                return False
            raise

    CancelScope.__exit__ = _patched_exit
    _patched = True
    logger.info("Applied anyio cancel scope patch for Python %s", sys.version_info[:2])
