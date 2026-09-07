"""Tests for tools/working_log_parser.py and tools/validate_working_log.py
(TCK-20260904-WORKING-LOG-CSV-PARSER).

Mirrors tests/tools/test_ticket_stats_report.py's own test conventions where applicable.
"""
from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from working_log_parser import (  # noqa: E402
    ParseResult,
    parse_working_log,
)
from validate_working_log import run_validation  # noqa: E402

REAL_LOG_PATH = Path(__file__).parent.parent.parent / "tickets" / "working_log.csv"

HEADER = "timestamp,ticket_id,title,status,summary,artifacts_path\n"


def _write_log(tmp_path: Path, body: str) -> Path:
    log = tmp_path / "working_log.csv"
    log.write_text(HEADER + body, encoding="utf-8")
    return log


# ---------------------------------------------------------------------------
# Step 2 — unit tests (fixture-based)
# ---------------------------------------------------------------------------


def test_clean_row_parses_with_expected_fields(tmp_path):
    log = _write_log(
        tmp_path,
        '2026-07-06T00:00:00Z,TCK-A,A,DONE,"Did a thing, with a comma",stored_artifacts/TCK-A\n',
    )
    result = parse_working_log(log)

    assert len(result.rows) == 1
    row = result.rows[0]
    assert row.classification == "clean"
    assert row.record == {
        "timestamp": "2026-07-06T00:00:00Z",
        "ticket_id": "TCK-A",
        "title": "A",
        "status": "DONE",
        "summary": "Did a thing, with a comma",
        "artifacts_path": "stored_artifacts/TCK-A",
    }


_QUOTE_DESYNC_MISMATCH_ROW = (
    '2026-08-21T08:33:52Z,TCK-D,"Title text","DONE",'
    '"summary one, exposed as result["mode_sequence"], summary two",'
    '"stored_artifacts/TCK-D/"\n'
)


def test_field_count_mismatch_row_is_flagged_ambiguous_not_dropped_or_merged(tmp_path):
    body = (
        # (a) unescaped comma inside artifacts_path (mirrors line 1581's shape)
        "2026-08-25T08:30:52Z,TCK-B,Some Title,DONE,A summary text here,none (epic, scope-only)\n"
        # (b) unescaped comma inside title (mirrors line 3245's shape)
        '2026-08-31T06:00:00Z,TCK-C,A Title, With Commas,DONE,A summary text,none\n'
        # (c) quote-desync (mirrors line 1511's shape): unescaped internal quote inside a quoted field
        + _QUOTE_DESYNC_MISMATCH_ROW
    )
    log = _write_log(tmp_path, body)
    result = parse_working_log(log)

    assert len(result.rows) == 3
    for row in result.rows:
        assert row.classification == "field_count_mismatch"

    row_a = result.rows[0]
    assert row_a.recoverable is True
    assert row_a.record["artifacts_path"] == "none (epic, scope-only)"
    assert not row_a.record["summary"].endswith(",none (epic")


def test_irreducibly_ambiguous_quote_desync_row_is_not_heuristically_repaired(tmp_path):
    log = _write_log(tmp_path, _QUOTE_DESYNC_MISMATCH_ROW)
    result = parse_working_log(log)

    row = result.rows[0]
    assert row.classification == "field_count_mismatch"
    assert row.recoverable is False
    assert row.record is None
    assert row.raw_fields  # raw content still present, never dropped


def test_duplicate_content_rows_are_flagged_not_fixed(tmp_path):
    line = '2026-08-31T06:00:00Z,TCK-C,A Title, With Commas,DONE,A summary text,none\n'
    log = _write_log(tmp_path, line + line)
    result = parse_working_log(log)

    assert len(result.rows) == 2
    first, second = result.rows
    assert first.is_duplicate is False
    assert first.duplicate_of_line is None
    assert second.is_duplicate is True
    assert second.duplicate_of_line == first.line_no


