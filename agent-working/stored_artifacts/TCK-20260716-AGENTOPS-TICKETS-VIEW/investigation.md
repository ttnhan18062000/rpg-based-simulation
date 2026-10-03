---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-AGENTOPS-TICKETS-VIEW
artifact_type: investigation
tags: [observability, agent-monitoring]
---

# Investigation — TCK-20260716-AGENTOPS-TICKETS-VIEW

## Current Behavior

**Backend — `GET /api/tickets` already exists and is functionally real, not a stub.**
Confirmed by direct read, not the ticket's own stale "Related Code Areas" boilerplate.

`src/api/agent_ops_dashboard/main.py:29-49` (`list_tickets`):
```python
@app.get("/api/tickets", response_model=List[TicketSummary])
async def list_tickets(
    tier: Optional[str] = None,
    layer: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tag: Optional[List[str]] = Query(default=None),
    lifecycle: Optional[str] = None,
    q: Optional[str] = None,
    sort: str = "date_desc",
) -> List[TicketSummary]:
```
Only `tag` is a repeatable/list param — `tier`/`layer`/`status`/`priority` each accept exactly one
value. This matches, not contradicts, the ticket's own AC #2 wording ("AND across dimensions, OR
within tag") — but it does **not** match `UI_INTERACTION_SPEC.md` §1's "multi-select pills for
Tier, Layer, Priority, Tag" (see Risks #1).

`DashboardCache.get_tickets` (`src/api/agent_ops_dashboard/ingest.py:448-485`):
- Equality filter per dimension (`tier`, `layer` — compared against `layer`, `status` — compared
  against `workflow_status` not frontmatter `status`, `priority`), `lifecycle` (`"all"` bypasses
  the filter), `tags` (set-intersection = OR-within-tag, `ingest.py:476`), `q` (substring match
  against `f"{title} {ticket_id}".lower()`).
- **Sort is date-only.** `ingest.py:484`: `filtered.sort(key=lambda r: r["date"] or "",
  reverse=(sort != "date_asc"))`. The `sort` query param has exactly two meaningful values
  (`date_desc`/`date_asc`, confirmed identically in `DATA_MODEL.md:29`: `` `sort` | `str` |
  `date_desc` (default) / `date_asc` ``). There is no server-side support for sorting by
  tier/layer/status/priority/tag despite this ticket's own Scope bullet 3 ("Implement column
  sorting by tier/layer/status/priority/tag") — see Risks #2, this is the most consequential
  finding in this investigation.
