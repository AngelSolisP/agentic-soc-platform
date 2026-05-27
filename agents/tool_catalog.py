"""
MCP Tool Catalog — ICM Scoping (Interpretable Context Methodology)

Single source of truth for MCP tool scoping across all agents.
Each agent receives ONLY the tools strictly necessary for its stage.

Principle: prevent "Lost in the Middle" degradation by keeping per-agent
context between 2K–8K tokens instead of loading all tools monolithically.

Domain groups map to Chronicle SecOps capability areas:
  SIEM_READ      → UDM queries, entity lookup (Chronicle SIEM)
  SIEM_RULES     → Detection rule management (read-only; write is not autonomous)
  GTI_TOOLS_CORE → Core IoC reports (gti-mcp server)
  GTI_TOOLS_DEEP → Deep investigation relationships (gti-mcp server)
  SOAR_READ      → Case/alert data retrieval (Chronicle SOAR)
  SOAR_WRITE     → Case state mutations (comments, updates, bulk close)
  SOAR_ACTIONS   → Containment actions — ALWAYS requires HITL approval
"""

# ---------------------------------------------------------------------------
# Domain groups
# ---------------------------------------------------------------------------

SIEM_READ = [
    "translate_udm_query",       # params: query (natural language)
    "udm_search",                # params: query (YARA-L from translate_udm_query)
    "summarize_entity",          # params: query (UDM expression) + startTime + endTime
    "search_entity",             # params: indicator (IoC VALUE, NOT an ID or "query")
    "get_ioc_match",             # params: startTime + endTime (ISO8601)
]

SIEM_RULES_READ = [
    "list_rules",
    "get_rule",
]

# --- GTI Tools (from google/mcp-security gti-mcp server) ---

# Core IoC enrichment (4 tools)
GTI_TOOLS_CORE = [
    "get_file_report",
    "get_ip_address_report",
    "get_domain_report",
    "get_url_report",
]

# Deep investigation (5 tools)
GTI_TOOLS_DEEP = [
    "get_entities_related_to_a_file",
    "get_entities_related_to_a_domain",
    "get_entities_related_to_an_ip_address",
    "get_file_behavior_summary",
    "get_collection_mitre_tree",
]

# All GTI tools for Enrichment Agent (core + deep = 9)
GTI_ENRICHMENT_TOOLS = GTI_TOOLS_CORE + GTI_TOOLS_DEEP

SOAR_READ = [
    "list_cases",               # params: filter (PascalCase SQL)
    "get_case",                 # params: caseId (numeric string)
    "list_case_alerts",         # params: caseId → returns caseAlertId + alertGroupIdentifier per alert
    "get_case_alert",           # params: caseId + caseAlertId (NOT alertId)
    "list_case_comments",       # params: caseId
]

SOAR_WRITE = [
    "update_case",              # params: caseId + fields to update. CANNOT set status=CLOSED
    "update_case_alert",        # params: caseId + caseAlertId + closureDetails (for closing)
    "create_case_comment",      # params: caseId + comment
    "execute_bulk_close_case",  # the ONLY way to close a case
]

# Containment actions: execute_manual_action fires real containment.
# Always gated by HITL — never called autonomously.
# params: caseId + actionProvider + actionName + targetEntities + alertGroupIdentifiers + isPredefinedScope
SOAR_ACTIONS = [
    "execute_manual_action",
]

# --- Alert-level enrichment (Chronicle SOAR) ---
# Tools for drilling into alert details, entities, and investigations.
SOAR_ALERT_ENRICHMENT = [
    "list_involved_entities",   # params: caseId + caseAlertId (NOT alertGroupIdentifier)
    "get_involved_entity",      # params: caseId + caseAlertId + involvedEntityId
    "fetch_alert_data",         # params: siemAlertId (NOT caseAlertId)
    "get_alert_latest_investigation",  # params: alertId (SIEM-side, NOT caseAlertId)
]

# --- Gemini Threat Intelligence (Chronicle SIEM) ---
# Direct Gemini Q&A for threat context — "What is APT41?", "Explain CVE-2024-xxxx"
GEMINI_THREAT_INTEL = [
    "get_threat_intel",             # params: query (natural language question about threats)
]

# --- Investigation Management (Chronicle SIEM) ---
# TIN investigation results and management.
INVESTIGATION_TOOLS = [
    "list_investigations",              # params: page_size, page_token
    "get_investigation",                # params: investigation_id
    "trigger_investigation",            # params: alert_id → triggers new TIN investigation
    "fetch_associated_investigations",  # params: detection_type (ALERT|CASE), alert_ids or case_ids
]

