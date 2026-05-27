"""Tests for the A2A Gateway — executor, FastAPI app, and routes."""

import json

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    Message,
    MessageSendParams,
    Part,
    Role,
    TaskState,
    TextPart,
)

from a2a_gateway.executor import TenantAwareA2aExecutor


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_context(
    client_id: str = "test-client",
    message_text: str = '{"case_id": "CASE-001", "alert_type": "PHISHING"}',
    *,
    client_id_in_request: bool = True,
    client_id_in_message: bool = False,
) -> RequestContext:
    """Build a minimal RequestContext with client_id in metadata."""
    msg = Message(
        messageId="msg-001",
        role=Role.user,
        parts=[Part(root=TextPart(text=message_text))],
        metadata={"client_id": client_id} if client_id_in_message else None,
    )
    req_metadata = {"client_id": client_id} if client_id_in_request else None
    return RequestContext(
        request=MessageSendParams(message=msg, metadata=req_metadata),
        task_id="task-001",
        context_id="ctx-001",
    )


def _make_event_queue() -> EventQueue:
    """Create a mock EventQueue that records enqueued events."""
    queue = AsyncMock(spec=EventQueue)
    queue.events = []

    async def capture_event(event):
        queue.events.append(event)

    queue.enqueue_event = capture_event
    return queue


# ── Executor: client_id extraction ───────────────────────────────────────


class TestExtractClientId:
    """Tests for client_id extraction from A2A metadata."""

    def test_extracts_from_request_metadata(self):
        """Extracts client_id from request-level metadata."""
        executor = TenantAwareA2aExecutor(orchestrator=None)
        context = _make_context("acme-corp", client_id_in_request=True)
        assert executor._extract_client_id(context) == "acme-corp"

    def test_extracts_from_message_metadata(self):
        """Falls back to message-level metadata."""
        executor = TenantAwareA2aExecutor(orchestrator=None)
        context = _make_context(
            "acme-corp",
            client_id_in_request=False,
            client_id_in_message=True,
        )
        assert executor._extract_client_id(context) == "acme-corp"

    def test_raises_on_missing_client_id(self):
        """Raises ValueError when no client_id in any metadata."""
        executor = TenantAwareA2aExecutor(orchestrator=None)
        context = _make_context(
            "ignored",
            client_id_in_request=False,
            client_id_in_message=False,
        )
        with pytest.raises(ValueError, match="client_id required"):
            executor._extract_client_id(context)


# ── Executor: alert parameter parsing ────────────────────────────────────


class TestParseAlertParams:
    """Tests for alert parameter extraction from A2A message."""

    def test_parses_structured_json(self):
        """Structured JSON message maps to process_alert() args."""
        executor = TenantAwareA2aExecutor(orchestrator=None)
        text = json.dumps({
            "case_id": "CASE-123",
            "alert_type": "MALWARE",
            "severity": "HIGH",
            "gti_enabled": True,
        })
        context = _make_context(message_text=text)
        params = executor._parse_alert_params(context)
        assert params["case_id"] == "CASE-123"
        assert params["alert_type"] == "MALWARE"
        assert params["severity"] == "HIGH"
        assert params["gti_enabled"] is True

    def test_natural_language_fallback(self):
        """Non-JSON text uses fallback with UNKNOWN alert type."""
        executor = TenantAwareA2aExecutor(orchestrator=None)
        context = _make_context(message_text="Triage this phishing alert")
        params = executor._parse_alert_params(context)
        assert params["alert_type"] == "UNKNOWN"
        assert params["raw_alert"]["a2a_message"] == "Triage this phishing alert"

    def test_defaults_for_missing_fields(self):
        """Missing optional fields get sensible defaults."""
        executor = TenantAwareA2aExecutor(orchestrator=None)
        text = json.dumps({"case_id": "CASE-001"})
        context = _make_context(message_text=text)
        params = executor._parse_alert_params(context)
        assert params["alert_type"] == "UNKNOWN"
        assert params["severity"] == "MEDIUM"
        assert params["autonomous_mode"] is False


# ── Executor: task lifecycle ─────────────────────────────────────────────


