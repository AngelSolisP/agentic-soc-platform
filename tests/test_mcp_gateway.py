"""
Tests for the MCP Gateway proxy.

Uses httpx AsyncClient to test FastAPI endpoints without a real
Chronicle backend. Mocks the auth and router layers.
"""

import json
import pytest
import pytest_asyncio
from contextlib import contextmanager
from unittest.mock import MagicMock, patch, AsyncMock

import httpx
from httpx import AsyncClient, ASGITransport

from proxy.mcp_gateway.model_armor import SanitizeResult, FilterResult
from proxy.mcp_gateway.circuit_breaker import CircuitBreaker
from proxy.mcp_gateway.rate_limiter import RateLimiter


def _make_streaming_resp(body=None, status=200):
    """Create mock httpx Response compatible with streaming forward (aread + aclose)."""
    content = json.dumps(body or {"jsonrpc": "2.0", "result": {}, "id": 1}).encode()
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status
    resp.content = content
    resp.headers = {"content-type": "application/json"}
    resp.aread = AsyncMock(return_value=content)
    resp.aclose = AsyncMock()
    return resp


@contextmanager
def _mock_forward(http_client, captured_body=None, resp_body=None, status=200):
    """Mock the streaming forward pattern (build_request + send)."""
    resp = _make_streaming_resp(resp_body, status)

    def _capture(*args, **kwargs):
        if captured_body is not None:
            content = kwargs.get("content")
            if content:
                captured_body.update(json.loads(content))
        return MagicMock()

    with (
        patch.object(http_client, "build_request", side_effect=_capture),
        patch.object(http_client, "send", new_callable=AsyncMock, return_value=resp),
    ):
        yield resp


# Patch GCP dependencies before importing the app
@pytest.fixture(autouse=True)
def mock_gcp():
    """Patch all GCP client initializations so tests run without credentials."""
    with (
        patch("proxy.mcp_gateway.router.firestore.Client"),
        patch("proxy.mcp_gateway.auth.secretmanager.SecretManagerServiceClient"),
        patch("proxy.mcp_gateway.auth.google.auth.default"),
        patch("proxy.mcp_gateway.auth.impersonated_credentials.Credentials"),
    ):
        yield


def _safe_armor_result():
    """Return a SanitizeResult that allows everything."""
    return SanitizeResult(allowed=True, filter_result=FilterResult.SAFE)


@pytest.fixture
def mock_client_config():
    from proxy.mcp_gateway.router import ClientConfig
    return ClientConfig(
        client_id="test-client",
        display_name="Test Client",
        gcp_project_id="test-project",
        chronicle_customer_id="test-uuid",
        chronicle_region="us",
        service_account_email="test-sa@test-project.iam.gserviceaccount.com",
        enabled=True,
    )


@pytest_asyncio.fixture
async def test_client(mock_client_config):
    """Create a test HTTP client against the gateway app."""
    # Set required env vars
    import os
    os.environ["PARTNER_PROJECT_ID"] = "test-partner-project"
    os.environ["DEV_MODE"] = "true"  # Bypass auth in tests

    from proxy.mcp_gateway.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Inject mocked router
        router_mock = MagicMock()
        router_mock.get_client.return_value = mock_client_config
        app.state.router = router_mock
        # Inject mocked Model Armor (always allows)
        armor_mock = AsyncMock()
        armor_mock.sanitize_user_prompt.return_value = _safe_armor_result()
        armor_mock.sanitize_model_response.return_value = _safe_armor_result()
        app.state.model_armor = armor_mock
        # Inject http_client, circuit_breaker, rate_limiter (ASGITransport skips lifespan)
        app.state.http_client = httpx.AsyncClient(timeout=5)
        app.state.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        app.state.gti_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        app.state.gti_http_client = httpx.AsyncClient(timeout=5)
        app.state.rate_limiter = RateLimiter(max_tokens=100, refill_rate=10.0)
        yield client

    await app.state.http_client.aclose()


