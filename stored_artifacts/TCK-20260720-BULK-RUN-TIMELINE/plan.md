---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260720-BULK-RUN-TIMELINE
artifact_type: plan
tags: [dashboard, observability, agent-monitoring, api-design]
---

# Implementation Plan — TCK-20260720-BULK-RUN-TIMELINE

## Summary

Add `GET /api/runs/timeline?since=&until=&limit=&offset=`, a bulk sibling of the existing
per-run `GET /api/runs/{run_id}/timeline`, returning `{entries_by_run: Dict[run_id, List[TimelineEntry]]}`
for every run in a since/until-bounded, limit/offset-paginated window. The approach has three
independent moving parts: (1) a pure refactor of `DashboardCache.get_timeline()`
(`src/api/agent_ops_dashboard/ingest.py:681-726`) that extracts its entries-building loop
(lines 690-708) into a private helper `_build_timeline_entries()`, with zero observable change
to `get_timeline()`'s own return value; (2) a new `DashboardCache.get_bulk_timeline()` method
that **duplicates** `get_runs()`'s (lines 629-664) since/sort/slice run-selection logic rather
than calling `get_runs()` and post-filtering — this is load-bearing: `until` must be applied
*before* the `[offset:offset+limit]` slice, in the same per-run-id filter loop as `since`, or a
requested page could silently be wrong — then calls the extracted helper per selected run_id,
discarding `entry_dicts` (bulk responses carry no `files_touched`/`live_tail`/`is_live`); and
(3) the new `BulkRunTimeline` Pydantic model (`models.py`) plus the new route (`main.py`),
registered ahead of the existing `/api/runs/{run_id}` route to avoid FastAPI's path-shadowing
wildcard trap (see Step 4). `get_timeline()`'s public signature/return shape and `get_runs()`'s
own filtering are never touched. This is a `src/api/` change — every response crossing the HTTP
boundary is a typed Pydantic model (`BulkRunTimeline`), never a raw dict or a domain object;
flagged explicitly here for architecture-reviewer visibility even though the ticket's own Scope
already requires it.

## Steps

### Step 1 — Extract `_build_timeline_entries()` helper; refactor `get_timeline()` to call it
**Files:** `src/api/agent_ops_dashboard/ingest.py`

**Change:** Add a new private method, placed directly above `get_timeline()`:

```python
def _build_timeline_entries(self, run_id: str) -> tuple[list[TimelineEntry], list[dict]]:
    """Pure extraction of get_timeline()'s entries-building loop. Caller must already hold
    self._lock and have already called self._maybe_rebuild() — this method does neither
    itself, since both get_timeline() and get_bulk_timeline() call it once per already-locked,
    already-rebuilt request, not once per run inside their own loops."""
    raw_events = sorted(
        self._events_by_run.get(run_id, []), key=lambda e: e.get("seq") or 0
    )
    entries = []
    entry_dicts = []
    for e in raw_events:
        raw_tool_calls = self._tools_by_seq.get((run_id, e.get("seq")), [])
        entries.append(
            TimelineEntry(
                seq=e.get("seq"),
                phase=e.get("phase"),
                agent=e.get("agent"),
                status=e.get("status", ""),
                summary=e.get("summary", ""),
                ts=_coerce_ts(e.get("ts")) or "",
                tool_call_count=e.get("tool_call_count"),
                cost_proxy_score=e.get("cost_proxy_score"),
                reason_code=e.get("reason_code"),
                tool_calls=[_tool_call_to_model(t) for t in raw_tool_calls],
            )
        )
        entry_dicts.append({"tool_calls": raw_tool_calls})
    return entries, entry_dicts
```

This is lines 687-708 moved verbatim (only the trailing `return` is new). Then edit
`get_timeline()` (lines 681-726) to replace its own inline copy of that block with:

```python
entries, entry_dicts = self._build_timeline_entries(run_id)
```

placed at the same position, still inside `get_timeline()`'s existing `with self._lock:` /
`self._maybe_rebuild()` / 404-check block. Everything after that line in `get_timeline()`
(`is_live`, `live_tail_raw`, `files_touched = extract_files_touched(entry_dicts, live_tail_raw)`,
the final `RunTimeline(...)` construction) is **untouched** — `get_timeline()` still needs
`entry_dicts` for `extract_files_touched()`, so the helper must keep returning both, not just
`entries`.

