# TCK-20260518-OPTIMIZATION-PROFILES

## Title

Scenario-Specific Optimization Profiles (Milestone 20)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement scenario-aware `OptimizationProfile` definitions (`COMBAT_HEAVY`, `MOVEMENT_HEAVY`, `RESOURCE_HEAVY`, `METROPOLIS`, `LOW_MEMORY`, `DEBUG_REFERENCE`) to tailor engine optimization budgets, indexing modes, compaction levels, cache size limits, and phase skipping behaviors to specific simulation workloads.

## Scope

- Create `src/config/optimization_profiles.py` defining `OptimizationProfile`, `IndexingMode`, `CompactionLevel`, and `PhaseSkipPolicy`.
- Define standard pre-configured optimization profiles (`COMBAT_HEAVY`, `MOVEMENT_HEAVY`, `RESOURCE_HEAVY`, `METROPOLIS`, `LOW_MEMORY`, `DEBUG_REFERENCE`).
- Implement `OptimizationProfileResolver` to map `RuntimeProfile` to a default `OptimizationProfile` while allowing scenario or flag overrides.
- Connect `OptimizationProfile` inside `Kernel` (`src/engine/kernel.py`), feeding its configurations into `CacheBudgetPolicy`, `PhaseDependencyGraph`, and `PhaseBudgetGovernor`.
- Implement unit test suite `tests/unit/optimization/test_optimization_profiles.py`.
- Implement integration test suite `tests/integration/optimization/test_profile_specific_behavior.py`.
- Update `perf_plan_v2.md`.

## Out of Scope

- Milestone 21 Optimization Documentation and Invariant Ledger.

## Acceptance Criteria

- All standard optimization profiles are fully deterministic and accessible.
- `DEBUG_REFERENCE` profile correctly disables unsafe narrowing (`UNSAFE_DISABLED`), disables compaction (`NONE`), and disables phase skipping (`NEVER_SKIP`).
- `LOW_MEMORY` profile correctly reduces optimization cache size limits and tightens background sweep intervals.
- `MOVEMENT_HEAVY` profile correctly prioritizes movement candidate budgets and cache envelopes.
- `RESOURCE_HEAVY` profile correctly prioritizes spatial grid versions and query optimization.

## Related Tickets

- TCK-20260518-CACHE-REGISTRY (Milestone 19)

## Related Docs

- `perf_plan_v2.md`
- `docs/engine/performance_contract.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260518-OPTIMIZATION-PROFILES/`

## Related Code Areas

- `src/config/optimization_profiles.py` (NEW)
- `src/core/state.py`
- `src/engine/kernel.py`
- `src/engine/apply.py`
- `src/engine/phase_graph.py`
- `src/engine/phase_governor.py`
- `src/engine/governor.py`

## Assumptions / Open Questions

- None.

## Implementation Notes

- Added `_opt_profile` and `_force_full_scan` to `AuthoritativeState` fields to ensure correct propagation across state generations produced by `ApplyPath`.
- Integrated `OptimizationProfileResolver` to dynamically resolve profiles from hardware class or dictionary override flags.

## Test Summary

- `tests/unit/optimization/test_optimization_profiles.py` (5 tests passed in 0.28s)
- `tests/integration/optimization/test_profile_specific_behavior.py` (3 tests passed in 0.73s)
- Entire optimization test suite passed (103 tests passed in 1.33s)

## Files Changed

- `src/config/optimization_profiles.py` (NEW)
- `src/core/state.py` (MODIFIED)
- `src/engine/kernel.py` (MODIFIED)
- `src/engine/apply.py` (MODIFIED)
- `src/engine/phase_graph.py` (MODIFIED)
- `src/engine/phase_governor.py` (MODIFIED)
- `src/engine/governor.py` (MODIFIED)
- `tests/unit/optimization/test_optimization_profiles.py` (NEW)
- `tests/integration/optimization/test_profile_specific_behavior.py` (NEW)

## Completion Summary

- Successfully established the scenario-specific optimization profile architecture, integrated standard profiles into the simulation engine (`Kernel`, `PhaseDependencyGraph`, `PhaseBudgetGovernor`), and verified full runtime behavior compliance.
