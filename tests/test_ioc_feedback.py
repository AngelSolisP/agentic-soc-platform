"""Tests for IoC Feedback Loop module (Phase B)."""

import json

from agents.ioc_feedback import (
    extract_confirmed_iocs,
    build_table_rows,
    format_feedback_summary,
    _extract_domain,
)


class TestExtractConfirmedIocs:
    """Tests for IoC extraction from triage output."""

    def test_extracts_malicious_iocs(self):
        triage_text = json.dumps({
            "verdict": "MALICIOUS",
            "iocs_found": [
                {"type": "IP", "value": "1.2.3.4"},
                {"type": "DOMAIN", "value": "evil.com"},
            ]
        })
        iocs = extract_confirmed_iocs(triage_text)
        assert len(iocs) == 2
        assert iocs[0]["value"] == "1.2.3.4"

    def test_skips_non_malicious_verdict(self):
        triage_text = json.dumps({
            "verdict": "BENIGN",
            "iocs_found": [
                {"type": "IP", "value": "8.8.8.8"},
            ]
        })
        iocs = extract_confirmed_iocs(triage_text)
        assert len(iocs) == 0

    def test_handles_missing_iocs(self):
        triage_text = json.dumps({"verdict": "MALICIOUS"})
        iocs = extract_confirmed_iocs(triage_text)
        assert len(iocs) == 0

    def test_filters_unknown_types(self):
        triage_text = json.dumps({
            "verdict": "MALICIOUS",
            "iocs_found": [
                {"type": "IP", "value": "1.2.3.4"},
                {"type": "CUSTOM_TYPE", "value": "something"},
            ]
        })
        iocs = extract_confirmed_iocs(triage_text)
        assert len(iocs) == 1
        assert iocs[0]["type"] == "IP"


class TestBuildTableRows:
    """Tests for Data Table row construction."""

    def test_ip_table_rows(self):
        iocs = [{"type": "IP", "value": "1.2.3.4"}]
        tables = build_table_rows(iocs, case_id="CASE-001")
        assert "agent_malicious_ips" in tables
        assert len(tables["agent_malicious_ips"]) == 1
        row = tables["agent_malicious_ips"][0]
        assert row["ip"] == "1.2.3.4"
        assert row["source_case"] == "CASE-001"

    def test_domain_table_rows(self):
        iocs = [{"type": "DOMAIN", "value": "evil.com"}]
        tables = build_table_rows(iocs, case_id="CASE-002")
        assert "agent_malicious_domains" in tables
        row = tables["agent_malicious_domains"][0]
        assert row["domain"] == "evil.com"

    def test_hash_table_rows(self):
        iocs = [{"type": "HASH", "value": "abc123def456"}]
        tables = build_table_rows(iocs, case_id="CASE-003")
        assert "agent_malicious_hashes" in tables
        row = tables["agent_malicious_hashes"][0]
        assert row["hash"] == "abc123def456"

    def test_url_extracts_domain(self):
        iocs = [{"type": "URL", "value": "https://evil.com/phish/login"}]
        tables = build_table_rows(iocs, case_id="CASE-004")
        assert "agent_malicious_domains" in tables
        row = tables["agent_malicious_domains"][0]
        assert row["domain"] == "evil.com"

    def test_mixed_iocs_multiple_tables(self):
        iocs = [
            {"type": "IP", "value": "1.2.3.4"},
            {"type": "DOMAIN", "value": "evil.com"},
            {"type": "HASH", "value": "abc123"},
        ]
        tables = build_table_rows(iocs, case_id="CASE-005")
        assert len(tables) == 3

    def test_empty_iocs(self):
        tables = build_table_rows([], case_id="CASE-006")
        assert tables == {}


class TestExtractDomain:
    """Tests for domain extraction from URLs."""

    def test_https_url(self):
        assert _extract_domain("https://evil.com/path") == "evil.com"

    def test_http_url(self):
        assert _extract_domain("http://malware.org") == "malware.org"

    def test_bare_domain(self):
        assert _extract_domain("evil.com/path") == "evil.com"

    def test_subdomain(self):
        assert _extract_domain("https://sub.evil.com") == "sub.evil.com"


class TestFormatFeedbackSummary:
    """Tests for feedback summary formatting."""

    def test_empty_tables(self):
        summary = format_feedback_summary({})
        assert "No IoCs pushed" in summary

    def test_with_entries(self):
        tables = {
            "agent_malicious_ips": [{"ip": "1.2.3.4", "source_case": "C1"}],
            "agent_malicious_domains": [{"domain": "evil.com", "source_case": "C1"}],
        }
        summary = format_feedback_summary(tables)
        assert "Data Tables Updated" in summary
        assert "agent_malicious_ips" in summary
        assert "1.2.3.4" in summary
