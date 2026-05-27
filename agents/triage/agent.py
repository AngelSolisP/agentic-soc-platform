"""
Triage Agent — Analyzes Chronicle alerts and produces structured assessments.

Uses Gemini 2.0 Flash for high-volume, cost-effective triage.
Connects to Chronicle via the MCP Gateway using McpToolset.
"""

import os
import logging
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

from .prompts import TRIAGE_SYSTEM_PROMPT, TRIAGE_TASK_TEMPLATE
from agents.tool_catalog import TRIAGE_TOOLS
from agents.mcp_auth import build_mcp_connection, build_mcp_auth_provider
from agents.runbook_loader import get_triage_contract
from agents.validation import safe_agent_name
from agents.risk_scoring import get_risk_score_modifier

logger = logging.getLogger(__name__)


def create_triage_agent(
    client_id: str,
    gateway_url: Optional[str] = None,
    model: Optional[str] = None,
    before_model_callback=None,
) -> LlmAgent:
    """
    Factory function: create a Triage Agent configured for a specific client.

    Args:
        client_id: The client identifier for routing through the MCP Gateway.
        gateway_url: Base URL of the MCP Gateway Cloud Run service.
                     Defaults to MCP_GATEWAY_URL env var.
        model: Gemini model ID. Defaults to GEMINI_FLASH_MODEL env var.

    Returns:
        Configured LlmAgent ready to run.
    """
    gateway_base = gateway_url or os.environ.get(
        "MCP_GATEWAY_URL", "http://localhost:8080"
    )
    mcp_url = f"{gateway_base}/mcp/{client_id}"
    model_id = model or os.environ.get("GEMINI_FLASH_MODEL", "gemini-2.5-flash")

    logger.info(
        "Creating Triage Agent",
        extra={"client_id": client_id, "model": model_id, "mcp_url": mcp_url},
    )

    toolset = McpToolset(
        connection_params=build_mcp_connection(mcp_url),
        tool_filter=TRIAGE_TOOLS,
        header_provider=build_mcp_auth_provider(mcp_url),
    )

    # ICM: Inject the default triage contract into the agent's system prompt.
    # The orchestrator routes dynamically via sub_agents, so we can't inject
    # at delegation time — the instruction field is the only injection point.
    default_contract = get_triage_contract("UNKNOWN")
    instruction_with_contract = (
        f"{TRIAGE_SYSTEM_PROMPT}\n\n"
        f"## STAGE CONTRACT (Default)\n{default_contract}"
    )

    agent = LlmAgent(
        name=f"triage_agent_{safe_agent_name(client_id)}",
        model=model_id,
        description=(
            "Tier-1 SOC analyst that triages Chronicle security alerts, "
            "enriches IoCs, assesses severity, and documents findings."
        ),
        instruction=instruction_with_contract,
        tools=[toolset, get_risk_score_modifier],
        before_model_callback=before_model_callback,
    )

    return agent


def build_triage_task(
    case_id: str,
    client_id: str,
    alert_type: str = "UNKNOWN",
    severity: str = "MEDIUM",
    additional_context: str = "",
    autonomous_mode: bool = False,
) -> str:
    """Format the triage task prompt with the appropriate runbook contract injected."""
    return TRIAGE_TASK_TEMPLATE.format(
        runbook_contract=get_triage_contract(alert_type),
        case_id=case_id,
        client_id=client_id,
        alert_type=alert_type,
        severity=severity,
        autonomous_mode=autonomous_mode,
        additional_context=additional_context or "No additional context provided.",
    )
