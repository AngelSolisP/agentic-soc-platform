# Agentic SOC

> A multi-agent system that replaces Tier-1 SOC analysts — built on Google ADK + Gemini, with first-class interpretability, human-in-the-loop safety, and cost guardrails.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Built with ADK](https://img.shields.io/badge/built%20with-Google%20ADK-4285F4.svg)](https://github.com/google/adk-python)

---

## Why this exists

LLM agents in security operations face a triad of hard problems:

1. **Interpretability** — Why did the agent decide this alert is benign? Black-box LLM reasoning is unacceptable when an alert is missed.
2. **Safety** — Containment actions (isolate endpoint, block IP) are irreversible. An autonomous mistake costs more than the analyst it replaces.
3. **Cost** — Naive multi-agent loops with frontier models burn $100s per alert. Production-viable agentic SOCs need hard cost guards.

This project is a working answer to all three, deployed end-to-end on Google Cloud against real Chronicle SecOps tenants.

## What it does

Replaces the **Tier-1 SOC analyst loop** — alert triage → enrichment → case management → response — with autonomous agents that:

- Read alerts from Chronicle SIEM/SOAR via Model Context Protocol (MCP)
- Enrich IoCs with Google Threat Intelligence (file/IP/domain/URL reputation, MITRE mapping)
- Make verdict decisions (`MALICIOUS | SUSPICIOUS | BENIGN | INCONCLUSIVE`) with explicit `confidence_score`
- Close false positives autonomously, escalate confirmed malicious, request human approval for irreversible actions
- Record every intermediate decision to a "Glass Box" log for post-hoc review

## Architecture

```
Orchestrator (Gemini 2.5 Pro)
├── Triage Agent          → Verdict + priority + confidence (Flash, high-volume)
├── Enrichment Agent      → GTI + Chronicle entity enrichment (parallel)
├── Case Manager Agent    → SOAR case lifecycle
└── Response Agent        → Containment actions (HITL guard — code-enforced)
         │
         ▼
  MCP Gateway (Cloud Run FastAPI)
  ├── Chronicle MCP (SIEM/SOAR — 73 tools)
  └── GTI MCP        (Threat Intel — 36 tools)
```

**Substrate:** Vertex AI Agent Engine · Cloud Run · Firestore · Secret Manager · Cloud Logging → BigQuery
**Front-end:** SOC Workbench (FastAPI + React) for HITL approval and case inspection

## What's novel here

This repo isn't just "LangChain + a SIEM." Three design choices make it interesting to AI safety / agent research:

### 1. ICM — Interpretable Context Methodology

Three-pillar discipline for keeping multi-agent reasoning legible:

- **Stage Contracts** — runbooks (markdown) declare the input/output/tools each stage may use. Loaded by `agents/runbook_loader.py` at runtime, not baked into prompts.
- **Tool Scoping** — `agents/tool_catalog.py` is the single source of truth for which MCP tools each agent can call. Triage gets 19 tools, Response gets 7. No agent has "all of Chronicle."
- **Glass Box** — `agents/stage_tracker.py` writes every intermediate agent output to Firestore (`workflow_stages` collection, TTL 30d). Every verdict has a full audit trail.

Token reduction vs naive prompt-stuffing: ~40K → 2–8K (5–20×). See `runbooks/tactical/` for live examples.

### 2. HITL as a code-enforced invariant

`before_tool_callback` (`_hitl_guard`) blocks `execute_manual_action` unless `approval_status ∈ {APPROVED, MODIFIED}`. Not a prompt instruction — a callback. Two-pass execution: agent submits request → analyst decides in Workbench → callback re-runs with decision. Approvals expire after `hitl_timeout_minutes` (default 30).

### 3. Five cost guards

1. `_llm_call_guard` — max 25 LLM calls per pipeline (kills runaway loops)
2. 120s hard timeout per agent
3. No-retry directive in prompts (prevents Gemini self-retry inflation)
4. IoC enrichment capped at 10 per alert
5. Flash (not Pro) for the HITL execution path

Result: median alert processing cost ~$0.08 vs >$1 unguarded.

## Multi-tenancy (MSSP design)

One partner GCP project serves N client Chronicle tenants. Per-request routing via Service Account Impersonation + `x-goog-user-project`. Gateway force-overrides `projectId`/`customerId`/`region`/`environmentId` from `ClientConfig` so a misbehaving agent cannot cross tenants.

## Project structure

```
agentic-soc/
├── agents/              # ADK agents + ICM machinery (tool_catalog, runbook_loader, stage_tracker)
├── runbooks/            # Stage Contracts (markdown) + personas + IRPs
├── proxy/mcp_gateway/   # Multi-tenant MCP proxy (FastAPI, Cloud Run)
├── a2a_gateway/         # Agent2Agent protocol surface
├── workbench/           # HITL UI (FastAPI + React/Vite/shadcn)
├── infra/terraform/     # IaC: project, IAM, Cloud Run, Firestore, budgets
├── evals/               # 47 ADK eval scenarios across 4 agents
├── tests/               # 407+ pytest cases
└── observability/       # OpenTelemetry tracing
```

## Quickstart (local)

```bash
# 1. Install
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env                  # fill in PARTNER_PROJECT_ID, etc.
cp .mcp.json.example .mcp.json        # fill in CHRONICLE_CUSTOMER_ID, VT_APIKEY

# 3. Run an alert through the pipeline (local agents, cloud MCP Gateway)
export GOOGLE_CLOUD_PROJECT=your-partner-gcp-project
export GOOGLE_GENAI_USE_VERTEXAI=true
.venv/bin/python scripts/test_e2e_local.py

# 4. Run tests
.venv/bin/python -m pytest tests/ -x -q
```

You'll need: a Chronicle SecOps tenant, a GCP project with Vertex AI enabled, and the [`mcp-security`](https://github.com/google/mcp-security) MCP servers cloned alongside this repo.

## Deploy

See `cloudbuild.yaml` for the staging deploy pipeline (tests → evals → Docker → Cloud Run). Terraform in `infra/terraform/` provisions: APIs, service accounts, IAM bindings, Cloud Run services, Firestore database, budget alerts.

## Status

Implementation phases 0–8 complete:
- ✅ Multi-tenant MCP Gateway (Cloud Run)
- ✅ Four agents (Triage, Enrichment, Case Manager, Response) with ICM
- ✅ HITL with code-enforced approval guard
- ✅ A2A protocol surface
- ✅ Memory Bank (per-client scope, 3 topics)
- ✅ Cost protection (5 guards)
- ✅ SOC Workbench (Google Sign-In, analyst assignment, audit log)
- ✅ 407+ tests, 47 evals

## License

[Apache License 2.0](LICENSE). See [NOTICE](NOTICE) for attribution.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome.

## Acknowledgments

Built on [Google Agent Development Kit (ADK)](https://github.com/google/adk-python), [Chronicle MCP Server](https://github.com/google/mcp-security), and the Model Context Protocol specification. ICM methodology adapted for production SOC workloads.

---

*This is an open implementation of patterns from a working MSSP deployment. The MCP servers and ICM design choices are reusable independent of the SOC domain.*