**Do NOT touch:** `get_timeline()`'s signature (`def get_timeline(self, run_id: str) -> Optional[RunTimeline]`),
its 404 check, its `is_live`/`live_tail_raw`/`files_touched` computation, or its final
`RunTimeline(...)` construction. Do NOT touch `get_runs()` (lines 629-664) in this step.

**Verify:** `test_run_timeline_404_for_unknown_run_id` (existing, must pass with zero
modification — this is the regression guard proving the extraction changed nothing observable).
No new test is required for this step alone; Step 6's
`test_get_timeline_and_bulk_timeline_return_identical_entries_for_same_run` is the test that
actually exercises the helper (it needs `get_bulk_timeline()` from Step 2 to exist first, so it
lands in Step 6, not here).

---

### Step 2 — Add `DashboardCache.get_bulk_timeline()`
**Files:** `src/api/agent_ops_dashboard/ingest.py`

**Change:** Add a new public method directly below `get_timeline()`:

```python
def get_bulk_timeline(
    self,
    *,
    since: Optional[str] = None,
    until: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> BulkRunTimeline:
    with self._lock:
        self._maybe_rebuild()
        all_run_ids = set(self._runs_by_id) | set(self._inferred_active)
        summaries = []
        for run_id in all_run_ids:
            summary = _build_run_summary(
                run_id, self._runs_by_id.get(run_id), self._inferred_active.get(run_id)
            )
            if since is not None and (summary.start_ts is None or summary.start_ts < since):
                continue
            if until is not None and (summary.start_ts is None or summary.start_ts > until):
                continue
            summaries.append(summary)

        summaries.sort(key=lambda s: s.start_ts or "", reverse=True)
        page = summaries[offset : offset + limit]

        entries_by_run: dict[str, list[TimelineEntry]] = {}
        for s in page:
            entries, _entry_dicts = self._build_timeline_entries(s.run_id)
            entries_by_run[s.run_id] = entries
        return BulkRunTimeline(entries_by_run=entries_by_run)
```

This is a **duplicated**, not delegated, copy of `get_runs()`'s `all_run_ids` build +
per-run-id filter loop + `summaries.sort(...)` + `[offset:offset+limit]` slice, with one new
`until` branch inserted alongside the existing `since` branch, using the identical
`start_ts is None or ...` guard shape (matching investigation Risk #5 — a bare
`summary.start_ts > until` would `TypeError` on `None`). Do **not** implement this by calling
`self.get_runs(...)` and then filtering/trimming the result — `get_runs()`'s own
`[offset:offset+limit]` slice happens before any `until` bound could be applied, which would
silently return the wrong page whenever an `until`-excluded run would otherwise have occupied a
slot ahead of an eligible one. `until` must sit in the *same* per-run-id filter loop as `since`,
before sort and slice — not after.

The method takes **only** `since`, `until`, `limit`, `offset` — no `status`, `workflow`,
`provider`, `execution_id`, or `ticket_id` parameters, even though `get_runs()` supports all of
those internally. The ticket's own Scope text names exactly `since`/`until`/`limit`/`offset` for
this method ("filters runs by since/until/limit/offset (mirroring get_runs' filtering)"); adding
the other four would be scope creep beyond what AC #3/#4 require.

