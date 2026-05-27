"""Investigation chat endpoint — conversational SOC analysis via Agent Engine."""
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from workbench.backend.auth import get_current_analyst
from workbench.backend.audit import AuditAction
from workbench.backend.security import validate_client_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    client_id: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    tool_calls: list[dict] = []
    session_id: Optional[str] = None


@router.post("/cases/{case_id}/chat", response_model=ChatResponse)
async def send_chat_message(
    case_id: str,
    body: ChatRequest,
    request: Request,
    analyst: dict = Depends(get_current_analyst),
):
    validate_client_id(body.client_id)
    allowed = analyst.get("allowed_clients", [])
    if analyst.get("role") != "admin" and body.client_id not in allowed:
        raise HTTPException(403, "Not authorized for this client")

    result = await _query_agent(
        client_id=body.client_id,
        case_id=case_id,
        message=body.message,
        session_id=body.session_id,
    )

    audit = request.app.state.audit
    audit.log(
        actor=analyst["email"],
        actor_type=analyst.get("role", "analyst"),
        action=AuditAction.CHAT_MESSAGE,
        client_id=body.client_id,
        case_id=case_id,
        details={"message_preview": body.message[:100]},
    )

    return ChatResponse(
        response=result.get("response", ""),
        tool_calls=result.get("tool_calls", []),
        session_id=result.get("session_id"),
    )


async def _query_agent(
    client_id: str,
    case_id: str,
    message: str,
    session_id: Optional[str] = None,
) -> dict:
    agent_engine_id = os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID")

    if agent_engine_id:
        from vertexai import agent_engines  # type: ignore

        engine = agent_engines.get(agent_engine_id)
        result = engine.query(
            input={
                "client_id": client_id,
                "case_id": case_id,
                "message": message,
                "mode": "investigation",
                "session_id": session_id,
            }
        )
        return result if isinstance(result, dict) else {"response": str(result)}

    return {
        "response": f"[Local mode] Received investigation query for case {case_id}: {message}",
        "tool_calls": [],
        "session_id": session_id,
    }
