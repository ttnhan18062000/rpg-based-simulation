"""Tests for tools/agent-monitoring/validate.py's compute_drift_report (Step 5)
and the single-source-of-truth vocabulary wiring (Step 6),
TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT.

Constructs runs/events as plain Python dicts, mirroring
test_generate_retro.py's fixture-construction style — no file I/O, no
subprocess, pure-function testing.
"""
import sys
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import record_events  # noqa: E402
import validate  # noqa: E402
from validate import compute_drift_report, compute_tool_count_drift_report  # noqa: E402

_BASE_RUN = {
    "run_id": "TCK-FAKE",
    "start_ts": "2026-07-08T00:00:00Z",
    "end_ts": "2026-07-08T01:00:00Z",
    "workflow": "implement-ticket",
    "tier": "standard",
    "final_status": "DONE",
    "agent_count": 3,
    "duration_s": 3600,
}


# ---------------------------------------------------------------------------
# compute_drift_report
# ---------------------------------------------------------------------------

def test_drift_report_counts_null_required_fields():
    runs = [
        dict(_BASE_RUN, run_id="TCK-A", workflow=None),
        dict(_BASE_RUN, run_id="TCK-B", tier=None),
        dict(_BASE_RUN, run_id="TCK-C", final_status=None),
        dict(_BASE_RUN, run_id="TCK-D"),  # clean
    ]
    report = compute_drift_report(runs, [])

    assert "workflow: 1" in report
    assert "tier: 1" in report
    assert "final_status: 1" in report


def test_drift_report_frequency_table_non_canonical_phase_and_agent():
    runs = [dict(_BASE_RUN)]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "ts": "t", "phase": "Investigate", "agent": "investigator", "status": "ok", "summary": "ok"},
        {"run_id": "TCK-FAKE", "seq": 2, "ts": "t", "phase": "investigate", "agent": "investigator", "status": "ok", "summary": "ok"},
        {"run_id": "TCK-FAKE", "seq": 3, "ts": "t", "phase": "investigate", "agent": "some-rando-agent", "status": "ok", "summary": "ok"},
    ]
    report = compute_drift_report(runs, events)

    assert "'investigate': 2" in report
    assert "'some-rando-agent': 1" in report


def test_drift_report_frequency_table_non_canonical_tier():
    runs = [dict(_BASE_RUN, run_id="TCK-A", tier="epic-batch"), dict(_BASE_RUN, run_id="TCK-B", tier="epic-batch")]
    report = compute_drift_report(runs, [])

    assert "'epic-batch': 2" in report


def test_drift_report_skips_events_with_unrecognized_workflow_prefix():
    runs = [dict(_BASE_RUN)]
    events = [
        {"run_id": "UNKNOWN-PREFIX-1", "seq": 1, "ts": "t", "phase": "WhoKnows", "agent": "whoever", "status": "ok", "summary": "ok"},
    ]
    report = compute_drift_report(runs, events)

    assert "'WhoKnows'" not in report
    assert "'whoever'" not in report


def test_drift_report_shows_zero_counts_not_omitted_section_when_clean():
    runs = [dict(_BASE_RUN)]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "ts": "t", "phase": "Scope", "agent": "ticket-scoper", "status": "ok", "summary": "ok"},
    ]
    report = compute_drift_report(runs, events)

    assert "workflow: 0" in report
    assert "tier: 0" in report
    assert "final_status: 0" in report
    assert "Non-canonical phase values (events.jsonl):" in report
    assert "Non-canonical agent values (events.jsonl):" in report
    assert "Non-canonical tier values (runs.jsonl):" in report


def test_drift_report_is_read_only(tmp_path, monkeypatch):
    # compute_drift_report must never write to runs.jsonl/events.jsonl — it only
    # reads whatever lists it's handed and returns a string.
    monkeypatch.chdir(tmp_path)
    runs = [dict(_BASE_RUN, workflow=None)]
    events = [{"run_id": "TCK-FAKE", "seq": 1, "ts": "t", "phase": "weird", "agent": "weird", "status": "ok", "summary": "ok"}]
    compute_drift_report(runs, events)

    assert not (tmp_path / "agent-monitoring").exists()


