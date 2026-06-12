---
status: active
layer: engine
authority: P1
audience: developer
---

# Task/Result/Update Substrate Contract

This document defines the authoritative substrate contract for the `src` engine. It formalizes the flow of information from scheduling to authoritative application.

## 1. The Three-Stage Authoritative Flow

The engine substrate operates in three distinct stages per tick:

1.  **Intent Selection (Task Packets)**: The `DeterministicScheduler` selects which entities or subsystems are allowed to "think" this tick.
2.  **Semantic Execution (Worker Results)**: Specialized executors process the tasks in isolation, producing proposed state changes.
3.  **Authoritative Refinement (Refined Updates)**: The `AuthoritativeApplyPipeline` consolidates all results, resolves conflicts, and enforces global invariants.

---

## 2. Task Packet Contract (WorkItem/WorkerPacket)

**Purpose**: Carry read-only context to a worker for deterministic execution.

### Task Shape
- `owner_id`: The ID of the entity or subsystem.
- `work_kind`: The semantic type of work (e.g., `MOVEMENT`, `INTERACTION`).
- `subject`: A frozen snapshot of the primary entity's state.
- `neighbor_view`: A sorted list of nearby entities (Deterministic Context).
- `payload`: A dictionary of intent-specific parameters.

### Constraints
- **Immutability**: The `subject` and `neighbor_view` are frozen.
- **Isolation**: Workers must not access global state; they must rely solely on the packet content.

---

## 3. Worker Result Contract (WorkerResult)

**Purpose**: Return granular, authoritative deltas linked to the source task.

### Result Shape
- `entity_id`: Must match the subject of the source packet.
- `update`: An `EntityUpdate` record containing proposed field changes.
- `status`: SUCCESS, FAILURE, or TIMEOUT.
- `work_debt_update`: (Optional) Metadata for subsystem scaling.

### Constraints
- **One Result Per Entity**: Each entity is limited to one authoritative result per tick (Option A Protocol).
- **No Side Effects**: Workers must not mutate any state; they only return the `update` record.

---

## 4. Update Domain Rules (StateUpdate)

**Purpose**: Represent the consolidation of all tick results before application.

### Domain Separation
Updates are grouped into logical domains to prevent cross-contamination during partial rejection:
- **Entity Domain**: Position, HP, Readiness, Kind, Navigation, Task.
- **World Domain**: Region hazard levels, Calamity intensity.
- **Building Domain**: Building HP, Functional status.

### Refinement Law
The `AuthoritativeApplyPipeline` is the ONLY place where updates are transformed or rejected based on multi-agent conflicts (e.g., occupancy).

---

## 5. Verification Path
This contract is enforced by:
- `src/core/protocol_validator.py`: Static validation of batches.
- `tests/engine/test_worker_integrity.py`: Runtime boundary proofs.
- `tests/engine/test_authoritative_apply.py`: Refinement/Apply correctness.
