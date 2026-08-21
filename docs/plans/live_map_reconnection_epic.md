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
   thing as the frontend's spatial `Region` type (center_x/center_y/radius/locations/difficulty) —
   **confirmed (see Open Questions) that this spatial shape doesn't exist anywhere in V2 at all**, not even
   in the compiled world spec's `RegionRecipeSpec` (`grid_bounds` only, no center/radius/locations). A real
   gap, resolved with a concrete derivation approach below, not an unresolved lookup.
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
   → `treasure_chests`, `guard_id` → `guard_entity_id`). Spatial `regions`: derive `center`/`radius` from
   `RegionRecipeSpec.grid_bounds` at presentation time (no stored field exists — see Open Questions), and
   either find a source for `locations`/`difficulty`/`name` or drop them from the ported schema.
2. **New lightweight per-tick entity-delta broadcast.** Port `src_legacy/api/routes/stream.py`'s
   `compute_delta()` logic (diff consecutive `EntitySlim`-shaped dicts into
   `{tick, changed, removed, events}`, 20-tick heartbeat on quiet ticks) onto V2's existing
   `add_tick_listener()`/WebSocket path instead of V1's Redis-Streams/SSE path — reuse the tick loop's
   already-tracked `DirtySet` (`dirty_set.all_dirty_entities`) as the "what changed" source instead of a
   full old-vs-new snapshot diff, since V2 already computes it and V1 didn't have it available. See
   "Scaling Design" §D and "Real-Time Transfer & Multi-Client Design Guidance" below for the
   delta-encoding/msgpack/interest-management specifics (§D has the corrected, load-bearing version).
   **Real correctness requirement, found via external review + verified (2026-08-21, see "External Design
   Review" below)**: the connect sequence must avoid a real race — register the tick-listener callback
   *before* taking the map/static snapshot, not after (mirrors how database change-data-capture systems
   atomically pair "record the resume point" with "take the snapshot"). Getting this ordering right means
   no deltas are ever missed during connect and no buffer-then-discard logic is needed. Each delta message
   must also carry `tick` and `snapshot_as_of_tick` fields so the client can sanity-check alignment and
   request a fresh reconnect/resnapshot on mismatch — full sequence/generation-number machinery is not
   needed at this project's scale. `EntitySlim` fields must stay absolute current values (`x`, `y`, `hp`,
   ...), never diffs-from-previous — this is what makes it safe for the server to coalesce or drop messages
   for a slow client under backpressure without any sequence tracking (already true of the ported V1
   schema; stated here as a hard requirement, not just an implementation detail).
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
   pre-optimization ~800KB–1.6MB) as a concrete regression check, not a bare "it feels fast" claim.
   **Precise, testable budget, revised to percentile-based (2026-08-21, corrected after external review —
   see "External Design Review" below)**: a flat "median ≤8ms, floor ≤16.6ms never crossed" statement isn't
   an achievable browser contract (GC pauses, OS scheduling, thermal throttling are real and outside the
   application's control) — restated as **p50 ≤8ms, p95 ≤12ms, p99 ≤16.6ms under bounded-viewport load**,
   plus tracking the percentage of frames exceeding 16.6ms rather than asserting it never happens. Still a
   frame-*time* budget, not a frame-*count* target, since `requestAnimationFrame` syncs to the viewer's
   actual display refresh rate (60/120/144Hz), not a hardcoded 60. Also verify the existing lerp/
   interpolation math is genuinely delta-time-based (elapsed wall-clock ms since last tick), not
   frame-count-based — required for it to degrade gracefully rather than visibly stutter below peak frame
   rate; currently unverified since this frontend has never run against live data. Report with the same
   scoped-claim discipline `docs/engine/performance_contract.md` requires elsewhere (runtime profile,
   hardware class, scenario). Any real optimization need this surfaces becomes a **separate future ticket**,
   driven by evidence — not designed speculatively inside this epic.
6. **New `GET /api/v1/manifest` endpoint** (small, backend + `useSimulation.ts` only — see "Scaling Design"
   below for the full design and precedent): fetched once alongside item 3's `/static` call, returning
   `{schema_version, terrain_types: {id:name}, entity_kinds: {id:name}, building_types: {...},
   location_types: {...}}`. Makes the backend's own registries the single source of truth for what an ID
   means, instead of the frontend's current independent, drift-prone hardcoded copy
   (`frontend/src/constants/colors.ts`'s `TERRAIN_COLORS`/`TILE_COLORS`/`KIND_COLORS`/etc.). **Scope
   boundary, stated honestly**: fetching and exposing the manifest is in-scope (backend route +
   `useSimulation.ts`); actually retiring `colors.ts`'s hardcoded maps in favor of manifest-driven values is
   a `GameCanvas.tsx`/`constants/` change, which crosses this epic's own stated boundary ("`GameCanvas.tsx`/
   `useCanvas.ts` are read-only reference... not modified by this epic"). This item scopes the endpoint and
   the fetch; switching the renderer to consume it is left for a fast-follow, not silently declared done
   here.
7. **Reserve, but do not implement, a spatial-subscription field on the delta message envelope** — e.g. an
   unused `region`/`chunk` field the client doesn't yet send and the server doesn't yet honor. Added after
   the bandwidth reassessment below (external review + independent verification) showed interest management
   is likely necessary at real target scale, not safely deferrable indefinitely as originally scoped —
   reserving the field now costs nothing and avoids a breaking protocol change later when it's actually
   implemented. Building real interest-management filtering itself remains out of scope for this epic (see
   Out of Scope) — this item is the envelope placeholder only.
8. **Explicit, phased loading state — don't conflate "fetching initial data" with "now live," and don't
   ship one opaque loading state.** Confirmed real, not hypothetical: `useSimulation.ts`'s `SimStatus` type
   today has only `'CONNECTING'` covering the *entire* pre-live sequence (map/static/manifest fetch, WS
   handshake, first-snapshot receipt, all one bucket); its fetch-failure path retries silently forever with
   no visible error (`setTimeout(loadInitial, 1000)`); `GameCanvas.tsx` shows one generic "Loading map..."
   string with no phase information at all. Item 8 replaces this with a real state machine matching the
   actual sequence — `INITIALIZING → FETCHING_WORLD_DATA → CONNECTING_LIVE → SYNCING → READY`, each a
   distinct status — plus a visible error state after repeated failures instead of infinite silent retry.
   `SYNCING` corresponds exactly to item 2's connect-time atomic-handoff window (listener registered,
   waiting for/applying the first snapshot) — the same correctness fix, now with a real, user-visible phase
   attached to it. The loading screen is a small, self-contained addition shown *instead of* `GameCanvas`
   while not yet `READY` — doesn't touch `GameCanvas.tsx`/`useCanvas.ts` themselves, so it doesn't cross
   this epic's stated boundary on those files.

## Scaling Design: Data Manifest, Layered Rendering, Frame Budget, Stream Correctness (2026-08-21 deep
research, externally reviewed)

