#!/usr/bin/env python3
"""Read-only baseline metrics over agent-monitoring/*.jsonl
(TCK-20260728-RETRIEVAL-BASELINE-METRICS).

One-off baseline snapshot of current retrieval/context-loading behavior, computed purely by
importing and composing existing functions from generate_retro.py (_load_runs_and_events,
load_jsonl, DEFAULT_TOOLS_FILE, _resolve_status, _is_gate_fail), legacy_reader.py
(classify_provenance), and manifest.py (_assert_safe_output_path) — never reimplementing any of
their logic. Prints a JSON report to stdout by default; never writes into agent-monitoring/ itself.

Distinct from generate_retro.py's own recurring weekly RETRO-*.md cadence — this tool is a
one-off/periodic snapshot, not part of that cadence, and does not write into agent-monitoring/retro/.
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_retro import (  # noqa: E402
    DEFAULT_TOOLS_FILE,
    _is_gate_fail,
    _load_runs_and_events,
    _resolve_status,
    load_jsonl,
)
from legacy_reader import classify_provenance  # noqa: E402
from manifest import _assert_safe_output_path  # noqa: E402

# The literal `tool` values confirmed present in the real corpus (investigation.md's direct scan)
# that represent a follow-up search action. mcp__knowledge-search__search_health is deliberately
# excluded — it is a health-check call, not a follow-up search. Bash is excluded even though some
# Bash calls have search-flavored input_summary text, since that is not distinguishable by tool
# name alone and this metric must stay precise, not inflated.
SEARCH_TOOL_NAMES = frozenset({
    "mcp__knowledge-search__search_docs",
    "ToolSearch",
    "WebSearch",
})

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


def build_search_count_section(tools: list) -> dict:
    per_run: dict = defaultdict(int)
    total = 0
    for record in tools:
        if record.get("tool") in SEARCH_TOOL_NAMES:
            # tools.jsonl records issued outside any workflow run carry run_id=None
            # (legacy_reader.py's "interactive_null" shape) — grouped under a literal
            # "unattributed" key rather than None, since a None dict key breaks
            # json.dumps(sort_keys=True)'s key comparison against the str keys of real runs.
            run_id = record.get("run_id") or "unattributed"
            per_run[run_id] += 1
            total += 1
    return {
        "derivation": "Derived from tools.jsonl's literal `tool` field, filtered to "
                      "SEARCH_TOOL_NAMES = {mcp__knowledge-search__search_docs, ToolSearch, "
                      "WebSearch}. This is a finer-grained derivation than the ticket AC's literal "
                      "'tool_call_count' wording — tool_call_count is a coarse per-event total-tool"
                      "-activity aggregate on events.jsonl records, and does not distinguish a search "
                      "call from any other tool call. This report uses the more precise, still-100%"
                      "-existing-data derivation because it actually answers 'how many follow-up "
                      "searches happened', per this ticket's plan.md Step 3.",
        "per_run": dict(per_run),
        "total": total,
    }


def build_duration_section(runs: list) -> dict:
    rows = []
    for r in runs:
        duration_s = r.get("duration_s")
        if not duration_s:
            continue
        rows.append({
            "run_id": r.get("run_id"),
            "duration_s": duration_s,
            "flag": "pause-contaminated",
            "note": "raw duration_s includes session-pause/idle gaps; a gap-aware active-duration "
                    "view does not exist in this repo today "
                    "(tools/agent-monitoring/duration_utils.py is absent) — see "
                    "docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md",
        })
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


def build_raw_investigation_count_section(tools: list) -> dict:
    per_run: dict = defaultdict(int)
    total = 0
    for record in tools:
        if record.get("tool") == "Read":
            # Same run_id=None -> "unattributed" convention as build_search_count_section
            # (see that function's inline comment) — reused verbatim, not reinvented.
            run_id = record.get("run_id") or "unattributed"
            per_run[run_id] += 1
            total += 1

    search_total = build_search_count_section(tools)["total"]
    if search_total > 0:
        ratio = round(total / search_total, 4)
    else:
        ratio = (
            "undefined: zero search_count.total in corpus, cannot compute a ratio "
            "without a fabricated denominator"
        )

    return {
        "derivation": (
            "Derived from tools.jsonl's literal `tool` field, filtered to `tool == \"Read\"` "
            "(the single most common non-Bash tool in this corpus). `Grep` is not counted "
            "because no distinct `Grep` tool name is ever recorded in this environment; "
            "grep-equivalent work runs through the catch-all `Bash` tool, which is excluded "
            "here for the same non-distinguishability rationale documented on "
            "SEARCH_TOOL_NAMES above (some Bash calls are search/grep-flavored by content, "
            "but that is not distinguishable by tool name alone). This section is therefore "
            "a proxy for raw investigation effort (how often the agent had to open a file "
            "directly to look), not a literal grep-call count. read_to_search_ratio is "
            "computed corpus-wide only (this section's total Read count divided by "
            "search_count's total, both derived from this same tools list), never per-run, "
            "because search_count.per_run and this section's per_run do not share an "
            "identical run_id key set in general; if search_count.total is 0 the ratio is "
            "the literal string above instead of a divided-by-zero or fabricated value."
        ),
        "per_run": dict(per_run),
        "total": total,
        "read_to_search_ratio": ratio,
    }


def build_baseline_report(runs: list, events: list, tools: list) -> dict:
    return {
        "ticket_id": "TCK-20260728-RETRIEVAL-BASELINE-METRICS",
        "generated_note": "one-off baseline snapshot — not the recurring weekly retro cadence",
        "context_tokens": build_context_tokens_section(),
        "search_count": build_search_count_section(tools),
        "raw_investigation_count": build_raw_investigation_count_section(tools),
        "duration": build_duration_section(runs),
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
