# Runbook: Response & Containment
**Applies to:** All containment actions (used by Response Agent)

---

## CONTRACT

### INPUTS
| Field | Type | Source |
|---|---|---|
| `CASE_ID` | string | Orchestrator task (this is the `caseId`) |
| `CLIENT_ID` | string | Orchestrator task |
| `CASE_ALERTS` | list[{caseAlertId, alertGroupIdentifier}] | Triage result |
| `APPROVAL_STATUS` | PENDING\|APPROVED\|REJECTED\|MODIFIED\|EXPIRED | HITL queue |
| `TRIAGE_RESULTS` | JSON | Triage Agent output |
| `PROPOSED_ACTIONS` | JSON | Pass 1 output |

### PROCESS
**Pass 1 (PENDING):** Propose actions, return PENDING_APPROVAL. Do NOT call execute_manual_action.
**Pass 2 (APPROVED/MODIFIED):** Execute via execute_manual_action. Document via create_case_comment.

### OUTPUTS
Pass 1: `RESPONSE_PROPOSAL`. Pass 2: `RESPONSE_RESULT`.

---

## Pass 1: Action Proposal

| Threat | Actions |
|---|---|
| Ransomware on host | Isolate Endpoint + Collect Forensics |
| Active C2 | Block IP + Block Domain |
| Credential compromise | Disable User + Revoke Sessions |
| Phishing + click | Block URL + Force Password Reset |
| Lateral movement | Isolate Endpoint + Block IP |

Proportionality: match scope to confirmed threat. Temporary for SUSPICIOUS, permanent for MALICIOUS.

## Pass 2: Execution

```
1. get_case(caseId=CASE_ID) + list_case_alerts(caseId=CASE_ID) (get alertGroupIdentifiers from CASE_ALERTS input)
2. execute_manual_action(caseId=CASE_ID, actionProvider=..., actionName=..., targetEntities=[{"Identifier": "value", "EntityType": "ADDRESS|HOSTNAME|USER"}], scope=..., alertGroupIdentifiers=[from CASE_ALERTS], isPredefinedScope=false)
3. create_case_comment(caseId=CASE_ID, comment=execution result)
```

Note: All parameters use camelCase. targetEntities inner keys use PascalCase (Identifier, EntityType).

## Handoff
Terminal agent — no downstream. Results written to case comment and HITL queue.
