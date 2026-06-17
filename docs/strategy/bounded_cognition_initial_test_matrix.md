---
status: active
layer: strategy
authority: P1
audience: developer
---

# Bounded Cognition Test Matrix

## Golden-Value (Case A, B, C)
Ensures exact compliance with the numeric derivations defined in the bounded cognition contract.

| Test Name | Input State | Case | Regression Purpose |
| :--- | :--- | :--- | :--- |
| `test_build_profile_min_attributes_full_stamina` | `1, 1, 1, 1` | Case A | Ensures absolute minimum baseline remains stable. |
| `test_build_profile_max_attributes_full_stamina` | `15, 15, 15, 15` | Case B | Ensures high-end cognition derives maximum allowed values. |
| `test_build_profile_max_attributes_half_stamina` | `15, 15, 15, 15, stamina=25/50` | Case C | Ensures fatigue correctly penalizes judgment and evidence quality. |

## Cap-Aware Normalization
Ensures normalization correctly respects dynamic attribute caps.

| Test Name | Input State | Regression Purpose |
| :--- | :--- | :--- |
| `test_build_profile_uses_attribute_caps` | `10, 10 cap` | Ensures normalization uses denominator `cap - 1`. |

## Missing Input Fallbacks
Ensures system stability when certain attributes or caps are missing (e.g., from older entity versions or malformed state).

| Test Name | Input State | Regression Purpose |
| :--- | :--- | :--- |
| `test_build_profile_handles_missing_attributes` | `MissingAttrs()` | Ensures default of `1` for missing attributes. |
| `test_build_profile_handles_missing_caps` | `MissingAttrs()` | Ensures default of `15` for missing caps. |
| `test_build_profile_handles_zero_max_stamina` | `max_stamina=0` | Ensures division-by-zero safety (ratio `1.0`). |

## Determinism
Ensures non-random, stable derivations across identical input states.

| Test Name | Regression Purpose |
| :--- | :--- |
| `test_profile_derivation_is_deterministic_for_same_entity_state` | Prevents flaky strategic reasoning across ticks or replays. |
| `test_profile_derivation_is_independent_of_tick_in_milestone_1` | Ensures tick-independence in the base builder. |
| `test_profile_derivation_does_not_use_rng` | Proves purity against external random sources. |

## Non-Mutation
Ensures the builder is a pure service that does not contaminate authoritative domain truth.

| Test Name | Regression Purpose |
| :--- | :--- |
| `test_build_profile_does_not_mutate_entity_attributes` | Prevents accidentally applying training or decay during a derivation call. |
| `test_build_profile_returns_new_profile_object_each_call` | Prevents shared-state interference for different entities or subsequent calls. |
