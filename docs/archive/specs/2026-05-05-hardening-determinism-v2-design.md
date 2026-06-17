---
status: archive
authority: P2
audience: historical
layer: simulation
original_date: 2026-05-05
---

# Hardening V2 Engine Determinism Phase 2

## Problem
The V2 engine has been successfully hardened for core determinism (Milestone D), but this has caused 224 regressions in the peripheral test suite (Economy, Social, AI, AI). These failures are split between:
1.  **Contract Mismatches**: Tests instantiating `EntityState` directly with legacy arguments (e.g., `position`).
2.  **Logic Shift**: Tests asserting on old readiness drain values (`-100.0` for acting, `-12.5` for wandering).

## Proposed Design

### 1. Systematic Test Migration
- **Action**: Replace all direct `EntityState(...)` calls in the test suite with `V2EntityBuilder(eid).build()`.
- **Reasoning**: Ensures all internal components (Stamina, Navigation, Combat) are initialized with V2 defaults.

### 2. Alignment with Authoritative Law
- **Action**: Update all test assertions to reflect the new "Hardened" values:
    - `MovementMode.WANDER` = 0.5 mult (20.0 drain per tick).
    - `REST` / `ACT` = 0.0 drain (passive gain only).
- **Reasoning**: These values were essential to pass the Bit-Identical Certification (Milestone D).

### 3. Deterministic Throttle
- **Action**: Refine `Kernel._phase_resolution` to sort pending updates by `entity_id` before applying the emergency budget throttle.
- **Reasoning**: Prevents non-deterministic work discard when the tick budget is exceeded, ensuring that if we MUST drop work, we do it in a repeatable way across all runs.

## Approaches
- **Approach A (Recommended)**: Update the test suite to the new hardened values. This prioritizes "Runtime Truth" and deterministic certification.
- **Approach B**: Make the readiness costs configurable per profile to maintain legacy test compatibility. This adds complexity but preserves old tests as-is.

## Verification Plan
- `pytest tests/combat tests/engine tests/rpg tests/tactical tests/ai tests/economy tests/social`
- All suites must achieve 100% pass rate.
- `test_high_pressure_determinism_equivalence` must pass consistently even with high noise injection.
