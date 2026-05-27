"""Tests for the Agent Engine deployed app wrapper."""

from unittest.mock import MagicMock, patch


class TestAgenticSOCApp:
    """Tests for AgenticSOCApp lifecycle methods."""

    def test_init_orchestrator_is_none(self):
        """App starts with no orchestrator before set_up()."""
        from agents.orchestrator.deployed_app import AgenticSOCApp

        app = AgenticSOCApp()
        assert app.orchestrator is None

    @patch.dict("os.environ", {
        "PARTNER_PROJECT_ID": "test-project",
        "MCP_GATEWAY_URL": "https://gateway.example.run.app",
    })
    @patch("agents.orchestrator.deployed_app.AgenticSOCOrchestrator")
    def test_set_up_creates_orchestrator(self, mock_orch_cls):
        """set_up() creates AgenticSOCOrchestrator from env vars."""
        from agents.orchestrator.deployed_app import AgenticSOCApp

        app = AgenticSOCApp()
        app.set_up()

        mock_orch_cls.assert_called_once_with(
            partner_project_id="test-project",
            gateway_url="https://gateway.example.run.app",
            gti_url="",
        )
        assert app.orchestrator is mock_orch_cls.return_value

    @patch.dict("os.environ", {
        "PARTNER_PROJECT_ID": "test-project",
        "MCP_GATEWAY_URL": "https://gateway.example.run.app",
        "GTI_GATEWAY_URL": "https://gti.example.run.app",
    })
    @patch("agents.orchestrator.deployed_app.AgenticSOCOrchestrator")
    def test_set_up_includes_gti_url(self, mock_orch_cls):
        """set_up() passes GTI_GATEWAY_URL when set."""
        from agents.orchestrator.deployed_app import AgenticSOCApp

        app = AgenticSOCApp()
        app.set_up()

        mock_orch_cls.assert_called_once_with(
            partner_project_id="test-project",
            gateway_url="https://gateway.example.run.app",
            gti_url="https://gti.example.run.app",
        )

    @patch("agents.orchestrator.deployed_app.asyncio")
    @patch("agents.orchestrator.deployed_app.AgenticSOCOrchestrator")
    def test_query_calls_process_alert(self, mock_orch_cls, mock_asyncio):
        """query() delegates to orchestrator.process_alert() via asyncio.run()."""
        from agents.orchestrator.deployed_app import AgenticSOCApp

        mock_orch = mock_orch_cls.return_value
        expected_result = {"case_id": "CASE-1", "agent_response": "done"}
        mock_asyncio.run.return_value = expected_result

        app = AgenticSOCApp()
        app.orchestrator = mock_orch

        result = app.query(
            client_id="acme",
            case_id="CASE-1",
            alert_type="PHISHING",
            severity="HIGH",
            gti_enabled=True,
        )

        assert result == expected_result
        mock_asyncio.run.assert_called_once()
        mock_orch.process_alert.assert_called_once_with(
            client_id="acme",
            case_id="CASE-1",
            alert_type="PHISHING",
            severity="HIGH",
            trigger="RULE_DETECTION",
            raw_alert=None,
            autonomous_mode=False,
            gti_enabled=True,
        )

    def test_query_default_severity(self):
        """query() defaults severity to MEDIUM."""
        from agents.orchestrator.deployed_app import AgenticSOCApp

        app = AgenticSOCApp()
        mock_orch = MagicMock()
        app.orchestrator = mock_orch

        with patch("agents.orchestrator.deployed_app.asyncio") as mock_asyncio:
            mock_asyncio.run.return_value = {"case_id": "C1"}
            app.query(client_id="acme", case_id="C1", alert_type="MALWARE")

        mock_orch.process_alert.assert_called_once_with(
            client_id="acme",
            case_id="C1",
            alert_type="MALWARE",
            severity="MEDIUM",
            trigger="RULE_DETECTION",
            raw_alert=None,
            autonomous_mode=False,
            gti_enabled=False,
        )

    def test_health_check_before_setup(self):
        """health_check() reports not initialized before set_up()."""
        from agents.orchestrator.deployed_app import AgenticSOCApp

        app = AgenticSOCApp()
        result = app.health_check()

        assert result["status"] == "unhealthy"
        assert result["orchestrator_initialized"] is False

    @patch("agents.orchestrator.deployed_app.AgenticSOCOrchestrator")
    def test_health_check_after_setup(self, mock_orch_cls):
        """health_check() reports healthy after set_up()."""
        from agents.orchestrator.deployed_app import AgenticSOCApp

        app = AgenticSOCApp()
        app.orchestrator = mock_orch_cls.return_value

        result = app.health_check()

        assert result["status"] == "healthy"
        assert result["orchestrator_initialized"] is True
