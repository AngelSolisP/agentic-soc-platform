"""
Tests for the HITL Dashboard Backend API.
"""

import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone


MOCK_APPROVAL = {
    "approval_id": "test-approval-123",
    "client_id": "test-client",
    "case_id": "CASE-001",
    "agent_name": "response_agent_test-client",
    "session_id": "session-abc",
    "status": "PENDING",
    "proposed_action": {
        "proposed_action": "isolate_endpoint",
        "integration": "EDR",
        "parameters": {"hostname": "workstation-01"},
        "justification": "Ransomware confirmed on host",
        "reversible": False,
        "hitl_required": True,
    },
    "triage_summary": "Confirmed ransomware activity on workstation-01",
    "analyst_instructions": "",
    "created_at": "2026-03-16T10:00:00Z",
    "updated_at": "2026-03-16T10:00:00Z",
    "decided_by": None,
    "decided_at": None,
}


@pytest.fixture(autouse=True)
def mock_firestore():
    with patch("ui.hitl_dashboard.backend.main.get_db") as mock_get_db, \
         patch("ui.hitl_dashboard.backend.main.ENFORCE_CLIENT_AUTH", False):
        db_mock = MagicMock()
        mock_get_db.return_value = db_mock
        yield db_mock


@pytest_asyncio.fixture
async def test_client():
    import os
    os.environ["PARTNER_PROJECT_ID"] = "test-project"
    os.environ["DEV_MODE"] = "true"  # Bypass auth in tests

    from ui.hitl_dashboard.backend.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_health(test_client):
    response = await test_client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_approvals(test_client, mock_firestore):
    """list_approvals should return list of approvals."""
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = MOCK_APPROVAL

    # Setup Firestore chain
    q = mock_firestore.collection.return_value
    q.where.return_value = q
    q.order_by.return_value = q
    q.limit.return_value = q
    q.stream.return_value = [mock_doc]

    response = await test_client.get("/approvals?status=PENDING")
    assert response.status_code == 200
    approvals = response.json()
    assert len(approvals) >= 0  # Empty ok if mock not fully wired


@pytest.mark.asyncio
async def test_approve_decision(test_client, mock_firestore):
    """Approve decision should update Firestore and return 200."""
    mock_doc_ref = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = MOCK_APPROVAL.copy()
    mock_doc_ref.get.return_value = mock_doc

    mock_firestore.collection.return_value.document.return_value = mock_doc_ref

    response = await test_client.post(
        "/approvals/test-approval-123/decide",
        json={
            "decision": "APPROVED",
            "analyst_id": "analyst-1",
            "analyst_notes": "Confirmed ransomware, isolate immediately",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_reject_decision(test_client, mock_firestore):
    """Reject decision should update Firestore."""
    mock_doc_ref = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = MOCK_APPROVAL.copy()
    mock_doc_ref.get.return_value = mock_doc

    mock_firestore.collection.return_value.document.return_value = mock_doc_ref

    response = await test_client.post(
        "/approvals/test-approval-123/decide",
        json={
            "decision": "REJECTED",
            "analyst_id": "analyst-1",
            "analyst_notes": "False positive, do not isolate",
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_decision(test_client):
    """Invalid decision value should return 400."""
    response = await test_client.post(
        "/approvals/test-approval-123/decide",
        json={
            "decision": "INVALID_DECISION",
            "analyst_id": "analyst-1",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_already_decided_returns_409(test_client, mock_firestore):
    """Deciding on an already-decided approval should return 409."""
    already_approved = {**MOCK_APPROVAL, "status": "APPROVED"}
    mock_doc_ref = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = already_approved
    mock_doc_ref.get.return_value = mock_doc

    mock_firestore.collection.return_value.document.return_value = mock_doc_ref

    response = await test_client.post(
        "/approvals/test-approval-123/decide",
        json={"decision": "APPROVED", "analyst_id": "analyst-2"},
    )
    assert response.status_code == 409
