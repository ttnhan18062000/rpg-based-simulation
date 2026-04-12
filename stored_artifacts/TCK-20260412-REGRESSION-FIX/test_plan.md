# Test Plan - TCK-20260412-REGRESSION-FIX

## Target Areas
- `InterpretedLifeEventKind` enum.
- Benchmark scaling for 1000+ entities.
- Combat engagement determinism.
- AOE skill selection logic.

## Verification Steps

### 1. Automated Regression Run
Run the full suite highlighting the previously failed tests:
```bash
pytest tests/unit/core/models/test_enums.py
pytest tests/bench/test_scaling.py
pytest tests/e2e/test_combat_arena_e2e.py
pytest tests/unit/ai/test_aoe_selection.py
```

### 2. Full Suite Pass
Ensure no side effects in other modules:
```bash
pytest tests/
```

### 3. Benchmark Validation
Verify performance is within 10% of the baseline (2.0s per 1000 ticks/entity-pair).

## Criteria for Success
- 100% pass rate in standard test runner.
- Zero `AttributeError` or `NameError` in chaos/remediation suites.
- Execution time per tick remains sub-millisecond for at least 95% of ticks.
