---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260717-TICKETS-TABLE-PAGINATION
artifact_type: investigation
tags: [observability, agent-monitoring, performance]
---

# Investigation — TCK-20260717-TICKETS-TABLE-PAGINATION

## Current Behavior

**`src/api/agent_ops_dashboard/main.py:29-49`** — `list_tickets` route. Declares
`response_model=List[TicketSummary]`. No `limit`/`offset` query params — every
call returns the entire filtered+sorted corpus. Contrast with the sibling
`list_runs` route (`main.py:52-60`), which already declares
`limit: int = Query(default=50, ge=1, le=100)` / `offset: int = Query(default=0, ge=0)`
and passes them through to `_cache.get_runs(...)`.

**`src/api/agent_ops_dashboard/ingest.py::DashboardCache.get_tickets`
(`L450-487`)** — builds `records` from `self._tickets_by_id.values()`, applies
AND-across-dimensions filtering (`tier`/`layer`/`status`==`workflow_status`/
`priority`), OR-within-tag filtering (`tags` set-intersection), free-text `q`
filtering, then `filtered.sort(...)` by `date` (`date_asc`/`date_desc`), and
returns `[_ticket_record_to_summary(r) for r in filtered]` — the full list,
unsliced. No `limit`/`offset` params exist on this method at all. Compare to
`get_runs` (`L489-515`), whose final line is `return summaries[offset : offset + limit]`.

**`src/api/agent_ops_dashboard/models.py:24-36`** — `TicketSummary` is a flat
Pydantic model. There is no wrapper/envelope model (no `TicketsPage`,
`TicketFacets`, or `total_count` concept anywhere in this file). `RunSummary`
is likewise flat — `/api/runs` has never had a `total_count` field either
(confirmed: no such field on `RunSummary`, `RunDetail`, or anywhere else).

**`dashboard-frontend/src/views/TicketsView.tsx`**:
- `loadInitial()` (`L128-150`) calls `fetchTickets({})` — no `limit`/`offset`
  — on mount, storing the full result into both `rows` (`L134`) and
  `optionsSource` (`L135`). `optionsSource` is the sole source for
  `distinctValues`/`distinctTags` (`L28-43`), which the four `FilterSelect`
  dropdowns and the tag-pill list read (`L213, L220, L227, L234, L238`) — i.e.
  filter-dropdown population and row rendering share the exact same unbounded
  fetch result today, which is precisely why adding pagination without a
  separate facets source would silently narrow the dropdowns to whatever is
  on the current page.
- `applyFilters()` (`L152-161`) and `toggleDateSort()` (`L163-173`) both
  re-fetch via `fetchTickets(buildFetchParams(...))` and overwrite `rows` only
  — `optionsSource` is never touched after the initial load, so today's
  dropdown options are frozen from the very first (currently: full-corpus)
  fetch, even as filters/sort change later fetches. This is pre-existing
  behavior, not something this ticket needs to fix directly, but the new
  `facets`-per-response design (per plan.md) intentionally changes this by
  updating `optionsFacets` on every fetch.
- `toggleColumnSort()`/`sortRows()`/`columnSort` (`L21-24, L57-67, L175-182`)
  and `displayedRows` (`L189-192`, a `useMemo` over `rows`) implement a
  client-side sort over whatever `rows` currently holds. Today `rows` is the
  full corpus, so this is a full-table sort. Once `rows` becomes one page
  (per this ticket), the exact same code becomes a page-scoped sort with zero
  code changes — confirmed by direct read of `sortRows`, which only ever
  operates on its `rows` argument, no external corpus reference.
- No pagination controls, no page-size constant, no `.slice(` windowing
  exists anywhere in this file today (confirmed via read, not grep-guessed).

**`dashboard-frontend/src/api.ts`**:
- `FetchTicketsParams` (`L96-105`) has no `limit`/`offset` fields.
  `fetchTickets()` (`L107-123`) builds a `URLSearchParams` from only
  `tier/layer/status/priority/tags/lifecycle/q/sort` and returns
  `Promise<TicketSummary[]>` (`L107`, `L122`: `return (await response.json()) as TicketSummary[]`) —
  a bare array, not an envelope.
