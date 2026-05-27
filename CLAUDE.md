# Agentic SOC — MSSP Platform on Google Cloud

## Project Overview

AI-powered SOC platform for MSSPs. Replaces Tier-1 analysts with autonomous agents (Google ADK + Gemini) connected to Chronicle SecOps via MCP. Central partner platform serves N client tenants.

**Working directory:** Root of this repo contains all source code.
**Status:** All implementation phases (0-8A) and development steps (1-6) are complete.

## Architecture

```
Orchestrator Agent (Gemini 2.5 Pro)
├── Triage Agent          → Alert analysis: verdict, priority, confidence_score
├── Enrichment Agent      → GTI (conditional) + Chronicle entity enrichment
│   ├── McpToolset #1     → Gateway /mcp/{client_id} → Chronicle MCP
│   └── McpToolset #2     → Gateway /gti/{client_id} → gti-mcp server (if gti_enabled)
├── Case Manager Agent    → SOAR case lifecycle (update/close/escalate)
└── Response Agent        → Containment actions (HITL + before_tool_callback guard)
         │
         ▼
  MCP Gateway (Cloud Run FastAPI)
  ├── /mcp/{client_id}  → Chronicle Remote MCP Server (SA impersonation)
  └── /gti/{client_id}  → gti-mcp server (VT_APIKEY, per-client gti_enabled check)
```

**Multi-tenancy:** One central partner GCP project. MCP Gateway routes to N client Chronicle instances via Service Account Impersonation + `x-goog-user-project` header.

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Agent Framework | Google ADK (google-adk) |
| LLMs | Gemini 2.5 Flash (triage/volume) + Gemini 2.5 Pro (complex analysis) |
| MCP Endpoint | Remote Managed MCP Server (Chronicle) |
| MCP Proxy | Cloud Run (FastAPI) |
| Agent Runtime | Vertex AI Agent Engine |
| Client DB | Firestore |
| Secrets | Secret Manager |
| HITL UI | SOC Workbench (FastAPI + React) |
| Logging | Cloud Logging + BigQuery |
| Security | Model Armor + Cloud Armor |
| Auth | Google Sign-In (OAuth 2.0) + Service Account Impersonation |
| IaC | Terraform |

## Project Structure

```
agentic-soc/
├── agents/
│   ├── orchestrator/      # LlmAgent coordinator (Gemini 2.5 Pro)
│   ├── triage/            # Alert analysis (Gemini 2.5 Flash)
│   ├── enrichment/        # IoC enrichment via GTI + SIEM
│   ├── case_manager/      # SOAR case lifecycle
│   ├── response/          # Containment (HITL always required)
│   ├── validation.py      # Input validation: client_id regex, alert payload sanitization, safe_agent_name()
│   ├── dedup.py           # Firestore-backed alert deduplication (SHA256, TTL, fail-open)
│   ├── tool_catalog.py    # ICM: Single source of truth for MCP tool scoping per agent
│   ├── runbook_loader.py  # ICM: Loads CONTRACT sections from runbooks into task prompts
│   ├── stage_tracker.py   # ICM: Glass Box — records intermediate agent outputs to Firestore
│   ├── memory_config.py   # Memory Bank factory: VertexAiMemoryBankService (prod) / InMemory (dev)
│   ├── compat.py          # Python 3.11 anyio cancel scope workaround (Thread+Queue pattern)
│   ├── mcp_auth.py        # MCP Gateway auth: identity tokens for Cloud Run
│   └── notifications.py   # Slack, PagerDuty, email notifications
├── runbooks/
│   ├── personas/          # t1_analyst.yaml, incident_responder.yaml, threat_hunter.yaml
│   ├── tactical/          # alert_triage.md, phishing_triage.md, malware_triage.md, ioc_enrichment.md
│   └── irps/              # ransomware_irp.md, phishing_irp.md
├── a2a_gateway/           # A2A Gateway: Agent2Agent protocol (Cloud Run)
├── proxy/
│   └── mcp_gateway/       # FastAPI proxy: main.py, router.py, auth.py, model_armor.py, circuit_breaker.py
├── workbench/
│   ├── backend/           # FastAPI backend (cases, auth, admin, WebSocket, audit)
│   └── frontend/          # React + TypeScript (Vite, shadcn/ui)
├── config/clients/        # Per-client YAML configs + client_template.yaml
├── infra/terraform/       # IaC: main.tf, variables.tf, modules/
├── scripts/               # onboard_client.py, deploy_agent.py, setup_gcp.sh
├── observability/         # OpenTelemetry tracing
├── evals/                 # ADK eval: 47 scenarios across 4 agents (Tier 1 mock + Tier 2 live)
├── tests/                 # pytest suite: 407+ tests. Run: .venv/bin/python -m pytest tests/ -x -q
└── __main__.py            # CLI: process / serve commands
```

