"""Tests for tools/agent-monitoring/legacy_reader.py's classify_provenance
(TCK-20260721-BASELINE-MONITORING-MANIFEST).

Three sections, in the order the implementation plan adds them:
  1. Inline-dict unit tests (no file I/O), mirroring
     test_validate_agent_monitoring.py's pure-function test style.
  2. Fixture-backed parametrized tests against tests/fixtures/agent_monitoring/.
  3. Round-trip readability test against real, recent runs.jsonl/events.jsonl
     records — proves the classifier agrees with validate.py's own tolerance
     for current-schema records.
"""
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from legacy_reader import classify_provenance  # noqa: E402
from validate import _record_is_complete  # noqa: E402

_FIXTURES_DIR = _REPO_ROOT / "tests" / "fixtures" / "agent_monitoring"


# ---------------------------------------------------------------------------
# Section 1 — inline-dict unit tests, one per classification rule
# ---------------------------------------------------------------------------

def test_runs_shape6_type_checker_exception():
    record = {"run_id": "TCK-FAKE", "outcome": "success", "phase": "implement"}
    assert classify_provenance(record, "runs") == frozenset({"shape6_type_checker_exception"})


def test_runs_shape5_folder_epic_bare_status():
    record = {"run_id": "FOLDER-fake-folder", "status": "DONE", "ts": "2026-01-01T00:00:00Z"}
    assert classify_provenance(record, "runs") == frozenset({"shape5_folder_epic_bare_status"})


def test_runs_shape5_epic_prefix_also_matches():
    record = {"run_id": "EPIC-fake-epic", "status": "DONE", "ts": "2026-01-01T00:00:00Z"}
    assert classify_provenance(record, "runs") == frozenset({"shape5_folder_epic_bare_status"})


def test_runs_current_schema_folder_prefix_is_not_shape5():
    # A FOLDER-*/EPIC-* record that already has final_status/start_ts/end_ts is
    # current-schema, not legacy shape 5 — the classifier must key on field
    # absence, never on the run_id prefix alone.
    record = {
        "run_id": "FOLDER-fake-current",
        "start_ts": "2026-01-01T00:00:00Z",
        "end_ts": "2026-01-01T01:00:00Z",
        "workflow": "implement-epic",
        "tier": "n/a",
        "final_status": "DONE",
        "agent_count": 3,
    }
    assert classify_provenance(record, "runs") == frozenset()


def test_runs_shape1_started_finished_notes():
    record = {
        "run_id": "TCK-FAKE",
        "started_at": "2026-01-01T00:00:00Z",
        "finished_at": "2026-01-01T01:00:00Z",
        "phases_completed": ["scope", "implement"],
    }
    assert classify_provenance(record, "runs") == frozenset({"shape1_started_finished_notes"})


def test_runs_shape2_final_status_no_end_ts():
    record = {"run_id": "TCK-FAKE", "start_ts": "2026-01-01T00:00:00Z", "final_status": "DONE"}
    assert classify_provenance(record, "runs") == frozenset({"shape2_final_status_no_end_ts"})


def test_runs_shape3_ts_start_ts_end_result():
    record = {"run_id": "TCK-FAKE", "ts_start": "2026-01-01T00:00:00Z", "ts_end": "2026-01-01T01:00:00Z", "result": "DONE"}
    assert classify_provenance(record, "runs") == frozenset({"shape3_ts_start_ts_end_result"})


def test_runs_shape4_completed_at_status():
    record = {"run_id": "TCK-FAKE", "started_at": "2026-01-01T00:00:00Z", "completed_at": "2026-01-01T01:00:00Z", "status": "DONE"}
    assert classify_provenance(record, "runs") == frozenset({"shape4_completed_at_status"})


def test_runs_current_schema_is_unclassified():
    record = {
        "run_id": "TCK-FAKE",
        "start_ts": "2026-01-01T00:00:00Z",
        "end_ts": "2026-01-01T01:00:00Z",
        "workflow": "implement-ticket",
        "tier": "standard",
        "final_status": "DONE",
        "agent_count": 3,
        "duration_s": 60,
    }
    assert classify_provenance(record, "runs") == frozenset()


def test_tools_interactive_null():
    record = {"session_id": "abc", "run_id": None, "seq": None, "ts": "t", "tool": "Read", "status": "ok"}
    assert classify_provenance(record, "tools") == frozenset({"interactive_null"})


def test_tools_phase_agent_null_gap():
    record = {"session_id": "abc", "run_id": "TCK-FAKE", "seq": 2, "ts": "t", "tool": "Read", "status": "ok"}
    assert classify_provenance(record, "tools") == frozenset({"tools_phase_agent_null_gap"})


def test_tools_current_schema_is_unclassified():
    record = {
        "session_id": "abc", "run_id": "TCK-FAKE", "seq": 2, "phase": "Implement", "agent": "implementer",
        "ts": "t", "tool": "Read", "status": "ok",
    }
    assert classify_provenance(record, "tools") == frozenset()


def test_events_reason_code_null_only():
    record = {"run_id": "TCK-FAKE", "seq": 1, "ts": "t", "phase": "Scope", "agent": "ticket-scoper", "status": "ok", "summary": "s", "tool_call_count": 3}
    assert classify_provenance(record, "events") == frozenset({"events_reason_code_null"})


def test_events_tool_call_count_absent_only():
    record = {"run_id": "TCK-FAKE", "seq": 1, "ts": "t", "phase": "Scope", "agent": "ticket-scoper", "status": "ok", "summary": "s", "reason_code": None}
    assert classify_provenance(record, "events") == frozenset({"events_tool_call_count_absent"})


