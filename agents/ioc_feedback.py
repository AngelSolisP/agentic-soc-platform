"""
IoC Feedback Loop — Pushes confirmed malicious IoCs to Chronicle Data Tables.

When the pipeline confirms an IoC as MALICIOUS, this module writes it to
per-client Chronicle Data Tables. YARA-L detection rules can reference
these tables for enhanced detection coverage.

Phase B: Data Tables Feedback Loop.

Data Table schema:
  agent_malicious_ips:     ip (STRING), first_seen (STRING), source_case (STRING), confidence (STRING)
  agent_malicious_domains: domain (STRING), first_seen (STRING), source_case (STRING), confidence (STRING)
  agent_malicious_hashes:  hash (STRING), malware_family (STRING), source_case (STRING), confidence (STRING)
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import httpx
from agents.mcp_auth import get_id_token

logger = logging.getLogger(__name__)

# Map IoC types to Data Table names
IOC_TABLE_MAP = {
    "IP": "agent_malicious_ips",
    "DOMAIN": "agent_malicious_domains",
    "URL": "agent_malicious_domains",  # Extract domain from URL
    "HASH": "agent_malicious_hashes",
}


def extract_confirmed_iocs(triage_text: str) -> list[dict]:
    """Extract IoCs from triage output that were confirmed malicious.

    Args:
        triage_text: Raw triage agent output text.

    Returns:
        List of {"type": str, "value": str} for MALICIOUS-confirmed IoCs.
    """
    iocs = []
    try:
        # Find iocs_found array in JSON output
        match = re.search(r'"iocs_found"\s*:\s*\[(.*?)\]', triage_text, re.DOTALL)
        if match:
            iocs_json = "[" + match.group(1) + "]"
            iocs = json.loads(iocs_json)
    except (json.JSONDecodeError, AttributeError):
        pass

    # Only return IoCs if the verdict is MALICIOUS
    if '"verdict"' in triage_text:
        verdict_match = re.search(r'"verdict"\s*:\s*"(\w+)"', triage_text)
        if verdict_match and verdict_match.group(1) != "MALICIOUS":
            return []  # Not malicious — don't push to feedback tables

    return [ioc for ioc in iocs if ioc.get("type") in IOC_TABLE_MAP]


def build_table_rows(iocs: list[dict], case_id: str, confidence: str = "HIGH") -> dict[str, list[dict]]:
    """Build Data Table rows grouped by table name.

    Args:
        iocs: List of {"type": str, "value": str} IoCs.
        case_id: Source case ID for provenance.
        confidence: Confidence level of the malicious determination.

    Returns:
        Dict of {table_name: [row_dicts]} ready for add_rows_to_data_table.
    """
    now = datetime.now(timezone.utc).isoformat()
    tables: dict[str, list[dict]] = {}

    for ioc in iocs:
        ioc_type = ioc.get("type", "").upper()
        ioc_value = ioc.get("value", "")
        if not ioc_value or ioc_type not in IOC_TABLE_MAP:
            continue

        table_name = IOC_TABLE_MAP[ioc_type]

        if table_name not in tables:
            tables[table_name] = []

        if ioc_type == "HASH":
            row = {
                "hash": ioc_value,
                "malware_family": ioc.get("malware_family", "unknown"),
                "source_case": case_id,
            }
        elif ioc_type == "URL":
            # Extract domain from URL for the domain table
            domain = _extract_domain(ioc_value)
            if not domain:
                continue
            row = {
                "domain": domain,
                "first_seen": now,
                "source_case": case_id,
                "confidence": confidence,
            }
        else:
            column_name = "ip" if ioc_type == "IP" else "domain"
            row = {
                column_name: ioc_value,
                "first_seen": now,
                "source_case": case_id,
                "confidence": confidence,
            }

        tables[table_name].append(row)

    return tables


def _extract_domain(url: str) -> Optional[str]:
    """Extract domain from a URL string."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url if "://" in url else f"https://{url}")
        return parsed.hostname
    except Exception:
        return None


def format_feedback_summary(tables: dict[str, list[dict]]) -> str:
    """Format feedback loop results for logging/comments.

    Args:
        tables: Output from build_table_rows().

    Returns:
        Human-readable summary of what was pushed.
    """
    if not tables:
        return "No IoCs pushed to Data Tables (verdict not MALICIOUS or no IoCs found)."

    lines = ["**IoC Feedback Loop — Data Tables Updated:**"]
    for table_name, rows in tables.items():
        lines.append(f"  - `{table_name}`: {len(rows)} entries added")
        for row in rows[:3]:  # Show first 3
            key = next((k for k in ["ip", "domain", "hash"] if k in row), "?")
            lines.append(f"    • {row.get(key, '?')}")
        if len(rows) > 3:
            lines.append(f"    • ... and {len(rows) - 3} more")

    return "\n".join(lines)


async def push_iocs(
    client_id: str,
    gateway_url: str,
    iocs: list[dict],
    case_id: str,
    confidence: str = "HIGH",
) -> dict:
    """Push confirmed IoCs to Chronicle Data Tables via MCP Gateway.

    Args:
        client_id: The client identifier for routing.
        gateway_url: Base URL of the MCP Gateway.
        iocs: List of {"type": str, "value": str} IoCs.
        case_id: Source case ID.
        confidence: Confidence level.

    Returns:
        Dict of {table_name: status} results.
    """
    tables = build_table_rows(iocs, case_id, confidence)
    if not tables:
        return {}

    mcp_url = f"{gateway_url}/mcp/{client_id}"
    parsed = urlparse(gateway_url)
    audience = f"{parsed.scheme}://{parsed.netloc}"

    headers = {"Content-Type": "application/json"}
    try:
        from agents.mcp_auth import needs_auth
        if needs_auth(gateway_url):
            token = get_id_token(audience)
            headers["Authorization"] = f"Bearer {token}"
    except Exception:
        logger.warning("No auth token for ioc feedback push (local dev?)")

    results = {}
    async with httpx.AsyncClient(timeout=30.0) as client:
        for table_name, rows in tables.items():
            payload = {
                "jsonrpc": "2.0",
                "id": f"feedback-{case_id}-{table_name}",
                "method": "tools/call",
                "params": {
                    "name": "add_rows_to_data_table",
                    "arguments": {
                        "tableName": table_name,
                        "rows": rows,
                    }
                }
            }
            try:
                resp = await client.post(mcp_url, json=payload, headers=headers)
                resp.raise_for_status()
                results[table_name] = "success"
            except Exception as e:
                logger.error("Failed to push to %s: %s", table_name, e)
                results[table_name] = f"error: {str(e)}"

    return results
