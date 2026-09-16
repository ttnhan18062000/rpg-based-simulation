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


def test_report_always_passes_regardless_of_count():
    events = [_event("TCK-B", 1), _event("TCK-B", 1), _event("TCK-C", 1), _event("TCK-C", 3)]
    results = check_event_seq_integrity(events)
    assert len(results) == 2
    assert all(r["status"] == "PASS" for r in results)
    assert "1 runs with a duplicate seq" in results[0]["evidence"]
    assert "1 runs with a seq gap" in results[1]["evidence"]


def test_a_legitimate_reopen_moves_both_counts_but_cannot_fail_ci():
    # Simulates the exact real-world event that consumed ratchet headroom on 2026-09-14: a single
    # run_id re-invoked for a legitimate reopen restarts its own local seq numbering, producing
    # both a duplicate seq (across invocations) and, depending on shape, a gap.
    events_no_reopen = [_event("TCK-A", 1), _event("TCK-A", 2)]
    events_with_reopen = [_event("TCK-A", 1), _event("TCK-A", 2), _event("TCK-A", 1)]
    dups_before, _ = find_seq_duplicates_and_gaps(events_no_reopen)
    dups_after, _ = find_seq_duplicates_and_gaps(events_with_reopen)
    assert dups_before != dups_after  # the reopen really does move the count

    results = check_event_seq_integrity(events_with_reopen)
    assert all(r["status"] == "PASS" for r in results)  # no gate left to consume that movement


def test_real_corpus_reports_both_counts():
    results = check_event_seq_integrity()
    assert len(results) == 2
    assert all(r["status"] == "PASS" for r in results)


def test_makefile_wires_event_seq_integrity_check():
    makefile_text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "event-seq-integrity-check:" in makefile_text
    assert "event_seq_integrity_check.py" in makefile_text
    assert "event-seq-integrity-check" in makefile_text.splitlines()[0], (
        ".PHONY line must declare the new target"
    )
