# Investigation: Milestone 8 Concurrency Mechanics

## Objective
Establish a bounded, deterministic concurrency model for the resource-safe engine.

## Current State Analysis
- **Execution Model**: Single-threaded, synchronous loop in `Kernel.tick_once`.
- **Work Units**: `WorkItem` contains payload and metadata but no isolated context.
- **State Integrity**: `AuthoritativeState` is a frozen Pydantic model (recursive freeze).
- **Update Path**: `ApplyPath` expects a `StateUpdate` (deltas).

## Concurrency Analysis
1.  **Payload Discipline**: 
    - A "Whole World" clone is forbidden (M8 Rule 1).
    - We must extract entity-local context. 
    - For this milestone, a `WorkerPacket` will include the target `EntityState` and a `NeighborhoodView` (read-only subset of other entities).

2.  **Order and Determinism**:
    - Concurrent execution order is naturally non-deterministic.
    - **Equivalence Rule**: The final `StateUpdate` merged from workers must be sorted by Entity ID before application. This ensures that even if workers race, the commit sequence remains stable across runs given the same seed.

3.  **Resource Ceiling Enforcement**:
    - `max_worker_count`: Controls the `ThreadPoolExecutor`.
    - `max_queue_depth`: Controls the `concurrent.futures` submission limit.
    - **Backpressure**: If the worker pool queue is full, the scheduler must switch to "Immediate" (Local) execution (M8 Rule 5).

## Proposed Structures
```python
@dataclass(frozen=True)
class WorkerPacket:
    tick: int
    seed: int
    subject: EntityState
    environment: Dict[int, EntityState] # Just nearby entities

@dataclass(frozen=True)
class WorkerResult:
    entity_id: int
    update: EntityUpdate
```

## Risks
- **Overhead**: For very small workloads, packetization might be slower than local execution. (Governance must be aware).
- **Thread Safety**: Workers must not access global mutable state. (AuthoritativeState is frozen, so this is handled).
