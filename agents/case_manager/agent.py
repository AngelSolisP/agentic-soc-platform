"""
Case Manager Agent — SOAR case lifecycle management.

Uses Gemini 2.0 Flash for case operations.
"""

import os
import logging
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

from .prompts import CASE_MANAGER_SYSTEM_PROMPT, CASE_MANAGER_TASK_TEMPLATE
from agents.tool_catalog import CASE_MANAGER_TOOLS
from agents.mcp_auth import build_mcp_connection, build_mcp_auth_provider
from agents.runbook_loader import get_case_manager_contract
from agents.validation import safe_agent_name

logger = logging.getLogger(__name__)


def create_case_manager_agent(
    client_id: str,
    gateway_url: Optional[str] = None,
    model: Optional[str] = None,
    before_model_callback=None,
) -> LlmAgent:
    gateway_base = gateway_url or os.environ.get(
        "MCP_GATEWAY_URL", "http://localhost:8080"
    )
    mcp_url = f"{gateway_base}/mcp/{client_id}"
    model_id = model or os.environ.get("GEMINI_FLASH_MODEL", "gemini-2.5-flash")

    toolset = McpToolset(
        connection_params=build_mcp_connection(mcp_url),
        tool_filter=CASE_MANAGER_TOOLS,
        header_provider=build_mcp_auth_provider(mcp_url),
    )

    # ICM: Inject case management contract into system prompt
    case_contract = get_case_manager_contract()
    instruction = (
        f"{CASE_MANAGER_SYSTEM_PROMPT}\n\n"
        f"## STAGE CONTRACT\n{case_contract}"
    )

    return LlmAgent(
        name=f"case_manager_agent_{safe_agent_name(client_id)}",
        model=model_id,
        description=(
            "SOAR case manager that updates, comments, escalates, "
            "and closes Chronicle SecOps cases based on analysis results."
        ),
        instruction=instruction,
        tools=[toolset],
        before_model_callback=before_model_callback,
    )


def build_case_manager_task(
    case_id: str,
    client_id: str,
    recommended_action: str,
    triage_results: str,
    enrichment_results: str = "",
) -> str:
    return CASE_MANAGER_TASK_TEMPLATE.format(
        case_id=case_id,
        client_id=client_id,
        recommended_action=recommended_action,
        triage_results=triage_results,
        enrichment_results=enrichment_results or "No enrichment performed.",
    )
