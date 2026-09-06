"""Tests for tools/agent-monitoring/record_events.py's non-null required-field
enforcement, ordering-safe summary truncation, and warn-only phase/agent
vocabulary check (TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT).

All subprocess-level tests here use only rejected (null-field) or non-writing
inputs, or run against tmp-cwd copies, so none of them write to the repo's real
agent-monitoring/data/<ISO-week>/events.jsonl.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import record_events  # noqa: E402
import writer  # noqa: E402
from cost_proxy import compute_cost_proxy_score  # noqa: E402
from record_events import compute_tool_stats, validate_record, warn_vocabulary_drift  # noqa: E402

_RECORD_PATH = _MONITORING_TOOLS_DIR / "record_events.py"


def _freeze_now(monkeypatch, frozen_iso):
    frozen = datetime.fromisoformat(frozen_iso)

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return frozen if tz is None else frozen.astimezone(tz)

    monkeypatch.setattr(record_events, "datetime", _FrozenDatetime)

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
        iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
        written = (tmp_path / "agent-monitoring" / "data" / iso_week / "events.jsonl").read_text()
        assert "TCK-VOCAB-WARN-TEST" in written


# ---------------------------------------------------------------------------
# TCK-20260719-COST-PROXY-WRITE-PATH — deterministic tool_call_count/cost_proxy_score,
# computed here from real tools.jsonl ground truth, never trusting a caller-supplied value.
# ---------------------------------------------------------------------------

def _write_tools_jsonl(tmp_path, rows, week="2026-W01"):
    week_dir = tmp_path / "agent-monitoring" / "data" / week
    week_dir.mkdir(parents=True, exist_ok=True)
    with open(week_dir / "tools.jsonl", "w") as f:
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
    iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
    events_file = tmp_path / "agent-monitoring" / "data" / iso_week / "events.jsonl"
    written = json.loads(events_file.read_text().strip())
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
    iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
    events_file = tmp_path / "agent-monitoring" / "data" / iso_week / "events.jsonl"
    written = json.loads(events_file.read_text().strip())
    assert written["cost_proxy_score"] == 0.0
    assert written["tool_call_count"] == 0


def test_implement_epic_and_create_tickets_records_now_computed_from_real_tools_jsonl(tmp_path, monkeypatch):
    # TCK-20260904-COST-PROXY-EPIC-TICKETS reverses TCK-20260719-COST-PROXY-WRITE-PATH's prior
    # exclusion of implement-epic ("EPIC-"/"FOLDER-" run_id prefix) and create-tickets
    # ("CREATE-TICKETS-" prefix) — that earlier exclusion was a scope-discipline decision for a
    # narrowly-framed bug-fix ticket (limiting blast radius to the one workflow already being
    # fixed), not a technical constraint (see investigation.md's Prior Work section). Both
    # workflows now register a real orchestrator-side writeSidecar() call at their covered sites
    # (implement-epic.js, create-tickets.js), so compute_tool_stats() must compute real, non-null
    # values for them exactly like implement-ticket, not leave them passed through untouched.
    monkeypatch.chdir(tmp_path)
    _write_tools_jsonl(tmp_path, [
        {"run_id": "EPIC-TCK-FAKE-EPIC", "seq": 1, "tool": "Read", "duration_ms": 5},
        {"run_id": "FOLDER-tickets-todos-fake", "seq": 2, "tool": "Bash", "duration_ms": 500},
        {"run_id": "CREATE-TICKETS-fake-source", "seq": 3, "tool": "Edit", "duration_ms": 10},
    ])
    records = [
        {**_VALID_EVENT, "run_id": "EPIC-TCK-FAKE-EPIC", "seq": 1},
        {**_VALID_EVENT, "run_id": "FOLDER-tickets-todos-fake", "seq": 2},
        {**_VALID_EVENT, "run_id": "CREATE-TICKETS-fake-source", "seq": 3},
    ]
    stats = compute_tool_stats(records)
    assert stats == {
        ("EPIC-TCK-FAKE-EPIC", 1): (1, 1.0),
        ("FOLDER-tickets-todos-fake", 2): (1, 0.5),
        ("CREATE-TICKETS-fake-source", 3): (1, 1.0),
    }


def test_zero_tool_call_no_sidecar_paths_compute_zero_not_null(tmp_path, monkeypatch):
    # implement-epic.js's 2 fire-and-forget bash()-only early-return paths (request mode's
    # EPIC_CREATED path, and the ticketIds.length===0 NOTHING_TO_DO path) never call agent(), so
    # they have no (run_id, seq) tool-call group to attribute in the first place — once the filter
    # widens, compute_tool_stats()'s existing unconditional-entry-per-wanted-key behavior must
    # legitimately return (0, 0.0) for these records, not omit the key (they genuinely made zero
    # tracked tool calls, not a gap in coverage).
    monkeypatch.chdir(tmp_path)
    records = [
        {**_VALID_EVENT, "run_id": "EPIC-TCK-FAKE-EPIC-CREATED", "seq": 1},
        {**_VALID_EVENT, "run_id": "FOLDER-tickets-todos-nothing", "seq": 1},
    ]
    stats = compute_tool_stats(records)
    assert stats == {
        ("EPIC-TCK-FAKE-EPIC-CREATED", 1): (0, 0.0),
        ("FOLDER-tickets-todos-nothing", 1): (0, 0.0),
    }


def test_compute_tool_stats_targets_implement_ticket_implement_epic_and_create_tickets(tmp_path, monkeypatch):
    # A 4-way mixed batch: one implement-ticket, one implement-epic, one create-tickets record —
    # each with its own matching tools.jsonl row at a distinct (run_id, seq), proving the 3
    # buckets compute independently with no cross-bucket leakage — plus one simq-audit record
    # with its own tools.jsonl row that must be ABSENT from the result entirely (not None, not
    # (0, 0.0)) — proving the filter is a membership check against exactly {implement-ticket,
    # implement-epic, create-tickets}, never "any known workflow".
    monkeypatch.chdir(tmp_path)
    _write_tools_jsonl(tmp_path, [
        {"run_id": "TCK-MIXED-BATCH", "seq": 1, "tool": "Read", "duration_ms": 5},
        {"run_id": "EPIC-TCK-MIXED-BATCH", "seq": 2, "tool": "Bash", "duration_ms": 500},
        {"run_id": "CREATE-TICKETS-MIXED-BATCH", "seq": 3, "tool": "Edit", "duration_ms": 10},
        {"run_id": "SIMQ-AUDIT-MIXED-BATCH", "seq": 4, "tool": "Bash", "duration_ms": 999},
    ])
    records = [
        {**_VALID_EVENT, "run_id": "TCK-MIXED-BATCH", "seq": 1},
        {**_VALID_EVENT, "run_id": "EPIC-TCK-MIXED-BATCH", "seq": 2},
        {**_VALID_EVENT, "run_id": "CREATE-TICKETS-MIXED-BATCH", "seq": 3},
        {**_VALID_EVENT, "run_id": "SIMQ-AUDIT-MIXED-BATCH", "seq": 4},
    ]
    stats = compute_tool_stats(records)
    assert stats == {
        ("TCK-MIXED-BATCH", 1): (1, 1.0),
        ("EPIC-TCK-MIXED-BATCH", 2): (1, 0.5),
        ("CREATE-TICKETS-MIXED-BATCH", 3): (1, 1.0),
    }
    assert ("SIMQ-AUDIT-MIXED-BATCH", 4) not in stats


def test_batch_top_level_negative_seq_and_child_ticket_positive_seq_do_not_cross_contaminate(tmp_path, monkeypatch):
    # Reproduces and pins the Step 1 collision fix from
    # staging_artifacts/TCK-20260904-COST-PROXY-EPIC-TICKETS/plan.md: implement-epic.js's 4
    # top-level sidecar sites (Discover, batch-monitoring-write, folder-cleanup,
    # tracking-doc-update) share one run_id (batchRunId) with the pre-existing batchEvents array,
    # which already uses seq=1..N under that identical run_id. This test proves, at the Python
    # compute_tool_stats() level (no JS execution needed), that the negative seq range (-1..-4)
    # this ticket's Step 1 introduces is provably disjoint from batchEvents' positive seq=1..N
    # range in BOTH directions — a positive-seq key never leaks a negative-seq row's tool calls,
    # and vice versa.
    monkeypatch.chdir(tmp_path)
    run_id = "EPIC-TCK-BATCH-COLLISION-TEST"
    _write_tools_jsonl(tmp_path, [
        # seq=-1 (Discover's own tool calls) — 2 rows.
        {"run_id": run_id, "seq": -1, "tool": "Bash", "duration_ms": 500},
        {"run_id": run_id, "seq": -1, "tool": "Read", "duration_ms": 10},
        # seq=-2 (batch-monitoring-write's own tool calls) — 1 row.
        {"run_id": run_id, "seq": -2, "tool": "Bash", "duration_ms": 200},
        # seq=1 (first child ticket's batchEvents slot) — 1 row.
        {"run_id": run_id, "seq": 1, "tool": "Edit", "duration_ms": 1},
        # No row at seq=2 (a second child ticket slot with genuinely zero tool calls).
    ])
    records = [
        {**_VALID_EVENT, "run_id": run_id, "seq": 1},
        {**_VALID_EVENT, "run_id": run_id, "seq": 2},
        {**_VALID_EVENT, "run_id": run_id, "seq": -1},
        {**_VALID_EVENT, "run_id": run_id, "seq": -2},
    ]
    stats = compute_tool_stats(records)

    # (run_id, 1): only its own 1 row, not seq=-1's 2 rows or seq=-2's 1 row.
    assert stats[(run_id, 1)] == (1, compute_cost_proxy_score([
        {"run_id": run_id, "seq": 1, "tool": "Edit", "duration_ms": 1},
    ]))
    # (run_id, 2): genuinely zero — not leaking seq=-2's row.
    assert stats[(run_id, 2)] == (0, 0.0)
    # (run_id, -1): only its own 2 rows.
    assert stats[(run_id, -1)] == (2, compute_cost_proxy_score([
        {"run_id": run_id, "seq": -1, "tool": "Bash", "duration_ms": 500},
        {"run_id": run_id, "seq": -1, "tool": "Read", "duration_ms": 10},
    ]))
    # (run_id, -2): only its own 1 row.
    assert stats[(run_id, -2)] == (1, compute_cost_proxy_score([
        {"run_id": run_id, "seq": -2, "tool": "Bash", "duration_ms": 200},
    ]))


# ---------------------------------------------------------------------------
# TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY — unified per-ISO-week folder,
# and the critical bug fix: compute_tool_stats() must read the union of every
# week folder's tools.jsonl, not just the current week's.
# ---------------------------------------------------------------------------


def test_writes_to_unified_week_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _freeze_now(monkeypatch, "2026-08-31T12:00:00+00:00")
    monkeypatch.setattr(sys, "argv", ["record_events.py", "--data", json.dumps([dict(_VALID_EVENT)])])

    record_events.main()

    written_path = tmp_path / "agent-monitoring" / "data" / "2026-W36" / "events.jsonl"
    assert written_path.exists()
    written = json.loads(written_path.read_text().strip())
    assert written["run_id"] == "TCK-FAKE-RUN"
    assert not (tmp_path / "agent-monitoring" / "events.jsonl").exists()


def test_two_different_iso_weeks_write_to_two_distinct_week_folders(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    _freeze_now(monkeypatch, "2026-08-31T12:00:00+00:00")
    monkeypatch.setattr(
        sys, "argv",
        ["record_events.py", "--data", json.dumps([{**_VALID_EVENT, "run_id": "TCK-WEEK-36"}])],
    )
    record_events.main()

    _freeze_now(monkeypatch, "2026-09-07T12:00:00+00:00")
    monkeypatch.setattr(
        sys, "argv",
        ["record_events.py", "--data", json.dumps([{**_VALID_EVENT, "run_id": "TCK-WEEK-37"}])],
    )
    record_events.main()

    week_36 = tmp_path / "agent-monitoring" / "data" / "2026-W36" / "events.jsonl"
    week_37 = tmp_path / "agent-monitoring" / "data" / "2026-W37" / "events.jsonl"
    assert week_36.exists()
    assert week_37.exists()
    assert json.loads(week_36.read_text().strip())["run_id"] == "TCK-WEEK-36"
    assert json.loads(week_37.read_text().strip())["run_id"] == "TCK-WEEK-37"


def test_tool_call_count_correct_for_tool_rows_in_a_non_current_week_folder(tmp_path):
    # The critical regression test: seed tool-call rows for the (run_id, seq) pair being
    # written in a deliberately NON-current week folder (simulating a paused/resumed session,
    # TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION), plus unrelated rows in yet another
    # week folder, then assert compute_tool_stats() finds them via its multi-week glob rather
    # than only looking at the current week's tools.jsonl.
    _write_tools_jsonl(tmp_path, [
        {"run_id": "TCK-CROSS-WEEK-TEST", "seq": 4, "tool": "Bash", "duration_ms": 500},
        {"run_id": "TCK-CROSS-WEEK-TEST", "seq": 4, "tool": "Read", "duration_ms": 10},
    ], week="2026-W20")
    _write_tools_jsonl(tmp_path, [
        {"run_id": "TCK-UNRELATED", "seq": 1, "tool": "Bash", "duration_ms": 100},
    ], week="2026-W21")

    record = {**_VALID_EVENT, "run_id": "TCK-CROSS-WEEK-TEST", "seq": 4}
    result = subprocess.run(
        [sys.executable, str(_RECORD_PATH), "--data", json.dumps(record)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
    events_file = tmp_path / "agent-monitoring" / "data" / iso_week / "events.jsonl"
    written = json.loads(events_file.read_text().strip())
    assert written["tool_call_count"] == 2
    assert written["cost_proxy_score"] > 0.0


def test_tool_call_count_sums_rows_across_multiple_weeks_for_same_key(tmp_path):
    # A single (run_id, seq) key with rows split across two different week folders must have
    # its tool_call_count sum across both, not just whichever week happens to be read first.
    _write_tools_jsonl(tmp_path, [
        {"run_id": "TCK-MULTI-WEEK-SAME-KEY", "seq": 2, "tool": "Bash", "duration_ms": 200},
    ], week="2026-W15")
    _write_tools_jsonl(tmp_path, [
        {"run_id": "TCK-MULTI-WEEK-SAME-KEY", "seq": 2, "tool": "Read", "duration_ms": 20},
    ], week="2026-W16")

    record = {**_VALID_EVENT, "run_id": "TCK-MULTI-WEEK-SAME-KEY", "seq": 2}
    result = subprocess.run(
        [sys.executable, str(_RECORD_PATH), "--data", json.dumps(record)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
    events_file = tmp_path / "agent-monitoring" / "data" / iso_week / "events.jsonl"
    written = json.loads(events_file.read_text().strip())
    assert written["tool_call_count"] == 2


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
    iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
    events_file = tmp_path / "agent-monitoring" / "data" / iso_week / "events.jsonl"
    written = json.loads(events_file.read_text().strip())
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

    iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
    events_file = tmp_path / "agent-monitoring" / "data" / iso_week / "events.jsonl"
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
