"""
Integration tests — MVP 1.5, 1.6

1.5  Response Agent submits isolation request -> appears in HITL Dashboard
1.6  Analyst approves -> execute_manual_action fires
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from .helpers import IS_LIVE, SYNTHETIC, MOCK_APPROVAL


# ---------------------------------------------------------------------------
# MVP 1.5 — Response Agent submits isolation request to HITL Dashboard
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.mock
def test_hitl_queue_submit_creates_pending_document():
    """HITLQueue.submit_approval_request writes a PENDING doc to Firestore."""
    with patch("agents.response.agent.firestore.Client") as mock_fs:
        mock_db = MagicMock()
        mock_fs.return_value = mock_db

        from agents.response.agent import HITLQueue

        queue = HITLQueue(partner_project_id="test-project")
        approval_id = queue.submit_approval_request(
            client_id=SYNTHETIC["client_id_a"],
            case_id=SYNTHETIC["case_id"],
            agent_name=f"response_agent_{SYNTHETIC['client_id_a']}",
            proposed_action={
                "proposed_action": "isolate_endpoint",
                "integration": "EDR",
                "parameters": {"hostname": SYNTHETIC["hostname"]},
                "justification": "Ransomware confirmed",
                "reversible": False,
                "hitl_required": True,
            },
            triage_summary="Confirmed ransomware on workstation-int-01",
            session_id="session-int-001",
        )

        assert approval_id is not None
        # Verify Firestore .set() was called
        mock_db.collection.assert_called_with("hitl_approvals")
        doc_ref = mock_db.collection.return_value.document.return_value
        doc_ref.set.assert_called_once()

        # Verify document contents
        written_doc = doc_ref.set.call_args[0][0]
        assert written_doc["status"] == "PENDING"
        assert written_doc["case_id"] == SYNTHETIC["case_id"]
        assert written_doc["client_id"] == SYNTHETIC["client_id_a"]
        assert written_doc["proposed_action"]["proposed_action"] == "isolate_endpoint"
        assert written_doc["approval_id"] == approval_id


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.mock
async def test_hitl_approval_appears_in_dashboard(hitl_client):
    """Pending approval should appear in HITL Dashboard GET /approvals."""
    db_mock = hitl_client._transport.app.state._test_db_mock

    # Wire Firestore to return our mock approval
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = MOCK_APPROVAL

    q = db_mock.collection.return_value
    q.where.return_value = q
    q.order_by.return_value = q
    q.limit.return_value = q
    q.stream.return_value = [mock_doc]

    response = await hitl_client.get("/approvals?status=PENDING")
    assert response.status_code == 200
    approvals = response.json()
    assert len(approvals) >= 1
    assert any(a.get("case_id") == SYNTHETIC["case_id"] for a in approvals)


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.mock
async def test_hitl_get_specific_approval(hitl_client):
    """GET /approvals/{id} should return the specific approval."""
    db_mock = hitl_client._transport.app.state._test_db_mock

    mock_doc_ref = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = MOCK_APPROVAL
    mock_doc_ref.get.return_value = mock_doc
    db_mock.collection.return_value.document.return_value = mock_doc_ref

    response = await hitl_client.get(f"/approvals/{MOCK_APPROVAL['approval_id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["case_id"] == SYNTHETIC["case_id"]


# ---------------------------------------------------------------------------
# MVP 1.6 — Analyst approves -> execute_manual_action fires
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.mock
async def test_analyst_approval_updates_firestore(hitl_client):
    """POST /approvals/{id}/decide APPROVED should update status via Firestore transaction."""
    db_mock = hitl_client._transport.app.state._test_db_mock

    mock_doc_ref = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = MOCK_APPROVAL.copy()
    mock_doc_ref.get.return_value = mock_doc
    db_mock.collection.return_value.document.return_value = mock_doc_ref

    mock_tx = MagicMock()
    db_mock.transaction.return_value = mock_tx

    response = await hitl_client.post(
        f"/approvals/{MOCK_APPROVAL['approval_id']}/decide",
        json={
            "decision": "APPROVED",
            "analyst_id": "analyst-int-01",
            "analyst_notes": "Confirmed ransomware, proceed with isolation.",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"

    # Verify transaction.update() was called with correct status
    mock_tx.update.assert_called_once()
    update_payload = mock_tx.update.call_args[0][1]
    assert update_payload["status"] == "APPROVED"
    # decided_by comes from JWT (DEV_MODE returns "dev@local"), not body analyst_id
    assert update_payload["decided_by"] == "dev@local"
    assert "decided_at" in update_payload


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.mock
async def test_analyst_rejection_updates_firestore(hitl_client):
    """POST /approvals/{id}/decide REJECTED should update status via transaction."""
    db_mock = hitl_client._transport.app.state._test_db_mock

    mock_doc_ref = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = MOCK_APPROVAL.copy()
    mock_doc_ref.get.return_value = mock_doc
    db_mock.collection.return_value.document.return_value = mock_doc_ref

    mock_tx = MagicMock()
    db_mock.transaction.return_value = mock_tx

    response = await hitl_client.post(
        f"/approvals/{MOCK_APPROVAL['approval_id']}/decide",
        json={
            "decision": "REJECTED",
            "analyst_id": "analyst-int-02",
            "analyst_notes": "False positive, do not isolate.",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REJECTED"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.mock
async def test_already_decided_returns_409(hitl_client):
    """Deciding on an already-approved approval should return 409."""
    db_mock = hitl_client._transport.app.state._test_db_mock

    already_approved = {**MOCK_APPROVAL, "status": "APPROVED"}
    mock_doc_ref = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = already_approved
    mock_doc_ref.get.return_value = mock_doc
    db_mock.collection.return_value.document.return_value = mock_doc_ref

    mock_tx = MagicMock()
    db_mock.transaction.return_value = mock_tx

    response = await hitl_client.post(
        f"/approvals/{MOCK_APPROVAL['approval_id']}/decide",
        json={"decision": "APPROVED", "analyst_id": "analyst-int-03"},
    )

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# End-to-end: submit → approve → verify state machine
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.mock
def test_full_hitl_state_machine():
    """
    End-to-end: HITLQueue submits PENDING -> get_approval_status returns PENDING
    -> (simulate analyst approval) -> get_approval_status returns APPROVED.
    """
    with patch("agents.response.agent.firestore.Client") as mock_fs:
        mock_db = MagicMock()
        mock_fs.return_value = mock_db

        from agents.response.agent import HITLQueue

        queue = HITLQueue(partner_project_id="test-project")

        # Step 1: Submit
        approval_id = queue.submit_approval_request(
            client_id=SYNTHETIC["client_id_a"],
            case_id=SYNTHETIC["case_id"],
            agent_name="response_agent_test",
            proposed_action={"proposed_action": "isolate_endpoint"},
            triage_summary="Ransomware confirmed",
        )

        # Step 2: Simulate Firestore returning the PENDING doc
        pending_doc = MagicMock()
        pending_doc.exists = True
        pending_doc.to_dict.return_value = {
            "approval_id": approval_id,
            "status": "PENDING",
            "case_id": SYNTHETIC["case_id"],
        }
        mock_db.collection.return_value.document.return_value.get.return_value = pending_doc

        status = queue.get_approval_status(approval_id)
        assert status["status"] == "PENDING"

        # Step 3: Simulate analyst approval (Firestore now returns APPROVED)
        approved_doc = MagicMock()
        approved_doc.exists = True
        approved_doc.to_dict.return_value = {
            "approval_id": approval_id,
            "status": "APPROVED",
            "case_id": SYNTHETIC["case_id"],
            "decided_by": "analyst-1",
        }
        mock_db.collection.return_value.document.return_value.get.return_value = approved_doc

        status = queue.get_approval_status(approval_id)
        assert status["status"] == "APPROVED"
        assert status["decided_by"] == "analyst-1"


# ---------------------------------------------------------------------------
# Response Agent tool scoping
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.mock
def test_response_agent_has_minimal_tools():
    """Response agent should have core tools + integration discovery."""
    from agents.tool_catalog import RESPONSE_TOOLS

    assert len(RESPONSE_TOOLS) == 7  # 5 core + 2 integrations
    assert "execute_manual_action" in RESPONSE_TOOLS
    assert "get_case" in RESPONSE_TOOLS
    assert "create_case_comment" in RESPONSE_TOOLS
    assert "update_case" in RESPONSE_TOOLS
    assert "update_case_alert" in RESPONSE_TOOLS
    assert "list_integrations" in RESPONSE_TOOLS
    assert "list_integration_actions" in RESPONSE_TOOLS


# ---------------------------------------------------------------------------
# Live tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.live
@pytest.mark.skipif(not IS_LIVE, reason="live mode only")
async def test_live_hitl_submit_and_approve():
    """Live: submit approval to real Firestore, approve, verify state."""
    from agents.response.agent import HITLQueue

    queue = HITLQueue(partner_project_id=SYNTHETIC["partner_project_id"])
    approval_id = None

    try:
        approval_id = queue.submit_approval_request(
            client_id=SYNTHETIC["client_id_a"],
            case_id=f"{SYNTHETIC['case_id']}-live",
            agent_name="response_agent_live_test",
            proposed_action={
                "proposed_action": "isolate_endpoint",
                "parameters": {"hostname": SYNTHETIC["hostname"]},
            },
            triage_summary="Live integration test — ransomware simulation",
        )

        status = queue.get_approval_status(approval_id)
        assert status["status"] == "PENDING"

    finally:
        # Cleanup: delete test document
        if approval_id:
            from google.cloud import firestore

            db = firestore.Client(project=SYNTHETIC["partner_project_id"])
            db.collection("hitl_approvals").document(approval_id).delete()
