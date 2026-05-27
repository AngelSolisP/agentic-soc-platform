"""
Mock MCP tool functions for ADK evaluation agents.

These replace McpToolset connections with plain Python functions that return
realistic canned responses. ADK auto-wraps them as FunctionTools.

Tool names MUST match the real MCP tool names exactly (agents reference them
by name in system prompts and tool_catalog.py).
"""


# ---------------------------------------------------------------------------
# SIEM Tools (5) — Chronicle UDM / entity queries
# ---------------------------------------------------------------------------

def translate_udm_query(natural_language_query: str) -> dict:
    """Translate a natural language security query into a Chronicle UDM query string."""
    return {
        "udm_query": 'metadata.event_type = "NETWORK_CONNECTION" AND target.ip = "203.0.113.42"',
        "status": "success",
    }


def udm_search(query: str, start_time: str = "", end_time: str = "") -> dict:
    """Search Chronicle UDM events using a UDM query."""
    return {
        "events": [
            {
                "event_type": "NETWORK_CONNECTION",
                "timestamp": "2026-03-25T10:28:15Z",
                "principal": {"ip": "10.0.1.50", "hostname": "workstation-01", "user": "john.doe"},
                "target": {"ip": "203.0.113.42", "port": 443, "hostname": "login-secure.example.com"},
                "network": {"direction": "OUTBOUND", "bytes_sent": 1250, "bytes_received": 48200},
            },
            {
                "event_type": "DNS_QUERY",
                "timestamp": "2026-03-25T10:28:10Z",
                "principal": {"ip": "10.0.1.50", "hostname": "workstation-01"},
                "target": {"hostname": "login-secure.example.com"},
                "network": {"dns_response_code": "NOERROR"},
            },
        ],
        "total_count": 2,
    }


def summarize_entity(entity_value: str, entity_type: str = "IP") -> dict:
    """Get a summary of an entity from Chronicle, including risk score and recent activity."""
    return {
        "entity": entity_value,
        "entity_type": entity_type,
        "risk_score": 75,
        "first_seen": "2026-03-20T00:00:00Z",
        "last_seen": "2026-03-25T10:30:00Z",
        "alert_count": 3,
        "summary": f"Entity {entity_value} has been observed in 3 alerts over the past 5 days. "
        "Associated with outbound connections to known suspicious infrastructure.",
    }


def search_entity(entity_value: str, entity_type: str = "IP") -> dict:
    """Search for an entity across Chronicle data sources."""
    return {
        "entity": entity_value,
        "matches": [
            {
                "source": "UDM",
                "event_count": 15,
                "first_seen": "2026-03-20T00:00:00Z",
                "last_seen": "2026-03-25T10:30:00Z",
            },
            {
                "source": "ALERT",
                "event_count": 3,
                "alert_names": ["Phishing URL Detected", "Suspicious Outbound Connection"],
            },
        ],
    }


def get_ioc_match(value: str) -> dict:
    """Check if a value matches known Indicators of Compromise in Chronicle threat intel."""
    return {
        "ioc_value": value,
        "match_found": True,
        "source": "GTI",
        "severity": "HIGH",
        "categories": ["phishing", "credential_harvesting"],
        "confidence": 85,
        "first_seen": "2026-03-01T00:00:00Z",
        "last_seen": "2026-03-25T08:00:00Z",
    }


# ---------------------------------------------------------------------------
# GTI Tools (9) — Google Threat Intelligence
# ---------------------------------------------------------------------------

def get_file_report(hash: str) -> dict:
    """Get a VirusTotal/GTI report for a file hash (MD5, SHA1, or SHA256)."""
    return {
        "hash": hash,
        "detection_ratio": "45/72",
        "verdict": "MALICIOUS",
        "malware_families": ["Emotet", "TrickBot"],
        "file_type": "PE32 executable",
        "file_size": 245760,
        "first_submission": "2026-02-15T00:00:00Z",
        "last_analysis": "2026-03-24T12:00:00Z",
        "tags": ["trojan", "banker", "emotet"],
    }


def get_ip_address_report(ip_address: str) -> dict:
    """Get a GTI reputation report for an IP address."""
    return {
        "ip": ip_address,
        "reputation_score": -80,
        "verdict": "MALICIOUS",
        "country": "RU",
        "asn": 12345,
        "as_owner": "Suspicious Hosting LLC",
        "categories": ["command_and_control", "phishing"],
        "last_analysis_stats": {"malicious": 12, "suspicious": 3, "clean": 55},
        "whois": {"network_name": "SUSPICIOUS-NET", "registration_date": "2026-01-10"},
    }


