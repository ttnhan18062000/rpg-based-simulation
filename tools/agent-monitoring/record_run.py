#!/usr/bin/env python3
"""Append a run record to agent-monitoring/runs.jsonl."""
import argparse
import json
import sys
from pathlib import Path

REQUIRED = {"run_id", "start_ts", "workflow", "tier", "final_status"}
RUNS_FILE = Path("agent-monitoring/runs.jsonl")


def validate_record(record: dict) -> list[str]:
    """Return a list of error strings; empty list means the record is valid.

    A field counts as missing if it is absent from the dict OR its value is
    None — a `null` in --data's JSON must fail identically to an absent key.
    """
    missing = {f for f in REQUIRED if f not in record or record[f] is None}
    if missing:
        return [f"Missing required fields: {sorted(missing)}"]
    return []


def main():
    parser = argparse.ArgumentParser(description="Append a run record to agent-monitoring/runs.jsonl")
    parser.add_argument("--data", required=True, help="JSON object to append")
    args = parser.parse_args()

    try:
        record = json.loads(args.data)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(record, dict):
        print("ERROR: --data must be a JSON object", file=sys.stderr)
        sys.exit(1)

    errors = validate_record(record)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)

    RUNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RUNS_FILE, "a") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")

    print(f"DONE: appended run record for {record['run_id']} (status={record['final_status']})")


if __name__ == "__main__":
    main()
