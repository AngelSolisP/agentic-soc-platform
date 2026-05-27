"""Tests for stage tracker error recording."""

from unittest.mock import patch, MagicMock


class TestStageTrackerErrors:
    """StageTracker should record errors when stages fail."""

    @patch("agents.stage_tracker.get_current_trace_id", return_value="abc123")
    def test_record_stage_with_error(self, mock_trace):
        from agents.stage_tracker import StageTracker

        tracker = StageTracker("test-project")
        mock_db = MagicMock()
        tracker._db = mock_db

        stage_id = tracker.record_stage(
            session_id="sess-1",
            case_id="CASE-1",
            client_id="acme",
            agent_key="triage",
            raw_output="Partial output before timeout",
            started_at=1000.0,
            completed_at=1005.0,
            error="TimeoutError: Agent execution exceeded 300s",
            error_severity="HIGH",
        )

        assert stage_id is not None
        doc = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert doc["error"] == "TimeoutError: Agent execution exceeded 300s"
        assert doc["error_severity"] == "HIGH"
        assert doc["status"] == "ERROR"

    @patch("agents.stage_tracker.get_current_trace_id", return_value=None)
    def test_record_stage_without_error(self, mock_trace):
        from agents.stage_tracker import StageTracker

        tracker = StageTracker("test-project")
        mock_db = MagicMock()
        tracker._db = mock_db

        tracker.record_stage(
            session_id="sess-1",
            case_id="CASE-1",
            client_id="acme",
            agent_key="enrichment",
            raw_output="IoCs enriched successfully",
            started_at=1000.0,
            completed_at=1003.0,
        )

        doc = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert doc["error"] is None
        assert doc["error_severity"] is None
        assert doc["status"] == "COMPLETED"

    @patch("agents.stage_tracker.get_current_trace_id", return_value=None)
    def test_record_pipeline_with_errors_dict(self, mock_trace):
        from agents.stage_tracker import StageTracker

        tracker = StageTracker("test-project")
        mock_db = MagicMock()
        tracker._db = mock_db

        agent_outputs = {
            "triage": {"texts": ["Triage complete"], "started": 100.0, "ended": 105.0},
            "enrichment": {"texts": ["Partial..."], "started": 105.0, "ended": 110.0},
        }
        errors = {
            "enrichment": {"error": "Timeout in enrichment", "severity": "HIGH"},
        }

        stage_ids = tracker.record_pipeline(
            session_id="sess-1",
            case_id="CASE-1",
            client_id="acme",
            agent_outputs=agent_outputs,
            errors=errors,
        )

        assert len(stage_ids) == 2
        calls = mock_db.collection.return_value.document.return_value.set.call_args_list

        # First call is triage (no error)
        triage_doc = calls[0][0][0]
        assert triage_doc["status"] == "COMPLETED"
        assert triage_doc["error"] is None

        # Second call is enrichment (with error)
        enrichment_doc = calls[1][0][0]
        assert enrichment_doc["status"] == "ERROR"
        assert enrichment_doc["error"] == "Timeout in enrichment"
        assert enrichment_doc["error_severity"] == "HIGH"

    @patch("agents.stage_tracker.get_current_trace_id", return_value=None)
    def test_record_pipeline_without_errors(self, mock_trace):
        """Backwards compatible: no errors param works fine."""
        from agents.stage_tracker import StageTracker

        tracker = StageTracker("test-project")
        mock_db = MagicMock()
        tracker._db = mock_db

        agent_outputs = {
            "triage": {"texts": ["Done"], "started": 100.0, "ended": 103.0},
        }

        stage_ids = tracker.record_pipeline(
            session_id="sess-1",
            case_id="CASE-1",
            client_id="acme",
            agent_outputs=agent_outputs,
        )

        assert len(stage_ids) == 1
        doc = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert doc["status"] == "COMPLETED"
        assert doc["error"] is None
