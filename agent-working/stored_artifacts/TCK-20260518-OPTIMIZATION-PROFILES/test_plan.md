---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260518-OPTIMIZATION-PROFILES
artifact_type: test_plan
tags: [optimization, profiles]
---

# Test Plan - Scenario-Specific Optimization Profiles

## Verification Strategy
We will verify that standard optimization profiles are fully deterministic, correctly override kernel behaviors, and enforce scenario-specific boundaries.

## Test Suites

### Unit Tests (`tests/unit/optimization/test_optimization_profiles.py`)
- Assert exact profile definitions (`COMBAT_HEAVY`, `MOVEMENT_HEAVY`, etc.).
- Assert `DEBUG_REFERENCE` profile disables unsafe narrowing (`UNSAFE_DISABLED`), compaction (`NONE`), and phase skipping (`NEVER_SKIP`).
- Assert `LOW_MEMORY` profile reduces cache envelopes.
- Assert `OptimizationProfileResolver` correctly resolves default profiles from `RuntimeProfile` hardware classes and flag overrides.

### Integration Tests (`tests/integration/optimization/test_profile_specific_behavior.py`)
- Assert `Kernel` initialized with `DEBUG_REFERENCE` profile executes all 17 phases regardless of clean dirty sets.
- Assert `Kernel` initialized with `MOVEMENT_HEAVY` profile expands movement plan cache envelopes and prioritizes movement candidate budgets under pressure.
- Assert `Kernel` initialized with `LOW_MEMORY` profile triggers earlier cache sweeps and compaction.

## Execution Commands
```bash
pytest -s tests/unit/optimization/test_optimization_profiles.py
pytest -s tests/integration/optimization/test_profile_specific_behavior.py
```
