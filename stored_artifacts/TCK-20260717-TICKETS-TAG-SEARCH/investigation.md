---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260717-TICKETS-TAG-SEARCH
artifact_type: investigation
tags: [observability, performance]
---

# Investigation — TCK-20260717-TICKETS-TAG-SEARCH

## CRITICAL CORRECTION TO THE TICKET'S OWN REQUEST SUMMARY / SCOPE

The ticket was written before `TCK-20260717-TICKETS-TABLE-PAGINATION` (merged
into the working tree the same day, `phase: done`) shipped. That sibling
ticket **removed the exact data flow this ticket's Scope section describes**.
Specifically:

- The ticket's Scope says: "Replace the flat `distinctTags(optionsSource)`
  button dump" and "Keep `optionsSource` (fetched ticket data) as the tag
  source — do not switch to `tag_registry.jsonl`." **Both `distinctTags()`
  and the `optionsSource` state variable no longer exist anywhere in
  `dashboard-frontend/src/`** (confirmed via repo-wide grep — the only
  remaining occurrence is a backward-reference comment in
  `TicketsView.test.tsx:32`). They were deleted by
  `TCK-20260717-TICKETS-TABLE-PAGINATION` Step 5
  (`stored_artifacts/TCK-20260717-TICKETS-TABLE-PAGINATION/plan.md` Step 5,
  ticket's own Implementation Notes: "Removed `distinctValues`/`distinctTags`
  ... and the `optionsSource` state entirely").
- The actual current tag source is `optionsFacets.tags`
  (`dashboard-frontend/src/views/TicketsView.tsx:105, 233`), populated from
  the backend's `TicketsPage.facets.tags` field
  (`dashboard-frontend/src/api.ts:96-108`), computed server-side in
  `src/api/agent_ops_dashboard/ingest.py::DashboardCache.get_tickets`
  (`L511-517`): `"tags": _distinct_sorted(tag for r in filtered for tag in
  r["tags"])` — a `sorted(set(...))` over the **full filtered-but-unpaginated
  corpus**, not the currently-loaded page and not the raw fetched rows.

This changes the correct scope statement to: *replace the flat
`optionsFacets.tags.map(...)` button dump with a searchable, collapsed
multi-select, keeping `optionsFacets.tags` (the server-computed facets field)
as the tag source — never re-deriving tags client-side from `rows`, and
never switching to `tag_registry.jsonl`.* The underlying user-facing bug
(flat unstyled button dump, no search/collapse, pushes the table below the
fold) is unchanged and still fully reproducible — only *where the tag list
comes from* has moved, from client-computed to server-computed. The fix
target (the JSX block rendering the buttons) is the same block, just fed by
a different variable.

## Current Behavior

**`dashboard-frontend/src/views/TicketsView.tsx:232-252`** — the tag filter
block, inside `data-testid="filter-tags"`:

```tsx
<div className="flex flex-wrap items-center gap-1" data-testid="filter-tags">
  {optionsFacets.tags.map((tag) => {
    const active = filters.tags.includes(tag)
    return (
      <button
        key={tag}
        type="button"
        data-testid={`filter-tag-${tag}`}
        aria-pressed={active}
        onClick={() => toggleTag(tag)}
        className={...}
      >
        {tag}
      </button>
    )
  })}
</div>
```

`optionsFacets` is `TicketsFacets` state (`L105`), initialized to
`EMPTY_FACETS` (`L27`), populated from every `fetchTickets()` response's
`.facets` field in `loadInitial` (`L123`), `applyFilters` (`L147`), and
`toggleDateSort` (`L161`). It is **not** derived from `rows` — it arrives
pre-sorted/pre-deduped from the backend on every fetch, already reflecting
the current filter set (tier/layer/status/priority/other-tags already
selected), not a global unfiltered corpus.

`toggleTag()` (`L177-180`) and `removeTag()` (`L67-72`, a manual `.reduce()`
loop, not `.filter(`) are unchanged by the pagination ticket and unaffected
by this ticket's scope — `toggleTag` mutates `filters.tags` and calls
`applyFilters`, which re-fetches via `fetchTickets(buildFetchParams(...))`,
appending one `tag=` query param per selected tag
(`dashboard-frontend/src/api.ts:129`: `for (const tag of params.tags ?? [])
query.append('tag', tag)`). This client→server contract must be preserved
byte-for-byte: selecting a tag through whatever new control replaces the
flat dump must still call `toggleTag(tag)` (or an equivalent that ends in
the same `applyFilters`/`fetchTickets` call), never re-filter rows
client-side.

**`FilterSelect` (`L74-101`)** is the existing `<select>` pattern used for
Tier/Layer/Status/Priority. It is a plain native `<select>` reading
`options: string[]` and calling `onChange(value)` — a single-value dropdown,
not a multi-select, and has no search box. It cannot be reused as-is for the
tag control (multi-select + search + collapse are all new requirements) but
its prop shape (`label`, `testId`, `options`, `onChange`) is the established
convention to follow for a new component if one is introduced.

**Tag volume**: `_distinct_sorted()` in `ingest.py` performs `sorted({v for v
in values if v})` — a plain alphabetical dedupe with no frequency ranking,
no truncation, no registry cross-reference. The ticket's ~1,309-value count
is the real number of distinct tag strings across the ticket corpus
(pre-taxonomy/free-text tags from tickets predating the tag allowlist
included), confirmed structurally consistent with `docs/guidelines/tag_registry.jsonl`
having only 48 entries (the controlled-vocabulary allowlist applies only to
tickets/artifacts created on or after 2026-07-04 — most of the corpus
predates it and carries legacy free-text tags). **`facets.tags` is exactly
as large as `optionsSource`'s old derivation was** — the pagination ticket
changed *where* the computation runs (server, over the full filtered set)
but not *what* it computes (still every distinct tag string in the corpus,
uncapped) — so the DOM-bloat bug this ticket targets is fully intact
post-pagination.

**No dependency for search/multi-select UI exists.**
`dashboard-frontend/package.json` has no combobox/multi-select/autocomplete
library (`@radix-ui/react-scroll-area`, `-slider`, `-slot`, `-tabs`,
`-tooltip` are present but none is a listbox/combobox primitive, and none is
actually imported anywhere in `src/` — confirmed via grep, zero
`ScrollArea`/`react-scroll-area` usages in production code). The ticket's
own Assumptions section already flags this correctly and it remains true
post-pagination.

## Mechanics / Engine Constraints

None. This is a read-only observability/reporting frontend view over
`tickets/**`, not a simulation subsystem — confirmed by the sibling
pagination ticket's own investigation.md ("None of `docs/mechanics/`'s six
chapters ... govern this subsystem"), which remains true here since this
ticket touches the same file for the same reason (UI only, no new backend
behavior).

The one binding architectural constraint is CLAUDE.md's API/routes rule
("API/routes present shaped read models through presenters/schemas, not raw
domain objects") — already satisfied by the existing `TicketsFacets`/
`TicketsPage` Pydantic models and untouched by this ticket, since this
ticket's Out of Scope explicitly excludes backend changes.

## Parity Ledger Overlap

**`docs/parity_ledger/infrastructure.yaml`, `INFRA-275`** (`L4478-4544+`,
`status: verified`, `priority: P2`) is the sole parity entry covering
`src/api/agent_ops_dashboard/` and, by extension, `TicketsView.tsx` as its
frontend consumer. It already carries three appended segments in
`v2_evidence`/`test_path` from `TCK-20260717-TICKET-TITLE-PARSE-FIX` and
`TCK-20260717-TICKETS-TABLE-PAGINATION` (most recently, the
`items/total_count/facets` envelope description). **This ticket is
frontend-only UI work (search/collapse over an already-existing facets
field) — it does not change `get_tickets`'s filter/facets computation, the
wire contract, or any typed model.** Whether INFRA-275 needs a fourth
appended segment depends on how "behavior changed" is read: no *backend*
behavior changes, but the *client contract* for how tags are selected
(previously: click any of N flat buttons; now: search-narrow then click)
could be read as a user-facing behavior change worth a short append,
consistent with the entry's existing practice of recording every ticket
that touched this file's client/server contract. Not P0, so no mandatory
test_path gate — but flag as a likely append target during Finalize
(parity-updater's call, not a hard requirement discovered here).

`INFRA-276` (build/serve) — confirmed unaffected, no build/serve code is
touched.

No other `docs/parity_ledger/*.yaml` file references this subsystem
(re-confirmed, same as the pagination ticket's own investigation).

## Prior Work

- **`stored_artifacts/TCK-20260717-TICKETS-TABLE-PAGINATION/`** (`investigation.md`,
  `plan.md`) — the ticket that most directly reshaped the exact code this
  ticket touches. Its plan.md Resolved Decision #3 fixed the *shape* of
  `facets` (folded into the existing `GET /api/tickets` response, computed
  pre-slice, `sorted(set(...))` per field) — this ticket must treat that
  shape as a fixed contract, not something to renegotiate. Its Anti-Drift
  Notes explicitly warn against adding a 6th route (e.g. a hypothetical
  `GET /api/tickets/facets`) — the same warning applies here: any
  server-side change this ticket might be tempted to make (e.g. a
  dedicated tag-search endpoint, or top-N/frequency-ranked tags) would
  violate both that prior ticket's design and this ticket's own explicit
  Out of Scope ("Backend changes to GET /api/tickets's tag query-param
  handling").
- **`stored_artifacts/TCK-20260716-AGENTOPS-TICKETS-VIEW/`** — original
  ticket that built `TicketsView.tsx`'s filter/sort/tag UI and established
  the AND-across-dimensions/OR-within-tag semantics this ticket must
  preserve.
- **`docs/plans/agent_ops_dashboard/proposal_ui_review_findings.md`,
  finding #2** ("Tickets view tag filter dumps the entire tag registry as
  unstyled buttons") — the origin proposal this ticket implements. Its text
  still says "tag registry" in the finding title, but the finding body and
  this ticket's own Assumptions section already correct that to
  `distinctTags(optionsSource)` (now further superseded by
  `optionsFacets.tags`, per this investigation). No further correction to
  that doc is in this ticket's scope — it is a historical proposal record,
  not a living contract doc.
- **No prior ticket has built a search/collapse/multi-select control
  anywhere in this frontend** — grep across `dashboard-frontend/src/`
  confirms zero existing `combobox`/collapsible/search-input patterns in
  either `src/components/` (`GanttBar.tsx`, `Legend.tsx`,
  `PlaybackScrubber.tsx`, `TimeAxis.tsx` — none is a list/search control) or
  any view. This is a genuinely new UI pattern for this codebase, not a
  reuse-an-existing-component task.

## Risks and Open Questions

1. **[BLOCKING — requires a decision before implementation] "Collapsed by
   default" is ambiguous between two designs with different regression
   consequences:**
   - **(a) Closed/hidden-until-opened dropdown** (click to reveal a search
     box + scrollable option list, nothing rendered until then). This is
     the more natural reading of "collapsed... multi-select" as a UI
     pattern (matches typical combobox/multiselect widgets) and best solves
     the >1.2MB-DOM-on-load complaint, since zero tag buttons render on
     initial page load.
   - **(b) Always-visible but count-bounded list** (e.g. first N tags
     alphabetically, or only currently-selected tags, shown inline; a
     search box narrows within that bound; no explicit open/close
     interaction).
   - **Why this matters**: two existing regression tests
     (`TicketsView.test.tsx:98-122`, `:124-144`) call
     `screen.getByTestId('filter-tag-observability')` /
     `filter-tag-infra` **directly, with no prior "open the dropdown"
     interaction**, against 2-tag fixtures. Under design (a), these tests
     would fail unless updated to first open the control (a legitimate,
     in-scope test update per AC #3's "matching existing test coverage" —
     but it does change these tests' bodies, which the ticket does not
     explicitly flag as expected). Under design (b) with a bound ≥ 2, both
     tests keep passing unmodified as long as the bound comfortably covers
     small fixtures. **This is a real fork in implementation approach, not
     a cosmetic detail — flag for planner/user decision, do not assume.**
2. **The `.filter(` anti-drift guard applies to the whole file's source
   text, not just the old client-row-filtering pattern.**
   `TicketsView.test.tsx:327-329`
   (`expect(TICKETS_VIEW_SOURCE).not.toMatch(/\.filter\(/)`) is a blanket
   regex over the entire file. The new tag-search-narrowing logic (matching
   `optionsFacets.tags` against a substring) **must not use
   `Array.prototype.filter`** anywhere in `TicketsView.tsx`, even though
   its actual purpose (narrowing a small in-memory string array by
   substring) is unrelated to the guard's original intent (preventing
   client-side re-filtering of fetched *rows* in place of server query
   params). The existing `removeTag()` (`L67-72`) already demonstrates the
   established workaround: a manual `.reduce()` loop. The new narrowing
   logic must follow the same non-`.filter()` idiom (e.g. `.reduce()`, a
   `for` loop, or `Array.from(iterable, ...)` with a manual push) to keep
   AC #4 passing. This is a hard implementation constraint, not a style
   preference.
3. **`optionsFacets.tags` already reflects the *currently active filter
   set*, not a global unfiltered corpus** (confirmed in `ingest.py:511-517`:
   facets are computed over `filtered`, post-filter, pre-slice). This means
   the tag list a user searches within legitimately shrinks/grows as other
   filters (tier/layer/status/priority/other tags) change — this is
   existing, intentional behavior from the pagination ticket, not something
   this ticket introduces or should "fix." No action needed, but worth
   confirming the new search UI doesn't cache a stale snapshot of
   `optionsFacets.tags` across re-fetches (React state re-render handles
   this automatically as long as the new component reads `optionsFacets`
   from props/state on every render, not a one-time captured value).
4. **No explicit AC bounds the exact count threshold ("collapsed/bounded")
   or the search debounce/interaction model** (e.g. is Escape-to-close
   required? Click-outside-to-close? Keyboard nav?). The ticket's AC #2
   only requires "initial page load does not render all ~1,309 distinct tag
   buttons simultaneously" — any bound well under that count satisfies the
   letter of the AC. Recommend the planner pick a concrete, testable number
   (e.g. render at most 20-30 tag buttons at a time, or nothing until the
   control is opened) rather than leaving it open through implementation.

## Anti-Drift Hazards

- **Do not resurrect `distinctTags(optionsSource)` or any client-side
  re-derivation of tags from `rows`.** The correct source is
  `optionsFacets.tags`, already server-computed and already reflecting the
  full filtered corpus. A well-intentioned "let me also filter/dedupe the
  tags client-side for the search box" edit that reads from `rows` instead
  of `optionsFacets` would silently reintroduce the page-1-only-tags bug
  the pagination ticket just fixed (AC #3 of that ticket) — this ticket's
  own AC has no equivalent guard test, so this must be caught by a new
  test in this ticket's own test_plan (a mocked corpus with an
  off-page tag present only in `facets.tags`, verified still reachable
  through the new search control).
- **Do not add a `.filter(` call anywhere in `TicketsView.tsx`** — see Risk
  #2 above. This is mechanically checked by an existing test and will hard-
  fail CI if violated.
- **Do not touch the tier/layer/status/priority `<select>` dropdowns** —
  explicit Out of Scope, and they are unrelated to the tag-volume problem
  (bounded corpora, already proper dropdowns).
- **Do not switch the tag source to `docs/guidelines/tag_registry.jsonl`**
  (48 entries) — this was already correctly ruled out in the ticket's own
  Assumptions, and remains ruled out: that file is a controlled-vocabulary
  allowlist for *new* tags going forward, not a reflection of what tags
  actually exist across the historical ticket corpus. Using it as the
  option source would silently hide ~1,261+ legitimate legacy tags from the
  filter.
- **Do not add a new backend route or query param** (e.g. a server-side
  tag-search endpoint) — explicit Out of Scope ("Backend changes to GET
  /api/tickets's tag query-param handling"), and the existing `facets.tags`
  payload is already small enough (~1,309 short strings, well under typical
  JSON response budgets) that client-side substring narrowing needs no
  server round-trip. AC #1 explicitly requires the narrowing to happen
  "without triggering a new fetchTickets call."
- **Do not change `toggleTag`, `removeTag`, `applyFilters`, or the
  `tag=`-per-selection query param contract in `api.ts`.** These are
  explicitly required to stay byte-for-byte compatible per AC #3 ("matching
  existing test coverage") — the new control's `onClick`/selection handler
  must still terminate in a call to the existing `toggleTag(tag)`.
- **`INFRA-275`'s three existing appended `v2_evidence`/`test_path`
  segments must not be overwritten** if this ticket appends a fourth at
  Finalize — append only, per CLAUDE.md's Parity rule and the pattern
  already established by the three prior tickets that touched this entry.
