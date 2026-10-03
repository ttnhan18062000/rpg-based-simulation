---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-GLOSSARY-API
artifact_type: test_plan
tags: [dashboard, observability, api-design]
---

# Test Plan — TCK-20260718-GLOSSARY-API

## Regression Surface
`tests/tools/test_agent_ops_dashboard_api_boundary.py::test_all_declared_routes_present` (pinned
route-set assertion, updated in place) and `test_typed_response_models_not_dict` (generic,
automatically covers the new route with no change needed).

## New Tests Required
`tests/tools/test_agent_ops_dashboard_glossary.py`:
- Merge happy path (glossary term + layer term both present, correct category/description each).
- Layer note reused live (editing the layer registry's note changes the next `get_glossary()`
  call's output — proves no duplication/staleness).
- Empty-note layer skipped (not present in output at all, not present-with-blank-description).
- Empty registries → `terms == {}`, no crash.
- Route-level: 200 status, correct typed JSON shape via `TestClient`.
- Route signature declares `GlossaryResponse` return type (API-boundary discipline check).
- Real, un-overridden repo registries: `DONE`/`economy` both present with correct categories,
  `len(terms) >= 35`.

## Scoped Pytest Commands
```
python3 -m pytest tests/tools/test_agent_ops_dashboard_glossary.py tests/tools/test_agent_ops_dashboard_api_boundary.py -q
```

## Live Verification (required, not optional — per this session's established discipline)
1. Kill any stale `dashboard-serve` process, confirm port 8420 free.
2. `make dashboard-serve`, wait for `curl -sf http://localhost:8420` to succeed.
3. `curl -s http://localhost:8420/api/glossary` — confirm real term count (54 = 35 glossary +
   19 layers) and spot-check `DONE`/`economy` entries.

## Anti-Drift Test Guards
`test_glossary_reuses_layer_note_never_duplicates_description` — directly proves the "merge at
read time, not copy" design decision holds under a live edit, not just a static fixture.
