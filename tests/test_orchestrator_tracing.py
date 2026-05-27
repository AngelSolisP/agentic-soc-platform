"""Tests that the Orchestrator creates OTel spans for alert processing."""
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


@pytest.fixture(autouse=True)
def _mock_adk_types():
    """Ensure google.genai.types is importable even if ADK is not fully installed."""
    mod = MagicMock()
    mod.Content = MagicMock
    mod.Part = MagicMock
    sys.modules.setdefault("google.genai.types", mod)
    yield


@pytest.fixture(autouse=True)
def _reset_otel():
    """Reset OTel global state between tests.

    OTel SDK >=1.38 uses a Once guard that prevents set_tracer_provider
    from being called more than once. We reset that guard so each test
    starts with a clean slate.
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


def _mock_event(author: str, text: str, is_final: bool = False):
    """Create a mock ADK event."""
    part = MagicMock()
    part.text = text
    content = MagicMock()
    content.parts = [part]
    event = MagicMock()
    event.author = author
    event.content = content
    event.is_final_response.return_value = is_final
    return event


@pytest.mark.asyncio
@pytest.mark.mock
class TestOrchestratorTracing:
    @patch("agents.orchestrator.agent.LlmAgent")
    @patch("agents.orchestrator.agent.StageTracker")
    @patch("agents.orchestrator.agent.AlertDeduplicator")
    @patch("agents.orchestrator.agent.Runner")
    @patch("agents.orchestrator.agent.InMemorySessionService")
    @patch("agents.orchestrator.agent.create_triage_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_enrichment_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_case_manager_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_response_agent", return_value=MagicMock())
    async def test_process_alert_creates_root_span(
        self, _resp, _cm, _enr, _tri, mock_session_svc, mock_runner_cls,
        mock_dedup_cls, mock_tracker_cls, _llm_agent, memory_exporter,
    ):
        mock_dedup = mock_dedup_cls.return_value
        mock_dedup.is_duplicate.return_value = False

        session = MagicMock()
        session.id = "session-001"
        mock_session_svc.return_value.create_session = AsyncMock(return_value=session)

        # Simulate the runner yielding events from triage then enrichment
        events = [
            _mock_event("triage_agent_c1", '{"verdict":"MALICIOUS","priority":"HIGH","confidence_score":0.92}'),
            _mock_event("enrichment_agent_c1", '{"threat_level":"CRITICAL"}', is_final=True),
        ]

        async def fake_run_async(**kwargs):
            for e in events:
                yield e

        runner_instance = mock_runner_cls.return_value
        runner_instance.run_async = fake_run_async

        mock_tracker_cls.return_value.record_pipeline.return_value = []

        from agents.orchestrator.agent import AgenticSOCOrchestrator

        orch = AgenticSOCOrchestrator(partner_project_id="test-project")
        result = await orch.process_alert(
            client_id="test-client",
            case_id="CASE-001",
            alert_type="PHISHING",
        )

        assert result["case_id"] == "CASE-001"

        spans = memory_exporter.get_finished_spans()
        span_names = [s.name for s in spans]
        assert "orchestrator.process_alert" in span_names

        root = next(s for s in spans if s.name == "orchestrator.process_alert")
        assert root.attributes["client.id"] == "test-client"
        assert root.attributes["case.id"] == "CASE-001"
        assert root.attributes["alert.type"] == "PHISHING"

    @patch("agents.orchestrator.agent.LlmAgent")
    @patch("agents.orchestrator.agent.StageTracker")
    @patch("agents.orchestrator.agent.AlertDeduplicator")
    @patch("agents.orchestrator.agent.Runner")
    @patch("agents.orchestrator.agent.InMemorySessionService")
    @patch("agents.orchestrator.agent.create_triage_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_enrichment_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_case_manager_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_response_agent", return_value=MagicMock())
    async def test_per_stage_child_spans_created(
        self, _resp, _cm, _enr, _tri, mock_session_svc, mock_runner_cls,
        mock_dedup_cls, mock_tracker_cls, _llm_agent, memory_exporter,
    ):
        mock_dedup = mock_dedup_cls.return_value
        mock_dedup.is_duplicate.return_value = False

        session = MagicMock()
        session.id = "session-002"
        mock_session_svc.return_value.create_session = AsyncMock(return_value=session)

        events = [
            _mock_event("triage_agent_c1", "Triage analysis..."),
            _mock_event("enrichment_agent_c1", "Enrichment data...", is_final=True),
        ]

        async def fake_run_async(**kwargs):
            for e in events:
                yield e

        mock_runner_cls.return_value.run_async = fake_run_async
        mock_tracker_cls.return_value.record_pipeline.return_value = []

        from agents.orchestrator.agent import AgenticSOCOrchestrator

        orch = AgenticSOCOrchestrator(partner_project_id="test-project")
        await orch.process_alert(
            client_id="test-client", case_id="CASE-002", alert_type="MALWARE",
        )

        spans = memory_exporter.get_finished_spans()
        span_names = [s.name for s in spans]
        assert "orchestrator.stage.triage" in span_names
        assert "orchestrator.stage.enrichment" in span_names