Following up on the section above, deeper research tied directly to a "what if this needs to handle a huge
map and thousands of entities" scaling conversation, **plus (§D) an external, project-blind AI design review
whose findings were independently verified — not trusted at face value — before being folded in**. Each
subsection proposes a concrete design tied to a cited real precedent — not general survey material. **Scope
honesty up front**: item 6 (the manifest) and item 7 (the spatial-subscription envelope placeholder) are
folded into this epic's actual Scope above because they're small and backend-plus-`useSimulation.ts`-only,
as is the connect-time race fix folded into item 2. Part B (layered rendering) is **not** folded into this
epic's Scope — it requires modifying `GameCanvas.tsx`/`useCanvas.ts`, which this epic deliberately keeps
untouched, and the epic's own philosophy (item 5: "any real optimization need becomes a separate future
ticket, driven by evidence") argues against speculatively rewriting a renderer that hasn't been measured
yet. It's captured here in full so the design isn't lost, sequenced as the natural next ticket once item 5's
real measurement pass shows whether/where it's actually needed.

### A. Data Manifest — Separating Meaning from Live Data

**The problem, precisely**: `frontend/src/constants/colors.ts` hardcodes `TERRAIN_COLORS`, `TILE_COLORS`,
`KIND_COLORS`, `LOCATION_TYPE_ICONS`, `DIFFICULTY_BADGES` — independent, frontend-owned copies of what a
backend terrain-tile-ID or entity-kind-ID *means*. This is architecturally backwards for a project that
treats registries as the source of truth everywhere else in its backend (`layer_registry.jsonl`,
`tag_registry.jsonl`, content catalogs) — the frontend maintaining its own parallel, driftable copy is the
one place that discipline doesn't hold.

