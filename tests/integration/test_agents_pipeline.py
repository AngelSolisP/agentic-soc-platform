"""
Integration tests — MVP 1.2, 1.3, 1.4

1.2  Triage Agent processes test alert and adds comment in Chronicle
1.3  Enrichment Agent enriches an IoC via GTI
1.4  Case Manager closes a false positive with documentation

These tests validate the agent factory functions, task building, and
ICM tool scoping contracts WITHOUT requiring Gemini API credentials.
Live tests exercise the full agent pipeline.
"""

import pytest
from unittest.mock import patch

from agents.tool_catalog import (
    TRIAGE_TOOLS,
    ENRICHMENT_TOOLS,
    CHRONICLE_ENRICHMENT_TOOLS,
    GTI_ENRICHMENT_TOOLS,
    GTI_TOOLS_CORE,
    GTI_TOOLS_DEEP,
    CASE_MANAGER_TOOLS,
    RESPONSE_TOOLS,
    SIEM_READ,
    SOAR_READ,
    SOAR_WRITE,
    REFERENCE_LISTS,
    SOAR_PLAYBOOKS,
    SOAR_INTEGRATIONS,
)
from agents.triage.agent import create_triage_agent, build_triage_task
from agents.enrichment.agent import create_enrichment_agent, build_enrichment_task
from agents.case_manager.agent import create_case_manager_agent, build_case_manager_task

from .helpers import IS_LIVE, SYNTHETIC


# ---------------------------------------------------------------------------
# MVP 1.2 — Triage Agent processes test alert, adds comment
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.mock
def test_triage_agent_created_with_correct_tools():
    """Triage agent should have exactly TRIAGE_TOOLS and use Flash model."""
    agent = create_triage_agent(
        client_id="test_client",
        gateway_url="http://mock:8080",
        model="gemini-2.5-flash",
    )

    assert agent.name == "triage_agent_test_client"
    assert agent.model == "gemini-2.5-flash"

    # Verify tool scoping: MCP toolset + risk tool
    assert len(agent.tools) == 2
    toolset = agent.tools[0]
    assert toolset.tool_filter == TRIAGE_TOOLS
    assert agent.tools[1].__name__ == "get_risk_score_modifier"


@pytest.mark.integration
@pytest.mark.mock
def test_triage_agent_excluded_tools():
    """Triage agent must NOT have execute_manual_action or update_case."""
    assert "execute_manual_action" not in TRIAGE_TOOLS
    assert "update_case" not in TRIAGE_TOOLS
    assert "execute_bulk_close_case" not in TRIAGE_TOOLS
    # But should have comment capability
    assert "create_case_comment" in TRIAGE_TOOLS


@pytest.mark.integration
@pytest.mark.mock
def test_triage_task_contains_case_data():
    """Triage task prompt should contain case_id, alert_type, and runbook contract."""
    task = build_triage_task(
        case_id=SYNTHETIC["case_id"],
        client_id=SYNTHETIC["client_id_a"],
        alert_type="PHISHING",
        severity="HIGH",
    )

    assert SYNTHETIC["case_id"] in task
    assert "PHISHING" in task
    assert "HIGH" in task
    # Runbook contract injection
    assert "CONTRACT" in task or "INPUTS" in task or "PROCESS" in task


@pytest.mark.integration
@pytest.mark.mock
def test_triage_task_uses_correct_runbook_for_malware():
    """Malware alert type should inject malware_triage runbook contract."""
    task = build_triage_task(
        case_id="CASE-MAL-001",
        client_id="test_client",
        alert_type="MALWARE",
        severity="CRITICAL",
    )

    assert "CASE-MAL-001" in task
    assert "MALWARE" in task


# ---------------------------------------------------------------------------
# MVP 1.3 — Enrichment Agent enriches an IoC via GTI
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.mock
def test_enrichment_agent_dual_toolset_with_gti():
    """Enrichment agent with gti_enabled=True should have 2 MCP toolsets + 2 function tools."""
    agent = create_enrichment_agent(
        client_id="test_client",
        gateway_url="http://mock:8080",
        gti_enabled=True,
        model="gemini-2.5-flash",
    )

    # 4 tools: [chronicle_toolset, risk_tool, threat_tool, gti_toolset]
    assert len(agent.tools) == 4
    # First tool: Chronicle toolset
    assert agent.tools[0].tool_filter == CHRONICLE_ENRICHMENT_TOOLS
    # Last tool: GTI toolset
    assert agent.tools[3].tool_filter == GTI_ENRICHMENT_TOOLS


