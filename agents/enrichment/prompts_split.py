"""Split enrichment prompts for parallel execution (Chronicle + GTI)."""

from agents.id_glossary import CHRONICLE_ID_GLOSSARY

CHRONICLE_ENRICHMENT_PROMPT = """Enrich IoCs using Chronicle SIEM data.

""" + CHRONICLE_ID_GLOSSARY + """

## Tool Patterns (MUST follow)
- **UDM Search**: `translate_udm_query` THEN `udm_search`. Never raw text to udm_search.
- **search_entity**: Parameter is `indicator` — pass the IoC VALUE (e.g. "8.8.8.8"), NOT an ID.
- **get_ioc_match**: Requires `startTime` + `endTime` (ISO8601). Does NOT take an indicator parameter.
- **summarize_entity**: Pass UDM `query` (e.g. `"principal.ip = \\"1.2.3.4\\""`) + `startTime`/`endTime`.

## IoC Routing
| IoC Type | Chronicle Tools |
|----------|-----------------|
| IP | get_ioc_match, search_entity, summarize_entity |
| Domain | get_ioc_match, search_entity |
| Hash | get_ioc_match |
| User/Host | summarize_entity, search_entity, udm_search |

## Output
```json
{
  "chronicle_enrichments": [{"ioc_type": "", "ioc_value": "", "chronicle_match": true, "context_summary": ""}]
}
```

## Rules
- Max 10 IoCs. No data → mark UNKNOWN. NEVER retry failed tools.
"""

GTI_ENRICHMENT_PROMPT = """Enrich IoCs using Google Threat Intelligence (GTI/VirusTotal).

IMPORTANT: Pass IoC VALUES to GTI tools, NOT IDs. These are indicator values like IPs, domains, URLs, file hashes.

## IoC Routing
| IoC Type | GTI Tool |
|----------|----------|
| IP | get_ip_address_report(ip_address="1.2.3.4") |
| Domain | get_domain_report(domain="evil.com") |
| URL | get_url_report(url="https://evil.com/payload") |
| Hash | get_file_report(file_hash="abc123...") |

## Output
```json
{
  "gti_enrichments": [{"ioc_type": "", "ioc_value": "", "gti_verdict": "MALICIOUS|SUSPICIOUS|BENIGN|UNKNOWN", "gti_score": 75, "malware_families": [], "mitre_techniques": []}]
}
```

## Rules
- Max 10 IoCs. GTI no data → gti_verdict=UNKNOWN. MALICIOUS → recommended_blocking=true.
- NEVER retry a failed tool call. Mark UNKNOWN and move on.
"""

ENRICHMENT_MERGER_PROMPT = """Merge Chronicle and GTI enrichment results into a unified report.

Read `chronicle_enrichment_result` and `gti_enrichment_result` from the previous agents' outputs.
Combine per-IoC findings into the canonical output schema.

## Output
```json
{
  "enrichments": [{"ioc_type": "", "ioc_value": "", "gti_verdict": "MALICIOUS|SUSPICIOUS|BENIGN|UNKNOWN", "gti_score": 75, "chronicle_match": true, "malware_families": [], "mitre_techniques": [], "context_summary": "", "recommended_blocking": true}],
  "threat_context": {"overall_threat_level": "HIGH|MEDIUM|LOW|UNKNOWN", "malware_families": [], "mitre_techniques": [], "enrichment_completeness": 0.9}
}
```

## Rules
- If GTI says MALICIOUS, set recommended_blocking=true.
- If only Chronicle data, use chronicle_match to infer threat level.
- Always document a case comment with `create_case_comment` before returning.
"""
