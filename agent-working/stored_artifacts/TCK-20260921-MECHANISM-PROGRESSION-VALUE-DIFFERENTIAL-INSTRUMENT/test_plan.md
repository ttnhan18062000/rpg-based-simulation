# Test Plan — TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT

## New tests
1. `tests/mechanic_scenarios/test_readiness_and_derived_stats_value_differential.py`
   - `test_agility_changes_readiness_speed_by_the_documented_formula` (positive control,
     `readiness_speed_scaling`)
   - `test_agility_does_not_change_derived_combat_stats` (negative control, `derived_stats`)
   - `test_vitality_and_strength_change_derived_combat_stats_by_the_documented_formula` (positive
     control, `derived_stats`)
   - `test_vitality_and_strength_do_not_change_readiness_speed` (negative control,
     `readiness_speed_scaling`)
2. `tests/mechanic_scenarios/test_evolution_xp_reward_value_differential.py`
   - `test_defender_evolution_level_scales_the_xp_reward_proportionally` (positive control)
   - `test_defender_evolution_points_does_not_change_the_xp_reward` (negative control)
   - Both assert the kill itself resolves identically (same outcome_kind, same rounds) across arms,
     to make the RNG-order-safety claim directly observable, not just argued.

## Existing tests to run (regression check, scoped — not full suite)
- `tests/unit/progression/` (whole directory — `test_leveling.py`, `test_evolution.py`,
  `test_phase8_progression.py`, `test_class_tiers.py`, `test_leveling_veterancy.py`)
- `tests/unit/tools/test_mechanism_registry.py` (registry invariants, including the duplicate-key
  check from Program A)
- `tests/mechanic_scenarios/` (whole directory — confirm no cross-test interference from the new
  files)

## Pass criteria
All new tests pass deterministically (same seed, re-run twice to confirm no flake). All existing
tests in the scoped set continue to pass. `registries/mechanisms.yaml` passes all invariants
including duplicate-key detection after the edit.
