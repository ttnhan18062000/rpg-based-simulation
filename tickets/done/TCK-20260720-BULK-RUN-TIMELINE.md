---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260720-BULK-RUN-TIMELINE
phase: done
date: 2026-07-20
tags: [dashboard, observability, agent-monitoring, api-design]
---

# TCK-20260720-BULK-RUN-TIMELINE

## Title
Add bulk run-timeline endpoint GET /api/runs/timeline

## Status
DONE

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
- [x] GET /api/runs/timeline?since=&limit=&offset=&until= is registered with a Pydantic response_model (BulkRunTimeline wrapping entries_by_run: Dict[str, List[TimelineEntry]]), and test_all_declared_routes_present's hardcoded path set is updated to include it
- [x] the bulk endpoint's per-run TimelineEntry list is byte-identical to what GET /api/runs/{run_id}/timeline returns for that run_id, produced via the same shared entry-building code path (not duplicated)
- [x] limit/offset/since on the bulk endpoint select the same set of runs as GET /api/runs with identical query params, scoped to entries_by_run's keys
- [x] the bulk endpoint accepts a new `until` query param bounding the run window's upper end via lexicographic string comparison against RunSummary.start_ts, consistent with since's existing comparison convention — required because the range-control component needs sinceIso AND untilIso and no current endpoint offers an upper bound
- [x] GET /api/runs/{run_id}/timeline is unmodified — existing tests still pass unchanged
- [x] the response model is a real Pydantic wrapper verified against test_typed_response_models_not_dict, not a bare dict

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

Implemented per `staging_artifacts/TCK-20260720-BULK-RUN-TIMELINE/plan.md` exactly, in the
plan's own step order:

1. **`_build_timeline_entries()` extraction** — pulled `get_timeline()`'s raw-events-sort +
   entries/entry_dicts-building loop (previously inline at `ingest.py:687-708`) into a new
   private method `_build_timeline_entries(self, run_id) -> tuple[list[TimelineEntry],
   list[dict]]`, placed directly above `get_timeline()`. `get_timeline()` now calls it at one
   line (`entries, entry_dicts = self._build_timeline_entries(run_id)`) and is otherwise
   unchanged in its own body. **One deviation from the plan surfaced here** — see below and
   `plan.md`'s new "Deviations" section.
2. **`DashboardCache.get_bulk_timeline()`** — new public method added directly below
   `get_timeline()`, accepting `since`/`until`/`limit`/`offset` (keyword-only). Duplicates (does
   not call) `get_runs()`'s `all_run_ids` build + per-run-id filter loop + sort + slice, adding a
   new `until` branch alongside the existing `since` branch in the same loop, before sort+slice,
   using the identical `start_ts is None or ...` guard shape. Calls
   `self._build_timeline_entries(s.run_id)` once per selected run inside the same
   `with self._lock:` block (safe: `self._lock` is a reentrant `RLock`), discarding
   `entry_dicts`. Does not call `get_runs()` and does not compute `files_touched`/`live_tail`/
   `is_live`.
3. **`BulkRunTimeline` model** (`models.py`) — added after `GlossaryResponse`, its closest shape
   precedent: `entries_by_run: Dict[str, List[TimelineEntry]]`.
4. **Route registration** (`main.py`) — `GET /api/runs/timeline` registered between the existing
   `GET /api/runs` and `GET /api/runs/{run_id}` routes (not after), avoiding the FastAPI
   single-path-segment wildcard shadowing hazard the plan flagged. `limit`/`offset` bounds
   (`ge=1, le=100` / `ge=0`) match `/api/runs`'s existing bounds, not `/api/tickets`'s wider
   `le=500`. No `provider`/`execution_id`/`ticket_id`/`status`/`workflow` exposed.
