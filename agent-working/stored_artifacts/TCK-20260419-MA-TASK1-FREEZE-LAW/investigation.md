---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260419-MA-TASK1-FREEZE-LAW
artifact_type: investigation
tags: [ma, task1, freeze, law]
---

# Investigation: Milestone A Law Set Freeze

## Current Engine State

### Kernel Phases (`src/engine/kernel.py`)
- Currently implements: `_phase_init`, `_phase_scheduling`, `_phase_collection`, `_phase_resolution`, `_phase_cleanup`, `_phase_advancement`.
- Also has a non-authoritative `_phase_persistence`.
- Phase order is strict: 1-6 are authoritative.

### Authoritative State (`src/core/state.py`)
- Fields: `tick`, `seed`, `world_time`, `entities`, `global_resources`, `periodic_due_ticks`, `work_debt`, `rng_checkpoint`.
- Optimization: Frozen dataclass with slots.

### Apply Path (`src/engine/apply.py`)
- Singular entry point: `ApplyPath.apply_generation`.
- Handles list-based dictionary updates with explicit sorting for determinism.

### Checkpointing (`src/engine/checkpoint.py`)
- Logic: `CanonicalStateHasher.get_hash`.
- Correctly isolates authoritative fields but could be more explicitly documented.

### Scheduler (`src/engine/scheduler.py`)
- Order: Critical (Entities) -> Periodic -> Deferred -> Opportunistic.
- Opportunistic is a placeholder.

## Gaps identified
- The existing `runtime_completion_contract_ma.md` is too brief and lacks details on work-order rules, out-of-scope items, and placeholder prohibitions.
- No `ma_test_matrix.md` exists.
- Core engine files have some law comments but they aren't finalized or consistently formatted.

## Proposed "Law" Definitions

### Tick Phase Ownership
1. **INIT**: `Kernel` - Governance and Policy.
2. **SCHEDULING**: `DeterministicScheduler` - Work selection.
3. **COLLECTION**: `WorkerManager` / `WorkerLogic` - Packet generation and execution.
4. **RESOLUTION**: `ApplyPath` - Aggregate deltas and mutate state.
5. **CLEANUP**: `Kernel` - Metric finalization.
6. **ADVANCEMENT**: `RuntimeStatus` - Seal tick signals.

### Work Ordering Tie-Breaks
- Critical items sorted by `(-readiness, owner_id)`.
- Periodic items sorted by `(due_tick, owner_id)`.
- Deferred items sorted by `owner_id`.

### Placeholder Prohibition
- Opportunistic work MUST be gated or removed in Milestone A.
- Simulator placeholder in `WorkerLogic` is allowed to stay as a "simulation" but must not define core engine semantics.
