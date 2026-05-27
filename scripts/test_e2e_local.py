#!/usr/bin/env python3
"""
Local E2E Pipeline Test — Runs the full orchestrator against a real Chronicle case.

Uses the cloud MCP Gateway but runs agents locally (no Cloud Run deploy needed).
Minimal billing: a few Gemini calls + MCP tool calls.

Usage:
    export GATEWAY_URL="https://your-mcp-gateway-url.run.app"
    export MCP_GATEWAY_URL="$GATEWAY_URL"
    export GOOGLE_GENAI_USE_VERTEXAI=true
    export GOOGLE_CLOUD_PROJECT=your-partner-gcp-project
    export GOOGLE_CLOUD_LOCATION=us-central1
    .venv/bin/python scripts/test_e2e_local.py
"""

import asyncio
import json
import os
import subprocess
import sys
import time

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _prefetch_mcp_token(gateway_url: str) -> None:
    """Pre-generate an identity token via SA impersonation and inject into auth cache.

    This allows local testing against the cloud MCP Gateway without modifying
    the core auth module. Uses the same impersonation pattern as test_mcp_live.py.
    """
    sa_email = os.environ.get(
        "MCP_IMPERSONATE_SA",
        f"agentic-soc-workbench@{os.environ.get('GOOGLE_CLOUD_PROJECT', 'your-partner-gcp-project')}.iam.gserviceaccount.com",
    )
    print(f"  Generating MCP token via SA impersonation ({sa_email})...")
    try:
        token = subprocess.check_output(
            [
                "gcloud", "auth", "print-identity-token",
                f"--impersonate-service-account={sa_email}",
                f"--audiences={gateway_url}",
            ],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to generate token: {e}")
        print("  Ensure your user has roles/iam.serviceAccountTokenCreator on the SA.")
        sys.exit(1)

    # Inject into mcp_auth's module-level cache so McpToolset picks it up
    from agents.mcp_auth import _id_token_cache
    _id_token_cache[gateway_url] = (token, time.time() + 3500)
    print(f"  ✓ Token cached (len={len(token)})")


async def main():
    # ── Config ────────────────────────────────────────────────────────
    client_id = os.environ.get("E2E_CLIENT_ID", "demo-tenant")
    case_id = os.environ.get("E2E_CASE_ID", "2734")
    alert_type = os.environ.get("E2E_ALERT_TYPE", "MALWARE")
    severity = os.environ.get("E2E_SEVERITY", "HIGH")
    gateway_url = os.environ.get("MCP_GATEWAY_URL", "https://your-mcp-gateway-url.run.app")
    gti_enabled = os.environ.get("E2E_GTI_ENABLED", "false").lower() == "true"

    # Force Vertex AI backend for Gemini
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "your-partner-gcp-project")
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
    os.environ.setdefault("MCP_GATEWAY_URL", gateway_url)
    # Use shorter timeout for local testing
    os.environ.setdefault("AGENT_TIMEOUT_SECONDS", "180")
    # Reduce LLM calls for cost
    os.environ.setdefault("MAX_LLM_CALLS_PER_PIPELINE", "20")

    # Pre-fetch MCP token for local → cloud auth
    _prefetch_mcp_token(gateway_url)

    print("=" * 70)
    print("AGENTIC SOC — Local E2E Pipeline Test")
    print("=" * 70)
    print(f"  Client:     {client_id}")
    print(f"  Case ID:    {case_id}")
    print(f"  Alert Type: {alert_type}")
    print(f"  Severity:   {severity}")
    print(f"  GTI:        {gti_enabled}")
    print(f"  Gateway:    {gateway_url}")
    print(f"  Project:    {os.environ.get('GOOGLE_CLOUD_PROJECT')}")
    print("=" * 70)

    # ── Import after env vars are set ─────────────────────────────────
    from agents.orchestrator.agent import AgenticSOCOrchestrator

    # ── Create orchestrator (no Firestore for dedup/stage tracking in local mode) ──
    orchestrator = AgenticSOCOrchestrator(
        partner_project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", "your-partner-gcp-project"),
        gateway_url=gateway_url,
    )

    # ── Run pipeline ──────────────────────────────────────────────────
    print(f"\n▶ Starting pipeline for case {case_id}...")
    start = time.time()

    try:
        result = await orchestrator.process_alert(
            client_id=client_id,
            case_id=case_id,
            alert_type=alert_type,
            severity=severity,
            autonomous_mode=True,  # NFR tenant — no HITL friction
            gti_enabled=gti_enabled,
            chronicle_region="us",
        )
    except Exception as e:
        elapsed = round(time.time() - start, 2)
        print(f"\n✗ Pipeline FAILED after {elapsed}s: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    elapsed = round(time.time() - start, 2)

    # ── Results ───────────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print(f"PIPELINE COMPLETE — {elapsed}s")
    print(f"{'=' * 70}")
    print(f"  Case ID:    {result.get('case_id')}")
    print(f"  Client:     {result.get('client_id')}")
    print(f"  Session:    {result.get('session_id')}")
    print(f"  Timed Out:  {result.get('timed_out')}")
    print(f"  Elapsed:    {result.get('elapsed_seconds')}s")

    response_text = result.get("agent_response", "")
    print(f"\n▶ Agent Response ({len(response_text)} chars):")
    print("-" * 70)
    print(response_text[:3000])
    if len(response_text) > 3000:
        print(f"\n... [{len(response_text) - 3000} chars truncated]")
    print("-" * 70)

    # ── Validate key fields in response ───────────────────────────────
    print("\n▶ Validation Checks:")
    checks = {
        "Has response text": bool(response_text),
        "Not timed out": not result.get("timed_out"),
        "Contains verdict": any(v in response_text.upper() for v in ["MALICIOUS", "SUSPICIOUS", "BENIGN", "INCONCLUSIVE"]),
        "Contains case_id": case_id in response_text,
        "Contains case_alerts or caseAlertId": "caseAlertId" in response_text or "case_alerts" in response_text,
        "Contains iocs_found or IoC data": "iocs_found" in response_text or "ioc" in response_text.lower(),
        "Contains recommended_action": any(a in response_text for a in ["CLOSE_FP", "ESCALATE_T2", "MONITOR", "CONTAIN"]),
    }

    all_passed = True
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
        if not passed:
            all_passed = False

    print(f"\n{'=' * 70}")
    if all_passed:
        print("✓ ALL CHECKS PASSED — Pipeline E2E working correctly")
    else:
        print("⚠ SOME CHECKS FAILED — Review agent response above")
    print(f"{'=' * 70}")

    # Dump full result as JSON for inspection
    print("\n▶ Full result JSON:")
    print(json.dumps(result, indent=2, default=str)[:2000])

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
