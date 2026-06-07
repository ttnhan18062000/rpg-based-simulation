#!/usr/bin/env python3
"""
Query agent-monitoring/events.jsonl and runs.jsonl.

Usage:
  python3 tools/agent-monitoring/query.py [filters]
  python3 tools/agent-monitoring/query.py --agent investigator --status failed
  python3 tools/agent-monitoring/query.py --run-id TCK-20260607-...
  python3 tools/agent-monitoring/query.py --phase Review --days 14
  python3 tools/agent-monitoring/query.py --summary-contains "parity gap"
  python3 tools/agent-monitoring/query.py --runs           # query runs instead of events
"""
import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


RUNS_FILE = Path("agent-monitoring/runs.jsonl")
EVENTS_FILE = Path("agent-monitoring/events.jsonl")
COL_WIDTH = 22


def load_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def trunc(s, n):
    s = str(s) if s is not None else ""
    return s[:n - 1] + "…" if len(s) > n else s.ljust(n)


def cutoff_ts(days):
    if days is None:
        return None
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def print_events(events):
    if not events:
        print("No matching events.")
        return
    header = f"{'run_id':<38} {'seq':>3} {'ts':<22} {'phase':<12} {'agent':<22} {'st':>7}  summary"
    print(header)
    print("-" * 120)
    for e in events:
        print(
            f"{trunc(e.get('run_id',''), 38)} "
            f"{str(e.get('seq','')):>3} "
            f"{trunc(e.get('ts',''), 22)} "
            f"{trunc(e.get('phase',''), 12)} "
            f"{trunc(e.get('agent',''), 22)} "
            f"{trunc(e.get('status',''), 7)}  "
            f"{e.get('summary','')}"
        )
    print(f"\n{len(events)} event(s)")


def print_runs(runs):
    if not runs:
        print("No matching runs.")
        return
    header = f"{'run_id':<38} {'start_ts':<22} {'tier':<10} {'status':<22} {'agents':>6} {'dur_s':>6}"
    print(header)
    print("-" * 110)
    for r in runs:
        print(
            f"{trunc(r.get('run_id',''), 38)} "
            f"{trunc(r.get('start_ts',''), 22)} "
            f"{trunc(r.get('tier',''), 10)} "
            f"{trunc(r.get('final_status',''), 22)} "
            f"{str(r.get('agent_count','')):>6} "
            f"{str(r.get('duration_s','')):>6}"
        )
    print(f"\n{len(runs)} run(s)")


def main():
    parser = argparse.ArgumentParser(description="Query agent monitoring records")
    parser.add_argument("--agent", help="Filter by agent name")
    parser.add_argument("--status", help="Filter by status (ok/failed/blocked/skipped or DONE/TESTS_FAILED/...)")
    parser.add_argument("--phase", help="Filter by workflow phase")
    parser.add_argument("--run-id", help="Filter by run_id (exact match)")
    parser.add_argument("--days", type=int, help="Only records from the last N days")
    parser.add_argument("--summary-contains", help="Filter events where summary contains this string")
    parser.add_argument("--runs", action="store_true", help="Query runs instead of events")
    args = parser.parse_args()

    cut = cutoff_ts(args.days)

    if args.runs:
        records = load_jsonl(RUNS_FILE)
        if args.run_id:
            records = [r for r in records if r.get("run_id") == args.run_id]
        if args.status:
            records = [r for r in records if r.get("final_status") == args.status]
        if cut:
            records = [r for r in records if (r.get("start_ts") or "") >= cut]
        print_runs(records)
    else:
        records = load_jsonl(EVENTS_FILE)
        if args.agent:
            records = [e for e in records if e.get("agent") == args.agent]
        if args.status:
            records = [e for e in records if e.get("status") == args.status]
        if args.phase:
            records = [e for e in records if e.get("phase") == args.phase]
        if args.run_id:
            records = [e for e in records if e.get("run_id") == args.run_id]
        if args.summary_contains:
            records = [e for e in records if args.summary_contains.lower() in e.get("summary", "").lower()]
        if cut:
            records = [e for e in records if (e.get("ts") or "") >= cut]
        print_events(records)


if __name__ == "__main__":
    main()
