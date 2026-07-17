---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-AGENTOPS-TICKETS-VIEW
artifact_type: plan
tags: [observability, agent-monitoring]
---

# Implementation Plan — TCK-20260716-AGENTOPS-TICKETS-VIEW

## Summary

Build `TicketsView.tsx`, a new read-only table component in `dashboard-frontend/` that fetches
`GET /api/tickets` via a new `fetchTickets()` client added to `api.ts`, renders every ticket across
all three lifecycle states, supports single-select tier/layer/status/priority filters plus
multi-select tag filters delegated entirely to backend query params (never re-filtered
client-side), supports a client-side re-order layer for the four non-date columns
(tier/layer/status/priority/tag) on top of the existing server-side date sort, renders every
`matching_runs` entry as its own link (trusting the backend's `start_ts`-descending order, never
re-sorted), and renders null `tier`/`priority`/`ticket_type` as empty cells. The component replaces
`App.tsx`'s `"Tickets view coming soon."` stub and reuses the existing `handleSelectRun`/
`selectedRunId` navigation wiring built by `AGENTOPS-REPLAY-TIMELINE` — no new routing mechanism.
Anti-drift `?raw` source-text guards (no client-side re-implementation of the AND/OR filter, no
re-sort of `matching_runs`, no non-date `sort` query param ever sent to the backend) land in the
same pass as the feature code, as a first-class step, per the `AGENTOPS-ACTIVITY-GANTT`
`DOD_BLOCKED` lesson. One additive-only backend test closing the `get_tickets` filter-coverage gap
is included since it directly de-risks AC #2 and touches no existing `ingest.py` function body.

## Decisions Locked In (resolving investigation.md Risks #1–#5)

These are implementation-detail decisions with a clear best answer given the AC wording and the
backend's actual param shape — not architectural ambiguities. Stated here so the implementer does
not re-litigate them:

- **Filter UI shape (Risk #1):** single-select (toggle/dropdown) for `tier`/`layer`/`status`/
  `priority`; multi-select (toggle pills) only for `tag`. Matches AC #2's own wording ("AND across
  dimensions, OR within tag") and the backend's actual param shape (`Optional[str]` for the four
  dimensions, `Optional[List[str]]` only for `tag`). Do **not** build multi-select pills for
  tier/layer/status/priority per the stale `UI_INTERACTION_SPEC.md` — that would send params the
  backend cannot OR together.
