"""Tests for the Chronicle ID glossary and its integration into agent prompts."""

import pytest

from agents.id_glossary import CHRONICLE_ID_GLOSSARY


class TestChronicleIDGlossary:
    """Verify the glossary contains all required ID types and warnings."""

    def test_glossary_contains_all_five_id_types(self):
        assert "caseId" in CHRONICLE_ID_GLOSSARY
        assert "caseAlertId" in CHRONICLE_ID_GLOSSARY
        assert "alertGroupIdentifier" in CHRONICLE_ID_GLOSSARY
        assert "siemAlertId" in CHRONICLE_ID_GLOSSARY
        assert "IoC values" in CHRONICLE_ID_GLOSSARY

    def test_glossary_warns_against_common_mistakes(self):
        assert "NEVER pass caseId where caseAlertId is expected" in CHRONICLE_ID_GLOSSARY
        assert "NEVER pass caseAlertId where alertGroupIdentifier is expected" in CHRONICLE_ID_GLOSSARY
        assert "NEVER pass a caseId, caseAlertId, or any other ID as an indicator" in CHRONICLE_ID_GLOSSARY

    def test_glossary_documents_parameter_names(self):
        # Verify camelCase parameter names are documented
        assert "get_case_alert: `caseId` + `caseAlertId`" in CHRONICLE_ID_GLOSSARY
        assert "list_playbook_instances: `caseId` + `alertGroupIdentifier`" in CHRONICLE_ID_GLOSSARY
        assert "search_entity: `indicator`" in CHRONICLE_ID_GLOSSARY
        assert "summarize_entity: `query`" in CHRONICLE_ID_GLOSSARY

    def test_glossary_documents_hierarchy_diagram(self):
        assert "Case (caseId:" in CHRONICLE_ID_GLOSSARY
        assert "CaseAlert (caseAlertId:" in CHRONICLE_ID_GLOSSARY
        assert "alertGroupIdentifier:" in CHRONICLE_ID_GLOSSARY
        assert "InvolvedEntity (involvedEntityId:" in CHRONICLE_ID_GLOSSARY


class TestGlossaryIntegration:
    """Verify the glossary is embedded in all agent prompts."""

    def test_triage_prompt_includes_glossary(self):
        from agents.triage.prompts import TRIAGE_SYSTEM_PROMPT
        assert "Chronicle SOAR ID Hierarchy" in TRIAGE_SYSTEM_PROMPT
        assert "caseAlertId" in TRIAGE_SYSTEM_PROMPT

    def test_enrichment_prompt_includes_glossary(self):
        from agents.enrichment.prompts import ENRICHMENT_SYSTEM_PROMPT
        assert "Chronicle SOAR ID Hierarchy" in ENRICHMENT_SYSTEM_PROMPT

    def test_enrichment_no_gti_prompt_includes_glossary(self):
        from agents.enrichment.prompts import ENRICHMENT_SYSTEM_PROMPT_NO_GTI
        assert "Chronicle SOAR ID Hierarchy" in ENRICHMENT_SYSTEM_PROMPT_NO_GTI

    def test_case_manager_prompt_includes_glossary(self):
        from agents.case_manager.prompts import CASE_MANAGER_SYSTEM_PROMPT
        assert "Chronicle SOAR ID Hierarchy" in CASE_MANAGER_SYSTEM_PROMPT
        assert "caseAlertId" in CASE_MANAGER_SYSTEM_PROMPT

    def test_response_prompt_includes_glossary(self):
        from agents.response.prompts import RESPONSE_SYSTEM_PROMPT
        assert "Chronicle SOAR ID Hierarchy" in RESPONSE_SYSTEM_PROMPT

    def test_response_prompt_uses_camelcase_params(self):
        from agents.response.prompts import RESPONSE_SYSTEM_PROMPT
        # Verify camelCase params are documented for execute_manual_action
        assert "actionProvider" in RESPONSE_SYSTEM_PROMPT
        assert "actionName" in RESPONSE_SYSTEM_PROMPT
        assert "targetEntities" in RESPONSE_SYSTEM_PROMPT
        assert "alertGroupIdentifiers" in RESPONSE_SYSTEM_PROMPT
        assert "isPredefinedScope" in RESPONSE_SYSTEM_PROMPT
        # The execute_manual_action Schema section must NOT use snake_case params
        schema_section = RESPONSE_SYSTEM_PROMPT.split("execute_manual_action Schema")[1].split("## How to Get")[0]
        assert "action_provider" not in schema_section
        assert "is_predefined_scope" not in schema_section
        assert "alert_group_identifiers" not in schema_section

    def test_triage_output_schema_includes_case_alerts(self):
        from agents.triage.prompts import TRIAGE_SYSTEM_PROMPT
        assert "case_alerts" in TRIAGE_SYSTEM_PROMPT
        assert "alertGroupIdentifier" in TRIAGE_SYSTEM_PROMPT

    def test_chronicle_split_prompt_includes_glossary(self):
        from agents.enrichment.prompts_split import CHRONICLE_ENRICHMENT_PROMPT
        assert "Chronicle SOAR ID Hierarchy" in CHRONICLE_ENRICHMENT_PROMPT

    def test_case_manager_mentions_bulk_close(self):
        from agents.case_manager.prompts import CASE_MANAGER_SYSTEM_PROMPT
        assert "execute_bulk_close_case" in CASE_MANAGER_SYSTEM_PROMPT
