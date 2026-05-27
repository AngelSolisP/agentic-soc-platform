"""
Tier 1: Validate agent output JSON schemas (no LLM needed).

Tests that sample agent outputs conform to the expected schema defined in
each agent's system prompt. Run in CI as part of @pytest.mark.mock suite.

Updated 2026-03-27: Aligned with new triage schema (verdict/priority/confidence_score),
enrichment array format, and response action_provider/target_entities format.
"""
import pytest


# -- Sample outputs (representing what a well-behaved agent produces) --

SAMPLE_TRIAGE_OUTPUT = {
    "case_id": "CASE-001",
    "alert_type": "PHISHING",
    "verdict": "MALICIOUS",
    "priority": "HIGH",
    "confidence_score": 0.92,
    "recommended_action": "CONTAIN",
    "key_indicators": ["credential_harvesting_page", "malicious_ip"],
    "iocs_found": [
        {"type": "IP", "value": "203.0.113.42"},
        {"type": "DOMAIN", "value": "login-secure.example.com"},
    ],
    "summary": "High-confidence phishing attack detected.",
    "escalation_notes": "Immediate credential reset required.",
}

SAMPLE_TRIAGE_OUTPUT_BENIGN = {
    "case_id": "CASE-003",
    "alert_type": "SUSPICIOUS_PROCESS",
    "verdict": "BENIGN",
    "priority": "INFORMATIVE",
    "confidence_score": 0.95,
    "recommended_action": "CLOSE_FP",
    "key_indicators": ["known_scanner", "authorized_subnet"],
    "iocs_found": [],
    "summary": "Known Nessus scanner from authorized subnet.",
    "escalation_notes": "",
}

SAMPLE_TRIAGE_OUTPUT_INCONCLUSIVE = {
    "case_id": "CASE-010",
    "alert_type": "ANOMALOUS_LOGIN",
    "verdict": "INCONCLUSIVE",
    "priority": "MEDIUM",
    "confidence_score": 0.40,
    "recommended_action": "ESCALATE_T2",
    "key_indicators": ["impossible_travel"],
    "iocs_found": [{"type": "IP", "value": "198.51.100.5"}],
    "summary": "Insufficient data to determine login legitimacy.",
    "escalation_notes": "Need user confirmation of travel activity.",
}

SAMPLE_ENRICHMENT_OUTPUT = {
    "enrichments": [
        {
            "ioc_type": "IP",
            "ioc_value": "203.0.113.42",
            "gti_verdict": "MALICIOUS",
            "gti_score": 92,
            "gti_categories": ["command_and_control"],
            "malware_families": ["Emotet"],
            "mitre_techniques": ["T1071.001"],
            "historical_activity": {
                "first_seen": "2026-03-20T00:00:00Z",
                "last_seen": "2026-03-25T10:30:00Z",
                "internal_hits": 15,
            },
            "related_iocs": ["login-secure.example.com"],
            "context_summary": "Confirmed malicious C2 infrastructure.",
            "recommended_blocking": True,
        }
    ],
    "threat_context": {
        "overall_threat_level": "CRITICAL",
        "threat_actors": ["TA505"],
        "malware_families": ["Emotet"],
        "mitre_techniques": ["T1071.001"],
        "enrichment_completeness": 0.95,
    },
}

SAMPLE_ENRICHMENT_OUTPUT_UNKNOWN = {
    "enrichments": [
        {
            "ioc_type": "IP",
            "ioc_value": "192.0.2.99",
            "gti_verdict": "UNKNOWN",
            "gti_categories": [],
            "malware_families": [],
            "mitre_techniques": [],
            "historical_activity": {
                "first_seen": "",
                "last_seen": "",
                "internal_hits": 0,
            },
            "related_iocs": [],
            "context_summary": "No GTI data available for this indicator.",
            "recommended_blocking": False,
        }
    ],
    "threat_context": {
        "overall_threat_level": "UNKNOWN",
        "threat_actors": [],
        "malware_families": [],
        "mitre_techniques": [],
        "enrichment_completeness": 0.3,
    },
}