**Real precedents, all confirmed and citable, not hypothetical:**
- **Avro + Confluent Schema Registry** — production-scale precedent for exactly this split. Wire format is
  a magic byte + 4-byte schema ID + binary data; the schema is never resent, only looked up by ID.
  Result: 30–70% smaller than self-describing JSON, and per-record overhead drops to 5 bytes.
- **H.264 SPS/PPS (Sequence/Picture Parameter Sets)** — a fair analogy, not a stretch: parameter sets are
  sent once, each subsequent unit carries only an index back to them, because the values "do not typically
  change" once set.
- **Source Engine's SendTables/DataTables** — the closest real *game*-networking match, and a shipping,
  decades-proven pattern: on connect, client and server exchange the list of known entity classes; if the
  client is missing a class the server references, the connection is rejected outright ("Client missing DT
  class"). No silent renegotiation.

**Design adopted**: `GET /api/v1/manifest` (Scope item 6 above), fetched once alongside `/static` — same
lifecycle, not a new connection step. Payload is a versioned ID→meaning lookup table. The live per-tick
broadcast carries **only IDs, zero self-description** — mirrors both Avro's compact-record principle and
H.264's per-frame terseness. A full schema-registry service or Protobuf codegen pipeline would be real
overkill at this project's scale — the *principle* (ID-indirection, fetched once, cached) is what transfers
here, not the infrastructure.

**Corrected after external review (2026-08-21)**: the original "one versioned manifest, hard-reconnect on
any mismatch" design conflated two genuinely different things that shouldn't share one version number —
**protocol schema** (the wire message structure/field layout) and **content dictionary** (what terrain ID 3
or entity-kind ID 7 currently mean). A deployment that relabels a terrain type shouldn't force every
connected client to hard-disconnect; a change to the message envelope itself should. Revised design: track
`protocol_version` and `dictionary_version` (or a content hash) separately. On a dictionary-version mismatch,
fetch the new dictionary and resume — no disconnect needed. Only an incompatible `protocol_version`
justifies the hard-disconnect-and-reconnect behavior originally proposed wholesale — that behavior is still
correct, just narrower in scope than first stated.

### B. Layered, Cache-First Rendering Architecture (design captured, not scoped into this epic)

**Precedents, all real and current, not guesses:**
- **Browser compositor layers — the analogy is exact, not loose.** A DOM element promoted to its own paint
  surface (via `transform`/`opacity`/`will-change`) has `transform`/`opacity` changes skip layout *and*
  paint entirely, applied directly on the GPU; anything else forces a real repaint of that layer's texture.
  This is precisely what the existing CSS-`transform`-based pan/zoom already does correctly — real
  compositor-only work, not a metaphor. Caveat worth keeping: layers aren't free (GPU memory, per-layer
  upload cost) — cache deliberately, don't promote everything.
- **Dirty-rectangle rendering** — a well-established, pre-1995 2D-game-engine technique: track the bounding
  rectangles of only the screen regions actually drawn-to this frame, and blit just those instead of
  redrawing the full frame. **Corrected after external review (2026-08-21)**: the original justification
  here — "the server's per-tick `DirtySet` is usually sparse, so redraw is cheap" — conflates two different
  things. The server's `DirtySet` tracks what changed *between authoritative ticks*; it says nothing about
  what changes *between rendered frames*, and a genuinely moving entity's on-screen position changes on
  essentially every rendered frame during interpolation, regardless of how sparse the underlying tick data
  is. Server-tick sparsity does not imply render-frame sparsity — verified as a real, separate-by-design
  distinction in real-time engine architecture (simulation and presentation are legitimately independent
  concerns, each with their own notion of "dirty"). The technique is still worth keeping, but only because
  this project's autonomous entities spend most of their simulated time in genuinely idle states (working,
  sleeping, standing) — confirmed as the standard behavior shape for this kind of simulation, and matching
  Pygame's own sprite-rendering library, which explicitly optimizes dirty-rect handling for scenes with many
  static sprites, not moving ones. **The corrected design tracks two separate client-side buckets** —
  currently-animating entities (redrawn every frame, no dirty-rect saving possible or expected) vs.
  genuinely-idle-since-last-frame entities (skipped) — rather than treating the server's `DirtySet` as a
  proxy for render cost.
