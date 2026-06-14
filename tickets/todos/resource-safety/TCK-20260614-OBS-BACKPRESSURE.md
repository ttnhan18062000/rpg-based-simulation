---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260614-OBS-BACKPRESSURE
phase: open
date: 2026-06-14
tags: [resource-safety, observability, backpressure, event-recorder, performance]
---

# TCK-20260614-OBS-BACKPRESSURE

## Title
Add Observability Backpressure Controller — dynamic mode switching for EventRecorder under pressure

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`EventRecorder` already has a bounded queue and `QueueDrainWorker`, but it still keeps an in-memory event list, creates queue envelopes, reconstructs events for stream publishing, and flushes file writes per event. Under sustained high entity count or anomaly burst, this becomes a memory source. Add a controller that switches observability mode dynamically: NORMAL → PRESSURE → DEGRADED → SURVIVAL. Observability should never kill the simulation.

## Scope
- Add `ObservabilityMode(str, Enum)` in `src/observability/event_recorder.py` (or new `src/observability/mode.py`): `NORMAL`, `PRESSURE`, `DEGRADED`, `SURVIVAL`
- Add `ObservabilityController` class:
  - `current_mode: ObservabilityMode` (default NORMAL)
  - `evaluate(queue_fill_ratio: float, event_rate_per_tick: float) -> ObservabilityMode` — pure function, returns recommended mode
  - Thresholds (configurable, defaults): PRESSURE at 70% queue, DEGRADED at 90%, SURVIVAL at 100%
- Wire controller into `EventRecorder.record_event()`:
  - `NORMAL`: record all events as-is
  - `PRESSURE`: sample INFO events (every Nth, configurable N=5), keep WARNING+
  - `DEGRADED`: drop INFO events entirely, keep WARNING+, batch file writes (flush every 10 events or every tick boundary, whichever comes first)
  - `SURVIVAL`: local counters only — no queue, no file write, no envelope creation; increment `_survival_event_counts: dict[str, int]`
- Expose `observability_status() -> dict`: `{"mode": str, "queue_fill_ratio": float, "events_dropped": int, "survival_counts": dict}`
- Wire into `SubsystemPressureReport` (feeds TCK-20260614-RESOURCE-DASHBOARD)
- Add `EventRecorder.reset_mode()` for test cleanup

## Out of Scope
- Changing the queue drain worker threading model
- Persisting survival-mode counters across runs
- Changing existing `max_events` bound

## Acceptance Criteria
- `ObservabilityMode` enum exists with 4 values
- `ObservabilityController.evaluate()` returns correct mode at each threshold
- `EventRecorder.record_event()` applies mode-appropriate behavior (sample / drop / batch / counter-only)
- In SURVIVAL mode: no queue enqueue, no file write — only `_survival_event_counts` updated
- In PRESSURE mode: INFO events sampled at 1-in-5 (default)
- `observability_status()` returns accurate mode, fill ratio, and drop counts
- Tests: each mode transition produces expected event recording behavior

## Related Tickets
- TCK-20260614-RESOURCE-SAFETY-EPIC (parent)
- TCK-20260614-RESOURCE-BUDGET-GATE (provides queue fill ratio threshold definitions)
- TCK-20260614-RESOURCE-DASHBOARD (reads observability_status())
- TCK-20260614-LIFECYCLE-SUPERVISOR (supervisor monitors mode during shutdown)

## Related Docs
- `docs/architecture/observability_hot_path_safety_contract.md` — CRITICAL authority: section 2 explicitly allows counter increments in hot path (SURVIVAL mode counter-only path is architecturally valid); section 3 forbids deep copies, IO, and lock contention in hot path (DEGRADED batching must flush outside the tick call)
- `docs/parity_ledger/infrastructure.yaml`
- `memory_features.md` (Feature 7)

## Related Code Areas
- `src/observability/event_recorder.py:18` — `EventRecorder` class, `max_events`, queue, `__init__`
- `src/observability/queue.py:87` — `QueueDrainWorker` class
- `src/observability/behavior/worker.py:70` — `BehaviorWorker`

## Assumptions / Open Questions
- Current `EventRecorder` queue fill ratio: `queue.qsize() / max_events` — confirm queue has a `qsize()` method
- Batched file writes in DEGRADED: buffer in `_pending_writes: list`, flush when `len(_pending_writes) >= 10` or at explicit `flush()` call — requires adding a `flush()` call at tick boundary in Kernel
- Sampling in PRESSURE: use `_press_event_counter % sample_rate == 0` counter per-instance

## Implementation Notes
- `ObservabilityController.evaluate()` is a pure function (no side effects) — easy to test in isolation
- Mode transitions should be logged once at INFO level when mode changes (not every event)
- SURVIVAL counters: key by event type string, value is count — zero overhead path

## Test Summary
- `tests/unit/observability/test_obs_backpressure.py` (new):
  - `test_normal_mode_records_all_events`
  - `test_pressure_mode_samples_info_events`
  - `test_degraded_mode_drops_info_events`
  - `test_survival_mode_no_queue_enqueue`
  - `test_survival_mode_increments_counters`
  - `test_mode_transition_at_correct_thresholds`
  - `test_observability_status_accurate`
- Run: `pytest tests/unit/observability/ -v`

## Files Changed
_(filled after implementation)_

## Completion Summary
_(filled after implementation)_
