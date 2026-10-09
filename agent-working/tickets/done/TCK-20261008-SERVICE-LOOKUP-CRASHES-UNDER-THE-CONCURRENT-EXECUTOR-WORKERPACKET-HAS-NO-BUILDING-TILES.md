---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261008-SERVICE-LOOKUP-CRASHES-UNDER-THE-CONCURRENT-EXECUTOR-WORKERPACKET-HAS-NO-BUILDING-TILES
phase: done
date: 2026-10-09
tags: [combat]
---

# TCK-20261008-SERVICE-LOOKUP-CRASHES-UNDER-THE-CONCURRENT-EXECUTOR-WORKERPACKET-HAS-NO-BUILDING-TILES

## Title
A service lookup crashes under the concurrent executor: `service_reach.building_kind_at` falls through to `state.building_tiles`, which a `WorkerPacket` does not have.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`src/engine/service_reach.py:30` read `state.building_tiles.get(tile)` whenever no building stood on the tile (most of the five reach offsets). Under the concurrent executor `state` is a `WorkerPacket` (`src/core/worker_protocol.py`: it carries `buildings` and `building_map`, no `building_tiles`), so the lookup raised `AttributeError: 'WorkerPacket' object has no attribute 'building_tiles'` and `worker_manager.py:226` logged "Internal worker crash" and returned a failure result.

Evidence, clean `main` `28e29ed2e`: (a) a real `WorkerPacket` with `buildings` and `building_map` and no `building_tiles`: `building_kind_at(packet, free_tile)` raises at `service_reach.py:30`, and `service_tile` at `service_reach.py:38` through it; (b) the longer cases of `tests/unit/worldassembly/test_corpus_diversity.py` (run with captured logs) log "Internal worker crash: 'WorkerPacket' object has no attribute 'building_tiles'" in: `test_simq_routing_test_seed42_1000t_cognition_grade_stability` (79 lines), `test_urban_political_seed123_1000t_social_economy_grade_stability` (33), `test_urban_political_seed42_1000t_social_grade_stability` (11), `test_simq_routing_test_seed42_500t_cognition_grade_stability` (7), `test_generated_frontier_3_42_extended_population_stability` (2), `test_urban_political_seed123_500t_cognition_grade_stability` (1). They only reproduce inside the suite's CPU-stress setup (a 400-tick and an 800-tick default-executor run did not hit it). Those tests already fail on `main` for grade or population reasons; this ticket does not claim to fix them.

## Scope
`service_reach.py` only: read the map with `getattr(state, "building_tiles", None)`, a missing map meaning no kind (the pattern `legality.py` already uses). No field on `WorkerPacket` (`core/worker_protocol` is perf-adjacent). `shop.py:56` and `blacksmith.py:130` read `state.building_tiles` directly but run as pipeline phases on the main thread with the authoritative state (`pipeline.py:223` and `:371`, `run_phase("blacksmith"/"shop", lambda u: ...enforce(state, u))`), never in a worker, so they are left alone; Lane B's batch 2 routes the shop through `service_reach`.

## Out of Scope
- The corpus-diversity grade and population failures; the shop and blacksmith systems.

## Acceptance Criteria
- [x] A lookup on a `WorkerPacket` beside a building returns its kind, and elsewhere returns None, without raising (`tests/unit/engine/test_service_reach_on_a_worker_packet.py`).
- [x] A state that fills `building_tiles` is still honoured.

## Related Tickets
- The testing-planner trace of the crash; Lane B's batch 2 (shop through `service_reach`).

## Related Docs
- `docs/engine/known_limitations.md`.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-SERVICE-LOOKUP-CRASHES-UNDER-THE-CONCURRENT-EXECUTOR-WORKERPACKET-HAS-NO-BUILDING-TILES/`.

## Related Code Areas
- `src/engine/service_reach.py`, `src/core/worker_protocol.py`, `src/engine/legality.py` (the existing pattern).

## Assumptions / Open Questions
- The six corpus tests above remain red for their own reasons on `main`; whether the crash contributes to their grade or population results is not established.

## Implementation Notes
One line in `building_kind_at`.

## Test Summary
`tests/unit/engine/test_service_reach_on_a_worker_packet.py` (4): fails on clean `main` at `service_reach.py:30`, passes with the fix.

## Files Changed
src/engine/service_reach.py, tests/unit/engine/test_service_reach_on_a_worker_packet.py.

## Completion Summary
A service lookup on a worker packet no longer raises; no behaviour change for authoritative states.
