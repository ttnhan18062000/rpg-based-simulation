---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261013-PIN-THE-REDIS-IMAGE-IN-COMPOSE
phase: done
date: 2026-10-13
tags: []
---

# TCK-20261013-PIN-THE-REDIS-IMAGE-IN-COMPOSE

## Title
Pin the redis image in compose.yaml to the exact 7.4.11 build, by digest (issue #515).

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`redis:7-alpine` floated while the other compose images are exact; Redis backs src/observability, so a new 7.x patch could change behaviour with no diff here.

## Scope
compose.yaml redis image; the one doc-comment docker run in tests/perf/test_simq_isolation_overhead.py.

## Out of Scope
Other images, redis client versions.

## Acceptance Criteria
The image is pinned exactly; every file that names the redis image is checked; the observability redis tests pass against that image.

## Related Tickets
GitHub issue #515.

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
compose.yaml; tests/perf/test_simq_isolation_overhead.py.

## Assumptions / Open Questions
The pulled `redis:7-alpine` (2026-10-13) is 7.4.11; `redis:7.4.11-alpine` resolves to the same index digest sha256:858f009f9709ce576febc734aa78b8f6d624b82571f9ddb6bda4377c833b3499.

## Implementation Notes
Pinned `redis:7.4.11-alpine@sha256:858f009f...`. Files naming the redis image: compose.yaml (service redis) and a docker run line in a perf-test docstring (updated to match). No CI workflow names it; tests use localhost:6379.

## Test Summary
tests/unit/observability/test_redis_stream_adapter.py and tests/integration/observability/test_stream_consumer_pel_reclaim.py: 6 passed against a container of the pinned image. `docker compose config` resolves.

## Files Changed
compose.yaml; tests/perf/test_simq_isolation_overhead.py.

## Completion Summary
Done.
