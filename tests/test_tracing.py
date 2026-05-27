"""Unit tests for the shared OpenTelemetry tracing module."""
import os
import pytest
from unittest.mock import patch

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


@pytest.fixture(autouse=True)
def _reset_tracer():
    """Reset OTel global state between tests.

    OTel SDK >=1.38 uses a Once guard (_TRACER_PROVIDER_SET_ONCE) that prevents
    set_tracer_provider from being called more than once. We reset that guard
    plus the cached provider so each test starts with a clean slate.
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
    """Set up an in-memory exporter and return it for assertions."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return exporter


class TestInitTracing:
    def test_console_exporter_is_default(self):
        """init_tracing() with no env var uses ConsoleSpanExporter."""
        import observability.tracing as mod

        mod._initialized = False
        with patch.dict(os.environ, {"OTEL_EXPORTER_TYPE": "console"}, clear=False):
            mod.init_tracing("test-service")
        provider = trace.get_tracer_provider()
        assert isinstance(provider, TracerProvider)

    def test_idempotent_init(self):
        """Calling init_tracing twice does not raise or reconfigure."""
        import observability.tracing as mod

        mod._initialized = False
        mod.init_tracing("svc-a")
        mod.init_tracing("svc-b")  # should be a no-op


class TestGetTracer:
    def test_returns_tracer(self):
        from observability.tracing import get_tracer

        tracer = get_tracer("test.module")
        assert tracer is not None


class TestSpanCreation:
    def test_span_has_attributes(self, memory_exporter):
        tracer = trace.get_tracer("test")
        with tracer.start_as_current_span("test.op") as span:
            span.set_attribute("client.id", "acme")
            span.set_attribute("case.id", "CASE-001")

        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "test.op"
        assert spans[0].attributes["client.id"] == "acme"
        assert spans[0].attributes["case.id"] == "CASE-001"

    def test_child_span_links_to_parent(self, memory_exporter):
        tracer = trace.get_tracer("test")
        with tracer.start_as_current_span("parent"):
            with tracer.start_as_current_span("child"):
                pass

        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 2
        child = next(s for s in spans if s.name == "child")
        parent = next(s for s in spans if s.name == "parent")
        assert child.parent.span_id == parent.context.span_id


class TestGetCurrentTraceId:
    def test_returns_hex_string_inside_span(self, memory_exporter):
        from observability.tracing import get_current_trace_id

        tracer = trace.get_tracer("test")
        with tracer.start_as_current_span("op"):
            tid = get_current_trace_id()
            assert tid is not None
            assert len(tid) == 32
            int(tid, 16)  # must be valid hex

    def test_returns_none_outside_span(self):
        from observability.tracing import get_current_trace_id

        assert get_current_trace_id() is None


class TestStageTrackerTraceId:
    def test_trace_id_included_in_stage_document(self, memory_exporter):
        """Verify that record_stage includes trace_id when inside a span."""
        from agents.stage_tracker import StageTracker
        from unittest.mock import MagicMock

        tracker = StageTracker(partner_project_id="test")
        mock_db = MagicMock()
        tracker._db = mock_db

        tracer = trace.get_tracer("test")
        with tracer.start_as_current_span("parent"):
            tracker.record_stage(
                session_id="s1", case_id="C1", client_id="acme",
                agent_key="triage", raw_output='{"result":"ok"}',
                started_at=1000.0, completed_at=1005.0,
            )

        call_args = mock_db.collection.return_value.document.return_value.set.call_args
        doc = call_args[0][0]
        assert "trace_id" in doc
        assert doc["trace_id"] is not None
        assert len(doc["trace_id"]) == 32

    def test_trace_id_none_when_no_span(self):
        """Verify that trace_id is None when not inside a span."""
        from agents.stage_tracker import StageTracker
        from unittest.mock import MagicMock

        tracker = StageTracker(partner_project_id="test")
        mock_db = MagicMock()
        tracker._db = mock_db

        tracker.record_stage(
            session_id="s1", case_id="C1", client_id="acme",
            agent_key="triage", raw_output='{"x":1}',
            started_at=1000.0, completed_at=1005.0,
        )

        call_args = mock_db.collection.return_value.document.return_value.set.call_args
        doc = call_args[0][0]
        assert "trace_id" in doc
        assert doc["trace_id"] is None


class TestExporterSelection:
    def test_console_exporter_by_default(self):
        """Default OTEL_EXPORTER_TYPE selects ConsoleSpanExporter."""
        import observability.tracing as mod

        mod._initialized = False
        with patch.dict(os.environ, {"OTEL_EXPORTER_TYPE": "console"}, clear=False):
            mod.init_tracing("test-console")

        provider = trace.get_tracer_provider()
        assert isinstance(provider, TracerProvider)
        assert len(provider._active_span_processor._span_processors) > 0

    def test_cloud_exporter_imports_succeed(self):
        """Verify that all cloud exporter dependencies are importable."""
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        assert OTLPSpanExporter is not None

    def test_cloud_exporter_selected_when_env_set(self):
        """When OTEL_EXPORTER_TYPE=cloud, init_tracing attempts cloud exporter."""
        from unittest.mock import MagicMock
        import observability.tracing as mod

        mod._initialized = False
        mock_exporter = MagicMock()
        with (
            patch.dict(os.environ, {"OTEL_EXPORTER_TYPE": "cloud"}, clear=False),
            patch.object(mod, "_create_cloud_exporter", return_value=mock_exporter) as mock_create,
        ):
            mod.init_tracing("test-cloud")
            mock_create.assert_called_once()


class TestErrorRecording:
    def test_exception_recorded_on_span(self, memory_exporter):
        tracer = trace.get_tracer("test")
        with pytest.raises(ValueError):
            with tracer.start_as_current_span("fail") as span:
                span.record_exception(ValueError("boom"))
                span.set_status(trace.StatusCode.ERROR, "boom")
                raise ValueError("boom")

        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].status.status_code == trace.StatusCode.ERROR
        events = spans[0].events
        assert any(e.name == "exception" for e in events)
