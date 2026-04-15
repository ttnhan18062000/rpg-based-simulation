# Regression Stabilization Plan

Resolve 17 test failures in the full regression suite to achieve 100% stability. Most failures stem from "stale" test logic that hasn't been updated to match the finalized strategic cognition architecture.

## User Review Required

> [!NOTE]
> Several tests in `tests/ai/` and `tests/unit/ai/` are failing because they are older unit tests that have data-structure mismatches with the "Finalized" integration tests in `tests/integration/strategy/`. I will align them with the new structures.

> [!IMPORTANT]
> The infrastructure isolation tests are failing because `pytest` caches imports across files. I will move these to separate processes or use more robust isolation.

## Proposed Changes

### Strategic Cognition (Tests)

#### [MODIFY] [test_cognition_explainability.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/ai/test_cognition_explainability.py)
- Update `primary_overload_source` assertion from `"concerns"` to `"complexity"`.
- Sync with `AIBrain` scoring logic.

#### [MODIFY] [test_cognition_integrity.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/ai/test_cognition_integrity.py)
- Update replay path/schema assertions.
- `planning_budget` and other capacity metrics are now nested inside `last_capacity_profile`.

#### [MODIFY] [test_intel_capacity_regression.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/ai/test_intel_capacity_regression.py)
- Fix `KeyError: 'planning_budget'` by accessing it through the `last_capacity_profile` nesting.

#### [MODIFY] [test_lead_learning.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/ai/test_lead_learning.py)
- Replace `MagicMock` with real `Vector2` objects for `location` fields in `InterpretedLifeEvent` to satisfy Pydantic validation.

### Systems & Buildings

#### [MODIFY] [test_building_unification.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/test_building_unification.py)
- Update `suggest_detours` calls to include the required `profile` argument.

#### [MODIFY] [test_phase_3_social_contracts.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/test_phase_3_social_contracts.py)
- Fix `AttributeError: 'types.SimpleNamespace' object has no attribute 'narrative'`.
- This is a mock structure mismatch in the recruitment haggling tests.

### Infrastructure & Core

#### [MODIFY] [test_infrastructure_isolation.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/test_infrastructure_isolation.py)
- Move imports inside test methods to ensure `sys.modules` patching works even if the modules were imported by prior tests in the same `pytest` run.

#### [MODIFY] [test_assertion_drift.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/test_assertion_drift.py)
- Fix the logic that is failing to raise `AssertionError` when drift is detected.

## Verification Plan

### Automated Tests
- Run the full regression suite again:
  `pytest tests/ -vv --tb=short`
- Expected: 1305 passed, 0 failed.

### Manual Verification
- Verify that `working_log.csv` remains accurate after the fixes.
