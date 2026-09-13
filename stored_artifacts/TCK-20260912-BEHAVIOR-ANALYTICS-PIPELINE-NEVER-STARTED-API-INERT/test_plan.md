# Test Plan — TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT

## New tests (`tests/api/test_inert_route_gating.py`, shared with the sibling ticket)

- `test_behavior_analytics_api_disabled_by_default`: default `RuntimeProfile`, real `TestClient`
  against real `create_v2_app()` — `GET /api/v1/behavior/events` returns FastAPI's own generic
  404 (`{"detail": "Not Found"}`), proving the route is genuinely not mounted.
- `test_behavior_analytics_api_reachable_when_enabled`: `enable_behavior_analytics_api=True` —
  same request returns 200 with an empty list, proving the gate controls registration, not the
  handler's own (unchanged) behavior.
- `test_gates_are_independent`: enabling this gate does not also enable the chronicle/campaigns
  gate.
- `test_unrelated_route_unaffected_by_default_gating`: `search.py` (explicitly left ungated) stays
  reachable regardless.

## Regression

- `tests/api/` full suite (153 passed) — confirms no existing test (including
  `test_phase27_behavior_query_api.py`, which calls handlers directly) regressed.
- `tests/unit/core/test_runtime_profile_contract.py` — confirms the new field doesn't break
  existing `RuntimeProfile` construction/immutability guarantees.
