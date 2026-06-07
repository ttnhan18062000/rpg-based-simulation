#!/usr/bin/env python3
"""Append a batch of event records to agent-monitoring/events.jsonl."""
import argparse
import json
import sys
from pathlib import Path

REQUIRED = {"run_id", "seq", "ts", "phase", "agent", "summary", "status"}
VALID_STATUS = {"ok", "failed", "blocked", "skipped"}
EVENTS_FILE = Path("agent-monitoring/events.jsonl")


def main():
    parser = argparse.ArgumentParser(description="Append event records to agent-monitoring/events.jsonl")
    parser.add_argument("--data", required=True, help="JSON array of event records (or single object)")
    args = parser.parse_args()

    try:
        data = json.loads(args.data)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    records = data if isinstance(data, list) else [data]

    errors = []
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"Record {i}: not an object")
            continue
        missing = REQUIRED - set(record.keys())
        if missing:
            errors.append(f"Record {i} ({record.get('run_id', '?')}): missing fields {sorted(missing)}")
        if record.get("status") not in VALID_STATUS:
            errors.append(f"Record {i}: invalid status '{record.get('status')}' — must be one of {VALID_STATUS}")
        summary = record.get("summary", "")
        if len(summary) > 200:
            records[i] = {**record, "summary": summary[:197] + "..."}

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if not records:
        print("SKIPPED: no records to write")
        return

    EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(EVENTS_FILE, "a") as f:
        for record in records:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")

    print(f"DONE: appended {len(records)} event record(s)")


if __name__ == "__main__":
    main()
