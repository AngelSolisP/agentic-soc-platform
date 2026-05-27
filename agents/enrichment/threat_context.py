"""
Threat Context Enricher — Structured threat intelligence from Gemini.

Provides utility functions for parsing and structuring the output of
`get_threat_intel` calls into actionable MITRE ATT&CK mappings and
threat actor profiles.

Phase E: Gemini Threat Intelligence Enhancement.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Templates for structured get_threat_intel queries
THREAT_INTEL_QUERIES = {
    "apt_group": (
        "What is {name}? Include: attribution, targeted industries, "
        "geographic focus, known TTPs (MITRE ATT&CK techniques), "
        "and recommended detection strategies."
    ),
    "cve": (
        "Explain {name}. Include: affected software, CVSS score, "
        "exploitation status (in-the-wild, PoC available), "
        "patch availability, and detection recommendations."
    ),
    "malware_family": (
        "What is {name} malware? Include: classification (RAT, ransomware, "
        "stealer, etc.), known variants, C2 infrastructure patterns, "
        "persistence mechanisms, and IoC patterns for detection."
    ),
    "technique": (
        "Explain MITRE ATT&CK technique {name}. Include: description, "
        "common sub-techniques, detection data sources, "
        "and example YARA-L detection logic."
    ),
}


def build_threat_query(threat_name: str, threat_type: Optional[str] = None) -> str:
    """Build a structured query for get_threat_intel.

    Args:
        threat_name: Name of the threat (e.g., "APT41", "CVE-2024-23897", "Cobalt Strike").
        threat_type: Optional type hint. Auto-detected if not provided.

    Returns:
        Formatted query string for get_threat_intel.
    """
    if threat_type is None:
        threat_type = _detect_threat_type(threat_name)

    template = THREAT_INTEL_QUERIES.get(threat_type, THREAT_INTEL_QUERIES["malware_family"])
    return template.format(name=threat_name)


def _detect_threat_type(name: str) -> str:
    """Auto-detect threat type from name pattern."""
    name_upper = name.upper()

    if re.match(r"CVE-\d{4}-\d+", name_upper):
        return "cve"
    if re.match(r"APT\d+|UNC\d+|FIN\d+|TEMP\.", name_upper):
        return "apt_group"
    if re.match(r"T\d{4}(\.\d{3})?", name_upper):
        return "technique"
    return "malware_family"


def extract_mitre_techniques(text: str) -> list[str]:
    """Extract MITRE ATT&CK technique IDs from text.

    Args:
        text: Response text from get_threat_intel or any analysis text.

    Returns:
        List of technique IDs (e.g., ["T1059.001", "T1547.001"]).
    """
    pattern = r'T\d{4}(?:\.\d{3})?'
    matches = re.findall(pattern, text)
    return sorted(set(matches))


def parse_threat_intel_response(response_text: str, threat_name: str) -> dict:
    """Parse get_threat_intel response into structured output.

    Args:
        response_text: Raw response from get_threat_intel.
        threat_name: The threat that was queried.

    Returns:
        Structured threat context dict.
    """
    mitre_techniques = extract_mitre_techniques(response_text)
    threat_type = _detect_threat_type(threat_name)

    return {
        "threat_name": threat_name,
        "threat_type": threat_type,
        "mitre_techniques": mitre_techniques,
        "summary": response_text[:1000] if response_text else "No intelligence available.",
        "has_intelligence": bool(response_text and len(response_text) > 50),
    }


def get_structured_threat_context(threat_name: str, get_threat_intel_response: str) -> dict:
    """Parse a get_threat_intel response into structured MITRE ATT&CK techniques and threat profile.

    Use this tool AFTER calling get_threat_intel to structure the novel threat context.
    It extracts TTPs (T-codes) and provides a summary for enrichment reports.

    Args:
        threat_name: The name of the threat (e.g. "APT41", "Cobalt Strike").
        get_threat_intel_response: The raw text response from the get_threat_intel tool.

    Returns:
        Structured threat context dict.
    """
    return parse_threat_intel_response(get_threat_intel_response, threat_name)
