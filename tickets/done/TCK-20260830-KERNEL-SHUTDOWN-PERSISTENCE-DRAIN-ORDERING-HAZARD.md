---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260830-KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD
phase: done
date: 2026-08-30
tags: [observability, performance]
---

# TCK-20260830-KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD

## Title
`Kernel.shutdown()` Stops `QualityPersistence` Before `EventRecorder`'s Drain Worker, Risking
Silently-Dropped In-Flight Writes

## Status
DONE

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
Resolved during implementation: `QueueDrainWorker.stop()` (`src/observability/queue.py`) is a
**blocking join** (`self._thread.join(timeout=1.0)`), not fire-and-forget. This is what makes the
reorder fix sufficient by itself: once `EventRecorder.shutdown()` returns, the drain worker's
thread is guaranteed to have exited (or the 1.0s join timeout was hit), so no further background
`_run()` loop iteration can race `QualityPersistence.shutdown()` afterward.

## Implementation Notes
Re-verified the hazard against current code (post the sibling batch-flush-visibility hotfix,
which changed `flush_fn` cadence but did not touch shutdown ordering) by direct read of
`src/engine/kernel.py::Kernel.shutdown()`, `src/observability/event_recorder.py`,
`src/observability/queue.py::QueueDrainWorker`, `src/simulation_quality/persistence.py`, and
`src/simulation_quality/quality_hub.py::QualityHub.on_envelope`. Confirmed real and still current:
`Kernel.shutdown()` called `_quality_hub`'s `_persistence.shutdown()` (closing
`QualityPersistence`'s file handle) BEFORE `_event_recorder.shutdown()` (which stops
`EventRecorder`'s background `QueueDrainWorker` thread). The worker calls `quality_fn`
(`QualityHub.on_envelope` → `QualityPersistence.write()`) on its own thread; `QualityPersistence.
write()` silently returns when `self._file_handle is None`, so any envelope the worker (or
`EventRecorder.shutdown()`'s own final manual drain) processed in that window was dropped with no
exception and no log line.

Fix (three coordinated changes, no flush-batching logic touched):
1. `src/engine/kernel.py::Kernel.shutdown()` — moved the `_event_recorder.shutdown()` call to run
   strictly BEFORE the `_quality_hub`/`_persistence` block (previously the reverse). `QueueDrain
   Worker.stop()` is a blocking join (confirmed by direct read, see Assumptions above), so once
   `_event_recorder.shutdown()` returns, no further drain-loop iteration can race persistence
   teardown. As a side benefit, `_quality_hub.get_quality_report()` (called just after, reading
   only in-memory `PillarAccumulator` state) now sees any last-window envelopes' scores too.
2. `src/observability/event_recorder.py::EventRecorder.shutdown()` — its own final manual drain
   (step 2, handling envelopes pushed after the worker's last loop iteration but before `.stop()`
   took effect) previously only wrote to file/stream, never called `quality_fn`. Now mirrors
   `QueueDrainWorker._run()`'s per-envelope dispatch (file write, stream publish, `quality_fn`,
   each exception-isolated) so nothing in that window is dropped from quality persistence either.
3. `src/simulation_quality/persistence.py::QualityPersistence.write()` — defense-in-depth
   backstop: logs a loud warning (event_id/pillar/tick) instead of staying fully silent if `write`
   is ever still called after the file handle has closed, satisfying the ticket's "or otherwise
   fail loudly" alternative even for any future path that might reintroduce a similar race.

Disclosed, not fixed (out of scope for this hotfix, pre-existing/unrelated):
- `docs/simulation_quality/quality_scoring_contract.md:1511` cites `src/engine/kernel.py:964-972`
  for `Kernel.shutdown()`'s `write_report()` call — that line range is stale (points at unrelated
  hard-law-violation-write code) independent of this ticket's edits; not touched, since it isn't
  caused by this change and fixing unrelated doc-citation drift is outside this ticket's scope.
- Two pre-existing, unrelated `tests/simulation_quality/test_grade_regression.py` calibration
  grade-anchor drift failures (`test_urban_political_selfmodel_cognition_isolated_grade_anchor`,
  `..._execution_isolated_grade_anchor`) reproduce identically with this ticket's changes fully
  reverted — confirmed via `git stash`. Matches the exact tick-budget-ceiling-artifact drift class
  `docs/testing/regression_policy.md` §9-10 already documents as a known, disclosed,
  not-code-fixable-via-floor-edit category; deselected from the Test-phase run rather than
  code-fixed, per Gate Integrity.

## Test Summary
`.venv/bin/python3 -m pytest tests/unit/observability/ tests/simulation_quality/ tests/unit/kernel/
tests/unit/engine/ tests/integration/kernel/ tests/integration/observability/
tests/perf/test_persistence_phase_cost.py -m "not slow" --deselect
tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_cognition_isolated_grade_anchor
--deselect
tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_execution_isolated_grade_anchor`
→ **2024 passed, 7 skipped (Redis/live-infra unavailable, pre-existing), 36 deselected (slow-marked
+ the 2 disclosed pre-existing calibration-drift tests above), 0 failed.**

New regression coverage added:
- `tests/simulation_quality/test_kernel_simq_integration.py::test_kernel_shutdown_persists_in_flight_quality_write`
  — end-to-end via a real `Kernel`: deterministically stalls the drain worker before an event is
  queued (no sleep/race), calls `kernel.shutdown()`, and asserts the record reaches
  `quality_scores.jsonl`. Verified this test fails without the `kernel.py` reorder (confirmed via
  `git stash` of just that file) — the write is silently dropped and the new loud warning fires,
  proving both the regression and the backstop.
- `tests/unit/observability/test_event_recorder_quality_fn.py::test_event_recorder_shutdown_final_drain_still_calls_quality_fn`
  — unit-level: stops the worker before an event is queued, so it can only be handled by
  `EventRecorder.shutdown()`'s own final manual drain, and asserts `quality_fn` still fires for it.

## Files Changed
- `src/engine/kernel.py` — reordered `Kernel.shutdown()`: `EventRecorder.shutdown()` now runs
  before the `QualityHub`/`QualityPersistence` teardown block.
- `src/observability/event_recorder.py` — `EventRecorder.shutdown()`'s final manual drain now
  also invokes `quality_fn` per envelope (previously file/stream writes only).
- `src/simulation_quality/persistence.py` — `QualityPersistence.write()` logs a loud warning
  instead of silently no-op'ing when called after its file handle has closed.
- `tests/simulation_quality/test_kernel_simq_integration.py` — new end-to-end regression test.
- `tests/unit/observability/test_event_recorder_quality_fn.py` — new unit-level regression test.
- `docs/engine/kernel.md` — documented the shutdown-ordering rule under `Kernel.shutdown()`.
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-249` updated (`text`/`v2_evidence`/`test_path`)
  via `tools/parity_ledger_writer.py::write_entry()`.

## Completion Summary
Confirmed the disclosed ordering hazard was still real against current code (`Kernel.shutdown()`
closed `QualityPersistence`'s file handle before stopping `EventRecorder`'s drain worker) and
fixed it by reordering the two teardown steps plus routing `EventRecorder.shutdown()`'s own final
drain through `quality_fn`, so an in-flight write during shutdown is now reliably persisted; added
a loud-warning backstop in `QualityPersistence.write()` for defense in depth. Two new regression
tests (one Kernel-level end-to-end, one EventRecorder-level unit test) reproduce the hazard
deterministically (no sleep/race) and both fail without the fix. Scoped test run: 2024 passed, 0
failed. Parity ledger `INFRA-249` updated to reflect the corrected ordering.
