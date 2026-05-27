"""Tests for the alert deduplication module (Firestore-backed)."""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from agents.dedup import AlertDeduplicator


def _make_dedup_with_store(ttl_seconds=60):
    """Create an AlertDeduplicator backed by a simple in-memory fake Firestore."""
    store: dict = {}

    with patch("agents.dedup.firestore") as mock_fs:
        mock_db = MagicMock()
        mock_fs.Client.return_value = mock_db

        def fake_document(key):
            doc_mock = MagicMock()

            def fake_set(data):
                store[key] = data

            def fake_get():
                m = MagicMock()
                if key in store:
                    m.exists = True
                    m.to_dict.return_value = store[key]
                else:
                    m.exists = False
                return m

            doc_mock.set.side_effect = fake_set
            doc_mock.get.side_effect = fake_get
            return doc_mock

        mock_db.collection.return_value.document.side_effect = fake_document
        dedup = AlertDeduplicator(partner_project_id="test-project", ttl_seconds=ttl_seconds)

    return dedup, store


@patch("agents.dedup.firestore")
def test_first_alert_not_duplicate(mock_fs):
    mock_db = MagicMock()
    mock_fs.Client.return_value = mock_db
    mock_doc = MagicMock()
    mock_doc.exists = False
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

    dedup = AlertDeduplicator(partner_project_id="test-project", ttl_seconds=60)
    assert dedup.is_duplicate("client-a", "PHISHING", "case-1") is False


@patch("agents.dedup.firestore")
def test_recorded_alert_is_duplicate(mock_fs):
    mock_db = MagicMock()
    mock_fs.Client.return_value = mock_db
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        "result": {"result": "FP"},
    }
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

    dedup = AlertDeduplicator(partner_project_id="test-project", ttl_seconds=60)
    dedup.record("client-a", "PHISHING", "case-1", {"result": "FP"})
    assert dedup.is_duplicate("client-a", "PHISHING", "case-1") is True


@patch("agents.dedup.firestore")
def test_different_alert_not_duplicate(mock_fs):
    mock_db = MagicMock()
    mock_fs.Client.return_value = mock_db

    # All lookups return no doc (different keys = different alerts = not duplicates)
    mock_doc = MagicMock()
    mock_doc.exists = False
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

    dedup = AlertDeduplicator(partner_project_id="test-project", ttl_seconds=60)
    assert dedup.is_duplicate("client-a", "MALWARE", "case-1") is False
    assert dedup.is_duplicate("client-b", "PHISHING", "case-1") is False
    assert dedup.is_duplicate("client-a", "PHISHING", "case-2") is False


@patch("agents.dedup.firestore")
def test_ttl_expiry(mock_fs):
    mock_db = MagicMock()
    mock_fs.Client.return_value = mock_db
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "expires_at": (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
        "result": None,
    }
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

    dedup = AlertDeduplicator(partner_project_id="test-project", ttl_seconds=1)
    # Record exists but is expired
    assert dedup.is_duplicate("client-a", "PHISHING", "case-1") is False


@patch("agents.dedup.firestore")
def test_get_previous_result(mock_fs):
    mock_db = MagicMock()
    mock_fs.Client.return_value = mock_db
    result = {"verdict": "TRUE_POSITIVE", "severity": "HIGH"}
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        "result": result,
    }
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

    dedup = AlertDeduplicator(partner_project_id="test-project", ttl_seconds=60)
    assert dedup.get_previous_result("client-a", "MALWARE", "case-5") == result


@patch("agents.dedup.firestore")
def test_get_previous_result_missing(mock_fs):
    mock_db = MagicMock()
    mock_fs.Client.return_value = mock_db
    mock_doc = MagicMock()
    mock_doc.exists = False
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

    dedup = AlertDeduplicator(partner_project_id="test-project", ttl_seconds=60)
    assert dedup.get_previous_result("client-a", "PHISHING", "case-99") is None


def test_deterministic_key():
    """Same inputs always produce the same key."""
    key1 = AlertDeduplicator._make_key("client-a", "PHISHING", "case-1")
    key2 = AlertDeduplicator._make_key("client-a", "PHISHING", "case-1")
    assert key1 == key2
    assert len(key1) == 24


@patch("agents.dedup.firestore")
def test_record_without_result(mock_fs):
    mock_db = MagicMock()
    mock_fs.Client.return_value = mock_db
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        "result": None,
    }
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

    dedup = AlertDeduplicator(partner_project_id="test-project", ttl_seconds=60)
    dedup.record("c", "t", "case-1")  # no result dict
    assert dedup.is_duplicate("c", "t", "case-1") is True
    assert dedup.get_previous_result("c", "t", "case-1") is None


@patch("agents.dedup.firestore")
def test_firestore_client_unavailable_fail_open(mock_fs):
    """If Firestore client init fails, deduplicator fails open (no dedup)."""
    mock_fs.Client.side_effect = Exception("No credentials")

    dedup = AlertDeduplicator(partner_project_id="test-project", ttl_seconds=60)
    # Should not raise, should fail open
    assert dedup.is_duplicate("c", "t", "case-1") is False
    dedup.record("c", "t", "case-1")  # no-op, no raise
    assert dedup.get_previous_result("c", "t", "case-1") is None
