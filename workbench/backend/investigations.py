"""Investigation management endpoints — reads from Chronicle SIEM via MCP Gateway."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from workbench.backend.auth import get_current_analyst
from workbench.backend.mcp_client import MCPClient, MCPToolError
from workbench.backend.security import validate_client_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["investigations"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_mcp_client(request: Request) -> MCPClient:
    if hasattr(request.app.state, "mcp_client") and request.app.state.mcp_client:
        return request.app.state.mcp_client
    client = MCPClient(
        gateway_url=request.app.state.mcp_gateway_url,
        http_client=request.app.state.http_client,
    )
    request.app.state.mcp_client = client
    return client


def _check_access(analyst: dict, client_id: str):
    allowed = analyst.get("allowed_clients", [])
    if analyst.get("role") == "admin":
        return
    if client_id not in allowed:
        raise HTTPException(status_code=403, detail="Not authorized for this client")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/api/investigations")
async def list_investigations(
    client_id: str,
    request: Request,
    page_size: int = 20,
    page_token: Optional[str] = None,
    analyst: dict = Depends(get_current_analyst),
    mcp: MCPClient = Depends(_get_mcp_client),
):
    """List Gemini TIN investigations for a client."""
    validate_client_id(client_id)
    _check_access(analyst, client_id)

    try:
        resp = await mcp.call_tool(client_id, "list_investigations", {
            "pageSize": page_size,
            "pageToken": page_token,
        })
        return resp
    except MCPToolError as e:
        logger.error("Failed to list investigations for %s: %s", client_id, e)
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/api/investigations/{investigation_id}")
async def get_investigation(
    client_id: str,
    investigation_id: str,
    request: Request,
    analyst: dict = Depends(get_current_analyst),
    mcp: MCPClient = Depends(_get_mcp_client),
):
    """Get details for a specific Gemini TIN investigation."""
    validate_client_id(client_id)
    _check_access(analyst, client_id)

    try:
        resp = await mcp.call_tool(client_id, "get_investigation", {
            "investigationId": investigation_id
        })
        return resp
    except MCPToolError as e:
        logger.error("Failed to get investigation %s for %s: %s", investigation_id, client_id, e)
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/api/investigations/trigger")
async def trigger_investigation(
    client_id: str,
    alert_id: str,
    request: Request,
    analyst: dict = Depends(get_current_analyst),
    mcp: MCPClient = Depends(_get_mcp_client),
):
    """Trigger a new Gemini TIN investigation for an alert."""
    validate_client_id(client_id)
    _check_access(analyst, client_id)

    try:
        resp = await mcp.call_tool(client_id, "trigger_investigation", {
            "alertId": alert_id
        })
        return resp
    except MCPToolError as e:
        logger.error("Failed to trigger investigation for alert %s in %s: %s", alert_id, client_id, e)
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/api/investigations/alerts/{siem_alert_id}")
async def get_alert_investigation(
    client_id: str,
    siem_alert_id: str,
    request: Request,
    analyst: dict = Depends(get_current_analyst),
    mcp: MCPClient = Depends(_get_mcp_client),
):
    """Get the latest investigation for a specific SIEM alert."""
    validate_client_id(client_id)
    _check_access(analyst, client_id)

    try:
        resp = await mcp.call_tool(client_id, "get_alert_latest_investigation", {
            "alertId": siem_alert_id
        })
        return resp
    except MCPToolError as e:
        logger.error("Failed to get latest investigation for alert %s in %s: %s", siem_alert_id, client_id, e)
        raise HTTPException(status_code=502, detail=str(e))
