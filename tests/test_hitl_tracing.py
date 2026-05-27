"""Tests that the HITL Backend creates OTel spans for approval decisions."""
import os
import pytest
from unittest.mock import MagicMock, patch

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from httpx import ASGITransport, AsyncClient


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


MOCK_PENDING_DOC = {
    "approval_id": "APR-001",
    "status": "PENDING",
    "client_id": "acme",
    "case_id": "CASE-001",
    "proposed_action": {"action": "isolate_endpoint"},
}


def _build_mock_db():
    """Build a mock Firestore client that returns a PENDING approval doc."""
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = MOCK_PENDING_DOC.copy()

    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc

    mock_db = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_doc_ref
    return mock_db


@pytest.mark.asyncio
@pytest.mark.mock
class TestHITLTracing:
    async def test_decide_approval_creates_span(self, memory_exporter):
        """POST /approvals/{id}/decide should create a hitl.decide_approval span."""
        os.environ["DEV_MODE"] = "true"
        os.environ["PARTNER_PROJECT_ID"] = "test-project"

        mock_db = _build_mock_db()

        with patch("ui.hitl_dashboard.backend.main.get_db", return_value=mock_db):
            from ui.hitl_dashboard.backend.main import app

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    "/approvals/APR-001/decide",
                    json={
                        "decision": "APPROVED",
                        "analyst_id": "analyst@test.com",
                        "analyst_notes": "Confirmed threat",
                    },
                )

        assert resp.status_code == 200
        spans = memory_exporter.get_finished_spans()
        span_names = [s.name for s in spans]
        assert any("hitl.decide_approval" in name for name in span_names)

    async def test_decide_approval_span_has_attributes(self, memory_exporter):
        """The hitl.decide_approval span must carry approval and decision attributes."""
        os.environ["DEV_MODE"] = "true"
        os.environ["PARTNER_PROJECT_ID"] = "test-project"

        mock_db = _build_mock_db()

        with patch("ui.hitl_dashboard.backend.main.get_db", return_value=mock_db):
            from ui.hitl_dashboard.backend.main import app

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.post(
                    "/approvals/APR-001/decide",
                    json={
                        "decision": "REJECTED",
                        "analyst_id": "analyst@test.com",
                        "analyst_notes": "False positive",
                    },
                )

        spans = memory_exporter.get_finished_spans()
        hitl_span = next(
            (s for s in spans if s.name == "hitl.decide_approval"), None
        )
        assert hitl_span is not None
        assert hitl_span.attributes.get("approval.id") == "APR-001"
        assert hitl_span.attributes.get("decision.type") == "REJECTED"
        assert hitl_span.attributes.get("approval.client_id") == "acme"
        assert hitl_span.attributes.get("approval.case_id") == "CASE-001"