# --- Watchlists (Chronicle SIEM) ---
# Entity risk management — watchlists apply risk multipliers to entity groups.
WATCHLIST_TOOLS = [
    "list_watchlists",
    "get_watchlist",
    "create_watchlist",
    "update_watchlist",
]

# --- Curated Detections (Chronicle SIEM) ---
# Google/Mandiant-maintained detection rules. Read-only for agents.
CURATED_DETECTIONS = [
    "list_curated_rules",
    "get_curated_rule",
    "get_curated_rule_by_name",
    "search_curated_detections",
    "list_curated_rule_sets",
    "get_curated_rule_set",
    "list_curated_rule_set_deployments",
    "update_curated_rule_set_deployment",  # HITL required — enables/disables rule sets
]

# Read-only subset of curated detections (safe for autonomous use)
CURATED_DETECTIONS_READ = [
    "list_curated_rules",
    "get_curated_rule",
    "search_curated_detections",
    "list_curated_rule_sets",
    "list_curated_rule_set_deployments",
]

# --- Data Tables (Chronicle SIEM) ---
# Multi-column lookup tables for enriching detection rules at evaluation time.
DATA_TABLE_TOOLS = [
    "create_data_table",
    "add_rows_to_data_table",
    "list_data_table_rows",
    "delete_data_table_rows",
]

# --- Reference Lists (Chronicle SIEM) ---
# IoC allowlists, blocklists, and custom reference data used for enrichment.
# Note: "list_reference_lists" does NOT exist on the Chronicle MCP server.
# Only get (by name) and create are available.
REFERENCE_LISTS = [
    "get_reference_list",
    "create_reference_list",
]

# --- Playbook visibility (Chronicle SOAR) ---
# Read-only access to playbook catalog and execution status.
SOAR_PLAYBOOKS = [
    "list_playbooks",             # params: (none required beyond common)
    "list_playbook_instances",    # params: caseId + alertGroupIdentifier (BOTH required)
]

# --- Integration discovery (Chronicle SOAR) ---
# Discover which integrations and actions are available per client.
SOAR_INTEGRATIONS = [
    "list_integrations",
    "list_integration_actions",
]

# ---------------------------------------------------------------------------
# Per-agent tool contracts (ICM Stage Contracts)
#
# Triage     → read a specific case from SIEM + SOAR, document assessment
# Enrichment → enrich IoCs via GTI + SIEM, document enrichment findings
# CaseMgr    → manage SOAR case lifecycle only (no SIEM, no GTI)
# Response   → execute approved HITL containment, update case record
# ---------------------------------------------------------------------------

# Triage: SIEM read + targeted SOAR read (single case) + comment only.
# Does NOT get list_cases (receives case_id directly) or update_case
# (state mutations belong to Case Manager).
# Includes alert enrichment tools for deeper entity analysis.
# Includes investigation tools to retrieve Gemini TIN results (mandatory).
# Includes watchlist tools to check entity risk context.
TRIAGE_TOOLS = SIEM_READ + [
    "get_case",
    "list_case_alerts",
    "get_case_alert",       # param: caseAlertId (NOT alertId)
    "create_case_comment",
] + SOAR_ALERT_ENRICHMENT + INVESTIGATION_TOOLS + [
    "list_watchlists",      # read-only: check if entity is on a watchlist
    "get_watchlist",
]

# Chronicle-only tools for Enrichment Agent (SIEM + SOAR + reference lists + alert enrichment)
# Includes Gemini threat intel Q&A and curated detection visibility.
CHRONICLE_ENRICHMENT_TOOLS = SIEM_READ + [
    "get_case",
    "list_case_alerts",
    "get_case_alert",       # param: caseAlertId (NOT alertId)
    "create_case_comment",
] + REFERENCE_LISTS + SOAR_ALERT_ENRICHMENT + GEMINI_THREAT_INTEL + CURATED_DETECTIONS_READ

# Combined enrichment tools (backward compat for tests)
ENRICHMENT_TOOLS = CHRONICLE_ENRICHMENT_TOOLS + GTI_ENRICHMENT_TOOLS

# Case Manager: SOAR only. No SIEM queries, no GTI.
# Receives pre-analyzed results from Triage/Enrichment via task context.
# Includes playbook visibility for reporting available automations.
# Includes data table write for IoC feedback loop.
CASE_MANAGER_TOOLS = SOAR_READ + SOAR_WRITE + SOAR_PLAYBOOKS + [
    "add_rows_to_data_table",
]

# Response: Read case for context, comment for audit trail, execute approved
# action, update case status. Includes integration discovery to verify
# which actions and providers are actually available before execution.
RESPONSE_TOOLS = [
    "get_case",
    "create_case_comment",
    "execute_manual_action",
    "update_case",
    "update_case_alert",    # alert-level closure with closure_details
] + SOAR_INTEGRATIONS
