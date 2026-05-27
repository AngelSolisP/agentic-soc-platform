"""Lightweight MCP client for calling tools through the MCP Gateway.

Auth: In Cloud Run (K_SERVICE set), obtains a Google OIDC identity token
for the gateway URL. In local dev, falls back to MCP_GATEWAY_API_KEY.

Session caching: Per MCP spec (2025-03-26), a client can reuse
mcp-session-id across multiple tools/call requests after a single
initialize. Sessions are cached per client_id. If the server returns
HTTP 404 (session expired), the client re-initializes automatically.

Retry: Transient errors (timeout, connection reset) are retried once.
Business logic errors (4xx from the tool) are NOT retried.
"""
import json
import logging
import os
import time
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# Identity token cache: {audience: (token, expiry_timestamp)}
_id_token_cache: dict[str, tuple[str, float]] = {}
_TOKEN_BUFFER_SECONDS = 120


def _fetch_id_token(audience: str) -> str:
    """Fetch a Google OIDC identity token for the given audience."""
    import google.auth.transport.requests
    import google.oauth2.id_token

    request = google.auth.transport.requests.Request()
    return google.oauth2.id_token.fetch_id_token(request, audience)


def _get_id_token(audience: str) -> str:
    """Get a cached or fresh identity token."""
    cached = _id_token_cache.get(audience)
    if cached and time.time() < cached[1] - _TOKEN_BUFFER_SECONDS:
        return cached[0]

    token = _fetch_id_token(audience)
    _id_token_cache[audience] = (token, time.time() + 3600)
    return token


class MCPToolError(Exception):
    def __init__(self, tool_name: str, detail: Any):
        self.tool_name = tool_name
        self.detail = detail
        super().__init__(f"MCP tool '{tool_name}' error: {detail}")


# Transient errors that should be retried
_RETRYABLE_ERRORS = (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError)


class MCPClient:
    """MCP client with session caching and automatic retry."""

    def __init__(
        self,
        gateway_url: str,
        http_client: httpx.AsyncClient,
        auth_token: str = "",
    ):
        self._gateway_url = gateway_url.rstrip("/")
        self._http = http_client
        self._auth_token = auth_token or os.environ.get("MCP_GATEWAY_API_KEY", "")
        self._use_id_token = bool(os.environ.get("K_SERVICE"))
        # Session cache: {client_id: mcp-session-id}
        self._sessions: dict[str, str] = {}

    async def call_tool(
        self, client_id: str, tool_name: str, arguments: Optional[dict] = None
    ) -> dict:
        """Call an MCP tool with session reuse and 1 automatic retry."""
        try:
            return await self._call_tool_inner(client_id, tool_name, arguments)
        except _RETRYABLE_ERRORS as e:
            logger.warning("MCP transient error, retrying: %s", e)
            # Clear cached session — may be stale after timeout
            self._sessions.pop(client_id, None)
            return await self._call_tool_inner(client_id, tool_name, arguments)

    async def _call_tool_inner(
        self, client_id: str, tool_name: str, arguments: Optional[dict] = None
    ) -> dict:
        url = f"{self._gateway_url}/mcp/{client_id}"
        headers = self._build_headers()

        # Try with cached session first (skip initialize)
        session_id = self._sessions.get(client_id)
        if session_id:
            headers["mcp-session-id"] = session_id
            call_resp = await self._post_tool_call(url, headers, tool_name, arguments)

            # MCP spec: 404 = session expired → re-initialize
            if call_resp.status_code == 404:
                logger.info("MCP session expired for %s, re-initializing", client_id)
                self._sessions.pop(client_id, None)
                del headers["mcp-session-id"]
            else:
                call_resp.raise_for_status()
                return self._parse_result(tool_name, call_resp.json())

        # Initialize new session
        init_body = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "soc-workbench", "version": "1.0.0"},
            },
            "id": 1,
        }
        init_resp = await self._http.post(url, json=init_body, headers=headers)
        init_resp.raise_for_status()

        new_session_id = init_resp.headers.get("mcp-session-id")
        if new_session_id:
            headers["mcp-session-id"] = new_session_id
            self._sessions[client_id] = new_session_id

        # Call tool
        call_resp = await self._post_tool_call(url, headers, tool_name, arguments)
        call_resp.raise_for_status()

        return self._parse_result(tool_name, call_resp.json())

    async def _post_tool_call(
        self,
        url: str,
        headers: dict,
        tool_name: str,
        arguments: Optional[dict],
    ) -> httpx.Response:
        call_body = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments or {}},
            "id": 2,
        }
        return await self._http.post(url, json=call_body, headers=headers)

    def _build_headers(self) -> dict:
        if self._use_id_token:
            parsed = urlparse(self._gateway_url)
            audience = f"{parsed.scheme}://{parsed.netloc}"
            token = _get_id_token(audience)
        else:
            token = self._auth_token
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

    def _parse_result(self, tool_name: str, rpc_response: dict) -> dict:
        if "error" in rpc_response:
            raise MCPToolError(tool_name, rpc_response["error"])

        tool_result = rpc_response.get("result", {})

        if tool_result.get("isError"):
            content = tool_result.get("content", [])
            detail = content[0].get("text", "Unknown error") if content else "Unknown error"
            raise MCPToolError(tool_name, detail)

        content = tool_result.get("content", [])
        if content and isinstance(content[0], dict):
            text = content[0].get("text", "")
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return {"text": text}

        return tool_result