`_build_timeline_entries(s.run_id)` is called once per selected run, inside the same
`with self._lock:` block already held by this method — safe because `self._lock` is a
reentrant `threading.RLock` (confirmed in investigation, `ingest.py:473`), and the helper itself
does not attempt to re-acquire the lock (per Step 1's docstring contract). Only `entries` is
kept; `entry_dicts` is discarded (`_entry_dicts`, unused) — do not call
`extract_files_touched()` or compute `is_live`/`live_tail` here.

**Do NOT touch:** `get_runs()` itself (lines 629-664) — read as a template only, not modified,
not called. Do NOT add `files_touched`, `live_tail`, or `is_live` anywhere in this method or in
`BulkRunTimeline`.

**Verify:** Step 6's new ingest-layer tests (items 1-7 of `test_plan.md`), specifically
`test_bulk_timeline_limit_offset_applied_after_since_until_filtering` — the single test that
would catch a wrong (slice-then-filter) implementation of this step.

---

### Step 3 — Add `BulkRunTimeline` response model
**Files:** `src/api/agent_ops_dashboard/models.py`

**Change:** Add, near `RunTimeline`/`TimelineEntry` (or alongside `GlossaryResponse` at the end
of the file — either location is fine, pick whichever keeps related models visually grouped):

```python
class BulkRunTimeline(BaseModel):
    entries_by_run: Dict[str, List[TimelineEntry]]
```

Direct shape precedent: `GlossaryResponse(BaseModel): terms: Dict[str, GlossaryEntry]`
(lines 262-263) — same `Dict[str, <model>]`-wrapper pattern, with `List[TimelineEntry]` instead
of a bare model per key. `TimelineEntry` (lines 67-77) is reused unchanged, not redefined.
`Dict`/`List` are already imported at the top of this file (used by `GlossaryResponse`/
`TicketsPage` etc.) — no new import needed beyond confirming they're in scope.

**Do NOT touch:** `RunTimeline`, `TimelineEntry`, or `GlossaryResponse` themselves — this step
only adds a new class.

**Verify:** `test_typed_response_models_not_dict` (existing, will automatically cover the new
route once Step 4 registers it — confirms `BulkRunTimeline` is a `BaseModel` subclass, not
`List[BulkRunTimeline]` or a bare `Dict[...]` alias, satisfying AC #6).

---

### Step 4 — Register `GET /api/runs/timeline` in `main.py`
**Files:** `src/api/agent_ops_dashboard/main.py`

**Change:** Two edits:

1. Add `BulkRunTimeline` to the `from src.api.agent_ops_dashboard.models import (...)` block
   (lines 16-26), alphabetically placed (between `AgentMonitoringStats` and `GlossaryResponse`).

2. Add the new route. **Critical placement requirement, newly surfaced during planning (not in
   the investigation): this route must be registered *before* `/api/runs/{run_id}`
   (currently at lines 76-81), not after it.** FastAPI/Starlette matches routes in registration
   order; `/api/runs/{run_id}` is a single-path-segment wildcard that would match a literal
   request to `/api/runs/timeline` (with `run_id="timeline"`) if it is registered first, silently
   routing the new endpoint's traffic into `get_run("timeline")` (which 404s, since no run is
   literally named `"timeline"`) instead of the new handler. Insert the new route immediately
   after the existing `GET /api/runs` list route (line 73) and before `GET /api/runs/{run_id}`
   (line 76):

```python
@app.get("/api/runs/timeline", response_model=BulkRunTimeline)
async def list_run_timelines(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    since: Optional[str] = None,
    until: Optional[str] = None,
) -> BulkRunTimeline:
    return _cache.get_bulk_timeline(since=since, until=until, limit=limit, offset=offset)
```

`limit`/`offset` bounds (`ge=1, le=100` / `ge=0`) match `GET /api/runs`'s existing bounds
(lines 67-68) exactly — **not** `/api/tickets`'s wider `le=500` (lines 43-44). The route does
**not** expose `provider`, `execution_id`, `ticket_id`, `status`, or `workflow` — matching
`GET /api/runs`'s existing public HTTP surface, which itself does not expose the first three of
those either even though `get_runs()` supports them internally.

**Do NOT touch:** the existing `GET /api/runs`, `GET /api/runs/{run_id}`, or
`GET /api/runs/{run_id}/timeline` route bodies — only insert the new route between the first two.
Do NOT give the new route a `Query(...)` wrapper for `since`/`until` (plain `Optional[str] = None`
matches `GET /api/runs`'s existing `since` param style at line 71 — no numeric/enum constraint
applies to a timestamp string).

**Verify:** Step 7's new API-layer tests (items 8-11), specifically
`test_bulk_run_timeline_route_returns_200_with_entries_by_run_shape` and
`test_bulk_run_timeline_route_rejects_out_of_range_limit_offset`. The route-shadowing hazard
above is directly exercised by any of the new integration tests hitting
`GET /api/runs/timeline` — if placement is wrong, they'll observe a 404 (from the
`{run_id}`-matched `get_run` handler) instead of 200.

---

