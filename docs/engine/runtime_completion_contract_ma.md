---
status: active
layer: engine
authority: P1
audience: developer
---

# Phase 4 / Milestone 1: Substrate Baseline Freeze Contract

## 1. Purpose
This document defines the authoritative law for the deterministic single-process engine substrate as it enters the "Phase 4 - Gameplay Attachment" phase. This milestone freezes the substrate to ensure a stable foundation for the first official RPG slices.

## 2. Scope of Milestone A
The scope is limited to the **deterministic single-process runtime path**. 
- **In-Scope**: Kernel phase execution, apply-path closure, deterministic work-order closure, canonical checkpoint proof, authoritative vs non-authoritative mutation boundaries.
- **Out-of-Scope**: Replay hardening, real signal hardening, governor behavior expansion, worker deepening, certification broadening, RPG gameplay attachment.

## 3. Deterministic Single-Process Baseline
The local single-process path is the absolute source of truth for:
- Tick semantics (incremental progression).
- Authoritative apply semantics (mutation purity).
- Work ordering (deterministic selection).
- Checkpoint identity (state integrity).
- Reference behavior for concurrent equivalence testing.

## 4. Kernel Orchestration Law
The `Kernel` MUST execute the following 6 phases in strict sequential order. Each phase has one owner and a defined boundary.

1. **INIT**: `Kernel` - Context setup, Governance, policy evaluation.
2. **SCHEDULING**: `DeterministicScheduler` - Work selection under current policy.
3. **COLLECTION**: `WorkerManager` - Work packetization and execution (Local/Concurrent).
4. **RESOLUTION**: `ApplyPath` - Authoritative deltas application and state generation increment (+1).
5. **CLEANUP**: `Kernel` - Internal metrics and state finalization.
6. **ADVANCEMENT**: `RuntimeStatus` - Signal recording and tick seal.

### Observational Boundary
Phase 7 (**PERSISTENCE**) and all other hooks (Replay, logging, metrics) are **non-authoritative**. They must NOT modify `AuthoritativeState` and should execute after the tick is logically sealed at Phase 6.

## 5. Authoritative Apply Law
- **Singular Mutation**: `ApplyPath.apply_generation` is the ONLY entry point for updating `AuthoritativeState`.
- **Generation-Based**: State transitions produce a new immutable instance (`replace`).
- **No Hidden Aliasing**: Nested structures (entities, properties) must be copied or treated as immutable to prevent side-channel mutation.
- **Sorted Inputs**: All collections (entities, resources, periodic ticks, work debt) MUST be sorted by key before application to ensure order-invariant deltas.

## 6. Deterministic Work-Order Law
The `DeterministicScheduler` MUST select and order work items according to these fixed rules:
1. **Class Hierarchy**:
   - `CRITICAL` (Entity Actions) first.
   - `PERIODIC` (Subsystem Upkeep) second.
   - `DEFERRED` (Debt Draining) third.
   - `OPPORTUNISTIC` (Optional Enrichment) - Gated/Disabled in Milestone A baseline.
2. **Tie-Break Rules**:
   - **Critical**: Sorted by `(-readiness, owner_id)`.
   - **Periodic**: Sorted by `(due_tick, owner_id)`.
   - **Deferred**: Sorted by `owner_id`.
3. **Invariance**: Work selection must depend only on the current `AuthoritativeState` and `GovernorPolicy`, not on previous tick transients or wall-clock time.

## 7. Canonical Checkpoint Law
The `CanonicalStateHasher` defines the proof of integrity.
- **Authoritative Only**: Only fields in `AuthoritativeState` are included. Governance, replay, and status fields are strictly EXCLUDED.
- **Canonical Structure**:
  - `tick`, `seed`, `world_time`: Exact values.
  - `entities`: Sorted by integer ID.
  - `global_resources`: Sorted by string key.
  - `periodic_due_ticks`: Sorted by string key.
  - `work_debt`: Sorted by string key.
  - `rng_checkpoint`: Exact state.
- **Serialization**: Compact JSON (sorted keys, no whitespace) hashed via SHA-256.

## 8. Forbidden Placeholder Behavior
- **No Scheduler Placeholders**: Opportunistic work branches must be explicitly gated or removed if not implemented.
- **No Baseline stubs**: The single-process tick path must not contain `pass` stubs or TODOs that affect ordering or mutation.
- **No Placeholder Tests**: Baseline runtime law tests must have real assertions, not just successful execution of a skeleton.

## 9. Non-Goals
- Real signal truth (B)
- Replay lifecycle safety (C)
- Concurrent equivalence (D)
- Full certification (E)

## 10. Verification Status
This contract is **FROZEN** for Phase 4 Milestone 1 and verified by the following:
- **Test Matrix**: `docs/engine/ma_test_matrix.md`
- **Closure Guard**: `tests/engine/test_milestone_a_closure.py`
- **Integrity Guard**: `tests/engine/test_substrate_freeze_m1.py` (New for Phase 4)

## 11. Completion Confirmation
The `src` substrate is formally frozen for gameplay attachment. Any divergence from this baseline must be logged in `docs/engine/divergence_log_m2.md`.

**Status: FROZEN (PHASE 4 MILESTONE 1)**
**Date: 2026-04-20**