def test_embedded_header_duplicate_row_is_flagged(tmp_path):
    body = (
        "2026-07-06T00:00:00Z,TCK-A,A,DONE,x,none\n"
        "timestamp,ticket_id,title,status,summary,artifacts_path\n"
    )
    log = _write_log(tmp_path, body)
    result = parse_working_log(log)

    assert result.rows[1].classification == "embedded_header_duplicate"
    assert result.rows[1].record is None
    assert result.embedded_header_duplicate_count == 1


def test_ambiguous_row_count_is_first_class_signal_matching_ticket_stats_report_convention(tmp_path):
    body = (
        "2026-07-06T00:00:00Z,TCK-A,A,DONE,x,none\n"
        '2026-08-31T06:00:00Z,TCK-C,A Title, With Commas,DONE,A summary text,none\n'
        # quote-desync-masquerading-as-clean row (6 fields, unbalanced parens)
        '2026-07-20T00:00:00Z,TCK-E,Title,DONE,"Did a thing.,N/A (hotfix", no staging artifacts)\n'
    )
    log = _write_log(tmp_path, body)
    result = parse_working_log(log)

    assert result.ambiguous_row_count == 2  # the mismatch row + the quote-desync row
    assert isinstance(result.ambiguous_row_count, int)


def test_ambiguous_row_count_is_zero_when_no_ambiguous_rows(tmp_path):
    log = _write_log(tmp_path, "2026-07-06T00:00:00Z,TCK-A,A,DONE,x,none\n")
    result = parse_working_log(log)
    assert result.ambiguous_row_count == 0


def test_quote_desync_masquerading_as_clean_rows_are_reclassified_and_reconstructed(tmp_path):
    body = (
        # line-1100 shape: N/A (hotfix
        '2026-07-20T00:00:00Z,TCK-F,Title,DONE,"Did a thing.,N/A (hotfix", no staging artifacts)\n'
        # line-1318 shape: none (hotfix
        '2026-08-09T00:00:00Z,TCK-G,Title,DONE,"Did a thing.,none (hotfix", no staging artifacts)\n'
        # line-1400 shape: none (scope-only epic
        '2026-08-15T00:00:00Z,TCK-H,Title,DONE,"Epic done.,none (scope-only epic", no staging artifacts)\n'
    )
    log = _write_log(tmp_path, body)
    result = parse_working_log(log)

    assert len(result.rows) == 3
    expected = [
        ("N/A (hotfix, no staging artifacts)", ",N/A (hotfix"),
        ("none (hotfix, no staging artifacts)", ",none (hotfix"),
        ("none (scope-only epic, no staging artifacts)", ",none (scope-only epic"),
    ]
    for row, (expected_ap, corrupted_suffix) in zip(result.rows, expected):
        assert row.classification == "quote_desync_masquerading_as_clean"
        assert row.recoverable is True
        assert row.record["artifacts_path"] == expected_ap
        assert not row.record["summary"].endswith(corrupted_suffix)


def test_quote_desync_row_with_unmatched_fragment_degrades_to_unrecoverable(tmp_path):
    log = _write_log(
        tmp_path,
        '2026-07-20T00:00:00Z,TCK-I,Title,DONE,"Did a thing.,unknown (fragment", trailing)\n',
    )
    result = parse_working_log(log)

    row = result.rows[0]
    assert row.classification == "quote_desync_masquerading_as_clean"
    assert row.recoverable is False
    assert row.record is None
    assert row.raw_fields


# ---------------------------------------------------------------------------
# Step 4 — run_validation() fixture tests
# ---------------------------------------------------------------------------


