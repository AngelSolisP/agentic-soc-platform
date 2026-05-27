"""
Agent Card builder for the Agentic SOC orchestrator.

Builds a custom AgentCard (not auto-generated) to avoid leaking the system
prompt and to provide domain-specific SOC skill descriptions for clients.
"""

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    AgentSkill,
    HTTPAuthSecurityScheme,
    SecurityScheme,
)


def build_agent_card(rpc_url: str) -> AgentCard:
    """Build the Agentic SOC Agent Card with SOC-specific skills.

    Args:
        rpc_url: The A2A JSON-RPC endpoint URL (Cloud Run service URL).

    Returns:
        AgentCard with 4 SOC skills and bearer auth.
    """
    return AgentCard(
        name="agentic-soc-orchestrator",
        description=(
            "MSSP SOC Orchestrator — automated security alert triage, "
            "enrichment, case management, and response coordination "
            "for Google Chronicle SecOps tenants."
        ),
        url=rpc_url,
        version="1.0.0",
        capabilities=AgentCapabilities(
            streaming=False,
            pushNotifications=False,
        ),
        skills=[
            AgentSkill(
                id="alert-triage",
                name="Security Alert Triage",
                description=(
                    "Analyzes security alerts from Chronicle SIEM/SOAR. "
                    "Returns verdict (MALICIOUS/SUSPICIOUS/BENIGN/INCONCLUSIVE), "
                    "priority (INFORMATIVE to CRITICAL), and confidence score."
                ),
                tags=["security", "triage", "soc", "chronicle"],
                examples=[
                    "Triage PHISHING alert for case 12345",
                    "Analyze MALWARE detection with HIGH severity",
                ],
            ),
            AgentSkill(
                id="ioc-enrichment",
                name="IoC Enrichment",
                description=(
                    "Enriches indicators of compromise via Google Threat "
                    "Intelligence (GTI) and Chronicle entity analysis. "
                    "Supports IPs, domains, URLs, file hashes, and user entities."
                ),
                tags=["security", "enrichment", "gti", "chronicle", "ioc"],
                examples=[
                    "Enrich suspicious IP 203.0.113.42",
                    "Look up file hash in GTI and Chronicle",
                ],
            ),
            AgentSkill(
                id="case-management",
                name="SOAR Case Management",
                description=(
                    "Manages cases in Chronicle SOAR: update priority, "
                    "add comments, escalate to Tier 2, close with disposition. "
                    "Supports bulk operations and playbook integration."
                ),
                tags=["security", "soar", "case-management", "chronicle"],
                examples=[
                    "Close case 12345 as false positive",
                    "Escalate case to Tier 2 with enrichment findings",
                ],
            ),
            AgentSkill(
                id="containment-response",
                name="Containment Response (HITL)",
                description=(
                    "Executes containment actions: host isolation, IP/domain "
                    "blocking, account disable, credential revocation. "
                    "All actions require human-in-the-loop approval."
                ),
                tags=["security", "response", "containment", "hitl"],
                examples=[
                    "Isolate compromised endpoint",
                    "Block malicious domain across perimeter",
                ],
            ),
        ],
        securitySchemes={
            "bearer": SecurityScheme(
                root=HTTPAuthSecurityScheme(
                    scheme="bearer",
                    bearerFormat="JWT",
                    description=(
                        "Google Cloud Identity Token (OIDC) or API key "
                        "for the Agentic SOC platform."
                    ),
                )
            ),
        },
        security=[{"bearer": []}],
        defaultInputModes=["text/plain", "application/json"],
        defaultOutputModes=["text/plain", "application/json"],
        provider=AgentProvider(
            organization="Agentic SOC MSSP Platform",
            url=rpc_url,
        ),
    )
