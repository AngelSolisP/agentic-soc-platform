"""Global LLM call budget guard as an ADK plugin.

Replaces the per-agent before_model_callback pattern with a single plugin
registered on the Runner. Applies to ALL agents in the hierarchy automatically.
"""

import os
import logging
from typing import Optional

from google.adk.plugins import BasePlugin
from google.adk.models import LlmResponse
from google.genai.types import Content, Part

logger = logging.getLogger(__name__)

DEFAULT_MAX_LLM_CALLS = 25


class CostGuardPlugin(BasePlugin):
    """Cap total LLM calls per pipeline run using shared session state."""

    def __init__(self, max_llm_calls: Optional[int] = None):
        super().__init__(name="cost_guard_plugin")
        self._max = max_llm_calls or int(
            os.environ.get("MAX_LLM_CALLS_PER_PIPELINE", str(DEFAULT_MAX_LLM_CALLS))
        )

    async def before_model_callback(
        self, *, callback_context, llm_request,
    ) -> Optional[LlmResponse]:
        count = callback_context.state.get("_llm_call_count", 0) + 1
        callback_context.state["_llm_call_count"] = count
        logger.info("CostGuardPlugin: LLM call %d/%d", count, self._max)

        if count > self._max:
            logger.warning(
                "CostGuardPlugin: budget exhausted",
                extra={"count": count, "max": self._max},
            )
            return LlmResponse(
                content=Content(
                    parts=[Part(text=(
                        f"MAX_LLM_CALLS ({self._max}) reached. "
                        "Stopping to prevent runaway costs. Returning current results."
                    ))],
                    role="model",
                ),
            )
        return None