### Step 5 — Update `test_all_declared_routes_present`
**Files:** `tests/tools/test_agent_ops_dashboard_api_boundary.py`

**Change:** Add `"/api/runs/timeline"` to the literal path set at lines 56-65 (the `assert
paths == {...}` block). No other edit to this file in this step.

**Do NOT touch:** `test_typed_response_models_not_dict`, `test_main_mounts_no_static_files`,
`test_agent_ops_dashboard_module_has_no_write_path`,
`test_agent_ops_dashboard_does_not_import_workflow_orchestrator` — all four must keep passing
unmodified; they already generically cover the new route/model without needing edits.

**Verify:** `test_all_declared_routes_present` itself (satisfies AC #1's second half).

---

### Step 6 — New cache-layer tests
**Files:** `tests/tools/test_agent_ops_dashboard_ingest.py`

**Change:** Add the 7 tests specified in `test_plan.md`'s "New Tests Required" §1
(items 1-7), against fixture data with multiple runs spanning distinct `start_ts` values,
events, and tool calls:

1. `test_get_timeline_and_bulk_timeline_return_identical_entries_for_same_run` — AC #2 (cache
   layer): `get_timeline(run_id).entries` `.model_dump()`-equal to
   `get_bulk_timeline(...).entries_by_run[run_id]`.
2. `test_bulk_timeline_selects_same_run_ids_as_get_runs_for_same_since_limit_offset` — AC #3.
3. `test_bulk_timeline_until_excludes_runs_with_start_ts_after_bound` — AC #4, upper bound.
4. `test_bulk_timeline_until_excludes_none_start_ts_runs_consistent_with_since` — AC #4,
   `None`-guard parity with `since`.
5. `test_bulk_timeline_since_and_until_combine_as_inclusive_window` — AC #4, both bounds
   compose.
6. `test_bulk_timeline_limit_offset_applied_after_since_until_filtering` — the highest-value
   test per test_plan.md's Anti-Drift Test Guards; proves filter-then-slice ordering (Step 2's
   core requirement), not slice-then-filter.
7. `test_bulk_timeline_empty_window_returns_empty_dict_not_error` — edge case: a matching-zero
   window returns `entries_by_run == {}}`, not an exception or 404.

**Do NOT touch:** any existing test body in this file (`test_get_runs_filters_by_provider_and_execution_id`,
the `test_inferred_active_*` family, `test_files_touched_dedup_by_path_restricted_to_edit_tools`,
etc.) — all must pass unmodified per the Regression Surface in `test_plan.md`.

**Verify:** the 7 tests themselves.

---

### Step 7 — New API-layer (HTTP) tests
**Files:** `tests/tools/test_agent_ops_dashboard_api.py`

**Change:** Add the 4 tests specified in `test_plan.md`'s "New Tests Required" §2
(items 8-11):

8. `test_bulk_run_timeline_route_returns_200_with_entries_by_run_shape` — AC #1 (200 + correct
   dict shape).
9. `test_bulk_run_timeline_route_rejects_out_of_range_limit_offset` — `limit=0`, `limit=101`,
   `offset=-1` all → 422, bounded to `le=100` (not `/api/tickets`'s `le=500`).
10. `test_bulk_run_timeline_route_since_until_pass_through_to_cache` — HTTP-boundary version of
    AC #4, confirms query params actually reach `get_bulk_timeline(...)`.
11. `test_bulk_run_timeline_route_matches_per_run_route_for_same_run_id` — AC #2 (HTTP-boundary
    version): `GET /api/runs/{run_id}/timeline`'s `entries` JSON equals
    `GET /api/runs/timeline`'s `entries_by_run[run_id]` JSON for the same run.

**Do NOT touch:** `test_run_timeline_404_for_unknown_run_id`, `test_run_detail_404_for_unknown_run_id`,
`test_run_detail_200_for_known_run_id`, `test_list_tickets_route_rejects_out_of_range_limit`,
`test_list_tickets_route_passes_limit_offset_through_to_cache`, or either
`test_malformed_jsonl_line_skipped_and_counted_in_health` / `test_health_status_is_always_ok_even_with_parse_errors`
— all must pass unmodified.

**Verify:** the 4 tests themselves; #11 in particular is the concrete proof of AC #5
("`GET /api/runs/{run_id}/timeline` is unmodified") holding at the HTTP boundary, not just the
cache layer.

