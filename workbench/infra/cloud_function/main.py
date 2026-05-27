"""Cloud Function: polls Chronicle SOAR for new cases, publishes to Pub/Sub.

Triggered by Cloud Scheduler (every 30s per client).
"""
import json
import logging
import os

import functions_framework
from google.cloud import firestore, pubsub_v1

logger = logging.getLogger(__name__)

PARTNER_PROJECT_ID = os.environ.get("PARTNER_PROJECT_ID", "")
PUBSUB_TOPIC = os.environ.get("PUBSUB_TOPIC", "new-cases")
MCP_GATEWAY_URL = os.environ.get("MCP_GATEWAY_URL", "")
MCP_GATEWAY_API_KEY = os.environ.get("MCP_GATEWAY_API_KEY", "")

db = firestore.Client(project=PARTNER_PROJECT_ID)
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PARTNER_PROJECT_ID, PUBSUB_TOPIC)


@functions_framework.http
def poll_cases(request):
    """HTTP Cloud Function entry point. Called by Cloud Scheduler."""
    import httpx

    # Get list of enabled clients
    clients_ref = db.collection("clients").where("enabled", "==", True)
    clients = [doc.to_dict() for doc in clients_ref.stream()]

    total_new = 0

    for client in clients:
        client_id = client.get("client_id")
        if not client_id:
            continue

        try:
            # Call list_cases via MCP Gateway
            new_cases = _poll_client(client_id)
            total_new += len(new_cases)

            # Publish new cases to Pub/Sub
            for case in new_cases:
                message = json.dumps({
                    "client_id": client_id,
                    "case_id": case.get("id"),
                    "alert_type": case.get("alertType", "GENERIC"),
                    "environment_id": client.get("soar_environment_id", ""),
                }).encode("utf-8")
                publisher.publish(topic_path, message)
                logger.info("Published new case", extra={"client_id": client_id, "case_id": case.get("id")})

        except Exception as e:
            logger.error("Failed to poll %s: %s", client_id, e)

    return json.dumps({"status": "ok", "new_cases": total_new}), 200


def _poll_client(client_id: str) -> list[dict]:
    """Poll a single client for new cases, compare with poll_state."""
    import httpx

    # Get last known case IDs
    poll_ref = db.collection("poll_state").document(client_id)
    poll_doc = poll_ref.get()
    last_case_ids = set()
    if poll_doc.exists:
        last_case_ids = set(poll_doc.to_dict().get("last_case_ids", []))

    # Fetch current open cases via MCP
    url = f"{MCP_GATEWAY_URL}/mcp/{client_id}"
    headers = {
        "Authorization": f"Bearer {MCP_GATEWAY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    with httpx.Client(timeout=30.0) as http:
        # Initialize
        init_body = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "case-poller", "version": "1.0.0"},
            },
            "id": 1,
        }
        init_resp = http.post(url, json=init_body, headers=headers)
        init_resp.raise_for_status()

        session_id = init_resp.headers.get("mcp-session-id")
        if session_id:
            headers["mcp-session-id"] = session_id

        # List cases
        list_body = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "list_cases", "arguments": {"filter": "Status='OPENED'"}},
            "id": 2,
        }
        list_resp = http.post(url, json=list_body, headers=headers)
        list_resp.raise_for_status()

    result = list_resp.json()
    content = result.get("result", {}).get("content", [])
    text = content[0].get("text", "{}") if content else "{}"

    try:
        cases_data = json.loads(text)
    except json.JSONDecodeError:
        cases_data = {}

    current_cases = cases_data.get("cases", [])
    current_ids = {c.get("id") for c in current_cases if c.get("id")}

    # Find new cases
    new_ids = current_ids - last_case_ids
    new_cases = [c for c in current_cases if c.get("id") in new_ids]

    # Update poll state
    from datetime import datetime, timezone

    poll_ref.set({
        "client_id": client_id,
        "last_poll_at": datetime.now(timezone.utc),
        "last_case_ids": list(current_ids)[:500],  # Cap to avoid large docs
    })

    return new_cases
