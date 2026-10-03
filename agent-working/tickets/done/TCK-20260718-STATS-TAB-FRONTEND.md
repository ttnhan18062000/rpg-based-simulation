---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-STATS-TAB-FRONTEND
phase: done
date: 2026-07-18
tags: [dashboard]
---

# TCK-20260718-STATS-TAB-FRONTEND

## Title
New "Stats" tab in the Agent Ops Dashboard frontend, rendering agent-monitoring and ticket-corpus statistics

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add a 4th tab to the Agent Ops Dashboard SPA (alongside the existing Recent Activity / Tickets / Replay), fetching from the two new backend endpoints (TCK-20260718-AGENTOPS-STATS-API and TCK-20260718-TICKET-CORPUS-REPORT) and rendering their data as charts/stat tiles. This is the user-facing deliverable of the whole epic — the prior two tickets exist only to give this one real data.

**Hard requirement, not optional**: no chart library exists in `dashboard-frontend/package.json` today (confirmed: only `@radix-ui/*`, no charting dependency). Before writing any chart component code or choosing any color, load the `dataviz` skill (`Skill(skill: "dataviz")`) — its own trigger description explicitly covers "stat tile", "chart colors", "dashboard", "KPI row". It teaches a design-system-agnostic method (form heuristic, color formula, mark specs) and ships a validated default palette; it does not mandate a specific charting library (matplotlib/plotly/d3/Recharts/inline-SVG are all in-scope per its own description), so the library choice is still an implementation decision, but the visual design discipline is not skippable.

## Scope
- New `PageView` union member (`'stats'` or similar) in `App.tsx`, alongside `'activity' | 'tickets' | 'replay'`, plus a new `NAV_ITEMS` entry and render branch — mirrors the existing pattern exactly (see `App.tsx`'s current ~55-line structure).
- New `dashboard-frontend/src/views/StatsView.tsx` (or split into two sub-views if investigation judges the two data domains read better separated — a reasoned UX call, document it either way) fetching from both new stats endpoints and rendering their data.
- **Load the `dataviz` skill before any chart code or color choice** — this is a hard requirement, see Request Summary. Follow its guidance for chart type selection, the color formula/palette, and light/dark theming (this dashboard already has both themes per its existing Tailwind setup — new charts must respect that, not hardcode a single-theme palette).
- Add whatever charting dependency is chosen to `dashboard-frontend/package.json`, justified in Implementation Notes (why this library, not another).
- New frontend tests in `dashboard-frontend/src/test/` mirroring the existing views' test patterns (mock fetch responses, assert rendered content, assert no direct un-mocked network calls) — per this project's `TicketsView.test.tsx`/`RecentActivityGantt.test.tsx` established conventions.

## Out of Scope
- Building the backend endpoints themselves — those are the two prerequisite tickets' scope; this ticket only consumes them.
- Real-time/live-updating stats (polling) — fetch-once-per-view-load unless investigation finds a strong reason otherwise; document the decision either way, don't default to polling without justification.
- Adding frontend CI (lint/typecheck/vitest wired into any CI workflow) — out of scope per the dashboard's own origin idea doc, which already deferred this repo-wide gap.

## Acceptance Criteria
- [x] A 4th "Stats" tab is selectable from the dashboard's header nav, following the exact same pattern as the other three.
- [x] `Skill(skill: "dataviz")` was actually invoked before any chart component code was written — verified during Architecture-Verify/Review, not just claimed in Implementation Notes.
- [x] The view renders real data from both new backend endpoints (not mock/placeholder values) — verified live via `curl` + a headless browser against a freshly-built `make dashboard-serve` instance.
- [x] Charts/stat tiles work correctly in both light and dark theme. (Scope call: the app has no live light theme anywhere — see Implementation Notes — chart colors read from token constants so a future toggle needs no chart rewrite.)
- [x] New tests cover the view's data-fetching and rendering, mocking the two new endpoints.
- [x] Zero console errors when the Stats tab is opened and interacted with.

## Related Tickets
- TCK-20260718-AGENTOPS-STATS-API (dependency — must land first)
- TCK-20260718-TICKET-CORPUS-REPORT (dependency — must land first)
- TCK-20260718-AGENTOPS-STATS-BOARD-EPIC (parent epic)

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_stats_board.md
- docs/guides/agent_ops_dashboard.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- dashboard-frontend/src/App.tsx
- dashboard-frontend/src/views/
- dashboard-frontend/src/api.ts
- dashboard-frontend/package.json

## Assumptions / Open Questions
- Charting library choice deferred to implementation, guided by the `dataviz` skill.
- One unified Stats view vs. two sub-sections (agent-monitoring / ticket-corpus) is a UX call for this ticket's own investigation to make and document, not fixed here.

## Implementation Notes
- `Skill(skill: "dataviz")` was invoked before any chart component or color was written. Its palette
  validator (`scripts/validate_palette.js`) was run against this app's actual dark chart surface
  (`--color-bg-tertiary #242835`), not the skill's generic default — the app's own pre-existing
  `--color-accent-*` tokens FAILED the lightness-band check against that surface and were not reused for
  chart fills; the skill's validated default dark 8-hue set PASSED (first two slots used:
  `dashboard-frontend/src/lib/chartPalette.ts`).
