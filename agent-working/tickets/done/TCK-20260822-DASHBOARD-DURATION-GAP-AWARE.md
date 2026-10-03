---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260822-DASHBOARD-DURATION-GAP-AWARE
phase: done
date: 2026-08-22
tags: [dashboard, agent-monitoring, api-design]
---

# TCK-20260822-DASHBOARD-DURATION-GAP-AWARE

## Title
Surface the active/idle duration split in the agent-ops dashboard

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The agent-ops dashboard was originally treated as a secondary consumer of run duration, conditional on whether it even surfaced duration at all. Investigation now confirms the premise is true today, not hypothetical: src/api/agent_ops_dashboard/ingest.py imports compute_retro_metrics directly from generate_retro.py, and dashboard-frontend/src/views/StatsView.tsx has live Slow Runs and Duration Outliers tables rendering raw duration_s. Because SlowRunEntry/DurationOutlierEntry/RunSummaryStats in models.py are constructed via explicit SlowRunEntry(**r)-style kwargs unpacking straight from the sibling ticket's compute_retro_metrics() output, this is a hard, real coupling: once that ticket ships its active_duration_s/idle_gap_s fields, the dashboard's Pydantic models, its TypeScript mirrors in api.ts, and StatsView.tsx's rendered tables must be updated in the same or a closely-sequenced change, or GET /api/stats breaks outright on the changed shape. This ticket makes that active/idle distinction visible in the dashboard's Slow Runs and Duration Outliers tables, strictly by consuming the sibling ticket's shared computation -- no independent duration/gap logic is added to ingest.py.

## Scope
- Update src/api/agent_ops_dashboard/models.py: SlowRunEntry, DurationOutlierEntry, OutlierStats, and RunSummaryStats gain whatever new field(s) the sibling ticket's compute_retro_metrics() output adds (active_duration_s, idle_gap_s), with existing duration_s fields remaining populated unchanged.
- Update src/api/agent_ops_dashboard/ingest.py's _build_run_summary (L349-383) and stats passthrough construction (L857-892) only as needed to keep the SlowRunEntry(**r)-style unpacking working against the updated output shape -- no independent duration/gap computation added.
- Update dashboard-frontend/src/api.ts TS interfaces (L151,187,194,210) to mirror the updated Pydantic shapes.
- Update dashboard-frontend/src/views/StatsView.tsx's Slow Runs table (L349-379) and Duration Outliers table (L382-419) to visibly surface the active/idle distinction (additional column or visual flag), not just carry it silently in the payload.
- Update/extend tests/tools/test_agent_ops_dashboard_stats.py and dashboard-frontend/src/test/StatsView.test.tsx to cover the new fields/columns.
- Flag RunSummary.duration_s (ingest.py L349-358, models.py L87) as a dormant second raw-passthrough field, currently unused by any frontend render site, so a future consumer doesn't bypass this fix.

## Out of Scope
- Any independent duration/gap computation in ingest.py -- the dashboard must consume only the sibling ticket's shared duration_utils.py / compute_retro_metrics() output, never recompute gaps itself.
- Starting implementation before the sibling ticket's duration_utils.py exists and generate_retro.py's output shape is finalized -- this ticket is strictly sequenced behind it.

## Acceptance Criteria
- [x] After the sibling ticket ships, GET /api/stats (ingest.py::get_agent_monitoring_stats) does not raise on the new compute_retro_metrics() output shape -- SlowRunEntry/DurationOutlierEntry/RunSummaryStats in models.py declare whatever new field(s) were added, existing duration_s fields remain populated unchanged (backward compatible).
- [x] dashboard-frontend/src/api.ts TS interfaces for the same 3 shapes are updated to match the new Pydantic shape.
- [x] StatsView.tsx's Slow Runs and Duration Outliers tables surface the active/idle distinction visibly (additional column or visual flag), not just carried silently in the API payload.
- [x] The dashboard continues to source duration data exclusively via compute_retro_metrics() -- no independent duration/gap computation added to ingest.py, preserving the single-shared-utility constraint.

## Related Tickets
- TCK-20260709-AGENT-MONITORING-DURATION
- TCK-20260719-RETRO-OUTLIER-FLAGS
- TCK-20260818-STANDARD-DASHBOARD-STATS-TABLES-SEARCH-SORT-PAGE
- TCK-20260728-RETRIEVAL-BASELINE-METRICS
- TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT

## Related Docs
- docs/parity_ledger/infrastructure.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/api/agent_ops_dashboard/ingest.py
- src/api/agent_ops_dashboard/models.py
- dashboard-frontend/src/views/StatsView.tsx
- dashboard-frontend/src/api.ts
- tools/agent-monitoring/generate_retro.py

