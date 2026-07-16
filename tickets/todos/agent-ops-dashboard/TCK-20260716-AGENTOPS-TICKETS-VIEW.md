---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260716-AGENTOPS-TICKETS-VIEW
phase: open
date: 2026-07-16
tags: []
---

# TCK-20260716-AGENTOPS-TICKETS-VIEW

## Title
Tickets view: filterable/sortable table over ticket lifecycle

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author wants a table view over all tickets (spanning tickets/inprogress, tickets/done, and tickets/todos) that can be filtered and sorted by tier, layer, status, priority, and tag, with each row linking to the matching run's Replay timeline. This is the frontend half of the concern; the backend endpoint it consumes is a separate, shared piece of infrastructure owned by the backend ticket in this same batch.

## Scope
- Build a TicketsView frontend component that renders a table of tickets sourced from GET /api/tickets
- Implement a filter bar for tier/layer/status/priority/tag with AND-across-dimensions, OR-within-tag semantics
- Implement column sorting by tier/layer/status/priority/tag
- Each row links to the Replay timeline view for its matching run(s)
- Render null tier/priority/type as null/empty (not an error or placeholder) when a ticket's body lacks those sections

## Out of Scope
- Implementing the /api/tickets endpoint itself, ticket frontmatter+body parsing, or ticket-to-run join logic (owned by AGENTOPS-DASHBOARD-BACKEND's ingest.py)
- The Replay timeline detail view content itself (owned by AGENTOPS-REPLAY-TIMELINE)
- The Recent Activity Gantt view (owned by AGENTOPS-ACTIVITY-GANTT)
- Backend caching or concurrency handling (owned by AGENTOPS-DASHBOARD-BACKEND)

## Acceptance Criteria
- [ ] Table renders rows from GET /api/tickets covering tickets/inprogress/, tickets/done/, and tickets/todos/
- [ ] Filtering by tier/layer/status/priority/tag narrows rows correctly (AND across dimensions, OR within tag)
- [ ] Each row's linked-runs control surfaces every matching_runs entry (sorted start_ts descending) as links to that run's Replay timeline, not collapsed to one
- [ ] A ticket with null tier/priority/type (missing body section) renders as null/empty in the table, not an error or placeholder

## Related Tickets
- TCK-20260716-AGENTOPS-DASHBOARD-BACKEND
- TCK-20260529-OBS-PHASE27-API-DASHBOARD
- TCK-20260614-RESOURCE-DASHBOARD
- TCK-20260607-MON-DASHBOARD

## Related Docs
- docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/TEST_PLAN.md
- experiments/agent_ops_dashboard/IMPLEMENTATION_CONTEXT.md
- docs/guides/ticket_reporting.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/validate_frontmatter.py
- tools/generate_registry.py
- src/api/server.py
- docs/REGISTRY.yaml
- tickets/working_log.csv
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/IMPLEMENTATION_CONTEXT.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md
- experiments/agent_ops_dashboard/TEST_PLAN.md
- docs/guides/ticket_reporting.md
- expected: frontend/src/views/TicketsView.tsx

## Assumptions / Open Questions
- docs/REGISTRY.yaml is not a viable data source for this view since it only covers tickets/done/ and omits status/layer/priority; the view depends entirely on the backend ticket's /api/tickets endpoint reflecting full lifecycle coverage
- Ticket-run join collisions (43/618 confirmed) mean the UI must show multiple linked runs per ticket, not assume a 1:1 relationship

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
