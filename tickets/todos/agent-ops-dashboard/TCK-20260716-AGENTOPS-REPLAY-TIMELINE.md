---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260716-AGENTOPS-REPLAY-TIMELINE
phase: open
date: 2026-07-16
tags: []
---

# TCK-20260716-AGENTOPS-REPLAY-TIMELINE

## Title
Run Detail / Replay timeline view: scrubbable playback of a run

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author wants a detail view for a single completed (or live) run: scrubbable phase-by-phase plus tool-call playback, plus a static files-touched panel. This is the frontend half of the concern; the underlying timeline join and files-touched derivation are shared infrastructure owned by the backend ticket in this same batch.

## Scope
- Build a Replay timeline frontend view: scrubbable phase-by-phase and tool-call playback for a single run, driven by GET /api/runs/{run_id}/timeline
- Build a static files-touched panel from the timeline payload's deduplicated files_touched list
- Implement a scrub/playback control that replays only the already-fetched RunTimeline payload client-side, without triggering new fetches
- Render honest '(phase unknown — run still in progress)' captions for live_tail entries where phase/agent are null

## Out of Scope
- Implementing GET /api/runs/{run_id}/timeline, its seq-ordered join logic, or files_touched derivation from tool_calls[].input_summary (owned by AGENTOPS-DASHBOARD-BACKEND's ingest.py)
- Fixing the live phase/agent null-labeling gap (independent sibling ticket, not this scope)
- The Recent Activity Gantt view (AGENTOPS-ACTIVITY-GANTT) and Tickets table view (AGENTOPS-TICKETS-VIEW)
- Concurrency/RLock implementation in the backend cache (owned by AGENTOPS-DASHBOARD-BACKEND)

## Acceptance Criteria
- [ ] Timeline view renders entries in the order returned by GET /api/runs/{run_id}/timeline (seq ascending), each showing its joined tools.jsonl rows
- [ ] Files-touched panel shows a deduplicated-by-path list restricted to Read/Edit/Write/MultiEdit tool calls, retaining first-seen ts+tool per file
- [ ] When is_live=true, every live_tail item displays phase=null and agent=null explicitly with an '(phase unknown — run still in progress)' caption, never a guessed value
- [ ] Scrubbing the playback control replays the already-fetched timeline payload client-side and triggers no new network fetch

## Related Tickets
- TCK-20260716-AGENTOPS-DASHBOARD-BACKEND

## Related Docs
- docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md
- experiments/agent_ops_dashboard/MONITORING_INSTRUMENTATION_GAP.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md
- experiments/agent_ops_dashboard/MONITORING_INSTRUMENTATION_GAP.md
- experiments/agent_ops_dashboard/IMPLEMENTATION_CONTEXT.md
- experiments/agent_ops_dashboard/TEST_PLAN.md
- src/api/server.py
- src/api/routes/history.py
- src/observability/reporting/history_query.py
- src/api/read_model_cache.py
- tools/agent-monitoring/post_tool_hook.py
- tools/agent-monitoring/pre_tool_hook.py
- docs/agent-monitoring/schema.md
- .claude/workflows/implement-ticket.js
- expected: frontend/src/views/ReplayTimelineView.tsx

## Assumptions / Open Questions
- Frontend currently has zero CI coverage; this view inherits that gap rather than fixing it
- The live phase/agent labeling sibling fix is independent, and this view must render honestly without depending on or blocking it

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
