# Plan: V2 Engine Performance Optimization (Phase 2)

## Goal
Achieve sub-100ms p95 latency for 1000+ entity simulations.

## Proposed Changes
1. **Movement Routing (`src/engine/pipeline_phases/movement.py`)**
   - Eliminate redundant `sorted(state.entities.keys())` in position swaps.
   - Cache `_desired_next_step_for_swap` across inner loop evaluations.
   - Early-out stationary entities before spatial grid queries.

2. **Action Routing (`src/engine/pipeline_phases/actions.py`)**
   - Eliminate redundant per-iteration dataclass copies of `sliding_state`.

3. **Read-Only View (`src/core/state.py`)**
   - Optimize `EntityState.to_readonly` by caching `IdentityComponent`, `InventoryComponent`, `CombatComponent`, and `EquipmentComponent` directly on the mutable entity once converted to `ReadOnlyDict` wrappers, avoiding object allocation storms during Collection phase.
   - Optimize `AuthoritativeState.to_readonly` to avoid rebuilding `ReadOnlyDict` for empty/unchanged world collections.

## Verification
- Run `pytest tests/perf/test_perf_movement.py` to verify p95 < 100ms for 1000 entities.
- Run `python3 artifacts/profile_subphases.py` to verify individual phase cost reductions.
- Verify determinism tests in `tests/integration/kernel/`.
