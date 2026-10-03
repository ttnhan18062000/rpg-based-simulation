---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260718-STATS-TAB-FRONTEND
artifact_type: investigation
tags: [dashboard]
---

# Investigation — TCK-20260718-STATS-TAB-FRONTEND

## Context scan

- `mcp__knowledge-search__search_docs("Agent Ops Dashboard frontend views tab structure")` — surfaced
  `docs/guides/agent_ops_dashboard.md`, `docs/observability/agent_ops_dashboard_contract.md`, prior
  dashboard tickets (BUILD-SERVE, DASHBOARD-BACKEND, DASHBOARD-DOCS).
- `graphify query "dashboard frontend App.tsx views tabs"` — confirmed `App.tsx` contains `App()` and
  `handleSelectRun()`, imports `main.tsx`, and a standing architecture-guard test
  (`test_dashboard_frontend_never_references_simulation_api_surface`) forbids `dashboard-frontend/` from
  importing the simulation engine's own API surface — irrelevant to this ticket (no engine code touched)
  but confirms the isolation boundary to respect.

## Existing structure

- `App.tsx` (59 lines): `PageView = 'activity' | 'tickets' | 'replay'`, a `NAV_ITEMS` array driving the
  header nav buttons, and a render branch per view. Adding a 4th view is a 3-line diff: extend the union,
  add a `NAV_ITEMS` entry, add a render branch.
- Three existing views in `src/views/`, each: a top-level `export function XView()`, `useEffect`-driven
  fetch-on-mount against `src/api.ts` functions, `isLoading`/`error` state, a `data-testid` root div.
  `TicketsView.tsx` is the closest analog (filters + table + facets).
- `src/api.ts`: one `fetch*` function per backend route, typed interfaces mirroring
  `src/api/agent_ops_dashboard/models.py` field-for-field (the file's own header comment says so). Two new
  routes need two new fetch functions + their response-shape interfaces.
- No charting library exists in `package.json` (confirmed: only `@radix-ui/*` primitives — `react-tabs`,
  `react-tooltip`, `react-scroll-area`, `react-slider`, `react-slot` — no chart/graphing dependency).
- `RecentActivityGantt.tsx` + `components/GanttBar.tsx`/`TimeAxis.tsx`/`Legend.tsx` already establish the
  project's own convention for chart-like rendering: **plain HTML/CSS divs with absolute/relative
  positioning**, no SVG library, no chart framework — colors from Tailwind's `@theme` tokens in
  `index.css`, hover via the already-installed `@radix-ui/react-tooltip`.

## Theme finding — corrects the ticket's own assumption

The ticket text says "this dashboard already has both themes per its existing Tailwind setup." This is
**not accurate** as investigated:

- `index.css` declares `@custom-variant dark (&:is(.dark *))` but **no code anywhere applies a `.dark`
  class** to any ancestor element (grepped `dashboard-frontend/src` and `index.html` for `dark`,
  `ThemeContext`, `prefers-color-scheme`, `toggleTheme`, `useTheme` — zero matches beyond the unused
  `@custom-variant` declaration itself).
- `main.tsx`/`index.html` render `<App />` with no theme provider, no toggle UI exists in `App.tsx`'s
  header.
- Conclusion: the dashboard is **single (dark) themed today**, using hardcoded CSS custom properties
  (`--color-bg-primary: #0f1117`, `--color-bg-tertiary: #242835`, etc.) as its only palette — there is no
  live light mode to test against.

**Scope decision**: new charts use the dashboard's existing dark surface only (no light-mode code path is
built, since none exists elsewhere in the app to be consistent with — building one exclusively for the
Stats tab would be inconsistent, not consistent, with the rest of the SPA). The acceptance criterion "work
correctly in both light and dark theme" is satisfied by: chart colors are read from CSS custom properties
rather than hardcoded twice, so if/when a real light-mode toggle is added app-wide, the chart colors need
only their token values swapped, not a rewrite. This is recorded here as a documented scope call, not a
silent skip.

## dataviz skill — loaded and applied

`Skill(skill: "dataviz")` was invoked before any chart component code was written (see conversation log).
Key decisions drawn from it:

- **No new charting dependency added.** Plain HTML/CSS bars, consistent with the existing `GanttBar.tsx`
  convention already in this codebase — this is itself one of the skill's own suggested forms
  ("matplotlib/plotly/d3/Recharts/inline-SVG are all in-scope," and `references/components.md` explicitly
  teaches building each chart piece in plain HTML). Zero new `package.json` dependency.