## Key Design Decisions

- **Centralized multi-tenancy** (not distributed): One partner GCP project, dynamic routing to N client tenants.
- **Service Account Impersonation**: Each client has a dedicated SA. Gateway obtains short-lived tokens per request.
- **HITL is mandatory + code-enforced** for all destructive actions. `before_tool_callback` (`_hitl_guard`) blocks `execute_manual_action` unless approval_status is APPROVED/MODIFIED.
- **Deduplication**: SHA256 hash of `client_id:alert_type:case_id`, TTL 900s, Firestore-backed, fail-open.
- **Model selection**: Flash for triage/high-volume, Pro for forensic analysis. Flash for HITL execution (cost).
- **Triage Output Schema**: `verdict` (MALICIOUS|SUSPICIOUS|BENIGN|INCONCLUSIVE), `priority` (INFORMATIVE→CRITICAL), `confidence_score` (0.0-1.0).
- **ICM (Interpretable Context Methodology)**: Tool Scoping (`tool_catalog.py`), Stage Contracts (runbook CONTRACTs), Glass Box (`stage_tracker.py` → Firestore).
- **Memory Bank**: Per-client scope (`user_id=client_id`). `PreloadMemoryTool` on orchestrator. 3 topics: alert_patterns, case_outcomes, analyst_preferences.
- **A2A Protocol**: `a2a_gateway/` exposes orchestrator via Agent2Agent. `TenantAwareA2aExecutor`. Inbound only (Phase 1).
- **HITL Two-Pass**: Response Agent submits request (pass 1) → analyst decides → callback runs pass 2. Approvals expire after `hitl_timeout_minutes` (default 30).
- **Cost Protection**: 5 guards — `_llm_call_guard` (max 25 LLM calls/pipeline), timeout 120s, no-retry prompt, IoC limit 10, Flash for HITL.
- **Notification Service**: Slack, PagerDuty, email. 4 triggers: HITL submission/timeout, case escalation, agent timeout.
- **Multi-Tenant Isolation**: Gateway force-overrides `projectId`/`customerId`/`region`/`environmentId` from ClientConfig.

## ICM Tool Scoping (per-agent MCP tools)

All definitions in `agents/tool_catalog.py`.

| Agent | Domains | Tool Count |
|---|---|---|
| Triage | SIEM_READ + SOAR read + comment + SOAR_ALERT_ENRICHMENT + INVESTIGATION_TOOLS + watchlists | 19 |
| Enrichment (Chronicle only) | SIEM_READ + SOAR read + comment + REFERENCE_LISTS + SOAR_ALERT_ENRICHMENT + GEMINI_THREAT_INTEL + CURATED_DETECTIONS_READ | 21 |
| Enrichment (with GTI) | CHRONICLE_ENRICHMENT_TOOLS + GTI_ENRICHMENT_TOOLS | 30 |
| Case Manager | SOAR_READ + SOAR_WRITE + SOAR_PLAYBOOKS (no SIEM, no GTI) | 11 |
| Response | get_case + comment + execute_manual_action + update_case + update_case_alert + SOAR_INTEGRATIONS | 7 |

## Critical SOAR API Patterns

- **get_case + list_case_alerts**: ALWAYS call both. `get_case` alone only returns high-level metadata.
- **UDM Search is two-step**: `translate_udm_query` (NL→YARA-L) then `udm_search` (execute).
- **Alert closure requires closure_details**: `{reason: "NOT_MALICIOUS|MALICIOUS|MAINTENANCE|INCONCLUSIVE|UNKNOWN", root_cause: "...", comment: "..."}`
- **execute_manual_action schema**: Requires `action_provider`, `action_name`, `target_entities`, `scope`, `alert_group_identifiers`, `is_predefined_scope`.
- **list_cases filter syntax**: PascalCase SQL-like: `"Priority='PRIORITY_CRITICAL' AND Status='OPENED'"`
- **get_case_alert**: Parameter is `caseAlertId` (numeric ID from resource name), NOT `alertId`.
- **search_entity**: Parameter is `indicator`, NOT `query` or `entity_value`.
- **get_ioc_match**: Requires `startTime` + `endTime` (ISO8601).
- **list_playbook_instances**: Requires both `caseId` AND `alertGroupIdentifier`.
- **`list_reference_lists` does NOT exist** — only `get_reference_list` and `create_reference_list`.
- **Chronicle MCP is StatelessServer**: No session tracking. `get_case` expects numeric `caseId` (e.g. "12345").
- **Chronicle MCP total**: 64 tools available. Only ~30 are scoped to agents via ICM.

