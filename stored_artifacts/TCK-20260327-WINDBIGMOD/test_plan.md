# WINDBIGMOD Test Plan

## 1. Unit Tests

### 1.1 `tests/unit/core/test_models_refactor.py` (New)
- **StatsShim Extraction**: Verify `Hero` still accesses `Equipment` stats via the shim.
- **Delegation Logic**: Verify `active_effects` properly modify stats via `StatsShim`.
- **Property Caching**: Ensure `StatsShim` results are deterministic and not recursive.

### 1.2 `tests/unit/ai/test_flow_fields_refinement.py` (New)
- **Bilinear Smoothing**: 
    - Test `get_vector` at (1.5, 1.5) with known neighbor vectors.
    - Check if result correctly interpolates between (1,0) and (0,1) for diagonal travel.
- **Target Caching**:
    - Verify `is_static_target` correctly identifies Town/Camps for infinite caching.
    - Verify World Bosses trigger TTL-based re-generation.

## 2. Integration Tests

### 2.1 `tests/integration/ai/test_wind_pillar_navigation.py` (New)
- **Scenario**: 10 Heroes returning from different map locations to a single Town.
- **Goal**: Verify all heroes reach the Town without "jagged" movement.
- **Metric**: Check total ticks vs A* Baseline (should be comparable).

## 3. Regression Tests
- **Existing Suite**: Run `make test-quick` to ensure no breaking changes in `AIBrain` or `WorldLoop`.
- **Determinism**: Run `tests/unit/platform/test_deterministic_replay.py`.

## 4. Performance Tests
- **Scenario**: 100 Entities targeting a central World Boss.
- **Verification**: `make profile` and compare "AI Movement" phase CPU usage before/after the refactor.
