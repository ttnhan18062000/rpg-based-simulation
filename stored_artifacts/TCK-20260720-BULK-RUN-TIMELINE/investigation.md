---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260720-BULK-RUN-TIMELINE
artifact_type: investigation
tags: [dashboard, observability, agent-monitoring, api-design]
---

# Investigation — TCK-20260720-BULK-RUN-TIMELINE

## Current Behavior

### `src/api/agent_ops_dashboard/ingest.py` — `DashboardCache.get_timeline()`
Actual location is **lines 681-726** (the ticket's "~656-701" is stale — the file has grown
since the ticket was written; content and length match, just shifted ~25 lines down). Signature:

```python
def get_timeline(self, run_id: str) -> Optional[RunTimeline]:
```

Body, under `with self._lock:` + `self._maybe_rebuild()`:
1. Returns `None` if `run_id` is in neither `self._runs_by_id` nor `self._inferred_active` (404 source).
2. `raw_events = sorted(self._events_by_run.get(run_id, []), key=lambda e: e.get("seq") or 0)`.
3. **The entries-building loop** (lines 690-708, not 662-683 as the ticket claims — same
   ~19-line span, shifted): iterates `raw_events`, looks up `self._tools_by_seq[(run_id, e.get("seq"))]`
   per event, and builds two parallel lists: `entries: list[TimelineEntry]` (the typed model) and
   `entry_dicts: list[dict]` (`{"tool_calls": raw_tool_calls}`, used only to feed
   `extract_files_touched()` afterward — not part of the response).
4. Computes `is_live`, builds `live_tail_raw` from `self._tools_by_run_recent[run_id]` filtered to
   unknown seqs (only relevant when `is_live`).
5. `files_touched = extract_files_touched(entry_dicts, live_tail_raw)`.
6. Returns `RunTimeline(run_id, is_live, entries, live_tail=[...], files_touched)`.

**This is the only place `entries: list[TimelineEntry]` gets built from raw events + tool calls.**
No standalone helper exists today — the ticket's assumption in Assumptions/Open Questions #1 is
confirmed correct: extraction is required for true reuse, not optional.

Extraction target: pull steps 2-3 (raw_events sort + the loop producing `entries`/`entry_dicts`)
into a private helper, e.g. `_build_timeline_entries(self, run_id: str) -> tuple[list[TimelineEntry], list[dict]]`,
called by both `get_timeline()` (which still needs `entry_dicts` for `extract_files_touched`) and
the new bulk method (which only needs `entries` — the `BulkRunTimeline` response model has no
`files_touched`/`live_tail`/`is_live` per run, so the bulk path can discard `entry_dicts` and skip
`extract_files_touched()`/live-tail computation entirely for each run).

### `DashboardCache.get_runs()` — lines 629-664
Signature accepts `limit`, `offset`, `status`, `workflow`, `since`, `provider`, `execution_id`,
`ticket_id` (all keyword-only). Selection logic:
```python
all_run_ids = set(self._runs_by_id) | set(self._inferred_active)
for run_id in all_run_ids:
    summary = _build_run_summary(run_id, self._runs_by_id.get(run_id), self._inferred_active.get(run_id))
    if status is not None and summary.final_status != status: continue
    if workflow is not None and summary.workflow != workflow: continue
    if since is not None and (summary.start_ts is None or summary.start_ts < since): continue
    ...
    summaries.append(summary)
summaries.sort(key=lambda s: s.start_ts or "", reverse=True)
return summaries[offset : offset + limit]
```
Key finding: **`since` excludes runs with `start_ts is None`** — a run with no start_ts can never
match a `since` filter, only an unfiltered call. The ticket's Assumptions section flags this as
something the new ticket "must decide/state" — it is already resolved by AC #4's text ("consistent
with since's existing comparison convention"), meaning `until` should apply the same
`start_ts is None → excluded` rule when `until` is set, not just `since`.

**`get_runs()` itself has no `until` parameter today** — confirmed, matches the ticket's premise.
Sort is always descending by `start_ts` (empty string for `None`, so `None`-start_ts runs sort
last), then `[offset:offset+limit]` slices. No `until` retrofit — per ticket's Out of Scope, the
new bulk method must mirror this filtering logic (new `since`/`until`/`limit`/`offset` selection)
without modifying `get_runs()`'s signature.

