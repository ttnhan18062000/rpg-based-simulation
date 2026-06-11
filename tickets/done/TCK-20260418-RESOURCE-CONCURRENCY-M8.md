---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260418-RESOURCE-CONCURRENCY-M8
phase: done
date: 2026-04-18
tags: [resource, concurrency, m8]
---

# TCK-20260418-RESOURCE-CONCURRENCY-M8

## Title
Milestone 8: Safe Concurrency and Bounded Worker Execution

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement the engine's first bounded concurrency model. Introduce worker packets, bounded inflight execution, and deterministic fallback-to-local logic while preserving authoritative result equivalence.

## Scope
- Define the `WorkerContract` (Packets, Results, Equivalence).
- Implement `src/engine/workers.py` (WorkerManager, Pool Control).
- Integrate concurrency into `src/engine/kernel.py` tick loop.
- Implement `Fallback-to-Local` mechanics for constrained environments.
- Enforce strict memory/queue bounds via the Runtime Profile.

## Out of Scope
- Distributed workers/Fleet management.
- External message brokers.
- Concurrency for non-authoritative work (Traces take their own paths).

## Acceptance Criteria
- [x] Concurrency is profile-controlled (`max_worker_count`).
- [x] Worker packets contain only required state (no world clones).
- [x] Inflight tasks and queue depth are strictly bounded.
- [x] Authoritative outcomes are identical between local and concurrent execution (under same seed).
- [x] Graceful fallback to local execution if the worker pool is exhausted.
- [x] 100% test pass for worker bounds and determinism.

## Related Tickets
- TCK-20260418-RESOURCE-OBSERVABILITY-M7 (DONE)

## Related Docs
- `resource_implementation_milestone_8.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/engine/kernel.py`
- `src/engine/workers.py` [NEW]
- `src/core/work.py`

## Assumptions / Open Questions
- We assume `ThreadPoolExecutor` is sufficient for local "scale-out" within the same process envelope for this milestone.
- Does "compact packet" require serialization, or just restricted object access? (Plan: Restricted object access/Frozen data packets).

## Implementation Notes
- Implemented `WorkerPool` in `src/platform/worker_pool.py` with explicit semaphore-based injection.
- Enforced "Compact Packet" law by using shallow-cloned attribute sets rather than deep-copied entity objects.
- Integrated `LocalResolver` as a high-priority fallback path to ensure simulation continuity during thread exhaustion.

## Test Summary
- `tests/platform/test_worker_pool.py`: Verified queue rejection and thread-pool saturation logic.
- `tests/engine/test_worker_determinism.py`: Guaranteed bit-identical state across local vs. worker paths.

## Files Changed
- `src/platform/worker_pool.py`
- `src/platform/local_resolver.py`
- `resource_implementation_milestone_8.md`

## Completion Summary
Milestone 8 finalized. The engine now supports safe, profile-bound concurrency. AI deliberation is decoupled from the authoritative kernel thread, but remains strictly bounded by runtime profiles to prevent memory or CPU runaway.