def get_domain_report(domain: str) -> dict:
    """Get a GTI reputation report for a domain."""
    return {
        "domain": domain,
        "reputation_score": -65,
        "verdict": "MALICIOUS",
        "categories": ["phishing", "credential_harvesting"],
        "registrar": "NameCheap Inc.",
        "creation_date": "2026-03-20T00:00:00Z",
        "last_analysis_stats": {"malicious": 8, "suspicious": 5, "clean": 57},
        "dns_records": [{"type": "A", "value": "203.0.113.42"}],
    }


def get_url_report(url: str) -> dict:
    """Get a GTI analysis report for a URL."""
    return {
        "url": url,
        "verdict": "MALICIOUS",
        "categories": ["phishing"],
        "final_url": url,
        "http_response_code": 200,
        "title": "Login - Secure Portal",
        "last_analysis_stats": {"malicious": 10, "suspicious": 2, "clean": 58},
    }


def get_entities_related_to_a_file(hash: str) -> dict:
    """Get entities related to a file hash (contacted IPs, domains, dropped files)."""
    return {
        "hash": hash,
        "contacted_ips": ["203.0.113.42", "198.51.100.10"],
        "contacted_domains": ["login-secure.example.com", "c2-server.example.net"],
        "dropped_files": [{"hash": "def456...", "name": "payload.dll", "verdict": "MALICIOUS"}],
        "embedded_urls": ["https://login-secure.example.com/harvest"],
    }


def get_entities_related_to_a_domain(domain: str) -> dict:
    """Get entities related to a domain (resolved IPs, subdomains, associated files)."""
    return {
        "domain": domain,
        "resolved_ips": ["203.0.113.42"],
        "subdomains": ["api.login-secure.example.com"],
        "associated_files": [{"hash": "abc123...", "verdict": "MALICIOUS"}],
        "sibling_domains": ["login-secure2.example.com"],
    }


def get_entities_related_to_an_ip_address(ip_address: str) -> dict:
    """Get entities related to an IP address (hosted domains, downloaded files, communicating files)."""
    return {
        "ip": ip_address,
        "hosted_domains": ["login-secure.example.com"],
        "communicating_files": [{"hash": "abc123...", "verdict": "MALICIOUS", "family": "Emotet"}],
        "downloaded_files": [{"hash": "def456...", "name": "payload.dll"}],
        "referrer_files": [],
    }


def get_file_behavior_summary(hash: str) -> dict:
    """Get behavioral analysis summary for a file from GTI sandbox."""
    return {
        "hash": hash,
        "sandbox_verdicts": {"Zenbox": "MALICIOUS", "Dr.Web vxCube": "MALICIOUS"},
        "network_activity": {
            "dns_queries": ["login-secure.example.com", "c2-server.example.net"],
            "http_requests": [{"method": "POST", "url": "https://c2-server.example.net/gate.php"}],
        },
        "process_activity": {
            "created_processes": ["cmd.exe", "powershell.exe"],
            "registry_modifications": 12,
            "files_written": 5,
        },
        "mitre_techniques": ["T1059.001", "T1055", "T1071.001"],
    }


def get_collection_mitre_tree(collection_id: str) -> dict:
    """Get MITRE ATT&CK technique tree for a GTI threat collection."""
    return {
        "collection_id": collection_id,
        "techniques": [
            {"technique_id": "T1566.001", "name": "Spearphishing Attachment", "tactic": "Initial Access"},
            {"technique_id": "T1059.001", "name": "PowerShell", "tactic": "Execution"},
            {"technique_id": "T1055", "name": "Process Injection", "tactic": "Defense Evasion"},
            {"technique_id": "T1071.001", "name": "Web Protocols", "tactic": "Command and Control"},
        ],
    }


# ---------------------------------------------------------------------------
# SOAR Tools (8) — Case management (7 read/write + 1 action)
# ---------------------------------------------------------------------------

def list_cases(status: str = "OPEN", limit: int = 10) -> dict:
    """List cases from Chronicle SOAR."""
    return {
        "cases": [
            {"case_id": "CASE-EVAL-001", "display_name": "Phishing Alert", "status": "OPEN", "priority": "P2"},
            {"case_id": "CASE-EVAL-002", "display_name": "Malware Detection", "status": "OPEN", "priority": "P1"},
        ],
        "total_count": 2,
    }