def test_run_validation_preserves_existing_duplicate_id_and_missing_entry_checks(tmp_path):
    tickets_dir = tmp_path / "tickets"
    done_dir = tickets_dir / "done"
    done_dir.mkdir(parents=True)
    (done_dir / "TCK-ORPHAN.md").write_text("# orphan\n", encoding="utf-8")

    log = tickets_dir / "working_log.csv"
    log.write_text(
        HEADER
        + "2026-07-06T00:00:00Z,TCK-A,A,DONE,x,none\n"
        + "2026-07-07T00:00:00Z,TCK-A,A again,DONE,y,none\n",
        encoding="utf-8",
    )

    result = run_validation(log, done_dir)

    assert any("Duplicate ticket IDs" in e for e in result["errors"])
    assert any("TCK-ORPHAN" in e for e in result["errors"])


def test_duplicate_ticket_ids_check_excludes_flagged_duplicate_rows(tmp_path):
    """TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP: an exact-duplicate physical
    line (is_duplicate=True, e.g. from a squash-merge whole-block duplication) must not
    trigger a false "Duplicate ticket IDs" error -- but a genuine same-ticket-ID,
    different-content second row (an actual reopened ticket / a real double-paste) must
    still be reported."""
    tickets_dir = tmp_path / "tickets"
    done_dir = tickets_dir / "done"
    done_dir.mkdir(parents=True)

    exact_duplicate_line = "2026-07-06T00:00:00Z,TCK-A,A,DONE,x,none\n"
    log = tickets_dir / "working_log.csv"
    log.write_text(
        HEADER
        + exact_duplicate_line
        + exact_duplicate_line  # exact-duplicate physical line -- flagged is_duplicate, not a real dupe
        + "2026-07-07T00:00:00Z,TCK-B,B,DONE,y,none\n"
        + "2026-07-08T00:00:00Z,TCK-B,B reopened,DONE,z,none\n",  # genuine same-ticket-ID dupe
        encoding="utf-8",
    )

    result = run_validation(log, done_dir)

    dupe_errors = [e for e in result["errors"] if "Duplicate ticket IDs" in e]
    assert len(dupe_errors) == 1
    assert "TCK-A" not in dupe_errors[0]
    assert "TCK-B" in dupe_errors[0]


def test_run_validation_reports_ambiguous_row_count(tmp_path):
    tickets_dir = tmp_path / "tickets"
    done_dir = tickets_dir / "done"
    done_dir.mkdir(parents=True)

    log = tickets_dir / "working_log.csv"
    log.write_text(
        HEADER
        + "2026-07-06T00:00:00Z,TCK-A,A,DONE,x,none\n"
        + '2026-08-31T06:00:00Z,TCK-C,A Title, With Commas,DONE,A summary text,none\n',
        encoding="utf-8",
    )

    result = run_validation(log, done_dir)

    assert result["ambiguous_row_count"] == 1
    # both rows have a populated record (the mismatch row is recoverable), so both feed
    # the pre-existing checks despite one being classification=="field_count_mismatch"
    assert result["row_count"] == 2


# ---------------------------------------------------------------------------
# Step 3 — integration tests against the real committed tickets/working_log.csv
# ---------------------------------------------------------------------------


def test_round_trip_parses_full_file_without_exception():
    with open(REAL_LOG_PATH, newline="", encoding="utf-8") as f:
        expected_count = sum(1 for _ in csv.reader(f)) - 1  # minus header

    result = parse_working_log(REAL_LOG_PATH)

    assert len(result.rows) == expected_count


