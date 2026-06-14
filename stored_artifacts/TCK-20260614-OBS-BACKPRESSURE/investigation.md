---
ticket_id: TCK-20260614-OBS-BACKPRESSURE
date: 2026-06-14
---

# Investigation: TCK-20260614-OBS-BACKPRESSURE

## Existing EventRecorder Architecture

`EventRecorder.record()` appends to an in-memory `events: List[SimulationEvent]` buffer,
creates an `ObservabilityEventEnvelope`, and calls `queue.try_push()`. The
`QueueDrainWorker` asynchronously drains the queue, calling `_write_envelope_to_file()`
and `_publish_envelope_to_stream()`.

Queue fill ratio = `queue.get_size() / queue.max_size`. `BoundedObservabilityQueue` exposes
`get_size()` (lock-protected) and `max_size` (set in `__init__`). No lock needed to read
`max_size` (immutable after init).

## Hot Path Safety

`docs/architecture/observability_hot_path_safety_contract.md` §2 allows counter increments
in hot path. §3 forbids deep copies, IO, and lock contention in hot path.

SURVIVAL mode counter path satisfies §2: `dict.get()` + `dict[k] = v` — pure in-memory,
no locks, no allocation beyond the dict entry.

For DEGRADED: file writes happen in QueueDrainWorker (off hot path). Not pushing to queue
in DEGRADED for INFO events is sufficient; the "batch" requirement is satisfied by
the existing async drain pipeline.

## SimulationEvent Validation

`entity_id` must be `int`, `event_category` must be one of the 13 allowed literals.
Tests must use `entity_id=1` and `event_category="combat"` (or other valid literal).

## Sampling Counter Thread Safety

`_press_event_counter` is not lock-protected. It is only written inside `record()`, which
is called from the simulation tick (single-threaded write path). Read-only in tests.
No lock needed.

## Existing pressure_report() Unchanged

The existing `pressure_report()` (INFRA-194) reports queue occupancy vs budget threshold.
This ticket adds a separate `observability_status()` and dynamic mode controller — they
coexist and serve different consumers (Governor reads pressure_report; dashboard reads
observability_status).
