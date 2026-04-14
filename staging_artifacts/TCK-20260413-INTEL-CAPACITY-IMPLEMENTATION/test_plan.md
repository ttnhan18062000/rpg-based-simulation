# Test Plan: Intel Capacity Milestone 1

## Purpose
Verify that the `CognitionCapacityBuilder` derivations are accurate, deterministic, and non-mutating.

## Unit Tests

### `tests/ai/test_cognition_capacity_builder.py`
- `test_build_profile_min_attributes_full_stamina`:
    - Input: `int_=1, wis=1, per=1, cha=1, stamina=50, max_stamina=50`.
    - Expected: Golden Case A values.
- `test_build_profile_max_attributes_full_stamina`:
    - Input: `int_=15, wis=15, per=15, cha=15, stamina=50, max_stamina=50`.
    - Expected: Golden Case B values.
- `test_build_profile_max_attributes_half_stamina`:
    - Input: `int_=15, wis=15, per=15, cha=15, stamina=25, max_stamina=50`.
    - Expected: Golden Case C values.
- `test_build_profile_uses_attribute_caps`:
    - Input: `int_=20, int_cap=20`.
    - Expected: Correct normalization using the 20 cap.
- `test_build_profile_handles_missing_attributes`:
    - Input: Mock entity with missing attribute fields.
    - Expected: Fallback to 1.
- `test_build_profile_handles_missing_caps`:
    - Input: Mock entity with missing cap fields.
    - Expected: Fallback to 15.
- `test_build_profile_handles_zero_max_stamina`:
    - Input: `stamina=5, max_stamina=0`.
    - Expected: Stamina ratio 1.0.

### `tests/ai/test_cognition_capacity_determinism.py`
- `test_profile_derivation_is_deterministic_for_same_entity_state`:
    - Run build twice on same entity.
    - Assert results are identical.
- `test_profile_derivation_is_independent_of_tick_in_milestone_1`:
    - Run build with different tick values.
    - Assert results are identical.
- `test_profile_derivation_does_not_use_rng`:
    - Run build twice with same entity.
    - Assert results are identical (basic check).

### `tests/ai/test_cognition_capacity_non_mutation.py`
- `test_build_profile_does_not_mutate_entity_attributes`:
    - Assert `entity.progression.attributes` remains unchanged after call.
- `test_build_profile_returns_new_profile_object_each_call`:
    - Assert `id(profile1) != id(profile2)`.

## Integration Tests
- None for Milestone 1 as it is foundational.

## Regression Coverage
- This test suite ensures that future changes to attributes or cognition logic can be verified against these baseline formulas.
