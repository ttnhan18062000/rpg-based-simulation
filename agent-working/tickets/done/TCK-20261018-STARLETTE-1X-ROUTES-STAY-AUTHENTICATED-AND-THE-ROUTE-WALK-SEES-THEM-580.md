---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-STARLETTE-1X-ROUTES-STAY-AUTHENTICATED-AND-THE-ROUTE-WALK-SEES-THEM-580
phase: done
date: 2026-10-18
tags: []
---

# TCK-20261018-STARLETTE-1X-ROUTES-STAY-AUTHENTICATED-AND-THE-ROUTE-WALK-SEES-THEM-580

## Title
Prepare the starlette 1.x bump (#580): every route stays authenticated and the route walk sees them

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
rpg-planner dispatch: prepare #580 for the v1 dependency window on a local branch (not pushed, not folded into rpg-next; it lands after the rpg-next PR merges). Keep every route, ws included, authenticated; add an all-routes auth test red on the bare upgrade; keep presenter and schema boundaries.

## Scope
pyproject.toml and uv.lock (fastapi, starlette); tests/helpers/api_routes.py; tests/api/test_all_routes_require_auth.py; the two tests that walk app.routes; one doc note.

## Out of Scope
Any change under src/api (runtime auth is unaffected); pushing; folding into rpg-next.

## Acceptance Criteria
All-routes auth test red on the bare upgrade and green after; API tests, tests/unit/api and lint-imports pass on starlette 1.8.0.

## Related Tickets
TCK-20260823-HTTP-API-KEY-AUTH

## Related Docs
docs/architecture/http_api_key_authentication.md

## Related Stored Artifacts
agent-working/stored_artifacts/TCK-20261018-STARLETTE-1X-ROUTES-STAY-AUTHENTICATED-AND-THE-ROUTE-WALK-SEES-THEM-580/

## Related Code Areas
pyproject.toml; uv.lock; tests/api; tests/helpers/api_routes.py

## Assumptions / Open Questions


## Implementation Notes
Runtime auth held on the bare upgrade (ws closed 1008, REST 401). What 1.x breaks is route introspection: app.routes holds _IncludedRouter nodes and a ws effective context has an empty path and no dependant. See investigation.md.

## Test Summary
tests/api 166 passed and tests/unit/api 63 passed on 1.8.0; 229 passed on 0.52.1; lint-imports 17 kept, 0 broken.

## Files Changed
pyproject.toml, uv.lock, docs/architecture/http_api_key_authentication.md, tests/helpers/api_routes.py, tests/api/test_all_routes_require_auth.py, tests/api/test_api_key_auth.py, tests/api/test_scenario_runtime_api.py

## Completion Summary
Dependency bump prepared on branch rpg-deps-starlette1, local only.
