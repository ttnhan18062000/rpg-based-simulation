---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260821-EPIC-LIVE-MAP-RECONNECTION
phase: open
date: 2026-08-21
tags: [architecture, api-design]
---

# TCK-20260821-EPIC-LIVE-MAP-RECONNECTION

## Title
Reconnect the existing player-facing live map renderer to the real V2 backend (map data,
static objects, live entity positions, pause/resume) — no HUD/info-display work

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`frontend/src/components/GameCanvas.tsx` + `frontend/src/hooks/useCanvas.ts` are a real, already-built
live map renderer (pan/zoom, cached minimap, fog-of-war, region/location labels, building icons, entity
dots, hover tooltips). It renders nothing today because its data layer, `useSimulation.ts`, was built
against a contract the real V2 backend never implements: a different streaming transport (SSE vs. the
real WebSocket), 5 missing REST routes, unsupported query params on an existing route, and — the deeper
finding — no per-tick entity-position broadcast exists in any shape today. The user explicitly chose to
reconnect this existing frontend (not build a new client against the separate server-owned rendering core
idea) and explicitly scoped this to the live map only: "focus on rendering live map first, don't need to
sculpt the HUD for information displaying now, using simple is enough." Full investigation and root-cause
trace: `docs/plans/live_map_reconnection_epic.md`.

## Scope
- New `StatePresenter` methods serializing existing live `AuthoritativeState` fields (`terrain`,
  `buildings`, `resource_nodes`, `chests`, `ground_items`) into the frontend's `MapData`/`StaticData`
  shapes.
- A new lightweight per-tick entity-delta broadcast (using the tick loop's existing `DirtySet` tracking)
  carrying `{tick, changed, removed, events}` over the real `/api/v1/ws` WebSocket connection.
- New REST routes: `/api/v1/map`, `/api/v1/static`, `/api/v1/stats`.
- Rewire `useSimulation.ts` (only) from `EventSource`/`/api/v1/stream` to the real WebSocket protocol at
  `/api/v1/ws`; map its `sendControl` calls onto the two real existing `/control/pause`/`/control/resume`
  routes.
- A real performance-validation pass once connected: observe actual FPS/update latency against a live
  running world, reported per `docs/engine/performance_contract.md`'s scoped-claims discipline (runtime
  profile, hardware class, scenario) — not assumed, not a bare number. Any real optimization need this
  surfaces is a separate future ticket, not designed here.

## Out of Scope
- Any new UI panel beyond what `GameCanvas.tsx` already renders (its minimap + locations panel is
  map-navigation, not HUD, and stays as-is).
- Wiring the real, already-existing HUD components (`Sidebar.tsx`, `EntityList.tsx`, `EventLog.tsx`,
  `InspectPanel.tsx`, `ControlPanel.tsx`, `BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`,
  `Legend.tsx`) to real data — they exist as code, rendered by `App.tsx` alongside `GameCanvas`; connecting
  their specific information-display needs is deferred per direct user instruction.
- `/api/v1/speed` UI polish (route wiring can ride along if trivial; no new widget) and `/api/v1/clear_events`
  (route + UI both deferred, tied to the World Log HUD feature).
- Any speculative rendering-performance rewrite not driven by this epic's own real measurement pass.
- Building a new client against `docs/plans/world_rendering/idea_world_rendering_core.md`'s "Option C"
  server-owned rendering core — explicitly ruled out this session in favor of reconnecting the existing
  frontend.

## Acceptance Criteria
- [ ] A documented, ordered child-ticket breakdown exists (this ticket + its plan doc) that a later
      `/create-tickets` pass can use directly
- [ ] Each child ticket, when opened, references this epic and `docs/plans/live_map_reconnection_epic.md`
- [ ] No implementation happens directly on this epic ticket or its plan doc

## Related Tickets
- `TCK-20260820-EPIC-WORLD-RENDERING-CORE` — a distinct, unrelated sibling system (server-side batch/QA
  measurement renderer for visual-quality scoring, not a player-facing live view). Neither epic depends on
  the other.

## Related Docs
- `docs/plans/live_map_reconnection_epic.md` — this epic's full plan doc and investigation trail
- `docs/engine/contracts/frontend.md` — the existing "Known gap (2026-07-16)" this epic's investigation
  confirms and extends
- `docs/plans/world_rendering/idea_world_rendering_core.md` — the alternative architecture explicitly not
  chosen
- `docs/engine/performance_contract.md` — scoped-claims methodology for the performance-validation
  acceptance criterion
- `tickets/done/infra-04-realtime-state-streaming.md` — the historical ticket whose incomplete step 4 is
  this epic's root cause

## Related Stored Artifacts
None.

## Related Code Areas
- `src/api/presenters/state_presenter.py` — new `present_map`/`present_static` methods
- `src/api/read_model_cache.py`, `src/api/engine_manager.py` — per-tick delta broadcast plumbing
- `src/api/ws/stream.py` — the real WebSocket protocol the frontend must speak
- `src/core/state.py` (`AuthoritativeState`) — source of the real `terrain`/`buildings`/`resource_nodes`/
  `chests`/`ground_items` runtime data
- `src/api/server.py` — new REST route registration
- `frontend/src/hooks/useSimulation.ts` — the only frontend file this epic's child tickets touch
- `frontend/src/types/api.ts` — target shapes (`MapData`, `StaticData`, `SimulationStats`, `WorldState`)
- `frontend/src/components/GameCanvas.tsx`, `frontend/src/hooks/useCanvas.ts` — read-only reference for
  the target contract; not modified by this epic

## Assumptions / Open Questions
- Where the frontend's spatial `Region` data (center/radius/locations/difficulty) actually lives at
  runtime is not yet confirmed — not `AuthoritativeState.regions` (that's a governance/political concept).
  Most likely the compiled world spec (`data/worlds/{id}/world.yaml`), loaded once at startup — needs
  confirmation in the relevant child ticket's own Investigate phase.
- Where cumulative `total_spawned`/`total_deaths` counters come from, if anywhere, is not yet confirmed —
  not present in `V2EngineManager`'s current metrics snapshot or `StatePresenter`. May need new counters.
- Whether the new per-tick delta broadcast extends the existing `/ws` payload or registers as a separate
  message type is an implementation-detail decision left to that child ticket's own investigation.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