- Ticket-run join (`build_matching_runs`, `ingest.py:178-199`): every `runs.jsonl` row whose
  `run_id == ticket_id`, sorted `start_ts` descending, rows without a `start_ts` sorted last never
  first. Already server-side, already sorted — do not re-sort client-side (AC #3).
- Nullable fields: `parse_ticket_file` (`ingest.py:87-118`) sets `tier`/`ticket_type`/`priority` to
  `None` via `parse_body_section(body, "Tier") or None` when the body section is absent — genuinely
  `None`, not an empty string or placeholder (AC #4 requirement already satisfied server-side).
- Lifecycle-collision handling: when the same `ticket_id` exists under more than one of
  `tickets/{inprogress,done,todos}/`, `_LIFECYCLE_PRIORITY` (`ingest.py:55`) picks
  `inprogress > done > todos` — relevant only as background, not something this frontend ticket
  touches.

**Response shape** (`src/api/agent_ops_dashboard/models.py:17-36`):
```python
class RunMatchSummary(BaseModel):
    run_id: str
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None
    final_status: str

class TicketSummary(BaseModel):
    ticket_id: str
    title: str
    tier: Optional[str] = None
    ticket_type: Optional[str] = None
    priority: Optional[str] = None
    layer: str
    status: str
    workflow_status: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    date: str
    lifecycle_state: str
    matching_runs: List[RunMatchSummary] = Field(default_factory=list)
```
Note `status` (frontmatter `status: active`, always present) vs. `workflow_status` (body `##
Status` section, nullable, the `OPEN`/`INPROGRESS`/`BLOCKED`/`DONE` value
`UI_INTERACTION_SPEC.md` §1 means by "Status badge") — these are two different fields and the
table must not conflate them.

**Frontend scaffold** (built by sibling tickets, confirmed DONE):
- `dashboard-frontend/src/api.ts` — mirrors `models.py` field-for-field for `RunSummary`/
  `RunDetail`/`RunTimeline`/etc., but has **no `TicketSummary`/`RunMatchSummary` interfaces and no
  `fetchTickets()` function yet**. This ticket must add both, following `fetchRuns`'s existing
  typed-fetch convention (`api.ts:82-95`) — build a `URLSearchParams` from a params object,
  `fetch('/api/tickets?...')`, throw on `!response.ok`, cast the JSON.
- `dashboard-frontend/src/App.tsx:5,9,44-46` — `PageView` union already includes `'tickets'`, the
  nav button already exists, and the render branch is a literal stub:
  `<div className="p-6 text-text-secondary">Tickets view coming soon.</div>` — exact text
  confirmed by direct read, matches handoff notes verbatim. This is the integration point to
  replace.
- `dashboard-frontend/src/test/App.test.tsx:53-59,61-77` already asserts this exact string in two
  places (`"lands on the RecentActivityGantt view by default"` checks it's absent;
  `"App-shell scaffold smoke test..."` checks it's present when the Tickets tab is active and
  absent when Replay is active). Both assertions will be **falsified** by a correct implementation
  — expected, in-scope churn (see `AGENTOPS-REPLAY-TIMELINE`'s identical precedent), not a
  regression to avoid.
- `App.tsx` already has `selectedRunId`/`handleSelectRun`/`ReplayTimelineView` wiring from
  `AGENTOPS-REPLAY-TIMELINE` — a Tickets row's "navigate to Replay timeline" link only needs to
  call the existing `handleSelectRun(runId)` (or an equivalent prop threaded down), not invent new
  navigation state.
- No routing library is used anywhere (`useState`-based view switching only) — do not introduce
  `react-router` for row-links; reuse the existing pattern.
- `dashboard-frontend/vite.config.ts:5` resolves `'@'` → `./src`; `RecentActivityGantt.tsx`/
  `ReplayTimelineView.tsx` both import via `@/api`, `@/components/...` — follow the same alias
  convention for the new `TicketsView.tsx`.
- Test convention confirmed: Vitest + Testing Library, colocated under
  `dashboard-frontend/src/test/`, `npm test` → `vitest run`. `GanttBar.test.tsx` establishes the
  `?raw` source-text anti-drift pattern, directly reusable here.

## Mechanics / Engine Constraints

None apply. This is presentation-layer tooling over `tickets/**` frontmatter/body text and
`agent-monitoring/*.jsonl` telemetry — not simulation gameplay mechanics, and it never touches
`AuthoritativeState`. Same conclusion as both sibling tickets' investigations. The repo-wide rule
that does apply is the API-boundary rule ("do not expose raw domain models from APIs"), already
satisfied server-side by `models.py`'s typed Pydantic responses (`TicketSummary`/
`RunMatchSummary`); the frontend mirror is to consume those typed shapes as declared in `api.ts`
and never duck-type or recompute fields the backend already computed (matching-runs sort order,
null-vs-placeholder semantics).

## Parity Ledger Overlap

- **`INFRA-275`** (`docs/parity_ledger/infrastructure.yaml:4478`), `status: verified`, `priority:
  P2` — covers the entire Agent Ops Dashboard backend including `GET /api/tickets` by name
  ("exposing GET /api/tickets, /api/runs, /api/runs/{run_id}, /api/runs/{run_id}/timeline,
  /api/health as typed Pydantic response models only"). No P0 entries in this area, so no
  `test_path` gate applies. This frontend-only ticket does not need a new parity ledger entry or
  edit to `INFRA-275` — it is presentation work consuming an already-parity-tracked backend, the
  same conclusion `AGENTOPS-REPLAY-TIMELINE`'s investigation reached for `/timeline`.
- No other parity ledger entry overlaps; `search_docs`/grep across `docs/parity_ledger/` for
  "tickets view"/"dashboard" surfaced only `INFRA-275` and unrelated simulation-engine "replay"
  entries (see `AGENTOPS-REPLAY-TIMELINE`'s investigation for that false-positive already
  recorded).

## Prior Work

- `TCK-20260716-AGENTOPS-DASHBOARD-BACKEND` (done): built `main.py`/`ingest.py`/`models.py`,
  including `/api/tickets` and its filter/sort/join logic this ticket consumes read-only.
  **Notably, `tests/tools/test_agent_ops_dashboard_ingest.py` has zero tests exercising
  `get_tickets`'s filter logic** (tier/layer/status/priority/tag/lifecycle/q) — its own docstring
  scopes it to "AC #2, #3, #6, #7, #8" (ticket-run join, inferred-active, files-touched,
  legacy-schema, malformed-JSONL), none of which is ticket filtering. This is a real backend
  regression-surface gap this ticket's own AC #2 depends on — see Risks #3.
- `TCK-20260716-AGENTOPS-ACTIVITY-GANTT` (done, plus a `DOD_BLOCKED` fix-pass): built the
  `dashboard-frontend/` scaffold, `api.ts`'s typed-fetch + hook pattern, `GanttBar.tsx`'s
  mutually-exclusive-class + `?raw` source-text anti-drift pattern this ticket should reuse for
  its own filter-state/row-rendering logic and guards.
- `TCK-20260716-AGENTOPS-REPLAY-TIMELINE` (done): built `ReplayTimelineView.tsx`, wired
  `App.tsx`'s `selectedRunId`/`handleSelectRun` state this ticket's row-links should reuse, and
  established the precedent (documented in its own investigation.md/test_plan.md) for how to
  handle "this ticket falsifies a sibling's stub-placeholder test on purpose" — same situation
  applies here for `App.test.tsx`'s `"Tickets view coming soon."` assertions.
- `docs/guides/ticket_reporting.md` — documents existing CLI reporting tools
  (`tools/generate_registry.py`, `tools/tag_registry.py`, etc.) that read the same
  `tickets/`/`docs/REGISTRY.yaml`/`working_log.csv` corpus this dashboard also reads, but via a
  different (registry-based, done/-only) path — confirms `docs/REGISTRY.yaml` is not a substitute
  data source for this view, consistent with the ticket's own Assumptions section.

## Risks and Open Questions

1. **Multi-select filter UI (per `UI_INTERACTION_SPEC.md` §1) does not match what the backend
   actually accepts for tier/layer/status/priority.** The design doc says "multi-select pills for
   Tier, Layer, Priority, Tag"; the real backend (`main.py:31-34`) accepts a single string for
   each of `tier`/`layer`/`status`/`priority` and only `tag` is a repeatable list
   (`Optional[List[str]]`). This ticket's own AC #2 text ("AND across dimensions, OR within tag")
   is actually consistent with **single-select per dimension, multi-select only for tag** — it
   does not require multi-select tier/layer/priority. Building true multi-select pills for those
   four dimensions per the design doc would require sending multiple values per param that the
   backend cannot OR together, silently producing wrong results (e.g., last-value-wins or a 422).
   **Recommendation, not yet a decision**: implement single-select (toggle/dropdown) for
   tier/layer/status/priority, multi-select only for tag, matching the AC text and backend
   contract over the stale design-doc detail. Flagging for the plan to state explicitly rather
   than an implementer discovering the param-shape mismatch mid-build.
2. **Column sorting by tier/layer/status/priority/tag (ticket Scope bullet 3) has no server-side
   support, and is explicitly *not* in this ticket's own Acceptance Criteria list.** Three sources
   disagree:
   - Ticket Scope: "Implement column sorting by tier/layer/status/priority/tag."
   - Ticket Acceptance Criteria (4 bullets): does not mention sorting at all — only rendering,
     filtering, linked-runs, and null-handling are testable ACs.
   - `UI_INTERACTION_SPEC.md` §1: "**No other sort columns for v1** — this is a filterable log,
     not a spreadsheet," and `DATA_MODEL.md:29` / `ingest.py:484` confirm the backend `sort` param
     is date-only.
   Given the handoff notes' own instruction not to reimplement server-side logic client-side, and
   this ticket's Out-of-Scope explicitly forbids modifying `ingest.py`, the only way to honor the
   Scope bullet without touching the backend is **client-side sort over the already-fetched
   (server-filtered) row set** for the four non-date columns, layered on top of the existing
   server-side date sort. This is a real scope/architecture decision the plan must pin down
   explicitly — do not assume; state the chosen interpretation in plan.md rather than silently
   picking one.
3. **`get_tickets`'s filter logic (tier/layer/status/priority/tag/lifecycle/q AND/OR semantics)
   has zero existing backend test coverage** (confirmed by reading
   `test_agent_ops_dashboard_ingest.py` in full — no `test_get_tickets*` or filter-focused test
   exists). This ticket's AC #2 depends on that untested behavior being correct. Since modifying
   `ingest.py`'s implementation is explicitly out of scope, but *adding a test* for existing,
   already-shipped behavior is not "implementing the endpoint," the plan should decide whether
   this ticket adds a backend regression test closing that gap (recommended, low-risk, additive
   only) or defers it and treats the AC as validated only by frontend integration-style tests
   against a live/mocked response. Flagging as an open question rather than assuming.
4. **Row-link picker UX for `matching_runs.length > 1` is unspecified at the AC level.**
   `UI_INTERACTION_SPEC.md` §1 describes a single-link icon vs. "×N" badge + picker interaction,
   but this ticket's AC #3 only requires "surfaces every matching_runs entry ... as links ... not
   collapsed to one" — it does not mandate the picker UX specifically. A simpler always-visible
   list of N links per row (no picker/modal) would also satisfy the AC text. Plan should state
   which interaction shape it commits to.
5. **`App.test.tsx`'s two existing `"Tickets view coming soon."` assertions will be falsified** by
   a correct implementation — expected, in-scope test churn per the identical precedent set by
   `AGENTOPS-REPLAY-TIMELINE`'s own stub-replacement (its investigation.md/test_plan.md Risk #5 /
   Regression Surface section). test_plan.md must call this out explicitly, not treat it as
   "keep green as-is."

## Anti-Drift Hazards

- Do not implement or modify `GET /api/tickets`, its filter logic, its date-only `sort`
  implementation, or `build_matching_runs`'s join/sort (`ingest.py:178-199, 448-485`) —
  backend-owned, already done. Consume `TicketSummary`/`RunMatchSummary` fields verbatim; any
  non-date sort must be a client-side re-sort of the already-fetched, server-filtered array, never
  a reimplementation of the filter/join logic itself.
- Do not conflate `status` (frontmatter, always present, not the workflow lifecycle) with
  `workflow_status` (body `## Status` section, nullable, the `OPEN`/`INPROGRESS`/`BLOCKED`/`DONE`
  value the design doc's "Status badge" column means) — two different `TicketSummary` fields.
- Do not add a placeholder/default string for a `null` `tier`/`priority`/`ticket_type` — AC #4 is
  explicit that these render as null/empty, not `"N/A"` or similar.
- Do not build the Recent Activity Gantt view or the Replay timeline view's own content — both
  fully out of scope, owned by sibling tickets already DONE. Row-links should call into the
  existing `handleSelectRun`/`ReplayTimelineView` wiring `App.tsx` already has, not reimplement
  any part of it.
- Do not introduce `react-router` or any routing library — mirror the existing `useState`-based
  view-switching convention.
- Do not touch `src/api/server.py`, `src/api/read_model_cache.py`, `src/api/routes/history.py`, or
  `src/api/ws/stream.py` — none are this dashboard's real API surface; already guarded
  directory-wide by `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`, which
  automatically covers any new file under `dashboard-frontend/src/` including
  `views/TicketsView.tsx` (confirmed via its `_frontend_source_files()` recursive glob). No
  ticket-specific duplicate of this guard is needed. `src/api/server.py`'s `.filter-bar`/
  `.filter-pill` CSS **class naming convention** may be reused as a naming pattern (no code
  coupling, no file-path string reference) — the guard only forbids referencing the forbidden
  *paths* as strings/imports in frontend source.
- Do not add Makefile targets, `vite build` production wiring, or `FastAPI` `StaticFiles`
  mounting — `AGENTOPS-BUILD-SERVE`'s scope.
- Carry forward the `DOD_BLOCKED` lesson from `AGENTOPS-ACTIVITY-GANTT`'s first pass: implement
  every anti-drift guard listed in test_plan.md in the same Implement pass as the feature code,
  not a follow-up fix pass.
