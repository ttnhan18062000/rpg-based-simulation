---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, api-design]
---

# Epic Plan — Reconnect the Existing Player-Facing Live Map to the Real V2 Backend

**Tracking ticket:** `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION`
**Source:** direct code investigation (2026-08-21), confirming and extending
`docs/engine/contracts/frontend.md`'s existing "Known gap (2026-07-16)" callout.
**Priority:** P1 — user-prioritized, reconnect-existing-frontend chosen explicitly over building a new
client against the separate server-owned rendering core idea (`docs/plans/world_rendering/idea_world_rendering_core.md`).

## Problem

`frontend/src/components/GameCanvas.tsx` + `frontend/src/hooks/useCanvas.ts` are a real, sophisticated,
already-built live map renderer: layered canvases, pan/zoom, a cached off-screen minimap terrain buffer
(redrawn only on fog-of-war change, not every frame), resizable/zoomable minimap, region/location labels,
building icons, entity dots, hover tooltips, click-to-jump navigation. This is not a stub. It renders
nothing today because its data layer, `frontend/src/hooks/useSimulation.ts`, was built against a contract
the real V2 backend never implements.

**Verified precisely, not assumed** (full grep of every `@router.get/post/websocket` and `@app.get/post`
decorator across `src/api/routes/*.py`, `src/api/ws/*.py`, `src/api/server.py`,
`src/simulation_quality/api/routes.py`):

1. **Transport mismatch.** `useSimulation.ts` opens `new EventSource('/api/v1/stream')` (Server-Sent
   Events). The real backend only streams over **WebSocket** at `/api/v1/ws`
   (`src/api/ws/stream.py::stream_ws`), with a custom JSON handshake
   (`{"type":"handshake","format":"json"|"msgpack"}`). No `/api/v1/stream` SSE route exists anywhere.
2. **5 REST routes genuinely missing**: `/api/v1/map`, `/api/v1/static`, `/api/v1/stats`, `/api/v1/speed`,
   `/api/v1/clear_events` — confirmed absent from the entire route surface. Matches
   `docs/engine/contracts/frontend.md`'s 2026-07-16 callout, still accurate.
3. **`/api/v1/state` exists but ignores query params.** The frontend calls
   `/state?since_tick=X&selected=Y`; the real handler (`src/api/server.py` ~L168) takes no params and
   always returns `manager.get_state()` in full.
4. **No generic control dispatch.** `useSimulation.ts`'s `sendControl(action: string)` POSTs to
   `/api/v1/control/{action}` for an arbitrary action string; the real backend only has
   `/api/v1/control/pause` and `/api/v1/control/resume` (`src/api/server.py` ~L203-211).
5. **The deeper gap: no per-tick entity-position broadcast exists at all, in any shape.** Traced through
   `V2EngineManager._notify_listeners()` → `stream_ws`'s `on_tick` callback: every tick, listeners receive
   `self._latest_snapshot`, which is exactly `StatePresenter.present_minimal(state)` =
   `{tick, world_time, entities_count, maturity, seed}` (`src/api/presenters/state_presenter.py` L14-22,
   `src/api/read_model_cache.py::get_minimal_summary`). **No entity positions, no changed/removed lists,
   no map or static-object data are pushed over the live stream today, in any form** — this is a bigger
   gap than "wrong transport," it's "the live broadcast literally carries no renderable payload yet."