### `main.py` — route registration (lines 1-114)
Existing 8 routes, each decorated `@app.get(path, response_model=<PydanticModel>)`, each an
`async def` that thinly delegates to `_cache.<method>(...)`. Relevant precedents:
- `GET /api/runs` (line 65-73): `Query(default=50, ge=1, le=100)` for limit, `Query(default=0, ge=0)`
  for offset, plain `Optional[str] = None` for `since`/`status`/`workflow` (no FastAPI `Query(...)`
  wrapper needed for optional untyped-constraint params). **Note:** the route does NOT expose
  `provider`/`execution_id`/`ticket_id` even though `DashboardCache.get_runs()` accepts them —
  those are cache-internal-only params, not part of the public HTTP surface.
- `GET /api/runs/{run_id}/timeline` (line 84-89): `async def get_run_timeline(run_id: str) -> RunTimeline`,
  404 via `HTTPException(status_code=404, ...)` when `_cache.get_timeline()` returns `None`. This
  ticket's Out of Scope confirms this route stays untouched.
- `GET /api/tickets` (line 33-62) is the file's only precedent for `limit`/`offset` validation
  bounds (`Query(default=100, ge=1, le=500)` / `Query(default=0, ge=0)`) — a *different* bound
  than `/api/runs`'s (100 vs 500). The new bulk route should follow `/api/runs`'s bound
  (`le=100`), per the ticket's explicit "follow GET /api/runs' existing since/limit/offset
  pagination shape."

### `models.py` — existing response model patterns (lines 1-264)
Module docstring (lines 1-9) states the hard rule: routes only ever return these typed models,
"never `.model_dump()`'d into a `response_model=dict`". Every model here is a flat
`pydantic.BaseModel` subclass; wrapper-of-dict-of-list patterns already exist as precedent:
`GlossaryResponse(BaseModel): terms: Dict[str, GlossaryEntry]` (line 262-263) is the closest
existing analog to the requested `BulkRunTimeline(BaseModel): entries_by_run: Dict[str, List[TimelineEntry]]`
— same `Dict[str, <model>]` wrapping shape, just `List[TimelineEntry]` instead of a bare model per
key. `TimelineEntry` itself already exists at lines 67-77, unchanged — the new model composes it,
does not redefine it.

## Mechanics / Engine Constraints

None. This is dashboard/observability tooling over `tickets/**` and
`agent-monitoring/*.jsonl` — it does not touch `AuthoritativeState`, does not read or write
simulation entities, and no chapter of `docs/mechanics/` or contract in `docs/engine/` governs
it. This matches every prior Agent Ops Dashboard ticket's own investigation finding (see INFRA-275
through INFRA-300 in `docs/parity_ledger/infrastructure.yaml`, all `support_boundary: >` stating
"no simulation behavior is involved").

