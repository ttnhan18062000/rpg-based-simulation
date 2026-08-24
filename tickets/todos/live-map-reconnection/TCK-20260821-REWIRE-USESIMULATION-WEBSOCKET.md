---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET
phase: open
date: 2026-08-21
tags: []
---

# TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET

## Title
Rewire useSimulation.ts from SSE to the real /api/v1/ws WebSocket contract

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
useSimulation.ts was built against a backend contract (SSE transport, query-param-aware /state, generic control dispatch) that the real V2 backend never implements, so the renderer shows nothing. The author wants useSimulation.ts (only) swapped from EventSource to a real WebSocket client speaking the actual /api/v1/ws handshake, keeping the existing changed/removed reducer logic, and mapping pause/resume calls onto the two real existing control routes instead of a generic dispatcher.

## Scope
- Replace useSimulation.ts's EventSource('/api/v1/stream') usage with a real WebSocket client to /api/v1/ws
- Send the required {"type":"handshake","format":"json"|"msgpack"} message as the first outgoing message before processing any data; pick and document one format explicitly
- Keep existing changed/removed reducer logic unchanged, adapting it to consume the new {tick,changed,removed,events,snapshot_as_of_tick} delta shape
- Map pause/resume calls onto the two real existing routes: single POST /api/v1/control/pause, single POST /api/v1/control/resume -- remove the generic dispatcher
- On WS close/error, reconnect (mirroring the current onerror/setTimeout retry behavior)
- Rewrite frontend/src/test/useSimulation.test.tsx against a mocked WebSocket (both existing tests are written against the old EventSource/SSE contract and are not reusable as-is)

## Out of Scope
- GameCanvas.tsx and useCanvas.ts -- not modified by this ticket
- Any change to /speed or /clear_events call sites
- Building the state-machine loading UI (separate TCK-20260821-PHASED-LOADING-STATE-MACHINE ticket)

## Acceptance Criteria
- [ ] hook opens WebSocket to /api/v1/ws (not EventSource/'/api/v1/stream'), sends handshake as first outgoing message before processing any data
- [ ] changed/removed/tick/events reducer logic behaviorally unchanged (ported test assertions: entities.length, entities[0].id, aliveCount, tick)
- [ ] pause maps to single POST /api/v1/control/pause, resume to single POST /api/v1/control/resume, no generic dispatcher introduced
- [ ] on WS close/error, hook reconnects (mirrors current onerror/setTimeout retry)
- [ ] GameCanvas.tsx and useCanvas.ts not modified (diff scope limited to useSimulation.ts + its test file)

## Related Tickets
- TCK-20260821-WS-ENTITY-DELTA-BROADCAST
- TCK-20260821-REST-MAP-STATIC-STATS
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- frontend/src/hooks/useSimulation.ts
- frontend/src/types/api.ts
- frontend/src/test/useSimulation.test.tsx
- src/api/ws/stream.py
- src/api/server.py
- frontend/src/components/GameCanvas.tsx
- frontend/src/hooks/useCanvas.ts

## Assumptions / Open Questions
- msgpack vs json handshake format choice is open -- this ticket should pick one explicitly and document why
- sendControl's current generic signature is used only for pause/resume today per scope, but call sites in GameCanvas.tsx/ControlPanel.tsx should be grepped before removing the generic path, even though those files aren't edited
- **Cross-epic sequencing note (2026-08-23), found while reconciling this batch against `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION`'s child tickets**: `TCK-20260822-DURABLE-SELECTION-STATE` and `TCK-20260822-ENTITY-LIST-SEARCH-RANK` (a separate epic, unrelated to this one in scope) both also list `frontend/src/hooks/useSimulation.ts` under their own Related Code Areas -- one extracts `selectedEntityId` state out of it into a shared model, the other reads/diffs its data for entity ranking. Neither of those tickets existed when this one was scoped. This ticket should land first: it rewrites `useSimulation.ts`'s internal transport and reducer shape (EventSource->WebSocket, old delta shape->new `{tick,changed,removed,events,snapshot_as_of_tick}` shape) wholesale, including a full rewrite of its test file -- any of that pair's work done against the pre-rewire hook would need re-doing against the post-rewire internals. Not a scope change to this ticket itself, just a recommended implementation order for whoever picks up either batch.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