- **PixiJS confirms the same pattern as a first-class, current engine feature** — `cacheAsTexture`
  (v8; `cacheAsBitmap` pre-v8) renders a container to a texture once and reuses it on later frames, explicitly
  documented as best for infrequently-updating content (i.e. exactly the terrain/semi-static-object case).
  `ParticleContainer` is a separate, deliberately stripped-down container built for rendering thousands of
  lightweight objects fast — the closest real-engine analog to this project's entity layer at scale. Worth
  noting: even PixiJS's culling is opt-in/manually triggered as of v8, not automatic — culling is a real,
  explicit responsibility in *any* engine, not something adopting one gives you for free.
- **Adopt an engine (PixiJS/WebGL) vs. extend Canvas2D — extend, don't migrate.** A rendering-engine swap is
  a different-shaped project (new render loop, new asset pipeline, full draw-logic rewrite, WebGL context
  management) than incrementally adding caching to working Canvas2D code. All three PixiJS-confirmed
  patterns above can be manually replicated in plain Canvas2D using the exact off-screen-canvas pattern
  already proven on this project's own minimap — no engine migration needed to capture the real benefit.

**Proposed layer model** (design for the follow-up ticket, not built here):
- **Layer 0 — terrain**: **corrected after external review (2026-08-21)** — a single whole-map off-screen
  bitmap is unsafe at "huge map" scale. Real browser canvas ceilings vary sharply by engine: Chrome/Firefox
  allow very large canvases (32,767px per dimension, hundreds of millions of px² area), but **Safari is the
  real binding constraint** — roughly 3-5 total megapixels depending on device RAM, with a further ~384MB
  total-canvas-memory ceiling across a whole page on iOS Safari historically. `devicePixelRatio` (2×/3× on
  most modern displays) squares into backing-store pixel count, so a modest-looking canvas can exceed this
  fast. **Revised design**: chunk terrain into a grid of cached tiles — researched against real web-mapping
  precedent (Leaflet/Mapbox GL); **512×512 tiles fit this project better than the more common 256×256** web
  standard, since the 256px convention is driven by HTTP-request-count concerns for *fetched* image tiles,
  which don't apply here (terrain is generated locally, not fetched) — fewer, larger chunks mean less
  per-chunk bookkeeping for the same coverage. Retain tiles within a fixed buffer radius around the camera
  viewport (Leaflet's `keepBuffer` pattern), evicting tiles once they fall outside it — not time-based
  expiry, since (unlike static map tiles) this project's terrain can genuinely change; invalidate a
  specific tile only on an actual terrain-change event inside it. A full per-zoom-level tile pyramid (what
  Leaflet/Mapbox actually maintain) is not needed yet — a single base-resolution tile cache under the
  existing CSS-transform zoom is sufficient unless far-zoomed views later need simplified/aggregated detail.
- **Layer 1 — semi-static objects** (buildings, resource nodes, chests): cache, invalidate per-object on the
  specific state-change event (harvested, destroyed), not a periodic full redraw. If sharing a chunked cache
  with Layer 0's tiles, invalidating one object requires rebuilding its containing chunk, not just that
  object — the same chunk-level (not object-level) invalidation Layer 0 uses.
- **Layer 2 — dynamic entities**: dirty-rect redraw using the two-bucket model above (animating vs. idle) —
  only the bounding regions of genuinely-idle entities are worth skipping; actively-moving entities are
  redrawn every frame regardless, and that's expected, not a failure of the technique.
- **Layer 3 — overlay** (hover, selection): unchanged, already cheap.
- Compositing all four is already free — they're separate DOM-stacked `<canvas>` elements, and the browser's
  own GPU compositor combines them without any new code, though each cached layer still has a real GPU
  memory/upload cost — cache deliberately, not everything.

### C. Frame-Budget Headroom, Not a 60 FPS Ceiling

**Precedent**: Glenn Fiedler's "Fix Your Timestep!" (gafferongames.com) is the recognized reference here,
addressing exactly the real problem of simulation/animation math breaking when tied to variable frame time —
its fix is an accumulator pattern that decouples simulation step from render frame rate. This validates this
project's existing design *shape* (12 TPS sim, interpolated render) as the right approach — but requires the
render loop's interpolation math to use real elapsed delta-time, not an assumed fixed frame count, or it
silently breaks the moment frame rate drops below the assumed value.

**Frame-budget headroom is real, named practice, not a novel idea**: convention is a 16.7ms budget for 60Hz,
8.3ms for 120Hz, with teams commonly reserving 10-15% margin within that budget for spikes rather than
budgeting to the full frame time — directly supporting an 8ms-class budget (120fps-capable) as real slack
against a 16.6ms (60fps) floor, exactly the shape proposed. `requestAnimationFrame` itself confirms why this
must be a **time** budget, not a **count** target: it syncs to the viewer's actual display refresh rate
(60/120/144Hz), not a hardcoded 60, so a frame-count-based target is meaningless across real viewers.

**Adopted wording** (folded into Scope item 5 above, **revised to percentile-based after external review —
see §D below**): p50 ≤8ms, p95 ≤12ms, p99 ≤16.6ms under bounded-viewport load, tracking the percentage of
frames that exceed 16.6ms rather than asserting it never happens — plus explicit verification that the
existing lerp is delta-time-based, not frame-count-based.

### D. External Design Review — Findings, Independently Verified (2026-08-21)

The three sections above (A/B/C) were sent, generalized and stripped of all project-specific detail, to an
external AI reviewer with no project context, specifically to get an outside, unbiased critique before
implementation starts. **Its findings were not accepted at face value** — each was independently checked
against real precedent or worked through analytically before being adopted, and at least one of the
reviewer's own claims was found to be imprecise on closer inspection. Full original review context: the
review request document and the reviewer's response are not part of this repo (external artifacts); this
section captures only the verified, adopted outcome.

**Two real correctness/design flaws found, confirmed, and fixed** (not just style preferences):

1. **Connect-time snapshot/delta race** — genuinely missing from the original design (folded into Scope
   item 2 above): nothing tied a delta message to the exact state it presumed as a starting point, so
   deltas arriving between "static fetch completes" and "stream subscription starts" would be silently
   lost. Verified real precedent (database change-data-capture systems solve exactly this by atomically
   pairing "record the resume point" with "take the snapshot") and adopted the simplest correct fix:
   register the tick-listener before taking the snapshot, not after — no buffer-then-discard logic needed,
   simpler than the reviewer's own more elaborate proposed alternative.
2. **Dirty-rect rendering's stated justification was flawed** (folded into §B above): conflated
   network-tick sparsity with render-frame sparsity, which are genuinely different things. Verified via
   research into real 2D-engine sprite architecture that the technique is still worth keeping — corrected
   to the two-bucket (animating vs. idle) model rather than abandoned.

**Bandwidth/interest-management reassessment — the reviewer's own number checked and refined, not just
trusted:**

The reviewer projected ~750KB–1.1MB/s per viewer by treating the measured V1 baseline (75KB) as if it were
already a per-tick delta message size. It wasn't — that figure was a **full-state poll** of all ~360 test
entities, not an incremental delta of only the entities that changed since the prior tick; a true delta at
that same test scale would be meaningfully smaller (worked the math directly: even a 100%-everything-changed
worst case at 360 entities is ~0.9MB/s, not the reviewer's higher estimate). **However**, redoing that same
math at the actual target scale this epic cites elsewhere (10,000 entities, `CLASS_A`) shows the reviewer's
underlying warning was right, and arguably more urgent than either of us first stated: even a modest 10-20%
changed-entity fraction per tick at 10,000 entities produces roughly 1.5-5MB/s per viewer (JSON; somewhat
less with `msgpack`) — comparable to or larger than the reviewer's original estimate for the much smaller
old test scale, simply because there are ~28x more entities. **Conclusion**: interest management (filtering
what's broadcast by what a viewer can actually see) is likely necessary at real target scale, not the
safely-indefinitely-deferrable nice-to-have this epic originally treated it as. Still correctly out of scope
to *build* now (no real measurement against a live system exists yet to size it against) — but Scope item 7
above (reserve an unused spatial-subscription field in the message envelope now) exists specifically because
of this reassessment, so the protocol doesn't need a breaking change when interest management does get
built.

**Adopted as real refinements, lower stakes:** the manifest's protocol-version/dictionary-version split
(§A above); percentile-based frame budgets replacing "median + inviolable floor" (§C above); chunked terrain
caching with real browser-limit numbers (§B above).

**Explicitly not adopted wholesale**: the reviewer's fuller operational playbook for backpressure/slow
clients (bounded-queue coalescing policies, randomized reconnect backoff, rolling-deployment manifest-skew
handling) is real, correct advice — calibrated for a system with many concurrent clients and multi-instance
deployments. This project's actual stated scale (single server, a handful of concurrent viewers) doesn't
justify building the full playbook now; the cheap, universally-applicable parts (bounded queue depth, a
resnapshot-on-fallen-too-far-behind policy) are worth doing regardless of scale and are captured in Scope
item 2's correctness fix above, but the heavier operational machinery is not being scoped speculatively.

## Real-Time Transfer & Multi-Client Design Guidance (2026-08-21 research)

**Read this after "Scaling Design" and §D above, not instead of them.** This section is the *first* research
pass done this session, before the deeper "Scaling Design" investigation and the external review that
follows it. Where the two overlap (delta-encoding, `msgpack`, interest management), §D above contains the
corrected, more complete, externally-verified treatment — most importantly, §D's bandwidth math is what
actually justifies interest management's priority, not this section's original framing of it. This section
is kept because its multi-client-reusability conclusion and its explicit "not worth adopting" list
(client-side prediction, priority tiering) are not repeated anywhere else and still stand.

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
  pattern, and this codebase already has the filtering logic to reuse server-side. **Priority raised after
  §D's bandwidth reassessment above** (§D precedes this section in the document — see its "Bandwidth/
  interest-management reassessment" for the actual math): originally framed here as "follow-up once
  measured, not before" —
  the corrected math at real target scale (10,000 entities) shows this is likely load-bearing, not a nice
  extra, so Scope item 7 now reserves the protocol field for it even though building the filtering itself
  stays out of this epic.
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

- `docs/plans/live_map_scaling_roadmap.md` — this epic is M1 of that roadmap; §B above is M2's
  (`TCK-20260821-EPIC-LIVE-MAP-RENDERING-PERFORMANCE`) design source, §D's bandwidth reassessment is M3's
  (`TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT`) design source. Both are gated on this epic shipping.
- **External sources for the "Scaling Design" section**: Confluent/Avro schema-registry docs
  (docs.confluent.io — ID-indirection wire format), H.264 SPS/PPS explainers (cardinalpeak.com,
  doc-kurento.readthedocs.io), Valve's Source Engine networking wiki (developer.valvesoftware.com —
  SendTables/DataTables), web.dev's "Stick to Compositor-Only Properties" (compositor-layer mechanics),
  classic dirty-rectangle rendering reference (phatcode.net), PixiJS v8 docs (`cacheAsTexture`,
  `ParticleContainer`), Glenn Fiedler's "Fix Your Timestep!" (gafferongames.com), and a frame-budget
  calculator/JS-game-loop reference (gamedevcheatsheet.com, aleksandrhovhannisyan.com) — full citations in
  the section itself.
- **External sources for §D (external review verification)**: Debezium/CDC snapshot+log-position docs
  (debezium.io, DeepWiki) for the atomic-handoff pattern; Pygame's `sprite`/`DirtySprite` documentation
  (pygame.org) and a real-time "state stream" engine architecture reference for the network-dirty vs.
  render-dirty distinction; MapTiler's 256×256-vs-512×512 tile explainer and the Mapbox zoom-level glossary
  for tile sizing; browser canvas-size-limit references (pqina.nl, Apple Developer Forums, testmuai.com) for
  the real Chrome/Firefox/Safari ceilings cited in §B's terrain-chunking revision.
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
