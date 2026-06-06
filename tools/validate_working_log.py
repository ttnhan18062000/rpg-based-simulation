#!/usr/bin/env python3
"""
Validate tickets/working_log.csv for consistency with tickets/done/.

Checks:
  1. No duplicate ticket IDs in the log.
  2. All tickets in tickets/done/ have a log entry.
  3. No empty fields in any row.

Usage: python3 tools/validate_working_log.py
Exit 0 on success, 1 on any error.
"""

import csv
import sys
from pathlib import Path


def main():
    log_path = Path("tickets/working_log.csv")
    done_dir = Path("tickets/done")

    if not log_path.exists():
        print(f"ERROR: {log_path} not found", file=sys.stderr)
        sys.exit(1)

    if not done_dir.exists():
        print(f"ERROR: {done_dir} not found", file=sys.stderr)
        sys.exit(1)

    errors = []

    with open(log_path, newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            print("ERROR: working_log.csv has no header row", file=sys.stderr)
            sys.exit(1)
        rows = list(reader)

    # 1. Duplicate ticket IDs
    ids = [r.get("ticket_id", "").strip() for r in rows]
    seen = set()
    dupes = set()
    for id_ in ids:
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
    for i, row in enumerate(rows, start=2):  # row 1 is header
        for field, val in row.items():
            if field and (val is None or not val.strip()):
                errors.append(
                    f"Row {i} ({row.get('ticket_id', '?')}): empty field '{field}'"
                )

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(
        f"OK: {len(rows)} log entries, {len(done_tickets)} done tickets — all consistent"
    )


if __name__ == "__main__":
    main()