- **Column sorting (Risk #2, Scope bullet 3):** implement client-side re-order of the four non-date
  columns over the already-fetched, server-filtered row array. The existing server-side `sort`
  query param (`date_asc`/`date_desc`) remains the only value ever sent to `fetchTickets` — a
  tier/layer/status/priority/tag column-header click never triggers a new fetch with a non-date
  `sort` value; it locally re-orders the current `TicketSummary[]` state.
- **Backend filter-coverage gap (Risk #3):** close it. Add one additive-only test function to
  `tests/tools/test_agent_ops_dashboard_ingest.py` exercising `get_tickets`'s AND-across-dimensions/
  OR-within-tag semantics. No edits to any existing test or to `ingest.py` itself.
- **Row-link picker UX (Risk #4):** render `matching_runs` as a plain always-visible list of links
  (one `<a>`/button per entry), not a dropdown, modal, or "×N" badge-with-picker. Simplest shape
  that satisfies AC #3's literal text.
- **`App.test.tsx` stub assertions (Risk #5):** the two existing `"Tickets view coming soon."`
  assertions are expected to be falsified by this ticket and must be edited, not preserved — same
  precedent as `AGENTOPS-REPLAY-TIMELINE`'s own stub replacement.

## Steps

### Step 1 — Add `TicketSummary`/`RunMatchSummary` types and `fetchTickets()` to `api.ts`
**Files:** `dashboard-frontend/src/api.ts`
**Change:** Add two new interfaces mirroring `src/api/agent_ops_dashboard/models.py:17-36` field-for-field:
```ts
export interface RunMatchSummary {
  run_id: string
  start_ts: string | null
  end_ts: string | null
  final_status: string
}

export interface TicketSummary {
  ticket_id: string
  title: string
  tier: string | null
  ticket_type: string | null
  priority: string | null
  layer: string
  status: string
  workflow_status: string | null
  tags: string[]
  date: string
  lifecycle_state: string
  matching_runs: RunMatchSummary[]
}
```
Add a `FetchTicketsParams` interface (`tier?`, `layer?`, `status?`, `priority?`, `tags?: string[]`,
`lifecycle?`, `q?`, `sort?: 'date_asc' | 'date_desc'`) and a `fetchTickets(params)` function
following `fetchRuns`'s existing convention (`api.ts:82-95`): build a `URLSearchParams`, append one
`tag` entry per element of `params.tags` via repeated `query.append('tag', t)` (matching the
backend's `Query(default=None)` list param, `main.py:26`), `fetch('/api/tickets?...')`, throw on
`!response.ok`, cast and return the JSON as `TicketSummary[]`.
**Do NOT touch:** `fetchRuns`, `fetchRunTimeline`, `useRunsPolling`, `mergeAndSortRuns`, or any
existing export in this file. Do not add a `sort` value other than `'date_asc' | 'date_desc'` to
the type — the backend has no other sort values (`ingest.py:484`).
**Verify:** No standalone test for `api.ts` in isolation (matches the existing convention — there is
no `fetchRuns`-only test either); covered indirectly by Step 3's filter call-args test and Step 2's
rendering test, both of which import and call `fetchTickets`.

### Step 2 — Build `TicketsView.tsx`: fetch-and-render table skeleton (AC #1)
**Files:** `dashboard-frontend/src/views/TicketsView.tsx` (new)
**Change:** New component following `ReplayTimelineView.tsx`'s one-shot fetch convention
(`useState`/`useEffect` with a `cancelled` flag, `isLoading`/`error` state — not
`useRunsPolling`'s interval-polling pattern, since tickets don't need a live poll). On mount, call
`fetchTickets({})` (no filters) and render one table row per `TicketSummary`, with columns:
ticket_id, title, tier, layer, status, workflow_status, priority, tags, date, lifecycle_state,
linked runs. Use the `@` alias for imports (`import { fetchTickets, type TicketSummary } from
'@/api'`), matching `RecentActivityGantt.tsx`/`ReplayTimelineView.tsx`. Export a
`TicketsViewProps` interface with `onSelectRun: (runId: string) => void` (same shape as
`RecentActivityGanttProps`, `RecentActivityGantt.tsx:28-30`) — wired up in Step 7.
**Do NOT touch:** `RecentActivityGantt.tsx`, `GanttBar.tsx`, `ReplayTimelineView.tsx`,
`PlaybackScrubber.tsx`, or any other existing component/view file.
**Verify:** New test `TicketsView renders rows from fetchTickets covering all three lifecycle
states` in `dashboard-frontend/src/test/TicketsView.test.tsx` (test_plan.md's first New Test).

### Step 3 — Filter bar: single-select tier/layer/status/priority + multi-select tag (AC #2)
**Files:** `dashboard-frontend/src/views/TicketsView.tsx`
**Change:** Add filter controls (dropdowns/toggle buttons) for `tier`, `layer`, `status`,
`priority` (single-select each — clicking a second value replaces the first, does not add to a
set) and a multi-select tag control (clicking toggles membership in a local `Set<string>`/array).
On any filter change, call `fetchTickets({ tier, layer, status, priority, tags: [...selectedTags]
})` and replace the rendered row set with the response — **the fetched array from the backend is
the filtered result; do not additionally `.filter()` it client-side keyed on any of these five
fields.** This is the mechanism, not just a style preference — see Step 9's guard, which asserts
this in source text.
**Do NOT touch:** the `sort` param in this step (that's Step 6); do not build multi-select controls
for tier/layer/status/priority (Decision above).
**Verify:** New test `filter bar narrows rows AND-across-dimensions, OR-within-tag, via server
query params` in `TicketsView.test.tsx` (asserts `fetchTickets`/`fetch` call-args carry the right
query params, including repeated `tag=`).

### Step 4 — Linked-runs rendering: one link per `matching_runs` entry (AC #3)
**Files:** `dashboard-frontend/src/views/TicketsView.tsx`
**Change:** For each ticket row, render its "linked runs" cell as a plain list: one link/button per
`matching_runs` entry, iterated in the array's existing order (already `start_ts`-descending from
the backend, `ingest.py:178-199`) — **do not call `.sort()` on `matching_runs` anywhere in this
component.** Each link's `onClick` calls `props.onSelectRun(entry.run_id)` using that specific
entry's own `run_id`, not always `matching_runs[0]`. When `matching_runs` is empty, render no
link/picker control for that row (not an empty/broken link).
**Do NOT touch:** `App.tsx`'s `handleSelectRun`/`selectedRunId` implementation itself (only call
the prop passed in) — that logic is `AGENTOPS-REPLAY-TIMELINE`'s, already built and out of scope to
modify.
**Verify:** New test `linked-runs control surfaces every matching_runs entry as a separate link,
never collapsed` in `TicketsView.test.tsx` (2+ entries → 2+ links, each navigating with its own
`run_id`; empty array → no control rendered).

### Step 5 — Null-safe rendering for `tier`/`priority`/`ticket_type` (AC #4)
**Files:** `dashboard-frontend/src/views/TicketsView.tsx`
**Change:** Render the `tier`, `priority`, and `ticket_type` table cells as empty when the field is
`null` — e.g. `{ticket.tier ?? ''}` or an explicit `<td data-testid="tier-cell">{ticket.tier}</td>`
where React renders `null` as nothing. Do **not** use `??` with a fallback string (no `'N/A'`,
`'—'`, `'unknown'`, `'null'`, or similar) — the cell must contain no text content for a null value.
**Do NOT touch:** the `status` field (frontmatter, always present, distinct from
`workflow_status`) — do not apply this null-handling pattern to `status`, and do not conflate
`status` with `workflow_status` in the column layout (two separate columns, per investigation.md's
explicit warning).
**Verify:** New test `null tier/priority/type render as null/empty, never a placeholder string` in
`TicketsView.test.tsx` — includes the negative assertion against `"N/A"`/`"null"`/`"—"`/`"unknown"`.

### Step 6 — Client-side sort for non-date columns (Scope bullet 3)
**Files:** `dashboard-frontend/src/views/TicketsView.tsx`
**Change:** Add clickable column headers for `tier`, `layer`, `status`, `priority`, and `tag`
(first tag, or a joined string, for sort-key purposes). Clicking a header re-orders the current
in-memory `TicketSummary[]` state (the already-fetched, already-server-filtered array) using a
local `[...rows].sort(...)` — this is the one permitted `.sort()` call in the component, and it
must never be applied to `matching_runs` (Step 4's guard) or trigger a new `fetchTickets` call.
Keep the existing date column's sort server-side: clicking the date header (or a dedicated
asc/desc toggle) calls `fetchTickets({ ...currentFilters, sort: 'date_asc' | 'date_desc' })` as
today. **Never construct or send a `sort` value other than `'date_asc'`/`'date_desc'`** to
`fetchTickets` for any column — non-date column clicks stay entirely local state.
**Do NOT touch:** `api.ts`'s `FetchTicketsParams.sort` type (already constrained to the two literal
values in Step 1) — do not widen it to accept `'tier_asc'` etc.
**Verify:** New test (test_plan.md Anti-Drift Test Guards item 4) asserting a non-date column-header
click re-orders rendered rows without calling `fetchTickets` again (or, if it does call it, that
`sort` is unchanged from its current `date_asc`/`date_desc` value). Location:
`TicketsView.test.tsx`.

### Step 7 — Wire `TicketsView` into `App.tsx`, replacing the stub
**Files:** `dashboard-frontend/src/App.tsx`
**Change:** Replace the literal stub at line 45 (`<div className="p-6
text-text-secondary">Tickets view coming soon.</div>`) with `<TicketsView onSelectRun={handleSelectRun} />`,
following the exact pattern already used for `<RecentActivityGantt onSelectRun={handleSelectRun}
/>` at line 43. Add the import: `import { TicketsView } from '@/views/TicketsView'`.
**Do NOT touch:** the `PageView` union, `NAV_ITEMS`, the `'activity'`/`'replay'` render branches, or
`handleSelectRun`/`selectedRunId` state — all already correct and owned by prior tickets. Do not
introduce `react-router` or any routing library.
**Verify:** Covered by Step 8's updated `App.test.tsx` assertions.

### Step 8 — Update `App.test.tsx`: replace falsified stub assertions, add navigation test
**Files:** `dashboard-frontend/src/test/App.test.tsx`
**Change:** Edit the two existing assertions referencing `"Tickets view coming soon."` (confirmed
at lines 53-59 and 61-77 by investigation.md) to instead assert the real `TicketsView` content (or
a `data-testid`) renders when the Tickets tab is active, and is absent when another tab is active.
Add the new integration test from test_plan.md: `row-link navigates to that row's Replay timeline
via the existing App navigation state` — clicking a Tickets row's link switches the active view to
Replay and renders `ReplayTimelineView` scoped to that row's `matching_runs[i].run_id`. Also add
`App-shell scaffold smoke test: Tickets tab renders the real TicketsView, other tabs unaffected` —
activating Tickets renders real content while Recent Activity and Replay continue to render
unchanged.
**Do NOT touch:** any assertion currently covering `'activity'` or `'replay'` tab content that
isn't specifically about the stale Tickets stub string — those must continue passing unmodified.
**Verify:** `dashboard-frontend/src/test/App.test.tsx` itself, run via `cd dashboard-frontend && npm test`.

### Step 9 — Anti-drift `?raw` source-text guards (first-class step)
**Files:** `dashboard-frontend/src/test/TicketsView.test.tsx`
**Change:** This is an explicit, dedicated step — not folded into Steps 2-6's feature tests — per
the `AGENTOPS-ACTIVITY-GANTT` `DOD_BLOCKED` lesson (guards planned but skipped in the first
Implement pass). Add, in the same test file, following `GanttBar.test.tsx`'s `?raw` import pattern
(`import TICKETS_VIEW_SOURCE from '../views/TicketsView.tsx?raw'`):
1. A guard asserting `TICKETS_VIEW_SOURCE` contains no `.filter(` call applied to a fetched
   `TicketSummary[]`/rows array keyed on `tier`/`layer`/`status`/`priority`/`tags` — filtering must
   only ever be expressed as query params passed into `fetchTickets` (Step 3's mechanism).
2. A guard asserting `TICKETS_VIEW_SOURCE` contains no `.sort(` call applied to a `matching_runs`
   array (Step 4's guard, made explicit and automated rather than left to code review).
3. A guard asserting `TICKETS_VIEW_SOURCE` never constructs a `sort` value other than the literals
   `'date_asc'`/`'date_desc'` for use in a `fetchTickets` call (Step 6's guard).
These three guards must be written and passing in the same Implement pass as Steps 2-6, not
deferred to a follow-up.
**Do NOT touch:** `GanttBar.test.tsx` itself (read-only reference for the `?raw` pattern, not a
file to modify).
**Verify:** The three new guard assertions themselves, run via `cd dashboard-frontend && npm test`.

### Step 10 — Additive backend test: `get_tickets` AND/OR filter semantics (closes Risk #3)
**Files:** `tests/tools/test_agent_ops_dashboard_ingest.py` (new test function(s) appended; no
edits to any existing test or to `ingest.py`/`main.py`/`models.py`)
**Change:** Add one or more new test functions (not modifying existing ones) exercising
`DashboardCache.get_tickets` directly against a fixture spanning several tickets with distinct
`tier`/`layer`/`workflow_status`/`priority`/`tags` combinations:
(a) combining `tier` + `layer` filters returns only rows matching both (AND),
(b) passing two `tag` values returns rows matching either (OR-within-tag),
(c) combining a dimension filter with a tag filter is AND between the two groups.
This closes the coverage gap investigation.md Risk #3 identified (zero existing
`test_get_tickets*` tests) and directly de-risks AC #2, which this ticket's frontend logic depends
on being correct.
**Do NOT touch:** `src/api/agent_ops_dashboard/main.py`, `ingest.py`, or `models.py` — this step is
test-only and additive. Do not modify any existing test function in
`test_agent_ops_dashboard_ingest.py` (including the ticket-run join tests or the null-body-section
test test_plan.md lists as must-stay-green-unmodified).
**Verify:** `pytest tests/tools/test_agent_ops_dashboard_ingest.py -m "not slow"` passes, including
the new test function(s), with zero diff to `src/api/agent_ops_dashboard/`.

### Step 11 — Final verification pass
**Files:** none (verification only)
**Change:** Run the full scoped test commands from test_plan.md:
```
pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/architecture/test_api_read_model_guard.py -m "not slow"
```
```
cd dashboard-frontend && npm test
```
Then run `git diff --stat` and confirm: (a) no changes under `src/api/agent_ops_dashboard/main.py`,
`ingest.py`, or `models.py` beyond Step 10's new test function(s) in the test file itself — no
existing function body in those three source files may differ; (b) all changed/new files are
confined to `dashboard-frontend/src/**` and `tests/tools/test_agent_ops_dashboard_ingest.py`.
**Do NOT touch:** nothing — this step performs no edits, only runs commands and inspects the diff.
**Verify:** Both scoped commands exit green; `git diff --stat` matches the expected file set above.

## Scope Guards

Explicit list of things this plan must not touch, derived from the ticket's Out of Scope section
and investigation.md's Anti-Drift Hazards:

- Do not implement or modify `GET /api/tickets` itself, its filter logic, its date-only `sort`
  implementation, or `build_matching_runs`'s join/sort logic
  (`src/api/agent_ops_dashboard/main.py`, `ingest.py:178-199,448-485`). Step 10's addition is
  test-only and additive; no existing function body in `main.py`/`ingest.py`/`models.py` changes.
- Do not build or modify the Replay timeline view's own content (`ReplayTimelineView.tsx`,
  `PlaybackScrubber.tsx`) — only call the existing `onSelectRun`/`handleSelectRun` prop wiring.
- Do not build or modify the Recent Activity Gantt view (`RecentActivityGantt.tsx`, `GanttBar.tsx`,
  `Legend.tsx`) — sibling ticket, already DONE.
- Do not conflate `status` (frontmatter, always present) with `workflow_status` (body `## Status`
  section, nullable) — render as two distinct columns.
- Do not add a placeholder/default string (`'N/A'`, `'—'`, `'unknown'`, `'null'`, etc.) for a null
  `tier`/`priority`/`ticket_type` — must render as empty.
- Do not introduce `react-router` or any routing library — reuse the existing `useState`-based
  view-switching convention in `App.tsx`.
- Do not touch `src/api/server.py`, `src/api/read_model_cache.py`, `src/api/routes/history.py`, or
  `src/api/ws/stream.py` — not this dashboard's real API surface. Already guarded directory-wide by
  `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`; no ticket-specific duplicate
  needed, but run it as part of Step 11.
- Do not add Makefile targets, `vite build` production wiring, or FastAPI `StaticFiles` mounting —
  `AGENTOPS-BUILD-SERVE`'s scope, a separate ticket in this batch.
- Do not build multi-select controls for `tier`/`layer`/`status`/`priority` (only `tag` is
  multi-select) — see Decisions Locked In, Risk #1.
- Do not re-implement the AND-across-dimensions/OR-within-tag filter logic client-side as a second
  filter pass over an already-fetched full list — filtering is expressed only as query params to
  `fetchTickets` (Step 3, guarded by Step 9).
- Do not re-sort `matching_runs` client-side — trust the backend's `start_ts`-descending order
  (Step 4, guarded by Step 9).
- Do not send any `sort` query param value to `fetchTickets` other than `'date_asc'`/`'date_desc'`
  (Step 6, guarded by Step 9).

## Dependency Map

- Step 1 (api.ts additions) must land before Steps 2-6 (all depend on `fetchTickets`/
  `TicketSummary`/`RunMatchSummary` existing).
- Step 2 (base table) must land before Steps 3, 4, 5, 6 (each extends the same component file).
- Steps 3, 4, 5 are independent of each other once Step 2 exists — order among them does not
  matter, but each is a separable, individually-testable change to the same file.
- Step 6 depends on Step 2 (needs the base table and column headers to attach sort behavior to).
- Step 7 (App.tsx wiring) depends on Steps 2-6 being complete (the component must be feature-complete
  before it replaces the stub, since Step 8's tests assert on the real rendered content).
- Step 8 (App.test.tsx updates) depends on Step 7.
- Step 9 (anti-drift guards) depends on Steps 2-6 (the source text being guarded must exist) but is
  independent of Steps 7-8 — can be written in parallel with them, must land in the same pass.
- Step 10 (backend test) is fully independent of Steps 1-9 — no shared files, can be done at any
  point in the sequence.
- Step 11 (final verification) depends on all prior steps being complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Table renders rows from GET /api/tickets covering tickets/inprogress/, tickets/done/, and tickets/todos/ | Step 1, Step 2 | `TicketsView renders rows from fetchTickets covering all three lifecycle states` (`TicketsView.test.tsx`) |
| Filtering by tier/layer/status/priority/tag narrows rows correctly (AND across dimensions, OR within tag) | Step 1, Step 3, Step 10 | `filter bar narrows rows AND-across-dimensions, OR-within-tag, via server query params` (`TicketsView.test.tsx`); `get_tickets AND-across-dimensions/OR-within-tag filter semantics` (`test_agent_ops_dashboard_ingest.py`) |
| Each row's linked-runs control surfaces every matching_runs entry (sorted start_ts descending) as links, not collapsed to one | Step 4 | `linked-runs control surfaces every matching_runs entry as a separate link, never collapsed` (`TicketsView.test.tsx`) |
| A ticket with null tier/priority/type renders as null/empty in the table, not an error or placeholder | Step 5 | `null tier/priority/type render as null/empty, never a placeholder string` (`TicketsView.test.tsx`) |
| (Scope bullet 3) Column sorting by tier/layer/status/priority/tag | Step 6, Step 9 (guard) | `TicketsView.test.tsx` sort-toggle test (test_plan.md Anti-Drift Test Guards item 4) |
| Each row links to the Replay timeline view for its matching run(s) | Step 4, Step 7 | `row-link navigates to that row's Replay timeline via the existing App navigation state` (`App.test.tsx`) |

## Anti-Drift Notes

- The single most consequential investigation finding: the backend `sort` param is date-only
  (`ingest.py:484`, `DATA_MODEL.md:29`), while the ticket's own Scope bullet 3 asks for column
  sorting across five fields. Step 6 resolves this via client-side re-order of the already-fetched
  array — never a fabricated non-date `sort` param value sent over the wire. Step 9's guard #3
  makes this a hard, automated check, not a convention relying on code review.
- `status` and `workflow_status` are two distinct `TicketSummary` fields with different meanings
  (frontmatter vs. body `## Status` section) — a naive implementer reading `UI_INTERACTION_SPEC.md`'s
  "Status badge" language could wire the wrong field. Step 2's column layout must keep them
  separate.
- `matching_runs` collisions are real (43/618 confirmed in investigation.md) — Step 4 must not
  assume a 1:1 ticket-to-run relationship, and must not silently show only the first entry.
- `App.test.tsx`'s two `"Tickets view coming soon."` assertions are *expected* to fail against the
  old code once this ticket lands — this is correct, in-scope churn (Step 8), not a regression to
  avoid, mirroring `AGENTOPS-REPLAY-TIMELINE`'s identical precedent for its own stub.
- Per the plan-gate static check (`tools/gate_checks/plan_gate_static.py::plan_has_unresolved_questions_heading`),
  this plan intentionally omits an `## Unresolved Questions` heading — all prior investigation
  Risks (#1-#5) were resolved into concrete decisions above, none require human input before
  implementation begins.
- Carry forward the `DOD_BLOCKED` lesson from `AGENTOPS-ACTIVITY-GANTT`'s first pass: Step 9's
  guards must be implemented in the same Implement pass as Steps 2-6, not deferred to a follow-up
  fix pass.

## Deviations

- **Step 2's column list omitted `ticket_type`.** Implemented anyway, as a `Type` column
  (`data-testid="type-cell-{ticket_id}"`), because AC #4 explicitly requires null-safe rendering
  for `tier`/`priority`/`ticket_type`, and that is untestable without a rendered `ticket_type`
  cell. Treated as an oversight in Step 2's literal column list relative to the ticket's own
  Acceptance Criteria, not an intentional scope exclusion — implementing it does not touch any
  file/function this plan's Scope Guards forbid.
- **Step 9 guard #1 ("no `.filter(` call... keyed on tier/layer/status/priority/tags")
  implemented as a blanket "no `.filter(` anywhere in `TicketsView.tsx`"**, matching the stricter
  precedent already set by `ReplayTimelineView.test.tsx`'s own anti-drift guard
  (`expect(REPLAY_VIEW_SOURCE).not.toMatch(/\.filter\(/)`), rather than a narrower regex trying to
  detect the specific keying. The component's actual implementation never needed `.filter()` for
  any purpose (tag removal uses `.reduce()` instead), so the blanket form is strictly satisfiable
  and simpler to keep true over time.
- **Step 9 guard #3 ("no `.sort(` applied to `matching_runs`") was first drafted as an "exactly one
  `.sort(` call in the whole file" assertion, which failed**: `distinctValues`/`distinctTags` (the
  filter-dropdown option builders) each call `.sort()` on their own local `Array.from(...)` value
  lists — unrelated to `rows` or `matching_runs`, and not a violation of the guard's actual intent.
  Rewrote the assertion to a targeted regex checking specifically that no `.sort(` call has
  `matching_runs` as its receiver, rather than counting total `.sort(` occurrences.
- `dashboard-frontend/node_modules` was absent at the start of Implement (only
  `package-lock.json` existed); ran `npm ci` before `npm test` could execute. Not a scope
  deviation — a pure lockfile-driven install, no plan step assumed a pre-installed
  `node_modules`.