SAMPLE_RESPONSE_OUTPUT = {
    "proposed_action": "Isolate Endpoint",
    "action_provider": "CrowdStrike",
    "target_entities": [{"identifier": "workstation-01", "entity_type": "HOSTNAME"}],
    "justification": "Confirmed C2 communication requires immediate isolation.",
    "reversible": True,
    "estimated_impact": "Single workstation isolated, user notified.",
    "kill_chain_phase": "Command and Control",
    "hitl_required": True,
}

SAMPLE_RESPONSE_OUTPUT_NETWORK = {
    "proposed_action": "Block IP",
    "action_provider": "PaloAlto",
    "target_entities": [{"identifier": "198.51.100.10", "entity_type": "ADDRESS"}],
    "justification": "Active C2 IP must be blocked at perimeter.",
    "reversible": True,
    "estimated_impact": "External IP blocked, no internal impact.",
    "kill_chain_phase": "Command and Control",
    "hitl_required": True,
}

SAMPLE_RESPONSE_OUTPUT_IDENTITY = {
    "proposed_action": "Disable User",
    "action_provider": "Okta",
    "target_entities": [{"identifier": "john.doe@company.com", "entity_type": "USER"}],
    "justification": "Credential compromise confirmed via phishing.",
    "reversible": True,
    "estimated_impact": "User locked out until credential reset.",
    "kill_chain_phase": "Credential Access",
    "hitl_required": True,
}


# -- Schema validation helpers --

TRIAGE_REQUIRED_FIELDS = {
    "case_id": str,
    "alert_type": str,
    "verdict": str,
    "priority": str,
    "confidence_score": float,
    "recommended_action": str,
    "key_indicators": list,
    "iocs_found": list,
    "summary": str,
}

TRIAGE_VALID_VERDICTS = {"MALICIOUS", "SUSPICIOUS", "BENIGN", "INCONCLUSIVE"}
TRIAGE_VALID_PRIORITIES = {"INFORMATIVE", "LOW", "MEDIUM", "HIGH", "CRITICAL"}
TRIAGE_VALID_ACTIONS = {"CLOSE_FP", "ESCALATE_T2", "MONITOR", "CONTAIN"}

ENRICHMENT_REQUIRED_FIELDS = {
    "enrichments": list,
    "threat_context": dict,
}

ENRICHMENT_ITEM_REQUIRED_FIELDS = {
    "ioc_type": str,
    "ioc_value": str,
    "gti_verdict": str,
    "gti_categories": list,
    "malware_families": list,
    "mitre_techniques": list,
    "historical_activity": dict,
    "related_iocs": list,
    "context_summary": str,
    "recommended_blocking": bool,
}

ENRICHMENT_VALID_IOC_TYPES = {"IP", "DOMAIN", "HASH", "USER", "HOST", "URL"}
ENRICHMENT_VALID_VERDICTS = {"MALICIOUS", "SUSPICIOUS", "BENIGN", "UNDETECTED", "UNKNOWN"}
ENRICHMENT_VALID_THREAT_LEVELS = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"}

THREAT_CONTEXT_REQUIRED_FIELDS = {
    "overall_threat_level": str,
    "enrichment_completeness": float,
}

RESPONSE_REQUIRED_FIELDS = {
    "proposed_action": str,
    "action_provider": str,
    "target_entities": list,
    "justification": str,
    "hitl_required": bool,
}

RESPONSE_VALID_PROVIDERS = {"CrowdStrike", "SentinelOne", "PaloAlto", "Zscaler", "Okta", "AzureAD", "Scripts"}
RESPONSE_VALID_ENTITY_TYPES = {"ADDRESS", "HOSTNAME", "USER", "URL"}


def _validate_schema(output: dict, required_fields: dict) -> list[str]:
    """Return list of validation errors."""
    errors = []
    for field, expected_type in required_fields.items():
        if field not in output:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(output[field], expected_type):
            errors.append(f"Field {field}: expected {expected_type.__name__}, got {type(output[field]).__name__}")
    return errors


# -- Tests --

