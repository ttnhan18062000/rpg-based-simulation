---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260823-HTTP-API-KEY-AUTH
artifact_type: test_plan
tags: [architecture, security, api-design]
---

# Test Plan — TCK-20260823-HTTP-API-KEY-AUTH

## Regression Surface

Confirmed by grepping `tests/` for `create_v2_app(` — only 4 files anywhere in the suite actually
build the full `create_v2_app()`-wired app; all other `tests/api/*.py` files invoke route handlers
directly or build their own bare single-router `FastAPI()` app and are **not** in the regression
surface for a `server.py`/`include_router()`-level auth dependency.

**Integration (in-process `TestClient(create_v2_app(...))`) — must keep passing, with auth-aware
updates where noted:**
- `tests/api/test_cors_config.py` — both tests hit `/health` with no API key. Must stay green
  unmodified if `/health` is exempted per this ticket's recommendation (it exercises CORS headers,
  not auth) — confirms the exemption decision is load-bearing for an existing green test, not just
  a nice-to-have.
- `tests/api/test_health_liveness.py` — hits `/health` with no key. Same as above: must stay green
  unmodified under the `/health`-exempt recommendation.
- `tests/api/test_scenario_runtime_api.py` — its `client` fixture (`RuntimeProfile(name="test", ...)`
  + `create_v2_app`) drives ~14 assertions against `/api/v1/scenarios/...` (the `scenarios`
  sub-router). This router is **not** exempt under the recommended list, so every call in this file
  needs a valid key attached once auth lands — cheapest fix is adding a default `headers=` dict to
  the `TestClient(...)` construction in the fixture (one line) rather than touching all ~14
  `client.get`/`client.post` call sites.
- `tests/observability/test_metrics_export.py::test_metrics_endpoint_direct` — calls the `/metrics`
  route's endpoint function directly (`await metrics_endpoint(manager)`), bypassing FastAPI's
  dependency-injection/HTTP layer entirely. **Unaffected** by adding `Depends()`-based auth to the
  route decorator, since the auth dependency is never invoked outside a real request. No change
  needed.
- `tests/observability/test_metrics_export.py::test_metrics_endpoint_integration` — launches a real
  `python3 -m src serve` subprocess and scrapes `/metrics` over HTTP with `requests.get(...)`, no
  key. `/metrics` is recommended non-exempt, so this test needs (a) the subprocess env seeded with a
  valid test key (`RPG_API_KEY_HASHES=...` or whatever field name Plan finalizes) and (b) the
  `requests.get()` call updated to send it. This is the one test that end-to-end-validates the
  CLI→env→`ConfigLoader`→`create_v2_app` chain for the new field — do not let it silently start
  failing with 401 and get treated as flaky.
- `tests/observability/test_metrics_export.py::test_prometheus_metrics_registry_and_structure`,
  `test_prometheus_hard_law_violation_metrics_export`, `test_multiple_registries_prevent_collision`
  — construct `V2EngineManager` directly, never touch `create_v2_app`/HTTP at all. Unaffected.

**Unit / direct-handler tests — confirmed unaffected, listed for completeness of the "did we scope
correctly" check, not because they need changes:**
- `tests/api/test_decision_api.py`, `test_campaign_history_api.py`, `test_chronicle_api.py`,
  `test_cognition_history_api.py`, `test_historical_event_search_api.py`,
  `test_live_entity_inspection.py`, `test_live_health_api.py`, `test_live_observability_status.py`,
  `test_observability_websocket.py`, `test_paged_logic.py`, `test_phase27_behavior_query_api.py`,
  `test_rest_parity.py`, `test_ws_protocol.py` — all invoke route logic directly or via bare
  test-local `FastAPI()` apps, not `create_v2_app()`. Run once after implementation as a sanity
  check that this scoping assumption held, but no code change to these files is expected.

## New Tests Required

Per acceptance criteria, following `tests/api/test_cors_config.py`'s established pattern
(`TestClient(create_v2_app(PROD_DEFAULT))`, real response status/headers asserted, no subprocess) —
new file `tests/api/test_api_key_auth.py`:

- **`test_missing_api_key_returns_401_on_protected_route`**
  Category: integration. Verifies a request to a non-exempt route (e.g. `/api/v1/state` or
  `/api/v1/entities`) with no `X-API-Key`-equivalent header returns 401, not a pass-through 200 and
  not a 500. Lives in `tests/api/test_api_key_auth.py`.
- **`test_invalid_api_key_returns_401_on_protected_route`**
  Category: integration. Same route, header present but value not in the configured key set — 401.
  Distinguishes "wrong key" from "no key" as separate assertions since both are separately named in
  the ticket's acceptance criteria.
- **`test_malformed_api_key_header_returns_401_not_500`**
  Category: integration/edge case. Empty-string header value, and a header value containing
  non-ASCII/control characters — must not raise an uncaught exception inside the comparison path
  (e.g. `hmac.compare_digest` on mismatched-length or wrong-type input) and must not surface as a
  500. Directly targets the acceptance criterion "not a 500 or an unauthenticated pass-through."
- **`test_valid_api_key_allows_request_through`**
  Category: integration. Valid key (seeded via the profile Plan defines, e.g.
  `RuntimeProfile(api_key_hashes=...)`) on a protected route returns the route's normal 200/expected
  body, proving the happy path isn't accidentally broken by adding the dependency.
- **`test_health_exempt_from_auth`**
  Category: integration. `/health` with no key still returns 200 — locks in the exemption decision
  as a regression guard, not just an implicit side effect of the CORS/liveness tests still passing.
