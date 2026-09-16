"""Tests for tools/gate_checks/working_log_duplicate_check.py
(TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS item 1).

Wires validate_working_log.py's duplicate-ticket-ID scan into something real (a Makefile target,
`make working-log-duplicate-check`), pinned here, since before this ticket nothing outside its
own test ever invoked it.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_GATE_CHECKS_DIR = _TOOLS_DIR / "gate_checks"
for _dir in (str(_TOOLS_DIR), str(_GATE_CHECKS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from working_log_duplicate_check import (  # noqa: E402
    check_working_log_duplicate_ticket_ids,
    compute_working_log_duplicate_ticket_ids,
)


def _write_log(tmp_path: Path, rows: list) -> tuple:
    tickets_dir = tmp_path / "tickets"
    done_dir = tickets_dir / "done"
    done_dir.mkdir(parents=True)
    log = tickets_dir / "working_log.csv"
    header = "timestamp,ticket_id,title,status,summary,artifacts_path\n"
    log.write_text(header + "".join(rows), encoding="utf-8")
    return log, done_dir


def test_compute_finds_no_duplicates_when_all_ticket_ids_unique(tmp_path):
    log, done_dir = _write_log(
        tmp_path,
        [
            "2026-07-06T00:00:00Z,TCK-A,A,DONE,x,none\n",
            "2026-07-07T00:00:00Z,TCK-B,B,DONE,y,none\n",
        ],
    )
    dupes, count = compute_working_log_duplicate_ticket_ids(log, done_dir)
    assert count == 0
    assert dupes == []


def test_compute_finds_duplicates_and_names_them(tmp_path):
    log, done_dir = _write_log(
        tmp_path,
        [
            "2026-07-06T00:00:00Z,TCK-A,A,DONE,x,none\n",
            "2026-07-07T00:00:00Z,TCK-A,A again,DONE,y,none\n",
            "2026-07-08T00:00:00Z,TCK-B,B,DONE,z,none\n",
            "2026-07-09T00:00:00Z,TCK-B,B again,DONE,w,none\n",
        ],
    )
    dupes, count = compute_working_log_duplicate_ticket_ids(log, done_dir)
    assert count == 2
    assert set(dupes) == {"TCK-A", "TCK-B"}


def test_a_legitimate_reopen_moves_the_count_but_cannot_fail_ci(tmp_path):
    # Simulates the exact real-world event that consumed ratchet headroom on 2026-09-14: a ticket
    # closes in two phases (BLOCKED then DONE), writing two working_log rows for the same
    # ticket_id -- a legitimate reopen, not a dual-writer/CRLF defect.
    log_no_reopen, done_dir_a = _write_log(
        tmp_path / "a", ["2026-07-06T00:00:00Z,TCK-A,A,DONE,x,none\n"],
    )
    log_with_reopen, done_dir_b = _write_log(
        tmp_path / "b",
        [
            "2026-07-06T00:00:00Z,TCK-A,A,BLOCKED,x,none\n",
            "2026-07-07T00:00:00Z,TCK-A,A,DONE,y,none\n",
        ],
    )
    _, count_no_reopen = compute_working_log_duplicate_ticket_ids(log_no_reopen, done_dir_a)
    _, count_with_reopen = compute_working_log_duplicate_ticket_ids(log_with_reopen, done_dir_b)
    assert count_no_reopen != count_with_reopen  # the reopen really does move the count

    # There is no gate left to consume that movement as a pass/fail signal.
    results = check_working_log_duplicate_ticket_ids(log_with_reopen, done_dir_b)
    assert results[0]["status"] == "PASS"


def test_real_corpus_reports_the_duplicate_count():
    results = check_working_log_duplicate_ticket_ids()
    assert results[0]["status"] == "PASS"
    assert "duplicate ticket_id" in results[0]["evidence"]


def test_makefile_wires_working_log_duplicate_check():
    makefile_text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "working-log-duplicate-check:" in makefile_text
    assert "working_log_duplicate_check.py" in makefile_text
    assert "working-log-duplicate-check" in makefile_text.splitlines()[0], (
        ".PHONY line must declare the new target"
    )
