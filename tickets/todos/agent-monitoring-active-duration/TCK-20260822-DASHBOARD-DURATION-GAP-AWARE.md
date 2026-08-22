---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260822-DASHBOARD-DURATION-GAP-AWARE
phase: open
date: 2026-08-22
tags: [dashboard, agent-monitoring, api-design]
---

# TCK-20260822-DASHBOARD-DURATION-GAP-AWARE

## Title
Surface the active/idle duration split in the agent-ops dashboard

## Status
OPEN

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
- [ ] After the sibling ticket ships, GET /api/stats (ingest.py::get_agent_monitoring_stats) does not raise on the new compute_retro_metrics() output shape -- SlowRunEntry/DurationOutlierEntry/RunSummaryStats in models.py declare whatever new field(s) were added, existing duration_s fields remain populated unchanged (backward compatible).
- [ ] dashboard-frontend/src/api.ts TS interfaces for the same 3 shapes are updated to match the new Pydantic shape.
- [ ] StatsView.tsx's Slow Runs and Duration Outliers tables surface the active/idle distinction visibly (additional column or visual flag), not just carried silently in the API payload.
- [ ] The dashboard continues to source duration data exclusively via compute_retro_metrics() -- no independent duration/gap computation added to ingest.py, preserving the single-shared-utility constraint.

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

## Test Summary

## Files Changed

## Completion Summary
