---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261024-API-SERVER-CHARACTERIZATION-TESTS
artifact_type: plan
tags: [architecture, api-design, testing]
---

# Plan
Add `tests/api/test_server_http_surface_characterization.py` and the fixture `tests/fixtures/api_server_http_surface.json`. The test builds `create_v2_app` for two profiles (default; both optional routers on) and walks the routes with `tests/helpers/api_routes.py`. It records route order and metadata, flattened dependencies, the OpenAPI document, the middleware stack, and the UI, redirect, `/metrics` and CORS preflight responses. No edit under `src/`. Regeneration: `UPDATE_API_SURFACE_FIXTURE=1`.
