---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20261018-DEPS-UV-MINOR-PATCH-GROUP
phase: done
date: 2026-10-18
tags: []
---

# TCK-20261018-DEPS-UV-MINOR-PATCH-GROUP

## Title
uv minor/patch group (#578): mypy 2.4, pydantic 2.14, fastapi 0.143 and 19 more

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Content of dependabot #578 plus the fixes it needs. mypy 2.1.0 to 2.4.0 alone broke Type check (dataclasses.replace kwargs now checked): types-only code fixes. pydantic 2.14 annotation typing: cast in config/loader.py. fastapi 0.143 lazy include_router: tests/api route-walking tests use a flat-routes helper. graphifyy pin test moved to 0.9.88.

## Scope
Dependency window on branch rpg-deps-uv-redis (local, dispatched by rpg-planner).

## Out of Scope
Pushing, merging.

## Acceptance Criteria
mypy gate, lint-imports, code health and the touched-area tests green.

## Related Tickets
TCK-20261018-REDIS-ADAPTER-MISSING-LIBRARY-TEST-BLOCKS-THE-IMPORT

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
pyproject.toml, uv.lock, compose.yaml, src/core, src/config, src/engine/movement.py, tests/api

## Assumptions / Open Questions
Soak on redis 8 pending (platform-implementer).

## Implementation Notes
See branch commits.

## Test Summary
See rpg-planner report: mypy 0 new, lint-imports 17/0, health 0 new, unit 1054, tools 2081, api/cli 164 passed.

## Files Changed
See branch diff against rpg-next b23e78128.

## Completion Summary
Prepared locally, unpushed.
