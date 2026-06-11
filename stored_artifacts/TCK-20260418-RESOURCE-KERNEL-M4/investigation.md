---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260418-RESOURCE-KERNEL-M4
artifact_type: investigation
tags: [resource, kernel, m4]
---

# Investigation: Resource-Safe Engine Milestone 4

## Goal
Implement a deterministic scheduler and work-class model to replace naive execution.

## Architectural Decisions

### 1. Work Item Representation
- Instead of the Kernel calling entities directly, it will receive a list of `WorkItem` objects from the `Scheduler`.
- `WorkItem` will include: `owner_id`, `work_class`, `payload`, and `priority`.

### 2. Work Classes
- **CRITICAL**: Simulation-critical (e.g., character actions).
- **PERIODIC**: Cadence-based (e.g., hourly economy tick).
- **OPPORTUNISTIC**: Non-critical enrichment (e.g., visual effect calculation).
- **DEFERRED**: Critical work postponed to the next available slot.

### 3. Deterministic Ordering
- Selection order: `(WorkClass, Priority, OwnerID)`.
- Tie-breaker: `OwnerID`.
- This ensures bit-identical results across runs.

### 4. Integration with Kernel
- `Kernel.tick_once()`:
  - Phase 2 (SCHEDULING) now calls `Scheduler.select_work(state, profile)`.
  - Phase 3 (COLLECTION) executes the selected `WorkItems` to produce `StateUpdates`.

### 5. Bounded Work Debt
- Deferred work will be stored in a `BoundedBuffer` with a `REJECT` policy. If debt is too high, the simulation must technically "halt" or "error" as per this milestone's focus on boundedness before adaptive degradation.

## Technical Risks
- **Scheduling Overhead**: Managing a queue every tick could be slower.
- **Solution**: Keep the scheduler lean. Avoid complex priority heaps; simple sorted lists are fine for Milestone 4 levels of complexity.
- **Semantic Drift**: The scheduler must use the same `readiness` threshold as Milestone 2.
