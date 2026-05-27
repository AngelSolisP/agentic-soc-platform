"""Tests for W3C traceparent header propagation."""

import os
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


@pytest.fixture(autouse=True)
def _reset_otel():
    """Reset OTel global state between tests."""
    import observability.tracing as _tracing_mod
    from opentelemetry import propagate
    from opentelemetry.propagators.composite import CompositePropagator

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


class TestTraceContextPropagator:
    """init_tracing should configure W3C TraceContext propagator."""

    def test_propagator_fields_include_traceparent(self):
        """After init_tracing, global propagator should include traceparent."""
        from opentelemetry import propagate
        import observability.tracing as mod

        mod._initialized = False
        with patch.dict(os.environ, {"OTEL_EXPORTER_TYPE": "console"}, clear=False):
            mod.init_tracing("test-svc")

        propagator = propagate.get_global_textmap()
        assert "traceparent" in propagator.fields

    def test_propagator_fields_include_baggage(self):
        """After init_tracing, global propagator should include baggage."""
        from opentelemetry import propagate
        import observability.tracing as mod

        mod._initialized = False
        with patch.dict(os.environ, {"OTEL_EXPORTER_TYPE": "console"}, clear=False):
            mod.init_tracing("test-svc")

        propagator = propagate.get_global_textmap()
        assert "baggage" in propagator.fields

    def test_inject_produces_traceparent_header(self):
        """propagate.inject() should add traceparent to carrier dict."""
        from opentelemetry import propagate
        from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
        from opentelemetry.propagate import set_global_textmap

        provider = TracerProvider()
        trace.set_tracer_provider(provider)
        set_global_textmap(TraceContextTextMapPropagator())

        tracer = trace.get_tracer("test")
        with tracer.start_as_current_span("test-span"):
            carrier = {}
            propagate.inject(carrier)
            assert "traceparent" in carrier
            assert carrier["traceparent"].startswith("00-")

    def test_extract_creates_context_with_trace_id(self):
        """propagate.extract() should parse traceparent into context."""
        from opentelemetry import propagate
        from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
        from opentelemetry.propagate import set_global_textmap

        set_global_textmap(TraceContextTextMapPropagator())

        carrier = {
            "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        }
        ctx = propagate.extract(carrier)
        span_ctx = trace.get_current_span(ctx).get_span_context()
        assert span_ctx.trace_id == int("0af7651916cd43dd8448eb211c80319c", 16)


class TestGatewayCorsHeaders:
    """Gateway CORS should allow traceparent headers."""

    def test_cors_allows_traceparent(self):
        from proxy.mcp_gateway.main import app

        cors_middleware = None
        for m in app.user_middleware:
            if "CORSMiddleware" in str(m.cls):
                cors_middleware = m
                break
        assert cors_middleware is not None
        assert "traceparent" in cors_middleware.kwargs.get("allow_headers", [])

    def test_cors_allows_tracestate(self):
        from proxy.mcp_gateway.main import app

        cors_middleware = None
        for m in app.user_middleware:
            if "CORSMiddleware" in str(m.cls):
                cors_middleware = m
                break
        assert cors_middleware is not None
        assert "tracestate" in cors_middleware.kwargs.get("allow_headers", [])

    def test_hitl_cors_allows_traceparent(self):
        from ui.hitl_dashboard.backend.main import app

        cors_middleware = None
        for m in app.user_middleware:
            if "CORSMiddleware" in str(m.cls):
                cors_middleware = m
                break
        assert cors_middleware is not None
        assert "traceparent" in cors_middleware.kwargs.get("allow_headers", [])

    def test_hitl_cors_allows_tracestate(self):
        from ui.hitl_dashboard.backend.main import app

        cors_middleware = None
        for m in app.user_middleware:
            if "CORSMiddleware" in str(m.cls):
                cors_middleware = m
                break
        assert cors_middleware is not None
        assert "tracestate" in cors_middleware.kwargs.get("allow_headers", [])


class TestGatewayTraceparentPropagation:
    """Gateway should extract incoming traceparent and inject into outgoing headers."""

    @pytest.fixture(autouse=True)
    def _mock_gcp(self):
        """Patch GCP clients so tests run without credentials."""
        with (
            patch("proxy.mcp_gateway.router.firestore.Client"),
            patch("proxy.mcp_gateway.auth.secretmanager.SecretManagerServiceClient"),
            patch("proxy.mcp_gateway.auth.google.auth.default"),
            patch("proxy.mcp_gateway.auth.impersonated_credentials.Credentials"),
        ):
            yield

    def _make_app_with_state(self):
        """Build a test app with mocked state dependencies."""
        os.environ["DEV_MODE"] = "true"
        os.environ["PARTNER_PROJECT_ID"] = "test-partner-project"

        from proxy.mcp_gateway.main import app
        from proxy.mcp_gateway.router import ClientConfig
        from proxy.mcp_gateway.circuit_breaker import CircuitBreaker
        from proxy.mcp_gateway.rate_limiter import RateLimiter
        from proxy.mcp_gateway.model_armor import SanitizeResult, FilterResult

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

        upstream_resp = MagicMock()
        upstream_resp.status_code = 200
        upstream_resp.content = json.dumps({"result": "ok"}).encode()
        upstream_resp.headers = {"content-type": "application/json"}
        upstream_resp.aread = AsyncMock(return_value=upstream_resp.content)
        upstream_resp.aclose = AsyncMock()

        http_client_mock = AsyncMock()
        http_client_mock.send.return_value = upstream_resp

        safe_result = SanitizeResult(allowed=True, filter_result=FilterResult.SAFE)
        armor_mock = AsyncMock()
        armor_mock.sanitize_user_prompt.return_value = safe_result
        armor_mock.sanitize_model_response.return_value = safe_result

        app.state.router = router_mock
        app.state.http_client = http_client_mock
        app.state.model_armor = armor_mock
        app.state.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        app.state.rate_limiter = RateLimiter(max_tokens=100, refill_rate=10.0)
        app.state.gti_http_client = AsyncMock()
        app.state.gti_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

        return app, http_client_mock

    @pytest.mark.asyncio
    @pytest.mark.mock
    async def test_outgoing_headers_contain_traceparent(self, memory_exporter):
        """When gateway forwards to upstream, headers should include traceparent."""
        from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
        from opentelemetry.propagate import set_global_textmap

        set_global_textmap(TraceContextTextMapPropagator())

        app, http_client_mock = self._make_app_with_state()

        with patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"):
            from httpx import ASGITransport, AsyncClient
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.post(
                    "/mcp/test-client",
                    json={"method": "list_cases", "params": {}},
                )

        # Inspect what headers were sent to the upstream via build_request
        call_args = http_client_mock.build_request.call_args
        outgoing_headers = call_args.kwargs.get("headers", {})
        assert "traceparent" in outgoing_headers
        assert outgoing_headers["traceparent"].startswith("00-")

    @pytest.mark.asyncio
    @pytest.mark.mock
    async def test_incoming_traceparent_is_used_as_parent(self, memory_exporter):
        """When request includes traceparent, gateway span should use that trace ID."""
        from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
        from opentelemetry.propagate import set_global_textmap

        set_global_textmap(TraceContextTextMapPropagator())

        app, http_client_mock = self._make_app_with_state()

        known_trace_id = "0af7651916cd43dd8448eb211c80319c"
        traceparent = f"00-{known_trace_id}-b7ad6b7169203331-01"

        with patch("proxy.mcp_gateway.main.get_impersonated_token", return_value="fake-token"):
            from httpx import ASGITransport, AsyncClient
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.post(
                    "/mcp/test-client",
                    json={"method": "list_cases", "params": {}},
                    headers={"traceparent": traceparent},
                )

        # The gateway.proxy_request span should belong to the incoming trace
        spans = memory_exporter.get_finished_spans()
        proxy_span = next((s for s in spans if s.name == "gateway.proxy_request"), None)
        assert proxy_span is not None
        actual_trace_id = format(proxy_span.context.trace_id, "032x")
        assert actual_trace_id == known_trace_id
