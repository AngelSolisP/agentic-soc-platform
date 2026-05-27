# Runbook: IoC Enrichment
**Applies to:** All alert types (used by Enrichment Agent)

---

## CONTRACT

### INPUTS
| Field | Type | Source |
|---|---|---|
| `CASE_ID` | string | Triage result |
| `CLIENT_ID` | string | Orchestrator task |
| `IOC_LIST` | list[{type, value}] | Triage result — structured array, NOT raw IDs |

IoCs are indicator VALUES (IPs, domains, hashes, users, hosts), NOT Chronicle IDs.
Each IoC has: `type` (IP, DOMAIN, URL, HASH, USER, HOST) and `value` (the actual indicator).

### PROCESS
For each IoC, route to matching type below. Max 10 IoCs, prioritize by severity.

### OUTPUTS
Produce `ENRICHMENT_RESULT` with per-IoC enrichments + `THREAT_CONTEXT`. Call `create_case_comment` before returning.

---

## IoC Type Routing

### IP Addresses
1. `get_ioc_match(startTime=, endTime=)` — Chronicle IoC match
2. `get_ip_address_report(ip_address=IP)` — GTI
3. `summarize_entity(query="principal.ip = \"IP\" OR target.ip = \"IP\"", startTime=, endTime=)`

### Domains
1. `get_ioc_match(startTime=, endTime=)`
2. `get_domain_report(domain=DOMAIN)` — GTI
3. `search_entity(indicator=DOMAIN)`

### File Hashes
1. `get_ioc_match(startTime=, endTime=)`
2. `get_file_report(file_hash=HASH)` — GTI

### Users
1. `summarize_entity(query="principal.user.userid = \"USER\"", startTime=, endTime=)`
2. `search_entity(indicator=USERNAME)`
3. `translate_udm_query` → `udm_search` (auth events, 7d)

### Hosts
1. `summarize_entity(query="principal.hostname = \"HOST\"", startTime=, endTime=)`
2. `search_entity(indicator=HOSTNAME)`

---

## Handoff
Downstream: **Case Manager Agent** reads `threat_context.overall_threat_level` and `recommended_blocking`.
