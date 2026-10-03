---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL
date: 2026-07-18
tags: [observability]
---

# Test Plan — TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL

## Regression Surface (existing tests that must pass)

- `tests/tools/test_agent_ops_dashboard_ingest.py` (all, especially the
  pinned facets test).
- `tests/tools/test_agent_ops_dashboard_api.py`,
  `test_agent_ops_dashboard_api_boundary.py`,
  `test_agent_ops_dashboard_concurrency.py`,
  `test_agent_ops_dashboard_frontend_api_surface.py`,
  `test_agent_ops_dashboard_serve.py`.
- `dashboard-frontend/src/test/TicketsView.test.tsx` (all).

## New Tests Required (per AC)

1. Backend: canonical tiers/layers/priorities with zero corpus matches.
2. Backend: canonical tiers/layers/priorities unaffected by an active
   filter.
3. Frontend: proof that `FilterSelect`'s fallback is not triggered by the
   real (canonical) facets contract.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/tools/test_agent_ops_dashboard_serve.py -q
cd dashboard-frontend && npm run test -- --run
```

## Anti-Drift Test Guards

Live verification (curl + headless browser against a freshly-built,
freshly-launched server, stale process killed first) is the actual proof
this ticket's highest-priority AC requires — unit tests alone are
insufficient, per the ticket's own explicit instruction.
