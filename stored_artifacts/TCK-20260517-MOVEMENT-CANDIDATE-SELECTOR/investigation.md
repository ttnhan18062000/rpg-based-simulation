# Investigation: MovementCandidateSelector

## Current State

In `src/engine/pipeline_phases/movement.py`, `MovementPhase.route_movement_intent` executes two passes every tick:
1. Pass 1 iterates over all `refined_entity_updates.keys()`.
2. Pass 2 iterates over all `state.entities.values()`.

This causes duplicate logic and forces an O(N) evaluation across all entities in the simulation on every tick, even if most entities are stationary, inactive, dead, or waiting for readiness accumulation.

## Measured Hotspot

Profiler reports indicate movement routing (`route_movement_intent`, `resolve_move`) is a primary compute hotspot, consuming over 20-35s in heavy benchmarks.

## Optimization Strategy

Implement `MovementCandidateSelector` in `src/engine/candidate_selector.py` to filter entity IDs prior to movement routing. By unifying Pass 1 and Pass 2 into a single deterministic iteration over pre-filtered candidate IDs, we eliminate redundant checks and significantly accelerate the movement phase while preserving perfect semantic correctness.
