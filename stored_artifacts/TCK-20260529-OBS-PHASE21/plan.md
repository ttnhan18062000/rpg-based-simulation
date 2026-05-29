# Plan - TCK-20260529-OBS-PHASE21

## Goal
Implement Phase 21 (Non-Blocking Event Emission Pipeline) to ensure that the main simulation loop can emit telemetry events without being delayed by I/O, serialization, or downstream service outages.

## Approach
1. **Define Models**:
   - Define `ObservabilityEventEnvelope` inside `src/observability/events.py` (or a dedicated models file).
   - Ensure the envelope is lightweight and avoids large references to full entity or world states.
2. **Implement Queue**:
   - Implement `BoundedObservabilityQueue` with thread-safe operations in `src/observability/queue.py`.
   - Create a non-blocking `try_push(envelope)` method.
   - Support a default drop policy: when full, drop low-priority events instead of blocking or throwing.
3. **Integrate into Hot Path**:
   - Hook the queue into `EventRecorder` / `EventExtractor` execution path.
   - Set up an async worker or draining process that pulls events from the queue and handles their I/O.
4. **Implement Isolation**:
   - Wrap workers in try-except clauses to isolate downstreams (e.g. file writing, Redis backend) from crashing the simulation thread.
5. **Add Verification Tests**:
   - Implement unit, integration, and performance budget tests.
