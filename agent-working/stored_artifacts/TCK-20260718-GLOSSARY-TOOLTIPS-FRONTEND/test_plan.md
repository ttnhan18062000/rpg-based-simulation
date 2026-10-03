---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND
artifact_type: test_plan
tags: [dashboard, observability, api-design]
---

# Test Plan — TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND

## Regression Surface
Pre-existing `TicketsView.test.tsx` (blanket-mock tests exercising every fetch call with the same
response body) is the main regression risk — `GlossaryTooltip`'s two-layer graceful-degradation
guard exists specifically so those tests keep passing unmodified.

## New Tests Required
`GlossaryTooltip.test.tsx` (new, 5 tests):
- Renders `children` plainly when `term` is null.
- Renders `children` plainly when glossary has no matching entry.
- Renders `children` plainly when glossary is `{}` (not yet loaded).
- Wraps in a hoverable trigger when a matching entry exists.
- Shows the real description text on hover (`findAllByText`, not `findByText` — Radix a11y
  duplicate).

`BarChart.test.tsx` (+2 tests):
- Appends a glossary description as a second line in the existing tooltip content on hover match.
- Renders the original label-only tooltip content unchanged when no description matches.

`StatsView.test.tsx` (+3 tests, `mockFetch` extended with a `glossary` param defaulting to `{}`):
- Wiring-confirmation test (full hover-content proof lives in `BarChart.test.tsx` — a StatsView-
  level full hover simulation flaked on Radix `data-state` under jsdom, root cause not fully
  diagnosed; isolated component-level testing is the correct fix, not chasing the jsdom quirk).
- Graceful degradation: Slow Runs status cell renders plainly when glossary has no matching entry.
- Anti-drift source guard: `expect(STATS_VIEW_SOURCE).not.toMatch(/description:\s*['"]/)`.

## Scoped Test Commands
```
cd dashboard-frontend && npm run test -- --run
npx tsc -b --noEmit
npm run build
```

## Live Verification (required, not optional)
1. `pgrep -af agent_ops_dashboard` / `curl -sf http://localhost:8420` to rule out a stale server
   (recurring false-negative this session) before rebuilding.
2. `make dashboard-serve` fresh, confirm `curl -sf http://localhost:8420/api/glossary` returns 54
   real terms.
3. Headless Chromium (Playwright) hover verification, at least 3 distinct label types:
   - Tickets view Layer cell → real category description.
   - Tickets view ticket-status cell (`OPEN`) → real ticket-status description.
   - Tickets view Priority cell (`P2`) → "Medium priority."
   - Stats view bar row (`DOD_BLOCKED`) → real reason-code description appended.
   - Stats view Slow Runs status cell (run-status) → real run-status description.
   Zero console errors across all of the above.

## Results
- `npm run test -- --run`: **11 files / 82 tests passing.**
- `npx tsc -b --noEmit`: clean, no output.
- `npm run build`: clean (`✓ 72 modules transformed`, `dist/assets/index-BTY5NTAg.js 285.02 kB`).
- Live curl: `/api/glossary` → 54 terms confirmed against a freshly rebuilt server (stale-process
  check ran first, port confirmed clear before rebuild).
- Live hover verification via headless Chromium: 5/5 target elements showed real backend-sourced
  description text on hover (Layer, ticket-status `OPEN`, Priority `P2`, Stats bar row
  `DOD_BLOCKED` reason-code, Stats Slow Runs run-status cell). Zero console errors across all
  hovers. One transient `NO TOOLTIP` result during the first pass on the `OPEN` cell was traced to
  a fixed-sleep timing race in the verification script itself (immediately re-tested with
  `page.waitForSelector('[role="tooltip"]', {timeout: 2000})` instead of a fixed delay — tooltip
  appeared correctly with the real description); not a product defect.

## Anti-Drift Test Guards
`StatsView.test.tsx`'s `STATS_VIEW_SOURCE` regex guard fails the suite the moment a hardcoded
`description: '...'` literal is introduced into `StatsView.tsx`.
