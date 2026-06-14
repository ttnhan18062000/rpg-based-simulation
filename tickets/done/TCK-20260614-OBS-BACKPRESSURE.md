---
status: done
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260614-OBS-BACKPRESSURE
phase: done
date: 2026-06-14
tags: [resource-safety, observability, backpressure, event-recorder, performance]
---

# TCK-20260614-OBS-BACKPRESSURE

## Title
Add Observability Backpressure Controller — dynamic mode switching for EventRecorder under pressure

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`EventRecorder` has no mechanism to shed load under pressure. Added a four-mode dynamic
controller (NORMAL → PRESSURE → DEGRADED → SURVIVAL) that evaluates queue fill ratio
on every `record()` call and applies mode-appropriate event filtering with zero IO on the
hot path in SURVIVAL mode.

## Scope
- `ObservabilityMode(str, Enum)`: NORMAL, PRESSURE, DEGRADED, SURVIVAL
- `ObservabilityController.evaluate()`: pure function, thresholds 0.70/0.90/1.00
- `EventRecorder.record()` mode-aware filtering
- `observability_status()` and `reset_mode()` methods
- INFRA-199 parity entry

## Out of Scope
- Changing queue drain worker threading model
- Persisting survival-mode counters across runs
- Changing existing `max_events` bound

## Acceptance Criteria
- [x] `ObservabilityMode` enum with 4 values
- [x] `ObservabilityController.evaluate()` returns correct mode at each threshold
- [x] `record()` applies correct behavior per mode (sample/drop/counter-only)
- [x] SURVIVAL: no queue push, no buffer append, only `_survival_event_counts` incremented
- [x] PRESSURE: INFO sampled at 1-in-5 (default)
- [x] `observability_status()` returns accurate mode, fill ratio, drop counts
- [x] 28 tests pass

## Related Tickets
- TCK-20260614-RESOURCE-SAFETY-EPIC (parent)
- TCK-20260614-RESOURCE-BUDGET-GATE (queue fill ratio baseline)
- TCK-20260614-RESOURCE-DASHBOARD (reads observability_status())
- TCK-20260614-LIFECYCLE-SUPERVISOR (supervisor monitors mode during shutdown)

## Related Docs
- `docs/architecture/observability_hot_path_safety_contract.md`
- `docs/parity_ledger/infrastructure.yaml` — INFRA-199

## Related Stored Artifacts
- `stored_artifacts/TCK-20260614-OBS-BACKPRESSURE/`

## Related Code Areas
- `src/observability/event_recorder.py`
- `tests/unit/observability/test_obs_backpressure.py`

## Assumptions / Open Questions
- `_press_event_counter` is not lock-protected — safe because `record()` is called
  from the single-threaded simulation tick write path.

## Implementation Notes
- SURVIVAL path: `dict.get()` + dict assignment only — no locks, no allocation beyond
  the dict entry; satisfies `observability_hot_path_safety_contract.md` §2.
- File writes remain in `QueueDrainWorker` (off hot path); DEGRADED "batching"
  is achieved by not pushing INFO to queue, naturally reducing queue pressure.
- Mode transitions logged at INFO level (once per change, not per event).

## Test Summary
28 tests in `tests/unit/observability/test_obs_backpressure.py`. All pass.
2 pre-existing `test_event_recorder.py` tests: all pass (no regression).

## Files Changed
- `src/observability/event_recorder.py` — ObservabilityMode, ObservabilityController, updated record()
- `tests/unit/observability/test_obs_backpressure.py` — new, 28 tests
- `docs/parity_ledger/infrastructure.yaml` — INFRA-199 added

## Completion Summary
Four-mode dynamic backpressure controller wired into EventRecorder.record(). Queue fill
ratio drives mode; SURVIVAL path is allocation-free on the hot path. 28 tests verify
all mode transitions and behaviors. INFRA-199 added to parity ledger.
