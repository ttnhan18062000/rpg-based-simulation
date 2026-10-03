---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260830-HOTFIX-EVENT-RECORDER-BATCH-FLUSH-VISIBILITY-REGRESSION
phase: done
date: 2026-08-30
tags: [observability, performance]
---

# TCK-20260830-HOTFIX-EVENT-RECORDER-BATCH-FLUSH-VISIBILITY-REGRESSION

## Title
Fix `EventRecorder` Batch-Flush Regression: Low-Volume Writes Never Became Visible Mid-Run

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Real regression caught while triaging CI on PR #90 after merging `origin/main` into
`m1-quick-wins` (2026-08-30). `TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION`
changed `EventRecorder._write_envelope_to_file()` to flush every 50 records
(`_FLUSH_INTERVAL`/`_pending_envelope_writes` counter) instead of every record, to fix a real
backpressure/I-O bottleneck in long, high-volume corpus calibration runs. This broke 4 tests in
`tests/simulation_quality/test_traceability_path.py` that inject a single low-volume event and
read `simulation_events.jsonl` mid-run (before `Kernel.shutdown()`) — the batching meant the file
stayed empty until 50 records accumulated or shutdown, so a single injected event never became
visible: `AssertionError: worst_events[0].event_id=... not found in simulation_events.jsonl
(event_ids present: set())`.

## Scope
- Fixed: `QueueDrainWorker` (`src/observability/queue.py`) gained an optional `flush_fn` callback,
  invoked once after each non-empty drain cycle's `for env in envelopes:` loop — not per-record,
  not on an arbitrary record-count threshold.
- `EventRecorder` (`src/observability/event_recorder.py`) wires `flush_fn=self._flush_file` (new
  method) into its `QueueDrainWorker`; `_write_envelope_to_file()` no longer flushes at all
  directly (removed the `_FLUSH_INTERVAL`/`_pending_envelope_writes` counter mechanism entirely —
  superseded by the cycle-based flush, which is both simpler and correctness-preserving: any
  written record becomes visible after at most one drain cycle, ~`_worker.interval_sec` = 0.01s,
  regardless of write volume).
- This still preserves the original fix's I/O-reduction goal: many records written within one
  drain cycle (the realistic high-volume case) still get exactly one flush, not N.
- Updated `tests/unit/observability/test_event_recorder.py`: rewrote
  `test_event_recorder_write_envelope_does_not_flush_every_record` (renamed
  `..._does_not_flush_directly`, since the old counter/threshold assertions no longer apply) and
  added `test_event_recorder_drain_worker_flushes_once_per_nonempty_cycle` (drives the real
  `record()`/queue/worker path, confirms a single event becomes visible on disk without needing 50
  records or a shutdown).

## Out of Scope
- `QualityPersistence`'s own separate flush-batching (`src/simulation_quality/persistence.py`) —
  not driven by `QueueDrainWorker`, no equivalent test failure was found for it in this CI run;
  left as-is unless a similar regression surfaces.
- The `Kernel.shutdown()` ordering hazard already tracked separately by
  `TCK-20260830-KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD`.

## Acceptance Criteria
- `tests/simulation_quality/test_traceability_path.py`'s 4 previously-failing tests pass.
- `tests/unit/observability/test_event_recorder.py` passes (updated tests).
- `tests/perf/test_persistence_phase_cost.py` (the original backpressure-fix regression guard)
  still passes — confirming this change doesn't reintroduce the original I/O bottleneck.

## Related Tickets
- TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION (introduced the regression)
- TCK-20260830-KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD (related, separate)

## Related Code Areas
- src/observability/queue.py (QueueDrainWorker.flush_fn)
- src/observability/event_recorder.py (EventRecorder._flush_file, _write_envelope_to_file)
- tests/unit/observability/test_event_recorder.py
- tests/simulation_quality/test_traceability_path.py

## Assumptions / Open Questions
None.

## Implementation Notes
Implemented and verified: `tests/unit/observability/test_event_recorder.py` (19 tests incl. the 2
rewritten/new ones), `tests/simulation_quality/test_traceability_path.py` (4 previously-failing
tests), `tests/simulation_quality/test_persistence.py`, `tests/perf/test_persistence_phase_cost.py`
all pass. No parity ledger entry needed — this is pure observability-pipeline internals with no
new mechanics/behavior parity claim beyond what `TCK-20260829`'s own `INFRA-397` entry already
covers (that entry's claim about `EventRecorder`'s "_pending_envelope_writes counter" mechanism is
now stale and should be corrected during Parity phase to describe the cycle-based flush instead).

## Test Summary
19 tests in tests/unit/observability/test_event_recorder.py pass; 4 previously-failing tests in
tests/simulation_quality/test_traceability_path.py now pass; tests/perf/test_persistence_phase_cost.py
(original backpressure regression guard) still passes.

## Files Changed
src/observability/queue.py, src/observability/event_recorder.py,
tests/unit/observability/test_event_recorder.py

## Completion Summary
(pending Parity/Verify/Finalize)
