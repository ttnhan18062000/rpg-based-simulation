---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261018-REDIS-ADAPTER-MISSING-LIBRARY-TEST-BLOCKS-THE-IMPORT
phase: done
date: 2026-10-18
tags: []
---

# TCK-20261018-REDIS-ADAPTER-MISSING-LIBRARY-TEST-BLOCKS-THE-IMPORT

## Title
test_redis_adapter_resilient_missing_library really blocks the redis import, so it passes with or without a live server on :6379

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found while proving the redis-py 8 / Redis 8 bump. The test deleted `sys.modules["redis"]`, but `import redis` simply re-imports the package, so the adapter connected to any live server on :6379 and reported "healthy" instead of "degraded". It passed only with no server running. Dispatched by rpg-planner.

## Scope
`tests/unit/observability/test_event_stream_adapters.py`: use `monkeypatch.setitem(sys.modules, "redis", None)` (makes `import redis` raise ImportError). Also `tests/perf/test_simq_isolation_overhead.py:17` docstring digest moved to the redis 8.10.2 image with the redis bump.

## Out of Scope
Any change to `RedisStreamAdapter`; `compose.yaml` (platform-owned).

## Acceptance Criteria
The test passes with no server and with a live redis:8.10.2-alpine on :6379.

## Related Tickets
TCK-20261013-PIN-THE-REDIS-IMAGE-IN-COMPOSE

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
src/observability/stream/adapters.py (unchanged), tests/unit/observability/test_event_stream_adapters.py

## Assumptions / Open Questions
None.

## Implementation Notes
Test-only change.

## Test Summary
tests/unit/observability/test_event_stream_adapters.py: 5 passed without a server and 5 passed with a live redis:8.10.2-alpine container on 127.0.0.1:6379 (before: 1 failed with a server).

## Files Changed
tests/unit/observability/test_event_stream_adapters.py, tests/perf/test_simq_isolation_overhead.py

## Completion Summary
The missing-library test now blocks the import for real and is independent of any local redis server.
