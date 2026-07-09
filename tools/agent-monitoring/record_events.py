#!/usr/bin/env python3
"""Append a batch of event records to agent-monitoring/events.jsonl."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vocabulary import WORKFLOW_PHASES, infer_workflow, is_known_agent  # noqa: E402

REQUIRED = {"run_id", "seq", "ts", "phase", "agent", "summary", "status"}
VALID_STATUS = {"ok", "failed", "blocked", "skipped"}
EVENTS_FILE = Path("agent-monitoring/events.jsonl")


def validate_record(record: dict) -> list[str]:
    """Return a list of error strings; empty list means the record is valid.

    A field counts as missing if it is absent from the dict OR its value is
    None — a `null` in --data's JSON must fail identically to an absent key.
    """
    errors = []
    missing = {f for f in REQUIRED if f not in record or record[f] is None}
    if missing:
        errors.append(f"missing fields {sorted(missing)}")
    if record.get("status") not in VALID_STATUS:
        errors.append(f"invalid status '{record.get('status')}' — must be one of {VALID_STATUS}")
    return errors


def warn_vocabulary_drift(record: dict) -> None:
    """Print (never raise/reject) a warning for a phase/agent value outside the
    canonical set for the record's inferred workflow. A record whose run_id
    prefix matches no known workflow is skipped silently — this is a warn-only
    signal, never a gate (CLAUDE.md: monitoring write failure must never fail
    the workflow)."""
    workflow = infer_workflow(record.get("run_id", ""))
    if workflow is None:
        return
    if record["phase"] not in WORKFLOW_PHASES.get(workflow, set()):
        print(f"WARNING: unrecognized phase '{record['phase']}' for workflow '{workflow}'", file=sys.stderr)
    if not is_known_agent(workflow, record["agent"]):
        print(f"WARNING: unrecognized agent '{record['agent']}' for workflow '{workflow}'", file=sys.stderr)


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
        record_errors = validate_record(record)
        for err in record_errors:
            errors.append(f"Record {i} ({record.get('run_id', '?')}): {err}")

        # Vocabulary check is skipped for a record that already failed non-null/status
        # validation — don't warn about a None phase/agent the null check has already
        # rejected as an error.
        if not record_errors:
            warn_vocabulary_drift(record)

        # Summary truncation must not run on a record already flagged as missing/null
        # "summary" — record.get("summary", "") would silently swallow a None summary
        # into "", masking the validation error and skipping len() on a NoneType crash
        # only by accident. Guard on "summary" not being in the null/missing set instead.
        if "summary" not in {f for f in REQUIRED if f not in record or record[f] is None}:
            summary = record["summary"]
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