---

### Step 8 — Parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Add one new entry, following the `INFRA-277`/`INFRA-278`/`INFRA-279` /
`INFRA-298`-style precedent of "new route → new ledger entry, referencing but not editing prior
entries." **Do not edit `INFRA-275`** (the original-route-count entry, already intentionally
left stale by every prior ticket in this module per investigation).

Before writing the entry, re-check the file's actual tail (`grep -n "^- id: INFRA-" docs/parity_ledger/infrastructure.yaml | tail -5`)
for the true next-free ID — at investigation time it was `INFRA-300` (making `INFRA-301` next),
but re-verify at implementation time since other in-flight tickets on this branch may have
claimed it first.

Entry shape (fields per `docs/parity_ledger/schema.json`):
- `status: verified` (route + model + tests all land in this same session)
- `priority: P2` (matching every other entry in this file — no P0 entry touches this module)
- `text`: one paragraph describing the new `GET /api/runs/timeline` route, `BulkRunTimeline`
  model, the extracted `_build_timeline_entries()` helper, and the duplicated (not delegated)
  since/until/limit/offset selection logic in `get_bulk_timeline()`.
- `v2_evidence`: cite **post-implementation** line numbers (`ingest.py`'s `_build_timeline_entries`/
  `get_bulk_timeline`, `models.py`'s `BulkRunTimeline`, `main.py`'s new route) — do not reuse
  this plan's or the investigation's pre-implementation line numbers verbatim, they will have
  shifted.
- `test_path`: point at the new integration test proving the shared-helper reuse, e.g.
  `tests/tools/test_agent_ops_dashboard_api.py::test_bulk_run_timeline_route_matches_per_run_route_for_same_run_id`.
- `support_boundary`: same "no simulation behavior, Mechanics Bible chapter, or engine contract
  governs this module" framing as INFRA-281 through INFRA-300 (dashboard/observability tooling
  only).

**Do NOT touch:** `INFRA-275`, `INFRA-277`, `INFRA-278`, `INFRA-279`, or any other existing
entry in this file. Do NOT touch any other parity ledger file (`substrate.yaml`,
`combat_movement.yaml`, etc.) — confirmed zero dashboard references in any of them.

**Verify:** manual cross-check that `test_path` points at a test that exists and passes after
Steps 1-7 land; YAML validates against `docs/parity_ledger/schema.json` if a validation script
is run.

---

### Step 9 — Full scoped regression run
**Files:** none (verification only)

**Change:** none — run the scoped pytest command from `test_plan.md`:

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py \
  tests/tools/test_agent_ops_dashboard_api.py \
  tests/tools/test_agent_ops_dashboard_api_boundary.py \
  tests/tools/test_agent_ops_dashboard_concurrency.py \
  -q
