import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import httpx

from workbench.backend.mcp_client import MCPClient, MCPToolError


@pytest.fixture
def mock_http():
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def mcp_client(mock_http):
    return MCPClient(
        gateway_url="http://gateway:8080",
        http_client=mock_http,
        auth_token="test-key",
    )


def _make_response(body: dict, status=200):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status
    resp.json.return_value = body
    resp.raise_for_status = MagicMock()
    if status >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp
        )
    return resp


@pytest.mark.asyncio
async def test_call_tool_success(mcp_client, mock_http):
    init_resp = _make_response({
        "jsonrpc": "2.0",
        "result": {"protocolVersion": "2025-03-26", "capabilities": {}},
        "id": 1,
    })
    init_resp.headers = {}

    tool_resp = _make_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps({"cases": [{"id": "1"}]})}]
        },
        "id": 2,
    })

    mock_http.post = AsyncMock(side_effect=[init_resp, tool_resp])

    result = await mcp_client.call_tool("client-a", "list_cases", {"Status": "OPENED"})
    assert result == {"cases": [{"id": "1"}]}
    assert mock_http.post.call_count == 2

    first_call_url = mock_http.post.call_args_list[0][0][0]
    assert first_call_url == "http://gateway:8080/mcp/client-a"


@pytest.mark.asyncio
async def test_call_tool_mcp_error(mcp_client, mock_http):
    init_resp = _make_response({
        "jsonrpc": "2.0",
        "result": {"protocolVersion": "2025-03-26"},
        "id": 1,
    })
    init_resp.headers = {}

    error_resp = _make_response({
        "jsonrpc": "2.0",
        "error": {"code": -32600, "message": "Case not found"},
        "id": 2,
    })

    mock_http.post = AsyncMock(side_effect=[init_resp, error_resp])

    with pytest.raises(MCPToolError) as exc_info:
        await mcp_client.call_tool("client-a", "get_case", {"caseId": "999"})
    assert "Case not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_call_tool_plain_text_response(mcp_client, mock_http):
    init_resp = _make_response({
        "jsonrpc": "2.0",
        "result": {"protocolVersion": "2025-03-26"},
        "id": 1,
    })
    init_resp.headers = {}

    tool_resp = _make_response({
        "jsonrpc": "2.0",
        "result": {"content": [{"type": "text", "text": "No cases found"}]},
        "id": 2,
    })

    mock_http.post = AsyncMock(side_effect=[init_resp, tool_resp])

    result = await mcp_client.call_tool("client-a", "list_cases", {})
    assert result == {"text": "No cases found"}


@pytest.mark.asyncio
async def test_call_tool_session_id_forwarded(mcp_client, mock_http):
    init_resp = _make_response({
        "jsonrpc": "2.0",
        "result": {"protocolVersion": "2025-03-26"},
        "id": 1,
    })
    init_resp.headers = {"mcp-session-id": "sess-123"}

    tool_resp = _make_response({
        "jsonrpc": "2.0",
        "result": {"content": [{"type": "text", "text": "{}"}]},
        "id": 2,
    })

    mock_http.post = AsyncMock(side_effect=[init_resp, tool_resp])

    await mcp_client.call_tool("client-a", "list_cases", {})

    second_call_headers = mock_http.post.call_args_list[1][1]["headers"]
    assert second_call_headers.get("mcp-session-id") == "sess-123"


@pytest.mark.asyncio
async def test_call_tool_http_error(mcp_client, mock_http):
    mock_http.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(httpx.ConnectError):
        await mcp_client.call_tool("client-a", "list_cases", {})


@pytest.mark.asyncio
async def test_call_tool_isError_response(mcp_client, mock_http):
    init_resp = _make_response({
        "jsonrpc": "2.0",
        "result": {"protocolVersion": "2025-03-26"},
        "id": 1,
    })
    init_resp.headers = {}

    tool_resp = _make_response({
        "jsonrpc": "2.0",
        "result": {
            "isError": True,
            "content": [{"type": "text", "text": "Invalid case ID"}],
        },
        "id": 2,
    })

    mock_http.post = AsyncMock(side_effect=[init_resp, tool_resp])

    with pytest.raises(MCPToolError) as exc_info:
        await mcp_client.call_tool("client-a", "get_case", {"caseId": "bad"})
    assert "Invalid case ID" in str(exc_info.value)