def get_case(case_id: str) -> dict:
    """Retrieve detailed case information from Chronicle SOAR."""
    return {
        "case_id": case_id,
        "display_name": f"Phishing Alert - {case_id}",
        "status": "OPEN",
        "priority": "P2",
        "severity": "HIGH",
        "create_time": "2026-03-25T10:30:00Z",
        "description": "Suspicious email with link to credential harvesting page detected. "
        "User john.doe@company.com clicked the link and entered credentials.",
        "assignee": "soc-automation@partner.iam",
        "alerts_count": 2,
        "tags": ["phishing", "credential_harvesting"],
    }


def list_case_alerts(case_id: str) -> dict:
    """List all alerts associated with a Chronicle SOAR case."""
    return {
        "alerts": [
            {
                "alert_id": "ALERT-001",
                "name": "Phishing URL Detected",
                "type": "PHISHING",
                "severity": "HIGH",
                "entities": [
                    {"type": "IP", "value": "203.0.113.42"},
                    {"type": "DOMAIN", "value": "login-secure.example.com"},
                    {"type": "USER", "value": "john.doe@company.com"},
                ],
                "timestamp": "2026-03-25T10:28:00Z",
            },
            {
                "alert_id": "ALERT-002",
                "name": "Credential Submission to External Site",
                "type": "DATA_EXFILTRATION",
                "severity": "HIGH",
                "entities": [
                    {"type": "IP", "value": "203.0.113.42"},
                    {"type": "USER", "value": "john.doe@company.com"},
                ],
                "timestamp": "2026-03-25T10:29:00Z",
            },
        ],
    }


def get_case_alert(case_id: str, alert_id: str) -> dict:
    """Get detailed information about a specific alert within a case."""
    return {
        "alert_id": alert_id,
        "case_id": case_id,
        "name": "Phishing URL Detected",
        "type": "PHISHING",
        "severity": "HIGH",
        "description": "User clicked phishing link and submitted credentials to external site.",
        "entities": [
            {"type": "IP", "value": "203.0.113.42"},
            {"type": "DOMAIN", "value": "login-secure.example.com"},
            {"type": "USER", "value": "john.doe@company.com"},
            {"type": "HOST", "value": "workstation-01"},
        ],
        "raw_log_snippet": "POST /login HTTP/1.1 Host: login-secure.example.com ...",
        "timestamp": "2026-03-25T10:28:00Z",
    }


def update_case(case_id: str, priority: str = "", status: str = "", comment: str = "") -> dict:
    """Update a Chronicle SOAR case (priority, status, etc.)."""
    return {
        "case_id": case_id,
        "updated": True,
        "new_priority": priority or "P2",
        "new_status": status or "OPEN",
    }


def create_case_comment(case_id: str, comment: str) -> dict:
    """Add a comment to a Chronicle SOAR case."""
    return {
        "case_id": case_id,
        "comment_id": f"CMT-{case_id}-001",
        "status": "created",
    }


def execute_bulk_close_case(case_ids: list[str], reason: str = "False positive") -> dict:
    """Bulk close cases as false positives with documentation."""
    return {
        "closed_cases": case_ids,
        "status": "closed",
        "reason": reason,
    }


def execute_manual_action(integration: str, action_name: str, parameters: str = "{}") -> dict:
    """Execute a manual containment action via Chronicle SOAR integration (HITL-gated)."""
    return {
        "integration": integration,
        "action_name": action_name,
        "status": "executed",
        "execution_id": "EXEC-001",
        "message": f"Action {action_name} executed successfully via {integration}.",
    }


# ---------------------------------------------------------------------------
# Grouped exports — agents pick the tools they need
# ---------------------------------------------------------------------------

MOCK_SIEM_TOOLS = [translate_udm_query, udm_search, summarize_entity, search_entity, get_ioc_match]

MOCK_GTI_TOOLS = [
    get_file_report, get_ip_address_report, get_domain_report, get_url_report,
    get_entities_related_to_a_file, get_entities_related_to_a_domain,
    get_entities_related_to_an_ip_address, get_file_behavior_summary,
    get_collection_mitre_tree,
]

MOCK_SOAR_TOOLS = [
    list_cases, get_case, list_case_alerts, get_case_alert,
    update_case, create_case_comment, execute_bulk_close_case,
]

MOCK_SOAR_ACTION_TOOLS = [execute_manual_action]
