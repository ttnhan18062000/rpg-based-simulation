# Plan - Scenario-Specific Optimization Profiles

## Objectives
Implement scenario-aware `OptimizationProfile` definitions and integrate them into the simulation runtime to dynamically adapt optimization mechanisms to specific simulation workloads.

## Implementation Steps
1. Create `src/config/optimization_profiles.py` defining `OptimizationProfile`, `IndexingMode`, `CompactionLevel`, `PhaseSkipPolicy`, and standard profiles (`COMBAT_HEAVY`, `MOVEMENT_HEAVY`, `RESOURCE_HEAVY`, `METROPOLIS`, `LOW_MEMORY`, `DEBUG_REFERENCE`).
2. Implement `OptimizationProfileResolver` to resolve default optimization profiles based on `RuntimeProfile` hardware class and scenario tags.
3. Update `Kernel.__init__` (`src/engine/kernel.py`) to resolve and store `self._opt_profile` and initialize `CacheRegistry` with its `cache_budget_policy`.
4. Update `PhaseDependencyGraph.should_run_phase` (`src/engine/phase_graph.py`) to respect `PhaseSkipPolicy.NEVER_SKIP` and `CONSERVATIVE`.
5. Update `PhaseBudgetGovernor.evaluate` (`src/engine/phase_governor.py`) to incorporate baseline movement and strategic budgets from `OptimizationProfile`.
6. Implement comprehensive unit tests (`tests/unit/optimization/test_optimization_profiles.py`).
7. Implement comprehensive integration tests (`tests/integration/optimization/test_profile_specific_behavior.py`).
8. Verify exact determinism parity across standard profiles.
