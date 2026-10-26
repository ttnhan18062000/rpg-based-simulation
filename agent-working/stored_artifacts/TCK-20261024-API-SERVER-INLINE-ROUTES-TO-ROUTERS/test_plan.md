---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261024-API-SERVER-INLINE-ROUTES-TO-ROUTERS
artifact_type: test_plan
tags: [architecture, api-design, refactor]
---

# Test plan
- Ticket 1 snapshot test passes with its fixture byte-unchanged since `a8b13680b` (route order, OpenAPI, middleware, UI sha256, `/metrics`, CORS).
- `lint-imports`: 17 kept, 0 broken. `python -m codebase.health check`: 0 new, 0 worse; every `server.py` row shrank or went (module-length, function-length x2, cognitive-complexity, ANN202, C901, D100, F401, I001, PLC0415, PLR0915 gone; BLE001 3 to 2).
- mypy: no new error. `tests/api`, the read-model guard, `tests/codebase`, `tests/static`, `tests/observability/test_metrics_export.py`, `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`: 834 passed.
