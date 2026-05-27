"""Tests that MCP Gateway creates OTel spans for key operations."""
import os
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from httpx import ASGITransport, AsyncClient

from proxy.mcp_gateway.circuit_breaker import CircuitBreaker
from proxy.mcp_gateway.rate_limiter import RateLimiter
from proxy.mcp_gateway.model_armor import SanitizeResult, FilterResult
from proxy.mcp_gateway.router import ClientConfig


@pytest.fixture(autouse=True)
def _reset_otel():
    """Reset OTel global state between tests.

    OTel SDK >=1.38 uses a Once guard that prevents set_tracer_provider
    from being called more than once. We reset that guard plus the
    cached provider so each test starts with a clean slate.
    Also reset observability.tracing._initialized so init_tracing can
    run again in subsequent tests after module-level calls (e.g. the
    HITL backend calls init_tracing at import time).
    """
    import observability.tracing as _tracing_mod
    trace._TRACER_PROVIDER_SET_ONCE._done = False
    trace._TRACER_PROVIDER = None
    _tracing_mod._initialized = False
    yield
    trace._TRACER_PROVIDER_SET_ONCE._done = False
    trace._TRACER_PROVIDER = None
    _tracing_mod._initialized = False


@pytest.fixture()
def memory_exporter():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return exporter


def _safe_armor_result():
    return SanitizeResult(allowed=True, filter_result=FilterResult.SAFE)


def _make_app_with_state():
    """Build a test app with mocked state dependencies.

    Uses the same patterns as tests/integration/conftest.py:
    - DEV_MODE=true to bypass auth
    - Manual app.state injection (ASGITransport skips lifespan)
    """
    os.environ["DEV_MODE"] = "true"
    os.environ["PARTNER_PROJECT_ID"] = "test-partner-project"

    from proxy.mcp_gateway.main import app

    config = ClientConfig(
        client_id="test-client",
        display_name="Test Client",
        gcp_project_id="test-project",
        chronicle_customer_id="abc-123",
        chronicle_region="us",
        service_account_email="sa@test-project.iam.gserviceaccount.com",
        enabled=True,
        gti_enabled=False,
    )

    router_mock = MagicMock()
    router_mock.get_client.return_value = config

    # Mock upstream response (streaming: build_request + send)
    upstream_resp = MagicMock()
    upstream_resp.status_code = 200
    upstream_resp.content = json.dumps({"result": "ok"}).encode()
    upstream_resp.headers = {"content-type": "application/json"}
    upstream_resp.aread = AsyncMock(return_value=upstream_resp.content)
    upstream_resp.aclose = AsyncMock()

    http_client_mock = AsyncMock()
    http_client_mock.send.return_value = upstream_resp

    armor_mock = AsyncMock()
    armor_mock.sanitize_user_prompt.return_value = _safe_armor_result()
    armor_mock.sanitize_model_response.return_value = _safe_armor_result()

    app.state.router = router_mock
    app.state.http_client = http_client_mock
    app.state.model_armor = armor_mock
    app.state.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
    app.state.rate_limiter = RateLimiter(max_tokens=100, refill_rate=10.0)
    app.state.gti_http_client = AsyncMock()
    app.state.gti_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

    return app


async def _send_mcp_request(app, path="/mcp/test-client", body=None):
    """Send a test MCP request through the gateway."""
    if body is None:
        body = {"method": "list_cases", "params": {}}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=body)


@pytest.fixture(autouse=True)
def _mock_gcp():
    """Patch GCP clients so tests run without credentials."""
    with (
        patch("proxy.mcp_gateway.router.firestore.Client"),
        patch("proxy.mcp_gateway.auth.secretmanager.SecretManagerServiceClient"),
        patch("proxy.mcp_gateway.auth.google.auth.default"),
        patch("proxy.mcp_gateway.auth.impersonated_credentials.Credentials"),
    ):
        yield


@pytest.mark.asyncio
@pytest.mark.mock
class TestGatewayTracing:
    async def test_proxy_request_creates_root_span(self, memory_exporter):
        """_proxy_request should create a gateway.proxy_request span."""
        app = _make_app_with_state()
        with patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"):
            resp = await _send_mcp_request(app)
        assert resp.status_code == 200
        spans = memory_exporter.get_finished_spans()
        span_names = [s.name for s in spans]
        assert any("gateway.proxy_request" in name for name in span_names)

    async def test_proxy_span_has_client_id_attribute(self, memory_exporter):
        """The gateway.proxy_request span must carry client.id and mcp.method."""
        app = _make_app_with_state()
        with patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"):
            await _send_mcp_request(app)
        spans = memory_exporter.get_finished_spans()
        proxy_span = next((s for s in spans if s.name == "gateway.proxy_request"), None)
        assert proxy_span is not None
        assert proxy_span.attributes.get("client.id") == "test-client"
        assert proxy_span.attributes.get("mcp.method") == "list_cases"

    async def test_proxy_span_has_backend_attribute(self, memory_exporter):
        """The gateway.proxy_request span must carry backend.name."""
        app = _make_app_with_state()
        with patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"):
            await _send_mcp_request(app)
        spans = memory_exporter.get_finished_spans()
        proxy_span = next((s for s in spans if s.name == "gateway.proxy_request"), None)
        assert proxy_span is not None
        assert proxy_span.attributes.get("backend.name") == "chronicle"

    async def test_child_spans_created(self, memory_exporter):
        """Key child spans should be created within the proxy request.

        Uses tools/call so that Model Armor spans are created (protocol
        methods like list_cases skip Model Armor per Google docs).
        """
        app = _make_app_with_state()
        tools_call_body = {
            "method": "tools/call",
            "params": {"name": "list_cases", "arguments": {"filter": "Status='OPENED'"}},
        }
        with patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"):
            await _send_mcp_request(app, body=tools_call_body)
        spans = memory_exporter.get_finished_spans()
        span_names = {s.name for s in spans}
        assert "gateway.model_armor.input" in span_names
        assert "gateway.auth.resolve" in span_names
        assert "gateway.forward" in span_names

    async def test_agent_id_and_session_id_on_span(self, memory_exporter):
        """agent.id and session.id should appear when headers are provided."""
        app = _make_app_with_state()
        with patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.post(
                    "/mcp/test-client",
                    json={"method": "list_cases", "params": {}},
                    headers={
                        "X-Agent-Id": "enrichment-agent",
                        "X-Session-Id": "sess-abc-123",
                    },
                )
        spans = memory_exporter.get_finished_spans()
        proxy_span = next((s for s in spans if s.name == "gateway.proxy_request"), None)
        assert proxy_span is not None
        assert proxy_span.attributes.get("agent.id") == "enrichment-agent"
        assert proxy_span.attributes.get("session.id") == "sess-abc-123"
