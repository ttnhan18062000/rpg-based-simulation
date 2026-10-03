---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND
artifact_type: plan
tags: [dashboard, observability, api-design]
---

# Implementation Plan — TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND

## Summary
Fetch `/api/glossary` once per app load and wire hover tooltips onto every closed-enum label
across `TicketsView`, `ReplayTimelineView`, and `StatsView` (cell text and chart bars), sourcing
all description text from the backend — zero hardcoded strings in the frontend.

## Steps

### Step 1 — `api.ts`: `GlossaryEntry`/`GlossaryTerms` types, `fetchGlossary()`, and
`useGlossary()` hook with a module-level `_glossaryPromise` singleton (fetch-once guard) and
defensive `.then()` coercion of any non-object payload to `{}`.

### Step 2 — `components/GlossaryTooltip.tsx` (new): `{term, glossary, children}` — renders
`children` unwrapped when `term` is null or no matching entry exists; otherwise wraps in
`Tooltip.Root`/`Tooltip.Trigger`/`Tooltip.Content` showing `entry.description`.

### Step 3 — `views/TicketsView.tsx`: wrap Tier/Layer/workflow-status/Priority cells in
`GlossaryTooltip`; add outer `Tooltip.Provider`. Do not wrap ticket frontmatter `status`.

### Step 4 — `views/ReplayTimelineView.tsx`: wrap event `status` text in `GlossaryTooltip`; add
outer `Tooltip.Provider`. Do not wrap `call.status`/`tailCall.status`.

### Step 5 — `components/BarChart.tsx` / `GroupedBarChart.tsx`: add optional
`descriptions?: Record<string, string>` prop; when a label matches, append a second line inside
the existing `Tooltip.Content` (no second nested `Tooltip.Root`).

### Step 6 — `views/StatsView.tsx`: `useGlossary()` + `glossaryDescriptions()` helper mapping
`{term: description}`; pass `descriptions` into all 5 chart usages; wrap Slow Runs `final_status`
cell in `GlossaryTooltip`; add outer `Tooltip.Provider`.

### Step 7 — Tests: `GlossaryTooltip.test.tsx` (new, 5 tests — plain render on null/no-match/empty
glossary, hoverable wrap + real hover text on match). `BarChart.test.tsx` (+2 tests — description
appended on match, unchanged when no match). `StatsView.test.tsx` (+3 tests — wiring-confirmation,
graceful degradation, anti-drift source guard) with `mockFetch` extended for a `glossary` param.

### Step 8 — Scope check: read `GanttBar.tsx`/`Legend.tsx` to confirm no raw enum text is
rendered there (only `run.run_id` and hand-written bucket prose) — no code change, document the
exclusion in investigation.md.

### Step 9 — Live verification: kill any stale `dashboard-serve` process, confirm port 8420 free,
rebuild fresh, drive real hover interactions via headless Chromium on Tickets (Layer/status/
priority cells) and Stats (bar row, Slow Runs status cell) — confirm real backend text appears,
zero console errors.

## Scope Guards
- No hardcoded description strings anywhere in `dashboard-frontend/src/` — enforced by
  `StatsView.test.tsx`'s source-string anti-drift guard.
- No second fetch call site for `/api/glossary` outside `useGlossary()`.
- Do not wrap ticket frontmatter `status` or Replay's `call.status`/`tailCall.status` — different,
  unconfirmed enum domains.
- Do not touch `GanttBar.tsx`/`Legend.tsx` — confirmed no raw enum text rendered there.

## Dependency Map
Depends on `TCK-20260718-GLOSSARY-API` (fetches its endpoint). Blocks
`TCK-20260718-GLOSSARY-DOCS-UPDATE` (docs describe the shipped tooltip behavior).

## Acceptance Criteria Map
- AC "Tier/Layer/Status/Priority cells show real backend descriptions on hover" → Steps 3, 7, 9.
- AC "Event status and chart bar labels show real backend descriptions on hover" → Steps 4-6, 7, 9.
- AC "Zero hardcoded description strings in frontend" → Step 7's anti-drift guard.
- AC "Glossary fetched exactly once per app load" → Step 1's singleton guard, confirmed by grep.
- AC "Deliberate Gantt/Legend exclusion documented, not silently skipped" → Step 8.

## Anti-Drift Notes
`STATS_VIEW_SOURCE` regex guard in `StatsView.test.tsx` is the durable mechanism preventing
future hardcoded description strings from silently reappearing in this view.
