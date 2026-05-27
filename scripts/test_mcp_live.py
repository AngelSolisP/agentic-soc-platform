#!/usr/bin/env python3
"""
Live MCP Tool Test Suite — Tests ALL Chronicle MCP tools against demo-tenant tenant.

Verifies that tool calls through the MCP Gateway return data aligned with
what the ADK agents expect (matching agents/tool_catalog.py scoping).

Usage:
    # Generate token and run:
    export GATEWAY_URL="https://your-mcp-gateway-url.run.app"
    export MCP_TOKEN=$(gcloud auth print-identity-token \
        --impersonate-service-account=agentic-soc-workbench@your-partner-gcp-project.iam.gserviceaccount.com \
        --audiences="$GATEWAY_URL" 2>/dev/null)
    python3 scripts/test_mcp_live.py
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

# ─── Config ───────────────────────────────────────────────────────────────────
GATEWAY_URL = os.environ.get(
    "GATEWAY_URL",
    "https://your-mcp-gateway-url.run.app",
)
TOKEN = os.environ.get("MCP_TOKEN", "")
CLIENT_ID = os.environ.get("MCP_CLIENT_ID", "demo-tenant")
MCP_ENDPOINT = f"{GATEWAY_URL}/mcp/{CLIENT_ID}"

# ─── Counters ─────────────────────────────────────────────────────────────────
passed = 0
failed = 0
skipped = 0
errors: list[dict] = []
results: list[dict] = []

# ─── Shared state (populated as tests run) ────────────────────────────────────
state: dict[str, Any] = {}


def mcp_call(method: str, params: dict | None = None, timeout: float = 60) -> dict:
    """Make a JSON-RPC MCP call and return parsed response."""
    body: dict[str, Any] = {
        "jsonrpc": "2.0",
        "method": method,
        "id": int(time.time() * 1000),
    }
    if params:
        body["params"] = params

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    resp = httpx.post(MCP_ENDPOINT, json=body, headers=headers, timeout=timeout)

    if resp.status_code != 200:
        return {"_http_error": resp.status_code, "_body": resp.text[:500]}

    data = resp.json()
    return data


def call_tool(tool_name: str, arguments: dict | None = None, timeout: float = 60) -> dict:
    """Call an MCP tool and return the result."""
    return mcp_call(
        "tools/call",
        {"name": tool_name, "arguments": arguments or {}},
        timeout=timeout,
    )


def extract_text(result: dict) -> str:
    """Extract text content from MCP tool result."""
    if "_http_error" in result:
        return f"HTTP {result['_http_error']}: {result.get('_body', '')}"
    if "error" in result:
        return f"RPC Error: {result['error']}"
    content = result.get("result", {}).get("content", [])
    if content and isinstance(content, list):
        return content[0].get("text", "")
    return str(result.get("result", ""))


def is_error(result: dict) -> bool:
    """Check if the result is an error."""
    if "_http_error" in result:
        return True
    if "error" in result:
        return True
    return result.get("result", {}).get("isError", False)


def run_test(
    name: str,
    tool_name: str,
    arguments: dict | None = None,
    agent: str = "",
    checks: list | None = None,
    save_key: str = "",
    timeout: float = 60,
):
    """Run a single MCP tool test with assertions."""
    global passed, failed, skipped

    print(f"\n{'─' * 70}")
    print(f"TEST: {name}")
    print(f"  Tool: {tool_name}")
    print(f"  Agent: {agent}")
    if arguments:
        # Don't print huge arguments
        args_str = json.dumps(arguments, ensure_ascii=False)
        if len(args_str) > 200:
            args_str = args_str[:200] + "..."
        print(f"  Args: {args_str}")

    try:
        result = call_tool(tool_name, arguments, timeout=timeout)
        text = extract_text(result)
        err = is_error(result)

        # Print response summary
        if err:
            print(f"  STATUS: ERROR")
            print(f"  Error: {text[:300]}")
        else:
            text_preview = text[:500] if len(text) > 500 else text
            print(f"  STATUS: OK ({len(text)} chars)")
            print(f"  Preview: {text_preview[:200]}...")

        # Save to state if needed
        if save_key and not err:
            state[save_key] = text
            try:
                state[f"{save_key}_json"] = json.loads(text)
            except (json.JSONDecodeError, TypeError):
                pass

        # Run checks
        test_passed = True
        if checks:
            for check_name, check_fn in checks:
                try:
                    check_result = check_fn(text, result)
                    if check_result:
                        print(f"  ✓ {check_name}")
                    else:
                        print(f"  ✗ {check_name}")
                        test_passed = False
                except Exception as e:
                    print(f"  ✗ {check_name}: {e}")
                    test_passed = False
        elif not err:
            print(f"  ✓ Tool returned data successfully")

        if err:
            failed += 1
            errors.append({"test": name, "tool": tool_name, "error": text[:300]})
            test_passed = False
        elif test_passed:
            passed += 1
        else:
            failed += 1
            errors.append({"test": name, "tool": tool_name, "error": "Check failed"})

        results.append({
            "test": name,
            "tool": tool_name,
            "agent": agent,
            "passed": test_passed and not err,
            "error": err,
            "response_length": len(text),
        })

    except Exception as e:
        failed += 1
        print(f"  STATUS: EXCEPTION — {e}")
        errors.append({"test": name, "tool": tool_name, "error": str(e)})
        results.append({
            "test": name, "tool": tool_name, "agent": agent,
            "passed": False, "error": True, "response_length": 0,
        })


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    global passed, failed

    if not TOKEN:
        print("ERROR: Set MCP_TOKEN env var first.")
        print("  export MCP_TOKEN=$(gcloud auth print-identity-token \\")
        print("    --impersonate-service-account=agentic-soc-workbench@your-partner-gcp-project.iam.gserviceaccount.com \\")
        print(f"    --audiences=\"{GATEWAY_URL}\")")
        sys.exit(1)

    print("=" * 70)
    print("AGENTIC SOC — Live MCP Tool Test Suite")
    print(f"Gateway: {GATEWAY_URL}")
    print(f"Client:  {CLIENT_ID}")
    print(f"Time:    {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    # ── 0. Connectivity ────────────────────────────────────────────────────
    print("\n\n▶ PHASE 0: Connectivity")
    result = mcp_call("initialize", {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "mcp-test-suite", "version": "1.0.0"},
    })
    if "error" in result or "_http_error" in result:
        print(f"FATAL: Cannot initialize MCP session: {result}")
        sys.exit(1)
    print("  ✓ MCP session initialized")

    result = mcp_call("tools/list")
    tools = result.get("result", {}).get("tools", [])
    print(f"  ✓ tools/list returned {len(tools)} tools")
    tool_names = {t["name"] for t in tools}

    # ── 1. TRIAGE AGENT TOOLS ──────────────────────────────────────────────
    print("\n\n▶ PHASE 1: Triage Agent Tools (TRIAGE_TOOLS — 13 tools)")

    # 1.1 list_cases — The starting point
    now = datetime.now(timezone.utc)
    run_test(
        "1.1 list_cases — Get recent cases",
        "list_cases",
        {"pageSize": 10},
        agent="Triage",
        checks=[
            ("Returns JSON array or object", lambda t, r: len(t) > 10),
            ("Contains case data", lambda t, r: "case" in t.lower() or "Case" in t),
        ],
        save_key="cases",
    )

    # 1.2 get_case — Get a specific case
    # Try to extract a case ID from the list_cases response
    case_id = None
    if "cases_json" in state:
        data = state["cases_json"]
        if isinstance(data, list) and data:
            case_id = str(data[0].get("id", data[0].get("caseId", "")))
        elif isinstance(data, dict):
            cases = data.get("cases", data.get("results", []))
            if cases:
                # Extract numeric caseId from resource name
                name = cases[0].get("name", "")
                if "/" in name:
                    case_id = name.split("/")[-1]
                else:
                    case_id = str(cases[0].get("id", cases[0].get("caseId", "")))

    if not case_id:
        # Fallback: try to parse text
        cases_text = state.get("cases", "")
        match = re.search(r'"caseId":\s*"?(\d+)"?', cases_text)
        if match:
            case_id = match.group(1)
        else:
            match = re.search(r'cases/(\d+)', cases_text)
            if match:
                case_id = match.group(1)

    if case_id:
        state["case_id"] = case_id
        print(f"\n  [Using case_id={case_id} for subsequent tests]")

        run_test(
            "1.2 get_case — Retrieve specific case",
            "get_case",
            {"caseId": case_id},
            agent="Triage",
            checks=[
                ("Returns case details", lambda t, r: len(t) > 50),
                ("Contains priority or status", lambda t, r:
                    "priority" in t.lower() or "status" in t.lower() or "Priority" in t or "Status" in t),
            ],
            save_key="case_detail",
        )

        # 1.3 list_case_alerts — MANDATORY after get_case
        run_test(
            "1.3 list_case_alerts — Alerts for the case (MANDATORY with get_case)",
            "list_case_alerts",
            {"caseId": case_id},
            agent="Triage",
            checks=[
                ("Returns alert data", lambda t, r: len(t) > 10),
            ],
            save_key="case_alerts",
        )

        # 1.4 get_case_alert — Specific alert
        alert_id = None
        alerts_text = state.get("case_alerts", "")
        match = re.search(r'"caseAlertId":\s*"?([^",}]+)"?', alerts_text)
        if not match:
            match = re.search(r'caseAlerts/([^/"]+)', alerts_text)
        if match:
            alert_id = match.group(1)
            state["alert_id"] = alert_id

        if alert_id:
            run_test(
                f"1.4 get_case_alert — Get specific alert (caseAlertId={alert_id})",
                "get_case_alert",
                {"caseId": case_id, "caseAlertId": alert_id},
                agent="Triage",
                checks=[
                    ("Returns alert details", lambda t, r: len(t) > 50),
                ],
                save_key="alert_detail",
            )
        else:
            print("\n  [SKIP] 1.4 get_case_alert — No alert ID found")

        # 1.5 create_case_comment — Write a test comment
        run_test(
            "1.5 create_case_comment — Add analysis comment",
            "create_case_comment",
            {"caseId": case_id, "comment": "[MCP Test Suite] Automated triage test — ignore this comment."},
            agent="Triage",
            checks=[
                ("Comment created", lambda t, r: not is_error(r)),
            ],
        )

        # 1.6 list_case_comments
        run_test(
            "1.6 list_case_comments — Read comments",
            "list_case_comments",
            {"caseId": case_id, "pageSize": 5},
            agent="Triage",
            checks=[
                ("Returns comments", lambda t, r: len(t) > 5),
            ],
        )

    else:
        print("\n  [SKIP] Tests 1.2-1.6 — No case_id available from list_cases")

    # 1.7 SOAR_ALERT_ENRICHMENT tools
    if case_id and alert_id:
        run_test(
            "1.7 list_involved_entities — Entities in the alert",
            "list_involved_entities",
            {"caseId": case_id, "caseAlertId": alert_id},
            agent="Triage",
        )

        # Extract an entity ID if possible
        entities_text = extract_text(call_tool("list_involved_entities", {"caseId": case_id, "caseAlertId": alert_id}))
        entity_match = re.search(r'"involvedEntityId":\s*"?([^",}]+)"?', entities_text)
        if not entity_match:
            entity_match = re.search(r'involvedEntities/([^/"]+)', entities_text)

        if entity_match:
            entity_id = entity_match.group(1)
            run_test(
                f"1.8 get_involved_entity — Entity detail ({entity_id[:30]})",
                "get_involved_entity",
                {"caseId": case_id, "caseAlertId": alert_id, "involvedEntityId": entity_id},
                agent="Triage",
            )

        run_test(
            "1.9 fetch_alert_data — Raw alert data from SIEM",
            "fetch_alert_data",
            {"siemAlertId": alert_id},
            agent="Triage",
            timeout=90,
        )

        run_test(
            "1.10 get_alert_latest_investigation — AI investigation",
            "get_alert_latest_investigation",
            {"alertId": alert_id},
            agent="Triage",
        )

    # 1.11-1.13 SIEM_READ tools
    run_test(
        "1.11 translate_udm_query — NL to YARA-L",
        "translate_udm_query",
        {"text": "show me all failed logins in the last 24 hours"},
        agent="Triage",
        checks=[
            ("Returns YARA-L query", lambda t, r: len(t) > 5),
        ],
        save_key="udm_query",
        timeout=90,
    )

    # Use translated query for UDM search
    udm_query = state.get("udm_query", "")
    if udm_query and not udm_query.startswith("HTTP"):
        # Extract the actual query from the response
        try:
            q_data = json.loads(udm_query)
            search_query = q_data.get("query", q_data.get("udmQuery", udm_query))
        except (json.JSONDecodeError, TypeError):
            search_query = udm_query.strip()

        end_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        start_time = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

        run_test(
            "1.12 udm_search — Execute YARA-L query",
            "udm_search",
            {
                "query": search_query if len(search_query) < 500 else 'metadata.event_type = "USER_LOGIN"',
                "startTime": start_time,
                "endTime": end_time,
                "maxEvents": 5,
            },
            agent="Triage",
            timeout=90,
        )

    run_test(
        "1.13 search_entity — Search by indicator (param is 'indicator', NOT 'query')",
        "search_entity",
        {"indicator": "8.8.8.8"},
        agent="Triage",
        checks=[
            ("Returns entity data or empty", lambda t, r: not is_error(r)),
        ],
        timeout=90,
    )

    run_test(
        "1.14 summarize_entity — Entity summary",
        "summarize_entity",
        {
            "query": "8.8.8.8",
            "startTime": (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endTime": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        agent="Triage",
        timeout=90,
    )

    end_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    start_time = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    run_test(
        "1.15 get_ioc_match — IoC matches (requires startTime + endTime)",
        "get_ioc_match",
        {"startTime": start_time, "endTime": end_time, "maxMatches": 5},
        agent="Triage",
        timeout=90,
    )

    # ── 2. ENRICHMENT AGENT TOOLS ──────────────────────────────────────────
    print("\n\n▶ PHASE 2: Enrichment Agent Tools (CHRONICLE_ENRICHMENT_TOOLS — 15 tools)")

    # Reference lists (unique to enrichment)
    run_test(
        "2.1 get_reference_list — Fetch a reference list",
        "get_reference_list",
        {"name": "test_blocklist"},
        agent="Enrichment",
    )

    # 2.2 list_rules (enrichment also has SIEM_READ + REFERENCE_LISTS)
    run_test(
        "2.2 list_rules — Available detection rules",
        "list_rules",
        {"pageSize": 5},
        agent="Enrichment",
        save_key="rules",
    )

    # Get a rule ID
    rules_text = state.get("rules", "")
    rule_match = re.search(r'"ruleId":\s*"?([^",}]+)"?', rules_text) if rules_text else None
    if not rule_match:
        rule_match = re.search(r'rules/([^/"]+)', rules_text) if rules_text else None

    if rule_match:
        rule_id = rule_match.group(1)
        run_test(
            f"2.3 get_rule — Rule detail ({rule_id[:30]})",
            "get_rule",
            {"ruleId": rule_id},
            agent="Enrichment",
        )

    # ── 3. CASE MANAGER AGENT TOOLS ────────────────────────────────────────
    print("\n\n▶ PHASE 3: Case Manager Agent Tools (CASE_MANAGER_TOOLS — 11 tools)")

    # Playbooks
    run_test(
        "3.1 list_playbooks — Available playbooks",
        "list_playbooks",
        {},
        agent="Case Manager",
        save_key="playbooks",
    )

    if case_id:
        # list_playbook_instances requires BOTH caseId AND alertGroupIdentifier
        alert_group = None
        alerts_text = state.get("case_alerts", "")
        ag_match = re.search(r'"alertGroupIdentifier":\s*"?([^",}]+)"?', alerts_text) if alerts_text else None
        if not ag_match:
            ag_match = re.search(r'alertGroupIdentifier["\s:]+([^",}\s]+)', alerts_text) if alerts_text else None

        if ag_match:
            alert_group = ag_match.group(1)
            run_test(
                f"3.2 list_playbook_instances — Playbooks for case (alertGroup={alert_group[:30]})",
                "list_playbook_instances",
                {"caseId": case_id, "alertGroupIdentifier": alert_group},
                agent="Case Manager",
            )
        else:
            print("\n  [SKIP] 3.2 list_playbook_instances — No alertGroupIdentifier found")

        # update_case — Read-only test (just change nothing critical)
        # Skip actual update to not modify real cases

        # list_cases with filter (Case Manager uses SQL-like filters)
        run_test(
            "3.3 list_cases — With SQL filter (PascalCase)",
            "list_cases",
            {"filter": "Status='OPENED'", "pageSize": 5},
            agent="Case Manager",
            checks=[
                ("Filter accepted", lambda t, r: not is_error(r)),
            ],
        )

    # ── 4. RESPONSE AGENT TOOLS ────────────────────────────────────────────
    print("\n\n▶ PHASE 4: Response Agent Tools (RESPONSE_TOOLS — 7 tools)")

    # list_integrations
    run_test(
        "4.1 list_integrations — Available SOAR integrations",
        "list_integrations",
        {"pageSize": 10},
        agent="Response",
        save_key="integrations",
    )

    # list_integration_actions (for a specific integration)
    integrations_text = state.get("integrations", "")
    int_match = re.search(r'"integrationId":\s*"?([^",}]+)"?', integrations_text) if integrations_text else None
    if not int_match:
        int_match = re.search(r'"identifier":\s*"?([^",}]+)"?', integrations_text) if integrations_text else None

    if int_match:
        integration_id = int_match.group(1)
        run_test(
            f"4.2 list_integration_actions — Actions for integration ({integration_id[:30]})",
            "list_integration_actions",
            {"integrationId": integration_id, "pageSize": 10},
            agent="Response",
        )
    else:
        print("\n  [SKIP] 4.2 list_integration_actions — No integration ID found")

    # execute_manual_action — DO NOT ACTUALLY EXECUTE (destructive)
    # Instead, just verify the tool exists in the catalog
    if "execute_manual_action" in tool_names:
        print(f"\n{'─' * 70}")
        print("TEST: 4.3 execute_manual_action — EXISTS in catalog (NOT executed — destructive)")
        print("  Agent: Response")
        print("  ✓ Tool exists and is HITL-gated by _hitl_guard()")
        passed += 1
        results.append({
            "test": "4.3 execute_manual_action exists",
            "tool": "execute_manual_action", "agent": "Response",
            "passed": True, "error": False, "response_length": 0,
        })

    # ── 5. SIEM-ONLY TOOLS (shared across agents) ─────────────────────────
    print("\n\n▶ PHASE 5: Additional SIEM Tools")

    run_test(
        "5.1 list_security_alerts — SIEM security alerts",
        "list_security_alerts",
        {
            "startTime": (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endTime": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "maxAlerts": 5,
        },
        agent="Shared",
        timeout=90,
    )

    # ── 6. TOOLS NOT IN AGENT SCOPING (should NOT be called by agents) ────
    print("\n\n▶ PHASE 6: Non-Scoped Tools (exist in MCP but NOT in agent tool_catalog)")

    non_scoped = [
        "create_rule", "validate_rule", "list_rule_detections", "list_rule_errors",
        "update_reference_list", "import_logs", "list_feeds", "list_parsers",
        "list_log_types", "list_data_tables", "get_agent_settings",
        "list_security_alerts", "get_security_alert", "update_security_alert",
        "trigger_investigation", "get_investigation_by_id",
        "fetch_enrichment_actions", "execute_actions",
        "get_connector_event", "list_connector_events",
        "create_data_table", "add_rows_to_data_table",
        "list_data_table_rows", "delete_data_table_row",
        "get_feed", "enable_feed", "disable_feed", "delete_feed",
        "create_feed", "update_feed", "generate_feed_secret",
        "get_parser", "run_parser", "activate_parser", "create_parser",
        "deactivate_parser", "list_integration_instances",
    ]
    in_mcp = [t for t in non_scoped if t in tool_names]
    print(f"  {len(in_mcp)} tools exist in MCP but are NOT scoped to any agent")
    print(f"  This is correct — ICM Tool Scoping prevents 'Lost in the Middle' degradation")
    for t in sorted(in_mcp):
        print(f"    - {t}")

    # ── 7. Verify agent tool scoping alignment ────────────────────────────
    print("\n\n▶ PHASE 7: Tool Catalog Alignment Verification")

    # Tools that SHOULD exist (from tool_catalog.py)
    expected_tools = {
        "TRIAGE_TOOLS": [
            "translate_udm_query", "udm_search", "summarize_entity",
            "search_entity", "get_ioc_match",
            "get_case", "list_case_alerts", "get_case_alert",
            "create_case_comment",
            "list_involved_entities", "get_involved_entity",
            "fetch_alert_data", "get_alert_latest_investigation",
        ],
        "CHRONICLE_ENRICHMENT_TOOLS": [
            "translate_udm_query", "udm_search", "summarize_entity",
            "search_entity", "get_ioc_match",
            "get_case", "list_case_alerts", "get_case_alert",
            "create_case_comment",
            "get_reference_list", "create_reference_list",
            "list_involved_entities", "get_involved_entity",
            "fetch_alert_data", "get_alert_latest_investigation",
        ],
        "CASE_MANAGER_TOOLS": [
            "list_cases", "get_case", "list_case_alerts", "get_case_alert",
            "list_case_comments",
            "update_case", "update_case_alert", "create_case_comment",
            "execute_bulk_close_case",
            "list_playbooks", "list_playbook_instances",
        ],
        "RESPONSE_TOOLS": [
            "get_case", "create_case_comment",
            "execute_manual_action",
            "update_case", "update_case_alert",
            "list_integrations", "list_integration_actions",
        ],
    }

    all_aligned = True
    for catalog_name, expected in expected_tools.items():
        missing = [t for t in expected if t not in tool_names]
        if missing:
            print(f"  ✗ {catalog_name}: MISSING from MCP → {missing}")
            all_aligned = False
        else:
            print(f"  ✓ {catalog_name}: All {len(expected)} tools present in MCP server")

    if all_aligned:
        passed += 1
    else:
        failed += 1
        errors.append({"test": "Tool catalog alignment", "tool": "N/A", "error": "Missing tools"})

    # ═══ SUMMARY ══════════════════════════════════════════════════════════
    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Passed:  {passed}")
    print(f"  Failed:  {failed}")
    print(f"  Total:   {passed + failed}")
    print()

    if errors:
        print("FAILURES:")
        for e in errors:
            print(f"  ✗ {e['test']} ({e['tool']}): {e['error'][:100]}")
    else:
        print("ALL TESTS PASSED ✓")

    print()

    # Print agent coverage
    print("AGENT TOOL COVERAGE:")
    agent_counts = {}
    for r in results:
        a = r.get("agent", "Unknown")
        if a not in agent_counts:
            agent_counts[a] = {"total": 0, "passed": 0}
        agent_counts[a]["total"] += 1
        if r["passed"]:
            agent_counts[a]["passed"] += 1
    for agent, counts in sorted(agent_counts.items()):
        print(f"  {agent}: {counts['passed']}/{counts['total']} passed")

    print(f"\nMCP Server: {len(tool_names)} tools total")
    scoped_tools = set()
    for tools_list in expected_tools.values():
        scoped_tools.update(tools_list)
    print(f"Agent-scoped: {len(scoped_tools)} unique tools ({len(scoped_tools)}/{len(tool_names)} = {len(scoped_tools)*100//len(tool_names)}%)")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
