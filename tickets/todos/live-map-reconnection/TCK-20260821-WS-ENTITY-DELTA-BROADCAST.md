---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260821-WS-ENTITY-DELTA-BROADCAST
phase: open
date: 2026-08-21
tags: [engine]
---

# TCK-20260821-WS-ENTITY-DELTA-BROADCAST

## Title
Broadcast per-tick entity deltas over the live WebSocket

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
There is no per-tick entity-position broadcast in any shape today -- the live stream only ever carries a minimal summary (tick, world_time, entities_count, maturity, seed), never entity positions or changed/removed lists. The author wants a lightweight delta broadcast (changed/removed/events, driven off the tick loop's existing DirtySet) added onto the existing WebSocket connection, including tick/snapshot_as_of_tick fields so clients can detect drift.

## Scope
- Add a per-tick delta broadcast (changed/removed/events) onto the existing /api/v1/ws connection, driven off the tick loop's existing DirtySet
- Build a slim per-entity dict via StatePresenter/ReadModelCache (new method), never touching AuthoritativeState fields directly in src/api/ws/
- Route the new delta payload through the already-negotiated msgpack format when the client requested msgpack in the handshake, not just JSON
- Include tick and snapshot_as_of_tick fields on every delta message so clients can detect drift
- Preserve stream_ws's existing listener-before-snapshot registration order (already correct); do not reorder it

## Out of Scope
- Any change to the cross-request REST /map,/static fetch vs WS connect-time race -- solved by the new tick/snapshot_as_of_tick fields for client-side drift detection, not by reordering stream_ws
- resource_node/building/chest state changes in the delta (DirtySet only covers entity-domain sets) -- that remains present_map/present_static's job (TCK-20260821-PRESENT-MAP-STATIC)
- Any spatial-subscription/region filtering field or logic (see the separate TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD ticket)

## Acceptance Criteria
- [ ] On a tick where DirtySet.all_dirty_entities is non-empty, /api/v1/ws sends changed (slim dicts for dirty+alive entities) and removed (IDs gone from state.entities), plus tick and snapshot_as_of_tick
- [ ] On a quiet tick (not a heartbeat), no message is sent
- [ ] Registering listener before capturing baseline snapshot means no tick in that window is lost (test: fire a tick between registration and snapshot-capture, confirm reflected not lost)
- [ ] EntitySlim fields are always absolute current values, never deltas (test: two consecutive changed-messages for same entity each independently equal true current state)
- [ ] Delta payload is sent via msgpack when the client's handshake negotiated msgpack, not only JSON

## Related Tickets
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION

## Related Docs
- docs/engine/read_model_service_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/api/ws/stream.py
- src/api/engine_manager.py
- src/core/dirty.py
- src/api/presenters/state_presenter.py
- src/api/read_model_cache.py
- tests/api/test_ws_protocol.py

## Assumptions / Open Questions
- No existing slim-entity cache/dict comparable to V1's _snapshot_to_slim_dict exists -- new StatePresenter/ReadModelCache method needed, not just wiring existing methods
- Bandwidth at 10k-entity scale projects 1.5-5MB/s per viewer even with delta-only encoding -- explicitly out of scope for this ticket to solve (separate gated M3 epic), noted here as context only

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