## Assumptions / Open Questions
- Hard dependency on the sibling ticket: if its output shape changes without updating models.py in the same session, /api/stats breaks outright (Pydantic **kwargs unpack raises on unexpected/missing keys) -- this is a real coupling, not hypothetical.
- RunSummary.duration_s (ingest.py L349-358, models.py L87) is a second independent raw-passthrough field, currently unused by any frontend render site, but would bypass any fix applied only to the Stats-tab path if a future view starts rendering it directly -- flagged as dormant, not addressed by this ticket unless a render site appears.
- Whether docs/parity_ledger/infrastructure.yaml's existing duration_s entries need updating as part of this change or as part of the sibling ticket is not settled by investigation and should be resolved during planning.
- Scope must stay strictly sequenced behind the sibling ticket -- attempting dashboard-side changes before duration_utils.py exists and generate_retro.py's output shape is finalized means guessing the shape twice.

## Implementation Notes
Corrected an overstated claim in this ticket's own original text during investigation: it claimed
`SlowRunEntry(**r)`-style kwargs unpacking "breaks outright" on the sibling ticket's new fields.
Empirically false, verified directly before writing any code — neither `SlowRunEntry` nor
`DurationOutlierEntry` declares `model_config = ConfigDict(extra="forbid")`, so Pydantic's default
`extra="ignore"` already silently dropped the new keys rather than raising.
`tests/tools/test_agent_ops_dashboard_stats.py` (17/17) already passed against the sibling
ticket's shipped shape before this ticket began. This doesn't change the real scope (the fields
should still be surfaced, not silently discarded) — it changes the severity framing from "prevents
a crash" to "surfaces data that was being silently dropped." Disclosed here rather than carried
forward silently.

No change needed at `ingest.py`'s construction site itself (`SlowRunEntry(**r)`/
`DurationOutlierEntry(**d)`, L857-892) — it already forwards whatever keys the dict contains;
adding the fields to the Pydantic models was sufficient for them to be captured and returned by
the real API. Verified end-to-end (not just at the model-unit level) via a new test writing real
runs.jsonl/events.jsonl fixtures and reading the split back out through
`ingest.DashboardCache.get_agent_monitoring_stats()`.

`RunSummary.duration_s` (ingest.py L349-383, a second, independent raw-duration passthrough)
confirmed genuinely dormant — no `.tsx` file references it — flagged with an inline comment per
scope, not touched.

`dashboard-frontend/` has no committed `node_modules/` in a fresh worktree; symlinked to the main
checkout's already-installed one (gitignored, not committed) to run `npm test`/`tsc -b` for real
rather than skipping frontend verification.

## Test Summary
- `pytest tests/tools/test_agent_ops_dashboard_stats.py -q` → 19 passed (17 pre-existing + 2 new).
- `npm test -- StatsView` (vitest) → 23 passed (21 pre-existing/updated fixture + 2 new).
- `npx tsc -b` → exit 0, clean compile (the new required TS interface fields don't break any
  existing fixture literal after the one pre-existing fixture at the top of the test file was
  updated to include them).
- Broader backend surface: `pytest tests/tools/test_agent_ops_dashboard_stats.py
  tests/tools/test_duration_utils.py tests/tools/test_generate_retro.py
  tests/tools/test_retrieval_baseline_metrics.py -q` → 210 passed.

## Files Changed
- `src/api/agent_ops_dashboard/models.py` — `SlowRunEntry`/`DurationOutlierEntry` gain
  `active_duration_s`/`idle_gap_s` (Optional[float]=None); `RunSummary` gains a dormant-field
  comment on its own separate `duration_s`.
- `dashboard-frontend/src/api.ts` — matching TS interface fields.
- `dashboard-frontend/src/views/StatsView.tsx` — Active/Idle columns on both tables.
- `tests/tools/test_agent_ops_dashboard_stats.py` — 2 new end-to-end tests.
- `dashboard-frontend/src/test/StatsView.test.tsx` — 1 fixture updated, 2 new tests.
- `docs/parity_ledger/infrastructure.yaml` — new entry `INFRA-393`.

## Completion Summary
Surfaced the sibling ticket's active/idle duration split through the Agent Ops Dashboard: Pydantic
models, TypeScript interfaces, and both Slow Runs/Duration Outliers tables now carry
`active_duration_s`/`idle_gap_s` end-to-end, verified through the real API pipeline (not just a
model-level unit test) and a real rendered-table assertion. No independent duration/gap
computation added to `ingest.py` — it consumes the sibling ticket's shared `compute_retro_metrics()`
output exclusively, as scoped. This ticket's own original claim that the coupling would "break
outright" was checked empirically and found overstated (Pydantic's default already tolerated the
new fields); corrected rather than carried forward. This is the last ticket in the
`agent-monitoring-active-duration` batch — the shared folder (with its `SEQUENCE.md`) moves to
`tickets/done/` as part of this ticket's own Finalize step.
