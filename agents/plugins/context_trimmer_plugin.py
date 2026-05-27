"""Context window trimmer plugin.

Trims old conversation history when it exceeds a threshold, while
preserving function call/response pairs to avoid model errors from
orphaned function responses.
"""

import logging
from typing import Optional

from google.adk.plugins import BasePlugin

logger = logging.getLogger(__name__)


class ContextTrimmerPlugin(BasePlugin):
    """Trim old messages while preserving function call/response integrity."""

    def __init__(self, max_messages: int = 40, keep_recent: int = 20):
        super().__init__(name="context_trimmer_plugin")
        self._max_messages = max_messages
        self._keep_recent = keep_recent

    async def before_model_callback(
        self, *, callback_context, llm_request,
    ) -> None:
        contents = llm_request.contents
        if not contents or len(contents) <= self._max_messages:
            return None

        total = len(contents)
        # Always keep first message (initial user task) and recent messages
        first = contents[:1]
        recent = contents[-self._keep_recent:]

        # Adjust split to avoid orphaned function responses:
        # A function_response without its preceding function_call breaks the model.
        start_idx = total - self._keep_recent
        start_idx = self._adjust_split(contents, start_idx)
        recent = contents[start_idx:]

        trimmed = first + recent
        trimmed_count = total - len(trimmed)

        if trimmed_count > 0:
            logger.debug(
                "ContextTrimmerPlugin: trimmed %d messages (%d → %d)",
                trimmed_count, total, len(trimmed),
            )
            llm_request.contents = trimmed

        return None

    @staticmethod
    def _adjust_split(contents: list, split_idx: int) -> int:
        """Move split point backward to avoid splitting function call/response pairs."""
        if split_idx <= 1:
            return split_idx

        # Walk backward from split point to find a safe boundary
        idx = split_idx
        while idx > 1:
            content = contents[idx]
            # Check if this message is a function response (model role with function_response parts)
            if hasattr(content, "parts") and content.parts:
                has_func_response = any(
                    hasattr(part, "function_response") and part.function_response
                    for part in content.parts
                )
                if has_func_response:
                    # Include the preceding function_call too
                    idx -= 1
                    continue
            break

        return idx
