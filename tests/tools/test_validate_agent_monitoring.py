"""Tests for tools/agent-monitoring/validate.py's compute_drift_report (Step 5)
and the single-source-of-truth vocabulary wiring (Step 6),
TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT.

Also covers the SQLite-index-backed read path migration,
TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE (see classes at the bottom of
this file): main() now sources runs/events/tools from
agent-monitoring-index/monitoring.db instead of direct JSONL reads, mirroring
tools/agent-monitoring/query.py's precedent (tests/tools/test_query.py).

Constructs runs/events as plain Python dicts, mirroring
test_generate_retro.py's fixture-construction style — no file I/O, no
subprocess, pure-function testing.
"""
import json
import sqlite3
import sys
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import pytest  # noqa: E402

import build_index  # noqa: E402
import record_events  # noqa: E402
import validate  # noqa: E402
from validate import (  # noqa: E402
    compute_drift_report,
    compute_multi_invocation_collision_report,
    compute_tool_count_drift_report,
)

_REPO_ROOT = Path(__file__).parent.parent.parent
_VALIDATE_MODULE_PATH = _MONITORING_TOOLS_DIR / "validate.py"
_FIXTURES_DIR = _REPO_ROOT / "tests" / "fixtures" / "agent_monitoring"

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
# compute_multi_invocation_collision_report (TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION)
# ---------------------------------------------------------------------------

def _scope_seq1(run_id):
    return {"run_id": run_id, "seq": 1, "ts": "t", "phase": "Scope", "agent": "ticket-scoper",
            "status": "ok", "summary": "ok"}


def test_multi_invocation_collision_report_detects_duplicate_scope_seq1():
    events = [
        _scope_seq1("TCK-COLLIDED"),
        _scope_seq1("TCK-COLLIDED"),
        _scope_seq1("TCK-NORMAL"),
    ]
    report = compute_multi_invocation_collision_report(events)

    assert "TCK-COLLIDED" in report
    assert "TCK-NORMAL" not in report


def test_multi_invocation_collision_report_is_read_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    events = [_scope_seq1("TCK-G"), _scope_seq1("TCK-G")]
    compute_multi_invocation_collision_report(events)

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


# ---------------------------------------------------------------------------
# SQLite-index-backed read path (TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE)
# ---------------------------------------------------------------------------

def _build_db(tmp_path, runs=None, events=None, tools=None):
    db_path = tmp_path / "monitoring.db"
    conn = sqlite3.connect(str(db_path))
    build_index._create_schema(conn)
    build_index._ingest_runs(conn, runs or [])
    build_index._ingest_events(conn, events or [])
    build_index._ingest_tools(conn, tools or [])
    conn.commit()
    conn.close()
    return db_path


def _load_fixture_jsonl(name):
    path = _FIXTURES_DIR / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


_RUN_SHAPE_FILES = [
    "shape1_started_finished_notes.jsonl",
    "shape2_final_status_no_end_ts.jsonl",
    "shape3_ts_start_ts_end_result.jsonl",
    "shape4_completed_at_status.jsonl",
    "shape5_folder_epic_bare_status.jsonl",
    "shape6_type_checker_exception.jsonl",
]
_EVENT_SHAPE_FILES = [
    "events_jsonl_reason_code_null.jsonl",
    "events_jsonl_tool_call_count_absent.jsonl",
]
_TOOLS_SHAPE_FILES = [
    "tools_jsonl_interactive_null.jsonl",
    "tools_jsonl_phase_agent_null_gap.jsonl",
]

_PARITY_RUNS = [record for name in _RUN_SHAPE_FILES for record in _load_fixture_jsonl(name)]
_PARITY_EVENTS = [record for name in _EVENT_SHAPE_FILES for record in _load_fixture_jsonl(name)]
_PARITY_TOOLS = [record for name in _TOOLS_SHAPE_FILES for record in _load_fixture_jsonl(name)]


