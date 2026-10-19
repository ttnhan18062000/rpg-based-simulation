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
Content of dependabot #578 plus the fixes it needs. Correction (rpg-planner, PR #645): the 6 dataclasses.replace / entity_id errors fixed in 54649f3f7 are NOT caused by the mypy 2.4 bump. They reproduce on rpg-next with the locked mypy 2.1.0 (rpg-next's folds introduced them; main is clean), and the fix was cherry-picked to rpg-next as 6d7bd1509. My earlier 'mypy 2.4 is the culprit' was wrong: I never ran the baseline filter on 2.1.0 first. Still to re-check on the rebased branch (after 54649f3f7 is dropped as already applied): which errors are really mypy 2.4's; known so far: config/loader.py issubclass on the pydantic 2.14 TypeForm annotation (135bb967e). pydantic 2.14 annotation typing: cast in config/loader.py. fastapi 0.143 lazy include_router: tests/api route-walking tests use a flat-routes helper. graphifyy pin test moved to 0.9.88.

## Scope
Dependency window on branch rpg-deps-uv-redis (local, dispatched by rpg-planner).

## Out of Scope
Pushing, merging. requirements-knowledge.txt: it is pinned by agent-working (#590), so the #578 bumps there (torch 2.12.1+cpu to 2.14.1, which drops the +cpu guard; graphifyy 0.8.39 to 0.9.88; headroom-ai 0.37.0 to 0.40.0) were reverted to origin/main's file, together with the matching graphifyy pin in tests/tools/test_code_test_index.py. requirements-knowledge is left to agent-working.

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