- **`test_metrics_requires_auth`**
  Category: integration. `/metrics` with no key returns 401 — locks in the "metrics is NOT exempt"
  recommendation as an explicit, intentional assertion (guards against a future implementer
  reflexively treating `/metrics` as infra-only and silently exempting it).
- **`test_control_mutation_routes_require_auth`**
  Category: integration. `/api/v1/control/pause` and `/api/v1/control/resume` (POST) both return 401
  with no key — the two highest-consequence unauthenticated writes named in the ticket's own Request
  Summary get an explicit, named regression guard rather than being covered only incidentally by a
  generic "protected routes" test.
- **`test_key_comparison_is_constant_time`**
  Category: architecture guard. Asserts the comparison implementation calls
  `hmac.compare_digest` (e.g. via `inspect`/monkeypatch spy on `hmac.compare_digest`, or a direct
  unit test on the comparison function asserting it is not a bare `==`) rather than testing timing
  directly (timing-based tests are flaky) — verifies the *mechanism*, matching the acceptance
  criterion's explicit call-out of `hmac.compare_digest` over `==`. Lives in
  `tests/api/test_api_key_auth.py` or a narrower `tests/unit/api/test_auth.py` if Plan creates a
  dedicated unit-test tier for the new module.
- **`test_keys_never_stored_or_compared_as_plaintext`**
  Category: unit / architecture guard. Given a raw test key, asserts the stored/compared
  representation is a hash (e.g. `len() == 64` and matches `hashlib.sha256` hex-digest shape, or
  asserts the raw key string never appears as a substring of the loaded config's in-memory
  representation) — guards the "hashed-at-rest, never plaintext" acceptance criterion at the
  representation level, not just behaviorally.
- **`test_config_loader_env_var_seeds_api_keys`**
  Category: integration. Sets the env var Plan defines (e.g. `RPG_API_KEY_HASHES`), calls
  `ConfigLoader.load_profile(...)`, and asserts the resulting `RuntimeProfile` carries the value and
  that a `TestClient(create_v2_app(profile))` request using the corresponding raw key succeeds —
  validates the "minimal operator-provisioning path" acceptance criterion end-to-end, and
  specifically exercises the env-var-loop code path this investigation flagged as type-fragile
  (must not raise `TypeError`).
- **`test_client_identity_exposes_client_id`**
  Category: unit. Given a valid key, asserts the resolved identity object (whatever `Depends()`
  callable Plan wires in) exposes at least a stable `client_id` attribute and is usable as a dict
  key (hashable) — a direct, explicit check on the acceptance criterion "reusable by a future
  admission-control layer without rework," since the sibling ticket's own Investigate phase will
  check this claim rather than trust it blindly.
- **`test_scenario_runtime_client_fixture_still_passes_with_auth`**
  Category: regression guard (not a new behavior test). After `test_scenario_runtime_api.py`'s
  `client` fixture is updated with a default auth header (see Regression Surface above), re-run its
  existing suite — not a new test, but explicitly called out here so it isn't missed as "someone
  else's file."

## Scoped Pytest Commands

```
PYTHONPATH=. /home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest \
  tests/api/ tests/observability/test_metrics_export.py -m "not slow" -v
```

Narrower loop while iterating on just the new auth module:

```
PYTHONPATH=. /home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest \
  tests/api/test_api_key_auth.py tests/api/test_cors_config.py tests/api/test_health_liveness.py \
  tests/api/test_scenario_runtime_api.py -v
```

Never `pytest tests/` — scope stays within `tests/api/` (the auth mechanism's actual surface) plus
`tests/observability/test_metrics_export.py` (the one non-`tests/api/` file that exercises
`create_v2_app()` over real HTTP and is therefore in-scope regression surface).

## Anti-Drift Test Guards

- `test_health_exempt_from_auth` and `test_metrics_requires_auth` together prevent the two most
  likely silent-drift outcomes: someone reflexively exempting `/metrics` "because it's a metrics
  endpoint," or someone accidentally gating `/health` and breaking liveness probing without anyone
  noticing until an infra incident.
- `test_control_mutation_routes_require_auth` specifically guards the two lifecycle-mutation
  endpoints so a future refactor of `server.py`'s route wiring (e.g. someone reorganizing the inline
  routes into a sub-router and forgetting to carry the dependency over) fails loud in CI rather than
  silently reopening the exact hole this ticket exists to close.
- `test_keys_never_stored_or_compared_as_plaintext` guards against a regression back toward a bare
  dict/list literal of plaintext keys (the Anti-Drift Hazard both this investigation and the parent
  epic investigation flag) — it fails if a future edit swaps the hashed representation back to raw
  strings for convenience.
- `test_client_identity_exposes_client_id` is the one test that exists specifically to protect the
  sibling ticket (`TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL`) from silent rework — if this
  test passes now and the sibling ticket's own Investigate phase finds the shape doesn't actually
  serve its needs, that is real information (the acceptance criterion was optimistic), not a gap
  this ticket's own test coverage failed to surface.
- Re-running the full `tests/api/` + `tests/observability/test_metrics_export.py` scoped command
  (not just the new file) after implementation is itself an anti-drift guard: it is exactly the set
  of tests this investigation determined has any exposure to `create_v2_app()`'s wiring, so a green
  run of that scoped command is real evidence the blast radius assessment above was correct, not
  just an assumption carried into Plan unchecked.
