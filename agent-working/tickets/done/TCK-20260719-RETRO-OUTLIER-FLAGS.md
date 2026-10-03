---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-RETRO-OUTLIER-FLAGS
phase: done
date: 2026-07-19
tags: []
---

# TCK-20260719-RETRO-OUTLIER-FLAGS

## Title
Add outlier flagging to agent-monitoring retro report

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The author wants a per-run/per-event outlier flag (e.g. duration_s greater than 3x a median, or cost_proxy_score greater than Nx the phase/agent median) surfaced as a visible line in make agent-monitoring-retro's output, closing the gap where real, unexplained outliers currently sit unflagged in the data with zero recorded investigation. The flag does not need to explain why an outlier occurred, just make it visible. Investigation found the proposal's claim that the dashboard "would benefit from this epic's fixes automatically" is FALSE for this concern: src/api/agent_ops_dashboard/ingest.py::get_agent_monitoring_stats() builds AgentMonitoringStats via explicit per-field typed submodel construction, never **metrics passthrough, so a new top-level 'outliers' key would be silently dropped at the API boundary unless models.py/ingest.py are also updated — this ticket is scoped to CLI/Markdown output only, and the ticket body corrects that claim explicitly.

## Scope
- Add a new top-level 'outliers' key to compute_retro_metrics()'s return dict in generate_retro.py flagging duration_s outliers (run-level, median basis per Plan decision) and cost_proxy_score outliers (phase/agent-scoped), Nx median, excluding nulls from both flag computation and median basis
- Add a new conditionally-rendered '## Outliers' Markdown section to the CLI report
- Update test_compute_retro_metrics_returns_all_documented_keys for the new key
- Ticket body explicitly corrects the proposal's false claim that the dashboard benefits from this automatically, and records dashboard exposure as a separate deliberate future follow-up

## Out of Scope
- Dashboard/API exposure — no changes to src/api/agent_ops_dashboard/models.py or ingest.py; the new key would be silently dropped at the API boundary today and wiring it through is a separate, deliberate future follow-up, not assumed free
- Removing or replacing the existing slow_runs fixed 1800s-threshold mechanism — relationship between it and the new relative/median outlier section is a Plan-phase decision, not a removal

## Acceptance Criteria
- [ ] compute_retro_metrics() returns a new top-level 'outliers' key covering duration_s (run-level) and cost_proxy_score (phase/agent-scoped) outliers at Nx median, with null values excluded from both flagging and median basis
- [ ] A new '## Outliers' section renders conditionally in the CLI Markdown report produced by make agent-monitoring-retro
- [ ] test_compute_retro_metrics_returns_all_documented_keys updated to include the new 'outliers' key
- [ ] Ticket body explicitly states the dashboard does NOT get this automatically (get_agent_monitoring_stats() uses explicit typed submodel construction, not **metrics passthrough) and records dashboard exposure as an out-of-scope future follow-up

## Related Tickets
- TCK-20260718-RETRO-STATS-REFACTOR
- TCK-20260718-AGENTOPS-STATS-API
- TCK-20260708-AGENT-COST-OBSERVABILITY

## Related Docs
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tests/tools/test_generate_retro.py
- src/api/agent_ops_dashboard/models.py
- src/api/agent_ops_dashboard/ingest.py

## Assumptions / Open Questions
- Median basis for duration_s outliers needs an explicit Plan-phase decision: runs.jsonl has no 'phase' field, only 'tier', so the proposal's literal 'duration_s > 3x the phase median' wording doesn't map onto the real schema — Plan must decide overall-median vs. tier-scoped-median
- Relationship between the new relative/median outlier section and the existing fixed-threshold slow_runs (1800s) mechanism needs an explicit Plan-phase decision so the two signals don't read as redundant or conflicting

## Implementation Notes
Added `OUTLIER_MEDIAN_MULTIPLIER = 3` (calibratable, mirroring `cost_proxy.py`'s own "weights are
calibratable" convention) and `_OUTLIER_MIN_GROUP_SIZE = 3` (a 1-2-point median is not a meaningful
baseline — a group below this is skipped entirely, no outliers flagged for it). A single generic
`_flag_outliers(items, group_key_fn, value_fn, multiplier)` helper groups items, computes each
group's `statistics.median`, and returns items exceeding `multiplier * median`, sorted by ratio
descending — reused for both duration_s and cost_proxy_score rather than writing two near-identical
loops.

