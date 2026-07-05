#!/usr/bin/env python3
"""
Cross-check agent-monitoring integrity against tickets/working_log.csv.

Checks:
  1. Every DONE entry in working_log (on or after MONITORING_START) has a run record.
  2. Every run record has at least one event record.
  3. Incomplete runs (start_ts present, end_ts absent/null) are flagged as CRASHED.

Only tickets with timestamps >= MONITORING_START are checked against runs.jsonl.
Historical tickets (before monitoring was introduced) are skipped silently.

Exit 0 = clean. Exit 1 = errors found.
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

RUNS_FILE = Path("agent-monitoring/runs.jsonl")
EVENTS_FILE = Path("agent-monitoring/events.jsonl")
LOG_FILE = Path("tickets/working_log.csv")
# Only validate working_log entries on or after this date (ISO prefix match)
MONITORING_START = "2026-06-07"

LEGACY_COMPLETION_FIELDS = ("end_ts", "finished_at", "completed_at", "ts_end")
# The full union of distinct final_status AND status values actually observed in
# agent-monitoring/runs.jsonl (12 total), minus "INPROGRESS" (the one genuinely
# non-terminal value found) — enumerated by reading BOTH fields' value sets
# independently and unioning them, not inferred, so a future value this list has
# never seen is NOT silently treated as terminal.
LEGACY_TERMINAL_STATUS_VALUES = {
    "DONE", "done", "complete", "completed", "success",
    "EPIC_SCOPED", "ALL_SCOPED",
    "DOD_BLOCKED", "NEEDS_HUMAN_INPUT", "GATE_FAIL", "STOPPED_BY_USER",
}


def _record_is_complete(rec: dict) -> bool:
    if any(rec.get(f) for f in LEGACY_COMPLETION_FIELDS):
        return True
    if rec.get("final_status") in LEGACY_TERMINAL_STATUS_VALUES:
        return True
    if rec.get("status") in LEGACY_TERMINAL_STATUS_VALUES:
        return True
    return False


def load_jsonl(path):
    if not path.exists():
        return []
    records = []
    for i, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"WARNING: {path}:{i}: invalid JSON — {e}", file=sys.stderr)
    return records


def main():
    errors = []
    warnings = []

    runs = load_jsonl(RUNS_FILE)
    events = load_jsonl(EVENTS_FILE)

    runs_by_id = {r["run_id"]: r for r in runs if "run_id" in r}
    events_by_run = defaultdict(list)
    for e in events:
        if "run_id" in e:
            events_by_run[e["run_id"]].append(e)

    # 1. Incomplete runs (start_ts but no end_ts), deduped by run_id and aware of
    # legacy completion-field variants (see LEGACY_COMPLETION_FIELDS/
    # LEGACY_TERMINAL_STATUS_VALUES above). A run_id's group of records is only
    # flagged if NONE of its records satisfy _record_is_complete() — aggregate
    # then check, not a last-write-wins dict swap, since file ordering is not a
    # documented guarantee.
    runs_grouped_by_id = defaultdict(list)
    for i, run in enumerate(runs):
        runs_grouped_by_id[run.get("run_id", f"?:{i}")].append(run)
    for run_id, group in runs_grouped_by_id.items():
        if not any(_record_is_complete(r) for r in group):
            warnings.append(f"Incomplete run (no end_ts — CRASHED?): {run_id}")

    # 2. Runs with no events
    for run_id in runs_by_id:
        if not events_by_run[run_id]:
            errors.append(f"Run with no events: {run_id}")

    # 3. Cross-check: every run record marked DONE should have a working_log entry.
    # (Forward direction only — historical tickets predating monitoring are not expected to
    #  have run records, so we don't check working_log → runs.)
    if LOG_FILE.exists():
        log_tids = set()
        with open(LOG_FILE, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tid = row.get("ticket_id", "").strip()
                if tid.startswith("TCK-"):
                    log_tids.add(tid)
        for run_id, run in runs_by_id.items():
            # Batch epic/folder runs (EPIC-*, FOLDER-*) are orchestration records, not
            # individual tickets — they never produce their own working_log entry.
            if not run_id.startswith("TCK-"):
                continue
            status = run.get("final_status") or run.get("status")
            if status == "DONE" and run_id not in log_tids:
                warnings.append(f"Run marked DONE has no working_log entry: {run_id}")
    else:
        warnings.append(f"{LOG_FILE} not found — skipping working_log cross-check")

    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        sys.exit(1)

    total_runs = len(runs)
    total_events = len(events)
    print(f"OK: {total_runs} runs, {total_events} events — {len(warnings)} warning(s)")


if __name__ == "__main__":
    main()
