#!/usr/bin/env python3
"""
Cross-check agent-monitoring integrity against agent-working/tickets/working_log.csv.

Checks:
  1. Every run record has at least one event record (ERROR -- gates the exit code).
  2. Every DONE entry in working_log (on or after MONITORING_START) has a run record (WARNING --
     informational only, never affects the exit code).
  3. Incomplete runs (start_ts present, end_ts absent/null) are flagged as CRASHED (WARNING).

Only ERRORS (check 1) cause a non-zero exit; WARNINGS (checks 2-3) are printed but never gate this
script's own exit code -- TCK-20260915-MONITORING-INTEGRITY-BACKLOG corrected a prior
investigation's mistaken belief that this gate's persistent redness was caused by warning-class
working_log gaps; the real, sole cause was check 1's ERROR class (see EVENTS_REQUIRED_START below).

Only tickets with timestamps >= MONITORING_START are checked against runs.jsonl.
Historical tickets (before monitoring was introduced) are skipped silently.

Exit 0 = clean. Exit 1 = errors found.
"""
import argparse
import csv
import json
from datetime import datetime
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vocabulary import CANONICAL_TIERS, PATH_REASONS, SKIP_REASONS, WORKFLOW_PHASES, infer_workflow, is_known_agent  # noqa: E402
from monitoring_shard_paths import shard_paths  # noqa: E402
import gate_verdicts  # noqa: E402
_REPO_ROOT_STR = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT_STR not in sys.path:
    sys.path.append(_REPO_ROOT_STR)
from tools.agent_working_paths import AGENT_MONITORING, AGENT_MONITORING_INDEX, TICKETS  # noqa: E402

LOG_FILE = TICKETS / "working_log.csv"
# Only validate working_log entries on or after this date (ISO prefix match)
MONITORING_START = "2026-06-07"

# TCK-20260915-MONITORING-INTEGRITY-BACKLOG: "Run with no events" is an ERROR (causes exit 1,
# unlike the WARNING-only checks below) -- and it was the actual, undocumented reason this gate
# stayed permanently red, not the working_log-cross-check warnings a prior investigation mistakenly
# named as the cause (warnings never affect the exit code; see the `if errors: sys.exit(1)` check
# below, which never inspects `warnings`). All 6 real instances found in the corpus as of
# 2026-09-15 are legacy batch (FOLDER-*/EPIC-*) or early individual-ticket runs written before
# events.jsonl tracking was consistently wired for every workflow shape -- there is no way to
# retroactively reconstruct per-phase event data for work already completed, so backfilling is not
# an option. All 6 predate 2026-07-08 (latest: 2026-07-07). Excluding runs starting before this
# date, mirroring MONITORING_START's own established pattern, keeps a genuinely NEW no-events
# defect (a real regression, not a schema-era gap) from being silently masked -- it only ever
# suppresses runs starting before the fix for a problem that stopped recurring, and any run whose
# own start timestamp can't be determined is NOT excluded (conservative default: surface it rather
# than assume it's historical).
EVENTS_REQUIRED_START = "2026-07-08"

# Legacy start-timestamp field name variants actually observed across runs.jsonl's several schema
# generations (mirrors LEGACY_COMPLETION_FIELDS's own multi-field-name pattern below) -- checked in
# this order since `start_ts` is the current, canonical field name.
LEGACY_START_TS_FIELDS = ("start_ts", "ts", "started_at")

DEFAULT_DB_PATH = AGENT_MONITORING_INDEX / "monitoring.db"


def _run_effective_start_ts(run: dict):
    """The run's own start timestamp under whichever legacy field name it was written with, or
    None if none of them hold a non-empty string."""
    for field in LEGACY_START_TS_FIELDS:
        value = run.get(field)
        if isinstance(value, str) and value:
            return value
    return None


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
# agent-working/agent-monitoring/runs.jsonl (12 total), minus "INPROGRESS" (the one genuinely
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


