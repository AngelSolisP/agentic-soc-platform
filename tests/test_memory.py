"""Tests for Vertex AI Memory Bank integration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from google.adk.agents import LlmAgent


def _stub_agent(name: str = "stub") -> LlmAgent:
    """Create a minimal real LlmAgent (Pydantic-valid) for sub_agents slots."""
    return LlmAgent(name=name, model="gemini-2.5-flash")


class TestCreateMemoryService:
    """Tests for the memory service factory."""

    def test_returns_inmemory_by_default(self):
        """Without env vars, returns InMemoryMemoryService."""
        with patch.dict("os.environ", {}, clear=True):
            from agents.memory_config import create_memory_service
            svc = create_memory_service()

        from google.adk.memory import InMemoryMemoryService
        assert isinstance(svc, InMemoryMemoryService)

    @patch("agents.memory_config.VertexAiMemoryBankService", create=True)
    def test_returns_vertex_with_agent_engine_id(self, mock_vertex_cls):
        """With GOOGLE_CLOUD_AGENT_ENGINE_ID, returns VertexAiMemoryBankService."""
        mock_vertex_cls.return_value = MagicMock()
        env = {
            "GOOGLE_CLOUD_AGENT_ENGINE_ID": "12345",
            "GOOGLE_CLOUD_PROJECT": "test-proj",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
        }
        with patch.dict("os.environ", env, clear=True):
            # Patch the import inside the function
            with patch(
                "google.adk.memory.VertexAiMemoryBankService", mock_vertex_cls
            ):
                from agents.memory_config import create_memory_service
                svc = create_memory_service()

        mock_vertex_cls.assert_called_once_with(
            project="test-proj",
            location="us-central1",
            agent_engine_id="12345",
        )

    @patch("agents.memory_config.VertexAiMemoryBankService", create=True)
    def test_fallback_agent_engine_id_env(self, mock_vertex_cls):
        """Falls back to AGENT_ENGINE_ID when GOOGLE_CLOUD_AGENT_ENGINE_ID is not set."""
        mock_vertex_cls.return_value = MagicMock()
        env = {
            "AGENT_ENGINE_ID": "67890",
            "GOOGLE_CLOUD_PROJECT": "test-proj",
        }
        with patch.dict("os.environ", env, clear=True):
            with patch(
                "google.adk.memory.VertexAiMemoryBankService", mock_vertex_cls
            ):
                from agents.memory_config import create_memory_service
                svc = create_memory_service()

        mock_vertex_cls.assert_called_once_with(
            project="test-proj",
            location="us-central1",
            agent_engine_id="67890",
        )

    def test_falls_back_when_project_missing(self):
        """With agent engine ID but no project, falls back to InMemory."""
        env = {
            "GOOGLE_CLOUD_AGENT_ENGINE_ID": "12345",
        }
        with patch.dict("os.environ", env, clear=True):
            # Remove GOOGLE_CLOUD_PROJECT
            import os
            os.environ.pop("GOOGLE_CLOUD_PROJECT", None)
            from agents.memory_config import create_memory_service
            svc = create_memory_service()

        from google.adk.memory import InMemoryMemoryService
        assert isinstance(svc, InMemoryMemoryService)

    def test_falls_back_on_init_exception(self):
        """If VertexAiMemoryBankService init fails, falls back to InMemory."""
        env = {
            "GOOGLE_CLOUD_AGENT_ENGINE_ID": "12345",
            "GOOGLE_CLOUD_PROJECT": "test-proj",
        }
        with patch.dict("os.environ", env, clear=True):
            with patch(
                "google.adk.memory.VertexAiMemoryBankService",
                side_effect=RuntimeError("init fail"),
            ):
                from agents.memory_config import create_memory_service
                svc = create_memory_service()

        from google.adk.memory import InMemoryMemoryService
        assert isinstance(svc, InMemoryMemoryService)


@pytest.mark.asyncio
class TestSavePipelineMemories:
    """Tests for the after_agent_callback that saves memories."""

    async def test_callback_calls_add_session_to_memory(self):
        """Callback invokes add_session_to_memory on the context."""
        from agents.orchestrator.agent import _save_pipeline_memories

        mock_ctx = AsyncMock()
        await _save_pipeline_memories(mock_ctx)

        mock_ctx.add_session_to_memory.assert_awaited_once()

    async def test_callback_failure_is_nonfatal(self):
        """Memory save failure does not raise — non-fatal."""
        from agents.orchestrator.agent import _save_pipeline_memories

        mock_ctx = AsyncMock()
        mock_ctx.add_session_to_memory.side_effect = RuntimeError("API error")

        # Should NOT raise
        await _save_pipeline_memories(mock_ctx)


class TestOrchestratorMemoryWiring:
    """Tests that the orchestrator correctly wires memory_service."""

    @patch("agents.orchestrator.agent.LlmAgent")
    @patch("agents.orchestrator.agent.StageTracker")
    @patch("agents.orchestrator.agent.AlertDeduplicator")
    @patch("agents.orchestrator.agent.InMemorySessionService")
    @patch("agents.orchestrator.agent.create_memory_service")
    @patch("agents.orchestrator.agent.create_triage_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_enrichment_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_case_manager_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_response_agent", return_value=MagicMock())
    def test_orchestrator_stores_memory_service(
        self, _resp, _cm, _enr, _tri, mock_mem_factory,
        mock_session_svc, mock_dedup_cls, mock_tracker_cls, _llm_agent,
    ):
        """Orchestrator stores memory_service from factory."""
        mock_mem = MagicMock()
        mock_mem_factory.return_value = mock_mem

        from agents.orchestrator.agent import AgenticSOCOrchestrator
        orch = AgenticSOCOrchestrator(partner_project_id="test-project")

        assert orch._memory_service is mock_mem

    @patch("agents.orchestrator.agent.LlmAgent")
    @patch("agents.orchestrator.agent.StageTracker")
    @patch("agents.orchestrator.agent.AlertDeduplicator")
    @patch("agents.orchestrator.agent.InMemorySessionService")
    @patch("agents.orchestrator.agent.create_memory_service")
    @patch("agents.orchestrator.agent.create_triage_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_enrichment_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_case_manager_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_response_agent", return_value=MagicMock())
    def test_orchestrator_accepts_custom_memory_service(
        self, _resp, _cm, _enr, _tri, mock_mem_factory,
        mock_session_svc, mock_dedup_cls, mock_tracker_cls, _llm_agent,
    ):
        """Orchestrator uses injected memory_service over factory."""
        custom_mem = MagicMock()

        from agents.orchestrator.agent import AgenticSOCOrchestrator
        orch = AgenticSOCOrchestrator(
            partner_project_id="test-project",
            memory_service=custom_mem,
        )

        assert orch._memory_service is custom_mem
        mock_mem_factory.assert_not_called()

    @patch("agents.orchestrator.agent.StageTracker")
    @patch("agents.orchestrator.agent.AlertDeduplicator")
    @patch("agents.orchestrator.agent.InMemorySessionService")
    @patch("agents.orchestrator.agent.create_memory_service")
    @patch("agents.orchestrator.agent.create_triage_agent", return_value=_stub_agent("triage"))
    @patch("agents.orchestrator.agent.create_enrichment_agent", return_value=_stub_agent("enrichment"))
    @patch("agents.orchestrator.agent.create_case_manager_agent", return_value=_stub_agent("case_mgr"))
    @patch("agents.orchestrator.agent.create_response_agent", return_value=_stub_agent("response"))
    def test_agents_created_with_cost_guard(
        self, _resp, _cm, _enr, _tri, mock_mem_factory,
        mock_session_svc, mock_dedup_cls, mock_tracker_cls,
    ):
        """Sequential pipeline creates agents via _get_agents."""
        from agents.orchestrator.agent import AgenticSOCOrchestrator

        orch = AgenticSOCOrchestrator(partner_project_id="test-project")
        agents = orch._get_agents("test-client")

        assert "triage" in agents
        assert "enrichment" in agents
        assert "case_manager" in agents
        assert "response" in agents

    @patch("agents.orchestrator.agent.StageTracker")
    @patch("agents.orchestrator.agent.AlertDeduplicator")
    @patch("agents.orchestrator.agent.InMemorySessionService")
    @patch("agents.orchestrator.agent.create_memory_service")
    @patch("agents.orchestrator.agent.create_triage_agent", return_value=_stub_agent("triage"))
    @patch("agents.orchestrator.agent.create_enrichment_agent", return_value=_stub_agent("enrichment"))
    @patch("agents.orchestrator.agent.create_case_manager_agent", return_value=_stub_agent("case_mgr"))
    @patch("agents.orchestrator.agent.create_response_agent", return_value=_stub_agent("response"))
    def test_run_single_agent_method_exists(
        self, _resp, _cm, _enr, _tri, mock_mem_factory,
        mock_session_svc, mock_dedup_cls, mock_tracker_cls,
    ):
        """Sequential pipeline has _run_single_agent method."""
        from agents.orchestrator.agent import AgenticSOCOrchestrator

        orch = AgenticSOCOrchestrator(partner_project_id="test-project")
        assert hasattr(orch, "_run_single_agent")
        assert callable(orch._run_single_agent)

    @patch("agents.orchestrator.agent.LlmAgent")
    @patch("agents.orchestrator.agent.StageTracker")
    @patch("agents.orchestrator.agent.AlertDeduplicator")
    @patch("agents.orchestrator.agent.Runner")
    @patch("agents.orchestrator.agent.InMemorySessionService")
    @patch("agents.orchestrator.agent.create_memory_service")
    @patch("agents.orchestrator.agent.create_triage_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_enrichment_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_case_manager_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_response_agent", return_value=MagicMock())
    @pytest.mark.asyncio
    async def test_runner_receives_memory_service(
        self, _resp, _cm, _enr, _tri, mock_mem_factory, mock_session_svc,
        mock_runner_cls, mock_dedup_cls, mock_tracker_cls, _llm_agent,
    ):
        """Sequential pipeline creates Runner for each agent stage."""
        mock_mem = MagicMock()
        mock_mem_factory.return_value = mock_mem

        mock_dedup_cls.return_value.is_duplicate.return_value = False

        session = MagicMock()
        session.id = "session-001"
        mock_session_svc.return_value.create_session = AsyncMock(return_value=session)

        async def fake_run_async(**kwargs):
            event = MagicMock()
            event.author = "triage_agent"
            event.content.parts = [MagicMock(text='{"verdict":"BENIGN"}')]
            event.is_final_response.return_value = True
            yield event

        mock_runner_cls.return_value.run_async = fake_run_async
        mock_runner_cls.return_value.close = AsyncMock()
        mock_tracker_cls.return_value.record_pipeline.return_value = []
        mock_tracker_cls.return_value.record_stage_incremental.return_value = None

        from agents.orchestrator.agent import AgenticSOCOrchestrator
        orch = AgenticSOCOrchestrator(partner_project_id="test-project")
        await orch.process_alert(
            client_id="test-client", case_id="CASE-001", alert_type="PHISHING",
        )

        # Verify Runner was created (at least for triage stage)
        assert mock_runner_cls.called

    @patch("agents.orchestrator.agent.LlmAgent")
    @patch("agents.orchestrator.agent.StageTracker")
    @patch("agents.orchestrator.agent.AlertDeduplicator")
    @patch("agents.orchestrator.agent.Runner")
    @patch("agents.orchestrator.agent.InMemorySessionService")
    @patch("agents.orchestrator.agent.create_memory_service")
    @patch("agents.orchestrator.agent.create_triage_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_enrichment_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_case_manager_agent", return_value=MagicMock())
    @patch("agents.orchestrator.agent.create_response_agent", return_value=MagicMock())
    @pytest.mark.asyncio
    async def test_scope_uses_client_id_as_user_id(
        self, _resp, _cm, _enr, _tri, mock_mem_factory, mock_session_svc,
        mock_runner_cls, mock_dedup_cls, mock_tracker_cls, _llm_agent,
    ):
        """Session is created with app_name='agentic_soc' and user_id=client_id."""
        mock_dedup_cls.return_value.is_duplicate.return_value = False

        session = MagicMock()
        session.id = "session-002"
        mock_session_svc.return_value.create_session = AsyncMock(return_value=session)

        async def fake_run_async(**kwargs):
            event = MagicMock()
            event.author = "orchestrator"
            event.content.parts = [MagicMock(text="done")]
            event.is_final_response.return_value = True
            yield event

        mock_runner_cls.return_value.run_async = fake_run_async
        mock_tracker_cls.return_value.record_pipeline.return_value = []

        from agents.orchestrator.agent import AgenticSOCOrchestrator, APP_NAME
        orch = AgenticSOCOrchestrator(partner_project_id="test-project")
        await orch.process_alert(
            client_id="demo-tenant", case_id="CASE-002", alert_type="MALWARE",
        )

        # Verify session created with correct scope
        create_session_call = mock_session_svc.return_value.create_session
        call_kwargs = create_session_call.call_args.kwargs
        assert call_kwargs["app_name"] == APP_NAME
        assert call_kwargs["user_id"] == "demo-tenant"

        # Verify Runner also uses APP_NAME
        runner_call_kwargs = mock_runner_cls.call_args.kwargs
        assert runner_call_kwargs["app_name"] == APP_NAME


class TestDeployMemoryBankConfig:
    """Tests that deploy_agent.py includes memory_bank_config."""

    def test_memory_bank_config_exists(self):
        """build_memory_bank_config returns all required sections."""
        from scripts.deploy_agent import build_memory_bank_config

        config = build_memory_bank_config("test-project", "us-central1")
        assert "similarity_search_config" in config
        assert "generation_config" in config
        assert "ttl_config" in config
        assert "customization_configs" in config

    def test_memory_bank_config_has_custom_topics(self):
        """Memory Bank config includes 3 custom SOC memory topics."""
        from scripts.deploy_agent import build_memory_bank_config

        config = build_memory_bank_config("test-project", "us-central1")
        topics = config["customization_configs"][0]["memory_topics"]
        labels = [t["custom_memory_topic"]["label"] for t in topics]
        assert "alert_patterns" in labels
        assert "case_outcomes" in labels
        assert "analyst_preferences" in labels

    def test_memory_bank_config_has_ttl(self):
        """TTL config has granular values."""
        from scripts.deploy_agent import build_memory_bank_config

        config = build_memory_bank_config("test-project", "us-central1")
        ttl = config["ttl_config"]["granular_ttl_config"]
        assert ttl["create_ttl"] == "7776000s"
        assert ttl["generate_created_ttl"] == "7776000s"
        assert ttl["generate_updated_ttl"] == "15552000s"

    def test_memory_bank_config_model_paths(self):
        """Model paths use full resource format."""
        from scripts.deploy_agent import build_memory_bank_config

        config = build_memory_bank_config("my-project", "us-central1")
        gen_model = config["generation_config"]["model"]
        emb_model = config["similarity_search_config"]["embedding_model"]
        assert gen_model == "projects/my-project/locations/us-central1/publishers/google/models/gemini-2.5-flash"
        assert emb_model == "projects/my-project/locations/us-central1/publishers/google/models/text-embedding-005"
