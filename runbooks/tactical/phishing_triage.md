# Runbook: Phishing Alert Triage
**Applies to:** PHISHING, SPEAR_PHISHING, EMAIL_THREAT

---

## CONTRACT

### INPUTS
| Field | Type | Source |
|---|---|---|
| `CASE_ID` | string | Orchestrator task |
| `CLIENT_ID` | string | Orchestrator task |
| `ALERT_TYPE` | PHISHING\|SPEAR_PHISHING\|EMAIL_THREAT | Orchestrator task |
| `SEVERITY` | LOW\|MEDIUM\|HIGH\|CRITICAL | Orchestrator task |

### PROCESS
Steps 1 → 2 → 3 → 4. If CREDENTIALS_ENTERED=true or RANSOMWARE detected, escalate immediately.

### OUTPUTS
Produce `PHISHING_TRIAGE_RESULT` including `seclm_investigation` (TIN verdict, confidence, path used), `case_alerts` (with `caseAlertId`, `alertGroupIdentifier`, `siemAlertId`), and `iocs_found`. Call `create_case_comment` before returning.

---

## Step 1: Alert Context + Gemini TIN (MANDATORY)

`get_case(caseId=CASE_ID)` + `list_case_alerts(caseId=CASE_ID)`

From each alert, extract `caseAlertId`, `alertGroupIdentifier`, and `siemAlertId` → store as `CASE_ALERTS`.

**TIN Investigation (always call):**
- `get_alert_latest_investigation(alertId=SIEM_ALERT_ID)` → TIN verdict (TRUE_POSITIVE/FALSE_POSITIVE), confidence, summary
- `fetch_alert_data(siemAlertId=SIEM_ALERT_ID)` → raw SIEM event data
- If TIN = FALSE_POSITIVE + HIGH confidence → Fast-path: verify with 1-2 IoC checks, skip Step 2-3

Extract: SENDER_EMAIL, SENDER_DOMAIN, RECIPIENT_EMAIL, URLS_IN_EMAIL, ATTACHMENT_HASHES, CLICKED_LINK (bool), CREDENTIALS_ENTERED (bool).

## Step 2: IoC Enrichment

**URLs/Domains:** `get_domain_report(domain=)`, `get_url_report(url=)`, `get_ioc_match(startTime=, endTime=)`
**Attachments:** `get_file_report(file_hash=HASH)`, `get_ioc_match(...)`
**Sender:** `search_entity(indicator=SENDER_DOMAIN)` — check spoofing, SPF/DKIM failures

## Step 3: User Impact

`translate_udm_query` → `udm_search` for RECIPIENT auth events (±2h).
Check: new login locations, OAuth grants, data access post-click.

## Step 4: Decision

| Scenario | Confidence | Action |
|---|---|---|
| Known phishing + clicked + new login | HIGH | CONTAIN (disable user) |
| Known phishing, not clicked | HIGH | CLOSE + block recommendation |
| Suspicious domain, not clicked | MEDIUM | MONITOR |
| All IoCs benign | LOW | CLOSE_FP |
| Credential harvesting confirmed | CRITICAL | ESCALATE_T2 + disable user (HITL) |

**Document (REQUIRED):** `create_case_comment(caseId=CASE_ID, comment=...)`

## Handoff
Downstream: **Case Manager Agent** (always) + **Response Agent** if USER_COMPROMISED=true.
