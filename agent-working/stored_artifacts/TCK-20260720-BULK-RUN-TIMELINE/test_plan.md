---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260720-BULK-RUN-TIMELINE
artifact_type: test_plan
tags: [dashboard, observability, agent-monitoring, api-design]
---

# Test Plan — TCK-20260720-BULK-RUN-TIMELINE

## Regression Surface

All must keep passing unchanged (none of these files' existing test bodies should require edits
except where "New Tests Required" below adds to them):

**Unit / cache-layer (`tests/tools/test_agent_ops_dashboard_ingest.py`)**
- `test_get_runs_filters_by_provider_and_execution_id` — locks `get_runs()`'s existing filter
  behavior; must not regress when the new bulk selection helper is added alongside it.
- `test_legacy_runs_jsonl_schema_generations_do_not_crash_ingest`,
  `test_run_summary_carries_provider_execution_id_ticket_id_when_present`,
  `test_run_summary_labels_legacy_record_as_legacy_not_none_silently` — all exercise
  `_build_run_summary()`, which the new bulk method's selection logic also calls; must be
  unaffected by any refactor.
- `test_inferred_active_*` (5 tests) — `is_inferred_active`/live-run detection feeds both
  `get_runs()` and `get_timeline()`; unaffected by this ticket but must not regress.
- `test_files_touched_dedup_by_path_restricted_to_edit_tools` — exercises
  `extract_files_touched()`, called only from `get_timeline()`'s (unchanged) return path, not from
  the new bulk method — confirms the refactor didn't accidentally start calling it per-run in bulk.
- `test_malformed_jsonl_line_is_skipped_and_counted`,
  `test_load_jsonl_handles_all_legacy_shapes_plus_new_execution_identity_format` — tolerant-load
  behavior the bulk endpoint inherits by construction (same `self._events_by_run`/`self._tools_by_seq`
  caches); must not regress.

**Integration / HTTP (`tests/tools/test_agent_ops_dashboard_api.py`)**
- `test_run_timeline_404_for_unknown_run_id` — **the only existing test covering
  `GET /api/runs/{run_id}/timeline` at all**; must pass unchanged post-refactor (AC #5's literal
  regression guard).
- `test_run_detail_404_for_unknown_run_id`, `test_run_detail_200_for_known_run_id` — exercise
  `_build_run_summary()`/`get_run()`, adjacent code path, must not regress.
- `test_list_tickets_route_rejects_out_of_range_limit`,
  `test_list_tickets_route_passes_limit_offset_through_to_cache` — template/precedent for this
  ticket's new pagination tests (see below); confirms the `Query(..., ge=, le=)` pattern this
  ticket's new route param declarations must follow still behaves as documented.
- `test_malformed_jsonl_line_skipped_and_counted_in_health`,
  `test_health_status_is_always_ok_even_with_parse_errors` — tolerant-load-through-HTTP behavior,
  unaffected but must not regress.

**Architecture guards (`tests/tools/test_agent_ops_dashboard_api_boundary.py`)**
- `test_typed_response_models_not_dict` — will automatically cover the new route once registered
  (it iterates `main.app.routes`), but must be re-run to confirm `BulkRunTimeline` passes its
  `issubclass(response_model, BaseModel)` check (not `List[BulkRunTimeline]` — the response is a
  single wrapper object, not a list).
- `test_all_declared_routes_present` — **must be edited** (not just re-run) per AC #1; see New
  Tests Required — this is technically a modification, not pure regression, since its literal set
  must gain `"/api/runs/timeline"`.
- `test_main_mounts_no_static_files`, `test_agent_ops_dashboard_module_has_no_write_path`,
  `test_agent_ops_dashboard_does_not_import_workflow_orchestrator` — module-wide static/AST guards;
  must stay green since the new route/method must not introduce a write call or a `StaticFiles`/
  `.mount()` call.

**Concurrency (`tests/tools/test_agent_ops_dashboard_concurrency.py`)**
- `test_concurrent_requests_never_observe_partial_rebuild`,
  `test_active_run_completion_flips_atomically_under_concurrent_reads` — confirm the `RLock`
  contract still holds; the new bulk method nests a call to the shared entries-helper inside its
  own `with self._lock:` block (reentrant-safe per investigation, but must not deadlock or race in
  practice).

## New Tests Required

### `tests/tools/test_agent_ops_dashboard_ingest.py`

