---
ticket_id: TCK-20260619-E12C-BALANCE-TESTS
phase: test_plan
date: 2026-06-20
---

# Test Plan: Balance Regression Tests

## Run

```bash
pytest tests/integration/scenarios/test_balance_regression.py -v
# Expected: 3 passed, 1 skipped
```

## Result

3 passed, 1 skipped in 52.17s
- test_combat_attrition_urban_in_band     PASSED
- test_adventure_routing_defaults_off     PASSED
- test_blocker_penalty_not_near_binary    SKIPPED (E12B)
- test_scoring_formula_constants_stable   PASSED
