#!/usr/bin/env python3
"""Verify the 2 documented foreign-key relationships across the multi-week
agent-monitoring/data/<ISO-week>/{runs,events,tools}.jsonl corpus
(TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY):

  1. events.run_id -> runs.run_id           (schema.md lines 141/172)
  2. tools.(run_id, seq) -> events.(run_id, seq)   (schema.md lines 370/407-408)

Both checks read the UNION of every agent-monitoring/data/<week>/ folder (including
the unknown-week fallback bucket) before searching for a match — never scoped to a
single week folder. A run's events/tools rows can legitimately land in a different
week folder than its own runs.jsonl row, or than each other, whenever a session
crosses an ISO-week boundary (see TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION).
A same-week-scoped join would false-positive on this real, legitimate data.

Documented, schema-sanctioned exceptions this checker does NOT flag:
  - events.run_id starting with "RETRIEVAL-EVENT-" has no matching runs.jsonl row by
    design (schema.md lines 353-364) — excluded from Check 1's checked population.
  - tools.jsonl rows with run_id: null occurred outside an active workflow run
    (schema.md line 407) — excluded from Check 2's checked population.
  - tools.jsonl rows with seq <= 0 are context-packet-wrapper shadow rows, deliberately
    disjoint from the monotonic seq >= 1 range (schema.md lines 145, 310, 338-340) —
    excluded from Check 2's checked population.

This tool is report-only: it never gates, never writes, never exits non-zero on
violation volume, and never depends on the SQLite index (agent-monitoring-index/
monitoring.db) or build_index.py, both confirmed stale against the current weekly-
folder layout. main() always exits 0 — this mirrors validate.py's own
compute_drift_report()/compute_tool_count_drift_report() precedent ("never gates
anything, purely additive reporting"), extended here to the whole script since this
tool has no separate errors/warnings split at all.

Note for a reader running this against a live, currently-in-progress corpus: a run
still mid-pipeline will show its latest phase's tools.jsonl rows as Check-2 orphans
until that phase's event-batch write lands (events are written in a batch at
end-of-phase; tools.jsonl rows land live via the PostToolUse hook). This is expected
and transient, not a bug.
"""
import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_DATA_DIR = Path("agent-monitoring/data")

RETRIEVAL_EVENT_PREFIX = "RETRIEVAL-EVENT-"


def load_all_weeks(data_dir: Path, source: str) -> list[tuple[dict, str]]:
    """Read every agent-monitoring/data/<week>/<source>.jsonl file (every ISO-week
    folder plus unknown-week, unconditionally — no filename filtering), returning a
    list of (record, week_folder_name) tuples so every downstream violation example
    can cite the week folder it was found in.

    Mirrors the glob-over-all-weeks pattern already established by
    record_events.py::compute_tool_stats(), migrate_monitoring_data.py, and
    schema.md's own Join Example — reused by reference, not imported (this loader
    returns (record, week) pairs, which those call sites do not need).

    Malformed JSON lines are skipped with a stderr warning, matching
    validate.py::load_jsonl()'s tolerance convention — defense-in-depth against
    pre-existing malformed historical rows, not a concurrency safeguard (a reader
    can at worst see a file with N lines partway through a concurrent write of line
    N+1, which splitlines() simply does not yet include; it cannot observe a torn
    line, since writer.py's write_line() never mutates already-written bytes).
    """
    records: list[tuple[dict, str]] = []
    for path in sorted(data_dir.glob(f"*/{source}.jsonl")):
        week_folder = path.parent.name
        for i, line in enumerate(path.read_text().splitlines(), 1):
            if not line:
                continue
            try:
                records.append((json.loads(line), week_folder))
            except json.JSONDecodeError as e:
                print(f"WARNING: {path}:{i}: invalid JSON — {e}", file=sys.stderr)
    return records


def check_events_to_runs(
    runs: list[tuple[dict, str]], events: list[tuple[dict, str]]
) -> tuple[int, list[dict]]:
    """Check 1: every events.run_id (excluding RETRIEVAL-EVENT-* run_ids) has a
    matching runs.run_id row somewhere across the full, all-weeks runs list — never
    scoped to a single week folder before searching."""
    valid_run_ids = {r.get("run_id") for r, _ in runs if r.get("run_id")}

    checked = 0
    violations: list[dict] = []
    for e, week in events:
        run_id = e.get("run_id")
        if run_id is None or run_id.startswith(RETRIEVAL_EVENT_PREFIX):
            continue
        checked += 1
        if run_id not in valid_run_ids:
            violations.append({"run_id": run_id, "seq": e.get("seq"), "week_folder": week})
    return checked, violations