- No new charting dependency added to `package.json`. Chart marks are plain HTML/CSS divs with inline
  `backgroundColor`, matching the convention `components/GanttBar.tsx` already established in this
  codebase; hover tooltips reuse the already-installed `@radix-ui/react-tooltip` (same dependency
  `RecentActivityGantt.tsx` uses), so no new interaction mechanism was introduced either.
- Investigation corrected a false assumption in this ticket's own Request Summary/Acceptance Criteria:
  the dashboard has no live light theme today. `index.css` declares `@custom-variant dark (&:is(.dark *))`
  but nothing anywhere applies a `.dark` class, and there is no `ThemeContext`/`prefers-color-scheme`
  handling in the app. Building a real light-mode chart path exclusively for this one tab would be
  inconsistent with the rest of the SPA, not consistent with it — the light/dark AC is satisfied by
  reading chart colors from named constants rather than hardcoding, so a future app-wide theme toggle
  needs only its token values swapped, not a chart rewrite. Documented in
  `stored_artifacts/TCK-20260718-STATS-TAB-FRONTEND/investigation.md`.
- One unified `StatsView.tsx` with two headed `<section>`s (Agent Monitoring, Ticket Corpus) was chosen
  over two separate nav tabs — both data domains are meant to be read together for a status check, and a
  5th top-level nav item felt like unnecessary navigation depth for what the user asked for as one board.
- `agent_status_distribution` (58 distinct agents, 6 status values) was rendered as a sortable table
  (top 15 by call volume), not a stacked bar chart — a per-agent multi-status stacked bar at that
  cardinality has no legible categorical-color form per the `dataviz` skill's own "fold to Other past 4"
  guidance; a table is the right form for data that doesn't fit a chart.
- `gate_failure_breakdown`/`reason_code_breakdown`/distribution charts are capped to the top 10 entries by
  value with a "+N more" note, since these are open-vocabulary free-form category names, not a small fixed
  enum.
- Both `fetch()` calls run via `Promise.all` — either endpoint failing surfaces the shared error state (no
  partial-render of just one domain). Acceptable for this read-only ops tool: a partial-data view without
  a visible reason it's partial would be more misleading than a clear "failed to load" state.

## Test Summary
- New: `dashboard-frontend/src/test/StatsView.test.tsx` (loading state, real-data rendering across both
  endpoints, rounded artifact-completeness percentage, fetch-failure error state, zero-corpus/zero-runs
  empty-state), `BarChart.test.tsx`, `GroupedBarChart.test.tsx` (empty state, sort/truncation,
  `sortByValue={false}` chronological-order preservation, legend). Extended `App.test.tsx` with a Stats-tab
  navigation test.
- `npm test -- --run` (dashboard-frontend): 71/71 passing (was 58 before this ticket).
- `npm run build` (`tsc -b && vite build`): clean, no type errors.
- `python3 -m pytest tests/tools/test_agent_ops_dashboard_api_boundary.py
  tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -q`: 6/6 passing (regression guard — this
  ticket added no backend route and doesn't touch the frontend/simulation-engine isolation boundary).
- `tools/gate_checks/architecture_reviewer_static.py::run_architecture_checks()` over all 11
  changed/added files: zero findings.
- Live verification: killed any stale `dashboard-serve` process, confirmed port 8420 free, ran a fresh
  `make dashboard-serve`, drove the Stats tab with headless Chromium (Playwright, via the npx cache path).
  Rendered `Total runs` (66) and `Scanned files` (1,178) matched direct `curl /api/stats/agent-monitoring`
  and `/api/stats/tickets` output exactly; artifact completeness rendered as the correctly-rounded 64%
  (623/970); 49 bar-chart rows + 4 grouped tier rows + 15 top-agent rows rendered; a bar's hover tooltip
  appeared on hover; zero browser console errors were captured across the whole run.

## Files Changed
- `dashboard-frontend/src/App.tsx` (extended `PageView`, `NAV_ITEMS`, render branch)
- `dashboard-frontend/src/api.ts` (new stats types + `fetchAgentMonitoringStats`/`fetchTicketCorpusStats`)
- `dashboard-frontend/src/views/StatsView.tsx` (new)
- `dashboard-frontend/src/components/BarChart.tsx` (new)
- `dashboard-frontend/src/components/GroupedBarChart.tsx` (new)
- `dashboard-frontend/src/components/StatTile.tsx` (new)
- `dashboard-frontend/src/lib/chartPalette.ts` (new)
- `dashboard-frontend/src/test/StatsView.test.tsx` (new)
- `dashboard-frontend/src/test/BarChart.test.tsx` (new)
- `dashboard-frontend/src/test/GroupedBarChart.test.tsx` (new)
- `dashboard-frontend/src/test/App.test.tsx` (extended)
- `docs/parity_ledger/infrastructure.yaml` (extended INFRA-275)

## Completion Summary
Added a 4th "Stats" tab to the Agent Ops Dashboard SPA, consuming the two backend endpoints the prior two
tickets in this epic built. No new npm dependency; chart marks follow the existing plain-HTML convention
and were color-validated via the `dataviz` skill against the app's real dark surface. Corrected a false
"both themes exist" assumption in the ticket's own text during investigation — documented as a scope call
rather than silently built around. Live-verified end-to-end with a headless browser against real repo
data, zero console errors.
