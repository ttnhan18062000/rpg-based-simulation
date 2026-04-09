# Test Plan: Architectural Stability & Convergence (TCK-20260403-FINAL-CONVERGENCE)

## Automated Verification

### 1. Immutability Tests
- **Target**: `tests/unit/core/test_snapshot_safety.py`
- **Method**: Verify `freeze()` on deeply nested collections (e.g. `list[list[int]]`).
- **Success**: Mutation of any level of a frozen `SimulationModel` raises `RuntimeError`.

### 2. Typed Records & Purge Verification
- **Target**: `tests/unit/actions/test_action_convergence.py` (or similar)
- **Method**: Verify that `ActionProposal` and `IntentUpdate` are strictly typed and no `intent_metadata` dicts are accepted by the `ConflictResolver`.

### 3. Cleanup Verification
- **Target**: `tests/unit/core/test_aoa_integrity.py`
- **Method**: Run integrity checks to ensure no legacy shims remain in `src/`.
- **Success**: No occurrences of `.stats`, `.mind.*` (flat), or use of `src/api/encoder.py`.

### 4. Serialization & Caching Performance
- **Target**: `tests/performance/test_api_throughput.py` (if any)
- **Method**: Verify `EngineManager._static_data_cache` effectively reduces CPU load on repeated static data requests.

### 5. Regression Recovery
- **Target**: `tests/integration/test_hero_lifecycle.py`, `tests/integration/test_invariants.py`, `tests/integration/test_snapshot_safety.py`.
- **Success**: 100% pass rate for all 26 failing tests.

## Manual Verification
- None required for architectural convergence (all must be library/infrastructure testable).
