---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260418-RESOURCE-KERNEL-M4
artifact_type: plan
tags: [resource, kernel, m4]
---

# Implementation Plan: Resource-Safe Engine Milestone 4

## Purpose
Implement a deterministic scheduler and work-class model.

## Proposed Changes
1. **Documentation**: `scheduler_contract_m4.md`, `m4_work_model_matrix.md`.
2. **Work Types**: `WorkItem`, `WorkClass` (Critical, Periodic, etc.).
3. **Scheduler**: `DeterministicScheduler` selecting by readiness/cadence and sorting by ID.
4. **Integration**: Update `Kernel` to use the scheduler for work selection.

## Task List
- [ ] Draft docs and matrices
- [ ] Implement `work.py` (Types)
- [ ] Implement `scheduler.py` (Core logic)
- [ ] Integrate with `kernel.py`
- [ ] Write `tests/` for scheduling and debt
- [ ] Verify determinism
