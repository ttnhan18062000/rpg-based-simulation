---
ticket_id: TCK-20260614-OBS-BACKPRESSURE
date: 2026-06-14
---

# Plan: TCK-20260614-OBS-BACKPRESSURE

## Step 1 — Add ObservabilityMode enum to event_recorder.py
- `ObservabilityMode(str, Enum)`: NORMAL, PRESSURE, DEGRADED, SURVIVAL

## Step 2 — Add ObservabilityController class
- `evaluate(queue_fill_ratio, event_rate_per_tick=0.0) -> ObservabilityMode`
- Thresholds: PRESSURE>=0.70, DEGRADED>=0.90, SURVIVAL>=1.00
- Pure function, no side effects

## Step 3 — Add controller fields to EventRecorder.__init__()
- `_obs_controller`, `_obs_mode`, `_press_sample_rate=5`,
  `_press_event_counter`, `_survival_event_counts`, `_events_dropped_by_mode`

## Step 4 — Update EventRecorder.record()
- Compute fill ratio from `queue.get_size() / queue.max_size`
- Call `_obs_controller.evaluate(fill)` and log mode transitions
- SURVIVAL: increment `_survival_event_counts`, return immediately
- DEGRADED: drop severity < WARNING
- PRESSURE: sample severity < WARNING at 1-in-`_press_sample_rate`
- Otherwise: existing eviction + buffer + queue logic

## Step 5 — Add observability_status() and reset_mode()
- `observability_status()` returns mode, queue_fill_ratio, events_dropped, survival_counts
- `reset_mode()` clears mode state for test cleanup

## Step 6 — Tests (28 tests in test_obs_backpressure.py)
- ObservabilityMode enum (2), ObservabilityController.evaluate() (8),
  Normal/Pressure/Degraded/Survival mode behavior (12),
  observability_status() (4), reset_mode() (1), plus status initial/reflects (2+1)

## Files Changed
- `src/observability/event_recorder.py`
- `tests/unit/observability/test_obs_backpressure.py` (new)
- `docs/parity_ledger/infrastructure.yaml` (INFRA-199 added)