class TestMainUsesIndex:
    """AC1 — main() sources runs/events/tools from the SQLite index, not direct
    JSONL reads. Each test runs with cwd pointed at an empty tmp_path (no
    agent-monitoring/ directory at all), so a passing report — reflecting real
    fixture content — can only have come from the index db."""

    def test_main_loads_runs_from_index_not_direct_jsonl(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        run = dict(_BASE_RUN, run_id="TCK-IDX-A")
        event = {"run_id": "TCK-IDX-A", "seq": 1, "ts": "t", "phase": "Scope",
                  "agent": "ticket-scoper", "status": "ok", "summary": "s"}
        db_path = _build_db(tmp_path, runs=[run], events=[event])

        validate.main(["--db-path", str(db_path)])
        out = capsys.readouterr().out

        assert "OK: 1 runs, 1 events" in out
        assert not (tmp_path / "agent-monitoring" / "runs.jsonl").exists()

    def test_main_loads_events_from_index_not_direct_jsonl(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        run = dict(_BASE_RUN, run_id="TCK-IDX-B")
        event = {"run_id": "TCK-IDX-B", "seq": 1, "ts": "t", "phase": "weird-phase",
                  "agent": "ticket-scoper", "status": "ok", "summary": "s"}
        db_path = _build_db(tmp_path, runs=[run], events=[event])

        validate.main(["--db-path", str(db_path)])
        out = capsys.readouterr().out

        assert "'weird-phase': 1" in out
        assert not (tmp_path / "agent-monitoring" / "events.jsonl").exists()

    def test_main_loads_tools_from_index_not_direct_jsonl(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        run = dict(_BASE_RUN, run_id="TCK-IDX-C")
        event = {"run_id": "TCK-IDX-C", "seq": 1, "ts": "t", "phase": "Implement",
                  "agent": "implementer", "status": "ok", "summary": "s", "tool_call_count": 5}
        tools = [{"run_id": "TCK-IDX-C", "seq": 1, "tool": "Read"} for _ in range(2)]
        db_path = _build_db(tmp_path, runs=[run], events=[event], tools=tools)

        validate.main(["--db-path", str(db_path)])
        out = capsys.readouterr().out

        assert "TCK-IDX-C seq=1: recorded=5 actual=2" in out
        assert not (tmp_path / "agent-monitoring" / "tools.jsonl").exists()


class TestArchitectureGuards:

    def test_validate_py_has_no_direct_jsonl_reads(self):
        source = _VALIDATE_MODULE_PATH.read_text(encoding="utf-8")
        for forbidden in ("RUNS_FILE", "EVENTS_FILE", "TOOLS_FILE"):
            assert forbidden not in source, f"validate.py must not reference {forbidden!r}"
        assert "def load_jsonl" in source, "load_jsonl must remain defined for legacy_reader.py/ingest.py"

    def test_legacy_allowlists_still_importable_from_validate(self):
        from validate import LEGACY_COMPLETION_FIELDS, LEGACY_TERMINAL_STATUS_VALUES

        assert len(LEGACY_COMPLETION_FIELDS) > 0
        assert len(LEGACY_TERMINAL_STATUS_VALUES) > 0


class TestRegressionParity:
    """AC2 — compute_drift_report/compute_tool_count_drift_report/
    compute_multi_invocation_collision_report must produce byte-identical
    output whether their inputs are loaded via load_jsonl() directly from the
    fixture files or via load_*_from_index() off a fixture SQLite db built
    from the same corpus. The three functions' bodies are unchanged by this
    migration; this proves the round-tripped raw_json dicts are field-for-
    field identical to the direct-JSONL dicts, so output cannot diverge."""

    def test_pre_and_post_migration_drift_report_output_identical(self, tmp_path):
        db_path = _build_db(tmp_path, runs=_PARITY_RUNS, events=_PARITY_EVENTS)
        conn = sqlite3.connect(str(db_path))
        indexed_runs = validate.load_runs_from_index(conn)
        indexed_events = validate.load_events_from_index(conn)
        conn.close()

        legacy_report = compute_drift_report(_PARITY_RUNS, _PARITY_EVENTS)
        migrated_report = compute_drift_report(indexed_runs, indexed_events)

        assert legacy_report == migrated_report

    def test_pre_and_post_migration_tool_count_drift_report_output_identical(self, tmp_path):
        db_path = _build_db(tmp_path, events=_PARITY_EVENTS, tools=_PARITY_TOOLS)
        conn = sqlite3.connect(str(db_path))
        indexed_events = validate.load_events_from_index(conn)
        indexed_tools = validate.load_tools_from_index(conn)
        conn.close()

        legacy_report = compute_tool_count_drift_report(_PARITY_EVENTS, _PARITY_TOOLS)
        migrated_report = compute_tool_count_drift_report(indexed_events, indexed_tools)

        assert legacy_report == migrated_report

    def test_pre_and_post_migration_collision_report_output_identical(self, tmp_path):
        db_path = _build_db(tmp_path, events=_PARITY_EVENTS)
        conn = sqlite3.connect(str(db_path))
        indexed_events = validate.load_events_from_index(conn)
        conn.close()

        legacy_report = compute_multi_invocation_collision_report(_PARITY_EVENTS)
        migrated_report = compute_multi_invocation_collision_report(indexed_events)

        assert legacy_report == migrated_report

    def test_tools_row_missing_tool_field_is_a_known_bounded_divergence(self, tmp_path):
        """Documents a real divergence found by spot-checking the live corpus
        (agent-monitoring/tools.jsonl), outside the curated fixture shapes: a
        tools.jsonl record with a valid run_id+seq but no 'tool' field is counted
        by compute_tool_count_drift_report's load_jsonl() path (which only checks
        run_id+seq presence — see its actual_counts loop) but is structurally
        excluded by build_index.py's _ingest_tools (which also requires
        isinstance(record.get("tool"), str)). Fixing this is out of this ticket's
        scope: it would require either changing build_index.py's tools-ingestion
        rule (owned by a sibling ticket) or changing
        compute_tool_count_drift_report's body to require a 'tool' field too
        (forbidden — its body must stay unchanged). Non-gating: this only shifts
        the reported 'Mismatches' count, never validate.py's exit code. Confirmed
        against production data 2026-07-28: exactly one such record exists in
        agent-monitoring/tools.jsonl (TCK-20260716-SIMQ-...-SWEEP seq=4), shifting
        the live report's mismatch count from 487 to 488."""
        off_schema_tool = {"run_id": "TCK-DIVERGE", "seq": 1, "ts": "t"}
        event = {"run_id": "TCK-DIVERGE", "seq": 1, "ts": "t", "phase": "Implement",
                  "agent": "implementer", "status": "ok", "summary": "s", "tool_call_count": 0}

        direct_report = compute_tool_count_drift_report([event], [off_schema_tool])

        db_path = _build_db(tmp_path, events=[event], tools=[off_schema_tool])
        conn = sqlite3.connect(str(db_path))
        indexed_events = validate.load_events_from_index(conn)
        indexed_tools = validate.load_tools_from_index(conn)
        conn.close()
        indexed_report = compute_tool_count_drift_report(indexed_events, indexed_tools)

        assert "recorded=0 actual=1" in direct_report
        assert "recorded=0 actual=0" not in direct_report
        assert "Mismatches (recorded != actual tools.jsonl row count): 0" in indexed_report
        assert direct_report != indexed_report


class TestMissingIndex:

    def test_missing_index_produces_actionable_error(self, tmp_path, capsys):
        missing_db = tmp_path / "does-not-exist" / "monitoring.db"
        with pytest.raises(SystemExit):
            validate.open_index(missing_db)
        captured = capsys.readouterr()
        assert "agent-monitoring-index" in captured.err
        assert "make agent-monitoring-index" in captured.err

    def test_missing_index_exits_nonzero(self, tmp_path):
        missing_db = tmp_path / "does-not-exist" / "monitoring.db"
        with pytest.raises(SystemExit) as exc_info:
            validate.open_index(missing_db)
        assert exc_info.value.code != 0

    def test_main_exits_nonzero_when_index_missing(self, tmp_path):
        missing_db = tmp_path / "nope" / "monitoring.db"
        with pytest.raises(SystemExit) as exc_info:
            validate.main(["--db-path", str(missing_db)])
        assert exc_info.value.code != 0
