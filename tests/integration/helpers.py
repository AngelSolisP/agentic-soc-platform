"""
Shared constants and utilities for integration tests.

Separated from conftest.py to allow reliable imports from test modules.
"""

import os
import json
from unittest.mock import MagicMock, AsyncMock

import httpx

from proxy.mcp_gateway.model_armor import SanitizeResult, FilterResult
from proxy.mcp_gateway.router import ClientConfig

# ---------------------------------------------------------------------------
# Mode detection
# ---------------------------------------------------------------------------
IS_LIVE = os.environ.get("INTEGRATION_TEST_MODE", "mock").lower() == "live"

# ---------------------------------------------------------------------------
# Synthetic test data (overridable via env vars for live mode)
# ---------------------------------------------------------------------------
SYNTHETIC = {
    "client_id_a": os.environ.get("LIVE_CLIENT_ID_A", "nfr-partner-client"),
    "client_id_b": os.environ.get("LIVE_CLIENT_ID_B", "nfr-client-b"),
    "case_id": os.environ.get("TEST_CASE_ID", "CASE-INT-001"),
    "alert_type": "PHISHING",
    "severity": "HIGH",
    "ioc_ip": os.environ.get("TEST_IOC_IP", "203.0.113.42"),
    "ioc_domain": os.environ.get("TEST_IOC_DOMAIN", "evil-phish.example.com"),
    "hostname": os.environ.get("TEST_HOSTNAME", "workstation-int-01"),
    "partner_project_id": os.environ.get("PARTNER_PROJECT_ID", "test-partner-project"),
}

# ---------------------------------------------------------------------------
# Client configs for multi-tenancy tests
# ---------------------------------------------------------------------------
CLIENT_A_CONFIG = ClientConfig(
    client_id=SYNTHETIC["client_id_a"],
    display_name="Partner NFR (Test)",
    gcp_project_id="project-alpha",
    chronicle_customer_id="uuid-alpha-1234",
    chronicle_region="us",
    service_account_email="nfr-sa@project-alpha.iam.gserviceaccount.com",
    enabled=True,
    gti_enabled=True,
)

CLIENT_B_CONFIG = ClientConfig(
    client_id=SYNTHETIC["client_id_b"],
    display_name="NFR Client B (Test)",
    gcp_project_id="project-beta",
    chronicle_customer_id="uuid-beta-5678",
    chronicle_region="us",
    service_account_email="nfr-sa@project-beta.iam.gserviceaccount.com",
    enabled=True,
    gti_enabled=False,
)

# ---------------------------------------------------------------------------
# HITL mock approval document
# ---------------------------------------------------------------------------
MOCK_APPROVAL = {
    "approval_id": "test-approval-int-001",
    "client_id": SYNTHETIC["client_id_a"],
    "case_id": SYNTHETIC["case_id"],
    "agent_name": f"response_agent_{SYNTHETIC['client_id_a']}",
    "session_id": "session-int-001",
    "status": "PENDING",
    "proposed_action": {
        "proposed_action": "isolate_endpoint",
        "integration": "EDR",
        "parameters": {"hostname": SYNTHETIC["hostname"]},
        "justification": "Ransomware confirmed on host",
        "reversible": False,
        "hitl_required": True,
    },
    "triage_summary": f"Confirmed ransomware activity on {SYNTHETIC['hostname']}",
    "analyst_instructions": "",
    "created_at": "2026-03-25T10:00:00Z",
    "updated_at": "2026-03-25T10:00:00Z",
    "decided_by": None,
    "decided_at": None,
}


# ---------------------------------------------------------------------------
# Chronicle mock response factory
# ---------------------------------------------------------------------------
def make_chronicle_response(result_payload: dict, request_id: int = 1) -> MagicMock:
    """Create a mock httpx.Response with a valid JSON-RPC 2.0 body.

    Includes aread/aclose for streaming forward compatibility.
    """
    body = json.dumps({
        "jsonrpc": "2.0",
        "result": result_payload,
        "id": request_id,
    })
    content = body.encode()
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.content = content
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.aread = AsyncMock(return_value=content)
    mock_resp.aclose = AsyncMock()
    return mock_resp


def safe_armor_result():
    return SanitizeResult(allowed=True, filter_result=FilterResult.SAFE)