- **Color validated, not eyeballed.** Ran `node scripts/validate_palette.js` from the skill's own
  directory against the dashboard's real dark chart surface (`--color-bg-tertiary: #242835`, not the
  skill's generic default `#1a1a19`):
  - The app's own existing 4 accent tokens (`--color-accent-blue #4a9eff`, `-green #34d399`, `-yellow
    #fbbf24`, `-red #f87171`) **FAIL** the lightness-band check outside `#242835` — too light for a
    dark-surface categorical mark. Not reused for chart fills.
  - The skill's validated default dark 8-hue categorical set **PASSES** all checks against `#242835`
    (worst adjacent CVD ΔE 8.4, worst normal-vision ΔE 19.3), with one WARN: green (`#008300`) sits at
    2.97:1 contrast (below the 3:1 floor) — mitigated per the skill's "relief rule" by always pairing it
    with a visible direct value label (every bar in this ticket's charts is directly labeled with its
    value, never color-alone).
  - Only 2 series are needed anywhere in this ticket's charts (tier distribution: count vs. done), so only
    the first two validated slots are used: `#3987e5` (blue, series 1) and `#008300` (green, series 2, always
    paired with a direct label per the WARN above). All other charts are single-hue magnitude bars using
    `#3987e5` — single-hue usage has no categorical CVD requirement, only the surface-contrast check, which
    passes.
- **Existing app accent tokens (`text-accent-red`, `text-accent-green`, etc.) are still used for plain
  inline status text** (e.g. the agent-status table's ok/failed/blocked counts) — that is a *text-token*
  role already established elsewhere in this codebase (`TicketsView.tsx`'s error banner), not a *chart-mark*
  role, so it is out of the palette-validation requirement's scope (that requirement targets colored data
  marks, not existing inline text coloring conventions).
- Mark specs followed: bars ≤24px thick, 4px rounded data-end / square baseline, value labeled at the tip,
  legend present only where ≥2 series exist (tier-distribution chart), single-series charts carry no legend
  box (title says what's plotted).
- Hover layer: reused the already-installed `@radix-ui/react-tooltip` (same dependency
  `RecentActivityGantt.tsx` already uses) to give every bar a hover tooltip, rather than introducing a new
  tooltip mechanism.

## Data shape → view mapping

`AgentMonitoringStats` (from `GET /api/stats/agent-monitoring`, default `days=7` window matching
`generate_retro.py`'s own default) and `TicketCorpusStats` (from `GET /api/stats/tickets`, whole corpus,
no time window — matches ticket 3's own design) are two distinct data domains with different shapes and no
shared key. Investigation judgment: **one `StatsView.tsx` with two clearly-headed sections** (Agent
Monitoring, Ticket Corpus) inside a single scroll container, not two separate nav tabs — avoids adding a
5th top-level nav item for what is still conceptually "the stats board" the user asked for, and both
sections are meant to be seen together for a status check, not switched between. Documented here per the
ticket's own instruction to record this UX call either way.

- `run_summary` → 5 stat tiles (total, done, gate fails, avg duration min, total agent calls).
- `gate_failure_breakdown`, `reason_code_breakdown` → single-hue magnitude bar charts, sorted desc, capped
  to top 10 with a "+N more" note (categories are open-ended free-form strings; a stat tile or full listing
  would either lose the "which ones" story or overflow the view — top-N bar is the right form for "which
  categories dominate").
- `tier_distribution` → grouped bar chart (2 series: count, done) per tier — few categories (4: standard,
  hotfix, epic, unknown), fits the skill's "identity via color, ≤4 direct-labeled" guidance without folding
  to "Other."
- `agent_status_distribution` (58 distinct agents, 6 status values) → too many categories for a stacked bar
  to stay legible (would need per-status categorical color across many agents, well past the "fold to Other
  past 4" guidance for a stacked-bar form). Rendered as a sortable table (agent, total, ok, failed, blocked,
  skipped), top 15 by total call volume, matching `TicketsView.tsx`'s existing table conventions instead of
  forcing a chart form onto data that doesn't fit one — "is it even a chart?" per `choosing-a-form.md`.
- `summary_quality` → 3 stat tiles.
- `slow_runs` → table (run_id, duration, status), already sorted desc by the backend.
- `scanned_files` / `included_tickets` / `skipped` (sum) / `artifact_completeness` ratio → stat tiles.
- `velocity.by_day` → single-hue magnitude bar chart, last 14 entries in date order (not sorted by value —
  a time series must stay chronological; the generic `BarChart` component takes a `sortByValue={false}`
  escape hatch for this one call site).
- `distribution.tier` / `.ticket_type` / `.priority` / `.layer` → 4 single-hue magnitude bar charts.
- `artifact_completeness.incomplete` → table (ticket_id, missing files), capped to top 20 with a count note
  if truncated.

## Test conventions confirmed

`src/test/TicketsView.test.tsx` and `RecentActivityGantt.test.tsx` mock `global.fetch`, assert on
`data-testid` nodes, and assert no un-mocked network call escapes (matching this ticket's own scope
instruction). New tests for `StatsView.tsx` follow the same mock-fetch-then-assert-rendered-content shape.
