"""
Triage Agent — ADK Evaluation Module.

Exposes `root_agent` for use with AgentEvaluator.evaluate().
Uses mock FunctionTools instead of McpToolset so evals run without MCP infra.

Usage:
    AgentEvaluator.evaluate(
        agent_module="evals.triage.agent",
        eval_dataset_file_path_or_dir="evals/triage/",
    )
"""
from google.adk.agents import LlmAgent

from agents.triage.prompts import TRIAGE_SYSTEM_PROMPT
from evals.mock_tools import (
    translate_udm_query,
    udm_search,
    summarize_entity,
    search_entity,
    get_ioc_match,
    get_case,
    list_case_alerts,
    get_case_alert,
    create_case_comment,
)

root_agent = LlmAgent(
    name="triage_agent",
    model="gemini-2.5-flash",
    instruction=TRIAGE_SYSTEM_PROMPT,
    tools=[
        translate_udm_query,
        udm_search,
        summarize_entity,
        search_entity,
        get_ioc_match,
        get_case,
        list_case_alerts,
        get_case_alert,
        create_case_comment,
    ],
)