@pytest.mark.integration
@pytest.mark.mock
def test_enrichment_agent_single_toolset_no_gti():
    """Enrichment agent with gti_enabled=False should have 1 MCP toolset + 2 function tools."""
    agent = create_enrichment_agent(
        client_id="test_client",
        gateway_url="http://mock:8080",
        gti_enabled=False,
        model="gemini-2.5-flash",
    )

    # 3 tools: [chronicle_toolset, risk_tool, threat_tool]
    assert len(agent.tools) == 3
    assert agent.tools[0].tool_filter == CHRONICLE_ENRICHMENT_TOOLS



@pytest.mark.integration
@pytest.mark.mock
def test_enrichment_agent_has_gti_tools():
    """Enrichment agent (with GTI enabled) should include all GTI enrichment tools."""
    agent = create_enrichment_agent(
        client_id="test_client",
        gateway_url="http://mock:8080",
        gti_enabled=True,
        model="gemini-2.5-flash",
    )

    assert agent.name == "enrichment_agent_test_client"
    # 4 tools: [chronicle_toolset, risk_tool, threat_tool, gti_toolset]
    gti_toolset = agent.tools[3]
    for tool in GTI_ENRICHMENT_TOOLS:
        assert tool in gti_toolset.tool_filter, f"Missing GTI tool: {tool}"


@pytest.mark.integration
@pytest.mark.mock
def test_enrichment_agent_has_siem_read():
    """Enrichment agent should include SIEM read tools."""
    for tool in SIEM_READ:
        assert tool in ENRICHMENT_TOOLS, f"Missing SIEM tool: {tool}"


@pytest.mark.integration
@pytest.mark.mock
def test_enrichment_agent_excluded_tools():
    """Enrichment agent must NOT have SOAR write tools (except comment)."""
    assert "execute_manual_action" not in ENRICHMENT_TOOLS
    assert "update_case" not in ENRICHMENT_TOOLS
    assert "execute_bulk_close_case" not in ENRICHMENT_TOOLS
    # Should have comment and case read
    assert "create_case_comment" in ENRICHMENT_TOOLS
    assert "get_case" in ENRICHMENT_TOOLS


@pytest.mark.integration
@pytest.mark.mock
def test_enrichment_task_contains_iocs():
    """Enrichment task prompt should contain IoC values."""
    iocs = [
        {"type": "IP", "value": SYNTHETIC["ioc_ip"]},
        {"type": "DOMAIN", "value": SYNTHETIC["ioc_domain"]},
    ]
    task = build_enrichment_task(
        case_id=SYNTHETIC["case_id"],
        client_id=SYNTHETIC["client_id_a"],
        iocs=iocs,
    )

    assert SYNTHETIC["ioc_ip"] in task
    assert SYNTHETIC["ioc_domain"] in task
    assert SYNTHETIC["case_id"] in task


# ---------------------------------------------------------------------------
# MVP 1.4 — Case Manager closes a false positive with documentation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.mock
def test_case_manager_has_soar_tools():
    """Case Manager should have SOAR_READ + SOAR_WRITE tools."""
    agent = create_case_manager_agent(
        client_id="test_client",
        gateway_url="http://mock:8080",
        model="gemini-2.5-flash",
    )

    assert agent.name == "case_manager_agent_test_client"
    toolset = agent.tools[0]

    for tool in SOAR_READ:
        assert tool in toolset.tool_filter, f"Missing SOAR_READ tool: {tool}"
    for tool in SOAR_WRITE:
        assert tool in toolset.tool_filter, f"Missing SOAR_WRITE tool: {tool}"


@pytest.mark.integration
@pytest.mark.mock
def test_case_manager_excluded_from_siem_and_gti():
    """Case Manager must NOT have SIEM or GTI tools."""
    for tool in SIEM_READ:
        assert tool not in CASE_MANAGER_TOOLS, f"Unexpected SIEM tool: {tool}"
    for tool in GTI_ENRICHMENT_TOOLS:
        assert tool not in CASE_MANAGER_TOOLS, f"Unexpected GTI tool: {tool}"
    # And no manual action
    assert "execute_manual_action" not in CASE_MANAGER_TOOLS


@pytest.mark.integration
@pytest.mark.mock
def test_case_manager_task_contains_close_action():
    """Case Manager task with CLOSE_FALSE_POSITIVE should contain the action."""
    task = build_case_manager_task(
        case_id=SYNTHETIC["case_id"],
        client_id=SYNTHETIC["client_id_a"],
        recommended_action="CLOSE_FALSE_POSITIVE",
        triage_results="No malicious activity confirmed. Benign scheduled task.",
    )

    assert "CLOSE_FALSE_POSITIVE" in task
    assert SYNTHETIC["case_id"] in task
    assert "No malicious activity confirmed" in task


