"""Tests for the A2A Agent Card builder."""

from a2a_gateway.agent_card import build_agent_card


class TestBuildAgentCard:
    """Tests that the Agent Card has all required SOC fields."""

    def test_card_has_required_fields(self):
        """Agent Card has name, url, version, skills."""
        card = build_agent_card("http://localhost:8082")
        assert card.name == "agentic-soc-orchestrator"
        assert card.url == "http://localhost:8082"
        assert card.version == "1.0.0"
        assert len(card.skills) == 4

    def test_card_has_four_soc_skills(self):
        """Agent Card declares all 4 SOC capabilities."""
        card = build_agent_card("http://localhost:8082")
        skill_ids = [s.id for s in card.skills]
        assert "alert-triage" in skill_ids
        assert "ioc-enrichment" in skill_ids
        assert "case-management" in skill_ids
        assert "containment-response" in skill_ids

    def test_card_declares_bearer_auth(self):
        """Security schemes include bearer token auth."""
        card = build_agent_card("http://localhost:8082")
        assert "bearer" in card.security_schemes
        scheme = card.security_schemes["bearer"]
        assert scheme.root.scheme == "bearer"

    def test_card_uses_rpc_url(self):
        """Agent Card URL matches the provided rpc_url."""
        card = build_agent_card("https://a2a.example.com")
        assert card.url == "https://a2a.example.com"
        assert card.provider.url == "https://a2a.example.com"

    def test_card_capabilities(self):
        """Capabilities: no streaming, no push notifications (Phase 1)."""
        card = build_agent_card("http://localhost:8082")
        assert card.capabilities.streaming is False
        assert card.capabilities.push_notifications is False

    def test_card_input_output_modes(self):
        """Supports text/plain and application/json."""
        card = build_agent_card("http://localhost:8082")
        assert "text/plain" in card.default_input_modes
        assert "application/json" in card.default_input_modes
        assert "text/plain" in card.default_output_modes
        assert "application/json" in card.default_output_modes

    def test_card_skills_have_tags(self):
        """Each skill has at least one tag."""
        card = build_agent_card("http://localhost:8082")
        for skill in card.skills:
            assert skill.tags, f"Skill {skill.id} has no tags"
            assert "security" in skill.tags, f"Skill {skill.id} missing 'security' tag"

    def test_card_serializes_to_json(self):
        """Agent Card serializes to valid JSON dict."""
        card = build_agent_card("http://localhost:8082")
        data = card.model_dump()
        assert isinstance(data, dict)
        assert data["name"] == "agentic-soc-orchestrator"
        assert len(data["skills"]) == 4
