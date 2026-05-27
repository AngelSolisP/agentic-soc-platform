# Runbook: Generic Alert Triage
**Applies to:** All alert types (default)

---

## CONTRACT

### INPUTS
| Field | Type | Source |
|---|---|---|
| `CASE_ID` | string | Orchestrator task |
| `CLIENT_ID` | string | Orchestrator task |
| `ALERT_TYPE` | string | Orchestrator task |
| `SEVERITY` | LOW\|MEDIUM\|HIGH\|CRITICAL | Orchestrator task |

### PROCESS
Execute Levels 1 → 2 → 3 in order. Short-circuit to Level 3 if `QUICK_VERDICT = LIKELY_FP` after Level 1.

### OUTPUTS
Produce `TRIAGE_RESULT` including `seclm_investigation` (TIN verdict, confidence, path used), `case_alerts` array (with `caseAlertId`, `alertGroupIdentifier`, and `siemAlertId` per alert) and `iocs_found` (with `type` and `value` per IoC). Call `create_case_comment` before returning.

---

## Level 0: Gemini TIN Investigation (MANDATORY — ALWAYS FIRST)

1. `get_case(caseId=CASE_ID)` → extract SEVERITY, STATUS, ENTITIES
2. `list_case_alerts(caseId=CASE_ID)` → alert types, time range, entities
3. From each alert in the response, extract:
   - `caseAlertId` (numeric, from "caseAlertId" field or resource name `.../caseAlerts/{id}`)
   - `alertGroupIdentifier` (opaque string, from "alertGroupIdentifier" field)
   - `siemAlertId` (SIEM-side alert ID, from alert object)
   Store as `CASE_ALERTS` array for downstream agents.
4. `get_alert_latest_investigation(alertId=SIEM_ALERT_ID)` → TIN verdict, confidence, summary
5. `fetch_alert_data(siemAlertId=SIEM_ALERT_ID)` → raw SIEM event data
6. Extract IOC_LIST (IPs, domains, hashes, users, hosts) with type and value

**Decision gate:**
- TIN = FALSE_POSITIVE + HIGH confidence → **Fast-path**: Quick verification (Level 1 only), then Level 3
- TIN = TRUE_POSITIVE, or MEDIUM/LOW confidence → **Standard-path**: Full Level 1 + Level 2
- TIN unavailable → **Standard-path**: Full Level 1 + Level 2

## Level 1: Quick Assessment

1. QUICK_VERDICT = LIKELY_FP | NEEDS_INVESTIGATION | SUSPICIOUS (cross-reference with TIN verdict)
2. If fast-path: verify TIN's FP conclusion with 1-2 entity checks → skip to Level 3

## Level 2: Full Investigation (skip if fast-path)

**Logs:** `translate_udm_query` → `udm_search` (±30 min window)
**Entities:** `summarize_entity(query=..., startTime=, endTime=)` + `search_entity(indicator=VALUE)`
**IoCs:** `get_ioc_match(startTime=ISO8601, endTime=ISO8601)`

## Level 3: Decision

| MALICIOUS_CONFIDENCE | FP_LIKELIHOOD | ACTION |
|---|---|---|
| HIGH | LOW | ESCALATE_T2 or CONTAIN |
| MEDIUM | MEDIUM | MONITOR |
| LOW | HIGH | CLOSE_FP |

**Document (REQUIRED):** `create_case_comment(caseId=CASE_ID, comment=...)`

## Handoff
Downstream: **Case Manager Agent** reads `recommended_action`, `confidence_score`, and `case_alerts` (for `caseAlertId` and `alertGroupIdentifier`).