def test_all_9_confirmed_live_mismatch_rows_are_flagged():
    """Was test_all_11_confirmed_live_mismatch_rows_are_flagged before
    TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP's Step 6 cleanup commit. Of the
    original 11 physical lines, 2 (3104, 3174) were themselves the exact-duplicate copies
    of 2 others in this same set (1511, 3104 = 1511+1593; 1581, 3174 = 1581+1593) --
    reproduced by PR #90's squash-merge whole-block duplication and removed by that
    cleanup commit, which deleted physical lines 1594-3180 inclusive. The remaining 9
    lines are the same real rows as before, at their post-cleanup physical positions
    (unaffected if < 1594, shifted down by exactly 1587 if originally > 3180). No
    classification logic changed -- verified directly: 1511 and 1581 keep their original
    line numbers (below the deleted range); 3245/3253/3284/3287/3289/3294/3307 shift to
    1658/1666/1697/1700/1702/1707/1720 (each original line number minus 1587)."""
    result = parse_working_log(REAL_LOG_PATH)
    by_line = {r.line_no: r for r in result.rows}

    expected_lines = {1511, 1581, 1658, 1666, 1697, 1700, 1702, 1707, 1720}
    for line_no in expected_lines:
        assert by_line[line_no].classification == "field_count_mismatch", line_no

    irreducible = {1511}
    for line_no in expected_lines:
        expected_recoverable = line_no not in irreducible
        assert by_line[line_no].recoverable is expected_recoverable, line_no


def test_trailing_field_comma_split_rows_reconstruct_correct_artifacts_path():
    """Line 3174 (the exact-duplicate copy of 1581) was removed by
    TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP's Step 6 cleanup commit -- only
    the original row at 1581 remains."""
    result = parse_working_log(REAL_LOG_PATH)
    by_line = {r.line_no: r for r in result.rows}

    for line_no in (1581,):
        row = by_line[line_no]
        assert row.record["artifacts_path"] == "none (epic, scope-only)"
        assert row.record["summary"].endswith("uncalibrated illustrative placeholders.")
        assert not row.record["summary"].endswith(",none (epic")


def test_ambiguous_row_count_matches_26_for_real_file():
    """Was test_ambiguous_row_count_matches_45_for_real_file before
    TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP's Step 6 cleanup commit removed
    the ~1586-row duplicate block (physical lines 1594-3180). 45 = 11 mismatch + 34
    quote-desync rows counted every duplicate copy as a separate ambiguous row; 26 = 9 + 17
    counts each real row exactly once now that the duplicate copies are gone."""
    result = parse_working_log(REAL_LOG_PATH)
    assert result.ambiguous_row_count == 26


def test_all_17_confirmed_live_quote_desync_lines_are_flagged():
    """Was test_all_34_confirmed_live_quote_desync_lines_are_flagged before
    TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP's Step 6 cleanup commit. All 17
    of the original 34 physical lines >= 2693 were exact-duplicate copies of these same 17
    lines (offset +1593, e.g. 1100+1593=2693), reproduced by PR #90's squash-merge and
    removed by that cleanup. The remaining 17 lines are unaffected -- all sit below the
    deleted range (1594-3180), so their line numbers did not shift."""
    result = parse_working_log(REAL_LOG_PATH)
    by_line = {r.line_no: r for r in result.rows}

    expected_lines = {
        1100, 1101, 1102, 1103, 1318, 1320, 1329, 1332, 1337, 1400, 1401,
        1415, 1453, 1457, 1459, 1460, 1462,
    }
    assert len(expected_lines) == 17

    for line_no in expected_lines:
        row = by_line[line_no]
        assert row.classification == "quote_desync_masquerading_as_clean", line_no
        assert row.recoverable is True, line_no


def test_quote_desync_line_1100_reconstructs_to_known_vocabulary_artifacts_path():
    result = parse_working_log(REAL_LOG_PATH)
    by_line = {r.line_no: r for r in result.rows}

    row = by_line[1100]
    assert row.record["artifacts_path"] == "N/A (hotfix, no staging artifacts)"
    assert not row.record["summary"].endswith(",N/A (hotfix")


def test_historical_rows_are_never_rewritten_byte_identical_after_run(tmp_path):
    copy_path = tmp_path / "working_log.csv"
    shutil.copy2(REAL_LOG_PATH, copy_path)
    original_bytes = copy_path.read_bytes()
    original_mtime = copy_path.stat().st_mtime

    parse_working_log(copy_path)

    assert copy_path.read_bytes() == original_bytes
    assert copy_path.stat().st_mtime == original_mtime
