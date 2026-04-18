# Worker Contract (Milestone 8)

## Purpose
Milestone 8 introduces safe concurrency to the engine. This contract ensures that parallel execution improves throughput without introducing resource blowups (payload leakage) or semantic drift (determinism loss).

## 1. Payload Discipline (Compact Packets)
- **Law**: A worker must never receive a clone of the entire world state.
- **WorkerPacket Structure**:
    - `subject`: The primary `EntityState` the worker is acting upon.
    - `neighbor_view`: A restricted `Dict[int, EntityState]` containing only the immediate context (neighbors) required for the action.
    - `meta`: (tick, world_time, seed).
- **Size Bound**: The `neighbor_view` size must be bounded by the profile or a hard system limit (default $N=10$ neighbors).

## 2. Result Semantics (Compact Results)
- **Law**: A worker must return only the resulting state changes, not a modified world object.
- **WorkerResult Structure**:
    - `entity_id`: The ID of the subject entity.
    - `update`: A typed `EntityUpdate` (e.g., readiness delta, property changes).

## 3. Deterministic Equivalence Law
- **Goal**: Local Execution == Concurrent Execution.
- **Commit Sequence**: The `Kernel` must collect ALL `WorkerResults` in a tick and **sort them by Entity ID** before passing them to the `ApplyPath`.
- **Commutativity**: Worker logic must be designed such that the order of application among different entities does not change the authoritative outcome within a single tick generation.

## 4. Backpressure & Fallback Law
- **Law**: Concurrency must remain subordinate to the resource envelope.
- **Exhaustion Trigger**: If the worker pool queue depth reaches `max_queue_depth`, further work is executed **immediately and synchronously** in the caller thread.
- **Graceful Degradation**: If `max_worker_count` is 0, the engine falls back to a purely sequential execution path.

## 5. Non-Goals
- No distributed workers (network boundaries).
- No shared mutable state between workers.
- No asynchronous result application (results must be joined at tick boundary).
