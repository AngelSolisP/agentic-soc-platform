"""Tests for Threat Context Enricher module (Phase E)."""

from agents.enrichment.threat_context import (
    build_threat_query,
    _detect_threat_type,
    extract_mitre_techniques,
    parse_threat_intel_response,
)


class TestDetectThreatType:
    """Tests for automatic threat type detection."""

    def test_cve_pattern(self):
        assert _detect_threat_type("CVE-2024-23897") == "cve"

    def test_apt_pattern(self):
        assert _detect_threat_type("APT41") == "apt_group"

    def test_unc_pattern(self):
        assert _detect_threat_type("UNC3886") == "apt_group"

    def test_fin_pattern(self):
        assert _detect_threat_type("FIN7") == "apt_group"

    def test_mitre_technique(self):
        assert _detect_threat_type("T1059.001") == "technique"

    def test_mitre_technique_no_sub(self):
        assert _detect_threat_type("T1059") == "technique"

    def test_malware_default(self):
        assert _detect_threat_type("Cobalt Strike") == "malware_family"

    def test_unknown_defaults_to_malware(self):
        assert _detect_threat_type("SomeNewThreat") == "malware_family"


class TestBuildThreatQuery:
    """Tests for structured threat intel query building."""

    def test_apt_query(self):
        query = build_threat_query("APT41")
        assert "APT41" in query
        assert "attribution" in query
        assert "MITRE ATT&CK" in query

    def test_cve_query(self):
        query = build_threat_query("CVE-2024-23897")
        assert "CVE-2024-23897" in query
        assert "CVSS" in query
        assert "exploitation" in query

    def test_malware_query(self):
        query = build_threat_query("Cobalt Strike")
        assert "Cobalt Strike" in query
        assert "C2" in query
        assert "persistence" in query

    def test_explicit_type_override(self):
        query = build_threat_query("CustomThreat", threat_type="apt_group")
        assert "attribution" in query


class TestExtractMitreTechniques:
    """Tests for MITRE technique ID extraction."""

    def test_extracts_techniques(self):
        text = "Uses T1059.001 (PowerShell) and T1547.001 for persistence."
        techniques = extract_mitre_techniques(text)
        assert "T1059.001" in techniques
        assert "T1547.001" in techniques

    def test_extracts_parent_technique(self):
        text = "Employs T1059 command execution."
        techniques = extract_mitre_techniques(text)
        assert "T1059" in techniques

    def test_deduplicates(self):
        text = "T1059.001 is used. Also T1059.001 appears again."
        techniques = extract_mitre_techniques(text)
        assert len(techniques) == 1

    def test_empty_text(self):
        assert extract_mitre_techniques("") == []

    def test_no_techniques(self):
        assert extract_mitre_techniques("No MITRE data here.") == []


class TestParseThreatIntelResponse:
    """Tests for structured response parsing."""

    def test_parses_response_with_techniques(self):
        response = "APT41 uses T1059.001 (PowerShell) and T1547.001 for persistence."
        result = parse_threat_intel_response(response, "APT41")
        assert result["threat_name"] == "APT41"
        assert result["threat_type"] == "apt_group"
        assert "T1059.001" in result["mitre_techniques"]
        assert result["has_intelligence"] is True

    def test_handles_empty_response(self):
        result = parse_threat_intel_response("", "UnknownThreat")
        assert result["has_intelligence"] is False
        assert result["summary"] == "No intelligence available."

    def test_truncates_long_summary(self):
        long_response = "x" * 2000
        result = parse_threat_intel_response(long_response, "APT41")
        assert len(result["summary"]) == 1000
