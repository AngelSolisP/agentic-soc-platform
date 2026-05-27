"""Tests for Firestore-backed alert deduplication."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta


class TestAlertDeduplicator:
    """Deduplication via Firestore collection."""

    @patch("agents.dedup.firestore")
    def test_not_duplicate_when_no_doc(self, mock_fs):
        from agents.dedup import AlertDeduplicator

        mock_db = MagicMock()
        mock_fs.Client.return_value = mock_db
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        dedup = AlertDeduplicator(partner_project_id="test-project")
        assert dedup.is_duplicate("acme", "MALWARE", "CASE-1") is False

    @patch("agents.dedup.firestore")
    def test_is_duplicate_when_not_expired(self, mock_fs):
        from agents.dedup import AlertDeduplicator

        mock_db = MagicMock()
        mock_fs.Client.return_value = mock_db
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            "result": {"status": "CLOSED_FP"},
        }
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        dedup = AlertDeduplicator(partner_project_id="test-project")
        assert dedup.is_duplicate("acme", "MALWARE", "CASE-1") is True

    @patch("agents.dedup.firestore")
    def test_not_duplicate_when_expired(self, mock_fs):
        from agents.dedup import AlertDeduplicator

        mock_db = MagicMock()
        mock_fs.Client.return_value = mock_db
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
            "result": None,
        }
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        dedup = AlertDeduplicator(partner_project_id="test-project")
        assert dedup.is_duplicate("acme", "MALWARE", "CASE-1") is False

    @patch("agents.dedup.firestore")
    def test_record_writes_to_firestore(self, mock_fs):
        from agents.dedup import AlertDeduplicator

        mock_db = MagicMock()
        mock_fs.Client.return_value = mock_db

        dedup = AlertDeduplicator(partner_project_id="test-project")
        dedup.record("acme", "MALWARE", "CASE-1", result={"status": "ESCALATED"})

        mock_db.collection.return_value.document.return_value.set.assert_called_once()
        written = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert written["client_id"] == "acme"
        assert written["result"] == {"status": "ESCALATED"}
        assert "expires_at" in written

    @patch("agents.dedup.firestore")
    def test_get_previous_result(self, mock_fs):
        from agents.dedup import AlertDeduplicator

        mock_db = MagicMock()
        mock_fs.Client.return_value = mock_db
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
            "result": {"status": "CLOSED_FP"},
        }
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        dedup = AlertDeduplicator(partner_project_id="test-project")
        result = dedup.get_previous_result("acme", "MALWARE", "CASE-1")
        assert result == {"status": "CLOSED_FP"}

    @patch("agents.dedup.firestore")
    def test_firestore_failure_is_fail_open(self, mock_fs):
        from agents.dedup import AlertDeduplicator

        mock_db = MagicMock()
        mock_fs.Client.return_value = mock_db
        mock_db.collection.return_value.document.return_value.get.side_effect = Exception("Firestore down")

        dedup = AlertDeduplicator(partner_project_id="test-project")
        assert dedup.is_duplicate("acme", "MALWARE", "CASE-1") is False
