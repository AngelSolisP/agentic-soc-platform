"""Tests for the deploy_agent.py script CLI and logic."""

import pytest
from unittest.mock import patch, MagicMock


class TestDeployParseArgs:
    """Test CLI argument parsing."""

    def test_dry_run_only_requires_project(self):
        """--dry-run mode only requires --project."""
        from scripts.deploy_agent import build_parser

        parser = build_parser()
        args = parser.parse_args(["--project", "my-proj", "--dry-run"])

        assert args.project == "my-proj"
        assert args.dry_run is True

    def test_deploy_requires_gateway_url(self):
        """Deployment (non-dry-run) requires --gateway-url."""
        from scripts.deploy_agent import validate_args

        parser_ns = MagicMock(
            project="my-proj", gateway_url="", dry_run=False,
            update=False, rollback=False, resource_id=None,
        )
        errors = validate_args(parser_ns)
        assert any("gateway-url" in e.lower() for e in errors)

    def test_update_requires_resource_id(self):
        """--update requires --resource-id."""
        from scripts.deploy_agent import validate_args

        parser_ns = MagicMock(
            project="my-proj", gateway_url="https://gw.run.app",
            dry_run=False, update=True, rollback=False, resource_id=None,
        )
        errors = validate_args(parser_ns)
        assert any("resource-id" in e.lower() for e in errors)

    def test_rollback_requires_resource_id(self):
        """--rollback requires --resource-id."""
        from scripts.deploy_agent import validate_args

        parser_ns = MagicMock(
            project="my-proj", gateway_url="https://gw.run.app",
            dry_run=False, update=False, rollback=True, resource_id=None,
        )
        errors = validate_args(parser_ns)
        assert any("resource-id" in e.lower() for e in errors)

    def test_valid_deploy_args_no_errors(self):
        """Valid args for a fresh deploy produce no errors."""
        from scripts.deploy_agent import validate_args

        parser_ns = MagicMock(
            project="my-proj", gateway_url="https://gw.run.app",
            dry_run=False, update=False, rollback=False, resource_id=None,
        )
        errors = validate_args(parser_ns)
        assert errors == []

    def test_rollback_flag_parsed(self):
        """--rollback flag is parsed correctly."""
        from scripts.deploy_agent import build_parser

        parser = build_parser()
        args = parser.parse_args([
            "--project", "my-proj",
            "--gateway-url", "https://gw.run.app",
            "--rollback",
            "--resource-id", "12345",
        ])
        assert args.rollback is True
        assert args.resource_id == "12345"


class TestDeployDryRun:
    """Test --dry-run mode."""

    @patch.dict("os.environ", {
        "PARTNER_PROJECT_ID": "test-project",
        "MCP_GATEWAY_URL": "https://gateway.run.app",
    })
    @patch("agents.orchestrator.deployed_app.AgenticSOCOrchestrator")
    def test_dry_run_validates_app(self, mock_orch_cls):
        """--dry-run instantiates AgenticSOCApp and calls set_up()."""
        from scripts.deploy_agent import do_dry_run

        result = do_dry_run()
        assert result is True
        mock_orch_cls.assert_called_once()


class TestDeployEnvVars:
    """Test environment variable construction for Agent Engine."""

    def test_build_env_vars_required(self):
        """build_env_vars includes required variables."""
        from scripts.deploy_agent import build_env_vars

        env = build_env_vars(
            project_id="my-proj",
            gateway_url="https://gw.run.app",
            model="gemini-2.5-pro",
        )
        assert env["PARTNER_PROJECT_ID"] == "my-proj"
        assert env["MCP_GATEWAY_URL"] == "https://gw.run.app"
        assert env["GEMINI_PRO_MODEL"] == "gemini-2.5-pro"
        assert env["OTEL_EXPORTER_TYPE"] == "cloud"

    def test_build_env_vars_with_gti(self):
        """build_env_vars includes GTI_GATEWAY_URL when provided."""
        from scripts.deploy_agent import build_env_vars

        env = build_env_vars(
            project_id="my-proj",
            gateway_url="https://gw.run.app",
            model="gemini-2.5-pro",
            gti_url="https://gti.run.app",
        )
        assert env["GTI_GATEWAY_URL"] == "https://gti.run.app"


class TestDeployRequirements:
    """Test requirements list for Agent Engine."""

    def test_agent_engine_requirements_include_adk(self):
        """Requirements include google-cloud-aiplatform[adk,agent_engines]."""
        from scripts.deploy_agent import AGENT_ENGINE_REQUIREMENTS

        assert any("agent_engines" in r for r in AGENT_ENGINE_REQUIREMENTS)
        assert any("google-adk" in r for r in AGENT_ENGINE_REQUIREMENTS)