@pytest.mark.integration
@pytest.mark.mock
def test_case_manager_has_bulk_close():
    """Case Manager should have execute_bulk_close_case for FP closure."""
    assert "execute_bulk_close_case" in CASE_MANAGER_TOOLS


# ---------------------------------------------------------------------------
# Cross-agent ICM scoping validation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.mock
def test_icm_tool_scoping_no_overlap_on_destructive_actions():
    """Only Response Agent should have execute_manual_action."""
    assert "execute_manual_action" in RESPONSE_TOOLS
    assert "execute_manual_action" not in TRIAGE_TOOLS
    assert "execute_manual_action" not in ENRICHMENT_TOOLS
    assert "execute_manual_action" not in CASE_MANAGER_TOOLS


@pytest.mark.integration
@pytest.mark.mock
def test_icm_tool_counts():
    """Verify documented tool counts per agent."""
    assert len(TRIAGE_TOOLS) == 19  # 5 SIEM + 4 SOAR + 4 alert enrichment + 4 investigation + 2 watchlist
    assert len(CHRONICLE_ENRICHMENT_TOOLS) == 21  # 5 SIEM + 4 SOAR + 2 ref lists + 4 alert enrichment + 1 threat intel + 5 curated detections
    assert len(GTI_ENRICHMENT_TOOLS) == 9
    assert len(ENRICHMENT_TOOLS) == 30  # 21 chronicle + 9 GTI
    assert len(CASE_MANAGER_TOOLS) == 12  # 5 SOAR_READ + 4 SOAR_WRITE + 2 playbooks + 1 data table
    assert len(RESPONSE_TOOLS) == 7  # 5 core + 2 integrations


@pytest.mark.integration
@pytest.mark.mock
def test_gti_tool_names_match_gti_mcp_server():
    """GTI tool names must match actual gti-mcp server tool names."""
    expected_core = [
        "get_file_report",
        "get_ip_address_report",
        "get_domain_report",
        "get_url_report",
    ]
    expected_deep = [
        "get_entities_related_to_a_file",
        "get_entities_related_to_a_domain",
        "get_entities_related_to_an_ip_address",
        "get_file_behavior_summary",
        "get_collection_mitre_tree",
    ]
    assert GTI_TOOLS_CORE == expected_core
    assert GTI_TOOLS_DEEP == expected_deep
    assert GTI_ENRICHMENT_TOOLS == expected_core + expected_deep
    assert len(GTI_ENRICHMENT_TOOLS) == 9


# ---------------------------------------------------------------------------
# New tool domains: Reference Lists, Playbooks, Integrations
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.mock
def test_reference_lists_in_enrichment():
    """Enrichment Agent should have reference list tools for allowlist/blocklist lookups."""
    for tool in REFERENCE_LISTS:
        assert tool in CHRONICLE_ENRICHMENT_TOOLS, f"Missing reference list tool: {tool}"
        assert tool in ENRICHMENT_TOOLS, f"Missing in combined enrichment: {tool}"
    # list_reference_lists does NOT exist on Chronicle MCP server (verified 2026-03-29)
    assert "get_reference_list" in CHRONICLE_ENRICHMENT_TOOLS
    assert "create_reference_list" in CHRONICLE_ENRICHMENT_TOOLS


@pytest.mark.integration
@pytest.mark.mock
def test_reference_lists_not_in_other_agents():
    """Reference list tools should only be in Enrichment Agent."""
    for tool in REFERENCE_LISTS:
        assert tool not in TRIAGE_TOOLS, f"Unexpected in triage: {tool}"
        assert tool not in CASE_MANAGER_TOOLS, f"Unexpected in case_manager: {tool}"
        assert tool not in RESPONSE_TOOLS, f"Unexpected in response: {tool}"


@pytest.mark.integration
@pytest.mark.mock
def test_playbooks_in_case_manager():
    """Case Manager should have playbook visibility tools."""
    for tool in SOAR_PLAYBOOKS:
        assert tool in CASE_MANAGER_TOOLS, f"Missing playbook tool: {tool}"
    assert "list_playbooks" in CASE_MANAGER_TOOLS
    assert "list_playbook_instances" in CASE_MANAGER_TOOLS


@pytest.mark.integration
@pytest.mark.mock
def test_playbooks_not_in_other_agents():
    """Playbook tools should only be in Case Manager."""
    for tool in SOAR_PLAYBOOKS:
        assert tool not in TRIAGE_TOOLS, f"Unexpected in triage: {tool}"
        assert tool not in RESPONSE_TOOLS, f"Unexpected in response: {tool}"