@pytest.mark.mock
class TestTriageOutputSchema:

    def test_required_fields_present(self):
        errors = _validate_schema(SAMPLE_TRIAGE_OUTPUT, TRIAGE_REQUIRED_FIELDS)
        assert not errors, f"Schema errors: {errors}"

    def test_benign_output_fields_present(self):
        errors = _validate_schema(SAMPLE_TRIAGE_OUTPUT_BENIGN, TRIAGE_REQUIRED_FIELDS)
        assert not errors, f"Schema errors: {errors}"

    def test_inconclusive_output_fields_present(self):
        errors = _validate_schema(SAMPLE_TRIAGE_OUTPUT_INCONCLUSIVE, TRIAGE_REQUIRED_FIELDS)
        assert not errors, f"Schema errors: {errors}"

    def test_verdict_valid_enum(self):
        assert SAMPLE_TRIAGE_OUTPUT["verdict"] in TRIAGE_VALID_VERDICTS

    def test_priority_valid_enum(self):
        assert SAMPLE_TRIAGE_OUTPUT["priority"] in TRIAGE_VALID_PRIORITIES

    def test_recommended_action_valid_enum(self):
        assert SAMPLE_TRIAGE_OUTPUT["recommended_action"] in TRIAGE_VALID_ACTIONS

    def test_confidence_score_range(self):
        score = SAMPLE_TRIAGE_OUTPUT["confidence_score"]
        assert 0.0 <= score <= 1.0, f"confidence_score {score} out of range [0.0, 1.0]"

    def test_confidence_score_range_low(self):
        score = SAMPLE_TRIAGE_OUTPUT_INCONCLUSIVE["confidence_score"]
        assert 0.0 <= score <= 1.0, f"confidence_score {score} out of range [0.0, 1.0]"

    def test_key_indicators_non_empty_for_malicious(self):
        assert len(SAMPLE_TRIAGE_OUTPUT["key_indicators"]) > 0

    def test_iocs_found_structure(self):
        for ioc in SAMPLE_TRIAGE_OUTPUT["iocs_found"]:
            assert "type" in ioc, "IoC missing 'type' field"
            assert "value" in ioc, "IoC missing 'value' field"

    def test_rejects_invalid_verdict(self):
        bad = {**SAMPLE_TRIAGE_OUTPUT, "verdict": "VERY_MALICIOUS"}
        assert bad["verdict"] not in TRIAGE_VALID_VERDICTS

    def test_rejects_invalid_priority(self):
        bad = {**SAMPLE_TRIAGE_OUTPUT, "priority": "EXTREME"}
        assert bad["priority"] not in TRIAGE_VALID_PRIORITIES

    def test_rejects_missing_field(self):
        bad = {k: v for k, v in SAMPLE_TRIAGE_OUTPUT.items() if k != "case_id"}
        errors = _validate_schema(bad, TRIAGE_REQUIRED_FIELDS)
        assert len(errors) == 1

    def test_rejects_invalid_confidence_score_type(self):
        bad = {**SAMPLE_TRIAGE_OUTPUT, "confidence_score": "high"}
        errors = _validate_schema(bad, TRIAGE_REQUIRED_FIELDS)
        assert any("confidence_score" in e for e in errors)


