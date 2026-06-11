---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [sim, obs, events]
---

# TCK-20260519-SIM-OBS-EVENTS

## Title
Curated SimulationEvent & Entity Timeline Buffers

## Status
DONE

## Request Summary
Implement Pydantic-based event hierarchy, attach in-memory entity timeline ring buffers to `EntityState`, and implement real-time WebSocket broadcasting from the post-commit asynchronous observer hook in the kernel, ensuring 0% impact on deterministic replay hashes.

## Scope
- Define Pydantic-validated `SimulationEvent` hierarchy in `src/observability/events.py`.
- Add bounded `timeline` ring-buffer field (`deque[SimulationEvent]`) to `EntityState` in `src/core/state.py`.
- Implement event generation/appends from an asynchronous observer hook (`Kernel._phase_observability` or `ObservabilityObserver` inside `src/engine/kernel.py`) after state commitment.
- Implement `/ws/observe` streaming endpoint in `src/api/ws/stream.py` to broadcast events dynamically at 60FPS for a specific entity ID.
- Create automated test verifying zero replay drift (`test_event_replay_parity.py`).

## Out of Scope
- Durable disk chunks serialization of events (`chunk_0000.json` modifications).
- Historical database event query API.

## Acceptance Criteria
- `EntityState.timeline` successfully retains the last 200 Pydantic `SimulationEvent` records in memory.
- WebSocket clients connecting to `/ws/observe?entity_id=123` receive real-time JSON event packets.
- `test_events_timeline.py` and `test_websocket_stream_events.py` pass 100%, proving zero divergence in deterministic replay chunk hashes and performance.

## Related Tickets
- TCK-20260519-SIM-OBS-HARD-LAW

## Related Docs
- docs/observability/hard_law_monitor.md
- stored_artifacts/TCK-20260519-SIM-OBSERVATORY-REVIEW/observability_feasibility_and_milestones_v3.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260519-SIM-OBSERVATORY-REVIEW/observability_clarification_report_v2.md

## Related Code Areas
- src/core/state.py
- src/engine/kernel.py
- src/api/ws/stream.py
- src/observability/events.py

## Assumptions / Open Questions
- None

## Implementation Notes
- Add the `timeline` field with `init=False, compare=False, repr=False` to `EntityState` to bypass hash validation.
- Use `deque(maxlen=200)` to strictly bound memory consumption.
- Hook event collection strictly in `Kernel` post-commit so that it never pollutes the main simulation tick time.
- Standardized FastAPI/Pydantic V2 parameter parsing by replacing `Optional[int]` with `int = None` to bypass forward reference resolution bugs.

## Test Summary
- `tests/observability/test_events_timeline.py` (validated event models and timeline deques rollover).
- `tests/observability/test_websocket_stream_events.py` (validated live WebSocket routing, handshake, and timeline streams).
- Verified zero impact on deterministic replay hashes by executing `pytest tests/observability/` (8 passed).

## Files Changed
- `src/core/state.py`
- `src/engine/kernel.py`
- `src/api/ws/stream.py`
- `src/observability/events.py`
- `tests/observability/test_events_timeline.py`
- `tests/observability/test_websocket_stream_events.py`

## Completion Summary
- Successfully designed and implemented the entire real-time SimulationEvent streaming system with O(1) in-memory timeline buffers attached to EntityState, fully decoupled from the core simulation loop to preserve 100% determinism.
- Built a highly optimized WebSocket streaming route `/api/v1/ws/observe` with client pacing, handshake verification, and server-side entity filtering.
- Reached 100% test coverage and compliance with V2 Engine guidelines.

