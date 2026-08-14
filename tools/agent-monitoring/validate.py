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
import argparse
import csv
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vocabulary import CANONICAL_TIERS, WORKFLOW_PHASES, infer_workflow, is_known_agent  # noqa: E402

LOG_FILE = Path("tickets/working_log.csv")
# Only validate working_log entries on or after this date (ISO prefix match)
MONITORING_START = "2026-06-07"

DEFAULT_DB_PATH = Path("agent-monitoring-index/monitoring.db")


def open_index(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        print(
            f"No agent-monitoring index found at {db_path} — run `make agent-monitoring-index` first.",
            file=sys.stderr,
        )
        sys.exit(1)
    return sqlite3.connect(str(db_path))


def load_runs_from_index(conn: sqlite3.Connection) -> list:
    cursor = conn.execute("SELECT raw_json FROM runs ORDER BY id")
    return [json.loads(row[0]) for row in cursor]


def load_events_from_index(conn: sqlite3.Connection) -> list:
    cursor = conn.execute("SELECT raw_json FROM events ORDER BY id")
    return [json.loads(row[0]) for row in cursor]


def load_tools_from_index(conn: sqlite3.Connection) -> list:
    cursor = conn.execute("SELECT raw_json FROM tools ORDER BY id")
    return [json.loads(row[0]) for row in cursor]


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


# Run-record fields checked for null-required-field drift. A subset of
# record_run.py's own REQUIRED set — "run_id" and "start_ts" are excluded
# because a null run_id/start_ts already breaks the runs_by_id/events_by_run
# joins elsewhere in this file, well before a drift report would matter.
RUN_REQUIRED_FIELDS_FOR_DRIFT = ("workflow", "tier", "final_status")


def compute_drift_report(runs: list, events: list) -> str:
    """Read-only vocabulary/null-field drift report, mirroring
    generate_retro.py's generate(runs, events, label) -> str shape for
    testability. Never gates anything — validate.py's exit-code contract
    (errors -> exit 1, else exit 0 regardless of warnings) is unaffected by
    what this function returns; it is purely additive reporting."""
    null_field_counts = Counter()
    for r in runs:
        for field in RUN_REQUIRED_FIELDS_FOR_DRIFT:
            if r.get(field) is None:
                null_field_counts[field] += 1

    phase_drift = Counter()
    agent_drift = Counter()
    for e in events:
        workflow = infer_workflow(e.get("run_id") or "")
        if workflow is None:
            continue
        phase = e.get("phase")
        if phase is not None and phase not in WORKFLOW_PHASES.get(workflow, set()):
            phase_drift[phase] += 1
        agent = e.get("agent")
        if agent is not None and not is_known_agent(workflow, agent):
            agent_drift[agent] += 1

    tier_drift = Counter()
    for r in runs:
        tier = r.get("tier")
        if tier is not None and tier not in CANONICAL_TIERS:
            tier_drift[tier] += 1

    lines = ["--- Vocabulary / Null-Field Drift Report ---", ""]
    lines.append("Null required fields (runs.jsonl):")
    for field in RUN_REQUIRED_FIELDS_FOR_DRIFT:
        lines.append(f"  {field}: {null_field_counts.get(field, 0)}")
    lines.append("")

    lines.append("Non-canonical phase values (events.jsonl):")
    if phase_drift:
        for value, count in phase_drift.most_common():
            lines.append(f"  '{value}': {count}")
    else:
        lines.append("  none")
    lines.append("")

    lines.append("Non-canonical agent values (events.jsonl):")
    if agent_drift:
        for value, count in agent_drift.most_common():
            lines.append(f"  '{value}': {count}")
    else:
        lines.append("  none")
    lines.append("")

    lines.append("Non-canonical tier values (runs.jsonl):")
    if tier_drift:
        for value, count in tier_drift.most_common():
            lines.append(f"  '{value}': {count}")
    else:
        lines.append("  none")

    return "\n".join(lines)


def compute_tool_count_drift_report(events: list, tools: list) -> str:
    """Read-only cross-check of events.jsonl's recorded tool_call_count against tools.jsonl
    ground truth, grouped by (run_id, seq) — mirrors compute_drift_report's shape (pure function,
    never gates anything, purely additive reporting).

    TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION: a direct empirical audit found ~35% of
    historical events had a tool_call_count that didn't match tools.jsonl, traced to two now-fixed
    mechanisms (Scope-phase sidecar gap; writeMonitoring's own calls polluting the last phase's
    count before its sidecar-clear ran). This report exists so a future recurrence of either
    mechanism — or a new one — surfaces automatically instead of requiring another manual audit.
    Historical drift from before the fix is expected and not itself actionable; this report is
    most meaningful when scoped to runs after the fix landed.
    """
    actual_counts = Counter()
    for t in tools:
        run_id = t.get("run_id")
        seq = t.get("seq")
        if run_id and seq is not None:
            actual_counts[(run_id, seq)] += 1

    mismatches = []
    checked = 0
    for e in events:
        run_id = e.get("run_id")
        seq = e.get("seq")
        recorded = e.get("tool_call_count")
        if run_id is None or seq is None or recorded is None:
            continue
        checked += 1
        actual = actual_counts.get((run_id, seq), 0)
        if recorded != actual:
            mismatches.append((run_id, seq, recorded, actual))

    lines = ["--- Tool Call Count Drift Report ---", ""]
    lines.append(f"Events checked (non-null tool_call_count, run_id+seq present): {checked}")
    lines.append(f"Mismatches (recorded != actual tools.jsonl row count): {len(mismatches)}")
    if mismatches:
        lines.append("")
        lines.append("Sample mismatches (run_id, seq, recorded, actual):")
        for run_id, seq, recorded, actual in mismatches[:20]:
            lines.append(f"  {run_id} seq={seq}: recorded={recorded} actual={actual}")
        if len(mismatches) > 20:
            lines.append(f"  ... and {len(mismatches) - 20} more")
    return "\n".join(lines)


def compute_multi_invocation_collision_report(events: list) -> str:
    """Read-only detector for TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION's specific
    mechanism: a run_id with more than one phase="Scope", seq=1 event is the empirical signature
    of a resumed session whose seq numbering restarted at 1 and aliased onto a prior session's
    (run_id, seq) tools.jsonl buckets (the exact signature this ticket's own investigation used to
    find the 8 affected run_ids in the live corpus). Distinct from
    compute_tool_count_drift_report's recorded-vs-actual mismatch detection: that function detects
    THAT a count disagrees; this one flags the specific multi-invocation cause."""
    scope_seq1_counts = Counter()
    for e in events:
        if e.get("phase") == "Scope" and e.get("seq") == 1 and e.get("run_id"):
            scope_seq1_counts[e["run_id"]] += 1

    collided = {run_id: count for run_id, count in scope_seq1_counts.items() if count > 1}

    lines = ["--- Multi-Invocation Seq Collision Report ---", ""]
    lines.append(
        f"run_ids with more than one Scope/seq=1 event (resume-collision candidates): {len(collided)}"
    )
    if collided:
        lines.append("")
        for run_id, count in sorted(collided.items()):
            lines.append(f"  {run_id}: {count} Scope/seq=1 events")
    return "\n".join(lines)


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


def build_parser():
    parser = argparse.ArgumentParser(
        description="Cross-check agent-monitoring integrity against tickets/working_log.csv"
    )
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="Path to the agent-monitoring SQLite index")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    errors = []
    warnings = []

    conn = open_index(Path(args.db_path))
    runs = load_runs_from_index(conn)
    events = load_events_from_index(conn)
    tools = load_tools_from_index(conn)
    conn.close()

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

    print(compute_drift_report(runs, events))
    print()
    print(compute_tool_count_drift_report(events, tools))
    print()
    print(compute_multi_invocation_collision_report(events))

    total_runs = len(runs)
    total_events = len(events)
    print(f"OK: {total_runs} runs, {total_events} events — {len(warnings)} warning(s)")


if __name__ == "__main__":
    main()
