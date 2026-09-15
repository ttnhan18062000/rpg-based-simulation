"""Tests for tools/gate_checks/event_seq_integrity_check.py
(TCK-20260915-EVENT-SEQ-INTEGRITY, child of TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC).
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_GATE_CHECKS_DIR = _TOOLS_DIR / "gate_checks"
for _dir in (str(_TOOLS_DIR), str(_GATE_CHECKS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from event_seq_integrity_check import (  # noqa: E402
    DUPLICATE_SEQ_CEILING,
    GAP_CEILING,
    check_event_seq_integrity,
    find_seq_duplicates_and_gaps,
)


def _event(run_id, seq):
    return {"run_id": run_id, "seq": seq}


def test_no_duplicates_no_gaps():
    events = [_event("TCK-A", 1), _event("TCK-A", 2), _event("TCK-A", 3)]
    dups, gaps = find_seq_duplicates_and_gaps(events)
    assert dups == []
    assert gaps == []


def test_duplicate_seq_detected():
    events = [_event("TCK-B", 1), _event("TCK-B", 1), _event("TCK-B", 2)]
    dups, gaps = find_seq_duplicates_and_gaps(events)
    assert dups == ["TCK-B"]


def test_gap_detected():
    events = [_event("TCK-C", 1), _event("TCK-C", 3)]
    dups, gaps = find_seq_duplicates_and_gaps(events)
    assert gaps == ["TCK-C"]


def test_single_event_run_has_no_gap():
    events = [_event("TCK-D", 1)]
    dups, gaps = find_seq_duplicates_and_gaps(events)
    assert gaps == []


def test_passes_when_both_at_or_below_ceiling():
    events = [_event("TCK-B", 1), _event("TCK-B", 1)]
    results = check_event_seq_integrity(events, duplicate_ceiling=1, gap_ceiling=0)
    assert all(r["status"] == "PASS" for r in results)


def test_fails_duplicate_condition_when_exceeded():
    events = [_event("TCK-B", 1), _event("TCK-B", 1)]
    results = check_event_seq_integrity(events, duplicate_ceiling=0, gap_ceiling=0)
    assert results[0]["status"] == "FAIL"
    assert "TCK-B" in results[0]["evidence"]


def test_fails_gap_condition_when_exceeded():
    events = [_event("TCK-C", 1), _event("TCK-C", 3)]
    results = check_event_seq_integrity(events, duplicate_ceiling=0, gap_ceiling=0)
    assert results[1]["status"] == "FAIL"
    assert "TCK-C" in results[1]["evidence"]


def test_ceilings_may_only_decrease_never_used_to_paper_over_a_regression():
    assert DUPLICATE_SEQ_CEILING == 71, (
        "DUPLICATE_SEQ_CEILING changed -- if this is because a legitimate fix reduced the real "
        "count, lower this value to match (never raise it to paper over a new duplicate)"
    )
    assert GAP_CEILING == 46, (
        "GAP_CEILING changed -- if this is because a legitimate fix reduced the real count, "
        "lower this value to match (never raise it to paper over a new gap)"
    )


def test_real_corpus_is_at_or_below_both_ratchet_ceilings():
    results = check_event_seq_integrity()
    for r in results:
        assert r["status"] == "PASS", f"real corpus exceeded a ratchet ceiling: {r['evidence']}"


def test_makefile_wires_event_seq_integrity_check():
    makefile_text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "event-seq-integrity-check:" in makefile_text
    assert "event_seq_integrity_check.py" in makefile_text
    assert "event-seq-integrity-check" in makefile_text.splitlines()[0], (
        ".PHONY line must declare the new target"
    )