@pytest.mark.asyncio
class TestExecutorLifecycle:
    """Tests for A2A task lifecycle events."""

    async def test_successful_execution_publishes_lifecycle(self):
        """Successful execution: submitted → working → artifact → completed."""
        mock_orch = AsyncMock()
        mock_orch.process_alert = AsyncMock(return_value={
            "status": "COMPLETED",
            "result": "Alert triaged as BENIGN",
        })

        executor = TenantAwareA2aExecutor(orchestrator=mock_orch)
        context = _make_context("valid-client-01")
        queue = _make_event_queue()

        await executor.execute(context, queue)

        # Should have 4 events: submitted, working, artifact, completed
        assert len(queue.events) == 4
        assert queue.events[0].status.state == TaskState.submitted
        assert queue.events[1].status.state == TaskState.working
        # events[2] is TaskArtifactUpdateEvent (no .status)
        assert queue.events[3].status.state == TaskState.completed
        assert queue.events[3].final is True

        # Verify orchestrator was called with correct params
        mock_orch.process_alert.assert_awaited_once()
        call_kwargs = mock_orch.process_alert.call_args.kwargs
        assert call_kwargs["client_id"] == "valid-client-01"
        assert call_kwargs["case_id"] == "CASE-001"
        assert call_kwargs["alert_type"] == "PHISHING"

    async def test_orchestrator_error_publishes_failed(self):
        """Orchestrator exception produces submitted → failed."""
        mock_orch = AsyncMock()
        mock_orch.process_alert = AsyncMock(
            side_effect=RuntimeError("Pipeline timeout")
        )

        executor = TenantAwareA2aExecutor(orchestrator=mock_orch)
        context = _make_context("valid-client-01")
        queue = _make_event_queue()

        await executor.execute(context, queue)

        # submitted + failed (working may also appear depending on error timing)
        states = [e.status.state for e in queue.events if hasattr(e, "status")]
        assert TaskState.submitted in states
        assert TaskState.failed in states

    async def test_invalid_client_id_publishes_failed(self):
        """Invalid client_id (regex fail) produces failed event."""
        executor = TenantAwareA2aExecutor(orchestrator=None)
        context = _make_context("../../../etc/passwd")
        queue = _make_event_queue()

        await executor.execute(context, queue)

        states = [e.status.state for e in queue.events if hasattr(e, "status")]
        assert TaskState.failed in states

    async def test_missing_client_id_publishes_failed(self):
        """Missing client_id produces failed event."""
        executor = TenantAwareA2aExecutor(orchestrator=None)
        context = _make_context(
            "ignored",
            client_id_in_request=False,
            client_id_in_message=False,
        )
        queue = _make_event_queue()

        await executor.execute(context, queue)

        states = [e.status.state for e in queue.events if hasattr(e, "status")]
        assert TaskState.failed in states


# ── Gateway: FastAPI routes ──────────────────────────────────────────────


class TestA2AGatewayRoutes:
    """Tests for the A2A Gateway FastAPI app routes."""

    @pytest.fixture
    def client(self):
        """Create an async HTTP client for the A2A Gateway app."""
        import os
        os.environ.setdefault("DEV_MODE", "true")
        os.environ.setdefault("PARTNER_PROJECT_ID", "test")
        os.environ.setdefault("MCP_GATEWAY_URL", "http://localhost:8080")

        from httpx import AsyncClient, ASGITransport
        from a2a_gateway.main import app

        return AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        )

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """GET /health returns ok."""
        async with client:
            r = await client.get("/health")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_agent_card_endpoint(self, client):
        """GET /.well-known/agent-card.json returns valid Agent Card."""
        async with client:
            r = await client.get("/.well-known/agent-card.json")
            assert r.status_code == 200
            card = r.json()
            assert card["name"] == "agentic-soc-orchestrator"
            assert len(card["skills"]) == 4

    @pytest.mark.asyncio
    async def test_agent_card_no_auth_required(self, client):
        """Agent Card is publicly accessible (no auth header needed)."""
        async with client:
            r = await client.get("/.well-known/agent-card.json")
            # No Authorization header sent — should still work
            assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_jsonrpc_endpoint_exists(self, client):
        """POST / accepts A2A JSON-RPC requests."""
        async with client:
            payload = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "id": "1",
                "params": {
                    "message": {
                        "messageId": "msg-001",
                        "role": "user",
                        "parts": [{"kind": "text", "text": "test"}],
                        "metadata": {"client_id": "test-client"},
                    },
                    "metadata": {"client_id": "test-client"},
                },
            }
            r = await client.post("/", json=payload)
            # Should return 200 with JSON-RPC response (may fail internally,
            # but the route exists and handles the request)
            assert r.status_code == 200
            resp = r.json()
            assert "jsonrpc" in resp
