"""
Tier 1: Validate agent business rules (no LLM needed).

Tests that agent decision logic follows documented business rules from
runbooks and system prompts. Run in CI as part of @pytest.mark.mock suite.

Updated 2026-03-27: Aligned with new triage schema (verdict/priority/confidence_score),
enrichment array format, and expanded business rule coverage.
"""
import pytest


# -- Business rule functions (reusable for live eval post-processing) --

def validate_triage_rules(output: dict) -> list[str]:
    """Check triage output against documented business rules."""
    violations = []
    verdict = output.get("verdict", "")
    action = output.get("recommended_action", "")
    priority = output.get("priority", "")
    confidence = output.get("confidence_score", 0.0)

    # Rule 1: MALICIOUS verdict -> never CLOSE_FP
    if verdict == "MALICIOUS" and action == "CLOSE_FP":
        violations.append("MALICIOUS verdict must not result in CLOSE_FP")

    # Rule 2: MALICIOUS verdict + high confidence -> should be CONTAIN or ESCALATE_T2
    if verdict == "MALICIOUS" and confidence >= 0.8 and action not in ("CONTAIN", "ESCALATE_T2"):
        violations.append(
            f"MALICIOUS verdict with confidence >= 0.8 should result in CONTAIN or ESCALATE_T2, got {action}"
        )

    # Rule 3: BENIGN -> should either CLOSE_FP or MONITOR, not CONTAIN/ESCALATE
    if verdict == "BENIGN" and action in ("CONTAIN", "ESCALATE_T2"):
        violations.append(f"BENIGN verdict should not result in {action}")

    # Rule 4: CLOSE_FP -> confidence_score must be > 0.85
    if action == "CLOSE_FP" and confidence <= 0.85:
        violations.append(
            f"CLOSE_FP action requires confidence_score > 0.85, got {confidence}"
        )

    # Rule 5: INCONCLUSIVE -> must ESCALATE_T2 or MONITOR (never CLOSE_FP or CONTAIN)
    if verdict == "INCONCLUSIVE" and action in ("CLOSE_FP", "CONTAIN"):
        violations.append(f"INCONCLUSIVE verdict should not result in {action}")

    # Rule 6: Low confidence (< 0.5) -> must ESCALATE_T2 (needs human review)
    if confidence < 0.5 and action != "ESCALATE_T2":
        violations.append(
            f"confidence_score < 0.5 should result in ESCALATE_T2, got {action}"
        )

    # Rule 7: CRITICAL priority -> must not be CLOSE_FP
    if priority == "CRITICAL" and action == "CLOSE_FP":
        violations.append("CRITICAL priority must not result in CLOSE_FP")

    # Rule 8: confidence_score must be in [0.0, 1.0]
    if not (0.0 <= confidence <= 1.0):
        violations.append(f"confidence_score {confidence} out of valid range [0.0, 1.0]")

    return violations


def validate_enrichment_rules(output: dict) -> list[str]:
    """Check enrichment output against documented business rules."""
    violations = []
    threat_context = output.get("threat_context", {})
    threat_level = threat_context.get("overall_threat_level", "")
    enrichments = output.get("enrichments", [])

    for item in enrichments:
        verdict = item.get("gti_verdict", "")
        blocking = item.get("recommended_blocking", False)

        # Rule 1: MALICIOUS gti_verdict -> recommended_blocking must be true
        if verdict == "MALICIOUS" and not blocking:
            violations.append(
                f"MALICIOUS gti_verdict for {item.get('ioc_value', '?')} must set recommended_blocking=true"
            )

        # Rule 2: UNKNOWN gti_verdict -> should not recommend blocking
        if verdict == "UNKNOWN" and blocking:
            violations.append(
                f"UNKNOWN gti_verdict for {item.get('ioc_value', '?')} should not set recommended_blocking=true"
            )

        # Rule 3: UNDETECTED gti_verdict -> should not recommend blocking
        if verdict == "UNDETECTED" and blocking:
            violations.append(
                f"UNDETECTED gti_verdict for {item.get('ioc_value', '?')} should not set recommended_blocking=true"
            )

    # Rule 4: UNKNOWN gti_verdict on all items -> threat_level should be UNKNOWN or LOW
    if enrichments and all(e.get("gti_verdict") == "UNKNOWN" for e in enrichments):
        if threat_level not in ("UNKNOWN", "LOW"):
            violations.append(
                f"All UNKNOWN GTI verdicts should not produce {threat_level} overall_threat_level"
            )

    # Rule 5: Any MALICIOUS with CRITICAL context -> enrichment_completeness should be > 0.5
    if threat_level == "CRITICAL":
        completeness = threat_context.get("enrichment_completeness", 0.0)
        if completeness < 0.5:
            violations.append(
                f"CRITICAL threat_level with enrichment_completeness {completeness} < 0.5 is unreliable"
            )

    return violations


