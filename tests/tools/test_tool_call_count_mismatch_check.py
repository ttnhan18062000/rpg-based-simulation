"""Tests for tools/gate_checks/tool_call_count_mismatch_check.py
(TCK-20260915-TOOL-CALL-COUNT-MISMATCH, child of TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC).
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_GATE_CHECKS_DIR = _TOOLS_DIR / "gate_checks"
for _dir in (str(_TOOLS_DIR), str(_GATE_CHECKS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from tool_call_count_mismatch_check import (  # noqa: E402
    FIX_DATE,
    MISMATCH_CEILING,
    check_tool_call_count_mismatches,
    find_tool_call_count_mismatches,
)


def _run(run_id, workflow="implement-ticket", start_ts="2026-08-01T00:00:00Z"):
    return {"run_id": run_id, "workflow": workflow, "start_ts": start_ts}


def _event(run_id, tcc):
    return {"run_id": run_id, "tool_call_count": tcc}


def _tool(run_id):
    return {"run_id": run_id}


def test_no_mismatch_when_counts_agree():
    runs = [_run("TCK-A")]
    events = [_event("TCK-A", 3)]
    tools = [_tool("TCK-A")] * 3
    mismatches = find_tool_call_count_mismatches(runs, events, tools)
    assert mismatches == []


def test_claimed_zero_actual_many_is_a_mismatch():
    """The ticket's own flagship example shape: 0 claimed, real rows exist."""
    runs = [_run("TCK-B")]
    events = [_event("TCK-B", 0)]
    tools = [_tool("TCK-B")] * 10
    mismatches = find_tool_call_count_mismatches(runs, events, tools)
    assert len(mismatches) == 1
    assert mismatches[0] == ("TCK-B", 0, 10)


def test_claimed_exceeds_actual_is_also_a_mismatch():
    """The ticket's own 4th example ran the other way -- claimed > actual."""
    runs = [_run("TCK-C")]
    events = [_event("TCK-C", 30)]
    tools = [_tool("TCK-C")] * 1
    mismatches = find_tool_call_count_mismatches(runs, events, tools)
    assert len(mismatches) == 1


def test_pre_fix_date_runs_are_excluded():
    runs = [_run("TCK-OLD", start_ts="2026-06-01T00:00:00Z")]
    events = [_event("TCK-OLD", 0)]
    tools = [_tool("TCK-OLD")] * 500
    mismatches = find_tool_call_count_mismatches(runs, events, tools)
    assert mismatches == []


def test_unsupported_workflow_is_excluded():
    runs = [_run("TCK-SIMQ", workflow="simq-audit")]
    events = [_event("TCK-SIMQ", 0)]
    tools = [_tool("TCK-SIMQ")] * 10
    mismatches = find_tool_call_count_mismatches(runs, events, tools)
    assert mismatches == []


def test_passes_when_mismatch_count_at_or_below_ceiling():
    runs = [_run("TCK-B")]
    events = [_event("TCK-B", 0)]
    tools = [_tool("TCK-B")] * 10
    results = check_tool_call_count_mismatches(runs, events, tools, ceiling=1)
    assert results[0]["status"] == "PASS"


def test_fails_when_mismatch_count_exceeds_ceiling():
    runs = [_run("TCK-B")]
    events = [_event("TCK-B", 0)]
    tools = [_tool("TCK-B")] * 10
    results = check_tool_call_count_mismatches(runs, events, tools, ceiling=0)
    assert results[0]["status"] == "FAIL"
    assert "TCK-B" in results[0]["evidence"]


def test_ceiling_matches_its_own_documented_history():
    assert MISMATCH_CEILING == 53, (
        "MISMATCH_CEILING changed again -- if this is because a legitimate fix reduced the real "
        "post-fix mismatch count, lower this value to match; if it's because a fresh, fully "
        "root-cause-diagnosed instance of an already-documented failure class pushed the real "
        "corpus over the previous ceiling (as TCK-20260921-HAND-ORCHESTRATION-SIDECAR-STALENESS-"
        "INCIDENT did, 49 -> 50, and TCK-20260922-HAND-ORCHESTRATION-SIDECAR-POST-SNAPSHOT-"
        "ACCUMULATION-INCIDENT did, 50 -> 53), raising it with the same standard of evidence is "
        "legitimate. Never raise it to paper over an unexplained new mismatch; see the module's "
        "own docstring for why this must be a ratchet, not a zero-tolerance assertion."
    )


def test_fix_date_constant_unchanged():
    assert FIX_DATE == "2026-07-19"


def test_real_corpus_is_at_or_below_the_ratchet_ceiling():
    results = check_tool_call_count_mismatches()
    assert results[0]["status"] == "PASS", (
        f"real corpus post-fix mismatch count exceeded the ratchet ceiling "
        f"({MISMATCH_CEILING}): {results[0]['evidence']}"
    )


def test_makefile_wires_tool_call_count_mismatch_check():
    makefile_text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "tool-call-count-mismatch-check:" in makefile_text
    assert "tool_call_count_mismatch_check.py" in makefile_text
    assert "tool-call-count-mismatch-check" in makefile_text.splitlines()[0], (
        ".PHONY line must declare the new target"
    )
