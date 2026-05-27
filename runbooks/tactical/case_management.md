# Runbook: Case Management
**Applies to:** All case lifecycle actions (used by Case Manager Agent)

---

## CONTRACT

### INPUTS
| Field | Type | Source |
|---|---|---|
| `CASE_ID` | string | Orchestrator task (this is the `caseId`) |
| `CLIENT_ID` | string | Orchestrator task |
| `CASE_ALERTS` | list[{caseAlertId, alertGroupIdentifier}] | Triage result |
| `RECOMMENDED_ACTION` | CLOSE_FP\|ESCALATE_T2\|MONITOR\|CONTAIN | Triage result |
| `TRIAGE_RESULTS` | JSON | Triage Agent output |
| `ENRICHMENT_RESULTS` | JSON | Enrichment Agent output (optional) |

### PROCESS
1. `get_case(caseId=CASE_ID)` + `list_case_alerts(caseId=CASE_ID)` (always both)
2. Execute RECOMMENDED_ACTION per routing below — use `caseAlertId` from CASE_ALERTS for alert-level operations
3. `create_case_comment(caseId=CASE_ID, comment=...)` documenting action
4. Verify with `get_case(caseId=CASE_ID)` after changes

### OUTPUTS
Produce `CASE_MANAGEMENT_RESULT`. Downstream: Response Agent (only if CONTAIN).

---

## Action Routing

### CLOSE_FP
Requires ALL: verdict=BENIGN, confidence>0.85, no MALICIOUS IoCs, no anomalies.
```
1. get_case(caseId=CASE_ID) + list_case_alerts(caseId=CASE_ID)
2. create_case_comment(caseId=CASE_ID, comment=FP documentation)
3. For each alert: update_case_alert(caseId=CASE_ID, caseAlertId=CASE_ALERT_ID, closureDetails={"reason": "NOT_MALICIOUS", "root_cause": "...", "comment": "..."})
4. execute_bulk_close_case to close the case (NOT update_case with status=CLOSED)
```

### ESCALATE_T2
```
1. get_case(caseId=CASE_ID) + list_case_alerts(caseId=CASE_ID)
2. update_case(caseId=CASE_ID, priority=HIGH|CRITICAL)
3. create_case_comment(caseId=CASE_ID, comment=escalation template with reason, IoCs, next steps)
```

### MONITOR
```
1. get_case(caseId=CASE_ID) + list_case_alerts(caseId=CASE_ID)
2. create_case_comment(caseId=CASE_ID, comment=findings summary)
```

### CONTAIN
```
1. get_case(caseId=CASE_ID) + list_case_alerts(caseId=CASE_ID)
2. update_case(caseId=CASE_ID, priority=HIGH|CRITICAL)
3. create_case_comment(caseId=CASE_ID, comment=containment context)
```

## Handoff
Downstream: **Response Agent** (only if ACTION_TAKEN=CONTAIN).
