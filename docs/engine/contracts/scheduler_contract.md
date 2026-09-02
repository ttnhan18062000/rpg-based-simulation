---
status: active
layer: engine
authority: P1
audience: developer
---

# Scheduler Contract — Deterministic Work Selection

## 1. Purpose
This document defines the execution model for the deterministic scheduler. It replaces naive "scan-everything" logic with a formal, deterministic scheduler that prioritizes consistency and semantic integrity.

## 2. Scheduler Scope
- **Input**: Authoritative State, Work Definitions, and Runtime Profile.
- **Output**: An ordered sequence of `WorkItem`s for the current tick.
- **Ordering**: Structural boundaries by class, then class-local deterministic sorting.

## 3. Readiness-Driven Selection Semantics
The scheduler selects entity work according to the readiness threshold (100.0) established by the minimal kernel contract.
- It does **not** redefine eligibility; it only selects eligible entities for the current execution window.
- The readiness threshold gates `ENTITY_ACT`/`ENTITY_MOVE` only. `ENTITY_BRAIN` (cognition/tactical
  evaluation) is explicitly exempt from the readiness gate — it costs 0 readiness and is instead
  governed by the entity's `strategic_intelligence` cadence ("Action Readiness Law, COMB-266",
  `src/engine/scheduler.py`). See `docs/engine/candidate_selection.md` Tier 1 for the full gate table.

## 4. Work Boundaries & Ordering
Execution is organized into ranked buckets. Work in a higher bucket must be selected/ordered before a lower bucket.

### A. Critical Bucket
- **Ordering**: `readiness` (descending), then `entity_id` (ascending).
- **Guarantee**: Non-deferrable. Failure to execute results in a kernel error.

### B. Periodic Bucket
- **Ordering**: `due_tick` (ascending), then `subsystem_id` (ascending).
- **Guarantee**: Executed according to cadence. Postponement recorded as debt.

### C. Opportunistic Bucket
- **Ordering**: `priority_hint` (descending), then `stable_id` (ascending).
- **Guarantee**: Best-effort. Eligible for deferral or drop.

## 5. Tie-Break Rules
- **Entity Identity**: `entity_id` is the primary tie-breaker for all entity-related work.
- **Stable Registration**: Periodic systems must use a stable `subsystem_id` (e.g., string or fixed int).

## 6. Hand-off to Authoritative Execution
The scheduler produces `WorkItems`. The `Kernel` passes these to the `COLLECTION` phase. The scheduler **never** mutates state directly.

## 7. Determinism Guarantees
- Same Seed + Same State + Same Inputs => Same Work Sequence.
- Independent of Python `dict` iteration order or set randomization.
