---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260720-PROGRESS-TIMELINE-VIEW
phase: open
date: 2026-07-20
tags: [dashboard, observability]
---

# TCK-20260720-PROGRESS-TIMELINE-VIEW

## Title
New ProgressTimelineView component replacing the Gantt-style Recent Activity view

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Build a new ProgressTimelineView.tsx component that replaces RecentActivityGantt.tsx, dropping the 'Gantt' naming. Wraps echarts-for-react's <ReactECharts>, retiring GanttBar.tsx, TimeAxis.tsx, Legend.tsx, and GanttBar's toPercent() math. Scope includes: a useRunTimelinesPolling(sinceIso) hook (sibling to useRunsPolling) polling the new bulk timeline endpoint; a pure toChartOption(runs, entriesByRun, nowIso) transform producing one y-axis category per run_id (newest-first) with one custom-series segment per phase, plus a trailing 'live' segment for in-progress runs; two dataZoom instances (inside + slider); a tooltip.formatter (run_id, tier, workflow, phase, agent, status, duration); and a rewrite of the existing Gantt test suite.

## Scope
- Create dashboard-frontend/src/views/ProgressTimelineView.tsx replacing RecentActivityGantt.tsx in App.tsx, wrapping echarts-for-react's <ReactECharts>
- Add useRunTimelinesPolling(sinceIso) hook (sibling to useRunsPolling) polling the bulk GET /api/runs/timeline endpoint, mirroring useRunsPolling's polling/merge/sort pattern
- Add pure toChartOption(runs, entriesByRun, nowIso) transform producing one y-axis category per run_id (newest-first, matching mergeAndSortRuns' sort), one custom-series segment per phase using the new phase-color palette module, plus a trailing 'live' segment for is_inferred_active runs
- Wire two dataZoom instances (type 'inside' + type 'slider'), both purely client-side (no new network requests triggered by zoom/pan)
- Add tooltip.formatter surfacing run_id, tier, workflow, phase, agent, status, duration
- Delete GanttBar.tsx, TimeAxis.tsx, Legend.tsx and GanttBar's toPercent() math once no longer imported
- Rewrite the Gantt test suite to assert toChartOption's returned data structure directly plus a smoke test that ReactECharts receives a non-null option, dropping DOM left/width percentage and gantt-bar--* CSS class assertions
- Explicitly decide whether the new ECharts tooltip.formatter surfaces GlossaryTooltip phase/agent glossary text, given tooltip.formatter runs in a non-React/HTML-string context and existing GlossaryTooltip hover copy cannot be reused verbatim

## Out of Scope
- Implementing the bulk timeline endpoint or the echarts dependency/palette module themselves — this ticket only consumes them
- The range-control UI (quick-range presets + custom picker) — covered by a separate ticket
- Updating docs/observability/agent_ops_dashboard_contract.md and docs/guides/agent_ops_dashboard.md, which name the retiring components — deferred to the separate C5 docs-update follow-up
- C5 docs update (docs/guides/agent_ops_dashboard.md, docs/observability/agent_ops_dashboard_contract.md) is deferred to a separate follow-up ticket, not covered here

## Acceptance Criteria
- [ ] toChartOption(runs, entriesByRun, nowIso) returns an EChartsOption with one y-axis category per run_id, ordered newest-first (matching mergeAndSortRuns' sort), independent of DOM rendering
- [ ] for N settled entries, toChartOption produces exactly N-1 segments (one per consecutive entries[i].ts -> entries[i+1].ts pair) plus, for is_inferred_active runs, exactly one additional trailing 'live' segment from the last known timestamp to nowIso, visually distinguishable from settled segments
- [ ] ProgressTimelineView renders exactly one ReactECharts instance with two dataZoom entries (type 'inside' + type 'slider'), both purely client-side (no new network requests triggered by zoom/pan)
- [ ] the rewritten test suite no longer asserts DOM left/width percentages or gantt-bar--* CSS classes via toPercent, asserting toChartOption's returned data structure directly plus a smoke test that ReactECharts receives a non-null option
- [ ] GanttBar.tsx, TimeAxis.tsx, Legend.tsx and toPercent() are deleted/no longer imported once ProgressTimelineView.tsx replaces RecentActivityGantt.tsx in App.tsx, with the 'activity' view and onSelectRun row-click-through to Replay preserved

## Related Tickets
- TCK-20260716-AGENTOPS-ACTIVITY-GANTT
- TCK-20260717-GANTT-TIME-AXIS
- TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT
- TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND
- TCK-20260718-GLOSSARY-TOOLTIPS-EPIC
- TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS
- TCK-20260716-AGENTOPS-REPLAY-TIMELINE
- TCK-20260720-BULK-RUN-TIMELINE
- TCK-20260720-ECHARTS-PHASE-PALETTE

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_progress_timeline.md
- docs/guides/agent_ops_dashboard.md
- docs/observability/agent_ops_dashboard_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- dashboard-frontend/src/views/RecentActivityGantt.tsx
- dashboard-frontend/src/components/GanttBar.tsx
- dashboard-frontend/src/components/TimeAxis.tsx
- dashboard-frontend/src/components/Legend.tsx
- dashboard-frontend/src/api.ts
- dashboard-frontend/src/App.tsx
- dashboard-frontend/package.json
- dashboard-frontend/src/test/RecentActivityGantt.test.tsx
- dashboard-frontend/src/test/GanttBar.test.tsx
- dashboard-frontend/src/test/TimeAxis.test.tsx
- dashboard-frontend/src/test/App.test.tsx
- dashboard-frontend/src/test/useRunsPolling.test.ts
- src/api/agent_ops_dashboard/main.py
- src/api/agent_ops_dashboard/models.py
- src/api/agent_ops_dashboard/ingest.py

## Assumptions / Open Questions
- Hard dependency on TCK-20260720-BULK-RUN-TIMELINE and TCK-20260720-ECHARTS-PHASE-PALETTE — both must land before this ticket can be implemented; this ticket cannot proceed standalone
- docs/observability/agent_ops_dashboard_contract.md and docs/guides/agent_ops_dashboard.md both describe the retiring components (RecentActivityGantt/GanttBar/Legend/TimeAxis) by name and will stay stale until the deferred C5 docs-update ticket lands; this is an explicit known-gap, not silently left unstated
- App.tsx hardcodes 'activity' as the nav view name/label tied to RecentActivityGantt — whether the nav label/testid ('Recent Activity' button text) also changes is an open implementation decision to resolve during this ticket; if changed, App.test.tsx's nav-click-flow assertions must be updated in the same ticket
- GanttBar's tooltip content was a '·'-joined string; ECharts tooltip.formatter runs in a non-React/HTML-string context, so existing GlossaryTooltip-based hover copy cannot be reused verbatim and needs its own string-formatting path
- The dataviz skill discoverability gap noted on the palette ticket is not blocking at the orchestrator level for this ticket either

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
