# TCK-20260406-AOA-CANONICALIZE-STREAM: Canonicalization & Stream Isolation

## Status: DONE

## Description
Centralize simulation map-stream production (Slim/Rich/Compact) into the engine's `PersistencePhase` to ensure a single source of truth and reduce API-replica overhead.

## Acceptance Criteria
- [x] `PersistencePhase` computes map-delta (Slim) and pushes to Redis `sim:stream`.
- [x] `PersistencePhase` computes Rich and Compact tick payloads and pushes to Redis.
- [x] `EngineManager` is decoupled from Redis publishing logic.
- [x] SSE and WS routes consume canonical Redis payloads.
- [x] Engine remains runnable without `redis` or `msgpack` installed (Infrastructure Hardening).
- [x] 100% test pass for `test_canonical_stream.py`.

## Changes Summary
- **src/engine/phases/persistence.py**: Integrated canonical Redis streaming.
- **src/api/engine_manager.py**: Removed redundant publishing logic.
- **src/api/routes/stream_ws.py**: Updated to consume canonical payloads.
- **src/api/redis_client.py**: Hardened against missing package.
- **src/engine/phases/context.py**: Added `tick_events` for orchestration.
- **src/engine/world_loop.py**: Passed `tick_events` to context.

## Artifacts
- [walkthrough_pillar5.md](file:///home/vboxuser/.gemini/antigravity/brain/d4923ea4-ede4-4b42-b61d-5fb64aef880a/walkthrough_pillar5.md)
- [test_canonical_stream.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/engine/test_canonical_stream.py)
