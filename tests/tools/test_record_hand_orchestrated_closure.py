"""Tests for tools/agent-monitoring/record_hand_orchestrated_closure.py
(TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE,
TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP).

Covers the pure build_records() expansion function directly and the CLI's real write behavior via
subprocess with an isolated cwd, mirroring test_record_run.py's/test_record_events.py's own
established pattern for these sibling tools.
"""
import csv
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

_TITLE_ARGS = ["--title", "Fake ticket title", "--log-summary", "Fake one-sentence summary."]

_WORKING_LOG_HEADER = "timestamp,ticket_id,title,status,summary,artifacts_path\n"


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
            ["--ticket-id", "TCK-FAKE-CLI", "--tier", "hotfix", "--events", json.dumps(_MINIMAL_EVENTS), *_TITLE_ARGS],
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
            ["--ticket-id", "TCK-FAKE-CLI", "--tier", "not_a_real_tier", "--events", json.dumps(_MINIMAL_EVENTS), *_TITLE_ARGS],
            tmp_path,
        )
        assert result.returncode != 0
        assert "invalid choice" in result.stderr

    def test_event_missing_required_field_rejected(self, tmp_path):
        bad_events = [{"phase": "Scope", "status": "ok"}]  # missing "summary"
        result = self._run(
            ["--ticket-id", "TCK-FAKE-CLI", "--tier", "hotfix", "--events", json.dumps(bad_events), *_TITLE_ARGS],
            tmp_path,
        )
        assert result.returncode == 1
        assert "missing required fields" in result.stderr
        assert not (tmp_path / "agent-monitoring").exists()

    def test_empty_events_array_rejected(self, tmp_path):
        result = self._run(
            ["--ticket-id", "TCK-FAKE-CLI", "--tier", "hotfix", "--events", "[]", *_TITLE_ARGS],
            tmp_path,
        )
        assert result.returncode == 1
        assert "non-empty" in result.stderr

    def test_final_status_and_workflow_are_overridable(self, tmp_path):
        result = self._run(
            [
                "--ticket-id", "TCK-FAKE-CLI", "--tier", "epic", "--events", json.dumps(_MINIMAL_EVENTS),
                "--final-status", "NEEDS_HUMAN_INPUT", "--workflow", "implement-epic", *_TITLE_ARGS,
            ],
            tmp_path,
        )
        assert result.returncode == 0, result.stderr
        iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
        runs_file = tmp_path / "agent-monitoring" / "data" / iso_week / "runs.jsonl"
        run_record = json.loads(runs_file.read_text().strip())
        assert run_record["final_status"] == "NEEDS_HUMAN_INPUT"
        assert run_record["workflow"] == "implement-epic"


class TestUnattributedStatsAreOmittedNotZero:
    """TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP: a hand-orchestrating session
    never has a live per-phase sidecar during the real work, so an unattributed phase must get
    no tool_call_count/cost_proxy_score keys at all -- never a false (0, 0.0)."""

    def _run(self, args, tmp_path):
        return subprocess.run(
            [sys.executable, str(_RECORD_PATH), *args],
            capture_output=True, text=True, cwd=tmp_path,
        )

    def test_no_matching_tools_jsonl_rows_omits_stats_keys_entirely(self, tmp_path):
        result = self._run(
            ["--ticket-id", "TCK-NO-SIDECAR-CLI", "--tier", "hotfix",
             "--events", json.dumps(_MINIMAL_EVENTS), *_TITLE_ARGS],
            tmp_path,
        )
        assert result.returncode == 0, result.stderr
        iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
        events_file = tmp_path / "agent-monitoring" / "data" / iso_week / "events.jsonl"
        event_lines = [json.loads(l) for l in events_file.read_text().strip().splitlines()]
        for event in event_lines:
            assert "tool_call_count" not in event
            assert "cost_proxy_score" not in event

    def test_real_attributed_rows_still_computed_correctly(self, tmp_path):
        # A mixed case: seq=1 has real tools.jsonl rows (e.g. a session that partially used the
        # live workflow before finishing via hand-orchestration); seq=2 has none.
        iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
        week_dir = tmp_path / "agent-monitoring" / "data" / iso_week
        week_dir.mkdir(parents=True, exist_ok=True)
        with open(week_dir / "tools.jsonl", "w") as f:
            f.write(json.dumps({"run_id": "TCK-MIXED-CLI", "seq": 1, "tool": "Read", "duration_ms": 5}) + "\n")

        events = [
            {"phase": "Scope", "status": "ok", "summary": "Scoped"},
            {"phase": "Implement", "status": "ok", "summary": "Implemented"},
        ]
        result = self._run(
            ["--ticket-id", "TCK-MIXED-CLI", "--tier", "hotfix", "--events", json.dumps(events), *_TITLE_ARGS],
            tmp_path,
        )
        assert result.returncode == 0, result.stderr
        events_file = tmp_path / "agent-monitoring" / "data" / iso_week / "events.jsonl"
        event_lines = [json.loads(l) for l in events_file.read_text().strip().splitlines()]
        seq1, seq2 = event_lines[0], event_lines[1]
        assert seq1["tool_call_count"] == 1
        assert "tool_call_count" not in seq2
        assert "cost_proxy_score" not in seq2


