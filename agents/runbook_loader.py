"""
Runbook Loader — ICM Contract Injection

Loads the CONTRACT section from tactical runbooks and injects it into
agent task prompts. This ensures each agent receives only the context
relevant to its current stage (ICM layered context loading principle).

Contract section = everything between ## CONTRACT and ## Overview in each runbook.
"""

import os
import re
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

_RUNBOOKS_DIR = os.path.join(os.path.dirname(__file__), "..", "runbooks", "tactical")

# Maps alert type prefixes to runbook filenames
_ALERT_TYPE_MAP = {
    "PHISHING": "phishing_triage.md",
    "SPEAR_PHISHING": "phishing_triage.md",
    "EMAIL_THREAT": "phishing_triage.md",
    "MALWARE": "malware_triage.md",
    "RANSOMWARE_INDICATOR": "malware_triage.md",
    "C2_COMMUNICATION": "malware_triage.md",
    "SUSPICIOUS_PROCESS": "malware_triage.md",
}

_DEFAULT_TRIAGE_RUNBOOK = "alert_triage.md"
_ENRICHMENT_RUNBOOK = "ioc_enrichment.md"
_CASE_MANAGEMENT_RUNBOOK = "case_management.md"
_RESPONSE_RUNBOOK = "response_containment.md"


@lru_cache(maxsize=16)
def _load_runbook(filename: str) -> str:
    """Load full runbook content. Cached after first read."""
    path = os.path.normpath(os.path.join(_RUNBOOKS_DIR, filename))
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("Runbook not found: %s", path)
        return ""


def _extract_contract(runbook_content: str) -> str:
    """
    Extract the CONTRACT section from a runbook.
    Returns everything between '## CONTRACT' and the next '## ' heading.
    Falls back to full content if section not found.
    """
    match = re.search(
        r"## CONTRACT\n(.*?)(?=\n## |\Z)", runbook_content, re.DOTALL
    )
    if match:
        return match.group(1).strip()
    logger.warning("No CONTRACT section found in runbook — using full content")
    return runbook_content.strip()


def get_triage_contract(alert_type: str) -> str:
    """Return the CONTRACT section for the appropriate triage runbook."""
    filename = _ALERT_TYPE_MAP.get(alert_type.upper(), _DEFAULT_TRIAGE_RUNBOOK)
    content = _load_runbook(filename)
    contract = _extract_contract(content)
    logger.debug("Loaded triage contract from %s (%d chars)", filename, len(contract))
    return contract


def get_enrichment_contract() -> str:
    """Return the CONTRACT section for the IoC enrichment runbook."""
    content = _load_runbook(_ENRICHMENT_RUNBOOK)
    return _extract_contract(content)


def get_case_manager_contract() -> str:
    """Return the CONTRACT section for the case management runbook."""
    content = _load_runbook(_CASE_MANAGEMENT_RUNBOOK)
    return _extract_contract(content)


def get_response_contract() -> str:
    """Return the CONTRACT section for the response/containment runbook."""
    content = _load_runbook(_RESPONSE_RUNBOOK)
    return _extract_contract(content)
