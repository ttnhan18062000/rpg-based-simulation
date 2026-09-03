#!/usr/bin/env python3
"""Append a run record to agent-monitoring/data/<ISO-week>/runs.jsonl."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from writer import write_line  # noqa: E402

REQUIRED = {"run_id", "start_ts", "workflow", "tier", "final_status", "agent_count"}


def validate_record(record: dict) -> list[str]:
    """Return a list of error strings; empty list means the record is valid.

    A field counts as missing if it is absent from the dict OR its value is
    None — a `null` in --data's JSON must fail identically to an absent key.
    """
    missing = {f for f in REQUIRED if f not in record or record[f] is None}
    if missing:
        return [f"Missing required fields: {sorted(missing)}"]
    return []


def compute_duration_s(record: dict) -> int | None:
    """Wall-clock seconds from start_ts to end_ts, or None if end_ts is absent
    or the pair is invalid (end before start).

    end_ts is not in REQUIRED (schema.md documents it nullable for crashed
    runs), so this must degrade to None rather than error when it's missing.
    Always overrides any caller-supplied duration_s — the point of computing
    it here is to stop depending on caller-supplied correctness.

    A negative result (end_ts earlier than start_ts) means at least one of
    the two timestamps was fabricated/estimated rather than really captured
    (TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG confirmed this
    happens when a caller hand-types start_ts under a wrong date assumption
    while end_ts is a real `date -u` capture) — degrading to None here,
    rather than silently storing a negative duration, surfaces the caller's
    own bad input instead of feeding it straight into the dashboard's
    Progress Timeline rendering.
    """
    end_ts = record.get("end_ts")
    if not end_ts:
        return None
    start = datetime.fromisoformat(record["start_ts"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_ts.replace("Z", "+00:00"))
    delta_s = int((end - start).total_seconds())
    if delta_s < 0:
        print(
            f"WARNING: end_ts ({end_ts}) is earlier than start_ts "
            f"({record['start_ts']}) — duration_s set to null instead of "
            f"{delta_s}. Re-check start_ts.",
            file=sys.stderr,
        )
        return None
    return delta_s


def main():
    parser = argparse.ArgumentParser(description="Append a run record to agent-monitoring/data/<ISO-week>/runs.jsonl")
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

    record["duration_s"] = compute_duration_s(record)

    iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
    runs_file = Path("agent-monitoring/data") / iso_week / "runs.jsonl"
    runs_file.parent.mkdir(parents=True, exist_ok=True)
    ok = write_line(runs_file, json.dumps(record, separators=(",", ":")))
    if not ok:
        print(
            f"WARNING: append failed for run_id={record['run_id']}, "
            f"see agent-monitoring/data/{iso_week}/.writer_health.jsonl",
            file=sys.stderr,
        )

    print(f"DONE: appended run record for {record['run_id']} (status={record['final_status']})")


if __name__ == "__main__":
    main()
