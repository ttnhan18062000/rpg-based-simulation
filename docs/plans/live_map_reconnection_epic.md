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

## Recoverable Reference Implementation (git archaeology, 2026-08-21)

**This "new work" was already built once, measured, and shipped — then deleted as "legacy" when V2
replaced V1, and never re-ported.** Commit `677abbfb` ("Update documentation, remove legacy code (#17)")
deleted an entire working implementation of exactly this contract under `src_legacy/api/`. Every file is
still fully recoverable via `git show 677abbfb^:<path>`:

- **`src_legacy/api/routes/map.py`** — the real `/api/v1/map` handler: pulls `manager.get_grid()`,
  RLE-encodes it (`[value, count, value, count, ...]`) exactly matching `useSimulation.ts`'s still-live
  `decodeRLE()`. 39 lines, complete.
- **`src_legacy/api/routes/state.py`** — `/api/v1/state?since_tick=&selected=` with those **exact** two
  query params the current frontend still calls — confirms the frontend's contract was never speculative,
  it's the real, previously-working V1 API being called against a backend that replaced it without notice.
- **`src_legacy/api/routes/stream.py`** — the real `/api/v1/stream` **SSE** handler `useSimulation.ts` was
  built against. `compute_delta()` diffs consecutive slim-entity dicts into exactly
  `{tick, changed, removed, events}` (byte-for-byte the shape `useSimulation.ts`'s `onmessage` handler
  still parses today), skips empty ticks except a heartbeat every 20 ticks to bound bandwidth, and used
  **Redis Streams** (`sim:stream`, `xread`) as a durable pub/sub layer decoupling tick production from SSE
  consumers — a different (arguably more robust) architecture than V2's current in-process
  `add_tick_listener()` callback + per-connection `asyncio.Queue`.
- **`src_legacy/api/presenters/state_presenter.py`** — has a `present_minimal()` method with the **exact
  same shape** V2's `src/api/presenters/state_presenter.py::present_minimal()` still has today
  (`{tick, world_time, entities_count, maturity, seed}`) — proof V2's presenter was itself partially
  ported from this file, but only that one method made the trip; `present_full`, `present_entity`,
  `present_region`, `present_building`, `present_node` were left behind.
- **`src_legacy/api/presenters/world_presenter.py`** (`to_world_state_response`, `to_static_data_response`)
  — the exact assembly logic turning raw world objects into `WorldStateResponse`/`StaticDataResponse`,
  including the field renames the new V2 presenter will need too (e.g. `chest.guard_id` →
  `guard_entity_id`).
