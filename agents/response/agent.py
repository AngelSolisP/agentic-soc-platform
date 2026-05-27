"""
Response Agent — Containment and remediation actions via Chronicle SOAR.

IMPORTANT: All actions in this agent require Human-in-the-Loop approval.
The agent proposes actions, submits them to the HITL queue, and only
executes upon explicit analyst approval.
"""

import os
import logging
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.cloud import firestore

from .prompts import RESPONSE_SYSTEM_PROMPT, RESPONSE_TASK_TEMPLATE
from agents.tool_catalog import RESPONSE_TOOLS
from agents.mcp_auth import build_mcp_connection, build_mcp_auth_provider
from agents.runbook_loader import get_response_contract
from agents.validation import safe_agent_name

logger = logging.getLogger(__name__)

# MCP tools that perform destructive/irreversible actions
_DESTRUCTIVE_TOOLS = frozenset({"execute_manual_action"})


def _hitl_guard(tool, args, tool_context):
    """
    Deterministic before_tool_callback that blocks destructive tool calls
    unless HITL approval has been granted.

    When approval_status is not APPROVED/MODIFIED, the tool call is intercepted
    and a dict is returned instead of executing the tool. This prevents prompt
    injection from bypassing HITL even if the LLM is compromised.
    """
    tool_name = getattr(tool, "name", "")
    if tool_name not in _DESTRUCTIVE_TOOLS:
        return None  # Allow non-destructive tools

    # Check approval status from session state (ADK ToolContext.state is always a State object)
    approval_status = tool_context.state.get("approval_status", "PENDING")

    if approval_status in ("APPROVED", "MODIFIED"):
        return None  # Allow — analyst has approved

    logger.warning(
        "HITL guard blocked destructive tool call",
        extra={
            "tool": tool_name,
            "approval_status": approval_status,
            "args_keys": list(args.keys()) if args else [],
        },
    )
    return {
        "error": "BLOCKED_BY_HITL_GUARD",
        "detail": (
            f"Tool '{tool_name}' requires HITL approval before execution. "
            f"Current approval_status: {approval_status}. "
            "Submit the proposed action to the HITL queue and wait for analyst approval."
        ),
    }


class HITLQueue:
    """
    Manages the Human-in-the-Loop approval queue using Firestore.

    Approval states: PENDING → APPROVED | REJECTED | MODIFIED
    """

    COLLECTION = "hitl_approvals"

    def __init__(self, partner_project_id: str, database: str = "(default)"):
        self._db = firestore.Client(
            project=partner_project_id, database=database
        )

    def submit_approval_request(
        self,
        client_id: str,
        case_id: str,
        agent_name: str,
        proposed_action: dict,
        triage_summary: str,
        session_id: Optional[str] = None,
        hitl_timeout_minutes: int = 30,
    ) -> str:
        """
        Submit a proposed action for human approval.

        Returns:
            approval_id: Unique ID to poll for approval status.
        """
        approval_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=hitl_timeout_minutes)
        doc = {
            "approval_id": approval_id,
            "client_id": client_id,
            "case_id": case_id,
            "agent_name": agent_name,
            "session_id": session_id,
            "status": "PENDING",
            "proposed_action": proposed_action,
            "triage_summary": triage_summary,
            "analyst_instructions": "",
            "created_at": now,
            "updated_at": now,
            "expires_at": expires_at,
            "decided_by": None,
            "decided_at": None,
        }
        self._db.collection(self.COLLECTION).document(approval_id).set(doc)
        logger.info(
            "HITL approval submitted",
            extra={
                "approval_id": approval_id,
                "client_id": client_id,
                "case_id": case_id,
                "action": proposed_action.get("proposed_action"),
                "expires_at": expires_at.isoformat(),
            },
        )
        return approval_id

    def get_approval_status(self, approval_id: str) -> dict:
        """Return the current approval document, marking expired if past TTL."""
        doc_ref = self._db.collection(self.COLLECTION).document(approval_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise KeyError(f"Approval '{approval_id}' not found")
        data = doc.to_dict()
        # Check expiry for PENDING approvals — persist to Firestore
        if data.get("status") == "PENDING" and data.get("expires_at"):
            raw_exp = data["expires_at"]
            if isinstance(raw_exp, datetime):
                expires_at = raw_exp
            else:
                expires_at = datetime.fromisoformat(str(raw_exp))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) >= expires_at:
                data["status"] = "EXPIRED"
                doc_ref.update({
                    "status": "EXPIRED",
                    "updated_at": datetime.now(timezone.utc),
                })
                logger.info(
                    "Approval expired and persisted",
                    extra={"approval_id": approval_id},
                )
        return data

    def list_pending(self, client_id: Optional[str] = None) -> list[dict]:
        """List all PENDING approvals, optionally filtered by client."""
        q = self._db.collection(self.COLLECTION).where("status", "==", "PENDING")
        if client_id:
            q = q.where("client_id", "==", client_id)
        return [doc.to_dict() for doc in q.stream()]


def create_response_agent(
    client_id: str,
    gateway_url: Optional[str] = None,
    model: Optional[str] = None,
    before_model_callback=None,
) -> LlmAgent:
    """
    Factory: create a Response Agent for a specific client.

    Uses Flash model by default for HITL proposals (cost optimization).
    Callers should pass model=Pro explicitly for execution passes.
    """
    gateway_base = gateway_url or os.environ.get(
        "MCP_GATEWAY_URL", "http://localhost:8080"
    )
    mcp_url = f"{gateway_base}/mcp/{client_id}"
    # Use Flash model for proposals, Pro only for execution — cost optimization
    model_id = model or os.environ.get("GEMINI_FLASH_MODEL", "gemini-2.5-flash")

    toolset = McpToolset(
        connection_params=build_mcp_connection(mcp_url),
        tool_filter=RESPONSE_TOOLS,
        header_provider=build_mcp_auth_provider(mcp_url),
    )

    # ICM: Inject response contract into system prompt
    response_contract = get_response_contract()
    instruction = (
        f"{RESPONSE_SYSTEM_PROMPT}\n\n"
        f"## STAGE CONTRACT\n{response_contract}"
    )

    return LlmAgent(
        name=f"response_agent_{safe_agent_name(client_id)}",
        model=model_id,
        description=(
            "Response agent that proposes and (upon human approval) executes "
            "containment actions: endpoint isolation, IP blocking, account disable."
        ),
        instruction=instruction,
        tools=[toolset],
        before_tool_callback=_hitl_guard,
        before_model_callback=before_model_callback,
    )


def build_response_task(
    case_id: str,
    client_id: str,
    approval_id: str,
    approval_status: str,
    triage_results: str,
    proposed_actions: str,
    analyst_instructions: str = "",
) -> str:
    return RESPONSE_TASK_TEMPLATE.format(
        case_id=case_id,
        client_id=client_id,
        approval_id=approval_id,
        approval_status=approval_status,
        triage_results=triage_results,
        proposed_actions=proposed_actions,
        analyst_instructions=analyst_instructions or "No modifications.",
    )