def test_events_both_fields_absent():
    # The real-corpus case: one historical record predates both fields at once.
    record = {"run_id": "TCK-FAKE", "seq": 1, "ts": "t", "phase": "Scope", "agent": "ticket-scoper", "status": "ok", "summary": "s"}
    assert classify_provenance(record, "events") == frozenset({"events_reason_code_null", "events_tool_call_count_absent"})


def test_events_current_schema_is_unclassified():
    record = {
        "run_id": "TCK-FAKE", "seq": 1, "ts": "t", "phase": "Scope", "agent": "ticket-scoper",
        "status": "ok", "summary": "s", "tool_call_count": 3, "reason_code": None,
    }
    assert classify_provenance(record, "events") == frozenset()


def test_classify_provenance_rejects_unknown_source():
    with pytest.raises(ValueError):
        classify_provenance({}, "bogus")


# ---------------------------------------------------------------------------
# Section 2 — fixture-backed parametrized tests
# ---------------------------------------------------------------------------

_FIXTURE_EXPECTATIONS = [
    ("shape1_started_finished_notes.jsonl", "runs", frozenset({"shape1_started_finished_notes"})),
    ("shape2_final_status_no_end_ts.jsonl", "runs", frozenset({"shape2_final_status_no_end_ts"})),
    ("shape3_ts_start_ts_end_result.jsonl", "runs", frozenset({"shape3_ts_start_ts_end_result"})),
    ("shape4_completed_at_status.jsonl", "runs", frozenset({"shape4_completed_at_status"})),
    ("shape5_folder_epic_bare_status.jsonl", "runs", frozenset({"shape5_folder_epic_bare_status"})),
    ("shape6_type_checker_exception.jsonl", "runs", frozenset({"shape6_type_checker_exception"})),
    ("tools_jsonl_phase_agent_null_gap.jsonl", "tools", frozenset({"tools_phase_agent_null_gap"})),
    ("tools_jsonl_interactive_null.jsonl", "tools", frozenset({"interactive_null"})),
    ("events_jsonl_tool_call_count_absent.jsonl", "events", frozenset({"events_reason_code_null", "events_tool_call_count_absent"})),
    ("events_jsonl_reason_code_null.jsonl", "events", frozenset({"events_reason_code_null", "events_tool_call_count_absent"})),
]


def _load_fixture_record(filename: str) -> dict:
    line = (_FIXTURES_DIR / filename).read_text().strip()
    return json.loads(line)


@pytest.mark.parametrize("filename,source,expected", _FIXTURE_EXPECTATIONS)
def test_fixture_classification(filename, source, expected):
    record = _load_fixture_record(filename)
    assert classify_provenance(record, source) == expected


def test_shape5_fixture_is_genuinely_legacy_not_current_schema():
    # Guards the 65-current-schema-vs-7-true-legacy trap directly: the shape-5
    # fixture must be one of the 7 true legacy bare-status records, never one of
    # the 65 FOLDER-*/EPIC-* records that already match the current schema.
    record = _load_fixture_record("shape5_folder_epic_bare_status.jsonl")
    assert "final_status" not in record
    assert "start_ts" not in record
    assert "end_ts" not in record


def test_tools_interactive_null_is_excluded_from_legacy_warning_rule():
    # Decided #3: interactive_null is by-design, never a "warning" — this is a
    # documentation-level assertion pinning that intent at the classifier layer.
    record = _load_fixture_record("tools_jsonl_interactive_null.jsonl")
    labels = classify_provenance(record, "tools")
    assert labels == frozenset({"interactive_null"})
    assert labels != frozenset()


# ---------------------------------------------------------------------------
# Section 3 — round-trip readability of recent real current-schema records
# ---------------------------------------------------------------------------

_REAL_MONITORING_DIR = _REPO_ROOT / "agent-monitoring"
_SAMPLE_SIZE = 20


def _recent_records(filename: str, n: int) -> list:
    path = _REAL_MONITORING_DIR / filename
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    records = []
    for line in lines[-n:]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def test_recent_runs_records_classify_as_current_and_agree_with_validate():
    records = _recent_records("runs.jsonl", _SAMPLE_SIZE)
    assert records, "no recent runs.jsonl records sampled — test would be vacuous"

    by_run_id: dict = {}
    for record in records:
        assert classify_provenance(record, "runs") == frozenset(), (
            f"recent run_id={record.get('run_id')!r} classified as legacy — "
            "expected current schema"
        )
        by_run_id.setdefault(record.get("run_id"), []).append(record)

    # A run_id's own group of records agrees with validate.py's completion check
    # (validate.py:271-276 groups by run_id and only flags a run_id as incomplete
    # if none of its records are complete) — an in-flight run-start record with no
    # end_ts is expected to be individually incomplete as long as a sibling record
    # for the same run_id (e.g. a later DONE record) satisfies the check.
    for run_id, group in by_run_id.items():
        assert any(_record_is_complete(r) for r in group), (
            f"recent run_id={run_id!r} disagrees with validate.py's own completion "
            "check (no record in its group is complete)"
        )


def test_recent_events_records_remain_parseable():
    records = _recent_records("events.jsonl", _SAMPLE_SIZE)
    assert records, "no recent events.jsonl records sampled — test would be vacuous"
    for record in records:
        # events.jsonl has no "current vs legacy" schema split the way runs.jsonl
        # does (reason_code/tool_call_count absence is itself the classifier's
        # signal, not an error) — this test only proves round-trip parseability.
        labels = classify_provenance(record, "events")
        assert isinstance(labels, frozenset)