def compute_vocabulary_drift_counts(runs: list, events: list) -> dict:
    """Structured (non-string) core of compute_drift_report -- extracted by
    TCK-20260915-MONITORING-ANOMALY-VALIDATOR so a ratchet check can consume raw Counters
    directly instead of parsing this function's own formatted text report. Returns
    {"null_field_counts", "phase_drift", "agent_drift", "tier_drift"}, each a `Counter`."""
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

    return {
        "null_field_counts": null_field_counts,
        "phase_drift": phase_drift,
        "agent_drift": agent_drift,
        "tier_drift": tier_drift,
    }


def compute_drift_report(runs: list, events: list) -> str:
    """Read-only vocabulary/null-field drift report, mirroring
    generate_retro.py's generate(runs, events, label) -> str shape for
    testability. Never gates anything — validate.py's exit-code contract
    (errors -> exit 1, else exit 0 regardless of warnings) is unaffected by
    what this function returns; it is purely additive reporting."""
    counts = compute_vocabulary_drift_counts(runs, events)
    null_field_counts = counts["null_field_counts"]
    phase_drift = counts["phase_drift"]
    agent_drift = counts["agent_drift"]
    tier_drift = counts["tier_drift"]

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


def load_jsonl_with_line_count(path) -> "tuple[list, int]":
    """Same parsing as load_jsonl, but also returns the non-blank line count derived from the
    SAME single `path.read_text()` call -- lets a caller compare "rows produced" against "raw
    lines present" without a second, independent read of a live, concurrently-written file
    (TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS item 3: two tests in
    test_agent_tool_usage_baseline.py each read agent-working/agent-monitoring/data/*/tools.jsonl twice --
    once via their own ad-hoc `path.read_text().splitlines()` count, once via load_data_glob's
    own separate read -- racing any concurrent session's PostToolUse hook append in between)."""
    if not path.exists():
        return [], 0
    non_blank_lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    records = []
    for i, line in enumerate(non_blank_lines, 1):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"WARNING: {path}:{i}: invalid JSON — {e}", file=sys.stderr)
    return records, len(non_blank_lines)


def load_jsonl(path):
    records, _ = load_jsonl_with_line_count(path)
    return records


def load_data_glob_with_line_count(data_dir: Path, source: str) -> "tuple[list, int]":
    """Same shard-glob concatenation as load_data_glob, but also returns the total non-blank
    line count across all shards, derived from the same per-shard reads (see
    load_jsonl_with_line_count's own docstring for why this matters).

    Path discovery delegates to the shared `monitoring_shard_paths.shard_paths()` resolver
    (TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION), globbing both the bare
    `<week>/<source>.jsonl` shape and the per-identifier `<week>/<id>.<source>.jsonl` shape
    (per-ticket, historically, and per-PR/branch since TCK-20260925-MONITORING-SHARD-PER-PR-KEY-
    FIX) -- confirmed by direct execution that the bare-only glob silently loaded 0 records for a
    real per-branch file before `TCK-20260925-MONITORING-STALE-READ-PATH-SWEEP` first widened
    this, affecting every one of this function's many consumers (`done_checker_static.py`,
    `monitoring_anomaly_validator.py`, `duplicate_run_record_check.py`,
    `tool_call_count_mismatch_check.py`, and others). NOTE: despite this docstring's own prior
    claim, `verify_referential_integrity.py` never actually called this function -- it carried its
    own independent, drifted copy of the same widened glob (migrated onto the shared resolver
    separately, same ticket)."""
    records = []
    total_lines = 0
    shards = shard_paths(data_dir, source)
    for shard in shards:
        shard_records, shard_lines = load_jsonl_with_line_count(shard)
        records.extend(shard_records)
        total_lines += shard_lines
    return records, total_lines


def load_data_glob(data_dir: Path, source: str) -> list:
    """Concatenate source.jsonl from every ISO-week folder under data_dir, sorted by week-folder
    name for determinism (matches record_events.py's write-side glob shape,
    tools/agent-monitoring/record_events.py:65)."""
    records, _ = load_data_glob_with_line_count(data_dir, source)
    return records


def check_gate_verdicts(data_dir: Path) -> list[str]:
    """One error line per invalid `gate_verdicts` row under `data_dir` (TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES)."""
    errors = []
    for shard in shard_paths(data_dir, gate_verdicts.KIND):
        rows, _ = load_jsonl_with_line_count(shard)
        for i, row in enumerate(rows, 1):
            problems = gate_verdicts.validate_record(row)
            if problems:
                errors.append(f"Invalid gate_verdicts row {shard.name}#{i}: {'; '.join(problems)}")
    return errors


