import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from workbench.backend.audit import AuditLogger, AuditAction


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def audit_logger(mock_db):
    return AuditLogger(mock_db)


def test_log_action(audit_logger, mock_db):
    audit_logger.log(
        actor="analyst@mssp.com",
        actor_type="analyst",
        action=AuditAction.CASE_APPROVED,
        client_id="client-a",
        case_id="case-123",
        details={"proposed_action": "isolate_host"},
    )

    mock_db.collection.assert_called_once_with("audit_log")
    call_args = mock_db.collection.return_value.add.call_args[0][0]
    assert call_args["actor"] == "analyst@mssp.com"
    assert call_args["action"] == "CASE_APPROVED"
    assert call_args["client_id"] == "client-a"
    assert call_args["case_id"] == "case-123"
    assert "timestamp" in call_args


def test_log_action_without_case(audit_logger, mock_db):
    audit_logger.log(
        actor="admin@mssp.com",
        actor_type="admin",
        action=AuditAction.CLIENT_CREATED,
        client_id="new-client",
        details={"display_name": "New Client"},
    )

    call_args = mock_db.collection.return_value.add.call_args[0][0]
    assert call_args["case_id"] is None
    assert call_args["action"] == "CLIENT_CREATED"


def test_audit_actions_enum():
    assert AuditAction.CASE_APPROVED == "CASE_APPROVED"
    assert AuditAction.CASE_REJECTED == "CASE_REJECTED"
    assert AuditAction.PIPELINE_TRIGGERED == "PIPELINE_TRIGGERED"
    assert AuditAction.CHAT_MESSAGE == "CHAT_MESSAGE"
    assert AuditAction.CLIENT_CREATED == "CLIENT_CREATED"
    assert AuditAction.CLIENT_UPDATED == "CLIENT_UPDATED"
    assert AuditAction.ANALYST_UPDATED == "ANALYST_UPDATED"


def test_log_failure_does_not_raise(audit_logger, mock_db):
    mock_db.collection.return_value.add.side_effect = Exception("Firestore down")
    audit_logger.log(
        actor="analyst@mssp.com",
        actor_type="analyst",
        action=AuditAction.CASE_APPROVED,
        client_id="client-a",
    )
