# IRP: Ransomware Incident Response Plan
**Version:** 1.0
**Persona:** incident_responder
**PICERL Model:** Preparation → Identification → Containment → Eradication → Recovery → Lessons Learned
**Severity:** CRITICAL (auto-P1)
**Last updated:** 2026-03-16

---

## ⚠️ RANSOMWARE IMMEDIATE ACTIONS

On detection of ANY ransomware indicator, execute Steps 1-3 IMMEDIATELY
before completing full investigation. Every minute counts.

---

## Phase 1: IDENTIFICATION (< 5 minutes)

### 1.1 Confirm Ransomware Indicators
```
Tool: get_case(case_id=CASE_ID)
Tool: list_case_alerts(case_id=CASE_ID)
```

Ransomware confirmation criteria (any 2 = confirmed):
- [ ] Mass file extension changes
- [ ] Shadow copy deletion commands
- [ ] Backup service termination
- [ ] Ransom note file created
- [ ] High-entropy file creation (encryption)
- [ ] Known ransomware binary hash (GTI)

### 1.2 Determine Scope — Patient Zero
```
Tool: translate_udm_query(text="Find first host with ransomware file extension changes")
Tool: udm_search(query=TRANSLATED_QUERY, time_range="last_24_hours")
```

Identify:
- `PATIENT_ZERO_HOST` — first infected host
- `INFECTION_TIMESTAMP` — when encryption started
- `RANSOMWARE_FAMILY` — which variant (via GTI file hash lookup)
- `AFFECTED_HOSTS_COUNT` — scope of spread

### 1.3 Identify Attack Vector
```
Tool: translate_udm_query(text="Show events on {PATIENT_ZERO_HOST} before infection timestamp")
Tool: udm_search(query=TRANSLATED_QUERY)
```

Determine initial access:
- Phishing email with malicious attachment?
- Exposed RDP / VPN vulnerability?
- Supply chain compromise?
- Insider threat?

---

## Phase 2: CONTAINMENT (HITL REQUIRED — < 15 minutes)

### 2.1 Immediate Isolation (HITL Required)

Submit to HITL queue for immediate approval:

**Action 1:** Isolate patient zero
```json
{
  "action": "isolate_endpoint",
  "parameters": {"hostname": "PATIENT_ZERO_HOST", "reason": "Ransomware confirmed"},
  "urgency": "IMMEDIATE",
  "hitl_required": true
}
```

**Action 2:** Isolate all confirmed affected hosts
```json
{
  "action": "isolate_endpoint",
  "parameters": {"hostname": "AFFECTED_HOST", "reason": "Ransomware lateral spread"},
  "hitl_required": true
}
```

**Action 3:** Block C2 infrastructure (if identified)
```json
{
  "action": "block_ip",
  "parameters": {"ip": "C2_IP", "direction": "both", "duration_hours": 720},
  "hitl_required": true
}
```

### 2.2 Lateral Movement Prevention

After isolation approvals:
- Identify service accounts used by ransomware
- Submit HITL for account disable/credential reset
- Block admin share access from infected hosts (if not isolated)

### 2.3 Backup Protection
- Verify backup system isolation (offline backups intact)
- Alert backup team to verify backup integrity
- Document: `LAST_CLEAN_BACKUP_DATE`

---

## Phase 3: ERADICATION

### 3.1 Malware Removal (Post-Isolation)
- Collect forensic images before wiping
- Identify all persistence mechanisms:
  - Scheduled tasks
  - Registry run keys
  - WMI subscriptions
  - Boot sector modifications
- Document IOCs for detection rule creation

### 3.2 Create Detection Rules
```
Tool: validate_rule(rule=DETECTION_RULE_YAML)
Tool: create_rule(rule=DETECTION_RULE_YAML)  # HITL required
```

Create rules for:
- Ransomware binary hash
- C2 IP/domain indicators
- Behavioral patterns (shadow deletion, mass file modification)

### 3.3 Environment Sweep
```
Tool: translate_udm_query(text="Find hosts with same ransomware IOCs in last 7 days")
Tool: udm_search(query=TRANSLATED_QUERY)
```

Verify no other infected hosts missed in initial scope.

---

## Phase 4: RECOVERY

### 4.1 Recovery Checklist
- [ ] All infected hosts isolated
- [ ] All C2 channels blocked
- [ ] Malware binaries identified and blocklisted
- [ ] Backup integrity verified
- [ ] Clean backup snapshot identified: `CLEAN_BACKUP_DATE`
- [ ] Recovery order determined (critical systems first)

### 4.2 Monitoring During Recovery
Set up enhanced monitoring:
```
Tool: create_rule(rule=POST_INCIDENT_MONITORING_RULE)  # HITL required
```

Monitor for re-infection during restore process.

---

## Phase 5: DOCUMENTATION (Required for Case Closure)

Add comprehensive incident report comment to Chronicle case:

```
[RANSOMWARE IRP - INCIDENT REPORT]
Incident ID: CASE_ID
Ransomware Family: RANSOMWARE_FAMILY
Patient Zero: PATIENT_ZERO_HOST
Infection Time: INFECTION_TIMESTAMP
Affected Hosts: AFFECTED_HOSTS_COUNT
Attack Vector: ATTACK_VECTOR

Containment Actions Taken: ACTION_LIST
Approvals Obtained: APPROVAL_LIST

IOCs:
- Hashes: HASH_LIST
- C2 IPs: C2_IP_LIST
- C2 Domains: C2_DOMAIN_LIST

Detection Rules Created: RULE_LIST
Clean Backup Date: CLEAN_BACKUP_DATE

Next Steps: RECOVERY_PLAN
Assigned To: HUMAN_INCIDENT_COMMANDER
```

---

## Output Variables
```
RANSOMWARE_IRP_RESULT = {
  PHASE_REACHED: IDENTIFICATION|CONTAINMENT|ERADICATION|RECOVERY,
  RANSOMWARE_FAMILY: string,
  PATIENT_ZERO: string,
  AFFECTED_HOSTS: list[string],
  CONTAINMENT_ACTIONS_APPROVED: list[string],
  CONTAINMENT_ACTIONS_PENDING: list[approval_id],
  C2_BLOCKED: list[string],
  RULES_CREATED: list[string],
  READY_FOR_RECOVERY: bool
}
```
