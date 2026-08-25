---
status: historical
layer: frontend
authority: P2
audience: agent
ticket_id: TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET
artifact_type: investigation
tags: [websocket, engine]
---

# Investigation — TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET

## Context Scan Note

Per CLAUDE.md's mandatory Context Scan, `mcp__knowledge-search__search_docs` was called first
(`query: "useSimulation websocket frontend rewire map static delta"`) and returned
`{"error":"index not found","action":"run make knowledge-index"}` — the knowledge-search index is
not built in this worktree. `graphify query "useSimulation websocket frontend"` was called next and
failed with `error: graph file not found: .../graphify-out/graph.json` — no graph has been built in
this worktree (`graphify-out/` does not exist). Both mandatory tools are confirmed unavailable here,
matching the task's own framing. Fell through to the documented fallback: read the 5 done sibling
tickets, the in-progress ticket, the epic plan doc, and the actual source files directly.

## Current Behavior

### `frontend/src/hooks/useSimulation.ts` (current, pre-rewire)
- `loadInitial()` (lines 86-116): already fetches `/map`, `/static`, `/manifest` via one
  `Promise.all` (this was added by the already-done `TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT`
  ticket) — decodes the RLE grid, sets `buildings`/`resourceNodes`/`treasureChests`/`regions`/
  `manifest`. This part is already correct against the real backend and must be preserved
  unchanged; it is not itself in this ticket's Scope.
