"""
Chronicle SOAR ID Glossary — Shared prompt block for all agents.

Prevents ID confusion between caseId, caseAlertId, alertGroupIdentifier,
siemAlertId, and IoC values across the multi-agent pipeline.
"""

CHRONICLE_ID_GLOSSARY = """
## Chronicle SOAR ID Hierarchy (MUST follow)

There are 5 different ID types in Chronicle SOAR. NEVER confuse them:

```
Case (caseId: "12345")
  └── CaseAlert (caseAlertId: "751")
       ├── alertGroupIdentifier: "rule_abc_123"
       ├── siemAlertId: "uuid-xxx"
       └── InvolvedEntity (involvedEntityId: "xyz")
```

1. **caseId** — Numeric string (e.g. "12345"). Identifies a SOAR case.
   - Obtained from: list_cases response, or the orchestrator task.
   - Used by: get_case, list_case_alerts, create_case_comment, update_case, list_case_comments, execute_bulk_close_case.

2. **caseAlertId** — Numeric string (e.g. "751"). Identifies an alert WITHIN a case.
   - Obtained from: list_case_alerts response → "caseAlertId" field, or resource name `.../caseAlerts/<id>`.
   - Used by: get_case_alert(caseId, caseAlertId), update_case_alert(caseId, caseAlertId), list_involved_entities(caseId, caseAlertId), get_involved_entity(caseId, caseAlertId, involvedEntityId).
   - NEVER pass caseId where caseAlertId is expected. NEVER pass alertId here.

3. **alertGroupIdentifier** — Opaque string. Groups related alerts within a case.
   - Obtained from: list_case_alerts response → "alertGroupIdentifier" field on each alert object.
   - Used by: list_playbook_instances(caseId, alertGroupIdentifier), execute_manual_action(alertGroupIdentifiers=[...]).
   - NEVER pass caseAlertId where alertGroupIdentifier is expected.

4. **siemAlertId** — SIEM-side alert identifier (may be UUID or alphanumeric).
   - Obtained from: list_case_alerts response → alert object fields.
   - Used by: fetch_alert_data(siemAlertId), get_alert_latest_investigation(alertId).
   - This is different from caseAlertId.

5. **IoC values** — Actual indicator values (IPs, domains, hashes, users, hosts). These are NOT IDs.
   - Used by: search_entity(indicator=VALUE), summarize_entity(query=UDM_EXPRESSION), and GTI tools (when available).
   - NEVER pass a caseId, caseAlertId, or any other ID as an indicator value.

### Critical Parameter Names (camelCase for Remote MCP)
- get_case: `caseId` (NOT case_id)
- get_case_alert: `caseId` + `caseAlertId` (NOT alertId)
- update_case_alert: `caseId` + `caseAlertId`
- list_involved_entities: `caseId` + `caseAlertId`
- list_playbook_instances: `caseId` + `alertGroupIdentifier`
- execute_manual_action: `caseId` + `alertGroupIdentifiers` + `actionProvider` + `actionName` + `targetEntities` + `isPredefinedScope`
- search_entity: `indicator` (NOT query, NOT entity_value)
- summarize_entity: `query` + `startTime` + `endTime`
- get_ioc_match: `startTime` + `endTime` (ISO 8601)
"""
