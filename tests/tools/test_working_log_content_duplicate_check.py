"""Tests for tools/gate_checks/working_log_content_duplicate_check.py
(TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS item 6).

Content check on tickets/working_log.csv catching duplicate (ticket_id, title) rows -- the shape
two sanctioned writers (append_working_log_row() called directly, then again internally by
record_hand_orchestrated_closure.py) can produce, which no writer-scan guard can catch since both
call sites are the one legitimate writer.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_GATE_CHECKS_DIR = _TOOLS_DIR / "gate_checks"
for _dir in (str(_TOOLS_DIR), str(_GATE_CHECKS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from working_log_content_duplicate_check import (  # noqa: E402
    DUPLICATE_PAIR_CEILING,
    check_working_log_content_duplicates,
    find_duplicate_ticket_id_title_pairs,
)


def _write_log(tmp_path: Path, rows: list) -> Path:
    log = tmp_path / "working_log.csv"
    header = "timestamp,ticket_id,title,status,summary,artifacts_path\n"
    log.write_text(header + "".join(rows), encoding="utf-8")
    return log


def test_no_duplicates_yields_empty_set(tmp_path):
    log = _write_log(
        tmp_path,
        [
            "2026-07-06T00:00:00Z,TCK-A,Title A,DONE,x,none\n",
            "2026-07-07T00:00:00Z,TCK-B,Title B,DONE,y,none\n",
        ],
    )
    assert find_duplicate_ticket_id_title_pairs(log) == set()


def test_same_ticket_id_different_title_is_not_a_content_duplicate(tmp_path):
    """The item-1-class defect (historical ticket_id namespace collision, different titles) must
    NOT be caught by this check -- that is item 1's own, separate scope."""
    log = _write_log(
        tmp_path,
        [
            "2026-07-06T00:00:00Z,TCK-A,First unrelated title,DONE,x,none\n",
            "2026-07-07T00:00:00Z,TCK-A,Second unrelated title,DONE,y,none\n",
        ],
    )
    assert find_duplicate_ticket_id_title_pairs(log) == set()


def test_same_ticket_id_and_title_is_the_dual_writer_content_duplicate(tmp_path):
    """The exact defect this check exists to catch: the same (ticket_id, title) pair written
    twice, e.g. via append_working_log_row() called directly and then again internally by
    record_hand_orchestrated_closure.py for the same ticket close."""
    log = _write_log(
        tmp_path,
        [
            "2026-07-06T00:00:00Z,TCK-A,Same Title,DONE,x,none\n",
            "2026-07-06T00:05:00Z,TCK-A,Same Title,DONE,x again,none\n",
        ],
    )
    dupes = find_duplicate_ticket_id_title_pairs(log)
    assert dupes == {("TCK-A", "Same Title")}


def test_passes_when_duplicate_pair_count_is_at_or_below_ceiling(tmp_path):
    log = _write_log(tmp_path, ["2026-07-06T00:00:00Z,TCK-A,Title A,DONE,x,none\n"])
    results = check_working_log_content_duplicates(log, ceiling=5)
    assert results[0]["status"] == "PASS"


def test_fails_when_duplicate_pair_count_exceeds_ceiling(tmp_path):
    log = _write_log(
        tmp_path,
        [
            "2026-07-06T00:00:00Z,TCK-A,Same Title,DONE,x,none\n",
            "2026-07-06T00:05:00Z,TCK-A,Same Title,DONE,x again,none\n",
        ],
    )
    results = check_working_log_content_duplicates(log, ceiling=0)
    assert results[0]["status"] == "FAIL"
    assert "TCK-A" in results[0]["evidence"]


def test_ceiling_may_only_decrease_never_used_to_paper_over_a_regression():
    assert DUPLICATE_PAIR_CEILING == 46, (
        "DUPLICATE_PAIR_CEILING changed -- if this is because a legitimate fix reduced the real "
        "duplicate-pair count, lower this value to match (never raise it to paper over a new "
        "duplicate; see the module's own docstring for why this must be a ratchet, not a "
        "zero-tolerance assertion)"
    )


def test_real_corpus_is_at_or_below_the_ratchet_ceiling():
    results = check_working_log_content_duplicates()
    assert results[0]["status"] == "PASS", (
        f"real corpus duplicate-(ticket_id, title)-pair count exceeded the ratchet ceiling "
        f"({DUPLICATE_PAIR_CEILING}): {results[0]['evidence']}"
    )


def test_item_6_ids_are_fully_contained_in_item_1_ids_on_the_real_corpus():
    """Pins the actual (post-item-2-fix) relationship between the two checks on the real corpus:
    every ticket_id involved in an item-6-class duplicate (ticket_id, title) pair is also caught
    by item 1's own duplicate-ticket_id scan, since a same-title duplicate is necessarily also a
    same-ticket_id duplicate. This is full containment, not the "mostly disjoint" relationship an
    earlier, pre-item-2-fix measurement found (before item 2 widened item 1's scan to include
    previously `is_duplicate`-flagged rows). The two checks remain justified as separate scopes for
    a semantic reason -- ticket_id reuse regardless of title (item 1) vs. ticket_id reuse with the
    identical title, i.e. the same entry written twice (item 6) -- not a set-overlap argument. See
    the module's own docstring for the full reasoning."""
    sys.path.insert(0, str(_TOOLS_DIR / "gate_checks"))
    from working_log_duplicate_check import DEFAULT_LOG_PATH, DEFAULT_DONE_DIR
    from validate_working_log import run_validation

    item1_result = run_validation(DEFAULT_LOG_PATH, DEFAULT_DONE_DIR)
    item1_ids = set(item1_result["duplicate_ticket_ids"])

    item6_pairs = find_duplicate_ticket_id_title_pairs()
    item6_ids = {pair[0] for pair in item6_pairs}

    assert item6_ids, "expected at least one item-6-class duplicate pair on the real corpus"
    assert item6_ids <= item1_ids, (
        "expected every item-6-class duplicate-pair ticket_id to also be an item-1-class "
        f"duplicate ticket_id (full containment); ids present only in item 6: "
        f"{sorted(item6_ids - item1_ids)}"
    )


def test_makefile_wires_working_log_content_duplicate_check():
    makefile_text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "working-log-content-duplicate-check:" in makefile_text
    assert "working_log_content_duplicate_check.py" in makefile_text
    assert "working-log-content-duplicate-check" in makefile_text.splitlines()[0], (
        ".PHONY line must declare the new target"
    )