```

Never run `pytest tests/` (full suite). Also acceptable to include
`test_agent_ops_dashboard_frontend_api_surface.py` and `test_agent_ops_dashboard_serve.py` per
test_plan.md's note (costs nothing extra, not required since this ticket touches neither
`serve.py` nor the frontend).

**Do NOT touch:** any file outside Steps 1-8 — this step is verification-only.

**Verify:** all listed commands pass; zero unexpected failures/regressions in the concurrency
suite (`test_concurrent_requests_never_observe_partial_rebuild`,
`test_active_run_completion_flips_atomically_under_concurrent_reads`) confirms the `RLock`
reentrancy assumption from Step 2 held in practice, not just in theory.

## Scope Guards

Reiterated verbatim from the ticket's Out of Scope section — none of the following may be
touched by this plan:

- No change to the existing single-run `GET /api/runs/{run_id}/timeline` endpoint or its
  behavior — `get_timeline()`'s return value must be byte-identical pre/post Step 1.
- No retrofit of `until` onto `GET /api/runs` itself — `until` exists only on the new bulk
  route/method; `get_runs()`'s signature is never touched.
- No frontend consumption of this endpoint (`useRunTimelinesPolling`, `ProgressTimelineView`,
  `dashboard-frontend/src/api.ts`) — covered by the downstream `ProgressTimelineView` ticket. Do
  not add a TypeScript interface or fetch helper anywhere under `dashboard-frontend/`.
- No `docs/guides/agent_ops_dashboard.md` / `docs/observability/agent_ops_dashboard_contract.md`
  update — deferred to a separate follow-up ticket per the ticket's own Out of Scope (C5).

Additional guards from the investigation's Anti-Drift Hazards, restated for the implementer:

- Do not add `files_touched`, `live_tail`, or `is_live` to `BulkRunTimeline` or to
  `get_bulk_timeline()`'s per-run computation — the response shape is
  `entries_by_run: Dict[str, List[TimelineEntry]]` only, nothing more.
- Do not expose `provider`, `execution_id`, `ticket_id`, `status`, or `workflow` on the new
  route or on `get_bulk_timeline()`'s signature.
- Do not implement `get_bulk_timeline()` by calling `self.get_runs(...)` and post-filtering —
  duplicate the filter/sort/slice logic inline with `until` added before the slice (Step 2).
- Do not let `test_all_declared_routes_present` require any change beyond adding the one new
  path string.
- Do not add a new exemption/allowlist entry to `test_agent_ops_dashboard_module_has_no_write_path`'s
  AST guard — the new code has no reason to write anything.

## Dependency Map

- **Step 1** (extract helper) has no dependencies — first step; both Step 2 and the continued
  correctness of `get_timeline()` depend on it.
- **Step 2** (`get_bulk_timeline()`) depends on **Step 1** (calls `_build_timeline_entries`).
- **Step 3** (`BulkRunTimeline` model) has no code dependency on Steps 1-2, but Step 2's return
  type annotation references it — implement Step 3 before or alongside Step 2 in practice (order
  in this plan is illustrative; the model and method may be written in either order as long as
  both exist before Step 4).
- **Step 4** (route registration) depends on **Step 2** and **Step 3** (calls
  `_cache.get_bulk_timeline`, imports `BulkRunTimeline`).
- **Step 5** (boundary test edit) depends on **Step 4** (route must exist for the path-set
  assertion to be meaningful, though the edit itself is a one-line literal change).
- **Step 6** (ingest tests) depends on **Steps 1-2** (exercises `_build_timeline_entries` and
  `get_bulk_timeline` directly).
- **Step 7** (API tests) depends on **Step 4** (exercises the HTTP route).
- **Step 8** (parity ledger) depends on **Steps 1-7** (cites real post-implementation line
  numbers and a real passing test path).
- **Step 9** (full verification) depends on all of Steps 1-8.

Steps 6 and 7 may proceed in parallel once their respective dependencies (Steps 1-2 and Step 4)
are done. Step 3 may be written in parallel with Step 1/2 since it has no dependency on either.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `GET /api/runs/timeline` registered with `response_model=BulkRunTimeline`; `test_all_declared_routes_present` updated | Step 3, Step 4, Step 5 | `test_all_declared_routes_present`, `test_typed_response_models_not_dict` |
| Bulk endpoint's per-run `TimelineEntry` list byte-identical to `GET /api/runs/{run_id}/timeline`, via shared helper (not duplicated) | Step 1, Step 2, Step 4 | `test_get_timeline_and_bulk_timeline_return_identical_entries_for_same_run`, `test_bulk_run_timeline_route_matches_per_run_route_for_same_run_id` |
| `limit`/`offset`/`since` select the same run set as `GET /api/runs` | Step 2 | `test_bulk_timeline_selects_same_run_ids_as_get_runs_for_same_since_limit_offset`, `test_bulk_timeline_limit_offset_applied_after_since_until_filtering` |
| New `until` param, lexicographic upper bound, `None`-start_ts guard consistent with `since` | Step 2 | `test_bulk_timeline_until_excludes_runs_with_start_ts_after_bound`, `test_bulk_timeline_until_excludes_none_start_ts_runs_consistent_with_since`, `test_bulk_timeline_since_and_until_combine_as_inclusive_window` |
| `GET /api/runs/{run_id}/timeline` unmodified; existing tests pass unchanged | Step 1 | `test_run_timeline_404_for_unknown_run_id` (unmodified) |
| Response model is a real Pydantic wrapper, not a bare dict | Step 3 | `test_typed_response_models_not_dict` |

## Anti-Drift Notes

- **Line numbers will shift.** The investigation already found the ticket's own citations stale
  (`get_timeline()` is at 681-726, not the ticket's ~656-701). This plan's own line citations
  (e.g. "lines 690-708") were current as of investigation/plan time — re-derive actual numbers
  during implementation and again for Step 8's parity entry; do not trust any line number in this
  document as gospel once other edits land.
- **`_build_timeline_entries()` must not acquire `self._lock` itself.** It is designed to be
  called only from inside a caller's own `with self._lock:` block (both `get_timeline()` and
  `get_bulk_timeline()` already hold it when calling). Since `self._lock` is a reentrant `RLock`,
  having the helper *also* acquire it would not deadlock — but it would be redundant and diverges
  from the "caller holds lock" contract stated in the helper's own docstring (Step 1). Keep it
  lock-free internally.
- **Route registration order in `main.py` is load-bearing** (Step 4) — `/api/runs/timeline` must
  be declared before `/api/runs/{run_id}`, or the wildcard route silently swallows it. This was
  not called out in the investigation; it was found during plan-time reading of `main.py`'s
  actual route order. Double-check this ordering is preserved if `main.py` is reformatted for any
  reason during implementation.
- **`get_bulk_timeline()`'s selection logic is a deliberate duplication of `get_runs()`'s logic,
  not a code-reuse violation.** The ticket's own Out of Scope forbids modifying `get_runs()`'s
  signature (to add `until`), and calling `get_runs()` internally would apply its
  `[offset:offset+limit]` slice before `until` could be applied — silently wrong pagination. Two
  small, independently-testable copies of a ~15-line filter/sort/slice block is the correct
  outcome here, not a refactor opportunity; do not "clean this up" by extracting a shared
  selection helper unless a future ticket explicitly asks for it.
- **API-boundary discipline (for reviewer visibility):** every new piece of data crossing
  `src/api/agent_ops_dashboard/main.py` in this ticket is the typed `BulkRunTimeline` Pydantic
  model (Step 3) — no `.model_dump()`-into-`dict` response_model, no raw `RunTimeline`/domain
  object returned as-is from the bulk path, and `main.py` itself does no file I/O (all reads stay
  in `ingest.py`, unchanged pattern). This matches `/api-design-principles`' shape/boundary
  concerns and this module's own established typed-response-only contract
  (`test_typed_response_models_not_dict`).

## Deviations

### Revision 1 (implementation time, Step 1)

Step 1's plan text states that "Everything after that line in `get_timeline()` (`is_live`,
`live_tail_raw`, `files_touched = extract_files_touched(entry_dicts, live_tail_raw)`, the final
`RunTimeline(...)` construction) is **untouched**." This was not quite accurate: the plan's own
reproduced code block for Step 1 (lines 43-71 of this plan) shows the extracted loop's local
`raw_events` variable is *also* referenced later in `get_timeline()`'s live-tail computation
(`known_seqs = {e.get("seq") for e in raw_events}`, immediately after the `is_live` check), not
just inside the loop itself. Once `raw_events` became local to `_build_timeline_entries()`, that
later reference in `get_timeline()` would be a `NameError` — this was a gap in the plan's "pure
extraction" claim, discovered while implementing, not a design decision to relitigate.

Fix applied: `known_seqs` is now built from `entries` (the helper's typed return value) instead
of the no-longer-in-scope `raw_events`: `known_seqs = {ent.seq for ent in entries}`. This is
behavior-preserving — `TimelineEntry.seq` is a direct, unmodified passthrough of
`e.get("seq")` for every event in `raw_events` (see the helper's own construction:
`TimelineEntry(seq=e.get("seq"), ...)`), so the resulting set is identical in both cardinality and
membership to the original `{e.get("seq") for e in raw_events}`. No behavior change to
`get_timeline()`'s return value; `test_run_timeline_404_for_unknown_run_id` and the new
`test_get_timeline_and_bulk_timeline_return_identical_entries_for_same_run` both pass, confirming
this holds in practice as well as by inspection.

No other deviation from the plan. All other steps (2-9) were implemented as specified, including
the deliberate duplication in `get_bulk_timeline()`, the pre-`{run_id}` route registration order
in `main.py`, and the INFRA-301 (confirmed still next-free at implementation time — INFRA-300 was
still the last entry) parity ledger entry.