- `FetchRunsParams`/`fetchRuns()` (`L66-72, L133-146`) already have
  `limit`/`offset`. `fetchAllRunsSince()` (`L153-167`) is the documented
  workaround for `/api/runs` having **no `total_count` field** — it loops on
  `offset` until a page comes back shorter than `RUNS_PAGE_LIMIT`. This is
  the "existing gap" the ticket's Assumptions section and plan.md's Resolved
  Decision #1 explicitly call out as *not* to be repeated for `/api/tickets`.

**`dashboard-frontend/src/test/TicketsView.test.tsx`** (`L1-237`, the portion
unaffected by the unrelated CSS-layer-padding-fix diff appended at `L235+`) —
every existing test uses a shared helper `mockFetchReturning(response: TicketSummary[])`
(`L29-33`) that mocks `globalThis.fetch` to resolve
`{ ok: true, json: async () => response }`, i.e. **the mock itself assumes
the bare-array wire shape**. This is not called out explicitly in plan.md's
per-step verify lists, but it is a load-bearing fact: once `fetchTickets`'s
return type changes to an envelope (`{items, total_count, facets}` per
plan.md's Resolved Decision #3), every one of the ~9 existing `it(...)` blocks
that call `mockFetchReturning([...])` with a bare ticket array will need that
helper (or its call sites) updated to return the new envelope shape, or every
existing test breaks simultaneously — not just the ones plan.md names as
needing rewrites (`'TicketsView — client-side column sort'`). See Anti-Drift
Hazards below.

**`tests/tools/test_agent_ops_dashboard_api_boundary.py`** (`L1-86`) — five
architecture guards: `test_typed_response_models_not_dict` (asserts every
route's `response_model` is a real Pydantic `BaseModel`, never `dict`),
`test_all_five_routes_are_declared` (asserts route paths, not shapes — safe
under a `response_model` swap on `/api/tickets`), `test_main_mounts_no_static_files`,
`test_agent_ops_dashboard_module_has_no_write_path`,
`test_agent_ops_dashboard_does_not_import_workflow_orchestrator`. None of
these assert `/api/tickets`'s specific response shape (`List[...]` vs. a
wrapper model) beyond "is a `BaseModel` (or `List[BaseModel]`)" — a new
`TicketsPage(BaseModel)` envelope satisfies `test_typed_response_models_not_dict`
unchanged since the `origin in (list, typing.List)` branch is simply not
taken for a non-list `response_model`; the `else` branch
(`isinstance(response_model, type) and issubclass(response_model, BaseModel)`)
covers it.

**`tests/tools/test_agent_ops_dashboard_ingest.py:432-469`** — three direct
`cache.get_tickets(...)` call tests (`test_get_tickets_and_across_dimensions_filters_tier_and_layer`,
`test_get_tickets_or_within_tag`,
`test_get_tickets_dimension_filter_and_tag_filter_combine_with_and`), all
calling `get_tickets` with zero `limit`/`offset` args and asserting on
`{r.ticket_id for r in results}` against a small (4-5 row) fixture. Confirmed:
these must keep returning the full unsliced set when `limit`/`offset` are
omitted — this is why plan.md's Resolved Decision #4 (cache-layer
`limit: Optional[int] = None` default, distinct from `get_runs`'s hardcoded
`limit: int = 50`) is correct and necessary, not optional.

**`tests/tools/test_agent_ops_dashboard_api.py:77-99`**
(`test_get_tickets_title_is_distinct_from_ticket_id`) — calls
`client.get("/api/tickets")`, does `tickets = resp.json()` then
`next(t for t in tickets if ...)` — **this indexes the top-level response as
a list directly.** Under the new `TicketsPage` envelope this line must become
`tickets = resp.json()["items"]` (or equivalent) or the test breaks with a
`TypeError` (iterating dict keys instead of ticket dicts). Confirmed exact
failure mode by reading the line, not assumed.

