---
status: active
layer: engine
authority: P1
audience: developer
---

# Frontend: Real-time Visualization

The WorldLoop Frontend is a high-performance React application built with **Vite** and **TypeScript**. It utilizes the **HTML5 Canvas API** to render thousands of entities and world objects at 60 FPS.

> **Known gap (2026-07-16), narrowed 2026-08-24, narrowed further 2026-08-24, closed for delta sync 2026-08-25:** the frontend's `useSimulation.ts` hook (§2 below) calls `/map`, `/static`, `/manifest`, `/stats`, `/speed`, `/clear_events`, `/control/pause`, `/control/resume`, and connects to `/api/v1/ws` for delta sync. As of `TCK-20260821-REST-MAP-STATIC-STATS`, `/map`, `/static`, and `/stats` exist as real routes in `src/api/server.py`. `/speed` and `/clear_events` remain missing (explicitly out of scope for that ticket, deferred to HUD-tied scope). As of `TCK-20260821-WS-ENTITY-DELTA-BROADCAST`, the backend half of the delta-sync gap closed: a real per-tick entity-delta broadcast (`changed`/`removed`/`tick`/`snapshot_as_of_tick`) exists on `/api/v1/ws`. As of `TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET`, the frontend half is also closed: `useSimulation.ts` now connects to the real `/api/v1/ws` WebSocket (§B below) instead of the never-existent `/api/v1/stream` SSE route. Two real, disclosed blockers still prevent live end-to-end verification of this connection today, neither fixed by that ticket: (1) fail-closed API-key auth (`TCK-20260823-HTTP-API-KEY-AUTH`) gates every route this hook calls, and the frontend has zero key-wiring anywhere; (2) `frontend/vite.config.ts`'s dev proxy does not set `ws: true`, so even with a key the dev-server proxy would not forward the WS upgrade. See `docs/plans/world_rendering/idea_world_rendering_core.md` for a proposed server-owned rendering core that would either reconnect this frontend (implementing its remaining missing routes, including the two blockers above) or supersede it with a new client — not yet decided.

---

## 1. Technology Stack

- **Core**: React 18, TypeScript 5.
- **Rendering**: Custom Canvas rendering engine (`useCanvas.ts`).
- **Real-time**: WebSocket (`/api/v1/ws`) for state deltas.
- **Styling**: Tailwind CSS (for UI overlays) + CSS Modules.
- **Icons**: Lucide React.

---

## 2. The `useSimulation` Hook

Central to the frontend is the `useSimulation` custom hook, which manages the lifecycle of the simulation connection.

### A. Initial Load (Full State)
On mount, the hook's `status` starts at `INITIALIZING` (`useState<SimStatus>('INITIALIZING')`).
`loadInitial()` sets `status` to `FETCHING_WORLD_DATA` as its first synchronous action, before any
fetch is issued, then performs three critical fetch calls joined into one `Promise.all`:
1.  **`/api/v1/map`**: Fetches the RLE-encoded tile grid.
2.  **`/api/v1/static`**: Fetches all persistent world objects (Buildings, Resource Nodes, Treasure Chests).
3.  **`/api/v1/manifest`**: Fetches the versioned ID-to-meaning lookup table (`terrain_types`,
    `entity_kinds`, `building_types`; `location_types` intentionally omitted — no backend registry
    exists for it, see `stored_artifacts/TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT/investigation.md`
    and `plan.md`). `terrain_types` is keyed by the same int codes `/api/v1/map`'s RLE grid uses.
    The fetched value is stored in hook state (`manifest`) but not yet consumed by any
    rendering/color logic — retiring `colors.ts`'s hardcoded maps to consume it is a fast-follow.

**Bounded retry / failure (`TCK-20260821-PHASED-LOADING-STATE-MACHINE`)**: if any of the three
fetches fails, `loadInitial()` retries at a fixed 1000ms delay, tracked by a `retryCountRef` counter.
After `LOAD_RETRY_LIMIT` (5) consecutive failures, `status` transitions to the terminal `LOAD_ERROR`
value and `loadInitial` is never invoked again for the lifetime of the mount — there is no retry
button and no automatic recovery short of a full page reload (which remounts the hook and resets the
counter).

### B. Delta Sync (WebSocket)
Once the base data is loaded, the hook opens a `WebSocket` to `/api/v1/ws` (derived from
`window.location` since `WebSocket`, unlike `fetch`, requires an absolute `ws://`/`wss://` URL and
cannot resolve a bare relative path).
- **Handshake**: On `onopen`, the hook sends `{"type":"handshake","format":"json"}` as its first
  outgoing message — the server (`src/api/ws/stream.py::stream_ws`) blocks on this and closes the
  connection (code 1003) if it is missing or malformed. `"json"` was chosen explicitly over
  `"msgpack"`: no msgpack decode library exists in `frontend/package.json`, and the server already
  defaults to `"json"` if the field is present but unrecognized.
- **Initial message**: immediately after the handshake, the server sends one full-state-shaped
  summary message (`{tick, world_time, entities_count, maturity, seed}`) before entering its
  per-tick delta loop. The hook distinguishes this from a delta by shape — `Array.isArray(data.changed)
  && Array.isArray(data.removed)` — rather than by message order, and treats a non-delta message as
  a no-op (it does not reduce it into `entities`/`aliveCount`/`events` state).
- **`onmessage` (delta path)**: Receives a JSON delta containing `changed` and `removed` entity
  lists (plus `tick`, `events`, `snapshot_as_of_tick`, and an always-`null` `region_id` the hook
  does not yet consume).
