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
    DUPLICATE_TICKET_ID_CEILING,
    check_working_log_duplicate_ticket_ids,
)


def _write_log(tmp_path: Path, rows: list) -> tuple:
    tickets_dir = tmp_path / "tickets"
    done_dir = tickets_dir / "done"
    done_dir.mkdir(parents=True)
    log = tickets_dir / "working_log.csv"
    header = "timestamp,ticket_id,title,status,summary,artifacts_path\n"
    log.write_text(header + "".join(rows), encoding="utf-8")
    return log, done_dir


def test_passes_when_duplicate_count_is_at_or_below_ceiling(tmp_path):
    log, done_dir = _write_log(
        tmp_path,
        [
            "2026-07-06T00:00:00Z,TCK-A,A,DONE,x,none\n",
            "2026-07-07T00:00:00Z,TCK-B,B,DONE,y,none\n",
        ],
    )
    results = check_working_log_duplicate_ticket_ids(log, done_dir, ceiling=5)
    assert results[0]["status"] == "PASS"


def test_fails_when_duplicate_count_exceeds_ceiling(tmp_path):
    log, done_dir = _write_log(
        tmp_path,
        [
            "2026-07-06T00:00:00Z,TCK-A,A,DONE,x,none\n",
            "2026-07-07T00:00:00Z,TCK-A,A again,DONE,y,none\n",
            "2026-07-08T00:00:00Z,TCK-B,B,DONE,z,none\n",
            "2026-07-09T00:00:00Z,TCK-B,B again,DONE,w,none\n",
        ],
    )
    # 2 real duplicates (TCK-A, TCK-B), ceiling 1 -> must FAIL, not silently pass.
    results = check_working_log_duplicate_ticket_ids(log, done_dir, ceiling=1)
    assert results[0]["status"] == "FAIL"
    assert "TCK-A" in results[0]["evidence"] or "TCK-B" in results[0]["evidence"]


def test_ceiling_may_only_decrease_never_used_to_paper_over_a_regression():
    """Pins the ceiling constant's own value and its docstring intent: it is not meant to be
    raised casually to make a newly-introduced duplicate pass. This test fails loudly if the
    constant increases without a deliberate, reviewed change to this file."""
    assert DUPLICATE_TICKET_ID_CEILING == 84, (
        "DUPLICATE_TICKET_ID_CEILING changed -- if this is because a legitimate fix reduced the "
        "real duplicate count, lower this value to match (never raise it to paper over a new "
        "duplicate; see the module's own docstring for why this must be a ratchet, not a "
        "zero-tolerance assertion)"
    )


def test_real_corpus_is_at_or_below_the_ratchet_ceiling():
    """The actual regression guard: run against the real, live tickets/working_log.csv and
    confirm the current count has not grown past the known baseline."""
    results = check_working_log_duplicate_ticket_ids()
    assert results[0]["status"] == "PASS", (
        f"real corpus duplicate-ticket_id count exceeded the ratchet ceiling "
        f"({DUPLICATE_TICKET_ID_CEILING}): {results[0]['evidence']}"
    )


def test_makefile_wires_working_log_duplicate_check():
    makefile_text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "working-log-duplicate-check:" in makefile_text
    assert "working_log_duplicate_check.py" in makefile_text
    assert "working-log-duplicate-check" in makefile_text.splitlines()[0], (
        ".PHONY line must declare the new target"
    )
