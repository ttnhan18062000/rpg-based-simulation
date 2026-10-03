---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND
artifact_type: investigation
tags: [dashboard, observability, api-design]
---

# Investigation: TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND

## Current Behavior
`TCK-20260718-GLOSSARY-API` (done) exposes `GET /api/glossary`, a typed `GlossaryResponse` of
`{term: {term, category, description}}`, merging 35 registry-owned glossary terms with 19
layer descriptions read live from `layer_registry.jsonl`'s `note` field. Nothing on the frontend
fetches it yet. Enum-like values render as bare text across the dashboard with no explanation of
what they mean: Tier/Layer/Status/Priority cells in `TicketsView`, event `status` values in
`ReplayTimelineView`, and bar labels (gate-failure reason codes, tier/type/priority/layer
distributions, Slow Runs `final_status`) in `StatsView`.

`RecentActivityGantt.tsx` + `GanttBar.tsx` + `Legend.tsx` were checked as in-scope candidates and
excluded: `GanttBar.tsx` renders only `run.run_id` as visible text, never the raw `final_status`
string; it colors bars via `classifyFinalStatus()`, a synthetic 3-way bucket (`done`/`failed`/
`neutral`) that collapses many distinct status values many-to-one. `Legend.tsx`'s three items are
hand-written descriptive prose already ("Blocked / Failed / Conflicts"), not a single enum value —
there is no 1:1 glossary term to attach a tooltip to. Confirmed by direct read of both files: no
raw status string is ever rendered as element text in either component.

## Mechanics/Engine Constraints
Dashboard tooling only, no Mechanics Bible/engine-contract surface. This ticket must not introduce
any hardcoded description string in `dashboard-frontend/src/` — the whole point of the epic is
that descriptions are backend-owned data, UI only renders what `/api/glossary` returns.

## Prior Work / Precedent
- Radix `Tooltip` primitive already used in this codebase (`RecentActivityGantt.tsx`'s existing
  bar tooltips) — reused directly rather than introducing a second tooltip library.
- `RecentActivityGantt.test.tsx` established the jsdom hover-simulation pattern for Radix
  (`pointerenter` + `pointermove` + `.focus()`, then `findAllByText` — not `findByText`, because
  Radix duplicates tooltip text into a visually-hidden `<span role="tooltip">` a11y mirror) —
  reused as-is in `GlossaryTooltip.test.tsx` and `BarChart.test.tsx`.
- Fetch-once-per-app-load pattern already established by other dashboard hooks — applied to
  `useGlossary()` via a module-level `_glossaryPromise` singleton so every view sharing one
  glossary fetch, not one fetch per component instance.

## Design Decisions
- **Fetch-once, not per-view.** `useGlossary()` guards on a module-level promise; confirmed by
  grep that `fetchGlossary(` has exactly one call site in the whole `src/` tree (inside the hook
  itself), which proves single-fetch by construction rather than by runtime observation alone.
- **Graceful degradation at two layers.** `useGlossary()`'s `.then()` coerces any non-object
  `terms` payload to `{}`; `GlossaryTooltip` itself independently guards `term && glossary` before
  indexing. Needed because pre-existing tests in `TicketsView.test.tsx` use a blanket
  `mockResolvedValue` that returns the same body for every fetch call regardless of URL — without
  both guards, `/api/glossary` resolving to a tickets-shaped body (no `.terms` field) crashes
  `GlossaryTooltip` with `Cannot read properties of undefined`. Fixed at the component/hook level,
  not by rewriting those tests' mocks.
- **Chart tooltips extend, never nest.** `BarChart`/`GroupedBarChart` already had their own
  `Tooltip.Content` for the bar's label/value; a `descriptions` prop appends a second line inside
  the *same* content block rather than introducing a second nested `Tooltip.Root`.
- **Scope is deliberately narrower than "every string on screen."** Only fields whose values are
  a closed enum with a real 1:1 glossary term get wrapped: Tier, Layer, ticket `## Status`
  (workflow status), Priority, event `status` (ok/failed/blocked/skipped), gate-failure/reason-code
  bar labels, tier/type/priority/layer distribution bar labels, Slow Runs `final_status`. Two
  deliberate non-wraps, both re-confirmed in this investigation: ticket frontmatter `status`
  (`active`/`historical`/... — a different doc-lifecycle enum, not in the glossary registry's
  `GLOSSARY_CATEGORIES`) and Replay's `call.status`/`tailCall.status` (tool-call-level status, an
  unconfirmed/different vocabulary from event-status).

## Risks and Open Questions
None outstanding. The one open risk during implementation — a StatsView-level integration test
for BarChart hover inside the full StatsView tree flaking on Radix `data-state` under jsdom
(likely nested-Provider or async-glossary-fetch timing) — was resolved by moving the real
hover-content assertion into `BarChart.test.tsx` in isolation (5/5 passing) and keeping a lighter
wiring + graceful-degradation + anti-drift-source-guard test at the StatsView level instead of
chasing the jsdom timing quirk further.

## Anti-Drift Hazards
- `StatsView.test.tsx` includes `expect(STATS_VIEW_SOURCE).not.toMatch(/description:\s*['"]/)` —
  a source-guard test that fails the build the moment anyone hardcodes a literal description
  string into `StatsView.tsx` instead of sourcing it from `useGlossary()`.
- `GlossaryTooltip`'s two-layer graceful-degradation guard must never be simplified to a single
  layer — the pre-existing blanket-mock tests in `TicketsView.test.tsx` depend on both layers to
  avoid crashing.
