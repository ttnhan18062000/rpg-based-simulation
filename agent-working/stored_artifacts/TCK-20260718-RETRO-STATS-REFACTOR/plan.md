---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-RETRO-STATS-REFACTOR
artifact_type: plan
tags: []
---

# Implementation Plan — TCK-20260718-RETRO-STATS-REFACTOR

## Summary

Extract `generate_retro.py::generate()`'s metric computation into a new function,
`compute_retro_metrics(runs, events, tickets_root=None)`, returning a plain `dict` (following
`tag_report.py::build_json_report()`'s precedent — no new dataclass/TypedDict pattern this module
doesn't already use). `generate()` becomes a thin wrapper: call `compute_retro_metrics()`, then
render its result to the exact same Markdown structure as today. Zero behavior change to the
public `generate()` function or the CLI.

## Steps

### Step 1 — Extract `compute_retro_metrics()`

Move every computation currently in `generate()` before the `lines = []` line (L242) — plus the
per-section value calculations currently interleaved with `lines.append()` calls (e.g.
`scored_events`/`phase_scores`/`agent_scores` for spend proxy, which today are computed
inline just before their own section) — into a new function:

```python
def compute_retro_metrics(runs, events, tickets_root=None) -> dict:
    ...
    return {
        "run_summary": {"total": total, "done_count": done_count, "gate_fail_count": len(gate_fails),
                         "avg_duration_s": avg_dur, "avg_agents": avg_agents,
                         "total_agent_calls": len(events)},
        "gate_failure_breakdown": dict(gate_counter),
        "reason_code_breakdown": dict(reason_counter),
        "tag_breakdown_subsystem": {tag: {"runs": len(rs), "done": ..., "gate_fails": ...}
                                     for tag, rs in subsystem_tag_runs.items()},
        "tag_breakdown_skill": {tag: {"runs": len(rs), "gate_hits": ...}
                                 for tag, rs in skill_tag_runs.items()},
        "tier_distribution": {tier: {"count": n, "scoped": tier_scoped[tier], "done": tier_done[tier]}
                               for tier, n in tier_counts.items()},
        "agent_status_distribution": {agent: dict(counts) for agent, counts in agent_stats.items()},
        "spend_proxy_by_phase": {phase: {"events_scored": len(s), "total": sum(s), "avg": sum(s)/len(s)}
                                  for phase, s in phase_scores.items()},
        "spend_proxy_by_agent": {...},  # same shape, by agent
        "summary_quality": {"empty_summaries_current": ..., "legacy_event_count": ...,
                             "long_summaries": ...},
        "slow_runs": [{"run_id": r["run_id"], "duration_s": r.get("duration_s"),
                        "final_status": r.get("final_status")} for r in slow_runs],
    }
```

Preserve every existing helper call exactly as-is (`_resolve_status`, `_is_gate_fail`,
`categorize_tag`, `_collect_tagged_tickets`, `load_registry`, `fmt_pct` — note `fmt_pct` stays a
rendering concern, called only in Step 2, not inside `compute_retro_metrics()`, since it returns
a formatted string not a number; the computation function should keep raw counts/values, deferring
percent-formatting to the renderer).

### Step 2 — Rewrite `generate()` as a thin renderer

`generate()` keeps its exact signature. Body becomes: call `compute_retro_metrics(runs, events,
tickets_root)`, then build `lines` from the returned dict using the identical Markdown text/table
structure as today (same headers, same column names, same conditional-render rules — a section
only renders when its underlying data is non-empty, exactly as today). The `label`/`week_str`
header lines and the static `## Notes` placeholder text stay in `generate()` (they're not
computed data).

### Step 3 — Byte-identical output proof

Before considering this ticket done: `git stash` (or copy the pre-refactor file aside), run
`python3 tools/agent-monitoring/generate_retro.py --all` against the real repo data, save output.
Restore the refactored code, run the same command again, save output. `diff` the two — must be
byte-identical. If not, the refactor introduced a real behavior change; investigate and fix before
proceeding, do not adjust the test/proof to accept a difference.

### Step 4 — New tests

Add tests for `compute_retro_metrics()` directly (see test_plan.md) alongside the existing 15
`generate()`-level tests, which must all continue passing unmodified — do not edit them unless a
genuine bug in their own fixtures is found (not expected).

### Step 5 — Full regression run

```
python3 -m pytest tests/tools/test_generate_retro.py -q
```
All 15 existing + new tests passing.

## Scope Guards

- Do not change `generate_retro.py`'s CLI (`main()`, `_update_index()`) — untouched.
- Do not change the Markdown text/structure/column-headers `generate()` produces — Step 3's
  byte-identical proof is the hard guard for this.
- Do not touch `tools/tag_report.py` — read-only precedent reference, not modified.
- Do not build the JSON API consumer (AGENTOPS-STATS-API's scope) — this ticket only produces the
  reusable function; the sibling ticket imports and calls it.

## Dependency Map

No dependencies within this ticket's own steps beyond sequential order (1→2→3→4→5). This ticket
itself is the first in the epic's SEQUENCE.md — TCK-20260718-AGENTOPS-STATS-API depends on this
ticket's `compute_retro_metrics()` existing.

## Acceptance Criteria Map

- AC "new function exists returning all metrics as structured data" → Step 1.
- AC "generate() refactored, no duplicated logic" → Step 2.
- AC "CLI output unchanged, proven via stash comparison" → Step 3.
- AC "existing tests pass, new tests cover extracted function" → Steps 4-5.
- AC "agent-monitoring-retro skill still produces same report shape" → implied by Step 3's
  byte-identical proof (the skill just invokes the CLI, which Step 3 already validates).

## Anti-Drift Notes

`fmt_pct()`'s `100 * n // total` integer-truncation behavior must not change — several existing
tests assert exact percentage strings computed with this specific rounding rule. Section ordering
in the rendered Markdown must not change — one existing test asserts relative `report.index(...)`
positions of five different sections.