**`tests/tools/test_agent_ops_dashboard_concurrency.py:75-114`**
(`test_concurrent_requests_never_observe_partial_rebuild`) — calls
`cache.get_tickets()` once at `L88` purely to "prime the cache", never reads
or asserts on its return value. Unaffected by any shape/slicing change as
long as the zero-arg call keeps succeeding.

## Mechanics / Engine Constraints

This ticket touches only `src/api/agent_ops_dashboard/` — a standalone
FastAPI app explicitly **not** mounted on `src/api/server.py` and confirmed
(via `docs/observability/agent_ops_dashboard_contract.md`'s Purpose section
and `main.py`'s own module docstring) to never touch `AuthoritativeState` or
the tick loop. None of `docs/mechanics/`'s six chapters (entity anatomy,
combat, economic, strategic cognition, world evolution, worldbuilding) govern
this subsystem — it is a read-only observability/reporting layer over
`tickets/**` and `agent-monitoring/*.jsonl`, not a simulation mechanic.

The relevant constraint is architectural, not mechanical:
`docs/observability/agent_ops_dashboard_contract.md`'s "Architecture Law"
section states every route must declare `response_model=` and never return a
raw dict — this ticket's `TicketsPage` envelope must be a Pydantic
`BaseModel`, consistent with the existing pattern (verified: this is exactly
what plan.md's Step 1 specifies).

CLAUDE.md's Durable State Rule and API/routes boundary rule ("API/routes
present shaped read models through presenters/schemas, not raw domain
objects") are satisfied by the existing `models.py` pattern and remain
satisfied by adding `TicketsPage`/`TicketFacets` as additional typed models —
no raw dict crosses the route boundary under the plan.

## Parity Ledger Overlap

**`docs/parity_ledger/infrastructure.yaml`, `INFRA-275`** (`L4478-4544`,
`status: verified`, `priority: P2`) — this is the sole parity entry covering
`src/api/agent_ops_dashboard/`. Its `text` describes the 5 typed routes
including `GET /api/tickets` (`L4480-4482`) and the `TicketSummary`-shaped
response contract. This entry's `v2_evidence` (`L4495-4516`) already carries
**one appended paragraph** (from `TCK-20260717-TICKET-TITLE-PARSE-FIX`,
`L4507-4516`, starting "TCK-20260717-TICKET-TITLE-PARSE-FIX: ingest.py:98...").
Its `test_path` (`L4518-4538`) carries **two appended segments**: one from
`TCK-20260716-AGENTOPS-TICKETS-VIEW` (`L4519-4531`, the three AND/OR-filter
tests) and one from `TCK-20260717-TICKET-TITLE-PARSE-FIX`
(`L4532-4538`). Confirmed by direct read — the ticket's briefing description
("already has TWO appended paragraphs") is accurate when counting both
`v2_evidence` and `test_path` appends together as prior-ticket additions to
this single entry. **Any parity update from this ticket must append a new,
distinguishable segment to both `v2_evidence` and `test_path` — never
overwrite or delete the existing appended text**, per plan.md's Step 6 and
CLAUDE.md's Parity rule.

`INFRA-275` is `P2`, not `P0` — no mandatory-passing-test-path gate beyond
the general "update status/evidence when behavior changes" rule.

**`INFRA-276`** (`L4545-4586`, serve.py/Makefile/StaticFiles mount) —
confirmed unaffected: this ticket touches no build/serve/Makefile code, and
`INFRA-276`'s own text explicitly scopes itself as "Explicitly outside
INFRA-275's support_boundary" — the two entries are already partitioned
correctly and this ticket's changes stay entirely within `INFRA-275`'s
support_boundary (`L4540-4544`: "Read-only over tickets/** and
agent-monitoring/*.jsonl... Excludes frontend, build/serve tooling").

No other `docs/parity_ledger/*.yaml` file references `agent_ops_dashboard`,
`TicketsView`, or `/api/tickets` (confirmed: this subsystem is
infrastructure/observability-only, not a simulation-mechanics subsystem, so
no overlap with `substrate.yaml`, `combat_movement.yaml`,
`strategic_cognition.yaml`, `town_resource.yaml`, `progression.yaml`,
`social_narrative.yaml`, or `world_dynamics.yaml`).

## Prior Work

- **`staging_artifacts/TCK-20260717-TICKETS-TABLE-PAGINATION/plan.md`**
  (this ticket's own interrupted-attempt plan, from a completed
  Investigate→Plan→Review round before the session was interrupted mid-
  Implement). **Confirmed via `git status --porcelain -- src/api/agent_ops_dashboard/ dashboard-frontend/src/`
  that zero code changes exist for this ticket's scope** — the only
  uncommitted diffs are (a) `ingest.py`'s `parse_h1_title` → `parse_body_section(body, "Title")`
  swap, which belongs to the already-done sibling
  `TCK-20260717-TICKET-TITLE-PARSE-FIX`, and (b) `TicketsView.test.tsx`'s
  appended `describe('TicketsView — index.css reset does not zero out padding utilities')`
  block plus `GanttBar.tsx`/`RecentActivityGantt.tsx`/`RecentActivityGantt.test.tsx`/
  `index.css`/new `TimeAxis.tsx`/`TimeAxis.test.tsx`, which belong to the
  already-done siblings `TCK-20260717-CSS-LAYER-PADDING-FIX` and
  `TCK-20260717-GANTT-TIME-AXIS`. Neither diff touches `main.py`,
  `models.py`, `get_tickets`/`list_tickets`, `api.ts`'s `fetchTickets`, or
  `TicketsView.tsx` itself. **The existing plan.md is safe to reuse as-is —
  its 4 resolved decisions and file:line citations were spot-checked against
  current file state during this investigation (Step 1-5's cited line ranges
  all match the current `main.py`/`ingest.py`/`models.py`/`api.ts`/`TicketsView.tsx`
  line numbers exactly, since no code changes have landed on top of it).**
- **`stored_artifacts/TCK-20260716-AGENTOPS-TICKETS-VIEW/`** — the ticket
  that originally built `TicketsView.tsx` and its filter/sort/tag UI. Its
  investigation.md is the source of the AND-across-dimensions/OR-within-tag
  filter semantics this ticket must preserve unchanged.
- **`TCK-20260716-AGENTOPS-DASHBOARD-BACKEND`** (parent of `INFRA-275`) —
  established the typed-response-model/no-raw-dict pattern this ticket's
  `TicketsPage`/`TicketFacets` models must follow.
- **`/api/runs`'s existing `limit`/`offset` pattern** (`main.py:52-60`,
  `ingest.py:489-515`) is the direct structural precedent this ticket mirrors
  for `/api/tickets`, with two deliberate deviations already reasoned through
  in plan.md: a higher `le=500` ceiling (larger corpus) and a `total_count`
  field (`/api/runs` still lacks one — explicitly Out of Scope to add there).

## Risks and Open Questions

All four open questions named in the ticket's own "Assumptions / Open
Questions" section were already resolved in the interrupted attempt's
plan.md (total_count: yes, new field; column-sort: left unchanged, becomes
page-scoped naturally; facets: new field in the same response, computed
pre-slice; default limit=100/le=500). No open questions remain that would
block implementation — re-confirmed against current source, nothing
invalidates these decisions.

One residual risk, not a blocking open question:

- **The shared `mockFetchReturning` test helper in `TicketsView.test.tsx`
  returns a bare array today, and every existing test in that file depends
  on it.** plan.md's Step 5 verify list only names the tests it expects to
  need rewriting/adding; it does not explicitly enumerate that the helper
  itself is a single point of breakage for ~9 pre-existing tests once
  `fetchTickets`'s return type changes to an envelope. This is not a design
  flaw in the plan — Step 4/5 already require the return-type change — but
  the implementer must update `mockFetchReturning` (or every call site) as
  part of Step 5, not treat it as already covered by the per-test verify
  bullets. Flagged here so it isn't missed as "someone else's test to fix."

## Anti-Drift Hazards

- **`optionsSource` → `optionsFacets` swap is the highest-risk single edit.**
  `distinctValues`/`distinctTags` (`TicketsView.tsx:28-43`) must be
  re-pointed from the paginated `rows`/`optionsSource` to the new
  `optionsFacets` state. A one-line miss here silently reintroduces exactly
  the page-1-only-dropdown-values bug AC #3 forbids, and none of today's
  existing tests would catch it (they all use small fixtures where page size
  ≥ corpus size) — only a new test with a mocked corpus larger than the page
  size and facets values absent from that page can catch it.
- **`get_tickets`'s cache-layer `limit: Optional[int] = None` default must
  not be "aligned" to `get_runs`'s hardcoded `limit: int = 50`.** Doing so
  breaks the three existing direct-call AND/OR-filter tests
  (`test_get_tickets_and_across_dimensions_filters_tier_and_layer`,
  `test_get_tickets_or_within_tag`,
  `test_get_tickets_dimension_filter_and_tag_filter_combine_with_and`),
  which call `get_tickets(...)` with no `limit`/`offset` and expect the full
  fixture back.
- **`mockFetchReturning`'s bare-array assumption (see Risks above) is a
  cross-cutting breakage point, not a single-test concern.** Every existing
  `it(...)` block in `TicketsView.test.tsx` that calls it will fail
  simultaneously the moment `fetchTickets`'s return type changes, unless the
  helper (or its call sites) is updated in the same step as the `api.ts`/
  `TicketsView.tsx` changes — not treated as a follow-up cleanup.
- **`/api/runs` must not be touched.** Explicit Out of Scope. Do not add
  `total_count` to `RunSummary`/`RunDetail`, do not edit `list_runs`,
  `get_runs`, `_build_run_summary`, `FetchRunsParams`, `fetchRuns`, or
  `fetchAllRunsSince`. A "while I'm in here, fix the sibling gap too" edit
  would violate the ticket's explicit Out of Scope and CLAUDE.md's scope
  discipline.
- **`INFRA-275`'s two existing appended segments (one in `v2_evidence`, one
  compound append in `test_path`) must not be overwritten.** The parity
  update at close must append a third, clearly distinguishable segment.
- **Do not add a 6th route** (e.g. a separate `GET /api/tickets/facets`) —
  `test_all_five_routes_are_declared` (`test_agent_ops_dashboard_api_boundary.py:50-58`)
  asserts the exact 5-path set; a new route would gratuitously break it, and
  the facets-in-envelope design (plan.md Resolved Decision #3) avoids this
  entirely by construction.
- **`docs/observability/agent_ops_dashboard_contract.md`'s route table
  (`L28`: `GET /api/tickets` → `List[TicketSummary]`) and "Ingest / cache"
  section (`L83-87`, still describing unpaginated `get_tickets`) will go
  stale once this ticket lands.** Not listed in the ticket's own Related
  Docs as something to edit, but CLAUDE.md's "Update related docs" step
  after work applies — this doc's own preamble (`L18-20`) already warns
  "re-verify against source before relying on exact behavior after any of
  the five source tickets' code changes again," anticipating exactly this
  kind of drift. Recommend updating it alongside the parity ledger, even
  though it is not itself a Related Doc requiring edits under the ticket's
  Related Docs list — the two Related Docs actually listed
  (`agent_ops_dashboard_contract.md` and `idea_agent_ops_dashboard.md`) were
  read for context, not as edit targets by the ticket's own scope; treat the
  contract doc update as a natural consequence of "Docs were updated if
  behavior changed" in the Definition of Done, not new scope.