def check_tools_to_events(
    events: list[tuple[dict, str]], tools: list[tuple[dict, str]]
) -> tuple[int, list[dict]]:
    """Check 2: every tools.(run_id, seq) (excluding run_id: null and seq <= 0 rows)
    has a matching events.(run_id, seq) row somewhere across the full, all-weeks
    events list — never scoped to a single week folder before searching.

    valid_keys is built as a set populated by iterating every event row, never a
    dict comprehension keyed by (run_id, seq) — the real corpus has 145 distinct
    (run_id, seq) keys with more than one events.jsonl row (legacy-schema duplicate
    alongside a current-schema record for the same identity); this is an existence
    check ("does at least one event exist at this key"), so a set is correct and
    sufficient, while a dict(...)-style construction would silently keep only the
    last-seen row per key depending on glob/file ordering.
    """
    valid_keys: set[tuple] = set()
    for e, _ in events:
        run_id = e.get("run_id")
        seq = e.get("seq")
        if run_id is not None and seq is not None:
            valid_keys.add((run_id, seq))

    checked = 0
    violations: list[dict] = []
    for t, week in tools:
        run_id = t.get("run_id")
        seq = t.get("seq")
        if run_id is None or seq is None or seq <= 0:
            continue
        checked += 1
        if (run_id, seq) not in valid_keys:
            violations.append({"run_id": run_id, "seq": seq, "week_folder": week})
    return checked, violations


@dataclass
class ReferentialIntegrityReport:
    """Structured result of both FK checks.

    The checked-count fields exclude every documented exception (RETRIEVAL-EVENT-*
    events, run_id: null tools rows, seq <= 0 tools rows) — they never inflate the
    denominator with rows the check was never meant to hold accountable, so a future
    consumer computing a violation rate (violations / checked) gets a meaningful
    number.

    This report format is the documented contract for a future consumer (dashboard,
    gate, manual audit): a structured caller reads events_violations/tools_violations
    directly; a human reads .to_text().
    """

    events_checked: int
    events_violations: list[dict] = field(default_factory=list)
    tools_checked: int = 0
    tools_violations: list[dict] = field(default_factory=list)

    def to_text(self, sample_size: int = 20) -> str:
        lines = ["--- Referential Integrity Report ---", ""]

        lines.append("Check 1: events.run_id -> runs.run_id")
        lines.append(f"  Events checked (excludes RETRIEVAL-EVENT-* run_ids): {self.events_checked}")
        lines.append(f"  Violations (no matching runs.jsonl row anywhere): {len(self.events_violations)}")
        if self.events_violations:
            lines.append("  Sample violations:")
            for v in self.events_violations[:sample_size]:
                lines.append(f"    {v['run_id']} seq={v['seq']} (week={v['week_folder']})")
            if len(self.events_violations) > sample_size:
                lines.append(f"    ... and {len(self.events_violations) - sample_size} more")
        lines.append("")

        lines.append("Check 2: tools.(run_id, seq) -> events.(run_id, seq)")
        lines.append(f"  Tool rows checked (excludes run_id: null and seq <= 0): {self.tools_checked}")
        lines.append(f"  Violations (no matching events row anywhere): {len(self.tools_violations)}")
        if self.tools_violations:
            lines.append("  Sample violations:")
            for v in self.tools_violations[:sample_size]:
                lines.append(f"    {v['run_id']} seq={v['seq']} (week={v['week_folder']})")
            if len(self.tools_violations) > sample_size:
                lines.append(f"    ... and {len(self.tools_violations) - sample_size} more")

        return "\n".join(lines)


def compute_referential_integrity_report(data_dir: Path = DEFAULT_DATA_DIR) -> ReferentialIntegrityReport:
    """Library-callable entry point: loads the full corpus (every week folder under
    data_dir) and runs both FK checks. data_dir is overridable so tests can point it
    at a tmp_path fixture directory instead of the real corpus."""
    runs = load_all_weeks(data_dir, "runs")
    events = load_all_weeks(data_dir, "events")
    tools = load_all_weeks(data_dir, "tools")

    events_checked, events_violations = check_events_to_runs(runs, events)
    tools_checked, tools_violations = check_tools_to_events(events, tools)

    return ReferentialIntegrityReport(
        events_checked=events_checked,
        events_violations=events_violations,
        tools_checked=tools_checked,
        tools_violations=tools_violations,
    )


def build_parser():
    parser = argparse.ArgumentParser(
        description="Verify referential integrity across agent-monitoring/data/<week>/{runs,events,tools}.jsonl"
    )
    parser.add_argument(
        "--data-dir",
        default=str(DEFAULT_DATA_DIR),
        help="Path to the agent-monitoring weekly data directory",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    report = compute_referential_integrity_report(Path(args.data_dir))
    print(report.to_text())
    # Report-only tool — never gates, never exits non-zero on violation volume (see
    # module docstring / ticket's Decision on item 4). No --strict flag: gate/CI
    # wiring is a deliberate, separate future decision.


if __name__ == "__main__":
    main()