@pytest.mark.mock
class TestEnrichmentOutputSchema:

    def test_top_level_fields_present(self):
        errors = _validate_schema(SAMPLE_ENRICHMENT_OUTPUT, ENRICHMENT_REQUIRED_FIELDS)
        assert not errors, f"Schema errors: {errors}"

    def test_enrichment_items_present(self):
        assert len(SAMPLE_ENRICHMENT_OUTPUT["enrichments"]) > 0

    def test_enrichment_item_fields(self):
        item = SAMPLE_ENRICHMENT_OUTPUT["enrichments"][0]
        errors = _validate_schema(item, ENRICHMENT_ITEM_REQUIRED_FIELDS)
        assert not errors, f"Item schema errors: {errors}"

    def test_ioc_type_valid_enum(self):
        item = SAMPLE_ENRICHMENT_OUTPUT["enrichments"][0]
        assert item["ioc_type"] in ENRICHMENT_VALID_IOC_TYPES

    def test_gti_verdict_valid_enum(self):
        item = SAMPLE_ENRICHMENT_OUTPUT["enrichments"][0]
        assert item["gti_verdict"] in ENRICHMENT_VALID_VERDICTS

    def test_threat_context_fields(self):
        tc = SAMPLE_ENRICHMENT_OUTPUT["threat_context"]
        errors = _validate_schema(tc, THREAT_CONTEXT_REQUIRED_FIELDS)
        assert not errors, f"Threat context errors: {errors}"

    def test_threat_level_valid_enum(self):
        tc = SAMPLE_ENRICHMENT_OUTPUT["threat_context"]
        assert tc["overall_threat_level"] in ENRICHMENT_VALID_THREAT_LEVELS

    def test_enrichment_completeness_range(self):
        tc = SAMPLE_ENRICHMENT_OUTPUT["threat_context"]
        score = tc["enrichment_completeness"]
        assert 0.0 <= score <= 1.0, f"enrichment_completeness {score} out of range"

    def test_unknown_verdict_output(self):
        errors = _validate_schema(SAMPLE_ENRICHMENT_OUTPUT_UNKNOWN, ENRICHMENT_REQUIRED_FIELDS)
        assert not errors, f"Unknown output schema errors: {errors}"

    def test_unknown_item_fields(self):
        item = SAMPLE_ENRICHMENT_OUTPUT_UNKNOWN["enrichments"][0]
        errors = _validate_schema(item, ENRICHMENT_ITEM_REQUIRED_FIELDS)
        assert not errors, f"Unknown item errors: {errors}"

    def test_historical_activity_structure(self):
        hist = SAMPLE_ENRICHMENT_OUTPUT["enrichments"][0]["historical_activity"]
        assert "first_seen" in hist
        assert "last_seen" in hist
        assert "internal_hits" in hist

    def test_rejects_invalid_threat_level(self):
        bad_tc = {**SAMPLE_ENRICHMENT_OUTPUT["threat_context"], "overall_threat_level": "EXTREME"}
        assert bad_tc["overall_threat_level"] not in ENRICHMENT_VALID_THREAT_LEVELS

    def test_rejects_invalid_verdict(self):
        bad_item = {**SAMPLE_ENRICHMENT_OUTPUT["enrichments"][0], "gti_verdict": "DEFINITELY_BAD"}
        assert bad_item["gti_verdict"] not in ENRICHMENT_VALID_VERDICTS


@pytest.mark.mock
class TestResponseOutputSchema:

    def test_required_fields_present(self):
        errors = _validate_schema(SAMPLE_RESPONSE_OUTPUT, RESPONSE_REQUIRED_FIELDS)
        assert not errors, f"Schema errors: {errors}"

    def test_network_response_fields(self):
        errors = _validate_schema(SAMPLE_RESPONSE_OUTPUT_NETWORK, RESPONSE_REQUIRED_FIELDS)
        assert not errors, f"Schema errors: {errors}"

    def test_identity_response_fields(self):
        errors = _validate_schema(SAMPLE_RESPONSE_OUTPUT_IDENTITY, RESPONSE_REQUIRED_FIELDS)
        assert not errors, f"Schema errors: {errors}"

    def test_action_provider_valid_enum(self):
        assert SAMPLE_RESPONSE_OUTPUT["action_provider"] in RESPONSE_VALID_PROVIDERS

    def test_target_entities_structure(self):
        for entity in SAMPLE_RESPONSE_OUTPUT["target_entities"]:
            assert "identifier" in entity, "Entity missing 'identifier'"
            assert "entity_type" in entity, "Entity missing 'entity_type'"
            assert entity["entity_type"] in RESPONSE_VALID_ENTITY_TYPES

    def test_hitl_always_required(self):
        assert SAMPLE_RESPONSE_OUTPUT["hitl_required"] is True

    def test_justification_non_empty(self):
        assert len(SAMPLE_RESPONSE_OUTPUT["justification"]) > 0

    def test_rejects_invalid_provider(self):
        bad = {**SAMPLE_RESPONSE_OUTPUT, "action_provider": "MAGIC"}
        assert bad["action_provider"] not in RESPONSE_VALID_PROVIDERS

    def test_rejects_missing_hitl(self):
        bad = {k: v for k, v in SAMPLE_RESPONSE_OUTPUT.items() if k != "hitl_required"}
        errors = _validate_schema(bad, RESPONSE_REQUIRED_FIELDS)
        assert any("hitl_required" in e for e in errors)
