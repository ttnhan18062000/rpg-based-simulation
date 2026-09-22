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


def test_fix_date_constant_unchanged():
    assert FIX_DATE == "2026-07-19"


def test_large_mismatch_count_still_returns_non_fail_with_count_in_evidence():
    """TCK-20260922-TOOL-CALL-COUNT-MISMATCH-RATCHET-REPORT-ONLY: no count, however large, can
    make this FAIL anymore -- it always reports PASS with the count and run_id set as evidence."""
    runs = [_run(f"TCK-MANY-{i}") for i in range(20)]
    events = [_event(f"TCK-MANY-{i}", 0) for i in range(20)]
    tools = [t for i in range(20) for t in [_tool(f"TCK-MANY-{i}")] * 10]
    results = check_tool_call_count_mismatches(runs, events, tools)
    assert results[0]["status"] == "PASS"
    assert "20 post-2026-07-19" in results[0]["evidence"]
    for i in range(20):
        assert f"TCK-MANY-{i}" in results[0]["evidence"]


def test_makefile_wires_tool_call_count_mismatch_check():
    makefile_text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "tool-call-count-mismatch-check:" in makefile_text
    assert "tool_call_count_mismatch_check.py" in makefile_text
    assert "tool-call-count-mismatch-check" in makefile_text.splitlines()[0], (
        ".PHONY line must declare the new target"
    )