1. **`test_get_timeline_and_bulk_timeline_return_identical_entries_for_same_run`**
   Category: unit
   Verifies: for a fixture run with multiple events + tool calls, `DashboardCache.get_timeline(run_id).entries`
   is byte-identical (`.model_dump()` equal) to the corresponding list inside the new bulk method's
   `entries_by_run[run_id]` — direct proof of AC #2 and that both call the same extracted helper,
   not duplicated logic.
   Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

2. **`test_bulk_timeline_selects_same_run_ids_as_get_runs_for_same_since_limit_offset`**
   Category: unit
   Verifies: calling the new bulk method and `get_runs()` with identical `since`/`limit`/`offset`
   (no `until`) produces `entries_by_run.keys() == {s.run_id for s in get_runs(...)}` — AC #3.
   Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

3. **`test_bulk_timeline_until_excludes_runs_with_start_ts_after_bound`**
   Category: unit
   Verifies: a run with `start_ts` lexicographically greater than `until` is excluded from
   `entries_by_run`; a run at or below `until` is included — proves the new upper-bound filter
   (AC #4), using string comparison consistent with `since`'s existing convention.
   Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

4. **`test_bulk_timeline_until_excludes_none_start_ts_runs_consistent_with_since`**
   Category: unit
   Verifies: a run with `start_ts is None` (e.g. inferred-active run with no persisted start) is
   excluded when `until` is set — mirrors `get_runs()`'s existing `since`-excludes-`None`
   behavior, per AC #4's "consistent with since's existing comparison convention." This is the
   test that pins down Investigation Risk #5 (the `None`-guard must exist on the `until` branch
   too, not just `since`).
   Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

5. **`test_bulk_timeline_since_and_until_combine_as_inclusive_window`**
   Category: unit
   Verifies: with both `since` and `until` set, only runs whose `start_ts` falls in
   `[since, until]` are present in `entries_by_run` — confirms the two bounds compose correctly
   rather than one silently overriding the other.
   Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

6. **`test_bulk_timeline_limit_offset_applied_after_since_until_filtering`**
   Category: unit
   Verifies: with a fixture of 5 runs spanning a `since`/`until` window that matches only 3, and
   `limit=1, offset=1` — the returned `entries_by_run` has exactly 1 key, and it is the *second*
   run in the filtered-and-sorted (descending `start_ts`) set, not the second of the unfiltered 5.
   Directly proves Investigation Risk #4's resolution (filter-then-slice ordering, not
   slice-then-filter) and prevents accidental use of `get_runs()`'s own already-sliced output.
   Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

7. **`test_bulk_timeline_empty_window_returns_empty_dict_not_error`**
   Category: unit / edge case
   Verifies: a `since`/`until` window matching zero runs returns `entries_by_run == {}`, not a 404
   or exception — the bulk endpoint returns a valid (possibly empty) window result, unlike the
   per-run endpoint's 404-on-unknown-run_id semantics.
   Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

### `tests/tools/test_agent_ops_dashboard_api.py`

8. **`test_bulk_run_timeline_route_returns_200_with_entries_by_run_shape`**
   Category: integration
   Verifies: `GET /api/runs/timeline` against a fixture repo with 2 runs (one with events, one
   without) returns 200 and a body whose `entries_by_run` dict has exactly the expected keys, and
   each value is a list of dicts shaped like `TimelineEntry` (seq/phase/agent/status/summary/ts/...).
   Location: `tests/tools/test_agent_ops_dashboard_api.py`