# ---------------------------------------------------------------------------
# compute_tool_count_drift_report (TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION)
# ---------------------------------------------------------------------------

def _tool_row(run_id, seq, tool="Read"):
    return {"run_id": run_id, "seq": seq, "ts": "t", "tool": tool, "input_summary": "x", "status": "ok", "duration_ms": 1}


def _event_with_count(run_id, seq, tool_call_count):
    return {"run_id": run_id, "seq": seq, "ts": "t", "phase": "Implement", "agent": "implementer",
            "status": "ok", "summary": "ok", "tool_call_count": tool_call_count}


def test_tool_count_drift_report_no_mismatch_when_counts_agree():
    events = [_event_with_count("TCK-A", 2, 3)]
    tools = [_tool_row("TCK-A", 2) for _ in range(3)]
    report = compute_tool_count_drift_report(events, tools)

    assert "Events checked (non-null tool_call_count, run_id+seq present): 1" in report
    assert "Mismatches (recorded != actual tools.jsonl row count): 0" in report


def test_tool_count_drift_report_detects_undercounted_mismatch():
    # Reproduces the real bug shape: recorded=0 but tools.jsonl actually has rows for that seq.
    events = [_event_with_count("TCK-B", 8, 0)]
    tools = [_tool_row("TCK-B", 8) for _ in range(34)]
    report = compute_tool_count_drift_report(events, tools)

    assert "Mismatches (recorded != actual tools.jsonl row count): 1" in report
    assert "TCK-B seq=8: recorded=0 actual=34" in report


def test_tool_count_drift_report_detects_overcounted_mismatch():
    # Reproduces the traced case shape: recorded=2 but tools.jsonl has zero rows for that seq
    # (the run's tool calls were actually attributed elsewhere, e.g. a stale sidecar).
    events = [_event_with_count("TCK-C", 1, 2)]
    tools = []
    report = compute_tool_count_drift_report(events, tools)

    assert "Mismatches (recorded != actual tools.jsonl row count): 1" in report
    assert "TCK-C seq=1: recorded=2 actual=0" in report


def test_tool_count_drift_report_skips_null_fields():
    # Events with no run_id/seq/tool_call_count (legacy shapes, or fields genuinely unset)
    # must not be counted as checked or mismatched.
    events = [
        {"run_id": None, "seq": 1, "ts": "t", "phase": "x", "agent": "x", "status": "ok", "summary": "s", "tool_call_count": 5},
        {"run_id": "TCK-D", "seq": None, "ts": "t", "phase": "x", "agent": "x", "status": "ok", "summary": "s", "tool_call_count": 5},
        {"run_id": "TCK-D", "seq": 1, "ts": "t", "phase": "x", "agent": "x", "status": "ok", "summary": "s", "tool_call_count": None},
    ]
    report = compute_tool_count_drift_report(events, [])

    assert "Events checked (non-null tool_call_count, run_id+seq present): 0" in report
    assert "Mismatches (recorded != actual tools.jsonl row count): 0" in report


def test_tool_count_drift_report_ignores_tools_rows_without_run_id_or_seq():
    # Interactive-use tool rows (run_id: null, seq: null) must not pollute any run's count.
    events = [_event_with_count("TCK-E", 3, 0)]
    tools = [
        {"run_id": None, "seq": None, "ts": "t", "tool": "Read", "input_summary": "x", "status": "ok", "duration_ms": 1},
    ]
    report = compute_tool_count_drift_report(events, tools)

    assert "Mismatches (recorded != actual tools.jsonl row count): 0" in report


def test_tool_count_drift_report_is_read_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    events = [_event_with_count("TCK-F", 1, 0)]
    tools = [_tool_row("TCK-F", 1)]
    compute_tool_count_drift_report(events, tools)

    assert not (tmp_path / "agent-monitoring").exists()


# ---------------------------------------------------------------------------
# Single-source-of-truth vocabulary wiring (Step 6)
# ---------------------------------------------------------------------------

def test_canonical_vocabulary_single_sourced():
    # record_events.py and validate.py must both import the same vocabulary
    # module object — not two independently-typed-out literal copies of the
    # same sets.
    assert record_events.WORKFLOW_PHASES is validate.WORKFLOW_PHASES
    assert record_events.infer_workflow is validate.infer_workflow
