---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-AGENTOPS-STATS-API
artifact_type: test_plan
tags: []
---

# Test Plan — TCK-20260718-AGENTOPS-STATS-API

## Regression Surface (existing tests that must pass)

- `tests/tools/test_agent_ops_dashboard_ingest.py` — full suite, unaffected by additive changes.
- `tests/tools/test_agent_ops_dashboard_api_boundary.py` — must still pass; extend if it
  enumerates routes/models exhaustively (check before assuming additive-only is sufficient).
- `tests/tools/test_generate_retro.py` — unaffected (this ticket only imports/calls
  `compute_retro_metrics()`, never modifies `generate_retro.py`).

## New Tests Required (per AC)

1. New Pydantic model(s) in `models.py` — a construction test confirming the model accepts
   `compute_retro_metrics()`'s actual return shape.
2. New route test(s) in a new or extended `tests/tools/test_agent_ops_dashboard_*.py` file:
   happy path (real fixture data returns 200 + correct shape), period-selection variants
   (`?days=N`, `?all=true`, `?week=...`), empty-data edge case (no runs/events at all — must not
   500), bad-input validation (e.g. conflicting `days`+`all`+`week` params, or invalid `week`
   format — proper `HTTPException`, not an unhandled exception).
3. API-boundary test extension (if `test_agent_ops_dashboard_api_boundary.py` enumerates routes)
   confirming the new route also returns a typed model, never a raw dict.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py -q
```

## Anti-Drift Test Guards

- Assert the new route's handler never reads `agent-monitoring/*.jsonl` directly — only via
  `DashboardCache`.
- Assert `compute_retro_metrics()` is imported, not copy-pasted, into `ingest.py` (source-text
  guard, mirroring this project's existing anti-drift test conventions).
