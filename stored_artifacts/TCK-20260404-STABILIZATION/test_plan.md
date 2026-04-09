# Test Plan - TCK-20260404-STABILIZATION

## Objectives
1.  Verify that `UnboundLocalError: Perception` is resolved.
2.  Verify that `NameError: HeroClass` is resolved.
3.  Verify that `AttributeError: Perception.get_faction_registry` is resolved.
4.  Verify that `SimulationModel.freeze()` handles slotted models and already-frozen instances correctly.
5.  Achieve 100% pass rate in the Combat Arena E2E suite.

## Test Cases

### 1. AI Decision Integrity
*   **Action**: Run `pytest tests/e2e/test_combat_arena_e2e.py`.
*   **Expected Result**: All 38 items pass. No "AI: Decision error" in logs.

### 2. Core Model Freezing
*   **Action**: Create a temporary test script that freezes a slotted SimulationModel.
*   **Expected Result**: No `AttributeError` on `__dict__` and successful recursive freezing.

### 3. API Payload Stability
*   **Action**: Run `pytest tests/integration/api/test_api_payload.py`.
*   **Expected Result**: Serialization and freezing work together without `ValidationError`.

### 4. Regression Suite
*   **Action**: Run `pytest tests/unit/core/test_invariants.py`.
*   **Expected Result**: All invariant tests pass, proving that freezing works correctly.
