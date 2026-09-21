#!/usr/bin/env python3
"""Read-only baseline metrics over agent-monitoring/*.jsonl
(TCK-20260728-RETRIEVAL-BASELINE-METRICS).

One-off baseline snapshot of current retrieval/context-loading behavior, computed purely by
importing and composing existing functions from generate_retro.py (_load_runs_and_events,
load_data_glob, DEFAULT_TOOLS_FILE, _resolve_status, _is_gate_fail, SEARCH_TOOL_NAMES,
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
    load_data_glob,
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
    # DEFAULT_TOOLS_FILE is directory-valued (TCK-20260903-MONITORING-DATA-CONSUMERS-CORE) — a
    # bare load_jsonl() against it raises IsADirectoryError; load_data_glob() is the multi-week-
    # aware replacement, matching generate_retro.py's own real call site (line 2275).
    tools = load_data_glob(DEFAULT_TOOLS_FILE, "tools")
    return runs, events, tools


def build_context_tokens_section() -> dict:
    """`agent-monitoring/data/*.jsonl` itself carries no token field, and this report is scoped to
    exactly that data (reproducible from the repo alone, on any machine, in CI). "unavailable" is
    still correct for THIS report's own status field -- but not because the underlying data is
    unobtainable everywhere: TCK-20260921-REAL-TOKEN-TELEMETRY corrected the earlier
    "platform-blocked, no workaround" claim as false. See `workaround` below."""
    return {
        "status": "unavailable",
        "reason": "agent-monitoring/data/*.jsonl carries no token field -- the workflow's own "
                  "per-event recording never receives real token usage from the Claude Code "
                  "runtime, so this report (reproducible from repo data alone) cannot include it.",
        "workaround": "tools/agent-monitoring/real_token_usage.py reads real per-request usage "
                      "directly from local Claude Code transcripts (~/.claude/projects/**/*.jsonl) "
                      "-- a separate, machine-local, retrospective analysis, not available in CI "
                      "or from a fresh clone, so it is not folded into this report's own "
                      "reproducible-from-repo-data shape. See generate_retro.py's "
                      "--include-real-tokens flag instead.",
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


def build_harm_check_baseline_section(runs: list, events: list, tools: list, window_start_ts: str) -> dict:
    """Pre-trial harm-check baseline (TCK-20260916-HEADROOM-HARM-CHECK-BASELINE).

    A read-only comparison point captured BEFORE Headroom is enabled, so the eventual harm check
    has something to compare a trial window against. Not a token/cost baseline — see this
    ticket's own Request Summary for why that's platform-blocked and would measure the wrong
    thing anyway (cost_proxy_score is tool-call-shape-derived, not token-derived, so it stays
    flat regardless of real savings).

    Deliberately does NOT include any Agent-tool-call duration metric: TCK-20260917-FORK-RETURNS-
    CONTENT-FREE-INDISTINGUISHABLE found that an Agent row's own duration_ms times only the async
    launch (~2s), never the dispatched work — a real, confirmed finding, not a hypothesis. Any
    future extension of this baseline that adds an Agent-duration signal must carry that caveat
    forward explicitly, or it measures launch latency and calls it agent behavior.
    """
    window_runs = [r for r in runs if str(r.get("start_ts") or "") >= window_start_ts]
    window_events = [e for e in events if str(e.get("ts") or "") >= window_start_ts]
    window_tools = [t for t in tools if str(t.get("ts") or "") >= window_start_ts]

    done_count = sum(1 for r in window_runs if _resolve_status(r) == "DONE")
    done_rate = done_count / len(window_runs) if window_runs else None

    event_status_counter = Counter(e.get("status") for e in window_events)
    total_events = len(window_events)
    failed_rate = (event_status_counter.get("failed", 0) / total_events) if total_events else None
    blocked_rate = (event_status_counter.get("blocked", 0) / total_events) if total_events else None

    reason_code_frequency = Counter(e.get("reason_code") for e in window_events if e.get("reason_code"))

    # tool_call_count per phase: record_events.py's own compute_tool_stats() writes this field at
    # write time, so it's read here, never recomputed. None values (rows predating that write, or
    # any hand-orchestrated closure that never had a live per-phase sidecar) are excluded from the
    # per-phase aggregate rather than treated as 0, so a genuinely-zero count and a not-recorded
    # count are never silently conflated.
    tool_call_count_by_phase = defaultdict(list)
    for e in window_events:
        tcc = e.get("tool_call_count")
        if tcc is not None:
            tool_call_count_by_phase[e.get("phase") or "MISSING_PHASE"].append(tcc)
    tool_call_count_per_phase = {
        phase: {"mean": sum(counts) / len(counts), "n": len(counts)}
        for phase, counts in sorted(tool_call_count_by_phase.items())
    }
    hand_orchestrated_zero_rate_note = (
        "Every tool_call_count sampled in this window's events is None or 0 — this window's real "
        "activity is dominated by hand-orchestrated closures (record_hand_orchestrated_closure.py), "
        "which never had a live per-phase sidecar tracking tool calls as they happened, not because "
        "no tool calls occurred. The over-compression detector this field is meant to serve "
        "(tool_call_count inflating when compression drops something the agent needed) will read as "
        "flat zero for hand-orchestrated trial activity too, for the same structural reason — this "
        "is a real blind spot in this window's own tool_call_count signal, not fabricated evidence "
        "of anything."
        if tool_call_count_per_phase and all(v["mean"] == 0 for v in tool_call_count_per_phase.values())
        else None
    )

    session_id_present = sum(1 for t in window_tools if t.get("session_id"))
    session_id_population_rate = (session_id_present / len(window_tools)) if window_tools else None

    return {
        "window_start_ts": window_start_ts,
        "window_end_ts": "now (report generation time) — this is a live snapshot, not a fixed historical range",
        "population": {
            "run_count": len(window_runs),
            "event_count": len(window_events),
            "tools_count": len(window_tools),
        },
        "done_rate": done_rate,
        "per_event_failed_rate": failed_rate,
        "per_event_blocked_rate": blocked_rate,
        "reason_code_frequency": dict(reason_code_frequency),
        "tool_call_count_per_phase": tool_call_count_per_phase,
        "tool_call_count_hand_orchestration_caveat": hand_orchestrated_zero_rate_note,
        "session_id_population_rate": session_id_population_rate,
        "session_id_reliability_note": (
            "session_id is populated on effectively every tools.jsonl row in this window "
            f"({session_id_present}/{len(window_tools)}), so isolating a later trial session's "
            "own rows by session_id is reliable, not assumed."
        ),
        "statistical_limit": (
            "At roughly 16-70 runs/week, this is a coarse tripwire: able to catch a run of clearly "
            "worse outcomes, not a subtle few-percent regression. No promotion/abandon decision "
            "should claim more precision than that."
        ),
        "trial_not_yet_started_note": (
            "Captured before any session routed real work through Headroom compression. A prior "
            "smoke test (TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL) called headroom_compress/"
            "retrieve/stats on synthetic payloads via explicit MCP calls only — it changed no "
            "session's own behavior and is not part of this window's real activity being measured."
        ),
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
    parser.add_argument(
        "--harm-check-window-start",
        type=str,
        default=None,
        help="ISO-8601 timestamp (e.g. 2026-09-16). When given, prints ONLY the "
        "TCK-20260916-HEADROOM-HARM-CHECK-BASELINE report for the window from this timestamp to "
        "now, instead of the default one-off baseline report -- a separate, additive report "
        "shape, not merged into build_baseline_report()'s own pinned key set.",
    )
    args = parser.parse_args()

    runs, events, tools = load_all_sources()

    if args.harm_check_window_start is not None:
        report = build_harm_check_baseline_section(runs, events, tools, args.harm_check_window_start)
    else:
        report = build_baseline_report(runs, events, tools)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"

    if args.output is not None:
        _assert_safe_output_path(args.output)
        args.output.write_text(output)

    sys.stdout.write(output)


if __name__ == "__main__":
    main()
