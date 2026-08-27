#!/usr/bin/env python3
"""Read-only baseline metrics over agent-monitoring/*.jsonl
(TCK-20260728-RETRIEVAL-BASELINE-METRICS).

One-off baseline snapshot of current retrieval/context-loading behavior, computed purely by
importing and composing existing functions from generate_retro.py (_load_runs_and_events,
load_jsonl, DEFAULT_TOOLS_FILE, _resolve_status, _is_gate_fail, SEARCH_TOOL_NAMES,
build_search_count_section, build_raw_investigation_count_section), legacy_reader.py
(classify_provenance), and manifest.py (_assert_safe_output_path) — never reimplementing any of
their logic. Prints a JSON report to stdout by default; never writes into agent-monitoring/ itself.

Distinct from generate_retro.py's own recurring weekly RETRO-*.md cadence — this tool is a
one-off/periodic snapshot, not part of that cadence, and does not write into agent-monitoring/retro/.
SEARCH_TOOL_NAMES/build_search_count_section/build_raw_investigation_count_section were relocated
into generate_retro.py by TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING to resolve a
circular-import constraint (this module already imports FROM generate_retro.py; the reverse
direction would create a cycle) and to let generate_retro.py's own recurring report trend the same
numbers this snapshot reports — the *numbers* are now shared, the one-off/recurring *cadences*
remain distinct.
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_retro import (  # noqa: E402
    DEFAULT_TOOLS_FILE,
    SEARCH_TOOL_NAMES,
    _is_gate_fail,
    _load_runs_and_events,
    _resolve_status,
    build_raw_investigation_count_section,
    build_search_count_section,
    load_jsonl,
)
from legacy_reader import classify_provenance  # noqa: E402
from manifest import _assert_safe_output_path  # noqa: E402
from duration_utils import compute_active_idle_split  # noqa: E402

# Deliberately narrower than generate_retro.py's _is_gate_fail — that predicate also covers
# TESTS_FAILED/DOD_BLOCKED (Test/Verify-phase gate fails), which are not "review rework".
# Scoped to exactly the two statuses investigation.md confirmed (via a direct grep of
# .claude/workflows/implement-ticket.js) terminate a run at the Review phase or the
# post-Implement Architecture-Verify phase.
REWORK_TRIGGER_STATUSES = frozenset({"NEEDS_CHANGES", "BLOCKED"})


def load_all_sources() -> tuple:
    runs, events = _load_runs_and_events()
    tools = load_jsonl(DEFAULT_TOOLS_FILE)
    return runs, events, tools


def build_context_tokens_section() -> dict:
    return {
        "status": "unavailable",
        "reason": "Real token/context-size telemetry is platform-blocked and is not recorded "
                  "anywhere in agent-monitoring/*.jsonl.",
        "citation": "docs/agent-monitoring/schema.md — 'What is not recorded' section",
    }


def build_duration_section(runs: list, events: list) -> dict:
    """TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT: rows now carry a real, computed active/idle split
    via the shared tools/agent-monitoring/duration_utils.py — never reimplemented here. A row is
    only flagged "pause-contaminated" when its own real idle_gap_s is nonzero (some computed gap
    met the pause threshold), not unconditionally for every row as before that ticket landed.
    """
    events_by_run_id = defaultdict(list)
    for e in events:
        rid = e.get("run_id")
        if rid:
            events_by_run_id[rid].append(e)

    rows = []
    for r in runs:
        duration_s = r.get("duration_s")
        if not duration_s:
            continue
        split = compute_active_idle_split(
            r.get("start_ts"), r.get("end_ts"), events_by_run_id.get(r.get("run_id"), [])
        )
        row = {"run_id": r.get("run_id"), "duration_s": duration_s}
        if split is None:
            row["active_duration_s"] = None
            row["idle_gap_s"] = None
            row["note"] = "start_ts/end_ts unparseable — gap-aware split unavailable for this row"
        else:
            row["active_duration_s"] = split["active_duration_s"]
            row["idle_gap_s"] = split["idle_gap_s"]
            if split["idle_gap_s"] > 0:
                row["flag"] = "pause-contaminated"
                row["note"] = (
                    f"{split['idle_gap_s']:.0f}s of this run's duration_s is idle gap time "
                    f"(largest: {split['largest_gap_from']} -> {split['largest_gap_to']}, "
                    f"{split['largest_gap_s']:.0f}s) — see tools/agent-monitoring/duration_utils.py"
                )
        rows.append(row)
    return {"rows": rows}


def build_gate_outcome_section(runs: list) -> dict:
    # A handful of legacy-shaped runs.jsonl records (shape6_type_checker_exception) have neither
    # final_status nor status, so _resolve_status(r) returns None; grouped under a literal
    # "MISSING_STATUS" key rather than None, since a None dict key breaks
    # json.dumps(sort_keys=True)'s key comparison against the str keys of resolved statuses.
    status_breakdown = Counter(_resolve_status(r) or "MISSING_STATUS" for r in runs)
    gate_fail_count = sum(1 for r in runs if _is_gate_fail(r))
    terminal_success_count = sum(1 for r in runs if _resolve_status(r) == "DONE")
    return {
        "status_breakdown": dict(status_breakdown),
        "gate_fail_count": gate_fail_count,
        "terminal_success_count": terminal_success_count,
        "disclosure": "derived proxy from runs.jsonl's final_status/status fields via "
                      "generate_retro.py's _resolve_status/_is_gate_fail — not fabricated",
    }


def build_review_rework_section(runs: list) -> dict:
    runs_grouped_by_id = defaultdict(list)
    for i, run in enumerate(runs):
        runs_grouped_by_id[run.get("run_id", f"?:{i}")].append(run)

    reworked_run_ids = []
    for run_id, group in runs_grouped_by_id.items():
        if len(group) < 2:
            continue
        sorted_group = sorted(group, key=lambda r: r.get("start_ts") or "")
        for idx, earlier in enumerate(sorted_group):
            if _resolve_status(earlier) not in REWORK_TRIGGER_STATUSES:
                continue
            later_records = sorted_group[idx + 1:]
            if any(_resolve_status(later) == "DONE" for later in later_records):
                reworked_run_ids.append(run_id)
                break

    return {
        "reworked_run_ids": sorted(reworked_run_ids),
        "count": len(reworked_run_ids),
        "rule": "A run_id is flagged as review-rework if 2+ runs.jsonl records share that run_id, "
                "an earlier record's resolved status is NEEDS_CHANGES or BLOCKED (the Review/"
                "Architecture-Verify gate-failure statuses), and a chronologically later record for "
                "the same run_id resolves to DONE.",
        "disclosure": "derived proxy from cross-run final_status transitions grouped by run_id — "
                      "not fabricated; reason_code/reason_code_breakdown is not used as a rework "
                      "signal",
    }


def build_legacy_schema_notes(runs: list, events: list, tools: list) -> dict:
    runs_legacy_count = sum(1 for r in runs if classify_provenance(r, "runs"))
    events_legacy_count = sum(1 for e in events if classify_provenance(e, "events"))
    tools_legacy_count = sum(1 for t in tools if classify_provenance(t, "tools"))
    return {
        "runs_legacy_count": runs_legacy_count,
        "events_legacy_count": events_legacy_count,
        "tools_legacy_count": tools_legacy_count,
        "note": "counts records whose shape matches one of legacy_reader.py's documented legacy "
                "schema generations (classify_provenance) — informational, not blocking",
    }


def build_baseline_report(runs: list, events: list, tools: list) -> dict:
    return {
        "ticket_id": "TCK-20260728-RETRIEVAL-BASELINE-METRICS",
        "generated_note": "one-off baseline snapshot — not the recurring weekly retro cadence",
        "context_tokens": build_context_tokens_section(),
        "search_count": build_search_count_section(tools),
        "raw_investigation_count": build_raw_investigation_count_section(tools),
        "duration": build_duration_section(runs, events),
        "gate_outcome": build_gate_outcome_section(runs),
        "review_rework": build_review_rework_section(runs),
        "legacy_schema_notes": build_legacy_schema_notes(runs, events, tools),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None, help="optional path to also write the JSON output to")
    args = parser.parse_args()

    runs, events, tools = load_all_sources()
    report = build_baseline_report(runs, events, tools)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"

    if args.output is not None:
        _assert_safe_output_path(args.output)
        args.output.write_text(output)

    sys.stdout.write(output)


if __name__ == "__main__":
    main()
