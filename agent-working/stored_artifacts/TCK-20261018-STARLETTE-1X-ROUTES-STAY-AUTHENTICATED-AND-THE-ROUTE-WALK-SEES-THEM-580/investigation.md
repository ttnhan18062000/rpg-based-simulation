# Investigation: starlette 1.x (#580) and route authentication

Stack under test: starlette 1.8.0 + fastapi 0.143.5 (+ opentelemetry-api 1.45.1, fastapi's new dependency) against the repo's 0.52.1 / 0.128.4. The shared .venv was not touched; the new stack was an overlay dir (`PYTHONPATH=/mnt/data/overlay-starlette1`), and uv.lock was re-resolved with `uv lock --upgrade-package starlette --upgrade-package fastapi` (only fastapi, starlette, opentelemetry-api change). fastapi 0.128.4 requires `starlette<1.0.0`, so fastapi has to move with it.

## Finding 1 (differs from the brief): runtime auth is NOT broken by 1.x
Bare upgrade, no code change, probe `auth_probe2.py` with a configured key:
- `/api/v1/ws`, `/api/v1/ws/observe`, `/api/v1/ws/observability/events` without a key: rejected, close code 1008 (same as 0.52.1).
- the same 3 with a key: accepted past auth (stops at `get_engine_manager`, as on 0.52.1).
- `GET /api/v1/state` without a key: 401.
So no request becomes reachable. What 1.x breaks is route *introspection*.

## Finding 2: what 1.x changes (and what "hides the ws auth")
- `app.routes` goes from 62 flat routes to 34 top-level nodes; each `include_router` call is one `_IncludedRouter` (no `.path`). `[r.path for r in app.routes]` raises AttributeError.
- The 62 effective routes are behind `_IncludedRouter.effective_candidates()` (fastapi routing.py `_IncludedRouter`, a private API).
- A websocket route's effective context (`_EffectiveRouteContext`) has `path == ""` and `dependant is None`; its path and its `Dependant` (with `require_api_key_ws`, `require_admission_ws`) sit on `.starlette_route`. A walker that reads `route.dependant` sees no auth on any ws route.
Two existing tests broke on the bare upgrade: `test_api_key_auth.py::test_only_dashboard_and_websocket_routes_use_weaker_auth_channel` and `test_scenario_runtime_api.py::test_route_registered_in_server`.

## Red -> green record
1. New test, bare-upgrade walker (what a naive `app.routes` walk leaves; walker line replaced by `candidates = None`), stack 1.8.0:
   `test_walk_finds_every_http_route_the_openapi_document_lists` FAILS: "routes the walk cannot see: [('GET','/api/v1/economy/health'), ('GET','/api/v1/manifest'), ('GET','/api/v1/map'), ...]" (every included route).
2. Final walker (`tests/helpers/api_routes.py`): both new tests pass on 0.52.1 and on 1.8.0.
3. Mutation check on 1.8.0: removing the `dependencies=` from the `history` and `stream` `include_router` calls makes `test_every_registered_route_rejects_an_unauthenticated_caller` fail; restored afterwards.
4. Public routes are pinned in the test: `/health`, `/openapi.json`, `/docs`, `/docs/oauth2-redirect`, `/redoc`. `/health` returned 500 (engine manager not initialised) rather than 401 in the unauthenticated walk: it is a public liveness route, not an auth gap.

## Proof
- tests/api (not slow) on 1.8.0: 166 passed. tests/unit/api on 1.8.0: 63 passed. Both dirs on 0.52.1: 229 passed.
- Before the test fixes, 1.8.0 had exactly the 2 failures above.
- lint-imports: 17 kept, 0 broken.

## Addendum: rebased onto the uv group branch (rpg-deps-uv-redis 31328d709), proof on the synced stack
- B's `tests/api/route_table.py::flat_routes` is removed; `test_api_key_auth.py` and `test_scenario_runtime_api.py` use `tests/helpers/api_routes.py` (the one helper; it also covers ws and has the OpenAPI cross-check).
- uv.lock = B's lock + `uv lock --upgrade-package starlette --upgrade-package fastapi==0.143.5`. Package diff vs B's lock: fastapi 0.143.0 -> 0.143.5, starlette 0.52.1 -> 1.8.0, nothing else (opentelemetry-api is already in B's lock). A bare `--upgrade-package fastapi` resolves 0.144.0, which was not tested here.
- Proof on `uv sync --locked` (starlette 1.8.0 / fastapi 0.143.5; the overlay is no longer used): all-routes auth test + coverage test 2 passed; tests/api + tests/unit/api (not slow) 229 passed; lint-imports 17 kept, 0 broken.