def validate_response_rules(output: dict) -> list[str]:
    """Check response output against documented business rules."""
    violations = []

    # Rule 1: hitl_required must ALWAYS be true
    if not output.get("hitl_required", False):
        violations.append("hitl_required must always be true for response actions")

    # Rule 2: Must have justification
    if not output.get("justification", "").strip():
        violations.append("Response proposal must include justification")

    # Rule 3: target_entities must have valid structure when present
    for entity in output.get("target_entities", []):
        if "identifier" not in entity:
            violations.append("target_entity missing 'identifier' field")
        if "entity_type" not in entity:
            violations.append("target_entity missing 'entity_type' field")

    return violations


def validate_case_manager_rules(
    recommended_action: str,
    triage_verdict: str,
    triage_confidence: float,
    action_taken: str,
) -> list[str]:
    """Check case manager follows action routing rules."""
    violations = []

    # Rule 1: Never close MALICIOUS verdict without T2 review
    if triage_verdict == "MALICIOUS" and action_taken == "CLOSED_FP":
        violations.append("Cannot close MALICIOUS verdict case as false positive without T2 review")

    # Rule 2: ESCALATE_T2 must update priority
    if recommended_action == "ESCALATE_T2" and action_taken == "COMMENT_ONLY":
        violations.append("ESCALATE_T2 must update case priority, not just add comment")

    # Rule 3: CLOSE_FP requires high triage confidence
    if recommended_action == "CLOSE_FP" and action_taken == "CLOSED_FP" and triage_confidence < 0.85:
        violations.append(
            f"Cannot close as FP with triage confidence {triage_confidence} < 0.85"
        )

    # Rule 4: CONTAIN must be routed through Response Agent (not Case Manager)
    if recommended_action == "CONTAIN" and action_taken == "EXECUTED_ACTION":
        violations.append("CONTAIN actions must be routed to Response Agent, not executed by Case Manager")

    return violations


# -- Tests --

@pytest.mark.mock
class TestTriageBusinessRules:

    def test_malicious_blocks_close_fp(self):
        output = {
            "verdict": "MALICIOUS",
            "recommended_action": "CLOSE_FP",
            "priority": "HIGH",
            "confidence_score": 0.90,
        }
        violations = validate_triage_rules(output)
        assert any("CLOSE_FP" in v for v in violations)

    def test_malicious_high_confidence_requires_contain_or_escalate(self):
        output = {
            "verdict": "MALICIOUS",
            "recommended_action": "MONITOR",
            "priority": "HIGH",
            "confidence_score": 0.90,
        }
        violations = validate_triage_rules(output)
        assert any("CONTAIN or ESCALATE_T2" in v for v in violations)

    def test_malicious_high_confidence_contain_passes(self):
        output = {
            "verdict": "MALICIOUS",
            "recommended_action": "CONTAIN",
            "priority": "HIGH",
            "confidence_score": 0.92,
        }
        violations = validate_triage_rules(output)
        assert not violations

    def test_malicious_high_confidence_escalate_passes(self):
        output = {
            "verdict": "MALICIOUS",
            "recommended_action": "ESCALATE_T2",
            "priority": "HIGH",
            "confidence_score": 0.85,
        }
        violations = validate_triage_rules(output)
        assert not violations

    def test_benign_allows_close_fp(self):
        output = {
            "verdict": "BENIGN",
            "recommended_action": "CLOSE_FP",
            "priority": "INFORMATIVE",
            "confidence_score": 0.95,
        }
        violations = validate_triage_rules(output)
        assert not violations

    def test_benign_blocks_contain(self):
        output = {
            "verdict": "BENIGN",
            "recommended_action": "CONTAIN",
            "priority": "LOW",
            "confidence_score": 0.90,
        }
        violations = validate_triage_rules(output)
        assert any("BENIGN" in v for v in violations)

    def test_benign_blocks_escalate(self):
        output = {
            "verdict": "BENIGN",
            "recommended_action": "ESCALATE_T2",
            "priority": "LOW",
            "confidence_score": 0.90,
        }
        violations = validate_triage_rules(output)
        assert any("BENIGN" in v for v in violations)

    def test_close_fp_requires_high_confidence(self):
        output = {
            "verdict": "BENIGN",
            "recommended_action": "CLOSE_FP",
            "priority": "LOW",
            "confidence_score": 0.60,
        }
        violations = validate_triage_rules(output)
        assert any("confidence_score" in v for v in violations)

    def test_inconclusive_blocks_close_fp(self):
        output = {
            "verdict": "INCONCLUSIVE",
            "recommended_action": "CLOSE_FP",
            "priority": "MEDIUM",
            "confidence_score": 0.90,
        }
        violations = validate_triage_rules(output)
        assert any("INCONCLUSIVE" in v for v in violations)

    def test_inconclusive_blocks_contain(self):
        output = {
            "verdict": "INCONCLUSIVE",
            "recommended_action": "CONTAIN",
            "priority": "MEDIUM",
            "confidence_score": 0.90,
        }
        violations = validate_triage_rules(output)
        assert any("INCONCLUSIVE" in v for v in violations)

    def test_inconclusive_allows_escalate(self):
        output = {
            "verdict": "INCONCLUSIVE",
            "recommended_action": "ESCALATE_T2",
            "priority": "MEDIUM",
            "confidence_score": 0.40,
        }
        violations = validate_triage_rules(output)
        assert not violations

    def test_low_confidence_requires_escalation(self):
        output = {
            "verdict": "SUSPICIOUS",
            "recommended_action": "MONITOR",
            "priority": "MEDIUM",
            "confidence_score": 0.35,
        }
        violations = validate_triage_rules(output)
        assert any("confidence_score < 0.5" in v for v in violations)

    def test_critical_priority_blocks_close_fp(self):
        output = {
            "verdict": "SUSPICIOUS",
            "recommended_action": "CLOSE_FP",
            "priority": "CRITICAL",
            "confidence_score": 0.90,
        }
        violations = validate_triage_rules(output)
        assert any("CRITICAL" in v for v in violations)

    def test_valid_suspicious_monitor(self):
        output = {
            "verdict": "SUSPICIOUS",
            "recommended_action": "MONITOR",
            "priority": "MEDIUM",
            "confidence_score": 0.65,
        }
        violations = validate_triage_rules(output)
        assert not violations

    def test_valid_suspicious_escalate(self):
        output = {
            "verdict": "SUSPICIOUS",
            "recommended_action": "ESCALATE_T2",
            "priority": "HIGH",
            "confidence_score": 0.72,
        }
        violations = validate_triage_rules(output)
        assert not violations