class TestWorkingLogCsvAppended:
    """TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP: the wrapper must append its own
    tickets/working_log.csv row -- previously never written at all for this call path."""

    def _run(self, args, tmp_path):
        return subprocess.run(
            [sys.executable, str(_RECORD_PATH), *args],
            capture_output=True, text=True, cwd=tmp_path,
        )

    def _seed_working_log(self, tmp_path):
        log_path = tmp_path / "tickets" / "working_log.csv"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(_WORKING_LOG_HEADER)
        return log_path

    def test_appends_one_row_with_correct_columns(self, tmp_path):
        log_path = self._seed_working_log(tmp_path)
        result = self._run(
            ["--ticket-id", "TCK-LOG-TEST", "--tier", "hotfix", "--events", json.dumps(_MINIMAL_EVENTS),
             "--title", "A test ticket", "--log-summary", "Did the test thing."],
            tmp_path,
        )
        assert result.returncode == 0, result.stderr
        rows = list(csv.reader(log_path.read_text().splitlines()))
        assert rows[0] == ["timestamp", "ticket_id", "title", "status", "summary", "artifacts_path"]
        assert len(rows) == 2
        _, ticket_id, title, status, summary, artifacts_path = rows[1]
        assert ticket_id == "TCK-LOG-TEST"
        assert title == "A test ticket"
        assert status == "DONE"
        assert summary == "Did the test thing."
        assert artifacts_path == "none (hotfix — no staging artifacts)"

    def test_artifacts_path_defaults_to_stored_artifacts_for_standard_tier(self, tmp_path):
        log_path = self._seed_working_log(tmp_path)
        result = self._run(
            ["--ticket-id", "TCK-LOG-STANDARD", "--tier", "standard", "--events", json.dumps(_MINIMAL_EVENTS),
             *_TITLE_ARGS],
            tmp_path,
        )
        assert result.returncode == 0, result.stderr
        rows = list(csv.reader(log_path.read_text().splitlines()))
        assert rows[1][5] == "stored_artifacts/TCK-LOG-STANDARD"

    def test_explicit_artifacts_path_overrides_default(self, tmp_path):
        log_path = self._seed_working_log(tmp_path)
        result = self._run(
            ["--ticket-id", "TCK-LOG-EXPLICIT", "--tier", "hotfix", "--events", json.dumps(_MINIMAL_EVENTS),
             *_TITLE_ARGS, "--artifacts-path", "custom/path"],
            tmp_path,
        )
        assert result.returncode == 0, result.stderr
        rows = list(csv.reader(log_path.read_text().splitlines()))
        assert rows[1][5] == "custom/path"

    def test_embedded_comma_in_summary_round_trips_correctly(self, tmp_path):
        log_path = self._seed_working_log(tmp_path)
        result = self._run(
            ["--ticket-id", "TCK-LOG-COMMA", "--tier", "hotfix", "--events", json.dumps(_MINIMAL_EVENTS),
             "--title", "A title", "--log-summary", "Fixed the bug, added tests, updated docs."],
            tmp_path,
        )
        assert result.returncode == 0, result.stderr
        rows = list(csv.reader(log_path.read_text().splitlines()))
        assert rows[1][4] == "Fixed the bug, added tests, updated docs."

    def test_missing_title_rejected_with_no_partial_write(self, tmp_path):
        self._seed_working_log(tmp_path)
        result = self._run(
            ["--ticket-id", "TCK-LOG-NOTITLE", "--tier", "hotfix", "--events", json.dumps(_MINIMAL_EVENTS),
             "--log-summary", "x"],
            tmp_path,
        )
        assert result.returncode != 0
        assert not (tmp_path / "agent-monitoring").exists()

    def test_missing_working_log_parent_dir_warns_but_does_not_fail_the_run(self, tmp_path):
        # No tickets/ dir at all in this isolated cwd -- monitoring writes must never fail the
        # workflow (CLAUDE.md Hard Rule), so the run/event write still succeeds.
        result = self._run(
            ["--ticket-id", "TCK-LOG-NODIR", "--tier", "hotfix", "--events", json.dumps(_MINIMAL_EVENTS),
             *_TITLE_ARGS],
            tmp_path,
        )
        assert result.returncode == 0, result.stderr
        assert "working_log.csv" in result.stderr
        iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
        assert (tmp_path / "agent-monitoring" / "data" / iso_week / "runs.jsonl").exists()
