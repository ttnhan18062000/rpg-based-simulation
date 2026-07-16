---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260716-AGENTOPS-ACTIVITY-GANTT
phase: open
date: 2026-07-16
tags: []
---

# TCK-20260716-AGENTOPS-ACTIVITY-GANTT

## Title
Recent Activity view: Gantt-style timeline of runs

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author wants a default-landing Gantt-style view: completed runs shown as solid authoritative bars from runs.jsonl, and runs with recent tools.jsonl activity but no runs.jsonl record yet shown as a visually distinct inferred-live estimate. This is the frontend half of the concern; the underlying is_inferred_active computation is shared infrastructure owned by the backend ticket in this same batch.

## Scope
- Build a RecentActivityGantt frontend component as the dashboard's default-landing view
- Poll GET /api/runs?since=<ISO> and render completed runs as solid authoritative bars using start_ts/end_ts
- Render runs with is_inferred_active=true as visually distinct fill/pattern with an explicit estimate label, never sharing style with authoritative bars
- Implement a settle-transition UI so that when a run flips from active to completed between polls, its bar updates to authoritative style/values without a jarring reload

## Out of Scope
- Implementing /api/runs, the is_inferred_active heuristic, or ACTIVE_WINDOW_MINUTES logic (owned by AGENTOPS-DASHBOARD-BACKEND's ingest.py)
- Fixing live_tail phase/agent always being null (MONITORING_INSTRUMENTATION_GAP — an independent sibling fix, not in scope here)
- The Replay timeline detail view (AGENTOPS-REPLAY-TIMELINE) and Tickets table view (AGENTOPS-TICKETS-VIEW)
- Retention/rotation policy for agent-monitoring/*.jsonl

## Acceptance Criteria
- [ ] GET /api/runs?since=<ISO> results render completed runs as solid bars using authoritative start_ts/end_ts, with is_inferred_active shown false
- [ ] A run present in tools.jsonl within the active window and absent from runs_by_id renders as an inferred-active bar with inferred_start_ts as its start point
- [ ] When a run transitions from active to completed across polls, the UI updates the bar from inferred style to authoritative style/values with no stale 'still active' state ever shown
- [ ] Inferred-active bars are always rendered with a visually distinct fill/pattern and an explicit estimate label, never sharing styling with authoritative completed bars

## Related Tickets
- TCK-20260716-AGENTOPS-DASHBOARD-BACKEND

## Related Docs
- docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md
- docs/plans/agent_ops_dashboard/idea_agent_monitoring_live_phase_label.md
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md
- experiments/agent_ops_dashboard/MONITORING_INSTRUMENTATION_GAP.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- tools/agent-monitoring/post_tool_hook.py
- tools/agent-monitoring/pre_tool_hook.py
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/validate.py
- src/api/read_model_cache.py
- src/api/routes/history.py
- src/observability/reporting/history_query.py
- src/api/server.py
- src/api/ws/stream.py
- docs/agent-monitoring/schema.md
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md
- experiments/agent_ops_dashboard/TEST_PLAN.md
- experiments/agent_ops_dashboard/IMPLEMENTATION_CONTEXT.md
- experiments/agent_ops_dashboard/MONITORING_INSTRUMENTATION_GAP.md
- expected: frontend/src/views/RecentActivityGantt.tsx

## Assumptions / Open Questions
- ACTIVE_WINDOW_MINUTES=10 default (owned by the backend ticket) is not yet validated against real crashed-run timing data; this view's live/estimate rendering depends on that value being reasonable
- live_tail items will always render phase=null/agent=null until the independent MONITORING_INSTRUMENTATION_GAP fix lands; accepted as a known limitation for this view, not blocking

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