- **`src_legacy/api/schemas.py`** (766 lines) — `EntitySlimSchema` (14 fields, matches
  `frontend/src/types/api.ts`'s `EntitySlim` closely), `RegionSchema` (`region_id, name, terrain,
  center_x, center_y, radius, difficulty, owner_faction, influence, locations` — **this resolves the
  Region open question below**: even in V1, this spatial region shape was never part of the authoritative
  governance state; it came from `WorldState.regions`, a separate world-model collection), and
  `SimulationStats` (`tick, world_day, alive_count, total_spawned, total_deaths, running, paused` —
  confirms these are real, previously-computed fields, not a novel ask).
- **`docs/archive/performance/performance-report-api-payload.md`** — the actual measured results of this
  V1 implementation: `/state` polling dropped from ~800KB–1.6MB per request to ~75KB (**91% reduction**)
  via exactly this slim-schema + RLE-map + separate-`/static`-endpoint design, verified against a
  ~360-entity test world, with **8 dedicated payload tests** (`tests/test_api_payload.py`, itself now also
  deleted with the rest of `tests_legacy/`).

**What this changes about scope**: child tickets for the new `StatePresenter` methods and REST routes are
now a **port-and-adapt** task against a concrete, proven reference — not a from-scratch design exercise.
The one deliberate deviation from directly copying V1: **transport**. V1 used Redis Streams + SSE; this
epic keeps V2's already-built WebSocket transport (per the "Explicitly ruled out" section below, no new
transport-layer infrastructure is being introduced) and carries the **payload shape** (`compute_delta()`'s
`{tick, changed, removed, events}`) over it instead — payload design reused, transport modernized, not the
reverse.

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
   `{width, height, grid}` — port `src_legacy/api/routes/map.py`'s RLE loop verbatim, it's
   transport-agnostic) and `present_static(state, ...)` (serialize `buildings`/`resource_nodes`/`chests`/
   `ground_items` into the frontend's `StaticData` shape, adapting
   `src_legacy/api/presenters/world_presenter.py::to_static_data_response`'s field mapping — e.g. `chests`
   → `treasure_chests`, `guard_id` → `guard_entity_id`). Spatial `regions` sourced per the resolved
   open-question finding below (compiled world spec, not `AuthoritativeState.regions`).
2. **New lightweight per-tick entity-delta broadcast.** Port `src_legacy/api/routes/stream.py`'s
   `compute_delta()` logic (diff consecutive `EntitySlim`-shaped dicts into
   `{tick, changed, removed, events}`, 20-tick heartbeat on quiet ticks) onto V2's existing
   `add_tick_listener()`/WebSocket path instead of V1's Redis-Streams/SSE path — reuse the tick loop's
   already-tracked `DirtySet` (`dirty_set.all_dirty_entities`) as the "what changed" source instead of a
   full old-vs-new snapshot diff, since V2 already computes it and V1 didn't have it available. See
   "Real-Time Transfer Design Guidance" below for the delta-encoding/msgpack/interest-management specifics.
3. **New REST routes**: `/api/v1/map`, `/api/v1/static` wrapping item 1; `/api/v1/stats` — port
   `src_legacy`'s `SimulationStats` shape (`tick, world_day, alive_count, total_spawned, total_deaths,
   running, paused`). **`total_spawned`/`total_deaths` fully traced now**: V1's `EngineManager` (`git show
   677abbfb^:src_legacy/api/engine_manager.py`, L73-74/221-222/400-405) tracked these as two plain instance
   counters (`self._total_spawned`, `self._total_deaths`), incremented each tick by `len(new_ids)`/
   `len(dead_ids)`, reset to 0 on world load. Confirmed via direct grep that `src/api/engine_manager.py`
   (`V2EngineManager`) has **zero** equivalent today — not a wiring gap, a genuine missing counter. Item 3's
   child ticket adds the same simple pattern to `V2EngineManager`, not a novel design.
4. **Frontend rewire (`useSimulation.ts` only, not `GameCanvas.tsx`/`useCanvas.ts`)**: swap `EventSource`
   for a `WebSocket` client speaking the real `/api/v1/ws` handshake protocol; keep the existing
   `changed`/`removed`/reducer logic unchanged (item 2's payload shape is deliberately designed to match
   it, minimizing frontend-side change); map `sendControl('pause'|'resume')` onto the two real existing
   routes instead of a generic dispatcher (no generic dispatcher scoped unless a real second caller needs
   one).
5. **Real performance-validation pass, once connected** — an explicit acceptance criterion, not assumed:
   observe actual FPS/update latency against a real running world, at both `CLASS_B` (2,500 entities,
   <40ms/tick target) and `CLASS_C` (500 entities, <30ms/tick target) scale per
   `docs/performance/perf_baseline_policy.md`'s already-registered hardware classes, and confirm broadcast
   payload size stays near the V1-measured baseline (~75KB per update at ~360 entities, not the
   pre-optimization ~800KB–1.6MB) as a concrete regression check, not a bare "it feels fast" claim. Report
   with the same scoped-claim discipline `docs/engine/performance_contract.md` requires elsewhere (runtime
   profile, hardware class, scenario). Any real optimization need this surfaces becomes a **separate future
   ticket**, driven by evidence — not designed speculatively inside this epic.

## Real-Time Transfer & Multi-Client Design Guidance (2026-08-21 research)

Two research passes this session looked at (a) established real-time game-state-streaming patterns and
(b) how to keep the new broadcast payload reusable by a future second client type. Findings, scoped to
what's genuinely worth adopting at this project's actual scale (one server, a handful of concurrent
viewers — not a large multiplayer game):

- **Delta-encode against the tick loop's `DirtySet` (item 2 above)** — this is simultaneously V1's own
  proven pattern (`compute_delta()`) and the canonical real-time-games pattern (Glenn Fiedler's
  "Snapshot Compression"/"State Synchronization" — gafferongames.com — and productized identically in
  Colyseus's `@colyseus/schema` `ChangeTree`). Doubly confirmed, not a new idea.
- **Actually use the `msgpack` format `src/api/ws/stream.py` already negotiates in its handshake but never
  sends** — near-free wire-size reduction; the format path exists today, item 2's new payload just needs
  to be routed through it instead of defaulting to JSON.
- **Turn the existing client-side vision-range filtering into real server-side interest management** — the
  minimap already computes a `vision_range`-filtered visible set when spectating an entity
  (`GameCanvas.tsx`), but purely for cosmetic dimming; the server still ships every entity to every client
  regardless. Gating what's actually broadcast by vision range is the standard MMO "Area of Interest"
  pattern, and this codebase already has the filtering logic to reuse server-side — genuinely worth
  scoping as a follow-up once item 2 ships and is measured (item 5), not before.
- **Multi-client reusability is a schema-versioning discipline, not a transport or infrastructure
  decision.** The planned payload (RLE terrain + semantic entity fields, no pixels, no web-specific view
  logic) is already client-agnostic by nature — a future native/mobile client or a debug/replay tool could
  consume the identical feed. The one thing worth doing now, cheaply: give the broadcast message an
  explicit schema-version marker and treat it as additive-only from day one (Protocol Buffers' real lesson
  isn't "use protobuf," it's this evolution discipline) — inexpensive now, expensive to retrofit once a
  second client depends on the shape. Full binary-schema frameworks (Colyseus itself, Protobuf, FlatBuffers)
  and the full "Option C" rendering-core abstraction remain correctly out of scope at this scale — see Out
  of Scope.
- **Not worth adopting**: client-side prediction/reconciliation (solves latency-hiding for a
  player-controlled avatar; this is a spectator view of an autonomous simulation, wrong problem) and
  priority/update-rate tiering (real technique, but premature before item 5's measurement shows it's
  needed).

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

## Open Questions

- **Region spatial data — now fully resolved, and it's a real gap, not a wiring gap.** Directly confirmed
  by reading `src/worldbuilding/recipe.py`'s `RegionRecipeSpec` in full: its only fields are `id, type,
  grid_bounds (min_x,min_y,max_x,max_y), terrain, hazard_level, hazard_kind, tags` — **no `center`,
  `radius`, `locations`, `difficulty`, or `name` field exists anywhere.** A repo-wide grep for
  `center_x|center_y|radius|locations` across `src/worldbuilding/`, `src/worldassembly/`, `src/core/state.py`,
  and the real compiled `data/worlds/sandbox_world/world.yaml` turned up nothing matching this shape either.
  V1 had the same gap in spirit (its spatial `RegionSchema` came from a separate `WorldState.regions`
  collection, not governance state) but V1's version actually had the fields; V2 genuinely doesn't. **This
  means item 1's `present_static` cannot just "look up" region spatial data — it must derive `center`
  (midpoint of `grid_bounds`) and `radius` (half the larger bound dimension) at presentation time, and
  either drop `locations`/`difficulty`/`name` from the ported `RegionSchema` or source them from elsewhere
  not yet identified.** This is real, scoped design work for item 1's child ticket, not a lookup task —
  flagged precisely so that ticket doesn't get scoped as trivial.
- **`total_spawned`/`total_deaths` — now fully resolved.** See item 3 above: V1's exact computation
  pattern found and confirmed absent from V2. Item 3's child ticket adds two simple counters to
  `V2EngineManager`, following V1's proven pattern.
- Whether item 2's new per-tick delta broadcast should extend the existing `/ws` connection's payload or
  register as a genuinely separate listener/message type remains an implementation-detail decision for
  that child ticket's own investigation — V1's fully-separate-transport precedent (Redis Streams + SSE, a
  different connection entirely from its REST API) shows both approaches are legitimate; V2 keeping it on
  the existing `/ws` connection is the lower-effort default given no separate transport is being
  introduced, but not mandated here.

## References

- `docs/engine/contracts/frontend.md` — the existing, still-accurate "Known gap (2026-07-16)" documenting
  the 5 missing REST routes; this epic's investigation extends it with the transport-mismatch and
  broadcast-payload findings that doc didn't cover.
- `docs/plans/world_rendering/idea_world_rendering_core.md` — the alternative "Option C" server-owned
  rendering core architecture, explicitly not chosen for this epic.
- `tickets/done/infra-04-realtime-state-streaming.md` — the historical V1-era ticket whose incomplete
  step 4 ("refactor `useSimulation`") is this epic's direct root cause.
- `docs/engine/performance_contract.md`, `docs/performance/perf_baseline_policy.md` — the scoped-claims
  methodology and the `CLASS_A`/`CLASS_B`/`CLASS_C` hardware-class targets item 5's performance-validation
  acceptance criterion must follow.
- `docs/archive/performance/performance-report-api-payload.md` — the measured V1 payload-size baseline
  (~75KB post-optimization at ~360 entities) item 5's regression check is grounded against.
- `src/api/presenters/state_presenter.py`, `src/api/read_model_cache.py`, `src/api/engine_manager.py`,
  `src/api/ws/stream.py`, `src/core/state.py` (`AuthoritativeState`) — the exact backend files this epic's
  child tickets touch.
- **`src_legacy/api/routes/map.py`, `src_legacy/api/routes/state.py`, `src_legacy/api/routes/stream.py`,
  `src_legacy/api/presenters/state_presenter.py`, `src_legacy/api/presenters/world_presenter.py`,
  `src_legacy/api/schemas.py`** (all recoverable via `git show 677abbfb^:<path>`, deleted by `677abbfb`) —
  the proven V1 reference implementation this epic's child tickets port and adapt from. Not live code, not
  restorable by a simple revert (V1's `EngineManager`/`WorldState` don't exist in V2), but the concrete
  shape/logic reference each child ticket should start from rather than designing blind.
- `frontend/src/hooks/useSimulation.ts`, `frontend/src/types/api.ts` — the exact frontend files item 4
  touches; `GameCanvas.tsx`/`useCanvas.ts` are read-only reference for the target contract, not touched.
