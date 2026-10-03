---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260720-TIMELINE-RANGE-CONTROL
phase: done
date: 2026-07-20
tags: [dashboard, observability]
---

# TCK-20260720-TIMELINE-RANGE-CONTROL

## Title
Range-control component for the timeline (quick-range presets + custom picker)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add a range-control UI placed above the timeline chart offering quick-range presets (1h/6h/24h/7d) plus a custom start/end picker, replacing today's hardcoded SINCE_WINDOW_MS = 24h default. Sets sinceIso/untilIso, which bounds what the bulk timeline endpoint fetches from the server — a distinct layer from the chart's own client-side dataZoom, and the two must not be conflated or made to drive each other.

## Scope
- Add a range-control component placed above the ProgressTimelineView chart, offering quick-range presets (1h/6h/24h/7d) plus a custom start/end picker
- Replace the hardcoded SINCE_WINDOW_MS = 24h default with the range-control's sinceIso/untilIso state, wired into useRunTimelinesPolling's fetch and bounding the bulk endpoint request via its `until` param
- Quick-range preset selection sets sinceIso = now - <preset duration> and untilIso = now, passed to the bulk timeline fetch (not just applied to chart dataZoom)
- Custom start/end picker emits zero-padded ISO 8601 UTC strings matching the backend's lexical-string-comparison convention; use a plain <input type="datetime-local"> to stay consistent with the dashboard's zero-new-npm-dependency precedent (Stats tab), since no existing date/time picker component exists today
- On initial mount with no user interaction, sinceIso/untilIso reproduce today's default (now-24h to now) — drop-in replacement with no default-behavior regression
- Keep the range-control's sinceIso/untilIso state independent from the chart's own client-side dataZoom state, verified as two separate, non-interacting layers

## Out of Scope
- Implementing the bulk endpoint's `until` param itself — this ticket only consumes it once available
- Implementing the ProgressTimelineView chart itself — this ticket only places the range-control above it and coordinates rather than independently modifying RecentActivityGantt.tsx/TimeAxis.tsx while they are being retired
- Any change to the chart's own client-side dataZoom behavior
- C5 docs update (docs/guides/agent_ops_dashboard.md, docs/observability/agent_ops_dashboard_contract.md) is deferred to a separate follow-up ticket, not covered here

## Acceptance Criteria
- [ ] selecting a quick-range preset (1h/6h/24h/7d) sets sinceIso = now - <preset duration> and untilIso = now, passed to the bulk timeline fetch (not just applied to chart dataZoom)
- [ ] selecting a custom start/end value sets sinceIso/untilIso to ISO 8601 UTC strings (zero-padded, matching the backend's lexical-string-comparison convention) and triggers a refetch bounded by those exact values
- [ ] on initial mount with no user interaction, sinceIso/untilIso reproduce today's default (now-24h to now) — drop-in replacement for SINCE_WINDOW_MS with no default-behavior regression
- [ ] changing the range control's sinceIso/untilIso does not reset or couple to the chart's independent client-side dataZoom state (verified as two separate, non-interacting state layers)
- [ ] this ticket's server-side bounding depends on the bulk timeline endpoint supporting an `until` query param; if that support is not yet landed, this ticket is blocked on it rather than reimplementing bounding independently

## Related Tickets
- TCK-20260716-AGENTOPS-ACTIVITY-GANTT
- TCK-20260717-GANTT-TIME-AXIS
- TCK-20260720-BULK-RUN-TIMELINE
- TCK-20260720-PROGRESS-TIMELINE-VIEW

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_progress_timeline.md

## Related Stored Artifacts
None.

## Related Code Areas
- dashboard-frontend/src/views/RecentActivityGantt.tsx
- dashboard-frontend/src/api.ts
- dashboard-frontend/src/components/TimeAxis.tsx
- dashboard-frontend/src/components/GanttBar.tsx
- src/api/agent_ops_dashboard/main.py

## Assumptions / Open Questions
- Hard dependency on TCK-20260720-BULK-RUN-TIMELINE adding an `until` query param — its originally proposed signature (since/limit/offset only) does not list one; this ticket depends on that ticket providing it rather than independently assuming it exists
- Depends on TCK-20260720-PROGRESS-TIMELINE-VIEW's chart existing first, since the range-control is placed above it — sequencing dependency
- Backend since is compared lexically as a string, never parsed to datetime — the custom picker must emit correctly formatted, zero-padded ISO 8601 UTC strings or lexical bounding silently misbehaves
- No existing date/time picker component or npm dependency exists in dashboard-frontend/src today; a plain <input type="datetime-local"> is assumed to stay consistent with this dashboard's zero-new-npm-dependency precedent, though the original proposal doesn't state this explicitly
- TCK-20260720-PROGRESS-TIMELINE-VIEW already rewrites RecentActivityGantt.test.tsx and retires RecentActivityGantt.tsx/TimeAxis.tsx — this ticket should coordinate with that ticket rather than independently modify the same soon-to-be-retired files
- `layer: observability` chosen because this is a dashboard-frontend UI control for the agent-ops observability dashboard; no more specific registered layer fits

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
