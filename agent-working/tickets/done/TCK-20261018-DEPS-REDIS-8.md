---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20261018-DEPS-REDIS-8
phase: done
date: 2026-10-18
tags: []
---

# TCK-20261018-DEPS-REDIS-8

## Title
redis-py 7.3.0 to 8.1.0 together with the Redis 8.10.2 image (#579 + #566)

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Dependabot #579 (client) and #566 (compose image) land as one tested pair. uv.lock only for the client (pyproject floor redis>=5.0.0 unchanged); compose.yaml redis service image pinned to redis:8.10.2-alpine by digest; perf docstring digest updated.

## PR notes (draft for the window PR)
1. Rollback: Redis 8 rewrites AOF/RDB files in the redis_data volume. Going back to 7.4 needs `docker compose down` plus removing the redis_data volume (dev data only).
2. Licence: Redis 8 is tri-licensed (RSALv2 / SSPLv1 / AGPLv3), no longer BSD. Fine for local use; our images do not bundle Redis.
3. Soak: platform-implementer runs a 30-minute live soak (anomaly worker, readiness) on the branch once pushed; the result goes on the PR.
4. Not tested: redis-py 8.1.0 against server 7.4.11.
5. Tested pair: redis-py 7.3.0 + server 7.4.11 vs 8.1.0 + 8.10.2-alpine, redis stream unit/integration/simulation_quality set: 162 passed, 1 skipped, 1 failed in both; the one failure was a test defect, fixed in TCK-20261018-REDIS-ADAPTER-MISSING-LIBRARY-TEST-BLOCKS-THE-IMPORT.

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