def check_path_record(runs: list, events: list) -> list[str]:
    """One error line per run with an unknown `path_reason` and per event with an unknown `skip_reason`
    (TCK-20261006-PATH-REASON-AND-PHASE-COVERAGE-RECORD). Absent fields are valid: rows before the fields have neither."""
    errors = [f"Unknown path_reason {r['path_reason']!r}: {r.get('run_id')}"
              for r in runs if r.get("path_reason") is not None and r["path_reason"] not in PATH_REASONS]
    errors += [f"Unknown skip_reason {e['skip_reason']!r}: {e.get('run_id')}#{e.get('seq')}"
               for e in events if e.get("skip_reason") is not None and e["skip_reason"] not in SKIP_REASONS]
    return errors


# TCK-20261007-MONITORING-EXECUTION-ID-HYGIENE: `execution_id` was added to run records by
# TCK-20260730-CLAUDE-EXECUTION-IDENTITY; a row from before that date cannot have one.
EXECUTION_ID_START = "2026-07-30"
# The two native workflows whose sidecar writers omit `execution_id`/`provider` on purpose: the native
# Workflow runtime has no clock or shell to build one (.claude/workflows/implement-epic.js,
# create-tickets.js; post_tool_hook.py and run_dedup.py tolerate the absence). Tolerated, not fixed.
EXECUTION_ID_BY_DESIGN_WORKFLOWS = ("create-tickets", "implement-epic")
DEFAULT_SINCE_WEEK = "2026-W40"


def _iso_week_of(ts):
    """`YYYY-Www` for an ISO timestamp string, or None when it cannot be parsed."""
    if not isinstance(ts, str) or not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%G-W%V")
    except ValueError:
        return None


def _is_probe_run(run_id):
    return "PROBE" in (run_id or "").upper()


def classify_missing_execution_id(run: dict) -> str:
    """`predates` (before the field existed), `by design` (create-tickets / implement-epic), `probe`
    (a deliberate probe run) or `unexplained`. Only meaningful for a run without an `execution_id`."""
    start = _run_effective_start_ts(run)
    if start is not None and start < EXECUTION_ID_START:
        return "predates"
    workflow = run.get("workflow") or infer_workflow(run.get("run_id") or "")
    if workflow in EXECUTION_ID_BY_DESIGN_WORKFLOWS:
        return "by design"
    if _is_probe_run(run.get("run_id")):
        return "probe"
    return "unexplained"


def compute_execution_id_report(runs: list, since_week: str = DEFAULT_SINCE_WEEK) -> str:
    """Report-only: run rows without `execution_id`, by class, plus the since-week rows named. Never
    gates anything, never rewrites a shard."""
    missing = [r for r in runs if not r.get("execution_id")]
    by_class = Counter(classify_missing_execution_id(r) for r in missing)
    lines = ["--- Missing execution_id Report ---", ""]
    lines.append(f"run rows without execution_id: {len(missing)} of {len(runs)}")
    for cls in ("predates", "by design", "probe", "unexplained"):
        lines.append(f"  {cls}: {by_class.get(cls, 0)}")
    recent = [r for r in missing
              if (_iso_week_of(_run_effective_start_ts(r)) or "") >= since_week and classify_missing_execution_id(r) != "predates"]
    lines.append("")
    lines.append(f"since {since_week} ({len(recent)} rows):")
    for r in sorted(recent, key=lambda r: (_iso_week_of(_run_effective_start_ts(r)) or "", r.get("run_id") or "")):
        lines.append(f"  {_iso_week_of(_run_effective_start_ts(r))} {classify_missing_execution_id(r)}: {r.get('run_id')}")
    if not recent:
        lines.append("  none")
    return "\n".join(lines)