@pytest.mark.mock
class TestEnrichmentBusinessRules:

    def test_malicious_requires_blocking(self):
        output = {
            "enrichments": [
                {"gti_verdict": "MALICIOUS", "recommended_blocking": False, "ioc_value": "1.2.3.4"}
            ],
            "threat_context": {"overall_threat_level": "HIGH", "enrichment_completeness": 0.9},
        }
        violations = validate_enrichment_rules(output)
        assert any("MALICIOUS" in v for v in violations)

    def test_malicious_with_blocking_passes(self):
        output = {
            "enrichments": [
                {"gti_verdict": "MALICIOUS", "recommended_blocking": True, "ioc_value": "1.2.3.4"}
            ],
            "threat_context": {"overall_threat_level": "CRITICAL", "enrichment_completeness": 0.9},
        }
        violations = validate_enrichment_rules(output)
        assert not violations

    def test_unknown_verdict_blocks_blocking(self):
        output = {
            "enrichments": [
                {"gti_verdict": "UNKNOWN", "recommended_blocking": True, "ioc_value": "1.2.3.4"}
            ],
            "threat_context": {"overall_threat_level": "UNKNOWN", "enrichment_completeness": 0.3},
        }
        violations = validate_enrichment_rules(output)
        assert any("UNKNOWN" in v for v in violations)

    def test_undetected_verdict_blocks_blocking(self):
        output = {
            "enrichments": [
                {"gti_verdict": "UNDETECTED", "recommended_blocking": True, "ioc_value": "1.2.3.4"}
            ],
            "threat_context": {"overall_threat_level": "LOW", "enrichment_completeness": 0.8},
        }
        violations = validate_enrichment_rules(output)
        assert any("UNDETECTED" in v for v in violations)

    def test_all_unknown_constrains_threat_level(self):
        output = {
            "enrichments": [
                {"gti_verdict": "UNKNOWN", "recommended_blocking": False, "ioc_value": "1.2.3.4"},
                {"gti_verdict": "UNKNOWN", "recommended_blocking": False, "ioc_value": "evil.com"},
            ],
            "threat_context": {"overall_threat_level": "HIGH", "enrichment_completeness": 0.3},
        }
        violations = validate_enrichment_rules(output)
        assert any("overall_threat_level" in v for v in violations)

    def test_all_unknown_with_low_passes(self):
        output = {
            "enrichments": [
                {"gti_verdict": "UNKNOWN", "recommended_blocking": False, "ioc_value": "1.2.3.4"},
            ],
            "threat_context": {"overall_threat_level": "LOW", "enrichment_completeness": 0.3},
        }
        violations = validate_enrichment_rules(output)
        assert not violations

    def test_critical_requires_minimum_completeness(self):
        output = {
            "enrichments": [
                {"gti_verdict": "MALICIOUS", "recommended_blocking": True, "ioc_value": "1.2.3.4"}
            ],
            "threat_context": {"overall_threat_level": "CRITICAL", "enrichment_completeness": 0.2},
        }
        violations = validate_enrichment_rules(output)
        assert any("completeness" in v for v in violations)

    def test_suspicious_no_blocking_passes(self):
        output = {
            "enrichments": [
                {"gti_verdict": "SUSPICIOUS", "recommended_blocking": False, "ioc_value": "1.2.3.4"}
            ],
            "threat_context": {"overall_threat_level": "MEDIUM", "enrichment_completeness": 0.7},
        }
        violations = validate_enrichment_rules(output)
        assert not violations

    def test_mixed_verdicts(self):
        output = {
            "enrichments": [
                {"gti_verdict": "MALICIOUS", "recommended_blocking": True, "ioc_value": "1.2.3.4"},
                {"gti_verdict": "BENIGN", "recommended_blocking": False, "ioc_value": "cdn.example.com"},
            ],
            "threat_context": {"overall_threat_level": "HIGH", "enrichment_completeness": 0.85},
        }
        violations = validate_enrichment_rules(output)
        assert not violations


