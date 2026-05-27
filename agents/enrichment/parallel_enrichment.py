"""
Parallel Enrichment — runs Chronicle and GTI enrichment concurrently.

Uses ADK ParallelAgent to execute both toolsets simultaneously,
then a merger LlmAgent combines results into the canonical output.
Falls back to a single LlmAgent when GTI is disabled.
"""

import os
import logging
from typing import Optional, Union

from google.adk.agents import LlmAgent, ParallelAgent

from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

from .prompts_split import (
    CHRONICLE_ENRICHMENT_PROMPT,
    GTI_ENRICHMENT_PROMPT,
    ENRICHMENT_MERGER_PROMPT,
)
from agents.tool_catalog import CHRONICLE_ENRICHMENT_TOOLS, GTI_ENRICHMENT_TOOLS
from agents.mcp_auth import build_mcp_connection, build_mcp_auth_provider
from agents.runbook_loader import get_enrichment_contract
from agents.validation import safe_agent_name

logger = logging.getLogger(__name__)


def create_parallel_enrichment_agent(
    client_id: str,
    gateway_url: Optional[str] = None,
    gti_gateway_url: Optional[str] = None,
    gti_enabled: bool = False,
    model: Optional[str] = None,
) -> Union[LlmAgent, ParallelAgent]:
    """
    Create enrichment agent(s) that run Chronicle and GTI in parallel.

    When gti_enabled=True, returns a ParallelAgent wrapping two LlmAgent
    sub-agents (chronicle + gti) that execute concurrently.
    When gti_enabled=False, returns a single chronicle-only LlmAgent.

    The orchestrator should include a merger agent downstream to combine
    results from both sub-agents.
    """
    gateway_base = gateway_url or os.environ.get(
        "MCP_GATEWAY_URL", "http://localhost:8080"
    )
    model_id = model or os.environ.get("GEMINI_FLASH_MODEL", "gemini-2.5-flash")
    safe_name = safe_agent_name(client_id)

    # Chronicle sub-agent (always present)
    chronicle_url = f"{gateway_base}/mcp/{client_id}"
    chronicle_toolset = McpToolset(
        connection_params=build_mcp_connection(chronicle_url),
        tool_filter=CHRONICLE_ENRICHMENT_TOOLS,
        header_provider=build_mcp_auth_provider(chronicle_url),
    )

    enrichment_contract = get_enrichment_contract()

    chronicle_agent = LlmAgent(
        name=f"chronicle_enrichment_{safe_name}",
        model=model_id,
        description="Chronicle SIEM IoC enrichment — UDM search, entity lookup, IoC matching.",
        instruction=f"{CHRONICLE_ENRICHMENT_PROMPT}\n\n## STAGE CONTRACT\n{enrichment_contract}",
        tools=[chronicle_toolset],
        output_key="chronicle_enrichment_result",
    )

    if not gti_enabled:
        # No GTI — return single chronicle agent (no ParallelAgent overhead)
        logger.info("Creating single Chronicle enrichment agent (GTI disabled)",
                     extra={"client_id": client_id})
        return chronicle_agent

    # GTI sub-agent
    gti_base = gti_gateway_url or gateway_base
    gti_url = f"{gti_base}/gti/{client_id}"
    gti_toolset = McpToolset(
        connection_params=build_mcp_connection(gti_url),
        tool_filter=GTI_ENRICHMENT_TOOLS,
        header_provider=build_mcp_auth_provider(gti_url),
    )

    gti_agent = LlmAgent(
        name=f"gti_enrichment_{safe_name}",
        model=model_id,
        description="GTI/VirusTotal IoC enrichment — file, IP, domain, URL reports.",
        instruction=GTI_ENRICHMENT_PROMPT,
        tools=[gti_toolset],
        output_key="gti_enrichment_result",
    )

    logger.info("Creating parallel enrichment agent (Chronicle + GTI)",
                 extra={"client_id": client_id})

    return ParallelAgent(
        name=f"parallel_enrichment_{safe_name}",
        sub_agents=[chronicle_agent, gti_agent],
    )


def create_enrichment_merger_agent(
    client_id: str,
    gateway_url: Optional[str] = None,
    model: Optional[str] = None,
) -> LlmAgent:
    """Create a lightweight agent that merges parallel enrichment results.

    Reads chronicle_enrichment_result and gti_enrichment_result from state
    and produces the unified enrichment output. Also adds a case comment.
    """
    gateway_base = gateway_url or os.environ.get(
        "MCP_GATEWAY_URL", "http://localhost:8080"
    )
    model_id = model or os.environ.get("GEMINI_FLASH_MODEL", "gemini-2.5-flash")

    # Merger needs comment tool to document findings
    chronicle_url = f"{gateway_base}/mcp/{client_id}"
    comment_toolset = McpToolset(
        connection_params=build_mcp_connection(chronicle_url),
        tool_filter=["create_case_comment"],
        header_provider=build_mcp_auth_provider(chronicle_url),
    )

    return LlmAgent(
        name=f"enrichment_merger_{safe_agent_name(client_id)}",
        model=model_id,
        description="Merges Chronicle and GTI enrichment results into unified report.",
        instruction=ENRICHMENT_MERGER_PROMPT,
        tools=[comment_toolset],
    )
