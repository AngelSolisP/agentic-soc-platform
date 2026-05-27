# IRP: Phishing Incident Response Plan
**Version:** 1.0
**Persona:** incident_responder
**PICERL Model**
**Severity:** HIGH (P2) — escalate to P1 if credentials confirmed stolen
**Last updated:** 2026-03-16

---

## Phase 1: IDENTIFICATION

### 1.1 Scope Assessment
```
Tool: get_case + list_case_alerts
Tool: udm_search  # Find all recipients of same phishing campaign
```

Determine:
- `CAMPAIGN_TYPE` — credential harvesting | malware delivery | BEC | VIP targeting
- `RECIPIENT_COUNT` — how many users received the phishing email
- `CLICKED_COUNT` — how many clicked
- `COMPROMISED_COUNT` — how many submitted credentials or executed payloads

### 1.2 Payload Analysis
- If malicious attachment → call `malware_triage` runbook
- If credential harvesting URL → enrich URL via GTI
- If BEC (Business Email Compromise) → escalate to T2 immediately

---

## Phase 2: CONTAINMENT

### 2a. Immediate Blocks (HITL Required)
- Block phishing URL/domain at proxy and email gateway
- Block sender domain in email security

### 2b. Compromised User Response (HITL Required)
For each user who submitted credentials:
```json
{"action": "revoke_sessions", "parameters": {"username": "USER"}}
{"action": "force_password_reset", "parameters": {"username": "USER"}}
```

For confirmed account takeover:
```json
{"action": "disable_user", "parameters": {"username": "USER", "reason": "Phishing compromise confirmed"}}
```

### 2c. Scope Control
- Alert all recipients via notification (outside agent scope — document for human)
- Check for OAuth consent grants by phished users
- Revoke suspicious OAuth grants (document for human admin)

---

## Phase 3: ERADICATION

- Confirm all phishing emails quarantined/deleted from mailboxes
- Verify no forwarding rules set by attacker
- Check for new accounts or admin role grants post-compromise
- Create detection rule for future phishing campaign IOCs

---

## Phase 4: RECOVERY

- Restore compromised accounts after credential reset
- Review data access during compromise window
- Brief affected users on phishing awareness

---

## Documentation Template

```
[PHISHING IRP - INCIDENT REPORT]
Campaign Type: CAMPAIGN_TYPE
Sender: SENDER_EMAIL / SENDER_DOMAIN
Phishing URLs: URL_LIST
Recipients: RECIPIENT_COUNT
Clicked: CLICKED_COUNT
Credentials Submitted: COMPROMISED_COUNT

Containment:
- URLs Blocked: URL_BLOCK_LIST
- Users Reset: USER_RESET_LIST
- Sessions Revoked: SESSION_REVOKE_LIST

Next Steps: RECOVERY_PLAN
```

---

## Output Variables
```
PHISHING_IRP_RESULT = {
  CAMPAIGN_TYPE: string,
  COMPROMISED_USERS: list[string],
  BLOCKS_SUBMITTED: list[approval_id],
  ACCOUNTS_RESET: list[string],
  RULE_CREATED: bool
}
```