- Delta stream (lines 119-268): opens `new EventSource('/api/v1/stream')` (line 127) — this route
  does not exist on the real backend at all (confirmed absent from every `@router`/`@app` decorator
  in `src/api/routes/*.py`, `src/api/server.py`, `src/api/ws/*.py`). `onmessage` (lines 129-169)
  JSON-parses `event.data` into `{tick, changed, removed, events}` and reduces it into `entities`/
  `aliveCount`/`tick`/`events` state exactly as this ticket's AC describes ("keep existing
  changed/removed reducer logic"). `onerror` (lines 171-174) closes and `setTimeout(connectStream,
  2000)` — the reconnect behavior this ticket's AC requires the WS version to mirror.
  `fallbackPoll` (lines 181-260, `setInterval(fallbackPoll, 500)`) separately fetches `/stats` and
  `/state?since_tick=...&selected=...` — **out of this ticket's Scope entirely** (not mentioned in
  Scope, and Out of Scope only names `/speed`/`/clear_events` explicitly, but by the ticket's own
  narrow framing `/stats`/`/state` polling is untouched too).
- `sendControl` (lines 270-276): `fetch(`${API_BASE}/control/${action}`, {method:'POST'})` — a
  generic string-templated dispatcher. `setSpeed`/`clearEvents` (lines 278-298) are separate,
  explicitly Out of Scope.

### Real backend WS contract (`src/api/ws/stream.py::stream_ws`, `/api/v1/ws`)
- `await websocket.accept()`, then `handshake = await websocket.receive_json()`; if
  `handshake.get("type") != "handshake"` → `websocket.close(code=1003, reason="Missing handshake")`.
  `fmt = handshake.get("format", "json")`. This is a **strict, blocking first-message
  requirement** — the client's first outgoing message must be exactly
  `{"type":"handshake","format":"json"|"msgpack"}` or the server closes the connection immediately.
- **The very next thing the server sends, unconditionally, before entering its per-tick delta
  loop**: `initial_payload = manager.get_state()` (full-state shape, not the slim delta shape),
  sent via `send_json`/`send_bytes` depending on `fmt`. Only after that does the `while True: payload
  = await queue.get()` per-tick delta loop begin, each message being
  `{tick, changed, removed, events, snapshot_as_of_tick, region_id}` (region_id always `null`,
  added by `TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD`).
- **This is a real shape difference the new `onmessage` handler must account for that the old SSE
  code never had to**: under SSE, every message on the stream was delta-shaped. Under the real WS
  contract, the *first* post-handshake message is a differently-shaped full-state payload; treating
  it as a delta (running it through the `changed`/`removed` reducer as-is) would either throw or
  silently corrupt state, since `manager.get_state()`'s shape is not `{changed, removed}`.
- **Auth gate**: `stream.router` is registered with `dependencies=[Depends(require_api_key_ws),
  Depends(require_admission_ws)]` (`src/api/server.py:101`). `require_api_key_ws`
  (`src/api/auth.py:110-125`) accepts the key via `X-API-Key` header **or** a `key` query parameter
  (browsers' native `WebSocket()` constructor cannot set custom headers), and raises
  `WebSocketException(code=1008, reason="Invalid or missing API key.")` on failure. See Risks below
  — this is real and currently unaddressed anywhere in the frontend.

### Real backend control routes (`src/api/server.py:230-238`)
Only two exist: `POST /api/v1/control/pause` and `POST /api/v1/control/resume`, both gated by
`require_admission` (→ `require_api_key`, **header-only**, no query fallback — this is not one of
the 3 dashboard/3-websocket routes that get the query-param exception). No `/start`, `/step`,
`/reset` route exists anywhere in `src/api/server.py` or `src/api/routes/*.py` (confirmed by grep).

### `frontend/src/components/ControlPanel.tsx` (out of scope, not modified, but a real consumer)
Calls `sendControl('start')`, `sendControl('pause')`, `sendControl('resume')`, `sendControl('step')`,
`sendControl('reset')` — **5 actions, not 2**. Only `pause`/`resume` have ever had (or will have) a
real backend route; `start`/`step`/`reset` were already effectively broken under the old generic
dispatcher (`/api/v1/control/start` etc. never existed on the real backend either) and remain
equally broken after this ticket — **not a regression this ticket introduces**, since the ticket's
own Assumptions section already flagged this exact grep as needed. The safe implementation is an
explicit branch on the action string (pause → one POST, resume → one POST, anything else → no-op,
matching today's effectively-silent failure via the existing `try/catch`+`console.error`), not a
generic dispatcher.

### `frontend/src/types/api.ts` `EntitySlim` (lines 88-103) vs. real WS payload
Declares 14 fields (`id, kind, x, y, hp, max_hp, state, level, tier, faction, weapon_range,
combat_target_id, loot_progress, loot_duration`). The real backend's
`StatePresenter.present_entity_slim` (`src/api/presenters/state_presenter.py:133-158`) — built by
the already-done `WS-ENTITY-DELTA-BROADCAST` ticket — emits only **9** of them: `id, kind, x, y, hp,
max_hp, level, faction, weapon_range`. Its own docstring is explicit: *"state, tier,
combat_target_id, loot_progress, loot_duration, display_name have no confirmed V2 source and are
dropped."* Confirmed real consumers of the missing 5 fields in `frontend/src/hooks/useCanvas.ts`
(out of scope, not modified): `ent.combat_target_id` (lines 208-212, combat target-line rendering),
`STATE_COLORS[ent.state]` (line 267, falls back to `'#888'` when `undefined` — safe), `ent.state ===
'LOOTING' && ent.loot_progress > 0` (lines 335-336, loot-progress-bar gating — silently `false` when
`undefined`, so the bar never renders — safe but a real, currently-inherited visual gap, not new to
this ticket), and `parts.push(ent.state)` (line 618, tooltip text — pushes a literal `undefined`
into a tooltip string array, a minor pre-existing cosmetic gap). See Risks/Open Questions.

### Frontend test infrastructure (checked directly, not assumed)
`frontend/package.json` has `vitest ^4.0.18`, `@testing-library/react ^16.3.2`,
`@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom ^28.1.0` as real, already-used
devDependencies. `frontend/vite.config.ts`'s `test` block is configured
(`environment: 'jsdom', globals: true, setupFiles: './src/test/setup.ts'`).
`frontend/src/test/setup.ts` wires `@testing-library/jest-dom` + `afterEach(cleanup)`. The **only**
existing frontend test file is `frontend/src/test/useSimulation.test.tsx` (2 tests), which mocks
`globalThis.fetch` and defines a hand-rolled `MockEventSource` class assigned to
`globalThis.EventSource` — entirely shaped around the old SSE contract, matching this ticket's own
Scope line: *"Rewrite frontend/src/test/useSimulation.test.tsx against a mocked WebSocket (both
existing tests are written against the old EventSource/SSE contract and are not reusable as-is)."*
No other frontend test file exists (`frontend/src/test/` has exactly these two files — confirmed by
directory listing). No Playwright/e2e config exists anywhere in `frontend/`. `package.json` has no
`"test"` script defined (only `dev`/`build`/`lint`/`preview`); vitest must be invoked directly
(`npx vitest run <path>`), which works fine as a devDependency without a script entry.

### `frontend/vite.config.ts` dev proxy (not in Related Code Areas, found while investigating)
The `/api` proxy block (`server.proxy['/api']`) sets `target`/`changeOrigin` but **not `ws: true`**.
Vite's dev-server proxy (built on `http-proxy`) does not forward WebSocket upgrade requests unless
`ws: true` is explicitly set on the proxy entry. See Risks below.

## Mechanics / Engine Constraints

None of the Mechanics Bible chapters (`docs/mechanics/`) or Engine Contracts (`docs/engine/`)
constrain this ticket's own diff — it is a pure frontend transport/reducer rewire, touching no
simulation law, formula, or kernel-pipeline behavior. The one relevant contract is
`docs/engine/contracts/frontend.md`, which documents the `useSimulation` hook's own contract (see
Docs Requiring Update) — not a Mechanics Bible chapter, but the closest thing to an authoritative
spec for this file's expected behavior.

## Docs Requiring Update

- `docs/engine/contracts/frontend.md`: §1's "Real-time: EventSource (SSE) for state deltas" bullet
  and §2B "Delta Sync (SSE)" section both still describe the pre-rewire SSE transport as current
  (with a disclosure note that the rewire is tracked separately in this ticket). Once this ticket
  lands, both must be rewritten to describe the real WebSocket client (handshake, chosen format,
  reconnect behavior) instead of SSE, and the disclosure note removed/resolved. §4's "Control Bar"
  line ("Allows the user to PAUSE, RESUME, and adjust the TPS") should also gain a note that only
  `pause`/`resume` map to real backend routes (the `start`/`step`/`reset` buttons visible in
  `ControlPanel.tsx` do not correspond to any real backend action, pre-existing and unrelated to
  this ticket, but worth being honest about in the doc since this ticket is what defines the real
  `sendControl` contract going forward).

The `docs/parity_ledger/infrastructure.yaml` entries `INFRA-386`/`INFRA-387`/`INFRA-388` (path:
`docs/parity_ledger/infrastructure.yaml`, under `docs/`) are not required to change for this ticket:
they already fully document the backend contracts (manifest, REST routes, WS delta broadcast) this
ticket is purely a *consumer* of — this ticket makes zero backend-behavior changes, and the parity
ledger tracks backend-logic-vs-doc parity, not frontend consumption. This matches the precedent set
by `TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT`, whose own `useSimulation.ts` touch (adding the
`/manifest` fetch) added no new/updated parity-ledger entry for the frontend half either.

The `docs/architecture/http_api_key_authentication.md` doc (path:
`docs/architecture/http_api_key_authentication.md`, under `docs/`) is not required to change for
this ticket: this ticket does not add any API-key wiring to the frontend (see Risks/Open Questions
below for why that gap exists and is being deliberately left as an open question rather than
silently resolved inside this ticket's scope) — no auth-mechanism behavior changes in this ticket's
diff.

## Parity Ledger Overlap

- `INFRA-386` (P2, `verified`) — `GET /api/v1/manifest`. This ticket's `loadInitial()` already
  fetches it (landed by ticket 2); no change needed to this entry.
- `INFRA-387` (P1, `verified`) — `/api/v1/map`, `/api/v1/static`, `/api/v1/stats`. `loadInitial()`
  already fetches `/map`/`/static`; `fallbackPoll` already fetches `/stats` — both untouched by this
  ticket's Scope. No change needed.
- `INFRA-388` (P1, `verified`) — `/api/v1/ws` per-tick delta broadcast
  (`{tick,changed,removed,events,snapshot_as_of_tick,region_id}`), including the documented
  `state`/`tier`/`combat_target_id`/`loot_progress`/`loot_duration` drop from `EntitySlim`. This is
  the exact payload shape this ticket's rewired `onmessage` handler must consume. No P0 entries are
  touched by this batch (all three are P1/P2); none require a new/updated `test_path` from this
  ticket.

## Prior Work

- `stored_artifacts/TCK-20260821-WS-ENTITY-DELTA-BROADCAST/plan.md`'s "Open Design Question 2" is
  the authoritative record of the `EntitySlim` field-drop decision (`state`/`tier`/
  `combat_target_id`/`loot_progress`/`loot_duration`) — cite it rather than re-litigating the
  decision; this ticket only needs to decide how the *frontend type* should reflect that reality
  (see Risks).
- `stored_artifacts/TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT/`'s own disclosed gap ("`loadInitial()`
  has zero existing test coverage anywhere in this codebase... this is a structural gap in the
  project's frontend test harness") is directly relevant precedent for this ticket's own test_plan.md
  honesty about what can/cannot be automated-tested.
- No prior ticket in this repo has touched `useSimulation.ts`'s transport layer (`EventSource`/`WS`)
  or its test file — this is the first.

## Risks and Open Questions

1. **Real, not blocking this ticket's own AC, but should be surfaced loudly**: `/api/v1/ws` and
   every REST route this hook calls (`/map`, `/static`, `/manifest`, `/stats`, `/control/pause`,
   `/control/resume`) are gated by `TCK-20260823-HTTP-API-KEY-AUTH`'s **fail-closed** auth
   (`RuntimeProfile.api_key_hashes` defaults to `""`, and the doc string is explicit: *"Empty string
   means no keys configured -- every protected route then 401s for every caller"*). The frontend has
   **zero** API-key wiring anywhere today (confirmed: no `X-API-Key`/`key=` usage anywhere under
   `frontend/src/`). This ticket's Scope/Related Code Areas say nothing about auth. **This means a
   perfectly-correct implementation of this ticket's own AC will still fail to connect against any
   real running backend** — the WS handshake will never even be attempted before
   `require_api_key_ws` closes the connection with code 1008, and REST fetches will 401. This is an
   open question for planner/implementer, not something to resolve unilaterally inside this ticket:
   either (a) land this ticket exactly as scoped, verified only against a mocked WebSocket in vitest,
   explicitly disclosing that live end-to-end verification against a real authenticated server is not
   currently possible without a follow-up ticket, or (b) fold in minimal key-wiring now. Do not
   silently pick (b) — it is real scope expansion beyond "swap EventSource for WebSocket... map
   pause/resume."
2. `frontend/vite.config.ts`'s dev proxy (`server.proxy['/api']`) does not set `ws: true`. Vite's
   proxy will not forward WebSocket upgrade requests without it — so even once (1) above is resolved
   and this ticket's own code is correct, `npm run dev` still cannot reach `/api/v1/ws` through the
   dev proxy. Not in Related Code Areas. Recommend adding `ws: true` to that one proxy block as a
   minimal, tightly-coupled fix, but flag it as a scope decision for planner rather than assuming
   it's included.
3. `EntitySlim`'s type/reality mismatch (5 declared fields the real payload never sends — see Current
   Behavior). Recommend marking `state`, `tier`, `combat_target_id`, `loot_progress`,
   `loot_duration` optional (`?:`) in `frontend/src/types/api.ts` (already in Related Code Areas) so
   the type accurately reflects what the WS delta actually carries, instead of silently declaring
   fields required that are never populated. This does not force any change to `GameCanvas.tsx`'s
   logic (its existing reads already degrade safely on `undefined`), so it doesn't cross the
   GameCanvas/useCanvas Out-of-Scope boundary — but it's a real decision, flagged for planner rather
   than assumed.
4. msgpack vs. json handshake format (ticket's own open Assumption, must be resolved by this ticket):
   no msgpack decode library exists anywhere in `frontend/package.json` today. Recommend `"json"` —
   zero new dependency, and the epic plan doc explicitly treats msgpack as a bandwidth optimization
   that's fine to defer (`docs/plans/live_map_reconnection_epic.md`'s "Real-Time Transfer" section:
   *"Actually use the msgpack format... near-free wire-size reduction... the format path exists
   today"* — framed as available, not mandatory). This is a recommendation, not a blocking question —
   the ticket explicitly asks this ticket to make the call.
5. The real WS connection's first post-handshake message is full-state-shaped
   (`manager.get_state()`), not delta-shaped — see Current Behavior. The new `onmessage` handler must
   distinguish this first message from subsequent delta messages (e.g. via a "have we received the
   first message yet" flag, or by checking for the presence of `changed`/`removed` keys) or it will
   attempt to reduce an incompatible shape. This has no old-SSE-code precedent to port from — it's
   new logic this ticket must add.

## Anti-Drift Hazards

- Do not touch `frontend/src/components/GameCanvas.tsx` or `frontend/src/hooks/useCanvas.ts` (hard
  Out of Scope) — verify with a diff-scope check, not just intent.
- Do not modify `/state`'s query-param-ignoring behavior, `fallbackPoll`, or its `/stats`/`/state`
  fetches — real, pre-existing gap (the epic doc's own finding #3), explicitly out of this ticket's
  narrow Scope.
- Do not remove or alter the `/manifest` fetch or `manifest` state added by
  `TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT` — easy to lose in a broad rewrite of the same file.
- Do not reintroduce a generic `/api/v1/control/${action}`-style dispatcher in any form, including as
  a "temporary" fallback for `start`/`step`/`reset` — the AC is explicit: "no generic dispatcher
  introduced."
- Do not touch `/speed` or `/clear_events` call sites (`setSpeed`, `clearEvents`) — hard Out of
  Scope.
- Do not conflate this ticket with `TCK-20260821-PHASED-LOADING-STATE-MACHINE` (ticket 8 in this
  batch, not yet started) — `SimStatus` stays exactly `'CONNECTING' | 'RUNNING' | 'PAUSED' |
  'STOPPED'`; do not add new status values or a state machine here.
- Do not silently add API-key/auth wiring to resolve Risk 1 above without an explicit scope decision
  — resist "fixing" the 401/1008 problem inside this ticket.
