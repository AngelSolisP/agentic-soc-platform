"""
Tests for the HITL Two-Pass Architecture.

Covers:
- HITLQueue expiry (expires_at field + automatic EXPIRED status)
- execute_approved_action() orchestrator method (APPROVED, REJECTED, EXPIRED, MODIFIED)
- AgenticSOCApp mode parameter (process_alert vs execute_approval)
- HITL decide endpoint callback (fire on APPROVED/MODIFIED, skip otherwise)
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

# ── TestHITLQueueExpiry ──────────────────────────────────────────────────────


class TestHITLQueueExpiry:
    """Tests for expires_at in HITLQueue.submit_approval_request()."""

    @patch("agents.response.agent.firestore")
    def test_submit_includes_expires_at(self, mock_firestore_mod):
        """submit_approval_request() should include an expires_at field."""
        from agents.response.agent import HITLQueue

        mock_db = MagicMock()
        mock_firestore_mod.Client.return_value = mock_db

        queue = HITLQueue("test-project")
        approval_id = queue.submit_approval_request(
            client_id="acme",
            case_id="CASE-001",
            agent_name="response_agent_acme",
            proposed_action={"proposed_action": "isolate_endpoint"},
            triage_summary="Ransomware detected",
        )

        assert approval_id  # Non-empty string
        # Verify Firestore set was called with expires_at
        call_args = mock_db.collection.return_value.document.return_value.set.call_args
        doc = call_args[0][0]
        assert "expires_at" in doc
        # expires_at should be a datetime object (native Firestore Timestamp)
        expires = doc["expires_at"]
        created = doc["created_at"]
        assert isinstance(expires, datetime)
        assert isinstance(created, datetime)
        # Default timeout is 30 minutes
        assert (expires - created) == timedelta(minutes=30)

    @patch("agents.response.agent.firestore")
    def test_default_timeout_30_minutes(self, mock_firestore_mod):
        """Default hitl_timeout_minutes should be 30."""
        from agents.response.agent import HITLQueue

        mock_db = MagicMock()
        mock_firestore_mod.Client.return_value = mock_db

        queue = HITLQueue("test-project")
        queue.submit_approval_request(
            client_id="acme",
            case_id="CASE-001",
            agent_name="response_agent_acme",
            proposed_action={"proposed_action": "block_ip"},
            triage_summary="C2 activity",
        )

        call_args = mock_db.collection.return_value.document.return_value.set.call_args
        doc = call_args[0][0]
        expires = doc["expires_at"]
        created = doc["created_at"]
        diff = expires - created
        assert diff == timedelta(minutes=30)

    @patch("agents.response.agent.firestore")
    def test_custom_timeout(self, mock_firestore_mod):
        """Custom hitl_timeout_minutes should be respected."""
        from agents.response.agent import HITLQueue

        mock_db = MagicMock()
        mock_firestore_mod.Client.return_value = mock_db

        queue = HITLQueue("test-project")
        queue.submit_approval_request(
            client_id="acme",
            case_id="CASE-001",
            agent_name="response_agent_acme",
            proposed_action={"proposed_action": "block_ip"},
            triage_summary="C2 activity",
            hitl_timeout_minutes=60,
        )

        call_args = mock_db.collection.return_value.document.return_value.set.call_args
        doc = call_args[0][0]
        expires = doc["expires_at"]
        created = doc["created_at"]
        assert (expires - created) == timedelta(minutes=60)

    @patch("agents.response.agent.firestore")
    def test_get_approval_returns_expired_status(self, mock_firestore_mod):
        """get_approval_status() should return EXPIRED for past-due PENDING approvals."""
        from agents.response.agent import HITLQueue

        mock_db = MagicMock()
        mock_firestore_mod.Client.return_value = mock_db

        # Simulate a PENDING approval that expired 5 minutes ago
        expired_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "approval_id": "test-id",
            "status": "PENDING",
            "expires_at": expired_time,
            "client_id": "acme",
            "case_id": "CASE-001",
        }
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        queue = HITLQueue("test-project")
        result = queue.get_approval_status("test-id")
        assert result["status"] == "EXPIRED"

    @patch("agents.response.agent.firestore")
    def test_get_approval_pending_not_expired(self, mock_firestore_mod):
        """get_approval_status() should return PENDING if not yet expired."""
        from agents.response.agent import HITLQueue

        mock_db = MagicMock()
        mock_firestore_mod.Client.return_value = mock_db

        future_time = (datetime.now(timezone.utc) + timedelta(minutes=25)).isoformat()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "approval_id": "test-id",
            "status": "PENDING",
            "expires_at": future_time,
            "client_id": "acme",
            "case_id": "CASE-001",
        }
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        queue = HITLQueue("test-project")
        result = queue.get_approval_status("test-id")
        assert result["status"] == "PENDING"


# ── TestExecuteApprovedAction ────────────────────────────────────────────────


class TestExecuteApprovedAction:
    """Tests for AgenticSOCOrchestrator.execute_approved_action()."""

    def _make_orchestrator(self):
        """Create an orchestrator with mocked dependencies."""
        with patch("agents.orchestrator.agent.StageTracker"), \
             patch("agents.orchestrator.agent.AlertDeduplicator"):
            from agents.orchestrator.agent import AgenticSOCOrchestrator
            orch = AgenticSOCOrchestrator(
                partner_project_id="test-project",
                gateway_url="http://localhost:8080",
            )
        return orch

    @pytest.mark.asyncio
    @patch("agents.orchestrator.agent.LlmAgent")
    @patch("agents.orchestrator.agent.Runner")
    @patch("agents.orchestrator.agent.create_response_agent")
    @patch("agents.orchestrator.agent.HITLQueue")
    async def test_approved_executes_agent(self, mock_queue_cls, mock_create_resp, mock_runner_cls, mock_llm_agent):
        """APPROVED status should run the response agent and return EXECUTED."""
        # Mock google.genai.types which is lazily imported inside execute_approved_action
        import sys
        mock_types = MagicMock()
        sys.modules["google.genai.types"] = mock_types

        orch = self._make_orchestrator()

        mock_queue = MagicMock()
        mock_queue.get_approval_status.return_value = {
            "status": "APPROVED",
            "client_id": "acme",
            "case_id": "CASE-001",
            "proposed_action": {"proposed_action": "isolate_endpoint"},
            "triage_summary": "Ransomware confirmed",
            "analyst_instructions": "Go ahead",
        }
        mock_queue_cls.return_value = mock_queue

        # Mock the runner to yield a final event
        mock_event = MagicMock()
        mock_event.is_final_response.return_value = True
        mock_part = MagicMock()
        mock_part.text = "Endpoint isolated successfully."
        mock_event.content.parts = [mock_part]

        mock_runner = MagicMock()

        async def fake_run_async(**kwargs):
            yield mock_event

        mock_runner.run_async = fake_run_async
        mock_runner_cls.return_value = mock_runner

        # Mock session creation
        mock_session = MagicMock()
        mock_session.id = "session-xyz"
        orch._session_service.create_session = AsyncMock(return_value=mock_session)

        result = await orch.execute_approved_action("approval-123")

        assert result["status"] == "EXECUTED"
        assert result["approval_id"] == "approval-123"
        assert result["case_id"] == "CASE-001"
        assert result["client_id"] == "acme"
        assert result["session_id"] == "session-xyz"
        assert "isolated" in result["agent_response"].lower()

    @pytest.mark.asyncio
    @patch("agents.orchestrator.agent.HITLQueue")
    async def test_rejected_skips_execution(self, mock_queue_cls):
        """REJECTED status should return immediately without running agent."""
        orch = self._make_orchestrator()

        mock_queue = MagicMock()
        mock_queue.get_approval_status.return_value = {
            "status": "REJECTED",
            "client_id": "acme",
            "case_id": "CASE-002",
            "analyst_instructions": "False positive, do not isolate",
        }
        mock_queue_cls.return_value = mock_queue

        result = await orch.execute_approved_action("approval-456")

        assert result["status"] == "REJECTED"
        assert result["approval_id"] == "approval-456"
        assert "rejected" in result["agent_response"].lower()
        assert "False positive" in result["agent_response"]

    @pytest.mark.asyncio
    @patch("agents.orchestrator.agent.HITLQueue")
    async def test_expired_returns_expired(self, mock_queue_cls):
        """EXPIRED status should return an expiry message without running agent."""
        orch = self._make_orchestrator()

        mock_queue = MagicMock()
        mock_queue.get_approval_status.return_value = {
            "status": "EXPIRED",
            "client_id": "acme",
            "case_id": "CASE-003",
        }
        mock_queue_cls.return_value = mock_queue

        result = await orch.execute_approved_action("approval-789")

        assert result["status"] == "EXPIRED"
        assert "expired" in result["agent_response"].lower()

    @pytest.mark.asyncio
    @patch("agents.orchestrator.agent.LlmAgent")
    @patch("agents.orchestrator.agent.Runner")
    @patch("agents.orchestrator.agent.create_response_agent")
    @patch("agents.orchestrator.agent.HITLQueue")
    async def test_modified_uses_modified_params(self, mock_queue_cls, mock_create_resp, mock_runner_cls, mock_llm_agent):
        """MODIFIED status should use modified_parameters for the task."""
        import sys
        sys.modules.setdefault("google.genai.types", MagicMock())

        orch = self._make_orchestrator()

        mock_queue = MagicMock()
        mock_queue.get_approval_status.return_value = {
            "status": "MODIFIED",
            "client_id": "acme",
            "case_id": "CASE-004",
            "proposed_action": {"proposed_action": "block_ip", "ip": "1.2.3.4"},
            "modified_parameters": {"proposed_action": "block_ip", "ip": "5.6.7.8", "duration_hours": 48},
            "triage_summary": "C2 confirmed",
            "analyst_instructions": "Block different IP",
        }
        mock_queue_cls.return_value = mock_queue

        mock_event = MagicMock()
        mock_event.is_final_response.return_value = True
        mock_part = MagicMock()
        mock_part.text = "IP 5.6.7.8 blocked for 48 hours."
        mock_event.content.parts = [mock_part]

        mock_runner = MagicMock()

        async def fake_run_async(**kwargs):
            yield mock_event

        mock_runner.run_async = fake_run_async
        mock_runner_cls.return_value = mock_runner

        mock_session = MagicMock()
        mock_session.id = "session-mod"
        orch._session_service.create_session = AsyncMock(return_value=mock_session)

        result = await orch.execute_approved_action("approval-mod")

        assert result["status"] == "EXECUTED"
        assert "5.6.7.8" in result["agent_response"]

    @pytest.mark.asyncio
    @patch("agents.orchestrator.agent.HITLQueue")
    async def test_unexpected_status_returns_error(self, mock_queue_cls):
        """Unexpected approval status should return ERROR."""
        orch = self._make_orchestrator()

        mock_queue = MagicMock()
        mock_queue.get_approval_status.return_value = {
            "status": "PENDING",
            "client_id": "acme",
            "case_id": "CASE-005",
        }
        mock_queue_cls.return_value = mock_queue

        result = await orch.execute_approved_action("approval-pending")

        assert result["status"] == "ERROR"
        assert "Unexpected" in result["agent_response"]


# ── TestAgenticSOCAppMode ────────────────────────────────────────────────────


class TestAgenticSOCAppMode:
    """Tests for AgenticSOCApp.query() mode parameter."""

    @patch("agents.orchestrator.deployed_app.asyncio")
    @patch("agents.orchestrator.deployed_app.AgenticSOCOrchestrator")
    def test_query_execute_approval_mode(self, mock_orch_cls, mock_asyncio):
        """mode='execute_approval' should call execute_approved_action()."""
        from agents.orchestrator.deployed_app import AgenticSOCApp

        mock_orch = mock_orch_cls.return_value
        expected_result = {
            "case_id": "CASE-001",
            "approval_id": "approval-123",
            "status": "EXECUTED",
        }
        mock_asyncio.run.return_value = expected_result

        app = AgenticSOCApp()
        app.orchestrator = mock_orch

        result = app.query(
            client_id="acme",
            case_id="CASE-001",
            alert_type="PHISHING",
            mode="execute_approval",
            approval_id="approval-123",
        )

        assert result == expected_result
        mock_orch.execute_approved_action.assert_called_once_with("approval-123", requesting_client_id="acme")
        mock_orch.process_alert.assert_not_called()

    @patch("agents.orchestrator.deployed_app.asyncio")
    @patch("agents.orchestrator.deployed_app.AgenticSOCOrchestrator")
    def test_query_default_mode_calls_process_alert(self, mock_orch_cls, mock_asyncio):
        """Default mode should call process_alert() as before."""
        from agents.orchestrator.deployed_app import AgenticSOCApp

        mock_orch = mock_orch_cls.return_value
        expected_result = {"case_id": "CASE-001", "agent_response": "done"}
        mock_asyncio.run.return_value = expected_result

        app = AgenticSOCApp()
        app.orchestrator = mock_orch

        result = app.query(
            client_id="acme",
            case_id="CASE-001",
            alert_type="PHISHING",
            severity="HIGH",
        )

        assert result == expected_result
        mock_orch.process_alert.assert_called_once_with(
            client_id="acme",
            case_id="CASE-001",
            alert_type="PHISHING",
            severity="HIGH",
            trigger="RULE_DETECTION",
            raw_alert=None,
            autonomous_mode=False,
            gti_enabled=False,
        )
        mock_orch.execute_approved_action.assert_not_called()

    def test_query_execute_approval_requires_approval_id(self):
        """mode='execute_approval' without approval_id should raise ValueError."""
        from agents.orchestrator.deployed_app import AgenticSOCApp

        app = AgenticSOCApp()
        app.orchestrator = MagicMock()

        with pytest.raises(ValueError, match="approval_id required"):
            app.query(
                client_id="acme",
                case_id="CASE-001",
                alert_type="PHISHING",
                mode="execute_approval",
            )


# ── TestHITLCallback ─────────────────────────────────────────────────────────


class TestHITLCallback:
    """Tests for the approval callback in the HITL decide endpoint."""

    @pytest.fixture(autouse=True)
    def mock_firestore(self):
        with patch("ui.hitl_dashboard.backend.main.get_db") as mock_get_db:
            db_mock = MagicMock()
            mock_get_db.return_value = db_mock
            yield db_mock

    @pytest_asyncio.fixture
    async def test_client(self):
        import os
        os.environ["PARTNER_PROJECT_ID"] = "test-project"
        os.environ["DEV_MODE"] = "true"

        from ui.hitl_dashboard.backend.main import app
        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client

    @pytest.mark.asyncio
    @patch("ui.hitl_dashboard.backend.main.APPROVAL_CALLBACK_URL", "http://callback.example.com/execute")
    @patch("ui.hitl_dashboard.backend.main.httpx.AsyncClient")
    async def test_decide_sends_callback_on_approval(self, mock_httpx_cls, test_client, mock_firestore):
        """APPROVED decision should fire callback when APPROVAL_CALLBACK_URL is set."""
        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "approval_id": "test-approval-cb",
            "client_id": "acme",
            "case_id": "CASE-CB",
            "agent_name": "response_agent_acme",
            "session_id": "session-1",
            "status": "PENDING",
            "proposed_action": {"proposed_action": "isolate_endpoint"},
            "triage_summary": "test",
            "analyst_instructions": "",
            "created_at": "2026-03-26T10:00:00Z",
            "updated_at": "2026-03-26T10:00:00Z",
            "decided_by": None,
            "decided_at": None,
        }
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref

        # Mock the httpx async client context manager
        mock_client_instance = AsyncMock()
        mock_httpx_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_httpx_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        response = await test_client.post(
            "/approvals/test-approval-cb/decide",
            json={
                "decision": "APPROVED",
                "analyst_id": "analyst-1",
                "analyst_notes": "Go ahead",
            },
        )
        assert response.status_code == 200
        # Verify callback was attempted
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        assert call_args[0][0] == "http://callback.example.com/execute"
        payload = call_args[1]["json"]
        assert payload["approval_id"] == "test-approval-cb"
        assert payload["decision"] == "APPROVED"

    @pytest.mark.asyncio
    @patch("ui.hitl_dashboard.backend.main.APPROVAL_CALLBACK_URL", "http://callback.example.com/execute")
    @patch("ui.hitl_dashboard.backend.main.httpx.AsyncClient")
    async def test_decide_skips_callback_on_rejection(self, mock_httpx_cls, test_client, mock_firestore):
        """REJECTED decision should NOT fire callback."""
        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "approval_id": "test-approval-rej",
            "client_id": "acme",
            "case_id": "CASE-REJ",
            "agent_name": "response_agent_acme",
            "session_id": "session-1",
            "status": "PENDING",
            "proposed_action": {"proposed_action": "isolate_endpoint"},
            "triage_summary": "test",
            "analyst_instructions": "",
            "created_at": "2026-03-26T10:00:00Z",
            "updated_at": "2026-03-26T10:00:00Z",
            "decided_by": None,
            "decided_at": None,
        }
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref

        response = await test_client.post(
            "/approvals/test-approval-rej/decide",
            json={
                "decision": "REJECTED",
                "analyst_id": "analyst-1",
                "analyst_notes": "False positive",
            },
        )
        assert response.status_code == 200
        # httpx.AsyncClient should NOT have been instantiated for callback
        mock_httpx_cls.assert_not_called()

    @pytest.mark.asyncio
    @patch("ui.hitl_dashboard.backend.main.APPROVAL_CALLBACK_URL", "")
    async def test_decide_skips_callback_when_no_url(self, test_client, mock_firestore):
        """No callback URL configured should skip callback entirely."""
        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "approval_id": "test-approval-nourl",
            "client_id": "acme",
            "case_id": "CASE-NOURL",
            "agent_name": "response_agent_acme",
            "session_id": "session-1",
            "status": "PENDING",
            "proposed_action": {"proposed_action": "isolate_endpoint"},
            "triage_summary": "test",
            "analyst_instructions": "",
            "created_at": "2026-03-26T10:00:00Z",
            "updated_at": "2026-03-26T10:00:00Z",
            "decided_by": None,
            "decided_at": None,
        }
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref

        # Should succeed without attempting callback
        response = await test_client.post(
            "/approvals/test-approval-nourl/decide",
            json={
                "decision": "APPROVED",
                "analyst_id": "analyst-1",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"
