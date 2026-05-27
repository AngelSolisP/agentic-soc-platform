"""
Enrichment Agent — IoC enrichment via GTI + Chronicle entity analysis.

Uses Gemini 2.0 Flash for parallel IoC lookups.
Dual McpToolset: Chronicle (always) + GTI (conditional per client).
"""

import os
import logging
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

from .prompts import (
    ENRICHMENT_SYSTEM_PROMPT,
    ENRICHMENT_SYSTEM_PROMPT_NO_GTI,
    ENRICHMENT_TASK_TEMPLATE,
)
from agents.tool_catalog import CHRONICLE_ENRICHMENT_TOOLS, GTI_ENRICHMENT_TOOLS
from agents.mcp_auth import build_mcp_connection, build_mcp_auth_provider
from agents.runbook_loader import get_enrichment_contract
from agents.validation import safe_agent_name
from agents.risk_scoring import get_risk_score_modifier
from agents.enrichment.threat_context import get_structured_threat_context

logger = logging.getLogger(__name__)


def create_enrichment_agent(
    client_id: str,
    gateway_url: Optional[str] = None,
    gti_gateway_url: Optional[str] = None,
    gti_enabled: bool = False,
    model: Optional[str] = None,
    use_parallel: bool = False,
    before_model_callback=None,
):
    """
    Factory: create an Enrichment Agent for a specific client.

    Args:
        client_id: Client identifier for MCP Gateway routing.
        gateway_url: MCP Gateway base URL (Chronicle route).
        gti_gateway_url: MCP Gateway URL for GTI route (defaults to gateway_url).
        gti_enabled: Whether this client has GTI enrichment enabled.
        model: Gemini model ID (Flash by default for cost efficiency).
        use_parallel: Use ParallelAgent for concurrent Chronicle + GTI enrichment.
    """
    if use_parallel:
        from .parallel_enrichment import create_parallel_enrichment_agent
        return create_parallel_enrichment_agent(
            client_id, gateway_url, gti_gateway_url, gti_enabled, model,
        )

    gateway_base = gateway_url or os.environ.get(
        "MCP_GATEWAY_URL", "http://localhost:8080"
    )
    model_id = model or os.environ.get("GEMINI_FLASH_MODEL", "gemini-2.5-flash")

    logger.info(
        "Creating Enrichment Agent",
        extra={"client_id": client_id, "model": model_id, "gti_enabled": gti_enabled},
    )

    # Chronicle toolset (always present)
    chronicle_url = f"{gateway_base}/mcp/{client_id}"
    toolset = McpToolset(
        connection_params=build_mcp_connection(chronicle_url),
        tool_filter=CHRONICLE_ENRICHMENT_TOOLS,
        header_provider=build_mcp_auth_provider(chronicle_url),
    )
    tools = [toolset, get_risk_score_modifier, get_structured_threat_context]

    # GTI toolset (conditional)

    if gti_enabled:
        gti_base = gti_gateway_url or gateway_base
        gti_url = f"{gti_base}/gti/{client_id}"
        gti_toolset = McpToolset(
            connection_params=build_mcp_connection(gti_url),
            tool_filter=GTI_ENRICHMENT_TOOLS,
            header_provider=build_mcp_auth_provider(gti_url),
        )
        tools.append(gti_toolset)

    base_instruction = ENRICHMENT_SYSTEM_PROMPT if gti_enabled else ENRICHMENT_SYSTEM_PROMPT_NO_GTI

    # ICM: Inject enrichment contract into system prompt
    enrichment_contract = get_enrichment_contract()
    instruction = (
        f"{base_instruction}\n\n"
        f"## STAGE CONTRACT\n{enrichment_contract}"
    )

    return LlmAgent(
        name=f"enrichment_agent_{safe_agent_name(client_id)}",
        model=model_id,
        description=(
            "Threat intelligence enrichment agent that queries GTI and Chronicle "
            "to enrich IoCs with reputation, malware families, and ATT&CK mappings."
        ),
        instruction=instruction,
        tools=tools,
        before_model_callback=before_model_callback,
    )


def build_enrichment_task(
    case_id: str,
    client_id: str,
    iocs: list[dict],  # [{"type": "IP", "value": "1.2.3.4"}, ...]
    alert_context: str = "",
) -> str:
    iocs_list = "\n".join(
        f"- {ioc.get('type', 'UNKNOWN')}: {ioc.get('value', '')}" for ioc in iocs
    )
    return ENRICHMENT_TASK_TEMPLATE.format(
        runbook_contract=get_enrichment_contract(),
        case_id=case_id,
        client_id=client_id,
        iocs_list=iocs_list or "No IoCs extracted — review alert manually.",
        alert_context=alert_context or "No additional context.",
    )
