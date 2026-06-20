---
ticket_id: TCK-20260619-E12C-BALANCE-TESTS
phase: plan
date: 2026-06-20
---

# Plan: Balance Regression Test Suite

## Tests to Write

1. test_combat_attrition_urban_in_band — integration/slow, 100 ticks, attrition < 60%
2. test_adventure_routing_defaults_off — fast flag check
3. test_blocker_penalty_not_near_binary — skip (E12B decision)
4. test_scoring_formula_constants_stable — unit test, no simulation

## Files Changed

- tests/integration/scenarios/test_balance_regression.py (new)
- docs/audits/D04_balance_tuning.md (status: partial → done)