9. **`test_bulk_run_timeline_route_rejects_out_of_range_limit_offset`**
   Category: integration
   Verifies: `GET /api/runs/timeline?limit=0`, `?limit=101`, `?offset=-1` all return 422 — mirrors
   `test_list_tickets_route_rejects_out_of_range_limit`'s pattern but bounded to `/api/runs`'s
   `le=100` (not `/api/tickets`'s `le=500`).
   Location: `tests/tools/test_agent_ops_dashboard_api.py`

10. **`test_bulk_run_timeline_route_since_until_pass_through_to_cache`**
    Category: integration
    Verifies: `GET /api/runs/timeline?since=...&until=...` narrows the returned `entries_by_run`
    keys exactly as the corresponding `DashboardCache` call would — confirms the route param wiring,
    not just the cache-layer logic (test #5 above covers the cache layer; this covers the HTTP
    boundary).
    Location: `tests/tools/test_agent_ops_dashboard_api.py`

11. **`test_bulk_run_timeline_route_matches_per_run_route_for_same_run_id`**
    Category: integration
    Verifies: for a run present in both, `GET /api/runs/{run_id}/timeline`'s `entries` field and
    `GET /api/runs/timeline`'s `entries_by_run[run_id]` are identical JSON — the end-to-end,
    HTTP-boundary version of AC #2 (test #1 above is the cache-layer version).
    Location: `tests/tools/test_agent_ops_dashboard_api.py`

### `tests/tools/test_agent_ops_dashboard_api_boundary.py`

12. **Edit `test_all_declared_routes_present`** (not a new test — required edit per AC #1)
    Add `"/api/runs/timeline"` to the literal path set at lines 56-65. Confirms the route's own
    docstring guidance ("keep the function name generic so it doesn't itself go stale") — no
    rename needed, just the set literal.
    Location: `tests/tools/test_agent_ops_dashboard_api_boundary.py`

13. **`test_typed_response_models_not_dict` covers `BulkRunTimeline` automatically** — no new test
    needed, but must be re-run post-implementation to confirm `BulkRunTimeline` (a `BaseModel`
    subclass, not `List[...]`) passes the `else` branch at line 44-47 of that file. Explicitly
    called out in AC #6.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py \
  tests/tools/test_agent_ops_dashboard_api.py \
  tests/tools/test_agent_ops_dashboard_api_boundary.py \
  tests/tools/test_agent_ops_dashboard_concurrency.py \
  -q
```

Never `pytest tests/`. This is the same scoped set the prior dashboard-backend tickets (INFRA-275
through INFRA-300) consistently re-ran at Parity time — matches this module's own established
verification footprint. `test_agent_ops_dashboard_frontend_api_surface.py` and
`test_agent_ops_dashboard_serve.py` are excluded from the required scope (this ticket does not
touch `serve.py` or the frontend), but re-running them costs nothing extra if the full backend
suite is preferred:

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py \
  tests/tools/test_agent_ops_dashboard_api.py \
  tests/tools/test_agent_ops_dashboard_api_boundary.py \
  tests/tools/test_agent_ops_dashboard_concurrency.py \
  tests/tools/test_agent_ops_dashboard_frontend_api_surface.py \
  tests/tools/test_agent_ops_dashboard_serve.py \
  -q
```

## Anti-Drift Test Guards

- **`test_run_timeline_404_for_unknown_run_id` must pass with zero modification.** If it needs
  editing to pass, the refactor touched the existing per-run route's behavior — a direct AC #5
  violation, stop and re-check the extraction.
- **Test #6 (`limit_offset_applied_after_since_until_filtering`) is the single highest-value new
  test** — it is the one guard that would catch a subtly wrong implementation where the bulk
  method calls `get_runs()` for run selection and then tries to bolt `until` on afterward (wrong
  order, per Investigation Risk #4). Do not skip or weaken this test even under time pressure.
- **No test should assert on `files_touched`, `live_tail`, or `is_live` appearing anywhere in the
  bulk endpoint's response body.** If a test needs those fields to pass, the implementation drifted
  into building full `RunTimeline` objects per run instead of using the entries-only helper —
  itself a scope-creep and performance regression (needless `extract_files_touched()` calls per
  run in a potentially large window).
- **No test should reference `dashboard-frontend/src/api.ts` or any `.ts`/`.tsx` file.** Frontend
  consumption is out of scope for this ticket; a test that starts asserting on `api.ts` content
  would indicate scope creep into the downstream `ProgressTimelineView` ticket's territory.
- **`test_agent_ops_dashboard_module_has_no_write_path`'s AST guard must keep passing without a
  new exemption/allowlist entry added to it.** The new bulk method has no reason to write
  anything; if implementation requires excluding a new file from that guard's scan, that itself
  signals an architecture violation (read-only dashboard contract), not a legitimate test
  adjustment.
- **Verify `BulkRunTimeline` is registered as `response_model=BulkRunTimeline` (bare model), not
  `response_model=Dict[str, List[TimelineEntry]]`.** The latter would satisfy runtime behavior but
  fail `test_typed_response_models_not_dict`'s `isinstance(response_model, type) and
  issubclass(response_model, BaseModel)` branch (a raw `Dict[...]` typing alias is not a
  `BaseModel` subclass) — this is exactly the trap AC #6 calls out by name.
