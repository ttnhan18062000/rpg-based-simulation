---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260716-AGENTOPS-DASHBOARD-BACKEND
phase: open
date: 2026-07-16
tags: [api-design]
---

# TCK-20260716-AGENTOPS-DASHBOARD-BACKEND

## Title
Backend API + ingest layer over tickets and agent-monitoring data

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author wants a FastAPI backend (main.py, ingest.py, models.py) exposing /api/tickets, /api/runs, /api/runs/{run_id}, /api/runs/{run_id}/timeline, and /api/health, returning only Pydantic schemas. ingest.py should own all file reads, rebuild an in-memory cache on mtime change, and reuse existing legacy-schema tolerance and frontmatter-parsing utilities rather than reimplementing them. It must correctly join tickets to runs (all matching runs.jsonl rows, not just the first) and be safely concurrent, since this is the shared foundation the three frontend views in this batch all depend on.

## Scope
- Create a new FastAPI app (main.py) exposing GET /api/tickets, GET /api/runs, GET /api/runs/{run_id}, GET /api/runs/{run_id}/timeline, GET /api/health
- Create ingest.py owning all file reads: parse frontmatter+body sections directly across tickets/inprogress/, tickets/done/, tickets/todos/ (docs/REGISTRY.yaml is not used as a source); load agent-monitoring runs.jsonl/tools.jsonl/events.jsonl reusing validate.py's legacy allowlists
- Create models.py with typed Pydantic response models for every route (e.g. TicketSummary, RunSummary, RunTimeline) — no raw dict/domain-object payloads
- Implement an in-memory cache rebuilt on file mtime change, reusing src/api/read_model_cache.py's RLock-per-method concurrency pattern
- Implement the ticket-to-run join returning all matching runs.jsonl rows for a ticket_id (not just the first), sorted start_ts descending
- Implement is_inferred_active computation (ACTIVE_WINDOW_MINUTES=10 default) for runs present in tools.jsonl but absent from runs_by_id
- Implement files_touched derivation for /api/runs/{run_id}/timeline: deduplicated-by-path from tool_calls[].input_summary restricted to Read/Edit/Write/MultiEdit

## Out of Scope
- Any frontend component or view (TicketsView, RecentActivityGantt, ReplayTimelineView — owned by AGENTOPS-TICKETS-VIEW, AGENTOPS-ACTIVITY-GANTT, AGENTOPS-REPLAY-TIMELINE)
- Build/serve tooling, Makefile targets, or static-file packaging (owned by AGENTOPS-BUILD-SERVE)
- Fixing the live phase/agent null-labeling gap (independent sibling ticket)
- Retention/rotation policy for agent-monitoring/*.jsonl

## Acceptance Criteria
- [ ] All 5 routes declare typed Pydantic response models (e.g. response_model=List[TicketSummary]) returning typed instances, never raw dict/domain-object payloads — src/api/routes/history.py's List[dict]+.model_dump() pattern is explicitly not mirrored
- [ ] For a ticket_id with N>1 matching runs.jsonl rows (43/618 confirmed in current data), /api/tickets' matching_runs field contains all N rows sorted start_ts descending, not collapsed to one
- [ ] ingest.py imports and calls extract_frontmatter(), load_jsonl(), and validate.py's legacy allowlists rather than reimplementing parsing logic
- [ ] Concurrent requests during a cache rebuild never observe a partially-rebuilt structure, verified via a concurrency test using an RLock-per-method pattern matching ReadModelCache's exact locking approach
- [ ] GET /api/runs/{run_id} returns 404 (not 500 or an empty 200) when run_id matches neither runs_by_id nor the inferred-active set
- [ ] A ticket missing '## Tier'/'## Priority'/'## Type' body sections surfaces those fields as null in the response, not an error or placeholder value
- [ ] A run_id present in tools.jsonl within ACTIVE_WINDOW_MINUTES=10 and absent from runs_by_id returns is_inferred_active=true with inferred_start_ts taken from the first tools.jsonl timestamp for that run
- [ ] On completion, is_inferred_active flips true->false and start_ts/end_ts switch to authoritative values; no request ever observes a completed run still flagged active

## Related Tickets
- TCK-20260518-READ-MODEL-CACHE
- TCK-20260705-MONITORING-RUNID-JOIN

## Related Docs
- docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/IMPLEMENTATION_CONTEXT.md
- docs/agent-monitoring/schema.md
- docs/guidelines/design_patterns.md
- docs/observability/read_model_service_contract.md
- docs/engine/architecture_reference.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/validate_frontmatter.py
- tools/agent-monitoring/query.py
- tools/agent-monitoring/validate.py
- tools/generate_registry.py
- src/api/read_model_cache.py
- src/observability/reporting/history_query.py
- src/api/routes/history.py
- src/api/routes/health.py
- src/observability/reporting/retention.py
- docs/agent-monitoring/schema.md
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/IMPLEMENTATION_CONTEXT.md
- expected: src/api/agent_ops_dashboard/main.py
- expected: src/api/agent_ops_dashboard/ingest.py
- expected: src/api/agent_ops_dashboard/models.py

## Assumptions / Open Questions
- src/api/routes/health.py exists but is currently empty (0 lines), so /api/health's shape must be derived from PROPOSAL.md §6 alone with no existing pattern to mirror
- docs/REGISTRY.yaml is confirmed not viable as the tickets data source since it only covers tickets/done/ and omits status/layer/priority; frontmatter+body must be parsed directly across all 3 lifecycle directories
- agent-monitoring/*.jsonl has no retention/rotation policy; unbounded growth is a known risk not addressed in this ticket
- live_tail phase/agent will remain null until the independent sibling fix lands; accepted as a known limitation, not a bug in this ticket's scope

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