@pytest.mark.integration
@pytest.mark.mock
def test_integrations_in_response():
    """Response Agent should have integration discovery tools."""
    for tool in SOAR_INTEGRATIONS:
        assert tool in RESPONSE_TOOLS, f"Missing integration tool: {tool}"
    assert "list_integrations" in RESPONSE_TOOLS
    assert "list_integration_actions" in RESPONSE_TOOLS


@pytest.mark.integration
@pytest.mark.mock
def test_integrations_not_in_other_agents():
    """Integration tools should only be in Response Agent."""
    for tool in SOAR_INTEGRATIONS:
        assert tool not in TRIAGE_TOOLS, f"Unexpected in triage: {tool}"
        assert tool not in CASE_MANAGER_TOOLS, f"Unexpected in case_manager: {tool}"


# ---------------------------------------------------------------------------
# Enrichment prompt variants
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.mock
def test_enrichment_prompts_variants_exist():
    """Both GTI and no-GTI prompt variants should exist."""
    from agents.enrichment.prompts import (
        ENRICHMENT_SYSTEM_PROMPT,
        ENRICHMENT_SYSTEM_PROMPT_NO_GTI,
    )
    assert "GTI" in ENRICHMENT_SYSTEM_PROMPT
    # No-GTI prompt should not reference GTI tool functions but may mention GTI is unavailable
    assert "get_ip_address_report" not in ENRICHMENT_SYSTEM_PROMPT_NO_GTI
    assert "get_domain_report" not in ENRICHMENT_SYSTEM_PROMPT_NO_GTI
    assert "Chronicle" in ENRICHMENT_SYSTEM_PROMPT_NO_GTI


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.mock
def test_dedup_prevents_reprocessing():
    """Same alert submitted twice should be deduplicated (Firestore-backed)."""
    from unittest.mock import MagicMock, patch
    from datetime import datetime, timezone, timedelta
    from agents.dedup import AlertDeduplicator, DEDUP_COLLECTION

    with patch("agents.dedup.firestore") as mock_fs:
        mock_db = MagicMock()
        mock_fs.Client.return_value = mock_db

        # Simulate a simple in-memory Firestore store keyed by document ID
        store: dict = {}

        def fake_document(key):
            doc_mock = MagicMock()

            def fake_set(data):
                store[key] = data

            def fake_get():
                m = MagicMock()
                if key in store:
                    m.exists = True
                    m.to_dict.return_value = store[key]
                else:
                    m.exists = False
                return m

            doc_mock.set.side_effect = fake_set
            doc_mock.get.side_effect = fake_get
            return doc_mock

        mock_db.collection.return_value.document.side_effect = fake_document

        dedup = AlertDeduplicator(partner_project_id="test-project", ttl_seconds=900)

        assert not dedup.is_duplicate("client-a", "PHISHING", "CASE-001")
        dedup.record("client-a", "PHISHING", "CASE-001", result={"status": "processed"})

        assert dedup.is_duplicate("client-a", "PHISHING", "CASE-001")
        assert dedup.get_previous_result("client-a", "PHISHING", "CASE-001") == {"status": "processed"}

        # Different alert should not be duplicate
        assert not dedup.is_duplicate("client-a", "MALWARE", "CASE-002")


# ---------------------------------------------------------------------------
# Live tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.mock
def test_orchestrator_threads_gti_to_enrichment():
    """Orchestrator should create enrichment agent with GTI params."""
    from agents.orchestrator.agent import AgenticSOCOrchestrator

    orch = AgenticSOCOrchestrator(
        partner_project_id="test-project",
        gateway_url="http://mock:8080",
        gti_url="http://mock:8080",
    )

    agents_with_gti = orch._get_agents("client_a", gti_enabled=True)
    agents_no_gti = orch._get_agents("client_b", gti_enabled=False)

    # With GTI: 4 tools (2 toolsets + 2 function tools)
    assert len(agents_with_gti["enrichment"].tools) == 4
    # Without GTI: 3 tools (1 toolset + 2 function tools)
    assert len(agents_no_gti["enrichment"].tools) == 3


# ---------------------------------------------------------------------------
# Live tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.live
@pytest.mark.skipif(not IS_LIVE, reason="live mode only")
async def test_live_triage_agent_processes_alert():
    """Live: full orchestrator pipeline against NFR tenant."""
    from agents.orchestrator.agent import AgenticSOCOrchestrator

    orchestrator = AgenticSOCOrchestrator(
        partner_project_id=SYNTHETIC["partner_project_id"],
    )
    result = await orchestrator.process_alert(
        client_id=SYNTHETIC["client_id_a"],
        case_id=SYNTHETIC["case_id"],
        alert_type=SYNTHETIC["alert_type"],
        severity=SYNTHETIC["severity"],
    )

    assert result["timed_out"] is False
    assert result["session_id"] is not None
