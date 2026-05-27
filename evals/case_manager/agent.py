"""
Case Manager Agent — ADK Evaluation Module.

Exposes `root_agent` with mock SOAR tools for eval.
Case Manager has NO SIEM or GTI tools (ICM scoping).
"""
from google.adk.agents import LlmAgent

from agents.case_manager.prompts import CASE_MANAGER_SYSTEM_PROMPT
from evals.mock_tools import (
    list_cases,
    get_case,
    list_case_alerts,
    get_case_alert,
    update_case,
    create_case_comment,
    execute_bulk_close_case,
)

root_agent = LlmAgent(
    name="case_manager_agent",
    model="gemini-2.5-flash",
    instruction=CASE_MANAGER_SYSTEM_PROMPT,
    tools=[
        list_cases,
        get_case,
        list_case_alerts,
        get_case_alert,
        update_case,
        create_case_comment,
        execute_bulk_close_case,
    ],
)
