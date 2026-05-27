"""Tests for Risk Scoring module (Phase A)."""

from agents.risk_scoring import (
    calculate_risk_modifier,
    aggregate_entity_risk,
    format_risk_context_for_prompt,
    RISK_MODIFIERS,
)


class TestCalculateRiskModifier:
    """Tests for individual watchlist risk modifier calculation."""

    def test_critical_assets_watchlist(self):
        assert calculate_risk_modifier("critical_assets_prod") == 0.20

    def test_privileged_accounts_watchlist(self):
        assert calculate_risk_modifier("privileged_accounts") == 0.15

    def test_vip_users_watchlist(self):
        assert calculate_risk_modifier("vip_users_executive") == 0.15

    def test_compromised_entities_watchlist(self):
        assert calculate_risk_modifier("compromised_entities_q4") == 0.20

    def test_unknown_watchlist_gets_default(self):
        assert calculate_risk_modifier("custom_watchlist_xyz") == 0.10

    def test_case_insensitive(self):
        assert calculate_risk_modifier("CRITICAL_ASSETS") == 0.20


class TestAggregateEntityRisk:
    """Tests for multi-entity risk aggregation."""

    def test_empty_watchlists_returns_none(self):
        result = aggregate_entity_risk([])
        assert result["risk_level"] == "NONE"
        assert result["total_modifier"] == 0.0

    def test_single_entity_on_watchlist(self):
        entries = [{"entity": "admin@corp.com", "watchlist": "privileged_accounts"}]
        result = aggregate_entity_risk(entries)
        assert result["risk_level"] == "MEDIUM"
        assert result["total_modifier"] == 0.15
        assert len(result["watchlisted_entities"]) == 1

    def test_multiple_entities_caps_at_030(self):
        entries = [
            {"entity": "10.0.0.1", "watchlist": "critical_assets"},
            {"entity": "admin@corp.com", "watchlist": "privileged_accounts"},
            {"entity": "ceo@corp.com", "watchlist": "vip_users"},
        ]
        result = aggregate_entity_risk(entries)
        # 0.20 + 0.15 + 0.15 = 0.50 → capped at 0.30
        assert result["total_modifier"] == 0.30
        assert result["risk_level"] == "HIGH"

    def test_highest_risk_watchlist_tracked(self):
        entries = [
            {"entity": "host-01", "watchlist": "compromised_entities"},
            {"entity": "user@corp.com", "watchlist": "custom_list"},
        ]
        result = aggregate_entity_risk(entries)
        assert result["highest_risk_watchlist"] == "compromised_entities"


class TestFormatRiskContext:
    """Tests for risk context prompt formatting."""

    def test_no_risk_entities(self):
        summary = aggregate_entity_risk([])
        text = format_risk_context_for_prompt(summary)
        assert "No entities on risk watchlists" in text

    def test_with_risk_entities(self):
        entries = [{"entity": "admin@corp.com", "watchlist": "privileged_accounts"}]
        summary = aggregate_entity_risk(entries)
        text = format_risk_context_for_prompt(summary)
        assert "MEDIUM" in text
        assert "admin@corp.com" in text
        assert "privileged_accounts" in text
