# Test Plan — TCK-20260921-MECHANISM-COMBAT-VALUE-DIFFERENTIAL-INSTRUMENT (re-scoped)

## New tests (2 files, both against combat_resolution only)
1. `tests/mechanic_scenarios/test_combat_resolution_damage_value_differential.py`
   - `test_attacker_atk_scales_damage_by_the_documented_formula`
   - `test_attacker_evolution_level_does_not_change_damage_dealt`
2. `tests/mechanic_scenarios/test_combat_attributes_real_fight_outcome_value_differential.py`
   - `test_attacker_strength_has_real_purchase_on_a_real_fights_outcome`
   - `test_attacker_charisma_does_not_move_the_fights_outcome`

## Existing tests to run (regression, scoped)
- `tests/mechanic_scenarios/` (whole dir)
- `tests/unit/progression/`
- `tests/unit/tools/test_mechanism_registry.py`

## Result
All 4 new tests passed on first real run. Full regression scope: 230/230 passed.
`make mechanism-registry-validate` + `make mechanism-prose-field-drift-check`: clean.