5. **`test_all_declared_routes_present`** — added `"/api/runs/timeline"` to the literal path set.
6. **7 new cache-layer tests** added to `tests/tools/test_agent_ops_dashboard_ingest.py`
   (plus a new `_write_runs_events_tools()` fixture helper), covering: identical entries between
   `get_timeline()` and `get_bulk_timeline()` for the same run; same run-id selection as
   `get_runs()` for identical `since`/`limit`/`offset`; `until` upper-bound exclusion; `until`'s
   `None`-start_ts exclusion (using a real inferred-active run derived from a live `tools.jsonl`
   tail, consistent with `since`'s existing `None`-guard); `since`+`until` combining as an
   inclusive window; limit/offset applied *after* since/until filtering (the plan's
   highest-value anti-drift guard — 5-run fixture, window matches 3, `limit=1, offset=1` lands on
   the filtered set's 2nd run, not the unfiltered set's); and an empty-window edge case returning
   `{}` rather than erroring.
7. **4 new API-layer tests** added to `tests/tools/test_agent_ops_dashboard_api.py`: 200 +
   `entries_by_run` shape (also asserts `files_touched`/`live_tail`/`is_live` are absent from the
   response body); `limit=0`/`limit=101`/`offset=-1` all 422; `since`/`until` pass-through to the
   cache at the HTTP boundary; and the bulk route's `entries_by_run[run_id]` matching the per-run
   route's `entries` JSON byte-for-byte for the same run — this last test is also the concrete
   proof the route-ordering fix works (a shadowed route would 404 here, not 200).
8. **Parity ledger** — added `INFRA-301` to `docs/parity_ledger/infrastructure.yaml` (confirmed
   `INFRA-300` was still the tail at implementation time, matching the investigation's
   prediction). `status: verified`, `priority: P2`, `proof_type: regression`, `test_path`
   pointing at `test_bulk_run_timeline_route_matches_per_run_route_for_same_run_id`.
   `INFRA-275`/`277`/`278`/`279` and every other existing entry left untouched. Validated the
   full file still parses as YAML and the new entry passes the `schema.json` JSON Schema
   individually (23 pre-existing schema violations elsewhere in the file, e.g. legacy
   `proof_type: feature`/`architecture` values and non-numeric IDs like `INFRA-PACK-001`, are
   unrelated pre-existing debt, not introduced by this change).
9. **Full scoped regression run** — all 59 tests across
   `test_agent_ops_dashboard_ingest.py`/`test_agent_ops_dashboard_api.py`/
   `test_agent_ops_dashboard_api_boundary.py`/`test_agent_ops_dashboard_concurrency.py` pass.
   Also ran the two optional extra files
   (`test_agent_ops_dashboard_frontend_api_surface.py`, `test_agent_ops_dashboard_serve.py`,
   7 more tests) per the plan's note that this costs nothing extra — all pass (66 total).

**Deviation from plan (Step 1):** the plan's own reproduced code for `get_timeline()` shows a
reference to the loop's local `raw_events` variable *after* the loop, inside the `is_live` block
(`known_seqs = {e.get("seq") for e in raw_events}`), which the plan's prose ("everything after
that line is untouched") did not account for once `raw_events` became local to
`_build_timeline_entries()`. Fixed by deriving `known_seqs` from the helper's returned `entries`
instead (`{ent.seq for ent in entries}`) — behavior-identical, since `TimelineEntry.seq` is an
unmodified passthrough of `e.get("seq")`. Recorded in `plan.md`'s new "Deviations" section
(Revision 1). No other deviation from the plan.

## Test Summary

Scoped pytest run (per `test_plan.md`'s command), all green:

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py \
  tests/tools/test_agent_ops_dashboard_api.py \
  tests/tools/test_agent_ops_dashboard_api_boundary.py \
  tests/tools/test_agent_ops_dashboard_concurrency.py \
  -q
# 59 passed
```

Plus the two optional extra files (not required by scope, cost nothing extra):
```
python3 -m pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py \
  tests/tools/test_agent_ops_dashboard_serve.py -q
# 7 passed
```

11 new tests added (7 cache-layer + 4 API-layer), all passing. All pre-existing tests in the
regression surface pass unmodified except the one required literal-set edit
(`test_all_declared_routes_present`). `test_run_timeline_404_for_unknown_run_id` passes
unmodified, confirming the Step 1 refactor changed nothing observable about the existing
per-run endpoint.

## Files Changed

- `src/api/agent_ops_dashboard/ingest.py` — extracted `_build_timeline_entries()`, refactored
  `get_timeline()` to call it, added `get_bulk_timeline()`, added `BulkRunTimeline` import.
- `src/api/agent_ops_dashboard/models.py` — added `BulkRunTimeline` model.
- `src/api/agent_ops_dashboard/main.py` — added `BulkRunTimeline` import, registered
  `GET /api/runs/timeline` between `GET /api/runs` and `GET /api/runs/{run_id}`.
- `tests/tools/test_agent_ops_dashboard_api_boundary.py` — added `"/api/runs/timeline"` to
  `test_all_declared_routes_present`'s literal path set.
- `tests/tools/test_agent_ops_dashboard_ingest.py` — added `_write_runs_events_tools()` fixture
  helper and 7 new tests.
- `tests/tools/test_agent_ops_dashboard_api.py` — added 4 new tests.
- `docs/parity_ledger/infrastructure.yaml` — added `INFRA-301`.
- `staging_artifacts/TCK-20260720-BULK-RUN-TIMELINE/plan.md` — added a "Deviations" section
  (Revision 1) documenting the Step 1 `raw_events` gap and its fix.

## Completion Summary

Added `GET /api/runs/timeline?since=&until=&limit=&offset=`, the bulk sibling of the existing
per-run `GET /api/runs/{run_id}/timeline` endpoint, returning
`{entries_by_run: Dict[run_id, List[TimelineEntry]]}` for every run in a since/until-bounded,
limit/offset-paginated window. Implemented exactly per the approved plan: extracted a shared
`_build_timeline_entries()` helper so both endpoints produce byte-identical entries for the same
run (no duplicated entry-building logic); `get_bulk_timeline()` deliberately duplicates (not
delegates to) `get_runs()`'s since/sort/slice run-selection logic, with the new `until` bound
applied in the same per-run-id filter loop as `since`, before pagination — avoiding the wrong-page
bug that would result from filtering after `get_runs()`'s own slice; the new route is registered
ahead of `/api/runs/{run_id}` to avoid FastAPI's wildcard-shadowing trap. One implementation-time
gap in the plan's Step 1 (a missed `raw_events` reference in `get_timeline()`'s live-tail
computation) was found and fixed with a behavior-identical substitution, documented in `plan.md`.
All 6 acceptance criteria satisfied; 59/59 scoped tests pass (11 new); parity ledger entry
`INFRA-301` added. No frontend, docs, or `get_runs()` changes made — all out of scope per the
ticket.
