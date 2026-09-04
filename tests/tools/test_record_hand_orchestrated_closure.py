"""Tests for tools/agent-monitoring/record_hand_orchestrated_closure.py
(TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE).

Covers the pure build_records() expansion function directly and the CLI's real write behavior via
subprocess with an isolated cwd, mirroring test_record_run.py's/test_record_events.py's own
established pattern for these sibling tools.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from record_hand_orchestrated_closure import build_records  # noqa: E402
from record_run import validate_record as validate_run_record  # noqa: E402
from record_events import validate_record as validate_event_record  # noqa: E402

_RECORD_PATH = _MONITORING_TOOLS_DIR / "record_hand_orchestrated_closure.py"

_MINIMAL_EVENTS = [
    {"phase": "Scope", "status": "ok", "summary": "Scoped the fix"},
    {"phase": "Implement", "status": "ok", "summary": "Applied the fix"},
    {"phase": "Verify", "status": "ok", "summary": "Confirmed tests pass"},
]


def test_build_records_shares_run_id_execution_id_provider_ticket_id_across_events():
    run_record, event_records = build_records(
        "TCK-FAKE", "hotfix", "DONE", _MINIMAL_EVENTS,
        None, None, "implement-ticket", "claude", "claude",
    )
    assert run_record["run_id"] == "TCK-FAKE"
    assert run_record["ticket_id"] == "TCK-FAKE"
    for record in event_records:
        assert record["run_id"] == "TCK-FAKE"
        assert record["ticket_id"] == "TCK-FAKE"
        assert record["execution_id"] == run_record["execution_id"]
        assert record["provider"] == "claude"


def test_build_records_assigns_sequential_1_indexed_seq_in_array_order():
    _, event_records = build_records(
        "TCK-FAKE", "hotfix", "DONE", _MINIMAL_EVENTS,
        None, None, "implement-ticket", "claude", "claude",
    )
    assert [r["seq"] for r in event_records] == [1, 2, 3]
    assert [r["phase"] for r in event_records] == ["Scope", "Implement", "Verify"]


def test_build_records_defaults_agent_but_respects_per_event_override():
    events = [
        {"phase": "Scope", "status": "ok", "summary": "x"},
        {"phase": "Implement", "status": "ok", "summary": "y", "agent": "implementer"},
    ]
    _, event_records = build_records(
        "TCK-FAKE", "hotfix", "DONE", events,
        None, None, "implement-ticket", "claude", "claude",
    )
    assert event_records[0]["agent"] == "claude"
    assert event_records[1]["agent"] == "implementer"


def test_build_records_agent_count_matches_event_count():
    run_record, event_records = build_records(
        "TCK-FAKE", "hotfix", "DONE", _MINIMAL_EVENTS,
        None, None, "implement-ticket", "claude", "claude",
    )
    assert run_record["agent_count"] == len(event_records) == 3


def test_build_records_start_end_ts_default_to_now_when_omitted():
    run_record, _ = build_records(
        "TCK-FAKE", "hotfix", "DONE", _MINIMAL_EVENTS,
        None, None, "implement-ticket", "claude", "claude",
    )
    assert run_record["start_ts"] == run_record["end_ts"]
    # Real ISO-8601 UTC, not a placeholder — must parse.
    datetime.fromisoformat(run_record["start_ts"].replace("Z", "+00:00"))


def test_build_records_explicit_start_end_ts_passed_through():
    run_record, _ = build_records(
        "TCK-FAKE", "hotfix", "DONE", _MINIMAL_EVENTS,
        "2026-09-04T10:00:00Z", "2026-09-04T10:05:00Z", "implement-ticket", "claude", "claude",
    )
    assert run_record["start_ts"] == "2026-09-04T10:00:00Z"
    assert run_record["end_ts"] == "2026-09-04T10:05:00Z"


def test_build_records_output_passes_the_real_underlying_validators():
    """The whole point of this wrapper is byte-compatible output with record_run.py/
    record_events.py's own contract — confirm both real validators accept it unchanged."""
    run_record, event_records = build_records(
        "TCK-FAKE", "hotfix", "DONE", _MINIMAL_EVENTS,
        None, None, "implement-ticket", "claude", "claude",
    )
    assert validate_run_record(run_record) == []
    for record in event_records:
        assert validate_event_record(record) == []


class TestCLIWritesRealRecords:
    def _run(self, args, tmp_path):
        return subprocess.run(
            [sys.executable, str(_RECORD_PATH), *args],
            capture_output=True, text=True, cwd=tmp_path,
        )

    def test_writes_one_run_and_n_event_records(self, tmp_path):
        result = self._run(
            ["--ticket-id", "TCK-FAKE-CLI", "--tier", "hotfix", "--events", json.dumps(_MINIMAL_EVENTS)],
            tmp_path,
        )
        assert result.returncode == 0, result.stderr

        iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
        runs_file = tmp_path / "agent-monitoring" / "data" / iso_week / "runs.jsonl"
        events_file = tmp_path / "agent-monitoring" / "data" / iso_week / "events.jsonl"

        run_record = json.loads(runs_file.read_text().strip())
        assert run_record["run_id"] == "TCK-FAKE-CLI"
        assert run_record["tier"] == "hotfix"
        assert run_record["final_status"] == "DONE"
        assert run_record["agent_count"] == 3

        event_lines = [json.loads(l) for l in events_file.read_text().strip().splitlines()]
        assert len(event_lines) == 3
        assert [e["seq"] for e in event_lines] == [1, 2, 3]

    def test_invalid_tier_rejected_by_argparse_choices(self, tmp_path):
        result = self._run(
            ["--ticket-id", "TCK-FAKE-CLI", "--tier", "not_a_real_tier", "--events", json.dumps(_MINIMAL_EVENTS)],
            tmp_path,
        )
        assert result.returncode != 0
        assert "invalid choice" in result.stderr

    def test_event_missing_required_field_rejected(self, tmp_path):
        bad_events = [{"phase": "Scope", "status": "ok"}]  # missing "summary"
        result = self._run(
            ["--ticket-id", "TCK-FAKE-CLI", "--tier", "hotfix", "--events", json.dumps(bad_events)],
            tmp_path,
        )
        assert result.returncode == 1
        assert "missing required fields" in result.stderr
        assert not (tmp_path / "agent-monitoring").exists()

    def test_empty_events_array_rejected(self, tmp_path):
        result = self._run(
            ["--ticket-id", "TCK-FAKE-CLI", "--tier", "hotfix", "--events", "[]"],
            tmp_path,
        )
        assert result.returncode == 1
        assert "non-empty" in result.stderr

    def test_final_status_and_workflow_are_overridable(self, tmp_path):
        result = self._run(
            [
                "--ticket-id", "TCK-FAKE-CLI", "--tier", "epic", "--events", json.dumps(_MINIMAL_EVENTS),
                "--final-status", "NEEDS_HUMAN_INPUT", "--workflow", "implement-epic",
            ],
            tmp_path,
        )
        assert result.returncode == 0, result.stderr
        iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
        runs_file = tmp_path / "agent-monitoring" / "data" / iso_week / "runs.jsonl"
        run_record = json.loads(runs_file.read_text().strip())
        assert run_record["final_status"] == "NEEDS_HUMAN_INPUT"
        assert run_record["workflow"] == "implement-epic"
