---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260718-STATS-TAB-FRONTEND
artifact_type: test_plan
tags: [dashboard]
---

# Test Plan — TCK-20260718-STATS-TAB-FRONTEND

## Normal flow
- `StatsView` mounts, fetches both endpoints, renders stat tiles with the mocked numeric values, renders
  bar-chart rows for gate-failure/reason-code/velocity/distribution data, renders the grouped tier chart
  with both series, renders the three tables with mocked rows.
- `App.tsx`: clicking the "Stats" nav button switches `currentView` to `'stats'` and unmounts the previously
  active view (mirrors the existing `App.test.tsx` pattern for the other three tabs, if present).

## Edge cases
- Both endpoints return the zero-corpus/zero-runs shape (empty dicts/lists, zero counts) — `BarChart`'s
  `emptyLabel` path renders instead of a crash or an empty div.
- `gate_failure_breakdown`/`agent_status_distribution` with more entries than the display cap — truncation
  note ("+N more") appears with the correct count, list of shown items is exactly `maxBars` long.
- `slow_runs`/`incomplete` arrays longer than their table cap — same truncation behavior.

## Failure modes
- One of the two `fetch` calls rejects (network error / non-OK status) — `StatsView` renders its error
  state, does not crash, and does not silently drop the other endpoint's already-successful data (or, if
  the chosen implementation fails both together via `Promise.all`, document that as the explicit tradeoff
  in Implementation Notes — decided during Implement, verified here).

## Regression-prone paths
- `BarChart`'s `sortByValue={false}` path (used only by the velocity chart) must preserve caller order, not
  silently re-sort — a broken flag here would show dates out of chronological order.
- The API-boundary test (`test_agent_ops_dashboard_api_boundary.py`) and its frontend counterpart
  (`test_agent_ops_dashboard_frontend_api_surface.py`) must keep passing unmodified — this ticket adds no
  new backend route and does not touch `dashboard-frontend`'s isolation from the simulation engine's own
  API surface.

## Existing tests to re-run (not just new ones)
- `dashboard-frontend`: `npm test` (all `src/test/*.test.tsx`) — full suite, since `App.tsx` is touched.
- `pytest tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -q`
  — confirms no backend/isolation regression from this frontend-only ticket.
