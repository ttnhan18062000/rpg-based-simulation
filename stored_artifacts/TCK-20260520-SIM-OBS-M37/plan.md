# Implementation Plan - TCK-20260520-SIM-OBS-M37

## Architectural Design

We are implementing a standalone **Live Anomaly Worker Service** that operates as an out-of-process consumer of simulation stream events. The design focuses on reliability, bounded memory usage, and zero-coupling to core authoritative simulation state.

### 1. Worker Lifecycle & Configuration

The worker config class `LiveWorkerConfig` will be added to support:
- `worker_id` (str)
- `stream_backend` (str): `"redis"`, `"in_process"`, or `"null"`
- `stream_name` (str)
- `consumer_group` (str)
- `window_ticks` (int, default=100): The sliding window size in ticks.
- `max_memory_mb` (float/int)
- `enabled_rules` (List[str]): List of active rule class names.
- `output_mode` (str): Destination for emitted anomalies (`"file"`, `"redis"`, or both).

### 2. Rolling Event Window (`RollingEventWindow`)

To prevent memory leaks and keep resource usage bounded, the worker maintains an in-memory `RollingEventWindow`:
- Bounded by `window_ticks`.
- Maps ticks to events occurring in that tick.
- Tracks `current_live_tick` as the maximum tick observed from incoming events.
- Evicts any events with `tick <= current_live_tick - window_ticks` on each event push.
- Bounded position history for entities (to check for stuck navigation).

### 3. Core Live Rules (`LiveAnomalyRule`)

We will implement the following rules inheriting from a base `LiveAnomalyRule`:
1. `HardLawViolationLive`: Matches if any event has `event_category == "hard_law"` or `event_type == "InvariantViolation"`.
2. `NavigationStuckLive`: Keeps track of entity positions over the rolling window. If an entity remains at the exact same coordinates for more than `stuck_ticks` (default=50) while actively moving (or has multiple movement events with the same target/coordinates), it flags a warning.
3. `EventDropRateHigh`: Monitors metrics or specific drop events. If drops exceed a threshold within a sliding tick window, it triggers an alert.
4. `GovernorDegradedLive`: Detects `GovernorModeChanged` events. If the mode stays `DEGRADED` or `SURVIVAL` for more than 5 ticks, it alerts.
5. `CriticalEventObserved`: Triggers on any event with `severity == "CRITICAL"`.

### 4. Deduplication & Alert Cooldown

To avoid flooding alert channels with repetitive warnings (e.g. Navigation Stuck on every tick for the same entity), a deduplication manager is integrated into the worker:
- Uses a unique deduplication key: `f"{rule_name}:{entity_id}:{event_type}"` or `f"{rule_name}:{category}"`.
- Implements a cooldown period (in ticks or seconds) to silence identical alerts.

### 5. Status Flushing & Heartbeats

The worker updates a local file `data/runs/workers/{worker_id}.json` containing:
- `worker_id`, `status` (`"RUNNING"`, `"DEGRADED"`, `"STOPPED"`).
- `heartbeat` (ISO timestamp).
- `events_processed` (cumulative).
- `anomalies_emitted` (cumulative).
- `last_event_tick` (integer).
- `last_error` (string, optional).
- `stream_lag` (derived or estimated).
- `memory_estimate` (RSS in MB).

---

## Proposed Changes

### Component: Observability

#### [MODIFY] [worker.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/anomaly/worker.py)
- Introduce `LiveWorkerConfig` Pydantic model.
- Introduce `LiveAnomalyWorker` class managing:
  - Stream consumption loop.
  - Periodic status flushing.
  - Memory usage check and soft-cap handling.
  - Dynamic rule execution.
- Maintain compatibility with `ExternalAnomalyWorker` (the offline post-run worker).

#### [MODIFY] [rules.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/anomaly/rules.py)
- Add base class `LiveAnomalyRule` and implementation classes:
  - `HardLawViolationLive`
  - `NavigationStuckLive`
  - `EventDropRateHigh`
  - `GovernorDegradedLive`
  - `CriticalEventObserved`

#### [MODIFY] [kernel.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py)
- Update `_phase_observability` to emit `GovernorModeChanged` events when `status.last_transition_tick == tick` to let the worker consume and alert on governor changes.
