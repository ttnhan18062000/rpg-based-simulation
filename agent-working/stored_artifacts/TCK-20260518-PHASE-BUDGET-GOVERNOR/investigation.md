---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260518-PHASE-BUDGET-GOVERNOR
artifact_type: investigation
tags: [phase, budget, governor]
---

# Investigation: Adaptive Phase Budget Governor

## Problem Statement
During high-load scenarios (e.g. 1000+ entities with dense spatial interactions or complex strategic AI), specific pipeline phases like `movement` or `strategic` can experience latency spikes exceeding per-tick compute budgets (e.g., 16ms for 60 TPS). Currently, candidate selection (e.g., `budget=50` in `StrategicWorkQueue`) is fixed or unmanaged dynamically at runtime based on actual per-phase p95 timing.

## Codebase Analysis
1. **`GovernorPolicy`** (`src/engine/policy.py`):
   Currently returns basic mode flags (NORMAL, CONSTRAINED, DEGRADED, SURVIVAL) and cadence multipliers. It lacks granular budget parameters (`strategic_budget`, `movement_budget`, `background_sweep_interval`, `compaction_level`).
2. **`StrategicWorkQueue`** (`src/systems/strategic_systems/work_queue.py`):
   Currently accepts `budget=50` as a default. Tier 1-6 are urgent/dirty work, while Tier 7 is a background sweep across all entities. Under compute pressure, Tier 7 background sweep should be throttled or spaced out (increasing sweep interval), while keeping Tier 1-6 intact.
3. **`MovementCandidateSelector`** (`src/engine/candidate_selector.py`):
   Currently selects all valid entities with active navigation targets. Under movement phase pressure, non-urgent entities (e.g., wandering or low-priority movement) should be deferred or throttled to respect `movement_budget`.
4. **`AuthoritativeApplyPipeline`** (`src/engine/pipeline.py`):
   Executes 17 phases sequentially. Under apply phase pressure, stronger compaction can be enabled, and optional phases can be given tighter budgets.

## Requirements
1. **`PhaseBudgetGovernor`**: Monitors recent phase execution costs (p95 latency or rolling averages), current tick cost, work debt, and candidate counts.
2. **Dynamic Budgets**: Computes `strategic_budget`, `movement_budget`, `background_sweep_interval`, and `scan_policy` (e.g. `"EXACT_DIRTY"`, `"THROTTLED"`, `"FULL"`).
3. **Correctness Preservation**: Critical phases (`death`, `resource_transactions`, `quest_rewards`, `inventory_capacity`) must never be deferred or skipped, even in SURVIVAL mode.
