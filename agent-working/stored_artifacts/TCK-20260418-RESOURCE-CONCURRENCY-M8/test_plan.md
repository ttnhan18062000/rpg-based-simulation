---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260418-RESOURCE-CONCURRENCY-M8
artifact_type: test_plan
tags: [resource, concurrency, m8]
---

# Test Plan: Milestone 8 Concurrency

## 1. Worker Contract Validation
- **Packet Isolation**: Verify that a worker receives only the specific entity state and context it needs.
- **Result Integrity**: Verify that worker results follow the strict `EntityUpdate` structure.
- **Bound Enforcement**: Verify that payload size (number of entities) stays within contract limits.

## 2. Concurrency Bounds
- **Thread Count**: Verify the `WorkerManager` respects `max_worker_count` from the profile.
- **Queue Limits**: Verify that submitting beyond `max_queue_depth` triggers backpressure or immediate execution.
- **Graceful Cleanup**: Verify that the `WorkerManager` shuts down cleanly without leaving orphaned threads.

## 3. Deterministic Equivalence (CRITICAL)
- **Local vs Worker**: Run a set of work items locally, then run the same set via the worker manager. Verify the final `StateUpdate` (and resulting `AuthoritativeState`) are identical.
- **Race Resistance**: Artificially delay some workers to ensure that the collection logic still produces the same ordered result.
- **Seed Stability**: Verify that concurrent execution using the same seed produces bit-identical results across multiple runs.

## 4. Fallback-to-Local
- **Exhaustion Trigger**: Force the worker pool queue to saturate and verify that subsequent work is executed in the main thread without failure.
- **Explicit Disable**: Set `max_worker_count=0` and verify the engine gracefully executes everything locally.

## Tests to Implement
- `tests/engine/test_worker_contract.py`
- `tests/engine/test_worker_bounds.py`
- `tests/engine/test_worker_determinism.py`
- `tests/engine/test_worker_fallback.py`
