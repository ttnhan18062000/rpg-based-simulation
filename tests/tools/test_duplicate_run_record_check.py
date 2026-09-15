"""Tests for tools/gate_checks/duplicate_run_record_check.py (TCK-20260915-DUPLICATE-RUN-RECORDS,
child of TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC).
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_GATE_CHECKS_DIR = _TOOLS_DIR / "gate_checks"
for _dir in (str(_TOOLS_DIR), str(_GATE_CHECKS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from duplicate_run_record_check import (  # noqa: E402
    IDENTICAL_OUTCOME_CEILING,
    check_duplicate_run_records,
)


def _run(run_id, execution_id, start_ts, final_status, end_ts, agent_count=1):
    return {
        "run_id": run_id, "execution_id": execution_id, "start_ts": start_ts,
        "final_status": final_status, "end_ts": end_ts, "agent_count": agent_count,
    }


def test_passes_on_empty_corpus():
    results = check_duplicate_run_records(runs=[], ceiling=0)
    assert results[0]["status"] == "PASS"


def test_progressive_continuation_not_counted_against_the_ratchet():
    """A real gate-fail-then-fix continuation (different final_status per checkpoint) must never
    trip this check, regardless of ceiling -- it is the exact healthy shape this check exists to
    NOT flag."""
    runs = [
        _run("TCK-A", "exec-1", "t1", "NEEDS_CHANGES", "e1"),
        _run("TCK-A", "exec-1", "t1", "DONE", "e2"),
    ]
    results = check_duplicate_run_records(runs=runs, ceiling=0)
    assert results[0]["status"] == "PASS"


def test_identical_outcome_duplicate_counted_against_the_ratchet():
    runs = [
        _run("TCK-B", "exec-2", "t2", "DONE", "e1"),
        _run("TCK-B", "exec-2", "t2", "DONE", "e1"),
    ]
    results = check_duplicate_run_records(runs=runs, ceiling=0)
    assert results[0]["status"] == "FAIL"
    assert "TCK-B" in results[0]["evidence"]


def test_passes_when_identical_outcome_count_is_at_or_below_ceiling():
    runs = [
        _run("TCK-B", "exec-2", "t2", "DONE", "e1"),
        _run("TCK-B", "exec-2", "t2", "DONE", "e1"),
    ]
    results = check_duplicate_run_records(runs=runs, ceiling=1)
    assert results[0]["status"] == "PASS"


def test_ceiling_may_only_decrease_never_used_to_paper_over_a_regression():
    assert IDENTICAL_OUTCOME_CEILING == 1, (
        "IDENTICAL_OUTCOME_CEILING changed -- if this is because a legitimate fix reduced the "
        "real count, lower this value to match (never raise it to paper over a new accidental "
        "duplicate; see the module's own docstring for why this must be a ratchet, not a "
        "zero-tolerance assertion)"
    )


def test_real_corpus_is_at_or_below_the_ratchet_ceiling():
    results = check_duplicate_run_records()
    assert results[0]["status"] == "PASS", (
        f"real corpus genuinely-ambiguous duplicate run-record count exceeded the ratchet ceiling "
        f"({IDENTICAL_OUTCOME_CEILING}): {results[0]['evidence']}"
    )


def test_makefile_wires_duplicate_run_record_check():
    makefile_text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "duplicate-run-record-check:" in makefile_text
    assert "duplicate_run_record_check.py" in makefile_text
    assert "duplicate-run-record-check" in makefile_text.splitlines()[0], (
        ".PHONY line must declare the new target"
    )
