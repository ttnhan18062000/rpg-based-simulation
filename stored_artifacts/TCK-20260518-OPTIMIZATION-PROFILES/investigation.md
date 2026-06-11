---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260518-OPTIMIZATION-PROFILES
artifact_type: investigation
tags: [optimization, profiles]
---

# Investigation - Scenario-Specific Optimization Profiles

## Context
The V2 RPG simulation engine executes distinct types of workloads (e.g. dense metropolitan interactions, large-scale pathfinding, intense combat encounters, resource harvesting). Running a single global optimization configuration across all scenarios creates sub-optimal performance tradeoffs. Milestone 20 introduces scenario-aware optimization profiles.

## Current Architecture
- `RuntimeProfile` (`src/config/profiles.py`) defines hardware envelopes (RAM MB, CPU %, max queue depth).
- `CacheBudgetPolicy` (`src/engine/cache_registry.py`) defines cache envelopes and tick sweep intervals.
- `PhaseBudgetGovernor` (`src/engine/phase_governor.py`) dynamically computes sub-phase candidate budgets.
- `PhaseDependencyGraph` (`src/engine/phase_graph.py`) schedules or skips phases based on dirty domain sets.

## Proposed Architecture
- Introduce `OptimizationProfile` in `src/config/optimization_profiles.py` encapsulating scenario-specific optimization parameters:
  - `movement_budget` and `strategic_budget` (integers)
  - `background_sweep_interval` (integer ticks)
  - `indexing_mode` (`DEFAULT`, `EXACT_NARROW`, `UNSAFE_DISABLED`)
  - `compaction_level` (`NORMAL`, `AGGRESSIVE`, `NONE`)
  - `phase_skip_policy` (`ALLOW_SKIP`, `CONSERVATIVE`, `NEVER_SKIP`)
  - `cache_budget_policy` (`CacheBudgetPolicy`)
- Define standard profiles: `COMBAT_HEAVY`, `MOVEMENT_HEAVY`, `RESOURCE_HEAVY`, `METROPOLIS`, `LOW_MEMORY`, `DEBUG_REFERENCE`.
- Connect to `Kernel` to override default settings and pass down to phase execution, cache sweeps, and governor evaluations.
