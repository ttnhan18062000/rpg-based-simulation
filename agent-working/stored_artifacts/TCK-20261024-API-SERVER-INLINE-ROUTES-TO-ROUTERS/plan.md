---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261024-API-SERVER-INLINE-ROUTES-TO-ROUTERS
artifact_type: plan
tags: [architecture, api-design, refactor]
---

# Plan
Grouping keeps the original registration order, so a router is a run of adjacent inline routes (a route moved across another would change the pinned order). New modules in `src/api/routes/`:
1. `engine_probes.py`: `/metrics`, `/health` (route-level dependencies: they differ).
2. `live_observability.py`: live status, snapshot, entity inspection.
3. `engine_state.py`: state, inspect, entities, entity lookup.
4. `engine_control.py`: pause, resume, test/publish_event.
5. `live_health.py`: live health, stream-health.
6. `run_reports.py`: the run report.
Names avoid the empty `state.py`, `control.py` and `health.py`. `create_v2_app` keeps the middleware, lifespan and a private `_register_routers` that holds the `include_router` calls. Function-local imports move to module top: no cycle (lint-imports 17 kept); no `PLC0415` noqa was needed. Endpoint docstrings and return annotations stay as they were, since both feed the pinned OpenAPI document; where a ruff rule asks for one, a `noqa` with that reason.
Kept as is: `BLE001` x2 and `e3-silent-except` in the lifespan (a behaviour-identical fix does not exist: they swallow errors on purpose), the `set_quality_persistence` mypy row, and `n4-version-marker-name`.
