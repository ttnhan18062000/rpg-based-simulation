---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261024-API-SERVER-CHARACTERIZATION-TESTS
artifact_type: investigation
tags: [architecture, api-design, testing]
---

# Investigation
- `create_v2_app` has exactly two conditional routers: `behavior` (`enable_behavior_analytics_api`) and `campaigns` + `chronicle` (`enable_campaign_chronicle_api`). Both branches are pinned; no conditional router is left unpinned.
- Default profile: 63 routes; both flags on: 74. The UI page is 92,747 bytes, sha256 081c122a...5f91b (requested with `Accept-Encoding: identity`).
- `/metrics` without a key is 401 (admission chains `require_api_key`); the SURVIVAL 429 branch is covered by `test_admission_control.py` and is not repeated here.
- Nothing in the snapshot needed a fix.

## CI finding (PR #731, first push fea1c1da0)
The shared venv carries fastapi 0.136.1 / starlette 1.0.0, while uv.lock and CI run 0.143.5 / 1.9.0. The first fixture was recorded on the older pair, so CI failed the snapshot (CORS preflight allow-methods gained `QUERY`; route and OpenAPI details differ). Rebuilt with the locked pair (`pip install --target` overlay on PYTHONPATH), recorded from the **base** src (`a8b13680b`), and the refactored src passes it unchanged: the move is behaviour-identical. Two older tests walked `app.routes` flat and, on the locked starlette, no longer saw routes held by `include_router` nodes; they now use `tests/helpers/api_routes.py`.
