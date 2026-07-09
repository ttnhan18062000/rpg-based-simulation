"""Tests for tools/agent-monitoring/record_events.py's non-null required-field
enforcement, ordering-safe summary truncation, and warn-only phase/agent
vocabulary check (TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT).

All subprocess-level tests here use only rejected (null-field) or non-writing
inputs, or run against tmp-cwd copies, so none of them write to the repo's real
agent-monitoring/events.jsonl.
"""
import json
import subprocess
import sys
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from record_events import validate_record, warn_vocabulary_drift  # noqa: E402

_RECORD_PATH = _MONITORING_TOOLS_DIR / "record_events.py"

_VALID_EVENT = {
    "run_id": "TCK-FAKE-RUN",
    "seq": 1,
    "ts": "2026-07-08T00:00:00Z",
    "phase": "Investigate",
    "agent": "investigator",
    "summary": "did a thing",
    "status": "ok",
}


# ---------------------------------------------------------------------------
# Step 2 — non-null enforcement + ordering-safe summary truncation
# ---------------------------------------------------------------------------

def test_valid_event_has_no_errors():
    assert validate_record(dict(_VALID_EVENT)) == []


def test_missing_key_rejected():
    record = dict(_VALID_EVENT)
    del record["phase"]
    errors = validate_record(record)
    assert any("missing fields" in e and "phase" in e for e in errors)


def test_null_required_field_rejected_identically_to_missing_key():
    record = dict(_VALID_EVENT)
    record["phase"] = None
    errors = validate_record(record)
    missing_errors = [e for e in errors if "missing fields" in e]
    assert missing_errors and "phase" in missing_errors[0]


def test_null_agent_rejected():
    record = dict(_VALID_EVENT)
    record["agent"] = None
    errors = validate_record(record)
    assert any("agent" in e for e in errors if "missing fields" in e)


def test_null_summary_does_not_crash_and_is_reported():
    record = dict(_VALID_EVENT)
    record["summary"] = None
    # validate_record itself must not raise, and must flag summary as missing.
    errors = validate_record(record)
    assert any("summary" in e for e in errors if "missing fields" in e)


class TestExitCodeContract:
    def _run(self, data):
        return subprocess.run(
            [sys.executable, str(_RECORD_PATH), "--data", json.dumps(data)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

    def test_exit_1_on_null_required_field(self):
        result = self._run({**_VALID_EVENT, "phase": None})
        assert result.returncode == 1
        assert "phase" in result.stderr

    def test_null_summary_produces_clean_error_not_typeerror(self):
        result = self._run({**_VALID_EVENT, "summary": None})
        assert result.returncode == 1
        assert "TypeError" not in result.stderr
        assert "ERROR" in result.stderr

    def test_exit_1_matches_missing_key_exit_code(self):
        record = dict(_VALID_EVENT)
        del record["phase"]
        missing_key_result = self._run(record)
        null_result = self._run({**_VALID_EVENT, "phase": None})
        assert missing_key_result.returncode == null_result.returncode == 1


# ---------------------------------------------------------------------------
# Step 4 — warn-only phase/agent vocabulary check
# ---------------------------------------------------------------------------

class TestVocabularyWarning:
    def test_unrecognized_phase_warns(self, capsys):
        record = {**_VALID_EVENT, "run_id": "TCK-FAKE-RUN", "phase": "NotARealPhase"}
        warn_vocabulary_drift(record)
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "NotARealPhase" in captured.err

    def test_canonical_phase_for_known_workflow_does_not_warn(self, capsys):
        record = {**_VALID_EVENT, "run_id": "TCK-FAKE-RUN", "phase": "Investigate", "agent": "investigator"}
        warn_vocabulary_drift(record)
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_orchestrator_pseudo_agent_workflow_never_warns(self, capsys):
        record = {**_VALID_EVENT, "run_id": "SIMQ-AUDIT-20260708T000000Z", "phase": "Recalibrate", "agent": "workflow"}
        warn_vocabulary_drift(record)
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_orchestrator_pseudo_agent_implement_ticket_never_warns(self, capsys):
        record = {**_VALID_EVENT, "run_id": "TCK-FAKE-RUN", "phase": "Test", "agent": "implement-ticket-orchestrator"}
        warn_vocabulary_drift(record)
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_create_tickets_dynamic_investigate_prefix_never_warns(self, capsys):
        record = {
            **_VALID_EVENT,
            "run_id": "CREATE-TICKETS-some-source",
            "phase": "Investigate",
            "agent": "investigate:concern-3",
        }
        warn_vocabulary_drift(record)
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_unknown_workflow_prefix_does_not_crash_or_warn(self, capsys):
        record = {**_VALID_EVENT, "run_id": "UNKNOWN-PREFIX-123", "phase": "AnythingGoes", "agent": "anyone"}
        warn_vocabulary_drift(record)
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_vocabulary_warning_never_raises_or_exits(self, tmp_path):
        # Exercises the full CLI path: an unrecognized phase must still exit 0
        # and still write the record — warn, never reject. Runs with cwd=tmp_path
        # so the relative "agent-monitoring/events.jsonl" write target lands in a
        # throwaway directory, never touching the repo's real events.jsonl.
        result = subprocess.run(
            [sys.executable, str(_RECORD_PATH), "--data", json.dumps({
                **_VALID_EVENT,
                "run_id": "TCK-VOCAB-WARN-TEST",
                "phase": "TotallyMadeUpPhase",
            })],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0
        assert "WARNING" in result.stderr
        assert "TotallyMadeUpPhase" in result.stderr
        written = (tmp_path / "agent-monitoring" / "events.jsonl").read_text()
        assert "TCK-VOCAB-WARN-TEST" in written
