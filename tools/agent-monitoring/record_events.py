#!/usr/bin/env python3
"""Append a batch of event records to agent-monitoring/data/<ISO-week>/events.jsonl."""
import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cost_proxy import compute_cost_proxy_score  # noqa: E402
from vocabulary import WORKFLOW_PHASES, infer_workflow, is_known_agent  # noqa: E402
from writer import write_lines  # noqa: E402

REQUIRED = {"run_id", "seq", "ts", "phase", "agent", "summary", "status"}
VALID_STATUS = {"ok", "failed", "blocked", "skipped"}


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


def compute_tool_stats(
    records: list[dict], *, omit_when_unattributed: bool = False
) -> dict[tuple, tuple[int, float]]:
    """Deterministically compute {(run_id, seq): (tool_call_count, cost_proxy_score)}
    from real agent-monitoring/data/*/tools.jsonl rows (every ISO-week folder,
    sorted, concatenated before grouping), for every (run_id, seq) pair in
    `records` whose run_id belongs to the 'implement-ticket' workflow.

    Reads the union of every week folder's tools.jsonl rather than just the
    current week's — a paused/resumed run's tool-call rows can land in an
    earlier week than the event being written now (see
    TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION). This is safe against
    double-counting because (run_id, seq) is globally unique across weeks.

    Mirrors record_run.py's compute_duration_s precedent: computed here, at write
    time, from ground truth — never trusts a caller-supplied value. Only
    'implement-ticket' run_ids are computed (that's the only workflow whose
    Scope-through-Finalize call sites write a live .claude/current_run sidecar per
    phase, giving this a real (run_id, seq) -> tool-call-group ground truth to
    read); every other workflow's records are left untouched by the caller in
    main() below — implement-epic/create-tickets never register a sidecar per
    agent call, so their tool_call_count/cost_proxy_score stay absent, as
    documented.

    `omit_when_unattributed`: by default (False), a key with zero matching
    tools.jsonl rows still gets (0, 0.0) — correct for this module's own CLI,
    where an implement-ticket phase always has a live sidecar, so "zero rows"
    means "confirmed zero calls" (see test_cost_proxy_score_absent_when_no_tools_jsonl_exists).
    Pass True for a caller whose events never had a live sidecar during the
    real work (e.g. record_hand_orchestrated_closure.py) — there, "zero rows"
    means "no attribution data was ever possible," not "confirmed zero," so the
    key is omitted entirely rather than reported as a false zero.
    """
    wanted = {
        (r.get("run_id"), r.get("seq"))
        for r in records
        if infer_workflow(r.get("run_id", "")) == "implement-ticket" and r.get("seq") is not None
    }
    if not wanted:
        return {}

    rows_by_key: dict[tuple, list[dict]] = defaultdict(list)
    for tools_path in sorted(Path(".").glob("agent-monitoring/data/*/tools.jsonl")):
        for line in tools_path.read_text().splitlines():
            if not line:
                continue
            row = json.loads(line)
            key = (row.get("run_id"), row.get("seq"))
            if key in wanted:
                rows_by_key[key].append(row)

    return {
        key: (len(rows_by_key[key]), compute_cost_proxy_score(rows_by_key[key]))
        for key in wanted
        if not omit_when_unattributed or rows_by_key[key]
    }


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
    parser = argparse.ArgumentParser(description="Append event records to agent-monitoring/data/<ISO-week>/events.jsonl")
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

    # Deterministic tool_call_count/cost_proxy_score, computed here from real tools.jsonl
    # ground truth — always overrides any caller-supplied value for implement-ticket
    # records (mirrors record_run.py's compute_duration_s precedent). Other workflows'
    # records are left exactly as passed through (no key added if not already present).
    tool_stats = compute_tool_stats(records)
    for i, record in enumerate(records):
        key = (record.get("run_id"), record.get("seq"))
        if key in tool_stats:
            tool_call_count, cost_proxy_score = tool_stats[key]
            records[i] = {**record, "tool_call_count": tool_call_count, "cost_proxy_score": cost_proxy_score}

    # iso_week is computed once per batch, not once per record: write_lines() takes one
    # target_path for the whole batch, so a batch straddling a UTC-midnight-on-Sunday ISO
    # week boundary lands entirely in whichever week "now" resolved to at this point — the
    # only interpretation compatible with write_lines' single-target batch-contiguity contract.
    iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
    events_file = Path("agent-monitoring/data") / iso_week / "events.jsonl"
    events_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, separators=(",", ":")) for record in records]
    ok = write_lines(events_file, lines)
    if not ok:
        print(
            f"WARNING: append failed for {len(records)} event record(s), "
            f"see agent-monitoring/data/{iso_week}/.writer_health.jsonl",
            file=sys.stderr,
        )

    print(f"DONE: appended {len(records)} event record(s)")


if __name__ == "__main__":
    main()