@pytest.mark.mock
class TestResponseBusinessRules:

    def test_hitl_always_required(self):
        output = {"hitl_required": False, "proposed_action": "Isolate Endpoint", "justification": "C2", "target_entities": []}
        violations = validate_response_rules(output)
        assert any("hitl_required" in v for v in violations)

    def test_hitl_present_passes(self):
        output = {"hitl_required": True, "proposed_action": "Isolate Endpoint", "justification": "C2 confirmed", "target_entities": []}
        violations = validate_response_rules(output)
        assert not violations

    def test_missing_justification(self):
        output = {"hitl_required": True, "proposed_action": "Block IP", "justification": "", "target_entities": []}
        violations = validate_response_rules(output)
        assert any("justification" in v for v in violations)

    def test_invalid_entity_structure(self):
        output = {
            "hitl_required": True,
            "proposed_action": "Block IP",
            "justification": "C2 confirmed",
            "target_entities": [{"ip": "1.2.3.4"}],
        }
        violations = validate_response_rules(output)
        assert any("identifier" in v for v in violations)

    def test_valid_entity_structure(self):
        output = {
            "hitl_required": True,
            "proposed_action": "Block IP",
            "justification": "C2 confirmed",
            "target_entities": [{"identifier": "1.2.3.4", "entity_type": "ADDRESS"}],
        }
        violations = validate_response_rules(output)
        assert not violations


@pytest.mark.mock
class TestCaseManagerBusinessRules:

    def test_cannot_close_malicious(self):
        violations = validate_case_manager_rules(
            recommended_action="CLOSE_FP",
            triage_verdict="MALICIOUS",
            triage_confidence=0.92,
            action_taken="CLOSED_FP",
        )
        assert any("MALICIOUS" in v for v in violations)

    def test_escalation_must_update_priority(self):
        violations = validate_case_manager_rules(
            recommended_action="ESCALATE_T2",
            triage_verdict="MALICIOUS",
            triage_confidence=0.88,
            action_taken="COMMENT_ONLY",
        )
        assert any("priority" in v for v in violations)

    def test_valid_close_fp_benign(self):
        violations = validate_case_manager_rules(
            recommended_action="CLOSE_FP",
            triage_verdict="BENIGN",
            triage_confidence=0.95,
            action_taken="CLOSED_FP",
        )
        assert not violations

    def test_close_fp_requires_high_confidence(self):
        violations = validate_case_manager_rules(
            recommended_action="CLOSE_FP",
            triage_verdict="BENIGN",
            triage_confidence=0.60,
            action_taken="CLOSED_FP",
        )
        assert any("confidence" in v for v in violations)

    def test_contain_blocked_in_case_manager(self):
        violations = validate_case_manager_rules(
            recommended_action="CONTAIN",
            triage_verdict="MALICIOUS",
            triage_confidence=0.90,
            action_taken="EXECUTED_ACTION",
        )
        assert any("Response Agent" in v for v in violations)

    def test_valid_escalation(self):
        violations = validate_case_manager_rules(
            recommended_action="ESCALATE_T2",
            triage_verdict="MALICIOUS",
            triage_confidence=0.88,
            action_taken="PRIORITY_UPDATED",
        )
        assert not violations

    def test_valid_monitor(self):
        violations = validate_case_manager_rules(
            recommended_action="MONITOR",
            triage_verdict="SUSPICIOUS",
            triage_confidence=0.65,
            action_taken="COMMENT_ADDED",
        )
        assert not violations
