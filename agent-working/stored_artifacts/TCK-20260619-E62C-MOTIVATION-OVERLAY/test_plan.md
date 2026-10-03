---
ticket_id: TCK-20260619-E62C-MOTIVATION-OVERLAY
phase: test_plan
date: 2026-06-23
---

# Test Plan — TCK-20260619-E62C-MOTIVATION-OVERLAY

## Tests Created

`tests/unit/culture/test_culture_applicator.py` (11 tests):
- test_zero_culture_produces_zero_delta — AC2
- test_high_fatalism_increases_caution_delta — AC1
- test_high_fatalism_decreases_combat_delta
- test_high_hero_veneration_increases_loyalty_delta
- test_high_scarcity_memory_increases_survival_delta
- test_high_conflict_exposure_increases_caution_delta
- test_high_conflict_exposure_decreases_loyalty_delta
- test_delta_bounded_upper (max 1.0)
- test_delta_bounded_lower (min -0.5)
- test_below_threshold_no_effect
- test_empty_tags_zero_delta

`tests/unit/motivation/test_motivation_bias_culture.py` (4 tests):
- test_compute_bias_multiplier_no_culture_unchanged — AC3
- test_compute_bias_multiplier_with_zero_culture_unchanged
- test_compute_bias_multiplier_with_fatalism_raises_caution — AC4
- test_compute_bias_multiplier_result_at_least_0_1

## Existing Tests

- tests/unit/domains/motivation/ — 10 existing tests pass (regression check)
- tests/unit/culture/ — 31 total pass (20 from E62A/B + 11 new)
- tests/unit/campaigns/ — 90 pass

## Result: 121 passed
