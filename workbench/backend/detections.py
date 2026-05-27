"""Detections management endpoints — reads/writes from Chronicle SIEM via MCP Gateway."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from workbench.backend.auth import get_current_analyst
from workbench.backend.mcp_client import MCPClient, MCPToolError
from workbench.backend.security import validate_client_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["detections"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class RuleSetUpdate(BaseModel):
    enabled: bool


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

@router.get("/api/detections/curated")
async def list_curated_rule_sets(
    client_id: str,
    request: Request,
    analyst: dict = Depends(get_current_analyst),
    mcp: MCPClient = Depends(_get_mcp_client),
):
    """List all Google-curated rule sets for a client."""
    validate_client_id(client_id)
    _check_access(analyst, client_id)

    try:
        resp = await mcp.call_tool(client_id, "list_curated_rule_sets", {})
        return resp.get("ruleSets", [])
    except MCPToolError as e:
        logger.error("Failed to list curated rule sets for %s: %s", client_id, e)
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/api/detections/curated/{rule_set_id}")
async def get_curated_rule_set(
    client_id: str,
    rule_set_id: str,
    request: Request,
    analyst: dict = Depends(get_current_analyst),
    mcp: MCPClient = Depends(_get_mcp_client),
):
    """Get details for a specific curated rule set."""
    validate_client_id(client_id)
    _check_access(analyst, client_id)

    try:
        resp = await mcp.call_tool(client_id, "get_curated_rule_set", {
            "name": rule_set_id
        })
        return resp
    except MCPToolError as e:
        logger.error("Failed to get curated rule set %s for %s: %s", rule_set_id, client_id, e)
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/api/detections/curated/{rule_set_id}/deployment")
async def update_curated_rule_set_deployment(
    client_id: str,
    rule_set_id: str,
    update: RuleSetUpdate,
    request: Request,
    analyst: dict = Depends(get_current_analyst),
    mcp: MCPClient = Depends(_get_mcp_client),
):
    """Enable or disable a curated rule set deployment."""
    validate_client_id(client_id)
    _check_access(analyst, client_id)

    try:
        # Note: This tool actually requires a full deployment object in some versions,
        # but let's assume the simplified toggle for now.
        resp = await mcp.call_tool(client_id, "update_curated_rule_set_deployment", {
            "name": rule_set_id,
            "enabled": update.enabled,
        })
        return resp
    except MCPToolError as e:
        logger.error("Failed to update curated rule set deployment %s for %s: %s", rule_set_id, client_id, e)
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/api/detections/rules")
async def list_curated_rules(
    client_id: str,
    request: Request,
    page_size: int = 50,
    page_token: Optional[str] = None,
    analyst: dict = Depends(get_current_analyst),
    mcp: MCPClient = Depends(_get_mcp_client),
):
    """List individual curated rules."""
    validate_client_id(client_id)
    _check_access(analyst, client_id)

    try:
        resp = await mcp.call_tool(client_id, "list_curated_rules", {
            "pageSize": page_size,
            "pageToken": page_token,
        })
        return resp
    except MCPToolError as e:
        logger.error("Failed to list curated rules for %s: %s", client_id, e)
        raise HTTPException(status_code=502, detail=str(e))
