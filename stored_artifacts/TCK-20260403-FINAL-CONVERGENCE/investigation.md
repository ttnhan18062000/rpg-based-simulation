# Investigation: Architectural Stability & Convergence (TCK-20260403-FINAL-CONVERGENCE)

## Current State Analysis

### 1. Immutability (`SimulationModel.freeze()`)
- **Found**: `src/core/models/base.py` implements recursive freezing.
- **Problem**: It handles immediate collections (`list`, `tuple`, `dict`) but doesn't recursively wrap collections *within* collections (e.g., `list[list[int]]` or `dict[str, list[int]]`).
- **Impact**: Deeply nested standard Python collections remain mutable if they aren't `SimulationModel` instances themselves.

### 2. Typed Records & `intent_metadata`
- **Found**: `ActionProposal.target` is already `TargetUnion`. `NavigationUpdate.target_pos` is `Vector2 | None`.
- **Problem**: `intent_metadata` (loose dict) was meant to be purged. 
- **Action**: Search for `intent_metadata` usage in `src/actions/` and `src/ai/`. 

### 3. Legacy Cleanup
- **Found**: `src/api/encoder.py` (legacy) vs `src/api/presenters/`.
- **Target**: Remove `src/api/encoder.py` and ensure all routes (including `stream_ws.py`) use presenters.
- **Target**: Check `src/core/entities/stats.py` for legacy property shims.

### 4. Serialization & Caching
- **Found**: `EngineManager` in `src/api/engine_manager.py` has `_static_data_cache`.
- **Impact**: Caching exists for static data, but might need unification for dynamic streaming payloads if throughput is high.

### 5. Test Failures (26 total)
- **Status**: Failed to collect due to missing `hypothesis`.
- **Suspected Root Cause**: Missing dev dependencies or architectural regressions in `HeroLifecycleSystem`.
- **Files to watch**: `tests/integration/test_hero_lifecycle.py`, `tests/integration/test_invariants.py`, `tests/integration/test_snapshot_safety.py`.

## Risks & Assumptions
- **Assumption**: `hypothesis` is a required dev dependency but missing from the environment.
- **Risk**: Deep `freeze()` might have performance overhead on large snapshots.
