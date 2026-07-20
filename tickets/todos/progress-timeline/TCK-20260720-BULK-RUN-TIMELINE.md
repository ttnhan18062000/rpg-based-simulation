---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260720-BULK-RUN-TIMELINE
phase: open
date: 2026-07-20
tags: [api-design]
---

# TCK-20260720-BULK-RUN-TIMELINE

## Title
Add bulk run-timeline endpoint GET /api/runs/timeline

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add a new backend endpoint, GET /api/runs/timeline?since=&limit=&offset=, that returns {entries_by_run: Record<run_id, TimelineEntry[]>} for every run in the requested window. It's a bulk sibling of the existing per-run GET /api/runs/{run_id}/timeline endpoint — it must reuse that endpoint's existing entry-loading logic rather than reimplementing it, follow the same since/limit/offset pagination shape as GET /api/runs, and expose a new typed Pydantic response model in models.py. The existing per-run endpoint itself is not modified. This also matters because it is the data source the new ProgressTimelineView (replacing the Gantt view) will poll instead of issuing N per-run calls, and because the range-control component needs an upper time bound this endpoint doesn't yet offer.

## Scope
- Add new route GET /api/runs/timeline?since=&limit=&offset=&until= registered in main.py with a Pydantic response_model
- Add a BulkRunTimeline response model to models.py wrapping entries_by_run: Dict[str, List[TimelineEntry]]
- Refactor DashboardCache.get_timeline() in ingest.py (~lines 656-701) to extract the entries-building loop (~lines 662-683) into a shared private helper, used by both the existing per-run get_timeline() and the new bulk method
- Add a DashboardCache bulk method that filters runs by since/until/limit/offset (mirroring get_runs' filtering) and calls the shared entries-building helper per selected run_id
- Add a new `until` query param to bound the runs window's upper end, needed by the range-control ticket's server-side fetch bounding, since neither GET /api/runs nor the per-run timeline endpoint currently accepts one
- Update test_all_declared_routes_present's hardcoded route-path set to include the new route

## Out of Scope
- No change to the existing single-run GET /api/runs/{run_id}/timeline endpoint or its behavior
- No retrofit of `until` onto GET /api/runs itself — only the new bulk timeline endpoint gains it
- Frontend consumption of this endpoint (useRunTimelinesPolling hook, ProgressTimelineView) — covered by the ProgressTimelineView ticket
- C5 docs update (docs/guides/agent_ops_dashboard.md, docs/observability/agent_ops_dashboard_contract.md) is deferred to a separate follow-up ticket, not covered here

## Acceptance Criteria
- [ ] GET /api/runs/timeline?since=&limit=&offset=&until= is registered with a Pydantic response_model (BulkRunTimeline wrapping entries_by_run: Dict[str, List[TimelineEntry]]), and test_all_declared_routes_present's hardcoded path set is updated to include it
- [ ] the bulk endpoint's per-run TimelineEntry list is byte-identical to what GET /api/runs/{run_id}/timeline returns for that run_id, produced via the same shared entry-building code path (not duplicated)
- [ ] limit/offset/since on the bulk endpoint select the same set of runs as GET /api/runs with identical query params, scoped to entries_by_run's keys
- [ ] the bulk endpoint accepts a new `until` query param bounding the run window's upper end via lexicographic string comparison against RunSummary.start_ts, consistent with since's existing comparison convention — required because the range-control component needs sinceIso AND untilIso and no current endpoint offers an upper bound
- [ ] GET /api/runs/{run_id}/timeline is unmodified — existing tests still pass unchanged
- [ ] the response model is a real Pydantic wrapper verified against test_typed_response_models_not_dict, not a bare dict

## Related Tickets
- TCK-20260716-AGENTOPS-DASHBOARD-BACKEND
- TCK-20260716-AGENTOPS-REPLAY-TIMELINE
- TCK-20260716-AGENTOPS-ACTIVITY-GANTT
- TCK-20260718-AGENTOPS-STATS-API

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/api/agent_ops_dashboard/main.py
- src/api/agent_ops_dashboard/models.py
- src/api/agent_ops_dashboard/ingest.py
- tests/tools/test_agent_ops_dashboard_api_boundary.py
- tests/tools/test_agent_ops_dashboard_api.py
- tests/tools/test_agent_ops_dashboard_ingest.py
- dashboard-frontend/src/api.ts

## Assumptions / Open Questions
- DashboardCache.get_timeline() builds the full RunTimeline object inline with no existing standalone 'build entries for run_id' helper; true reuse requires refactoring get_timeline() to extract the entries-building loop into a shared private method
- get_runs()'s since filter excludes runs with start_ts is None — this ticket must decide/state whether entries_by_run does the same for consistency
- self._lock is a threading.RLock (reentrant), safe for the new bulk method to call both get_runs-style filtering and the shared entry-building helper under one `with self._lock:` block
- This ticket is a hard prerequisite for the ProgressTimelineView ticket, which polls this bulk endpoint via useRunTimelinesPolling, and for the range-control ticket, which depends on this endpoint's new `until` param to bound server-side fetches
- The dashboard is read-only over tickets/** and agent-monitoring/*.jsonl — this endpoint must not write anything

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