6. **The map/static data these routes need does exist in real runtime state**, just unserialized for API
   consumption: `AuthoritativeState` (`src/core/state.py` ~L1083) carries `terrain: Dict[tuple[int,int],
   str]` (the real per-tile grid), `buildings`, `resource_nodes`, `chests`, `ground_items` — all live,
   tick-mutated fields. No `StatePresenter` method currently serializes any of them into the RLE/JSON
   shapes `frontend/src/types/api.ts` expects (`MapData`, `StaticData`). `AuthoritativeState.regions`
   (`RegionState`: owner_faction_id/influence/hazard_level — a governance concept) is **not** the same
   thing as the frontend's spatial `Region` type (center_x/center_y/radius/locations/difficulty) — that
   spatial data most likely lives only in the compiled world spec (`data/worlds/{id}/world.yaml`, per this
   session's separate worldgen investigation), not in live tick state. Flagged as an open question below,
   not resolved here.
7. **Root cause / history**: `tickets/done/infra-04-realtime-state-streaming.md` (a historical V1-era
   ticket) planned this exact WS/SSE refactor, including "Refactor the React `useSimulation` hook" as its
   own step 4. Only the backend half shipped, under V2, as WebSocket (not the SSE shape that ticket
   sketched) — the frontend step was never done, leaving `useSimulation.ts` stuck on the old contract ever
   since.

**Bottom line**: this is not a thin "add 5 routes" fix. The renderer is done; the read-model/broadcast
layer needs real (but bounded, non-HUD) new work: new presenter methods to serialize existing runtime
data into the missing shapes, plus a new lightweight per-tick entity-delta broadcast (the tick loop
already tracks a `DirtySet` of changed entities each tick — `dirty_set.all_dirty_entities` — so this is
additive serialization work, not new tracking infrastructure).

## Explicitly ruled out this session

Building a new client against `docs/plans/world_rendering/idea_world_rendering_core.md`'s "Option C"
server-owned rendering core — that doc's own live-streaming mode is "deferred in full... no
implementation plan exists yet." The user chose the faster, already-mostly-built reconnect path instead.

## Not related to this epic

`TCK-20260820-EPIC-WORLD-RENDERING-CORE` (batch/QA measurement-only PNG renderer feeding the visual-quality
scoring system, already scoped into 9 child tickets under `tickets/todos/world-rendering-core/`) is a
distinct, unrelated system — a server-side offline renderer for scoring, not a player-facing live view.
Neither epic depends on the other.

## Scope for the eventual `create-tickets` pass

Not created yet — this epic is scope-only. Prospective child tickets, in rough dependency order:

1. **New `StatePresenter` methods**: `present_map(state)` (RLE-encode `state.terrain` into
   `{width, height, grid}`) and `present_static(state, ...)` (serialize `buildings`/`resource_nodes`/
   `chests`/`ground_items` into the frontend's `StaticData` shape — field-name mapping required, e.g.
   `chests` → `treasure_chests`). Spatial `regions` (center/radius/locations/difficulty) sourced from
   wherever the compiled world spec actually keeps that data (open question — see below).
2. **New lightweight per-tick entity-delta broadcast.** Extend (or add alongside) the tick-listener path
   to compute a slim `EntitySlim`-shaped delta (`id, x, y, kind, hp, ...`) for `dirty_set.all_dirty_entities`
   plus a `removed` list, and push `{tick, changed, removed, events}` — matching the shape
   `useSimulation.ts`'s existing reducer logic already expects, to minimize total frontend-side change.
3. **New REST routes**: `/api/v1/map`, `/api/v1/static` wrapping item 1; `/api/v1/stats` (total_spawned /
   total_deaths / running / paused — exact source of these cumulative counters not yet confirmed, flagged
   below).
4. **Frontend rewire (`useSimulation.ts` only, not `GameCanvas.tsx`/`useCanvas.ts`)**: swap `EventSource`
   for a `WebSocket` client speaking the real `/api/v1/ws` handshake protocol; keep the existing
   `changed`/`removed`/reducer logic if item 2's payload shape matches it; map `sendControl('pause'|'resume')`
   onto the two real existing routes instead of a generic dispatcher (no generic dispatcher scoped unless a
   real second caller needs one).
5. **Real performance-validation pass, once connected** — an explicit acceptance criterion, not assumed:
   observe actual FPS/update latency against a real running world at a realistic entity count, reported
   with the same scoped-claim discipline `docs/engine/performance_contract.md` requires elsewhere (runtime
   profile, hardware class, scenario) rather than a bare number. Any real optimization need this surfaces
   becomes a **separate future ticket**, driven by evidence — not designed speculatively inside this epic.

## Out of Scope

- **Any new UI panel beyond what `GameCanvas.tsx` already renders.** Its existing minimap + locations
  panel is map-navigation, not information-HUD, so it stays as-is.
- **Wiring the HUD components that already exist as real frontend code** — confirmed present:
  `Sidebar.tsx`, `EntityList.tsx`, `EventLog.tsx`, `InspectPanel.tsx`, `ControlPanel.tsx`,
  `BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`, `Legend.tsx`, all rendered by `App.tsx`
  alongside `GameCanvas`. They exist (this is not "the HUD isn't built"); connecting their specific data
  needs to the real backend is explicitly deferred, per the user's direct instruction not to sculpt
  information-display work now. Only the data `GameCanvas` itself needs (map, static objects, live entity
  positions, pause/resume) is in scope.
- **`/api/v1/speed` UI polish** — the route wiring itself is cheap and can ride along with item 3/4 above
  if trivial, but no new TPS-adjustment widget is scoped.
- **`/api/v1/clear_events`**, both route and any UI — tied entirely to the World Log HUD feature, deferred
  whole.
- **Any speculative rendering-performance rewrite** not driven by item 5's real measurement pass.
- **Building a new client against the server-owned rendering core** (see "Explicitly ruled out" above).

## Acceptance Signal for This Epic (not yet broken into child tickets)

- A documented, ordered child-ticket breakdown exists (done, above) that a later ticket-creation pass can
  use directly.
- Each child ticket, when opened, references this epic and this plan doc.
- No implementation happens directly on the epic ticket or this plan doc — both are scope/planning
  artifacts only.

## Open Questions (flagged, not resolved here)

- **Where does the frontend's spatial `Region` data (center/radius/locations/difficulty) actually live at
  runtime?** Not in `AuthoritativeState.regions` (confirmed — that's a governance/political concept).
  Likely the compiled world spec (`data/worlds/{id}/world.yaml`), loaded once at startup rather than
  per-tick — needs confirmation before item 1's child ticket is investigated in depth.
- **Where do cumulative `total_spawned`/`total_deaths` counters come from, if anywhere?** Not found in
  `V2EngineManager`'s metrics snapshot (`active_entities` is a live count, not a cumulative total) or in
  `StatePresenter`. May need new counters, or may already exist in a kernel-side metrics module not yet
  checked — needs confirmation before item 3's `/stats` child ticket is investigated in depth.
- Whether item 2's new per-tick delta broadcast should extend the existing `/ws` connection's payload or
  register as a genuinely separate listener/message type — an implementation-detail decision for that
  child ticket's own investigation phase, not resolved here.

## References

- `docs/engine/contracts/frontend.md` — the existing, still-accurate "Known gap (2026-07-16)" documenting
  the 5 missing REST routes; this epic's investigation extends it with the transport-mismatch and
  broadcast-payload findings that doc didn't cover.
- `docs/plans/world_rendering/idea_world_rendering_core.md` — the alternative "Option C" server-owned
  rendering core architecture, explicitly not chosen for this epic.
- `tickets/done/infra-04-realtime-state-streaming.md` — the historical V1-era ticket whose incomplete
  step 4 ("refactor `useSimulation`") is this epic's direct root cause.
- `docs/engine/performance_contract.md` — the scoped-claims methodology (Runtime Profile / Hardware Class
  / Scenario / Execution Mode) item 5's performance-validation acceptance criterion must follow.
- `src/api/presenters/state_presenter.py`, `src/api/read_model_cache.py`, `src/api/engine_manager.py`,
  `src/api/ws/stream.py`, `src/core/state.py` (`AuthoritativeState`) — the exact backend files this epic's
  child tickets touch.
- `frontend/src/hooks/useSimulation.ts`, `frontend/src/types/api.ts` — the exact frontend files item 4
  touches; `GameCanvas.tsx`/`useCanvas.ts` are read-only reference for the target contract, not touched.
