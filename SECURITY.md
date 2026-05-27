# Security Policy

## Reporting a vulnerability

**Do not file a public issue.** Email the maintainer privately and we will respond within 72 hours.

Include:
- A description of the vulnerability
- Steps to reproduce
- The version / commit hash affected
- Your assessment of severity (low / medium / high / critical)

## Supported versions

This project is pre-1.0. Only `master` receives security fixes.

## Threat model

This project ships an opinionated security agent that:
- Holds Service Account credentials with `roles/chronicle.admin` and `roles/chronicle.soarAdmin` on client GCP projects
- Calls LLMs with attacker-controlled input (alert payloads, IoC strings, case comments)
- Can execute irreversible containment actions (isolate endpoint, block IP) when approved by a human analyst

**In scope:**
- Prompt injection that bypasses HITL guards or tool scoping
- Tenant cross-talk in the MCP Gateway (client A reading client B's data)
- Cost-burn attacks (forcing unbounded LLM loops past `_llm_call_guard`)
- Credential leakage through agent responses or stage logs
- SSRF / SQLi / auth bypass in the Workbench or MCP Gateway

**Out of scope:**
- Vulnerabilities in upstream dependencies (file with them, not us)
- LLM hallucinations that don't bypass code-enforced guards
- Issues that require physical access to a deployed instance

## Production hardening reminders

- Set `ENFORCE_CLIENT_AUTH=true` (default)
- Model Armor in fail-closed mode (default)
- 1MB request body limit on MCP Gateway (default)
- IAM Role Mapping configured in Chronicle SOAR
- Per-client SA impersonation, never shared credentials
- Firestore security rules deny direct client read (`infra/terraform/firestore.rules`)