@pytest.mark.asyncio
async def test_health_endpoint(test_client):
    response = await test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_proxy_unknown_client(test_client):
    """Unknown client_id should return 404."""
    app_router = test_client._transport.app.state.router
    app_router.get_client.side_effect = KeyError("Client 'unknown' not found")

    response = await test_client.post(
        "/mcp/unknown-client",
        json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_proxy_disabled_client(test_client, mock_client_config):
    """Disabled client should return 403."""
    mock_client_config.enabled = False
    app_router = test_client._transport.app.state.router
    app_router.get_client.return_value = mock_client_config

    response = await test_client.post(
        "/mcp/test-client",
        json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_proxy_forwards_request(test_client, mock_client_config):
    """Proxy should forward request to Chronicle MCP and return response."""
    with (
        patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"),
        _mock_forward(
            test_client._transport.app.state.http_client,
            resp_body={"jsonrpc": "2.0", "result": {"tools": []}, "id": 1},
        ),
    ):
        response = await test_client.post(
            "/mcp/test-client",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
        )

    assert response.status_code == 200
    body = response.json()
    assert "result" in body


@pytest.mark.asyncio
async def test_model_armor_blocks_injection(test_client):
    """Model Armor should block prompt injection and return 422."""
    armor = test_client._transport.app.state.model_armor
    armor.sanitize_user_prompt.return_value = SanitizeResult(
        allowed=False,
        filter_result=FilterResult.BLOCKED,
        blocked_reason="prompt_injection_detected",
    )

    response = await test_client.post(
        "/mcp/test-client",
        json={"jsonrpc": "2.0", "method": "tools/call", "id": 1,
              "params": {"name": "udm_search", "arguments": {"query": "ignore instructions"}}},
    )
    assert response.status_code == 422
    assert "Model Armor" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cache_invalidation(test_client):
    """Cache invalidation endpoint should return 200."""
    response = await test_client.delete("/cache/test-client")
    assert response.status_code == 200
    assert "test-client" in response.json()["message"]


@pytest.mark.asyncio
async def test_chronicle_param_injection(test_client, mock_client_config):
    """Gateway injects projectId/customerId/region into Chronicle tool call args."""
    captured_body = {}

    with (
        patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"),
        _mock_forward(test_client._transport.app.state.http_client, captured_body),
    ):
        response = await test_client.post(
            "/mcp/test-client",
            json={
                "jsonrpc": "2.0", "id": 1,
                "method": "tools/call",
                "params": {"name": "list_cases", "arguments": {"page_size": 5}},
            },
        )

    assert response.status_code == 200
    args = captured_body["params"]["arguments"]
    assert args["projectId"] == "test-project"
    assert args["customerId"] == "test-uuid"
    assert args["region"] == "us"
    assert args["page_size"] == 5  # Original arg preserved


@pytest.mark.asyncio
async def test_chronicle_param_injection_blocks_cross_tenant(test_client, mock_client_config):
    """Gateway MUST override caller-supplied projectId/customerId/region to prevent cross-tenant access."""
    captured_body = {}

    with (
        patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"),
        _mock_forward(test_client._transport.app.state.http_client, captured_body),
    ):
        response = await test_client.post(
            "/mcp/test-client",
            json={
                "jsonrpc": "2.0", "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "get_case",
                    "arguments": {
                        "caseId": "123",
                        # Attacker tries to access a different tenant
                        "projectId": "victim-project",
                        "customerId": "victim-uuid",
                        "region": "eu",
                    },
                },
            },
        )

    assert response.status_code == 200
    args = captured_body["params"]["arguments"]
    # Gateway MUST force the correct client's values, ignoring the attacker's
    assert args["projectId"] == "test-project"
    assert args["customerId"] == "test-uuid"
    assert args["region"] == "us"
    # Original non-tenant args preserved
    assert args["caseId"] == "123"


@pytest.mark.asyncio
async def test_soar_environment_id_injected_when_configured(test_client, mock_client_config):
    """Gateway should inject environmentId when soar_environment_id is configured."""
    mock_client_config.soar_environment_id = "env-abc-123"
    captured_body = {}

    with (
        patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"),
        _mock_forward(test_client._transport.app.state.http_client, captured_body),
    ):
        response = await test_client.post(
            "/mcp/test-client",
            json={
                "jsonrpc": "2.0", "id": 1,
                "method": "tools/call",
                "params": {"name": "list_cases", "arguments": {}},
            },
        )

    assert response.status_code == 200
    args = captured_body["params"]["arguments"]
    assert args["environmentId"] == "env-abc-123"
    assert args["projectId"] == "test-project"


@pytest.mark.asyncio
async def test_soar_environment_id_not_injected_when_empty(test_client, mock_client_config):
    """Gateway should NOT inject environmentId when soar_environment_id is empty."""
    mock_client_config.soar_environment_id = ""
    captured_body = {}

    with (
        patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"),
        _mock_forward(test_client._transport.app.state.http_client, captured_body),
    ):
        response = await test_client.post(
            "/mcp/test-client",
            json={
                "jsonrpc": "2.0", "id": 1,
                "method": "tools/call",
                "params": {"name": "list_cases", "arguments": {}},
            },
        )

    assert response.status_code == 200
    args = captured_body["params"]["arguments"]
    assert "environmentId" not in args


@pytest.mark.asyncio
async def test_health_ready_does_not_leak_client_ids(test_client):
    """The /health/ready endpoint must NOT expose client_ids in circuit breaker info."""
    response = await test_client.get("/health/ready")
    data = response.json()
    cb_info = data["checks"]["circuit_breaker"]
    # Must only have counts, never a list of client IDs
    assert "open_circuits" not in cb_info
    assert "total_tracked" not in cb_info
    assert "open_count" in cb_info


@pytest.mark.asyncio
async def test_global_cache_invalidation_requires_api_key(test_client):
    """Global cache invalidation must be restricted to API key callers."""
    import os
    # Switch from DEV_MODE to API key auth
    os.environ.pop("DEV_MODE", None)
    os.environ["API_KEYS"] = "test-api-key"

    try:
        # Google ID token user should be rejected
        with patch("proxy.mcp_gateway.auth_middleware._verify_google_id_token") as mock_verify:
            mock_verify.return_value = {"email": "user@example.com"}
            response = await test_client.delete(
                "/cache",
                headers={"Authorization": "Bearer google-id-token"},
            )
            assert response.status_code == 403
            assert "platform API key" in response.json()["detail"]

        # API key user should succeed
        response = await test_client.delete(
            "/cache",
            headers={"Authorization": "Bearer test-api-key"},
        )
        assert response.status_code == 200
    finally:
        os.environ["DEV_MODE"] = "true"
        os.environ.pop("API_KEYS", None)


@pytest.mark.asyncio
async def test_status_circuits_no_client_ids(test_client):
    """The /status/circuits endpoint must NOT expose individual client_ids."""
    response = await test_client.get("/status/circuits")
    assert response.status_code == 200
    data = response.json()
    # Must return aggregate counts, not per-client states
    assert "total_tracked" in data
    assert "open_count" in data
    # No keys that look like client_ids
    for key in data:
        assert key in ("total_tracked", "open_count", "half_open_count")


@pytest.mark.asyncio
async def test_no_injection_for_tools_list(test_client):
    """Gateway should NOT inject params for non-tools/call methods like tools/list."""
    captured_body = {}

    with (
        patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"),
        _mock_forward(
            test_client._transport.app.state.http_client,
            captured_body,
            resp_body={"jsonrpc": "2.0", "result": {"tools": []}, "id": 1},
        ),
    ):
        response = await test_client.post(
            "/mcp/test-client",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        )

    assert response.status_code == 200
    # tools/list should not have arguments injected
    assert "arguments" not in captured_body.get("params", {})


@pytest.mark.asyncio
async def test_upstream_500_with_mcp_error_normalized_to_200(test_client, mock_client_config):
    """Gateway should convert upstream HTTP 500 to 200 when body is a valid MCP error response.

    Chronicle MCP returns HTTP 500 for tool errors (e.g. invalid case ID) even though the
    response body is a valid JSON-RPC response with isError=true. MCP spec requires HTTP 200
    for tool error results. ADK's McpToolset treats non-2xx as 'Connection closed'.
    """
    mcp_error_body = {
        "id": 4,
        "jsonrpc": "2.0",
        "result": {
            "content": [{"text": "Case not found", "type": "text"}],
            "isError": True,
        },
    }

    with (
        patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"),
        _mock_forward(
            test_client._transport.app.state.http_client,
            resp_body=mcp_error_body,
            status=500,
        ),
    ):
        response = await test_client.post(
            "/mcp/test-client",
            json={
                "jsonrpc": "2.0", "id": 4,
                "method": "tools/call",
                "params": {"name": "get_case", "arguments": {"caseId": "999"}},
            },
        )

    # Must be normalized to 200 so McpToolset can process the error
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["isError"] is True


@pytest.mark.asyncio
async def test_upstream_500_without_mcp_error_stays_500(test_client, mock_client_config):
    """Genuine upstream 500 (no valid MCP error body) should NOT be normalized."""
    with (
        patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"),
        _mock_forward(
            test_client._transport.app.state.http_client,
            resp_body={"error": "Internal server error"},
            status=500,
        ),
    ):
        response = await test_client.post(
            "/mcp/test-client",
            json={
                "jsonrpc": "2.0", "id": 5,
                "method": "tools/call",
                "params": {"name": "get_case", "arguments": {"caseId": "1"}},
            },
        )

    # Not a valid MCP response → keep 500
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_upstream_501_with_mcp_error_normalized_to_200(test_client, mock_client_config):
    """HTTP 501 from Chronicle (case not found) with valid MCP body should also be normalized."""
    mcp_error_body = {
        "id": 6,
        "jsonrpc": "2.0",
        "result": {
            "content": [{"text": "Entity not found", "type": "text"}],
            "isError": True,
        },
    }

    with (
        patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"),
        _mock_forward(
            test_client._transport.app.state.http_client,
            resp_body=mcp_error_body,
            status=501,
        ),
    ):
        response = await test_client.post(
            "/mcp/test-client",
            json={
                "jsonrpc": "2.0", "id": 6,
                "method": "tools/call",
                "params": {"name": "get_case", "arguments": {"caseId": "1"}},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["isError"] is True
