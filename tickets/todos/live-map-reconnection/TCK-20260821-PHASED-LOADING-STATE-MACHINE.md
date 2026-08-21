---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260821-PHASED-LOADING-STATE-MACHINE
phase: open
date: 2026-08-21
tags: []
---

# TCK-20260821-PHASED-LOADING-STATE-MACHINE

## Title
Replace opaque CONNECTING status with a phased loading state machine

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Today the frontend's SimStatus type has only a single CONNECTING state covering the entire pre-live sequence, its fetch-failure path retries silently forever with no visible error, and GameCanvas shows one generic "Loading map..." string with no phase information. The author wants a real state machine (INITIALIZING -> FETCHING_WORLD_DATA -> CONNECTING_LIVE -> SYNCING -> READY) plus a visible error state after repeated failures, without touching GameCanvas.tsx/useCanvas.ts themselves.

## Scope
- Extend SimStatus to a superset covering INITIALIZING -> FETCHING_WORLD_DATA -> CONNECTING_LIVE -> SYNCING -> READY (plus existing RUNNING/PAUSED/STOPPED), starting at INITIALIZING not bare CONNECTING
- Make SYNCING correspond exactly to the entity-delta broadcast ticket's connect-time atomic-handoff window (first live snapshot received), not a newly invented mechanism
- Bound loadInitial()'s fetch-retry loop with a retry counter; after N failures, transition to a new visible ERROR-class status instead of retrying silently forever
- Add a new wrapper component (mounted in App.tsx around GameCanvas) rendering phase-specific loading text/UI per non-READY status and a distinct error UI
- Update frontend/src/test/useSimulation.test.tsx's initial-status assertion (status==='CONNECTING') and other affected assertions for the new enum

## Out of Scope
- GameCanvas.tsx and useCanvas.ts -- remain byte-for-byte unmodified (verifiable via git diff)
- Building the underlying WS connect sequence -- this ticket only wires status transitions to it
- Whether the EventSource-style reconnect loop (separate from loadInitial's fetch retry) also gets bounded-retry treatment is an explicit open decision this ticket must state, not silently resolve

## Acceptance Criteria
- [ ] SimStatus extended to superset covering INITIALIZING/FETCHING_WORLD_DATA/CONNECTING_LIVE/SYNCING/READY (plus existing RUNNING/PAUSED/STOPPED), starts at INITIALIZING not bare CONNECTING, transitions to READY only once first live snapshot (SYNCING handoff) has landed
- [ ] loadInitial()'s catch tracks a bounded retry counter (not unconditional setTimeout forever); after N failures, status transitions to new visible ERROR-class status
- [ ] new wrapper component (mounted in App.tsx around GameCanvas) renders phase-specific loading text/UI per non-READY status and distinct error UI, GameCanvas.tsx/useCanvas.ts remain byte-for-byte unmodified
- [ ] existing SSE-stream/entity-processing behavior in useSimulation.test.tsx continues to pass unmodified aside from initial-status assertion

## Related Tickets
- TCK-20260821-WS-ENTITY-DELTA-BROADCAST
- TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- frontend/src/hooks/useSimulation.ts
- frontend/src/components/GameCanvas.tsx
- frontend/src/App.tsx
- frontend/src/test/useSimulation.test.tsx

## Assumptions / Open Questions
- whether the second, separate EventSource-reconnect infinite-retry loop also gets bounded-retry+visible-error treatment, or is deliberately left alone, is not resolved by investigation and should be an explicit decision in this ticket
- no existing frontend retry-count utility exists anywhere -- new local state, keep minimal
- layer registered as new value `frontend` (registries/layer_registry.jsonl) since no existing entry covers frontend/React client code distinct from backend engine/systems layers; this layer should be reused by sibling tickets in the live-map-reconnection epic

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