def compute_tool_row_report(data_dir: Path, max_listed: int = 20) -> str:
    """Report-only: tools-shard lines the loader cannot parse, named `file:line`. A torn line is skipped
    by every reader, so it is invisible unless counted here."""
    bad = []
    for shard in shard_paths(data_dir, "tools"):
        lines = [line.strip() for line in shard.read_text(errors="replace").splitlines() if line.strip()]
        for i, line in enumerate(lines, 1):
            try:
                json.loads(line)
            except json.JSONDecodeError:
                bad.append(f"{shard.name}:{i}")
    out = ["--- Skipped tools.jsonl Rows Report ---", "", f"tools-shard lines the loader cannot parse: {len(bad)}"]
    out += [f"  {b}" for b in bad[:max_listed]]
    if len(bad) > max_listed:
        out.append(f"  ... and {len(bad) - max_listed} more")
    return "\n".join(out)


def working_log_shard_ticket_ids(data_dir: Path) -> set:
    """Ticket ids that have a row in any `working_log` shard (data/YYYY-Www/*.working_log.jsonl), the place
    the closure recorder writes since the CSV stopped being appended to
    (TCK-20261008-VALIDATOR-WORKING-LOG-SHARDS-FALSE-POSITIVE)."""
    ids = set()
    for row in load_data_glob(data_dir, "working_log"):
        tid = str(row.get("ticket_id") or "").strip()
        if tid.startswith("TCK-"):
            ids.add(tid)
    return ids


def compute_since_week_summary(classified: list, runs_by_id: dict, since_week: str) -> str:
    """`W40+ warnings: N of M` with its filter method. `classified` is [(class, run_id)]; a run without a
    parseable start_ts is counted as unknown, not as since-week."""
    in_range, unknown = Counter(), 0
    for cls, run_id in classified:
        week = _iso_week_of(_run_effective_start_ts(runs_by_id.get(run_id, {})))
        if week is None:
            unknown += 1
        elif week >= since_week:
            in_range[cls] += 1
    detail = ", ".join(f"{k}: {v}" for k, v in sorted(in_range.items())) or "none"
    return (f"{since_week}+ warnings: {sum(in_range.values())} of {len(classified)} "
            f"(filter: run start_ts ISO week >= {since_week}; {unknown} without a parseable start_ts are not counted; {detail})")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Cross-check agent-monitoring integrity against agent-working/tickets/working_log.csv"
    )
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="Path to the agent-monitoring SQLite index")
    parser.add_argument("--data-dir", default=str(AGENT_MONITORING / "data"), help="Shard root for the gate_verdicts, working_log and tools-row checks")
    parser.add_argument("--since-week", default=DEFAULT_SINCE_WEEK, help="ISO week (YYYY-Www) for the since-week warning count")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    errors = []
    warnings = []
    classified = []  # (class, run_id) beside each run-keyed warning, for the since-week summary

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
            classified.append(("incomplete", run_id))

    # 2. Runs with no events (see EVENTS_REQUIRED_START above for the legacy exclusion)
    for run_id, run in runs_by_id.items():
        if events_by_run[run_id]:
            continue
        start_ts = _run_effective_start_ts(run)
        if start_ts is not None and start_ts < EVENTS_REQUIRED_START:
            continue
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
        log_tids |= working_log_shard_ticket_ids(Path(args.data_dir))
        for run_id, run in runs_by_id.items():
            # Batch epic/folder runs (EPIC-*, FOLDER-*) are orchestration records, not
            # individual tickets — they never produce their own working_log entry.
            if not run_id.startswith("TCK-"):
                continue
            status = run.get("final_status") or run.get("status")
            if status == "DONE" and run_id not in log_tids:
                warnings.append(f"Run marked DONE has no working_log entry: {run_id}")
                classified.append(("done-without-working_log", run_id))
    else:
        warnings.append(f"{LOG_FILE} not found — skipping working_log cross-check")

    errors.extend(check_gate_verdicts(Path(args.data_dir)))
    errors.extend(check_path_record(runs, events))

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
    print()
    print(compute_execution_id_report(runs, args.since_week))
    print()
    print(compute_tool_row_report(Path(args.data_dir)))
    print()
    print(compute_since_week_summary(classified, runs_by_id, args.since_week))

    total_runs = len(runs)
    total_events = len(events)
    print(f"OK: {total_runs} runs, {total_events} events — {len(warnings)} warning(s)")


if __name__ == "__main__":
    main()
