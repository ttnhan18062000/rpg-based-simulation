#!/usr/bin/env python3
"""
Tolerant parser for tickets/working_log.csv.

The file is manually/LLM-appended (no programmatic writer exists anywhere in the
codebase), so a visible subset of historical rows carry unescaped commas or stray
quote characters that desync naive CSV parsing. This module never rewrites the file
on disk — every row is read-only, and every classification is surfaced explicitly
rather than silently repaired or dropped.

Two independent, evidenced corruption classes are detected today:

  1. field_count_mismatch (TCK-20260904-WORKING-LOG-CSV-PARSER's own Finding 1):
     csv.reader splits a row into something other than 6 fields. Most such rows are
     mechanically recoverable via a status-token-anchor rejoin (the same technique
     TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS used); a strict=True re-parse
     distinguishes the recoverable rows from the two (1511, 3104) whose stray quote
     desyncs csv.reader's own quote-tracking state badly enough that no rejoin can be
     trusted.

  2. quote_desync_masquerading_as_clean (Finding 3): a row that still parses to exactly
     6 raw fields (invisible to the field-count check) because a stray quote immediately
     followed by the field delimiter is legal CSV, even though it closed the wrong field.
     Detected via a parenthesis-balance check on the parsed artifacts_path value and
     recovered only against a closed, evidence-only 3-string vocabulary; anything outside
     that vocabulary degrades to unrecoverable rather than being guessed.

See staging_artifacts/TCK-20260904-WORKING-LOG-CSV-PARSER/investigation.md for the full
evidence trail (exact line numbers, root causes, false-positive sweeps) behind both.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet, Optional

_TOOLS_DIR = Path(__file__).parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from ticket_field_values import WORKFLOW_STATUS_VALUES  # noqa: E402

# Two historical status-column values that appear as real rows in the live file but
# predate WORKFLOW_STATUS_VALUES' canonicalization as a ticket-body enum (confirmed via
# direct csv.reader tally against tickets/working_log.csv, 2026-09-06: AMENDED x2, BACKLOG x2).
STATUS_VOCAB: FrozenSet[str] = WORKFLOW_STATUS_VALUES | {"AMENDED", "BACKLOG"}

HEADER_FIELDS = ("timestamp", "ticket_id", "title", "status", "summary", "artifacts_path")

# Closed, evidence-only vocabulary for Finding 3's reconstruction. Never add a 4th
# fragment or generalize this into a regex/prefix match — an unmatched row must degrade
# to recoverable=False, never a guess (see investigation.md Finding 3 / plan.md Anti-Drift Notes).
QUOTE_DESYNC_SUMMARY_FRAGMENTS = ("N/A (hotfix", "none (hotfix", "none (scope-only epic")


@dataclass
class ParsedRow:
    """One physical data row from tickets/working_log.csv, classified but never rewritten."""

    line_no: int
    raw_fields: list
    classification: str
    recoverable: Optional[bool]
    record: Optional[dict]
    is_duplicate: bool
    duplicate_of_line: Optional[int]
    reason: str


@dataclass
class ParseResult:
    """Aggregate parse output. ambiguous_row_count mirrors
    ticket_stats_report.py::compute_velocity's unparseable_rows convention: a bare,
    always-present int, incremented for any row proven unsafe-as-clean, never omitted,
    never causing a crash or a dropped row."""

    rows: list
    ambiguous_row_count: int
    quote_desync_count: int
    duplicate_row_count: int
    embedded_header_duplicate_count: int


def _find_status_anchor(raw_fields: list) -> Optional[int]:
    """First index i (2 <= i <= len-2) whose value is a known status word. Search starts
    at index 2, not a fixed index 3, because an unescaped comma in title can itself
    absorb extra fields and shift status's true index rightward (confirmed for rows
    3245/3284/3287/3307 in the live file, where status lands at index 4, 4, 5, and 5
    respectively). Returns None if zero or more than one candidate is found — either
    case must degrade to recoverable=False, never a guess."""
    candidates = [
        i
        for i in range(2, len(raw_fields) - 1)
        if raw_fields[i].strip() in STATUS_VOCAB
    ]
    if len(candidates) == 1:
        return candidates[0]
    return None


def _split_trailing_artifacts_path(remaining: list):
    """Decide how many of remaining's trailing raw fields belong to artifacts_path via a
    parenthesis-balance plausibility check, smallest candidate first. Returns (n,
    artifacts_path, summary) or (None, None, None) if neither n=1 nor n=2 is plausible.

    Needed because artifacts_path itself can be the field with the unescaped comma
    (rows 1581/3174: 'none (epic, scope-only)' splits into 'none (epic' + ' scope-only)'),
    not just title/summary — a blind remaining[-1]-alone assumption truncates these two
    rows and corrupts summary with a stray fragment. Verified against all 11 real
    field_count_mismatch rows and cross-checked against every genuinely-complete
    artifacts_path value elsewhere in the file (zero false positives)."""
    n1 = remaining[-1]
    if n1.count("(") == n1.count(")"):
        n = 1
    elif len(remaining) >= 2:
        n2 = ",".join(remaining[-2:])
        if n2.count("(") == n2.count(")"):
            n = 2
        else:
            return None, None, None
    else:
        return None, None, None
    artifacts_path = ",".join(remaining[-n:])
    summary = ",".join(remaining[:-n])
    return n, artifacts_path, summary


def _classify_field_count_mismatch(line_no: int, raw_line: str, raw_fields: list) -> ParsedRow:
    """Finding 1: len(raw_fields) != 6. strict=True is the load-bearing signal separating
    the two irreducibly-ambiguous rows (1511, 3104 — a stray quote not immediately
    followed by the delimiter desyncs csv.reader's quote-tracking state badly enough that
    no rejoin can be trusted) from the 9 mechanically-recoverable rows. Empirically
    verified against all 11 real rows (staging_artifacts/.../plan.md, Step 1) — do not
    substitute a hand-rolled quote-counting heuristic; two such heuristics were tried
    during planning and both misclassified at least one of the 11 real rows."""
    try:
        next(csv.reader([raw_line], strict=True))
        strict_error = None
    except csv.Error as exc:
        strict_error = str(exc)

    if strict_error is not None:
        return ParsedRow(
            line_no=line_no,
            raw_fields=raw_fields,
            classification="field_count_mismatch",
            recoverable=False,
            record=None,
            is_duplicate=False,
            duplicate_of_line=None,
            reason=f"csv.Error under strict=True: {strict_error}",
        )

    anchor = _find_status_anchor(raw_fields)
    if anchor is None:
        return ParsedRow(
            line_no=line_no,
            raw_fields=raw_fields,
            classification="field_count_mismatch",
            recoverable=False,
            record=None,
            is_duplicate=False,
            duplicate_of_line=None,
            reason=f"field-count {len(raw_fields)} != 6, no unambiguous status anchor found",
        )

    remaining = raw_fields[anchor + 1 :]
    n, artifacts_path, summary = _split_trailing_artifacts_path(remaining)
    if n is None:
        return ParsedRow(
            line_no=line_no,
            raw_fields=raw_fields,
            classification="field_count_mismatch",
            recoverable=False,
            record=None,
            is_duplicate=False,
            duplicate_of_line=None,
            reason=(
                f"field-count {len(raw_fields)} != 6, status anchor found at index "
                f"{anchor}, but no plausible artifacts_path trailing-field split (n=1 or n=2)"
            ),
        )

    title = ",".join(raw_fields[2:anchor])
    status = raw_fields[anchor]
    record = {
        "timestamp": raw_fields[0],
        "ticket_id": raw_fields[1],
        "title": title,
        "status": status,
        "summary": summary,
        "artifacts_path": artifacts_path,
    }
    return ParsedRow(
        line_no=line_no,
        raw_fields=raw_fields,
        classification="field_count_mismatch",
        recoverable=True,
        record=record,
        is_duplicate=False,
        duplicate_of_line=None,
        reason=f"field-count {len(raw_fields)} != 6, status anchor found at index {anchor}, rejoin n={n}",
    )


def _classify_quote_desync(line_no: int, raw_fields: list) -> ParsedRow:
    """Finding 3: raw_fields has exactly 6 entries, but artifacts_path (raw_fields[5])
    has unbalanced parens — proof a stray quote immediately followed by the delimiter
    closed the wrong field, absorbing a real comma that should have stayed inside the
    intended (never actually quoted) artifacts_path value. Reconstruction only applies
    against the closed 3-fragment vocabulary; anything else degrades to recoverable=False."""
    summary_candidate = raw_fields[4]
    artifacts_path_candidate = raw_fields[5]
    for fragment in QUOTE_DESYNC_SUMMARY_FRAGMENTS:
        suffix = "," + fragment
        if summary_candidate.endswith(suffix):
            new_summary = summary_candidate[: -len(suffix)]
            new_artifacts_path = fragment + "," + artifacts_path_candidate
            record = {
                "timestamp": raw_fields[0],
                "ticket_id": raw_fields[1],
                "title": raw_fields[2],
                "status": raw_fields[3],
                "summary": new_summary,
                "artifacts_path": new_artifacts_path,
            }
            return ParsedRow(
                line_no=line_no,
                raw_fields=raw_fields,
                classification="quote_desync_masquerading_as_clean",
                recoverable=True,
                record=record,
                is_duplicate=False,
                duplicate_of_line=None,
                reason=(
                    "field-count == 6 but artifacts_path parens unbalanced "
                    f"({artifacts_path_candidate!r}); matched fixed-vocabulary fragment {fragment!r}"
                ),
            )
    return ParsedRow(
        line_no=line_no,
        raw_fields=raw_fields,
        classification="quote_desync_masquerading_as_clean",
        recoverable=False,
        record=None,
        is_duplicate=False,
        duplicate_of_line=None,
        reason=(
            "field-count == 6 but artifacts_path parens unbalanced "
            f"({artifacts_path_candidate!r}); no known fixed-vocabulary fragment matched"
        ),
    )


def parse_working_log(path: Path) -> ParseResult:
    """Round-trip parse tickets/working_log.csv (or any file of the same shape). Returns
    exactly one ParsedRow per physical data row, in file order, never dropped or merged.
    Opens the file read-only; never writes to it."""
    rows = []
    seen_raw_lines = {}

    with open(path, newline="", encoding="utf-8") as f:
        raw_lines = f.readlines()

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # header
        for raw_fields in reader:
            line_no = reader.line_num
            raw_line = raw_lines[line_no - 1]

            if len(raw_fields) == 6:
                stripped = tuple(v.strip() for v in raw_fields)
                if stripped == HEADER_FIELDS:
                    row = ParsedRow(
                        line_no=line_no,
                        raw_fields=raw_fields,
                        classification="embedded_header_duplicate",
                        recoverable=None,
                        record=None,
                        is_duplicate=False,
                        duplicate_of_line=None,
                        reason="6 fields exactly equal the header row's own fields",
                    )
                else:
                    artifacts_path_candidate = raw_fields[5]
                    if artifacts_path_candidate.count("(") != artifacts_path_candidate.count(")"):
                        row = _classify_quote_desync(line_no, raw_fields)
                    else:
                        record = dict(zip(HEADER_FIELDS, raw_fields))
                        row = ParsedRow(
                            line_no=line_no,
                            raw_fields=raw_fields,
                            classification="clean",
                            recoverable=None,
                            record=record,
                            is_duplicate=False,
                            duplicate_of_line=None,
                            reason="field-count == 6, artifacts_path parens balanced",
                        )
            else:
                row = _classify_field_count_mismatch(line_no, raw_line, raw_fields)

            if raw_line in seen_raw_lines:
                row.is_duplicate = True
                row.duplicate_of_line = seen_raw_lines[raw_line]
            else:
                seen_raw_lines[raw_line] = line_no

            rows.append(row)

    ambiguous_row_count = sum(
        1 for r in rows if r.classification not in ("clean", "embedded_header_duplicate")
    )
    quote_desync_count = sum(
        1 for r in rows if r.classification == "quote_desync_masquerading_as_clean"
    )
    duplicate_row_count = sum(1 for r in rows if r.is_duplicate)
    embedded_header_duplicate_count = sum(
        1 for r in rows if r.classification == "embedded_header_duplicate"
    )

    return ParseResult(
        rows=rows,
        ambiguous_row_count=ambiguous_row_count,
        quote_desync_count=quote_desync_count,
        duplicate_row_count=duplicate_row_count,
        embedded_header_duplicate_count=embedded_header_duplicate_count,
    )


if __name__ == "__main__":
    result = parse_working_log(Path("tickets/working_log.csv"))
    print(f"rows={len(result.rows)}")
    print(f"ambiguous_row_count={result.ambiguous_row_count}")
    print(f"quote_desync_count={result.quote_desync_count}")
    print(f"duplicate_row_count={result.duplicate_row_count}")
    print(f"embedded_header_duplicate_count={result.embedded_header_duplicate_count}")
