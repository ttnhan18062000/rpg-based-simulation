---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261024-API-SERVER-CHARACTERIZATION-TESTS
phase: open
date: 2026-10-24
tags: [architecture, api-design, testing]
---

# TCK-20261024-API-SERVER-CHARACTERIZATION-TESTS

## Title
Characterization tests that pin the HTTP surface of create_v2_app before src/api/server.py is split

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
M7 refactor lane, batch 1, ticket 1 of 3 for `src/api/server.py`. The user approved the scope on 2026-10-24 in codebase-planner's terminal ("Full split"), logged at https://github.com/ttnhan18062000/rpg-based-simulation/issues/715#issuecomment-6384147652. rpg-planner confirmed on #697 (2026-10-22 17:27Z) that no rpg work is open on the file.

Roadmap section 9 says characterization tests come first. This ticket adds tests that pin what `create_v2_app` exposes today, so tickets 2 and 3 can prove they changed nothing. The tests must pass on origin/main **before** any move commit, and they stay as permanent regression tests.

## Scope
1. A recorded snapshot fixture and a test that builds the app the way `tests/api/test_all_routes_require_auth.py` does.
   - Fixture: JSON under `tests/fixtures/`. Not under `agent-working/stored_artifacts/`, which gitignores `.json`.
   - Test: for example `tests/api/test_server_http_surface_characterization.py`.
   - It pins the following for **every** route, whether HTTP, WebSocket or included from a router:
     - path, methods, endpoint `__name__`, route `name`, `response_class`, `response_model` (repr or `None`) and `include_in_schema`;
     - the dependency callables, flattened (route-level and router-level, by qualified name, in order);
     - **registration order**. FastAPI matches the first route that fits, so the order is behaviour.
2. The full `app.openapi()` document, pinned byte-for-byte as a canonical JSON dump (sorted keys). Tickets 2 and 3 keep the endpoint function names, so operation ids must not change.
3. The middleware stack: classes in order, with these options:
   - `RequestDurationMiddleware` outermost;
   - `GZipMiddleware` with `minimum_size=512`;
   - `CORSMiddleware` with `allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]` and `allow_credentials` unset.
4. Responses, through `TestClient` with the auth and admission headers the existing tests use:
   - `GET /api/v1/observability/ui`: status 200, `content-type`, and the **sha256 of the body bytes**, requested without `Accept-Encoding: gzip`;
   - `/observability/ui` and `/api/v1/observability/live/ui`: redirect status and `location`;
   - `/metrics`: rejected without admission and served with it, following the pattern in `tests/api/test_admission_control.py`;
   - a CORS preflight (`OPTIONS` with `Origin` and `Access-Control-Request-Method`) and the `access-control-*` headers in its response.
5. A regeneration path (an `--update` switch or a small helper) for the fixture, used **only** when a later ticket intends a surface change. No ticket in this batch does. Document it in the test module's docstring.

## Out of Scope
- Any edit under `src/`.
- Handler behaviour beyond the items above (already covered by `tests/api/`).
- Fixing anything the snapshot reveals. Record it in investigation.md and tell codebase-planner.

## Acceptance Criteria
- The new tests pass on origin/main with `src/` untouched: `git diff origin/main -- src/` is empty at this ticket's commit.
- Breaking each pinned item makes the test fail. Run five probes, record each probe and its failure in test_plan.md, then revert them:
  1. rename an endpoint;
  2. swap two `include_router` calls;
  3. change one byte of the UI HTML;
  4. drop a dependency;
  5. change the GZip `minimum_size`.
- The snapshot is deterministic: two runs in fresh processes produce identical fixtures.
- `tests/api` and `tests/architecture/test_api_read_model_guard.py` pass.

## Related Tickets
- Next: `TCK-20261024-API-SERVER-OBSERVABILITY-UI-STATIC-PAGE`, `TCK-20261024-API-SERVER-INLINE-ROUTES-TO-ROUTERS`
- `TCK-20260823-HTTP-API-KEY-AUTH`, `TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG` (the decisions behind the auth and CORS lines)

## Related Docs
- `docs/plans/codebase_health/python_code_craft_roadmap.md`:
  - the M7 row;
  - the decision 7 amendment of 2026-10-20;
  - section 9 "Refactor risk" (characterization tests first; the determinism and replay suites are the gate).
- `docs/guidelines/python_code_standard.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260823-HTTP-API-KEY-AUTH/plan.md` (route and auth table)

## Related Code Areas
- `src/api/server.py` (read only in this ticket)
- `tests/api/test_all_routes_require_auth.py`, `tests/api/test_admission_control.py`, `tests/api/test_cors_config.py`, `tests/api/server_readiness.py`

## Assumptions / Open Questions
- `tests/api/**` routes to the rpg domain. The owner-approved M7 lane covers tests that characterize the file it refactors. The PR body names the new test files so rpg-planner sees them.
- Open: some routers are included only under a condition (`server.py:132`, `:147`, `:150`), so the route set may depend on the profile or arguments passed to `create_v2_app`. Snapshot every branch the existing tests exercise. List any conditional router left unpinned in investigation.md.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
