---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260822-DURABLE-SELECTION-STATE
phase: open
date: 2026-08-22
tags: [hud, architecture]
---

# TCK-20260822-DURABLE-SELECTION-STATE

## Title
Introduce durable selection/navigation state model

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Create explicit, separated durable state for active workspace, camera position, selected entity/location/event, open inspector/tab, and active filter/search query. This fixes a concrete bug: Sidebar.tsx's isBuildingView/isLootView/isSpectating automatic mode-switching silently destroys prior panel context.

## Scope
- Create a single typed, centrally-owned state model (context/reducer under frontend/src/contexts/ or frontend/src/state/) exposing get/set for active workspace, camera position, selection (entity/location/event), open inspector/tab, and filter/search query.
- Fix Sidebar.tsx's isBuildingView/isLootView/isSpectating auto-switch effect (lines 43-49) so that switching into building/loot/spectate mode and back preserves EntityList/EventLog scroll position and the previously active tab, instead of the current one-way reset to 'inspect'.
- Migrate the scattered local useState currently split across App.tsx (selectedBuilding, inspectedLoot), GameCanvas.tsx (pan, zoom), useSimulation.ts (selectedEntityId), and Sidebar.tsx (activeTab) into the new consolidated model, or explicitly document which subset is covered now vs. deferred.
- Add a new automated test that directly exercises the auto-switch path and asserts prior panel context is recoverable after mode reverts.

## Out of Scope
- Adopting a new state library dependency beyond what's needed for this model — no state library exists in package.json today; scope is the model itself, not a broader library migration.
- Wiring a future filter/search feature's UI — only the durable state slot for filter/search query is introduced here, not filter UI/behavior itself.
- Modifying MetadataContext.tsx's existing read-only/fetch-once pattern — it remains a separate concern.

## Acceptance Criteria
- [ ] Switching into building/loot/spectate mode and back preserves EntityList/EventLog scroll position and the previously active tab, instead of Sidebar's current one-way reset (Sidebar.tsx lines 43-49's useEffect currently only ever force-sets activeTab to 'inspect', never restores).
- [ ] Selecting a new entity/building/loot while another was selected does not silently clear unrelated durable state (camera pan/zoom, filter query).
- [ ] A single typed, centrally-owned state model exposes get/set for workspace, camera, selection, open inspector/tab, and filter/search query, replacing the scattered local useState in App.tsx, GameCanvas.tsx, useSimulation.ts, and Sidebar.tsx (or a documented subset thereof).
- [ ] A new automated test directly exercises the auto-switch path and asserts prior panel context is recoverable after mode reverts.

## Related Tickets
- TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION
- TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET — a hard-recommended sequencing dependency (not this ticket's
  own epic, a separate one): that ticket rewrites `useSimulation.ts`'s internal transport and reducer shape
  wholesale. This ticket's own migration of `useSimulation.ts`'s `selectedEntityId` state into the shared
  model should land after that rewrite, not before or in parallel — see this ticket's own Assumptions below.

## Related Docs
- docs/plans/hud_delivery_roadmap.md
- CLAUDE.md

## Related Stored Artifacts
None.

## Related Code Areas
- frontend/src/components/Sidebar.tsx
- frontend/src/App.tsx
- frontend/src/components/GameCanvas.tsx
- frontend/src/hooks/useSimulation.ts
- frontend/src/contexts/MetadataContext.tsx
- frontend/src/test/useSimulation.test.tsx

## Assumptions / Open Questions
- Whether all four scattered state locations (App.tsx, useSimulation.ts, GameCanvas.tsx, Sidebar.tsx) must be fully consolidated now, versus explicitly deferring some subset, is left to implementation judgment as long as the covered/deferred split is explicitly documented.
- No scroll-position state exists anywhere today, so "preserved" requires introducing new state to capture it, not just protecting existing state.
- No writable Context/Zustand/Redux pattern exists yet in the frontend; this ticket establishes the first one, a genuinely new pattern for this codebase.
- Soft sequencing note: TCK-20260822-ENTITY-LIST-SEARCH-RANK (a sibling child ticket of the same parent epic) introduces its own local search/filter query state independently; if both tickets are implemented, doing this one first lets that one plug its query state directly into this model's filter/search slot instead of needing a later migration — not a hard blocking dependency, just a recommended order if both are picked up close together.
- **Cross-epic file collision (2026-08-23), found while reconciling this batch against the live-map
  reconnection epic's own child tickets**: this ticket's own Scope explicitly touches
  `frontend/src/hooks/useSimulation.ts` (extracting `selectedEntityId`) and `frontend/src/components/GameCanvas.tsx`
  (extracting `pan`/`zoom`). `TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET` (a separate epic,
  `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION`) rewrites `useSimulation.ts`'s internals wholesale and explicitly
  states `GameCanvas.tsx`/`useCanvas.ts` stay untouched by that epic — meaning this ticket is the one that
  will actually first modify `GameCanvas.tsx`'s internals, something the reconnection epic's own scope
  assumed wouldn't happen yet. Recommended order: let `TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET` land
  first (avoids redoing the `useSimulation.ts` extraction against pre-rewire internals); this ticket's
  `GameCanvas.tsx` pan/zoom migration has no equivalent hard blocker but should still be done with awareness
  that the reconnection epic's own "read-only reference" assumption about that file no longer holds once
  this ticket lands.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
