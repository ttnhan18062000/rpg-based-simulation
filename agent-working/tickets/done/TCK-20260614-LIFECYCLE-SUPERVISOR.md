---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-LIFECYCLE-SUPERVISOR
phase: done
date: 2026-06-14
tags: [resource-safety, lifecycle, workers, shutdown, observability]
---

# TCK-20260614-LIFECYCLE-SUPERVISOR

## Title
Add Worker Lifecycle Supervisor — systematic shutdown reporting and orphan detection

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Promoted Kernel.shutdown() to produce a machine-readable `ShutdownReport` with worker
accounting, pending replay flushes, survival event counts, and open file handle count.
BehaviorWorker threads are now joined during shutdown. `shutdown_report()` accessor added
for post-mortem inspection.

## Scope
- `ShutdownReport` dataclass in `src/core/lifecycle.py`
- `Kernel.__slots__` extended with `_workers_started`, `_last_shutdown_report`
- `Kernel.__init__()` initializes `_workers_started` from obs worker count
- `Kernel.shutdown()` builds and caches `ShutdownReport`; return type preserved (`ShutdownResult`)
- `Kernel.shutdown_report()` accessor
- BehaviorWorker thread join by thread name with 1s timeout
- INFRA-200 parity entry

## Out of Scope
- Changing WorkerManager internals
- Process-wide file handle auditing beyond psutil
- Automatic worker restart

## Acceptance Criteria
- [x] `ShutdownReport` with 7 fields exists in lifecycle.py
- [x] `Kernel.shutdown()` returns `ShutdownResult` (unchanged) and caches `ShutdownReport`
- [x] `workers_started == workers_stopped` in normal shutdown
- [x] Non-zero `pending_replay_flushes` generates a warning
- [x] BehaviorWorker thread joined during shutdown
- [x] 14 tests pass

## Related Tickets
- TCK-20260614-RESOURCE-SAFETY-EPIC (parent)
- TCK-20260614-OBS-BACKPRESSURE (survival_event_counts source)
- TCK-20260614-REPLAY-BACKPRESSURE (pending_replay_flushes source)

## Related Docs
- `docs/engine/kernel.md`
- `docs/parity_ledger/infrastructure.yaml` — INFRA-200

## Related Stored Artifacts
- `stored_artifacts/TCK-20260614-LIFECYCLE-SUPERVISOR/`

## Related Code Areas
- `src/core/lifecycle.py` — ShutdownReport
- `src/engine/kernel.py` — shutdown(), shutdown_report()
- `tests/unit/engine/test_lifecycle_supervisor.py`

## Assumptions / Open Questions
- BehaviorWorker is not kernel-owned, so it's found by thread name. If no such thread
  is running, the loop body never executes (safe).
- `open_file_handles` uses psutil with fallback to -1 on import/call failure.

## Implementation Notes
- `__slots__` required explicit extension — missed slot causes AttributeError at runtime.
- `_workers_started` counts QueueDrainWorker (EventRecorder._worker) only; WorkerManager
  workers are compute-on-demand and not tracked here.
- Return type of `shutdown()` unchanged to preserve 5+ existing callers.

## Test Summary
14 tests in `tests/unit/engine/test_lifecycle_supervisor.py`. All pass.
52 pre-existing kernel unit tests: all pass (1 pre-existing intermittent ERROR in teardown).

## Files Changed
- `src/core/lifecycle.py` — ShutdownReport dataclass
- `src/engine/kernel.py` — __slots__, _workers_started, updated shutdown(), shutdown_report()
- `tests/unit/engine/test_lifecycle_supervisor.py` — new, 14 tests
- `docs/parity_ledger/infrastructure.yaml` — INFRA-200 added

## Completion Summary
`ShutdownReport` produced and cached by `Kernel.shutdown()`. BehaviorWorker threads joined
by name. Worker accounting tracks EventRecorder._worker. Survival counts and replay flush
metrics captured. 14 tests pass. INFRA-200 added to parity ledger.
