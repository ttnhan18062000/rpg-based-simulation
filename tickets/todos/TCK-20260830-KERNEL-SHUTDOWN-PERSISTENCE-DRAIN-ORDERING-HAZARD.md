---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260830-KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD
phase: open
date: 2026-08-30
tags: [observability, performance]
---

# TCK-20260830-KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD

## Title
`Kernel.shutdown()` Stops `QualityPersistence` Before `EventRecorder`'s Drain Worker, Risking
Silently-Dropped In-Flight Writes

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Filed from `TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION`'s implementation. That
ticket fixed two real persistence-phase performance bugs (a redundant synchronous
`ReplayManager` re-serialization, and unconditional per-record `.flush()` calls in
`QualityPersistence`/`EventRecorder`) but disclosed, without fixing, a separate ordering hazard in
`Kernel.shutdown()`: `QualityPersistence.shutdown()` runs before `EventRecorder`'s background
drain-worker has fully stopped. In that window, any in-flight write submitted to the drain worker
can silently no-op rather than being written or erroring loudly.

## Scope
- Confirm the exact ordering in `Kernel.shutdown()` (or wherever the two components' shutdown
  sequence is actually orchestrated) and the drain-worker's stop semantics.
- Reorder shutdown so `EventRecorder`'s drain worker is fully stopped/drained before
  `QualityPersistence` (or any other persistence sink sharing the same hazard) tears down, or
  otherwise make the in-flight-write-during-shutdown case fail loudly instead of silently
  no-op'ing.
- Add a regression test that reproduces the ordering hazard (an in-flight write during shutdown)
  and confirms it's no longer silently dropped.

## Out of Scope
- The persistence-phase performance fixes already landed by the filing ticket — do not re-touch
  `ReplayManager`/`QualityPersistence`/`EventRecorder`'s flush-batching logic.
- Any change to `CanonicalStateHasher`'s per-tick cadence — already a documented, verified parity
  contract (INFRA-223), not in scope here either.

## Acceptance Criteria
- A write submitted during the shutdown window is either reliably persisted or the shutdown path
  surfaces a clear error/log — not a silent no-op.
- A regression test demonstrates this.
- Existing observability/persistence shutdown tests still pass.

## Related Tickets
- TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION (filing ticket, disclosed this
  finding)

## Related Code Areas
- src/engine/kernel.py (shutdown orchestration)
- src/observability/event_recorder.py (drain worker)
- src/simulation_quality/persistence.py (QualityPersistence.shutdown)

## Assumptions / Open Questions
Exact drain-worker stop semantics (blocking join vs. fire-and-forget) not yet confirmed — to be
established during implementation.

## Implementation Notes
(Not yet implemented — filed and deferred.)

## Test Summary
(Not yet implemented.)

## Files Changed
(Not yet implemented.)

## Completion Summary
(Not yet implemented.)
