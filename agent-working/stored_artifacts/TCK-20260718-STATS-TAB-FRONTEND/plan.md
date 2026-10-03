---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260718-STATS-TAB-FRONTEND
artifact_type: plan
tags: [dashboard]
---

# Plan — TCK-20260718-STATS-TAB-FRONTEND

## Scope guard

In scope: a 4th "Stats" nav view in the existing Agent Ops Dashboard SPA, consuming the two already-shipped
backend endpoints, rendered with plain-HTML chart components (no new dependency), colors validated via the
`dataviz` skill. Out of scope: backend changes (both endpoints already exist and are tested), a light-mode
theme (none exists in this app — see investigation.md), polling/live-updates (fetch-once-per-mount, same as
`TicketsView.tsx`).

## Steps

1. **`src/lib/chartPalette.ts`** (new) — two validated hex constants (`CHART_SERIES_1` blue `#3987e5`,
   `CHART_SERIES_2` green `#008300`) with a comment recording the validator invocation and surface used.
2. **`src/components/BarChart.tsx`** (new) — generic single-hue horizontal magnitude bar chart. Props:
   `data: {label, value}[]`, `color`, `maxBars` (default 10), `sortByValue` (default true — set false for
   pre-ordered time-series callers), `emptyLabel`. Renders: 4px rounded data-end bars, value labeled at the
   tip, Radix `Tooltip` per bar (full label + value on hover), "+N more" note when truncated, an
   empty-state message when `data` is empty (covers both endpoints' zero-corpus / zero-runs edge case).
3. **`src/components/GroupedBarChart.tsx`** (new) — 2-series grouped bar chart for tier distribution (count
   vs. done). Props: `data: {label, series1, series2}[]`, `series1Label`, `series2Label`,
   `series1Color`/`series2Color` defaulting to the palette constants. Renders a legend (2 swatches + text
   tokens for the labels, never colored text) since ≥2 series are present.
4. **`src/components/StatTile.tsx`** (new) — `label` + `value` tile per `marks-and-anatomy.md`'s stat-tile
   contract (sentence-case label, semibold value, no delta/trend needed here — this is a point-in-time
   status board, not a period-over-period comparison view).
5. **`src/api.ts`** — add `AgentMonitoringStats`/`TicketCorpusStats` and their nested interfaces (mirroring
   `models.py` field-for-field, per the file's own existing convention comment), plus
   `fetchAgentMonitoringStats()` and `fetchTicketCorpusStats()` functions following the existing
   `fetchTickets`/`fetchRuns` pattern (build `URLSearchParams`, `fetch`, throw on non-OK, return parsed
   JSON).
6. **`src/views/StatsView.tsx`** (new) — fetch-on-mount both endpoints in parallel (`Promise.all`),
   `isLoading`/`error` state matching `TicketsView.tsx`'s pattern, `data-testid="stats-view"` root. Two
   `<section>`s ("Agent Monitoring", "Ticket Corpus") per investigation.md's data-mapping table: stat-tile
   rows, `BarChart`/`GroupedBarChart` instances, and two small tables (top agents by call volume, slow
   runs) built with the same `<table>`/`<td data-testid=...>` shape `TicketsView.tsx` already uses, plus a
   third table for incomplete artifacts.
7. **`src/App.tsx`** — extend `PageView` to `'activity' | 'tickets' | 'replay' | 'stats'`, add a
   `{ view: 'stats', label: 'Stats' }` entry to `NAV_ITEMS`, add `{currentView === 'stats' && <StatsView />}`
   render branch. 3-line diff, no other changes to this file.
8. **Tests** — `src/test/StatsView.test.tsx` (new): mock `fetch` for both endpoints, assert stat tiles /
   bar chart rows / tables render real mocked values, assert an error state renders on a failed fetch,
   assert loading state renders before resolution. `src/test/BarChart.test.tsx` and
   `GroupedBarChart.test.tsx` (new, small): empty-state, truncation ("+N more"), sort behavior. Extend
   `src/test/App.test.tsx` if it enumerates `NAV_ITEMS` or view branches (read the file first; only touch
   what the existing test already asserts against, don't invent new assertions there beyond the 4th tab's
   presence).
9. **No `package.json` changes** — no new dependency added (see investigation.md's dependency decision).
10. **Live verification** — kill any stale `dashboard-serve` process, confirm port 8420 free, `make
    dashboard-serve` (fresh build), drive the Stats tab in a headless browser: confirm both sections render
    real numbers (cross-check a couple against direct `curl` output), confirm zero console errors, confirm
    tooltips/hover work, confirm the tab is reachable from the nav.

## Acceptance-criteria map

| AC | Step |
|---|---|
| 4th "Stats" tab selectable from nav, same pattern as others | 7 |
| `Skill(skill: "dataviz")` invoked before chart code | done pre-Plan (see investigation.md) — Architecture-Verify checks the conversation record, not a file |
| View renders real data from both endpoints, verified live | 5, 6, 10 |
| Charts/tiles work in both light and dark theme | investigation.md's documented scope call — dark-only today, tokens ready for a future toggle |
| New tests cover fetching and rendering, mocking both endpoints | 8 |
| Zero console errors on open + interaction | 10 |
