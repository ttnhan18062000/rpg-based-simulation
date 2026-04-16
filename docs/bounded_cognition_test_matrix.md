# Test Matrix: Bounded Strategic Cognition

This matrix identifies the test suite segments that prove the operational integrity of the bounded cognition engine.

## Unit Tests

| Test Class / Method | Domain | Proves |
| :--- | :--- | :--- |
| `test_cognition_derivation` | `CognitionCapacityBuilder` | Correct mapping of INT/WIS/PER/CHA to profile limits. |
| `test_cognition_fatigue_penalty` | `CognitionCapacityBuilder` | Low stamina correctly reduces `judgment_stability`. |
| `test_candidate_build_bounding` | `AIBrain` | The candidate list is sliced correctly based on `active_slice_limit`. |
| `test_overload_flag_trigger` | `AIBrain` | `is_overloaded` is set when candidates are dropped. |

## Integration Tests

| Test Module | Domain | Proves |
| :--- | :--- | :--- |
| `test_event_interpretation.py` | Event logic | Bounded agents drop lower-priority interpretation consequences. |
| `test_strategic_brain_integration.py` | Strategic logic | High-stability agents resist project switches; low-stability agents drift. |
| `test_social_reasoning_bounding.py` | Social logic | Quality of social contracts and recruitment is bounded by character capacity. |

## E2E Regression Tests

| Test Case | Scenario | Proves |
| :--- | :--- | :--- |
| `test_intel_capacity_replay` | Headless Scenario | Cognitive metrics correctly survive serialization into `replay.json`. |
| `test_intel_capacity_graph` | Headless Scenario | `cognition_profile` node appears in graph export with correct attributes. |
| `test_intel_capacity_determinism` | Dual Run | Identical seeds produce bit-identical cognitive artifacts across runs. |

## Visibility Tests

| Component | Proves |
| :--- | :--- |
| `AIPresenter` | API schema contains `capacity`, `usage`, and `overload` fields. |
| `EntityInspector` | CLI output renders color-coded budget bars and overload alerts. |

## Non-Goals (What is NOT proven)
- **RNG sensitivity**: Tests do not prove behavior under varying RNG (RNG is strictly seeded for determinism).
- **Long-term Balance**: Tests prove the *bounds*, not whether a budget of 5 is "fun" for a 50-hour campaign.
