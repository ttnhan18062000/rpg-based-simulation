#!/usr/bin/env python3
"""Convenience wrapper for hand-orchestrated ticket closures to record real monitoring coverage
in one call, instead of hand-crafting two separate --data JSON blobs for record_run.py and
record_events.py. (TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE)

Reuses record_run.py's validate_record/compute_duration_s and record_events.py's
validate_record/warn_vocabulary_drift/compute_tool_stats directly -- this wrapper only fills in
the boilerplate fields (run_id, execution_id, provider, ticket_id, agent, seq) that are identical
across every phase of one ticket's closure, so a hand-orchestrating session no longer has to repeat
them by hand for every event.

Usage:
    python3 tools/agent-monitoring/record_hand_orchestrated_closure.py \\
        --ticket-id TCK-20260904-EXAMPLE --tier hotfix \\
        --title "Short ticket title" \\
        --log-summary "One sentence of what was implemented." \\
        --events '[
          {"phase": "Scope", "status": "ok", "summary": "..."},
          {"phase": "Implement", "status": "ok", "summary": "..."},
          {"phase": "Test", "status": "ok", "summary": "..."},
          {"phase": "Parity", "status": "skipped", "summary": "..."},
          {"phase": "Verify", "status": "ok", "summary": "..."},
          {"phase": "Finalize", "status": "ok", "summary": "..."}
        ]'

Each event object only needs `phase`/`status`/`summary` (plus an optional per-event `ts`, `agent`
override) -- `run_id`, `execution_id`, `provider`, `ticket_id`, and `seq` (1-indexed, in array
order) are filled in automatically and shared across the whole batch, matching a single real
`Workflow` run's own shape. `--start-ts`/`--end-ts` default to "now" (matching this project's own
existing hand-orchestrated `runs.jsonl` precedent of using an identical start/end timestamp when
real elapsed wall-clock time wasn't tracked) but accept explicit ISO-8601 values when known.

`tool_call_count`/`cost_proxy_score` are only ever added when real `tools.jsonl` rows are found
for a given (run_id, seq) -- a hand-orchestrating session never has a live per-phase sidecar
during the actual work, so an unattributed phase correctly gets no such keys at all (never a
false `0`/`0.0`).

This call also appends one row to `tickets/working_log.csv` (`--title`/`--log-summary` plus
`--artifacts-path`, which defaults to `stored_artifacts/<ticket-id>` for standard/epic tier or
"none (hotfix — no staging artifacts)" for hotfix) -- do not append that row by hand separately
when using this wrapper, or the ticket will get a duplicate working_log entry.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import record_events  # noqa: E402
import record_run  # noqa: E402
from vocabulary import CANONICAL_TIERS  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from working_log_writer import append_working_log_row  # noqa: E402


def build_records(
    ticket_id: str,
    tier: str,
    final_status: str,
    events: list[dict],
    start_ts: str | None,
    end_ts: str | None,
    workflow: str,
    provider: str,
    default_agent: str,
) -> tuple[dict, list[dict]]:
    """Expands a minimal `events` list (phase/status/summary per entry) into a full run record
    plus a full event-record batch, both matching record_run.py's/record_events.py's own REQUIRED
    field sets exactly -- so the two modules' own `validate_record()` accepts the output unchanged.
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    execution_id = f"{provider}-{ticket_id}-{int(time.time() * 1000)}"

    run_record = {
        "run_id": ticket_id,
        "execution_id": execution_id,
        "provider": provider,
        "ticket_id": ticket_id,
        "start_ts": start_ts or now,
        "end_ts": end_ts or now,
        "workflow": workflow,
        "tier": tier,
        "final_status": final_status,
        "agent_count": len(events),
    }

    event_records = [
        {
            "run_id": ticket_id,
            "execution_id": execution_id,
            "provider": provider,
            "ticket_id": ticket_id,
            "seq": i,
            "phase": e["phase"],
            "agent": e.get("agent", default_agent),
            "status": e["status"],
            "summary": e["summary"],
            "ts": e.get("ts", now),
        }
        for i, e in enumerate(events, start=1)
    ]

    return run_record, event_records


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--ticket-id", required=True)
    parser.add_argument("--tier", required=True, choices=sorted(CANONICAL_TIERS - {"n/a"}))
    parser.add_argument("--events", required=True, help="JSON array of {phase, status, summary, ts?, agent?}")
    parser.add_argument("--final-status", default="DONE")
    parser.add_argument("--start-ts", default=None, help="ISO-8601; defaults to now")
    parser.add_argument("--end-ts", default=None, help="ISO-8601; defaults to now")
    parser.add_argument("--workflow", default="implement-ticket")
    parser.add_argument("--provider", default="claude")
    parser.add_argument("--agent", default="claude", help="Default agent value for events that don't override it")
    parser.add_argument("--title", required=True, help="Ticket title, for tickets/working_log.csv")
    parser.add_argument("--log-summary", required=True, help="One-sentence summary for tickets/working_log.csv")
    parser.add_argument(
        "--artifacts-path",
        default=None,
        help="Defaults to stored_artifacts/<ticket-id> for standard/epic tier, "
        "'none (hotfix — no staging artifacts)' for hotfix",
    )
    args = parser.parse_args()

    try:
        events = json.loads(args.events)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in --events: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(events, list) or not events:
        print("ERROR: --events must be a non-empty JSON array", file=sys.stderr)
        sys.exit(1)

    for i, e in enumerate(events):
        missing = {f for f in ("phase", "status", "summary") if f not in e or e[f] is None}
        if missing:
            print(f"ERROR: events[{i}] missing required fields {sorted(missing)}", file=sys.stderr)
            sys.exit(1)

    run_record, event_records = build_records(
        args.ticket_id, args.tier, args.final_status, events,
        args.start_ts, args.end_ts, args.workflow, args.provider, args.agent,
    )

    run_errors = record_run.validate_record(run_record)
    if run_errors:
        for err in run_errors:
            print(f"ERROR (run record): {err}", file=sys.stderr)
        sys.exit(1)

    event_errors = []
    for i, record in enumerate(event_records):
        for err in record_events.validate_record(record):
            event_errors.append(f"events[{i}] ({record.get('phase')}): {err}")
    if event_errors:
        for err in event_errors:
            print(f"ERROR (event record): {err}", file=sys.stderr)
        sys.exit(1)

    for record in event_records:
        record_events.warn_vocabulary_drift(record)

    run_record["duration_s"] = record_run.compute_duration_s(run_record)

    tool_stats = record_events.compute_tool_stats(event_records, omit_when_unattributed=True)
    for i, record in enumerate(event_records):
        key = (record.get("run_id"), record.get("seq"))
        if key in tool_stats:
            tool_call_count, cost_proxy_score = tool_stats[key]
            event_records[i] = {**record, "tool_call_count": tool_call_count, "cost_proxy_score": cost_proxy_score}

    iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
    runs_file = Path("agent-monitoring/data") / iso_week / "runs.jsonl"
    events_file = Path("agent-monitoring/data") / iso_week / "events.jsonl"
    runs_file.parent.mkdir(parents=True, exist_ok=True)

    from writer import write_line, write_lines  # noqa: E402

    run_ok = write_line(runs_file, json.dumps(run_record, separators=(",", ":")))
    lines = [json.dumps(record, separators=(",", ":")) for record in event_records]
    events_ok = write_lines(events_file, lines)

    if not run_ok:
        print(f"WARNING: run-record append failed for run_id={args.ticket_id}", file=sys.stderr)
    if not events_ok:
        print(f"WARNING: event-record append failed for {len(event_records)} record(s)", file=sys.stderr)

    artifacts_path = args.artifacts_path
    if artifacts_path is None:
        artifacts_path = (
            "none (hotfix — no staging artifacts)"
            if args.tier == "hotfix"
            else f"stored_artifacts/{args.ticket_id}"
        )

    try:
        append_working_log_row(
            run_record["end_ts"], args.ticket_id, args.title, args.final_status, args.log_summary, artifacts_path,
        )
        log_ok = True
    except OSError as e:
        log_ok = False
        print(f"WARNING: working_log.csv append failed: {e}", file=sys.stderr)

    if not log_ok:
        print("WARNING: working_log.csv was not updated — append it manually", file=sys.stderr)

    print(f"DONE: recorded 1 run + {len(event_records)} event record(s) for {args.ticket_id}")


if __name__ == "__main__":
    main()