**Two Plan-phase decisions the ticket explicitly required, made and documented here, not left
implicit**:
1. **Median basis for `duration_s`**: **tier-scoped**, not global. `runs.jsonl` has no `phase`
   field (only `tier`), and a global median would be meaningless across wildly different natural
   durations (an epic and a hotfix don't share a "typical" duration) — comparing against a single
   global median would flag nearly every epic as "an outlier" for no real reason. Verified against
   real data: `TCK-20260710-SIMQ-DEPTH-SOCIAL` (49729s) correctly flags at 15.3x its own
   `standard`-tier median (3254s).
2. **Relationship to `slow_runs`**: kept **both**, unmerged, clearly labeled as answering different
   questions. `slow_runs` = "was this literally a long time" (fixed 1800s absolute threshold,
   unchanged). `outliers` = "was this way more than similar runs typically take" (relative, Nx
   group median). The two can and do overlap on the same run — that's expected, not a bug — the
   rendered `## Outliers` section opens with an explicit sentence distinguishing it from Slow Runs
   immediately above it, so a reader isn't misled into thinking they're duplicate signals.

`cost_proxy_score` outliers are grouped by **normalized** phase, reusing `_normalize_phase()` from
`TCK-20260719-PHASE-AGENT-CASE-FOLD` (the immediately-preceding ticket in this same batch) — a
casing-fragmented phase would otherwise silently split one real group into several
too-small-to-median groups, undermining the outlier detection itself. This is a direct, deliberate
synergy between the two tickets, not a coincidence.

**Real-data verification, not just synthetic fixtures**: ran the fix against the full live
`agent-monitoring/{runs,events}.jsonl` corpus (`generate_retro.py --all`). It correctly, and
automatically, surfaced D25's own original finding (`experiments/audit_expansion/PROPOSAL.md`,
"Top investigator/Investigate call scored 34,837... 10x spread") as a live-computed 444.1x
cost-proxy-score outlier for `TCK-20260710-SIMQ-DEPTH-SOCIAL`'s `Investigate` phase — confirming
the fix genuinely closes the "zero recorded investigation" gap D25 identified, not just passing
synthetic tests. 26 duration outliers and 82 cost-proxy-score outliers found across the full
historical corpus (going forward this will naturally shrink as more data accumulates around
typical values). **Found, unrelated, pre-existing bug** (not fixed here, out of scope): running
`generate_retro.py --days N` crashes (`TypeError: '>=' not supported between instances of 'float'
and 'str'`) on a `runs.jsonl` record whose `start_ts` is a float, not a string — confirmed via
`git stash` that this crash is identical with and without this ticket's changes, so it predates
this work. Worth its own future ticket.

**Explicitly out of scope, as the ticket's own AC requires stating plainly**: the Agent Ops
Dashboard does **not** get this automatically. `src/api/agent_ops_dashboard/ingest.py::get_agent_monitoring_stats()`
builds `AgentMonitoringStats` via explicit per-field typed submodel construction
(`RunSummaryStats(**metrics["run_summary"])`, etc.), never `**metrics` passthrough — the new
`outliers` key is silently absent from that model until `models.py`/`ingest.py` are separately,
deliberately updated to add it. No such change was made in this ticket. Verified no regression to
the dashboard's existing behavior by re-running `test_agent_ops_dashboard_stats.py` (8/8 passing,
unmodified).

**Deviation from normal Scope→Investigate→Plan→Review→Implement ordering, self-flagged per this
project's traceability rule**: implemented directly in the same pass as investigation, with staging
artifacts written retroactively after implementation and full test verification — same pattern as
the two preceding tickets in this batch.

## Test Summary
- `python3 -m pytest tests/tools/test_generate_retro.py -q` — 33/33 passing (7 new: tier-scoped
  vs. global median proof, null-exclusion from both flagging and median basis, minimum-group-size
  skip, normalized-phase grouping for cost_proxy_score, null cost_proxy_score exclusion, section
  omitted when nothing flagged, section rendered with correct content when something is).
- `python3 -m pytest tests/tools/ -q -k "monitoring or record_events or record_run or cost_proxy or sidecar or agent_ops_dashboard or generate_retro or validate_agent"` — 169/169 passing.
- `python3 tools/agent-monitoring/generate_retro.py --all` — real end-to-end run against the full
  live corpus (677 runs, 3435 events), correctly surfacing 26 duration outliers and 82
  cost-proxy-score outliers, including D25's own originally-cited 444.1x finding.

## Files Changed
- tools/agent-monitoring/generate_retro.py (`_flag_outliers()` helper, `OUTLIER_MEDIAN_MULTIPLIER`/
  `_OUTLIER_MIN_GROUP_SIZE` constants, new `outliers` key wired into `compute_retro_metrics()`, new
  "## Outliers" Markdown section in `generate()`)
- tests/tools/test_generate_retro.py (1 test updated for the new key, 7 new tests)
- docs/parity_ledger/infrastructure.yaml (new entry INFRA-284)

## Completion Summary
Added a new `outliers` key to `compute_retro_metrics()`'s return dict, flagging `duration_s` values
(grouped by tier) and `cost_proxy_score` values (grouped by normalized phase) exceeding 3x their
group's median — a purely relative visibility signal, explicitly not claiming to explain *why* a
value is high, matching the ticket's own framing. Two required Plan-phase decisions (median basis;
relationship to the existing `slow_runs` mechanism) were made and documented explicitly, not left
implicit. Verified end-to-end against the full real production corpus, where it automatically
surfaced D25's own originally-cited outlier finding. The ticket's own correction of the source
proposal's false "dashboard benefits automatically" claim is preserved — no dashboard/API changes
were made, confirmed via passing, unmodified dashboard tests.
