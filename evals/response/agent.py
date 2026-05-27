"""
Response Agent — ADK Evaluation Module.

Exposes `root_agent` with minimal SOAR tools for eval.
Response Agent has only 4 tools (ICM scoping) — the smallest tool surface.
"""
from google.adk.agents import LlmAgent

from agents.response.prompts import RESPONSE_SYSTEM_PROMPT
from evals.mock_tools import (
    get_case,
    create_case_comment,
    execute_manual_action,
    update_case,
)

root_agent = LlmAgent(
    name="response_agent",
    model="gemini-2.5-pro",
    instruction=RESPONSE_SYSTEM_PROMPT,
    tools=[
        get_case,
        create_case_comment,
        execute_manual_action,
        update_case,
    ],
)