- **State Reconciliation**: A `Map` is used to efficiently upsert changed entities into the local
  React state, minimizing re-renders. The real per-entity payload
  (`StatePresenter.present_entity_slim`) omits `state`, `tier`, `combat_target_id`,
  `loot_progress`, and `loot_duration` (no confirmed V2 source); the hook explicitly defaults these
  five fields (`'' `/`0`/`null` as appropriate) when constructing the `EntitySlim` object it stores,
  so downstream consumers (`useCanvas.ts`) keep seeing a fully-populated shape.
- **Reconnect**: on `onclose` or `onerror`, the hook closes the socket (if not already closed) and
  reconnects after 2000ms, mirroring the prior SSE reconnect behavior. This reconnect loop is
  **deliberately left unbounded** by `TCK-20260821-PHASED-LOADING-STATE-MACHINE` — unlike
  `loadInitial()`'s new bounded retry (§2.A above), there is no `LOAD_ERROR`-equivalent terminal
  status for repeated WS reconnect failures. This is a stated, reviewed asymmetry: `loadInitial()` is
  a one-shot initial load where silent infinite retry is a real defect, while `scheduleReconnect()` is
  the steady-state reconnect path for an already-running live-view client, where indefinite background
  retry is the correct behavior.

**Status wiring (`TCK-20260821-PHASED-LOADING-STATE-MACHINE`)**: `SimStatus` transitions are now
tied directly to this lifecycle — `status` becomes `CONNECTING_LIVE` at the start of `connectWS()`
(before the socket is constructed), `SYNCING` on `onopen` immediately after the handshake is sent,
and `READY` on the first message that passes the `isDelta` shape-guard above (unconditionally on
every subsequent delta too, not gated behind a first-time-only flag — the reducer's own delta
detection is the sole trigger, not a separately invented one). `READY` is a transient handoff
marker, not a permanent status: the secondary `fallbackPoll` (§2.C) overwrites it with
`RUNNING`/`PAUSED`/`STOPPED` within its next 500ms tick once `/stats` confirms simulation state.

> Two real, disclosed blockers prevent live verification of this connection against a running dev
> server today, neither fixed by `TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET`: fail-closed
> API-key auth gates every route this hook calls and the frontend has no key-wiring anywhere
> (`TCK-20260823-HTTP-API-KEY-AUTH`), and `frontend/vite.config.ts`'s dev proxy does not set
> `ws: true`, so it would not forward the WS upgrade even with a key. Both are out of scope for
> that ticket; only the mocked-`WebSocket` unit/integration test suite (`useSimulation.test.tsx`)
> and `npm run build` verify this section's behavior today.

### C. Inspection Polling
When a user selects an entity, a secondary slow-poll (500ms) is triggered:
- **`/api/v1/state?selected={id}`**: Fetches the `FullSchema` for the selected entity, enabling the detailed "Cognitive Inspect" sidebar.

---

## 3. Rendering Engine (`useCanvas`)

The `useCanvas` hook manages the main 2D viewport.

- **Tile Layer**: Renders the base grid (Forest, Water, Road, etc.) using a cached off-screen canvas for static tiles.
- **Entity Layer**: Renders actor icons, HP bars, and state labels.
- **Interpolation**: While the simulation ticks at 12 TPS, the renderer uses **linear interpolation (lerp)** to ensure smooth movement between tick positions at 60 FPS.
- **Culling**: Only tiles and entities within the current camera frustum are drawn.

---

## 4. UI Components

- **Loading Gate**: `GameCanvas` is mounted inside `SimulationLoadingGate`
  (`frontend/src/components/SimulationLoadingGate.tsx`, added by
  `TCK-20260821-PHASED-LOADING-STATE-MACHINE`), which renders phase-specific loading text for
  `INITIALIZING`/`FETCHING_WORLD_DATA`/`CONNECTING_LIVE`/`SYNCING`, a distinct error UI for
  `LOAD_ERROR`, and `GameCanvas` itself (via `children`) for every other status
  (`READY`/`RUNNING`/`PAUSED`/`STOPPED`) — gated on a loading-status allowlist rather than literal
  `status === 'READY'` equality, since `READY` is transient (see §2.B).
- **Control Bar**: Allows the user to `PAUSE`, `RESUME`, and adjust the `TPS` (Ticks Per Second).
  Only `pause`/`resume` map to real backend routes (`POST /api/v1/control/pause`,
  `POST /api/v1/control/resume`) — `ControlPanel.tsx`'s `start`/`step`/`reset` buttons have no
  corresponding backend route (pre-existing gap, not introduced by
  `TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET`, but now honestly documented since that ticket
  removed `sendControl`'s prior generic dispatcher and replaced it with an explicit
  pause/resume branch, falling to a logged no-op for any other action).
- **World Log**: A real-time scrolling list of global events (Kills, Level ups, Region discoveries).
- **Inspector Sidebar**: Displays the selected entity's "Brain" state, Equipment, and Combat History.
- **Minimap**: A high-level overview of entity clusters and fog-of-war.

---

## 5. State Handling Strategy

To prevent "React Lag" during high-frequency updates:
1.  **Refs for Hot Data**: Tick count and raw entity maps are stored in `useRef` and only synced to `useState` at a controlled frequency.
2.  **Memoization**: The Canvas renderer is passed the raw data and only re-draws when the `tick` or `camera` state changes.
3.  **Event Throttling**: UI-only events (like hover highlights) are debounced to ensure they don't block the main rendering loop.
