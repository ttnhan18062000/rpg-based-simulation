#!/usr/bin/env python3
"""
Query the agent-monitoring SQLite index (agent-monitoring-index/monitoring.db),
built from agent-monitoring/{runs,events}.jsonl by build_index.py.

Usage:
  python3 tools/agent-monitoring/query.py [filters]
  python3 tools/agent-monitoring/query.py --agent investigator --status failed
  python3 tools/agent-monitoring/query.py --run-id TCK-20260607-...
  python3 tools/agent-monitoring/query.py --phase Review --days 14
  python3 tools/agent-monitoring/query.py --summary-contains "parity gap"
  python3 tools/agent-monitoring/query.py --runs           # query runs instead of events
  python3 tools/agent-monitoring/query.py --db-path path/to/monitoring.db

Requires the index to exist first: `make agent-monitoring-index`.
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


DEFAULT_DB_PATH = Path("agent-monitoring-index/monitoring.db")
COL_WIDTH = 22


def open_index(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        print(
            f"No agent-monitoring index found at {db_path} — run `make agent-monitoring-index` first.",
            file=sys.stderr,
        )
        sys.exit(1)
    return sqlite3.connect(str(db_path))


def load_runs_from_index(conn: sqlite3.Connection) -> list:
    cursor = conn.execute("SELECT resolved_status, raw_json FROM runs ORDER BY id")
    records = []
    for resolved_status, raw_json in cursor:
        record = json.loads(raw_json)
        record["_resolved_status"] = resolved_status
        records.append(record)
    return records


def load_events_from_index(conn: sqlite3.Connection) -> list:
    cursor = conn.execute("SELECT raw_json FROM events ORDER BY id")
    return [json.loads(row[0]) for row in cursor]


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


def filter_runs(records, args):
    cut = cutoff_ts(args.days)
    if args.run_id:
        records = [r for r in records if r.get("run_id") == args.run_id]
    if args.status:
        # TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE: compare against the SQL
        # resolved_status column (final_status-or-legacy-status fallback), not raw
        # final_status — fixes a pre-migration bug where legacy-schema runs with only
        # a bare `status` field were silently excluded from `--runs --status` results.
        records = [r for r in records if r.get("_resolved_status") == args.status]
    if cut:
        records = [r for r in records if (r.get("start_ts") or "") >= cut]
    return records


def filter_events(records, args):
    cut = cutoff_ts(args.days)
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
    return records


def build_parser():
    parser = argparse.ArgumentParser(description="Query agent monitoring records")
    parser.add_argument("--agent", help="Filter by agent name")
    parser.add_argument("--status", help="Filter by status (ok/failed/blocked/skipped or DONE/TESTS_FAILED/...)")
    parser.add_argument("--phase", help="Filter by workflow phase")
    parser.add_argument("--run-id", help="Filter by run_id (exact match)")
    parser.add_argument("--days", type=int, help="Only records from the last N days")
    parser.add_argument("--summary-contains", help="Filter events where summary contains this string")
    parser.add_argument("--runs", action="store_true", help="Query runs instead of events")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="Path to the agent-monitoring SQLite index")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    conn = open_index(Path(args.db_path))
    if args.runs:
        records = load_runs_from_index(conn)
        conn.close()
        print_runs(filter_runs(records, args))
    else:
        records = load_events_from_index(conn)
        conn.close()
        print_events(filter_events(records, args))


if __name__ == "__main__":
    main()
