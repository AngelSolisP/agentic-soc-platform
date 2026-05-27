"""Watchlist management endpoints — reads/writes from Chronicle SIEM via MCP Gateway."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from workbench.backend.auth import get_current_analyst
from workbench.backend.mcp_client import MCPClient, MCPToolError
from workbench.backend.security import validate_client_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["watchlists"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class WatchlistCreate(BaseModel):
    name: str
    description: str
    entity_type: str  # USER, HOST, IP, DOMAIN
    entities: list[str] = []


class WatchlistUpdate(BaseModel):
    description: Optional[str] = None
    entities_to_add: list[str] = []
    entities_to_remove: list[str] = []


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

@router.get("/api/watchlists")
async def list_watchlists(
    client_id: str,
    request: Request,
    analyst: dict = Depends(get_current_analyst),
    mcp: MCPClient = Depends(_get_mcp_client),
):
    """List all watchlists for a client."""
    validate_client_id(client_id)
    _check_access(analyst, client_id)

    try:
        resp = await mcp.call_tool(client_id, "list_watchlists", {})
        return resp.get("watchlists", [])
    except MCPToolError as e:
        logger.error("Failed to list watchlists for %s: %s", client_id, e)
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/api/watchlists/{watchlist_id}")
async def get_watchlist(
    client_id: str,
    watchlist_id: str,
    request: Request,
    analyst: dict = Depends(get_current_analyst),
    mcp: MCPClient = Depends(_get_mcp_client),
):
    """Get details for a specific watchlist."""
    validate_client_id(client_id)
    _check_access(analyst, client_id)

    try:
        resp = await mcp.call_tool(client_id, "get_watchlist", {"name": watchlist_id})
        return resp
    except MCPToolError as e:
        logger.error("Failed to get watchlist %s for %s: %s", watchlist_id, client_id, e)
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/api/watchlists")
async def create_watchlist(
    client_id: str,
    watchlist: WatchlistCreate,
    request: Request,
    analyst: dict = Depends(get_current_analyst),
    mcp: MCPClient = Depends(_get_mcp_client),
):
    """Create a new watchlist."""
    validate_client_id(client_id)
    _check_access(analyst, client_id)

    try:
        resp = await mcp.call_tool(client_id, "create_watchlist", {
            "name": watchlist.name,
            "description": watchlist.description,
            "entityType": watchlist.entity_type,
            "entities": watchlist.entities,
        })
        return resp
    except MCPToolError as e:
        logger.error("Failed to create watchlist for %s: %s", client_id, e)
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/api/watchlists/{watchlist_id}")
async def update_watchlist(
    client_id: str,
    watchlist_id: str,
    update: WatchlistUpdate,
    request: Request,
    analyst: dict = Depends(get_current_analyst),
    mcp: MCPClient = Depends(_get_mcp_client),
):
    """Update an existing watchlist."""
    validate_client_id(client_id)
    _check_access(analyst, client_id)

    try:
        resp = await mcp.call_tool(client_id, "update_watchlist", {
            "name": watchlist_id,
            "description": update.description,
            "entitiesToAdd": update.entities_to_add,
            "entitiesToRemove": update.entities_to_remove,
        })
        return resp
    except MCPToolError as e:
        logger.error("Failed to update watchlist %s for %s: %s", watchlist_id, client_id, e)
        raise HTTPException(status_code=502, detail=str(e))
