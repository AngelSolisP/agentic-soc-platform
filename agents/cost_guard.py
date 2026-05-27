"""Shared LLM call guard — dual protection: call budget + wall-clock timeout.

Applied as before_model_callback on every agent in the pipeline.
Replaces reliance on asyncio.timeout (broken with anyio/MCP cancel scopes)
and CostGuardPlugin (not firing in production for unknown reasons).

Belt-and-suspenders: this callback runs per-agent while the plugin remains
registered on the Runner as a second layer.
"""

import os
import time
import logging

from google.adk.models import LlmResponse
from google.genai.types import Content, Part

logger = logging.getLogger(__name__)

MAX_LLM_CALLS = int(os.environ.get("MAX_LLM_CALLS_PER_PIPELINE", "25"))
PIPELINE_TIMEOUT = int(os.environ.get("AGENT_TIMEOUT_SECONDS", "120"))


def llm_call_guard(callback_context, llm_request):
    """before_model_callback: dual guard — call budget + wall-clock timeout.

    Uses session state so the counter and start time are shared across
    all agents in a single pipeline run.

    Returns LlmResponse to halt the agent if either limit is exceeded.
    Returns None to allow the LLM call to proceed.
    """
    state = callback_context.state

    # ── Call budget ─────────────────────────────────────────
    count = state.get("_llm_call_count", 0) + 1
    state["_llm_call_count"] = count
    logger.info("llm_call_guard: LLM call %d/%d", count, MAX_LLM_CALLS)

    if count > MAX_LLM_CALLS:
        logger.warning(
            "llm_call_guard: budget exhausted (%d/%d)", count, MAX_LLM_CALLS,
        )
        return LlmResponse(
            content=Content(
                parts=[Part(text=(
                    f"MAX_LLM_CALLS ({MAX_LLM_CALLS}) reached. "
                    "Stopping to prevent runaway costs. Return your current results now."
                ))],
                role="model",
            ),
        )

    # ── Wall-clock timeout ─────────────────────────────────
    now = time.time()
    start = state.get("_pipeline_start_time")
    if start is None:
        state["_pipeline_start_time"] = now
        start = now

    elapsed = now - start
    if elapsed > PIPELINE_TIMEOUT:
        logger.warning(
            "llm_call_guard: wall-clock timeout (%.0fs > %ds)",
            elapsed, PIPELINE_TIMEOUT,
        )
        return LlmResponse(
            content=Content(
                parts=[Part(text=(
                    f"Pipeline timeout ({PIPELINE_TIMEOUT}s) exceeded — "
                    f"elapsed {elapsed:.0f}s. "
                    "Stopping to prevent runaway costs. Return your current results now."
                ))],
                role="model",
            ),
        )

    return None
