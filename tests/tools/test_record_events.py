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

import record_events  # noqa: E402
import writer  # noqa: E402
from record_events import compute_tool_stats, validate_record, warn_vocabulary_drift  # noqa: E402

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


# ---------------------------------------------------------------------------
# TCK-20260719-COST-PROXY-WRITE-PATH — deterministic tool_call_count/cost_proxy_score,
# computed here from real tools.jsonl ground truth, never trusting a caller-supplied value.
# ---------------------------------------------------------------------------

def _write_tools_jsonl(tmp_path, rows):
    tools_dir = tmp_path / "agent-monitoring"
    tools_dir.mkdir(parents=True, exist_ok=True)
    with open(tools_dir / "tools.jsonl", "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_cost_proxy_score_and_tool_call_count_computed_from_real_tools_jsonl_not_passthrough(tmp_path):
    # A caller-supplied cost_proxy_score/tool_call_count must be IGNORED and overridden by the
    # real computed value — this is the exact anti-pattern (trusting an LLM-transcribed number)
    # this ticket fixes. Two Bash rows (500ms + 1500ms) and one Read row for seq=1 give a known,
    # hand-computable expected score: W_BASH=0.001 * 2000 + W_EDIT=1 * 1 = 3.0, tool_call_count=3.
    _write_tools_jsonl(tmp_path, [
        {"run_id": "TCK-COST-PROXY-TEST", "seq": 1, "tool": "Bash", "duration_ms": 500},
        {"run_id": "TCK-COST-PROXY-TEST", "seq": 1, "tool": "Bash", "duration_ms": 1500},
        {"run_id": "TCK-COST-PROXY-TEST", "seq": 1, "tool": "Read", "duration_ms": 10},
        {"run_id": "TCK-COST-PROXY-TEST", "seq": 2, "tool": "Bash", "duration_ms": 999},  # different seq, must not leak in
    ])
    record = {
        **_VALID_EVENT,
        "run_id": "TCK-COST-PROXY-TEST",
        "seq": 1,
        "cost_proxy_score": 999999.0,  # deliberately wrong caller-supplied value
        "tool_call_count": 999999,
    }
    assert validate_record(record) == []

    result = subprocess.run(
        [sys.executable, str(_RECORD_PATH), "--data", json.dumps(record)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0
    written = json.loads((tmp_path / "agent-monitoring" / "events.jsonl").read_text().strip())
    assert written["cost_proxy_score"] == 3.0
    assert written["tool_call_count"] == 3


def test_cost_proxy_score_absent_when_no_tools_jsonl_exists(tmp_path):
    # No agent-monitoring/tools.jsonl at all in this cwd — compute_tool_stats must not crash,
    # and an implement-ticket record with genuinely zero recorded tool calls gets 0, not a stale
    # caller-supplied value.
    record = {**_VALID_EVENT, "run_id": "TCK-NO-TOOLS-FILE", "seq": 1}
    result = subprocess.run(
        [sys.executable, str(_RECORD_PATH), "--data", json.dumps(record)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0
    written = json.loads((tmp_path / "agent-monitoring" / "events.jsonl").read_text().strip())
    assert written["cost_proxy_score"] == 0.0
    assert written["tool_call_count"] == 0


def test_implement_epic_and_create_tickets_records_unaffected_no_sidecar():
    # implement-epic ("EPIC-"/"FOLDER-" run_id prefix) and create-tickets ("CREATE-TICKETS-"
    # prefix) never register a per-agent-call sidecar — compute_tool_stats must leave their
    # records exactly as passed through, never adding a tool_call_count/cost_proxy_score key
    # that wasn't already there (matches this ticket's explicit Out-of-Scope: "100% missing for
    # both fields by documented, deliberate design").
    records = [
        {**_VALID_EVENT, "run_id": "EPIC-TCK-FAKE-EPIC", "seq": 1},
        {**_VALID_EVENT, "run_id": "FOLDER-tickets-todos-fake", "seq": 1},
        {**_VALID_EVENT, "run_id": "CREATE-TICKETS-fake-source", "seq": 1},
    ]
    stats = compute_tool_stats(records)
    assert stats == {}


def test_compute_tool_stats_only_targets_implement_ticket_workflow(tmp_path, monkeypatch):
    # A mixed batch: one implement-ticket record (gets computed) and one implement-epic record
    # (must not appear in the result at all, even though tools.jsonl has no rows for it either).
    monkeypatch.chdir(tmp_path)
    _write_tools_jsonl(tmp_path, [
        {"run_id": "TCK-MIXED-BATCH", "seq": 1, "tool": "Read", "duration_ms": 5},
    ])
    records = [
        {**_VALID_EVENT, "run_id": "TCK-MIXED-BATCH", "seq": 1},
        {**_VALID_EVENT, "run_id": "EPIC-TCK-MIXED-BATCH", "seq": 1},
    ]
    stats = compute_tool_stats(records)
    assert stats == {("TCK-MIXED-BATCH", 1): (1, 1.0)}


# ---------------------------------------------------------------------------
# TCK-20260721-MONITORING-WRITER-UNIFICATION — shared writer migration
# ---------------------------------------------------------------------------


def test_execution_identity_fields_pass_through_unchanged(tmp_path):
    record = {
        **_VALID_EVENT,
        "execution_id": "claude-TCK-FAKE-RUN-1234567890-abcd1234",
        "provider": "claude",
        "ticket_id": "TCK-FAKE-RUN",
    }
    result = subprocess.run(
        [sys.executable, str(_RECORD_PATH), "--data", json.dumps([record])],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    written = json.loads((tmp_path / "agent-monitoring" / "events.jsonl").read_text().strip())
    assert written["execution_id"] == "claude-TCK-FAKE-RUN-1234567890-abcd1234"
    assert written["provider"] == "claude"
    assert written["ticket_id"] == "TCK-FAKE-RUN"


def test_append_failure_is_non_blocking(tmp_path, monkeypatch, capsys):
    # An append-layer failure (post-validation) must not sys.exit(1) — reserved
    # for validation failures, which happen before write_lines is ever called.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(record_events, "write_lines", lambda *a, **kw: False)
    monkeypatch.setattr(sys, "argv", ["record_events.py", "--data", json.dumps([dict(_VALID_EVENT)])])

    record_events.main()  # must not raise SystemExit

    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "DONE:" in captured.out


def test_batch_write_holds_contiguous_lines_under_concurrent_writer(tmp_path):
    # write_lines holds one lock acquisition for the whole batch, so a batch's
    # own N lines cannot be interleaved by a concurrent single-line writer —
    # this is a property enforced structurally by the lock, verified here by
    # racing record_events.py's own batch write against direct writer.write_line
    # calls targeting the same file.
    import threading

    events_file = tmp_path / "agent-monitoring" / "events.jsonl"
    events_file.parent.mkdir(parents=True, exist_ok=True)

    batch_size = 5
    batch = [
        {**_VALID_EVENT, "run_id": "TCK-BATCH-CONTIG-TEST", "seq": i, "summary": f"batch-{i}"}
        for i in range(batch_size)
    ]

    proc = subprocess.Popen(
        [sys.executable, str(_RECORD_PATH), "--data", json.dumps(batch)],
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    stop_flag = threading.Event()

    def _single_writer():
        i = 0
        while not stop_flag.is_set() and i < 500:
            writer.write_line(events_file, json.dumps({"run_id": "single-writer", "marker": f"single-{i}"}))
            i += 1

    t = threading.Thread(target=_single_writer)
    t.start()
    proc.wait(timeout=10)
    stop_flag.set()
    t.join(timeout=10)

    assert proc.returncode == 0, proc.stderr.read()

    records = [json.loads(line) for line in events_file.read_text().splitlines()]
    batch_indices = [i for i, r in enumerate(records) if r.get("run_id") == "TCK-BATCH-CONTIG-TEST"]
    assert len(batch_indices) == batch_size
    assert batch_indices == list(range(batch_indices[0], batch_indices[0] + batch_size))