## Firestore Collections

| Collection | Purpose |
|---|---|
| `hitl_approvals` | HITL approval queue (Response Agent → analyst) |
| `workflow_stages` | ICM Glass Box — intermediate agent outputs per pipeline run (TTL 30d) |
| `alert_dedup` | Deduplication cache — SHA256 doc ID, TTL via `expires_at` field |
| `analyst_assignments` | Per-client analyst authorization — `allowed_clients` list per email |
| `audit_log` | Workbench audit trail (TTL 90d) |

## IAM Requirements (Per Client GCP Project)

```
roles/mcp.toolUser
roles/chronicle.admin
roles/chronicle.soarAdmin
roles/serviceusage.serviceUsageConsumer
roles/iam.serviceAccountTokenCreator
```

## HITL Autonomous vs Supervised

**Autonomous (no approval):** Triage, enrichment, case comments, false positive closure.

**HITL required:** Isolate endpoint, block IP/domain, modify detection rules, escalate to T2, any irreversible action.

## MCP Tools Available

**SIEM:** `translate_udm_query`, `udm_search`, `summarize_entity`, `search_entity`, `get_ioc_match`, `list_rules`, `get_rule`, `create_rule`, `validate_rule`, `import_logs`

**SOAR:** `list_cases`, `get_case`, `update_case`, `update_case_alert`, `create_case_comment`, `list_case_comments`, `execute_bulk_close_case`, `list_case_alerts`, `get_case_alert`, `execute_manual_action`, `list_playbooks`, `list_playbook_instances`, `list_integrations`, `list_integration_actions`, `list_involved_entities`, `get_involved_entity`, `fetch_alert_data`, `get_alert_latest_investigation`

**SIEM Reference Lists:** `get_reference_list`, `create_reference_list`

**GTI (via gti-mcp):** get_file_report, get_ip_address_report, get_domain_report, get_url_report, get_entities_related_to_a_file, get_entities_related_to_a_domain, get_entities_related_to_an_ip_address, get_file_behavior_summary, get_collection_mitre_tree

## Development Notes

- First client = partner's NFR tenant. Validate full architecture before onboarding real clients.
- SOAR tools require client to have migrated to Chronicle REST APIs (not legacy SOAR APIs).
- Local run: MCP Gateway on port 8080, Workbench backend on 8000.
- `google.genai.types` (NOT `google.adk.types`): `Content` and `Part` live in `google.genai.types`. `google.adk.types` does not exist.
- `GOOGLE_GENAI_USE_VERTEXAI=true`: Required env var for ADK to use Vertex AI backend.
- ADK `LlmAgent` names must be Python identifiers. `safe_agent_name()` replaces hyphens with underscores.
- CI/CD: Cloud Build trigger `agentic-soc-deploy-staging` fires on push to `master`. Tests → evals → Docker → deploy.
- GTI MCP: gti-mcp server from `google/mcp-security`. Auth: `VT_APIKEY` env var. `gti_enabled` per-client in ClientConfig.
- SOAR `environmentId` injected by Gateway only when `soar_environment_id` is configured (MSSP multi-tenant isolation).
- **SOAR IAM Role Mapping**: REQUIRED for SA-based access. Configure in Chronicle SOAR Settings → Advanced → IAM Role Mapping. Without it, SA only sees "Default Environment".
- **SOAR Auth**: API Keys and Service Accounts have SEPARATE configs. Remote MCP Server uses SA auth → IAM Role Mapping is what matters (not API Keys).
- HITL Security: `decided_by` from JWT (body ignored). Firestore transactions for decisions. `ENFORCE_CLIENT_AUTH=true` by default.
- Gateway Hardening: 1MB body limit, Model Armor fail-closed by default.
- Deploy script: `scripts/deploy_agent.py` (--dry-run/--update/--rollback). Agent Engine wrapper: `agents/orchestrator/deployed_app.py`.
- Agent Engine `query()` receives keyword args (not dict): `engine.query(client_id=..., case_id=..., ...)`.
- Sensitive data (URLs, resource IDs, credentials): configure via `.env`, `.mcp.json`, and `infra/terraform/terraform.tfvars` (all gitignored). See `.env.example` and `.mcp.json.example` for templates.
