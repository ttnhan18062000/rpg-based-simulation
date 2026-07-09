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
from validate import compute_drift_report  # noqa: E402

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
# Single-source-of-truth vocabulary wiring (Step 6)
# ---------------------------------------------------------------------------

def test_canonical_vocabulary_single_sourced():
    # record_events.py and validate.py must both import the same vocabulary
    # module object — not two independently-typed-out literal copies of the
    # same sets.
    assert record_events.WORKFLOW_PHASES is validate.WORKFLOW_PHASES
    assert record_events.infer_workflow is validate.infer_workflow