The only binding constraints are this project's own established **API-design conventions** for
this module (see `docs/plans/agent_ops_dashboard/proposal_progress_timeline.md`'s "Architectural
constraints" section, itself carried forward from `TCK-20260716-AGENTOPS-DASHBOARD-BACKEND`):
- Typed Pydantic response models only, never raw dict (`test_typed_response_models_not_dict` —
  confirmed real, see below).
- `main.py` never reads a file directly — all data loading lives in `ingest.py`.
- Reuse existing entry-loading logic; do not duplicate it.
- `DashboardCache` stays read-only over `tickets/**` and `agent-monitoring/*.jsonl`.
- Single `threading.RLock()` per method, matching `src/api/read_model_cache.py::ReadModelCache`'s
  pattern — confirmed present at `ingest.py:473` (`self._lock = threading.RLock()`), and it is
  reentrant (`RLock`, not `Lock`), so the new bulk method can safely nest a call to the shared
  entries-building helper inside its own `with self._lock:` block, matching the ticket's
  Assumptions #3.

## Parity Ledger Overlap

`docs/parity_ledger/infrastructure.yaml` is the only ledger file mentioning the dashboard
(confirmed via grep — `substrate.yaml`, `combat_movement.yaml`, etc. have zero dashboard
references). Relevant existing entries, all `status: verified`, `priority: P2` (no P0 entries
touch this module — dashboard tooling has never been P0 in this ledger):

- **INFRA-275** (`TCK-20260716-AGENTOPS-DASHBOARD-BACKEND`) — establishes the FastAPI app, the 5
  original typed routes (including the untouched `/api/runs/{run_id}/timeline`), `ingest.py`'s
  file-read ownership, and the `RLock`-per-method cache pattern. Its `v2_evidence` text still says
  "5 typed routes" — stale relative to the current 8-route app, but that staleness is *intentional
  scope*, not a bug: INFRA-277/278/279 each added their own new ledger entries for their own new
  routes rather than editing INFRA-275's route count. This ticket should follow the same pattern:
  **add a new entry (next available ID is INFRA-301 — INFRA-300 is the current last entry)**
  rather than editing INFRA-275.
- **INFRA-277** (glossary registry) / **INFRA-278** (glossary route) / **INFRA-279** — precedent
  for the "new route → new ledger entry, referencing the module but not editing prior entries"
  pattern.
- No P0 entries overlap this scope — nothing here requires a `test_path` gate beyond the project's
  general "add or update tests when behavior changes" rule.

**Action for Parity phase:** add a new `INFRA-301` entry (or next free number at implementation
time — re-check the tail of the file, since other in-flight tickets on this branch may claim
INFRA-301 first) documenting the new route, the `BulkRunTimeline` model, and the extracted
`_build_timeline_entries`-style helper, with `v2_evidence` citing exact post-implementation line
numbers (do not reuse this investigation's pre-implementation line numbers verbatim — they will
shift once the helper is extracted).

## Prior Work

Closest prior tickets (found via `stored_artifacts/` matching the `agent_ops_dashboard` code area,
no `REGISTRY.yaml`-driven `related_code_areas` match beyond what's already listed since the
registry only indexes done tickets and this module has 13 done tickets touching it):

- **TCK-20260716-AGENTOPS-DASHBOARD-BACKEND** — origin ticket; establishes every pattern this
  ticket must follow (typed models, `ingest.py`-owns-reads, `RLock` cache).
- **TCK-20260718-AGENTOPS-STATS-API** — most recent precedent for "add a new route + new
  Pydantic model(s) + new `DashboardCache` method," and it extended
  `test_all_declared_routes_present`'s (then named `test_all_five_routes_are_declared`) hardcoded
  path set exactly the way this ticket's AC #1 requires again.
- **TCK-20260718-GLOSSARY-API** (INFRA-278/279) — closest shape precedent for a `Dict[str, Model]`
  wrapper response (`GlossaryResponse.terms: Dict[str, GlossaryEntry]`), directly informing
  `BulkRunTimeline.entries_by_run: Dict[str, List[TimelineEntry]]`'s shape.
- **TCK-20260717-TICKETS-TABLE-PAGINATION** — establishes the `limit`/`offset` `Query(..., ge=, le=)`
  validation pattern and its own test coverage shape (`test_list_tickets_route_rejects_out_of_range_limit`,
  `test_list_tickets_route_passes_limit_offset_through_to_cache`) — direct template for this
  ticket's new pagination tests, adapted to `/api/runs`'s bound (`le=100`) rather than
  `/api/tickets`'s (`le=500`).
- **`docs/plans/agent_ops_dashboard/proposal_progress_timeline.md`** — the proposal doc this
  ticket was carved out of (Concern #1 verbatim). Confirms this ticket is a hard prerequisite for
  the not-yet-created `ProgressTimelineView`/range-control child tickets, and that frontend
  consumption (`dashboard-frontend/src/api.ts`, `useRunTimelinesPolling`) is explicitly deferred.

No stored artifact exists yet for a "bulk run timeline" or "until param" concept specifically —
this is new ground within an established pattern, not a re-implementation of prior work.

## Risks and Open Questions

1. **Ticket's line-number citations are stale but structurally accurate.** `get_timeline()` is at
   681-726, not 656-701; the entries loop is at 690-708, not 662-683. Same shape, shifted ~25
   lines (from later ticket additions to `ingest.py`, e.g. `get_agent_monitoring_stats` and
   `get_ticket_corpus_stats` inserted earlier in the file). Not a scope problem, but the plan
   phase must re-derive real line numbers rather than trusting the ticket text, and Parity must
   re-derive them again post-implementation.
2. **No existing positive-path test for `get_timeline()`'s entries-building logic.** Only
   `test_run_timeline_404_for_unknown_run_id` exists today (`test_agent_ops_dashboard_api.py:38`)
   — there is no test asserting `GET /api/runs/{run_id}/timeline` returns correct `entries` for a
   known run with real events/tool-calls. This means AC #2's "byte-identical to what
   `GET /api/runs/{run_id}/timeline` returns" claim has no existing regression baseline to diff
   against — the new bulk-endpoint test must *itself* establish the expected entries shape from
   fixture data and assert both endpoints agree, rather than diffing against a pre-existing
   golden test.
3. **No existing test for `get_runs()`'s `since` filter at all.** Neither `test_agent_ops_dashboard_ingest.py`
   nor `test_agent_ops_dashboard_api.py` has a `since`-specific test today (confirmed via grep,
   zero matches). AC #3 ("limit/offset/since on the bulk endpoint select the same set of runs as
   GET /api/runs with identical query params") has no existing precedent test to mirror line-for-
   line — new tests must be written from first principles against the source semantics found
   above (`None`-`start_ts` exclusion, descending sort, slice-after-filter).
4. **Design decision, not blocking, but worth flagging for Plan:** should the new bulk method call
   `self.get_runs(...)` internally for run selection, or duplicate its filtering logic with
   `until` added? The ticket's own Scope text ("filters runs by since/until/limit/offset
   (mirroring get_runs' filtering)") and Out of Scope ("No retrofit of `until` onto GET /api/runs
   itself") together imply a **parallel, not delegating, implementation** — i.e., a new private
   selection helper/method that duplicates `get_runs()`'s since/sort/slice logic plus the new
   `until` check, rather than calling `get_runs()` and post-filtering (post-filtering after
   `get_runs()`'s own `[offset:offset+limit]` slice would be wrong — `until` must apply *before*
   pagination, not after, or the requested page of runs would be wrong). This must be resolved in
   plan.md, not assumed here.
5. **`RunSummary.start_ts` is `Optional[str]`** (models.py:85) — lexicographic string comparison
   against `None` is a `TypeError` in Python 3; the existing `since` check already guards this
   correctly (`summary.start_ts is None or summary.start_ts < since` — short-circuits before ever
   comparing `None < since`). Any new `until` check must use the same guard shape
   (`summary.start_ts is None or summary.start_ts > until`), not a bare `summary.start_ts > until`.

## Anti-Drift Hazards

- **Do not modify `get_timeline()`'s public signature or return value.** AC #5 requires the
  existing per-run endpoint's tests to pass unchanged — the extraction must be a pure refactor
  (pull code into a helper, call the helper from the same call site) with zero observable
  behavior change to `RunTimeline`'s shape or content.
- **Do not let the bulk method reuse `get_runs()`'s `[offset:offset+limit]` slice before applying
  `until`.** See Risk #4 — `until` is a filter, not a post-slice trim; it must sit alongside
  `since` in the per-run-id filter loop, before sort+slice.
- **Do not add `files_touched`/`live_tail`/`is_live` to the bulk response.** The ticket's Scope
  text is explicit: `entries_by_run: Dict[str, List[TimelineEntry]]` only. Building the full
  `RunTimeline` per run (calling `get_timeline()` in a loop) would technically "reuse" the logic
  but would compute `extract_files_touched()`/live-tail unnecessarily for every run in the window
  — wasteful and out of the requested response shape. Use the extracted entries-only helper, not
  a loop over `get_timeline()`.
- **Do not expose `provider`/`execution_id`/`ticket_id` on the new bulk route.** `get_runs()`
  supports them internally but `main.py`'s existing `/api/runs` route deliberately does not
  surface them at the HTTP boundary — the new route should match that public-surface scope, not
  the cache method's full internal capability.
- **`test_all_declared_routes_present`'s exact-set assertion (`test_agent_ops_dashboard_api_boundary.py:56-65`)
  will fail the moment the new route is registered until its literal set is updated** — this is
  the test's intended job (a deliberate regression guard, per its own docstring), not a bug to
  route around.
- **Frontend (`dashboard-frontend/src/api.ts`) is explicitly out of scope** — do not add a
  TypeScript interface or fetch helper there even though the module header comment
  ("new response interfaces there must mirror models.py field-for-field") might tempt a "let's
  keep it in sync" edit. That's the downstream `ProgressTimelineView` ticket's job.
