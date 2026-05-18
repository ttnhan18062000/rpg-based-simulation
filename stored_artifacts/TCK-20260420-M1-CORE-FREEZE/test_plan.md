# Test Plan - Core Substrate Freeze (M1)

## Strategy
We will use a combination of existing law tests and new "integrity" tests to verify that the substrate is indeed frozen and compliant with the Milestone 1 contract.

## New Tests

### `tests/engine/test_substrate_freeze_m1.py`
- **Baseline Invariance**: Verify that `Kernel.tick_once` calls the 6 phases in the exact order: INIT, SCHEDULING, COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT.
- **Schema Lock**: Verify the field names and types of `PressureSignals`. Any change will require a deliberate contract break.
- **Authoritative Purity**: Verify `AuthoritativeState` slots/fields only contain simulation-relevant data.
- **Apply Exclusivity**: Use a mock/spy to ensure `ApplyPath.apply_generation` is the only point of state transition in the loop.

## Regression Tests
- **Milestone A Closure**: Ensure all existing single-process tests pass.
- **Determinism Suite**: Ensure bit-identical outcome between sequential and concurrent executors still holds.
- **Certification Gate**: Ensure the final gate for substrate trust still passes.

## Test Matrix
| Category | Requirement | Test |
|----------|-------------|------|
| Determinism | Bit-identical equivalence | `test_determinism_suite.py` |
| Authority | Mutate-only through Apply | `test_substrate_freeze_m1.py` |
| Observability | Stable signal schema | `test_substrate_freeze_m1.py` |
| Lifecycle | Real runtime truth | `test_final_gate.py` |

## Acceptance Criteria
- 100% pass rate in the above suite.
- Zero `TODO`s in `Kernel` or `Apply` affecting authoritative logic.
