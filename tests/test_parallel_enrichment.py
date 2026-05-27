"""Tests for parallel enrichment agent creation."""

import os
import pytest
from unittest.mock import patch, MagicMock

from google.adk.agents import ParallelAgent, LlmAgent

from agents.enrichment.agent import create_enrichment_agent
from agents.enrichment.parallel_enrichment import (
    create_parallel_enrichment_agent,
    create_enrichment_merger_agent,
)
from agents.tool_catalog import CHRONICLE_ENRICHMENT_TOOLS, GTI_ENRICHMENT_TOOLS


@pytest.fixture(autouse=True)
def mock_mcp():
    """Patch MCP toolset creation to avoid real connections."""
    with patch("agents.enrichment.parallel_enrichment.McpToolset") as mock_ts, \
         patch("agents.enrichment.parallel_enrichment.build_mcp_connection") as mock_conn, \
         patch("agents.enrichment.parallel_enrichment.build_mcp_auth_provider", return_value=None):
        mock_ts.return_value = MagicMock()
        mock_conn.return_value = MagicMock()
        yield mock_ts


@pytest.fixture(autouse=True)
def mock_mcp_merger():
    """Patch MCP for merger agent."""
    with patch("agents.enrichment.parallel_enrichment.McpToolset") as mock_ts, \
         patch("agents.enrichment.parallel_enrichment.build_mcp_connection") as mock_conn, \
         patch("agents.enrichment.parallel_enrichment.build_mcp_auth_provider", return_value=None):
        mock_ts.return_value = MagicMock()
        mock_conn.return_value = MagicMock()
        yield


class TestParallelEnrichment:
    """Tests for parallel enrichment agent factory."""

    def test_creates_parallel_agent_when_gti_enabled(self):
        agent = create_parallel_enrichment_agent(
            "test-client", "http://localhost:8080",
            gti_gateway_url="http://localhost:8080",
            gti_enabled=True,
        )
        assert isinstance(agent, ParallelAgent)
        assert len(agent.sub_agents) == 2

    def test_creates_single_agent_without_gti(self):
        agent = create_parallel_enrichment_agent(
            "test-client", "http://localhost:8080",
            gti_enabled=False,
        )
        assert isinstance(agent, LlmAgent)

    def test_sub_agents_have_output_keys(self):
        agent = create_parallel_enrichment_agent(
            "test-client", "http://localhost:8080",
            gti_gateway_url="http://localhost:8080",
            gti_enabled=True,
        )
        assert isinstance(agent, ParallelAgent)
        chronicle_agent = agent.sub_agents[0]
        gti_agent = agent.sub_agents[1]
        assert chronicle_agent.output_key == "chronicle_enrichment_result"
        assert gti_agent.output_key == "gti_enrichment_result"

    def test_sub_agent_names_include_client_id(self):
        agent = create_parallel_enrichment_agent(
            "my-client", "http://localhost:8080",
            gti_gateway_url="http://localhost:8080",
            gti_enabled=True,
        )
        names = [a.name for a in agent.sub_agents]
        assert any("chronicle" in n for n in names)
        assert any("gti" in n for n in names)

    def test_use_parallel_flag_delegates(self):
        """create_enrichment_agent(use_parallel=True) delegates to parallel impl."""
        with patch("agents.enrichment.agent.McpToolset") as mock_ts, \
             patch("agents.enrichment.agent.build_mcp_connection") as mock_conn, \
             patch("agents.enrichment.agent.build_mcp_auth_provider", return_value=None):
            mock_ts.return_value = MagicMock()
            mock_conn.return_value = MagicMock()

            agent = create_enrichment_agent(
                "test-client", "http://localhost:8080",
                gti_enabled=True,
                use_parallel=True,
            )
            assert isinstance(agent, ParallelAgent)

    def test_use_parallel_false_returns_single_agent(self):
        """create_enrichment_agent(use_parallel=False) returns standard LlmAgent."""
        with patch("agents.enrichment.agent.McpToolset") as mock_ts, \
             patch("agents.enrichment.agent.build_mcp_connection") as mock_conn, \
             patch("agents.enrichment.agent.build_mcp_auth_provider", return_value=None):
            mock_ts.return_value = MagicMock()
            mock_conn.return_value = MagicMock()

            agent = create_enrichment_agent(
                "test-client", "http://localhost:8080",
                gti_enabled=True,
                use_parallel=False,
            )
            assert isinstance(agent, LlmAgent)


class TestEnrichmentMerger:
    """Tests for enrichment merger agent."""

    def test_merger_has_comment_tool(self):
        agent = create_enrichment_merger_agent("test-client", "http://localhost:8080")
        assert isinstance(agent, LlmAgent)
        assert "merger" in agent.name

    def test_merger_has_no_output_key(self):
        agent = create_enrichment_merger_agent("test-client", "http://localhost:8080")
        assert agent.output_key is None
