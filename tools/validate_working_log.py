#!/usr/bin/env python3
"""
Validate tickets/working_log.csv for consistency with tickets/done/.

Checks:
  1. No duplicate ticket IDs in the log.
  2. All tickets in tickets/done/ have a log entry.
  3. No empty fields in any row.

Row loading is tolerant (see tools/working_log_parser.py): malformed rows are
classified explicitly rather than silently mis-mapped by a bare DictReader, and the
ambiguous-row count is surfaced as a first-class signal (mirrors
tools/ticket_stats_report.py::compute_velocity's unparseable_rows convention).

Usage: python3 tools/validate_working_log.py
Exit 0 on success, 1 on any error.
"""

import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from working_log_parser import parse_working_log  # noqa: E402


def run_validation(log_path: Path, done_dir: Path) -> dict:
    """Run the three pre-existing checks (duplicate ticket IDs, missing done/ entries,
    empty fields) against the tolerant parser's clean + recovered records, and surface
    the ambiguous/duplicate row counts as first-class signals. Check logic itself is
    unchanged from the prior bare-DictReader implementation — only the row source
    changed."""
    errors = []

    parse_result = parse_working_log(log_path)
    kept_rows = [r for r in parse_result.rows if r.record is not None]
    rows = [r.record for r in kept_rows]

    # 1. Duplicate ticket IDs. Exclude rows the tolerant parser already flagged
    # is_duplicate=True (an exact-duplicate physical line, e.g. from a squash-merge
    # whole-block duplication -- see TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP)
    # -- those are a known, tracked defect class, not a genuine reopened/duplicate ticket.
    # Checks 2 and 3 below deliberately keep using the unfiltered `ids`/`kept_rows` — this
    # exclusion applies to the duplicate-ticket-ID scan only.
    ids = [r.get("ticket_id", "").strip() for r in rows]
    non_duplicate_ids = [
        r.record.get("ticket_id", "").strip() for r in kept_rows if not r.is_duplicate
    ]
    seen = set()
    dupes = set()
    for id_ in non_duplicate_ids:
        if id_ in seen:
            dupes.add(id_)
        seen.add(id_)
    if dupes:
        errors.append(f"Duplicate ticket IDs in working_log.csv: {sorted(dupes)}")

    # 2. Done tickets missing log entries
    logged_ids = {id_ for id_ in ids if id_}
    done_tickets = {f.stem for f in done_dir.glob("*.md")}
    missing = done_tickets - logged_ids
    if missing:
        errors.append(
            f"{len(missing)} ticket(s) in done/ with no working_log entry:\n"
            + "\n".join(f"  {t}" for t in sorted(missing))
        )

    # 3. Empty fields
    for parsed_row in kept_rows:
        row = parsed_row.record
        for field, val in row.items():
            if field and (val is None or not val.strip()):
                errors.append(
                    f"Row {parsed_row.line_no} ({row.get('ticket_id', '?')}): empty field '{field}'"
                )

    return {
        "errors": errors,
        "row_count": len(rows),
        "done_count": len(done_tickets),
        "ambiguous_row_count": parse_result.ambiguous_row_count,
        "duplicate_row_count": parse_result.duplicate_row_count,
    }


def main():
    log_path = Path("tickets/working_log.csv")
    done_dir = Path("tickets/done")

    if not log_path.exists():
        print(f"ERROR: {log_path} not found", file=sys.stderr)
        sys.exit(1)

    if not done_dir.exists():
        print(f"ERROR: {done_dir} not found", file=sys.stderr)
        sys.exit(1)

    result = run_validation(log_path, done_dir)

    if result["errors"]:
        for e in result["errors"]:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(
        f"OK: {result['row_count']} log entries, {result['done_count']} done tickets — "
        f"all consistent (ambiguous_row_count={result['ambiguous_row_count']}, "
        f"duplicate_row_count={result['duplicate_row_count']})"
    )


if __name__ == "__main__":
    main()
