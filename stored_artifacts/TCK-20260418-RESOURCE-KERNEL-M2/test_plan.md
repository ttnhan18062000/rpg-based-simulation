# Test Plan: Resource-Safe Engine Milestone 2

## Purpose
Verify the executable correctness and bit-identical determinism of the minimal single-thread kernel.

## Test Areas

### 1. Minimal Kernel Execution (`tests/engine/test_minimal_kernel.py`)
- **Goal**: Verify phase flow and time advancement.
- **Tests**:
  - `test_tick_advancement`: Assert `tick` increases by 1 each call.
  - `test_world_time_advancement`: Assert `world_time` increases correctly (passive).
  - `test_phase_order_execution`: Use mocks to verify the exact phase sequence is executed.

### 2. Authoritative Apply Path (`tests/engine/test_authoritative_apply.py`)
- **Goal**: Verify state mutation integrity.
- **Tests**:
  - `test_copy_on_write_integrity`: Ensure old state remains identical after an apply operation.
  - `test_deterministic_apply_order`: Assert that updates are applied in sorted `entity_id` order regardless of input order.
  - `test_invalid_update_rejection`: Attempt illegal state changes and verify rejection.

### 3. Readiness Gating (`tests/engine/test_readiness.py`)
- **Goal**: Verify active vs passive separation.
- **Tests**:
  - `test_readiness_threshold`: Entity only acts when readiness >= 100.
  - `test_quiet_tick_progression`: Verify `world_time` advances even when no entity is ready.

### 4. Determinism Suite (`tests/engine/test_determinism_suite.py`)
- **Goal**: Hard proof of reproducibility.
- **Tests**:
  - `test_seed_to_hash_stability`: Run 100 iterations, collect final hash, verify all 100 are identical.
  - `test_canonical_serialization`: Verify that dict keys are sorted and types are preserved in the hash material.

## Success Criteria
- 100% test pass on the above.
- Zero non-deterministic failures (flakiness).
