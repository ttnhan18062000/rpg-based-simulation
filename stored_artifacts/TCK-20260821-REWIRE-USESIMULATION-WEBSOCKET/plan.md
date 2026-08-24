---
status: historical
layer: frontend
authority: P2
audience: agent
ticket_id: TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET
artifact_type: plan
tags: [websocket, engine]
---

# Implementation Plan — TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET

## Summary

This is a frontend-only rewire of `frontend/src/hooks/useSimulation.ts`'s delta-stream transport
from a nonexistent `EventSource('/api/v1/stream')` to the real `WebSocket('/api/v1/ws')` contract
implemented by `src/api/ws/stream.py::stream_ws` (`src/api/ws/stream.py:18-87`). The approach: (1)
add a `WireEntitySlim` type for parsing the raw WS payload (5 fields optional, matching what the
backend actually sends) while `EntitySlim` itself — the type `useCanvas.ts` and every other
consumer already compiles against — stays completely unchanged, with the merge logic in (3)
explicitly constructing fully-populated `EntitySlim` objects before they ever reach hook state, (2)
replace the `EventSource`
connection block with a `WebSocket` connection that sends the required handshake as its first
outgoing message, (3) add new `onmessage` branching logic that distinguishes the WS connection's
first post-handshake message (a full-state-shaped summary, never delta-shaped) from every
subsequent per-tick delta message, reusing the existing changed/removed reducer only for the
latter, (4) mirror the existing `onerror`/`setTimeout` reconnect behavior onto `onclose`/`onerror`,
(5) replace the generic `sendControl(action)` string-templated dispatcher with an explicit
pause/resume branch, dropping to a no-op+log for the three actions (`start`/`step`/`reset`) that
have never had a real backend route, and (6) rewrite the test file end-to-end against a mocked
`WebSocket`. `loadInitial()` (`/map`, `/static`, `/manifest`), `fallbackPoll` (`/stats`, `/state`),
`setSpeed`, and `clearEvents` are all preserved byte-for-byte — none of them are in this ticket's
Scope. No backend file needs to change: `src/api/ws/stream.py` and the two `/control/pause`,
`/control/resume` routes in `src/api/server.py:230-237` already implement everything this hook
needs to consume (delivered by the already-done `TCK-20260821-WS-ENTITY-DELTA-BROADCAST` and
`TCK-20260821-REST-MAP-STATIC-STATS`); `src/api/ws/stream.py` and `src/api/server.py` appear in the
ticket's Related Code Areas only as read-reference for the real contract, not as edit targets.

## Design Decisions (resolving investigation.md's open questions)

### 1. `EntitySlim` type mismatch — add a separate `WireEntitySlim` type; `EntitySlim` stays untouched

`frontend/src/types/api.ts:88-103` currently declares `EntitySlim` with 14 required fields. The
real WS delta payload's per-entity dicts are built by
`StatePresenter.present_entity_slim` (`src/api/presenters/state_presenter.py:132-158`), which
returns exactly 9 keys — `id, kind, x, y, hp, max_hp, level, faction, weapon_range` — and its own
docstring (`state_presenter.py:136-140`) states `state, tier, combat_target_id, loot_progress,
loot_duration, display_name have no confirmed V2 source and are dropped`.

**Decision (revised — a first draft of this decision, making these 5 fields optional directly on
`EntitySlim`, was rejected twice by architecture-review: it broke `tsc -b` in `useCanvas.ts`, and a
follow-up attempt to paper over that with a runtime `?? ''`/`?? 0` default inside the merge logic
also failed, since a runtime default at one call site cannot narrow a type-level `T | undefined`
for a separately-typed downstream consumer — TypeScript checks the declared type structurally, not
by tracing which setter produced a given value):** introduce a new type, `WireEntitySlim`, used
*only* to parse the raw `data.changed[]` array elements in Step 3's `onmessage` handler — it has
the 5 unsourced fields optional, everything else identical to `EntitySlim`. `EntitySlim` itself is
left **completely unchanged** — all 14 fields stay required, exactly as before this ticket. Step
3's merge logic explicitly constructs a fully-populated `EntitySlim` object (defaulting the 5
fields via `??`) before it is ever stored into the hook's `entities` state, so `useCanvas.ts` (and
every other existing consumer) never sees `WireEntitySlim` and needs zero changes or even awareness
that this ticket touched the wire shape. Deleting the 5 fields outright was also rejected: it would
still require touching every read site (`useCanvas.ts:208-212,267,335-336,618`, confirmed in
investigation.md's Current Behavior section) since TypeScript would then error on unknown
properties, which is exactly the Out-of-Scope violation this design avoids. `display_name` is not
currently declared on `EntitySlim` at all (`api.ts:88-103` has no such field) so there is nothing
to change for it.

### 2. msgpack vs. json handshake format — pick `"json"` explicitly

Decision: the hook sends `{"type":"handshake","format":"json"}` as its first outgoing message.
Rationale: no msgpack decode library exists anywhere in `frontend/package.json` today (confirmed by
investigation.md's dependency check); adding one would be new-dependency scope creep this ticket's
own Scope line ("send the required handshake message... pick and document one format explicitly")
does not ask for. `src/api/ws/stream.py:36` (`fmt = handshake.get("format", "json")`) already
defaults to `"json"` server-side if the field were omitted, but the AC requires sending the
handshake explicitly, so `format: "json"` must be included literally, not omitted. This is
consistent with the epic plan doc's own framing of msgpack as a deferrable bandwidth optimization,
not a functional requirement.

### 3. First-message-is-full-state-not-delta — explicit shape check, not an ordinal flag

The real server sends `initial_payload = manager.get_state()` immediately after handshake
(`src/api/ws/stream.py:56-63`), which resolves to `ReadModelCache.get_minimal_summary`
(`src/api/engine_manager.py:196-201`) → `StatePresenter.present_minimal`
(`src/api/presenters/state_presenter.py:15-23`): `{tick, world_time, entities_count, maturity,
seed}` — no `changed`/`removed` keys. Every subsequent per-tick message
(`src/api/ws/stream.py:65-79`) is `dict(payload)` with `snapshot_as_of_tick` and `region_id` added
on top of the `compute_tick_delta` shape, which always has `changed` and `removed` as arrays.
Decision: branch on shape, not on message order — `Array.isArray(data.changed) &&
Array.isArray(data.removed)` selects the delta path; anything else (including the initial summary)
is treated as a non-delta message and is a no-op for `entities`/`aliveCount`/`events` state (it does
not throw, and it does not touch those three pieces of state). This is more robust than a "have we
seen the first message yet" boolean, because it doesn't silently misclassify a message if ordering
assumptions are ever violated (e.g. a future reconnect race), and it exactly matches what
`test_plan.md` test 3 asks for: "does not crash the reducer and does not corrupt subsequent delta
processing."

### 4. `sendControl`'s 5 actions vs. 2 real routes — explicit branch, not a generic dispatcher

`frontend/src/components/ControlPanel.tsx` (confirmed via `grep -n sendControl
frontend/src/components/ControlPanel.tsx`) calls `sendControl('start')`, `sendControl('pause')`,
`sendControl('resume')`, `sendControl('step')`, `sendControl('reset')` — 5 actions. Only
`POST /api/v1/control/pause` and `POST /api/v1/control/resume` exist on the real backend
(`src/api/server.py:230-237`, confirmed by grep — no `/control/start`, `/control/step`,
`/control/reset` route exists anywhere in `src/api/server.py` or `src/api/routes/*.py`). Decision:
`sendControl` becomes an explicit `if (action === 'pause') { … } else if (action === 'resume') { …
} else { console.error(...); }` — no string-templated URL construction anywhere in the function.
This is a pre-existing gap (the `start`/`step`/`reset` buttons in `ControlPanel.tsx` were already
silently broken under the old generic dispatcher, since `/api/v1/control/start` etc. never existed
either) — this plan does not fix `ControlPanel.tsx` (Out of Scope, not modified) and does not add
new routes; it only ensures the rewritten `sendControl` fails the same way (silently, via existing
`try/catch` + `console.error`) rather than reintroducing a generic dispatcher, which AC 3 explicitly
forbids.

## Known, Disclosed Gaps to Live Verification (do not fix in this ticket)

Two real blockers prevent live end-to-end verification of this ticket's change against a running
dev server, confirmed independently by investigation.md and re-confirmed by this plan:

1. **Fail-closed API-key auth with zero frontend key-wiring.** `stream.router` in
   `src/api/server.py` and every REST route this hook calls are gated by
   `TCK-20260823-HTTP-API-KEY-AUTH`'s fail-closed auth (merged 2026-08-23, after this epic's
   design). `grep -r 'api.?key\|API_KEY' frontend/src/` returns nothing — no key-wiring exists
   anywhere in the frontend. A correct implementation of this ticket's own AC will still 401/1008
   against any real running backend.
2. **Vite dev proxy has no `ws: true`.** `frontend/vite.config.ts`'s `server.proxy['/api']` block
   (confirmed by direct read, lines 15-19) sets only `target`/`changeOrigin` — Vite's `http-proxy`
   based dev proxy does not forward WebSocket upgrade requests without `ws: true` explicitly set.

**Neither is fixed by this plan.** Both are out-of-scope security/infra concerns beyond this
ticket's remit (fixing them would be unscoped drive-by work). What this means for Verify:

- **CAN be verified in this ticket**: all 8 new/rewritten unit/integration tests in
  `frontend/src/test/useSimulation.test.tsx`, run via `cd frontend && npx vitest run
  src/test/useSimulation.test.tsx` — these exercise the hook against a mocked `globalThis.WebSocket`
  and mocked `globalThis.fetch`, never a real socket or real HTTP call, so neither blocker applies.
- **CANNOT be verified in this ticket**: connecting a real browser dev-server session
  (`npm run dev`) to a real running backend (`python -m src serve`) and observing live entities
  render. No Playwright/e2e harness exists in this repo to automate this even if the two blockers
  were resolved. This must be disclosed as a known gap in the ticket's Test Summary at Finalize, not
  silently treated as "tests pass" = "verified live."

## Steps

### Step 1 — Add a `WireEntitySlim` wire-parsing type; `EntitySlim` itself keeps `state`/
`loot_progress`/`loot_duration` required

**Files:** `frontend/src/types/api.ts`

**Architecture-review finding (second round), resolved for real this time:** a first attempt at
this step made `EntitySlim.state`/`.loot_progress`/`.loot_duration` optional on the type itself,
then tried to paper over the resulting `useCanvas.ts` compile break with a runtime `?? ''`/`?? 0`
default inside Step 3's merge logic. **This does not work** — `tsc` checks the *declared* type of
`useSimulation.ts`'s `entities` state (`useState<EntitySlim[]>`), which flows unchanged through
`GameCanvas.tsx` into `useCanvas.ts`; a runtime default at one specific call site cannot narrow a
type-level `string | undefined` back to `string` for a downstream consumer TypeScript checks
structurally, not by tracing which setter call produced a given value. The actual fix requires two
*separate* types: one for what the raw WS wire payload optionally contains, one for what the hook
promises its consumers (`useCanvas.ts` included) always has.

**Change:** Add a new type in `api.ts`, immediately after the `EntitySlim` interface:
```ts
type WireEntitySlim = Omit<EntitySlim, 'state' | 'tier' | 'combat_target_id' | 'loot_progress' | 'loot_duration'> & {
  state?: string;
  tier?: number;
  combat_target_id?: number | null;
  loot_progress?: number;
  loot_duration?: number;
};
```
This is the type used **only** to parse `data.changed[]` elements off the raw WS delta payload in
Step 3 (`present_entity_slim` never sends these 5 fields — `state_presenter.py:133-158` confirms
exactly 9 keys). `EntitySlim` itself (`api.ts:88-103`) is **left completely unchanged** — all
fields, including `state`, `loot_progress`, `loot_duration`, stay required, exactly as they are
today. This is what `useCanvas.ts` (and every other existing consumer) already assumes and compiles
against, so nothing downstream needs to change or even be aware this ticket touched the wire shape.

**Do NOT touch:** `EntitySlim`, `Entity`, `Building`, `ResourceNode`, `TreasureChest`, `WorldState`,
or any other interface in this file — only the new `WireEntitySlim` type is added.

**Verify:** No dedicated test asserts the TypeScript type directly (TS interfaces have no runtime
assertion), but test 4 (`reduces a real {tick,changed,removed,...} delta correctly`, from
test_plan.md) feeds a 9-field-only entity object through the reducer and asserts on
`entities[0].id`. The real compile-check gate is `npm run build` (`tsc -b && vite build`) — **an
explicit required step (Step 8)**, not assumed to pass implicitly; it must be run and confirmed
green before this ticket's Test phase can be considered complete, specifically to catch this exact
class of break (vitest's esbuild transform does not type-check, so the vitest-only command
test_plan.md names as its primary gate would not have caught this on its own). Step 8 is the actual
proof this fix works — a second architecture-review pass will re-run it independently, not just
re-read this text.

### Step 2 — Replace the `EventSource` connection with a `WebSocket` connection, handshake-first
**Files:** `frontend/src/hooks/useSimulation.ts`
**Change:** Inside the existing delta-stream `useEffect` (currently lines 119-268, dependency
`[mapData]`, guarded by `if (!mapLoadedRef.current && !mapData) return;` — keep this guard
unchanged), replace the `let evtSource: EventSource | null = null;` declaration and the
`connectStream` function's `EventSource` construction with a `WebSocket` construction. `WebSocket`,
unlike `fetch`, cannot resolve a bare relative path — it requires an absolute `ws://`/`wss://` URL.
Add a small helper (module-level or inline in the effect) that derives the URL from
`window.location`:
```ts
function wsBase(): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}${API_BASE}`;
}
```
`connectStream` becomes (renamed `connectWS` is fine, or keep the name — implementer's call, not
load-bearing):
```ts
let ws: WebSocket | null = null;
const connectWS = () => {
  ws = new WebSocket(`${wsBase()}/ws`);
  ws.onopen = () => {
    ws!.send(JSON.stringify({ type: 'handshake', format: 'json' }));
  };
  ws.onmessage = (event) => { /* Step 3 */ };
  ws.onclose = () => { /* Step 4 */ };
  ws.onerror = () => { /* Step 4 */ };
};
```
The handshake send MUST happen in `onopen` (the socket is not writable before the `open` event) and
MUST be the first `send()` call on the socket — no other `send()` call exists anywhere else in this
hook, so this is trivially satisfied as long as no other code path calls `ws.send(...)`.
**Other writers to this file:** `frontend/src/hooks/useSimulation.ts` is also listed under Related
Code Areas of two not-yet-started tickets in a separate epic — `TCK-20260822-DURABLE-SELECTION-STATE`
(extracts `selectedEntityId` state out of this hook into a shared model) and
`TCK-20260822-ENTITY-LIST-SEARCH-RANK` (reads/diffs this hook's data for entity ranking) — per
investigation.md's Cross-Epic Sequencing Note. Neither ticket has started; this plan does not need
to coordinate with in-flight edits to this file. The investigation's own recommendation (this
ticket lands first, since it rewrites the file's transport and reducer shape wholesale) still holds
and is not re-litigated here — it is a sequencing note for whoever picks up either of those two
tickets next, not an action item for this plan.
**Do NOT touch:** `loadInitial()` (lines 86-116), the `fallbackPoll` function or its `/stats`/
`/state` fetches (Out of Scope), `setSpeed`/`clearEvents` (Out of Scope).
**Verify:** test_plan.md tests 1 and 2 (`sends handshake as the first outgoing message before
processing any data`, `opens WebSocket to /api/v1/ws, not EventSource`).

### Step 3 — `onmessage`: branch on shape (delta vs. initial full-state), reduce only deltas
**Files:** `frontend/src/hooks/useSimulation.ts`
**Change:** Port the existing `changed`/`removed`/`events` reducer body (current
`useSimulation.ts:129-169`) into the new `ws.onmessage` handler, but gate it behind an explicit
shape check per Design Decision 3:
```ts
ws.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data);
    if (data.error) {
      console.error('Stream error:', data.error);
      return;
    }
    const isDelta = Array.isArray(data.changed) && Array.isArray(data.removed);
    if (!isDelta) {
      // Initial post-handshake message: manager.get_state() minimal-summary shape
      // ({tick, world_time, entities_count, maturity, seed}), not a delta. No entity/event
      // state to reduce here — intentionally a no-op beyond this point.
      return;
    }
    setTick(data.tick);
    setEntities((prev: EntitySlim[]) => {
      const entMap = new Map(prev.map(e => [e.id, e]));
      for (const id of data.removed) entMap.delete(id);
      for (const upd of data.changed as WireEntitySlim[]) {
        // present_entity_slim never sends state/loot_progress/loot_duration (dropped, ticket 4 —
        // no real V2 source exists). WireEntitySlim (Step 1) types these optional for parsing the
        // raw payload; the object constructed here must satisfy EntitySlim (all fields required —
        // the type useCanvas.ts, explicitly out of scope per AC 5, already compiles against
        // unchanged). '' never matches 'LOOTING', so useCanvas.ts's loot-progress-bar branch stays
        // dead code, same as today — this default is inert, not a fabricated value implying real
        // loot data exists.
        const full: EntitySlim = {
          ...upd,
          state: upd.state ?? '',
          tier: upd.tier ?? 0,
          combat_target_id: upd.combat_target_id ?? null,
          loot_progress: upd.loot_progress ?? 0,
          loot_duration: upd.loot_duration ?? 0,
        };
        entMap.set(full.id, full);
      }
      const next = Array.from(entMap.values());
      setAliveCount(next.length);
      return next;
    });
    if (data.events && data.events.length > 0) {
      setEvents((prev: GameEvent[]) => {
        const existingKeys = new Set(prev.map(e => `${e.tick}:${e.message}`));
        const fresh = data.events.filter((e: GameEvent) => !existingKeys.has(`${e.tick}:${e.message}`));
        return fresh.length > 0 ? [...prev, ...fresh] : prev;
      });
    }
  } catch (err) {
    console.error('Failed to parse WS payload:', err);
  }
};
```
`data.snapshot_as_of_tick` and `data.region_id` (present on every real delta message per
`src/api/ws/stream.py:72-74`) are intentionally read by neither this handler nor any other part of
this hook — they are not consumed by this ticket's Scope (no drift-detection or region-filtering
logic is being added here), and the reducer must tolerate their presence without erroring, which
this destructuring-free approach already does by construction.
**Do NOT touch:** the reducer's actual merge logic (`Map`-based upsert/delete pattern) — it is
"behaviorally unchanged" per AC 2, only re-hosted under the new shape guard.
**Verify:** test_plan.md test 3 (`ignores/threads the initial full-state message distinctly from
delta messages`) and test 4 (`reduces a real {tick,changed,removed,events,snapshot_as_of_tick,
region_id} delta correctly` — the exact four ported assertions: `entities.length`,
`entities[0].id`, `aliveCount`, `tick`). Covers AC 2 and the first-message half of AC 1.

### Step 4 — Reconnect on close/error, mirroring the old `onerror`/`setTimeout(2000)` behavior
**Files:** `frontend/src/hooks/useSimulation.ts`
**Change:** Add a reconnect scheduler shared by both `onclose` and `onerror`, guarded against
double-scheduling (since `WebSocket.onerror` in browsers/jsdom is typically followed by `onclose`
for the same failure, and both are independently tested per test_plan.md test 7):
```ts
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
const scheduleReconnect = () => {
  if (reconnectTimeout) return;
  reconnectTimeout = setTimeout(() => {
    reconnectTimeout = null;
    connectWS();
  }, 2000);
};
// inside connectWS():
ws.onclose = () => { scheduleReconnect(); };
ws.onerror = () => { ws?.close(); scheduleReconnect(); };
```
This mirrors the old `evtSource.onerror = () => { evtSource?.close(); setTimeout(connectStream,
2000); };` (`useSimulation.ts:171-174`) exactly in delay (2000ms) and in closing-before-scheduling
behavior, extended to also cover the `onclose` path (which `EventSource` does not expose as a
distinct event the old code used, but `WebSocket` does, and AC 4 says "on WS close/error").
Additionally: clear `reconnectTimeout` in the effect's cleanup function (alongside the existing
`if (pollInterval) clearInterval(pollInterval);`) so an in-flight scheduled reconnect does not fire
after unmount — this is a correctness property of the new code being written, not a fix to
old-code behavior (the old code had no reconnect-timeout cleanup either, but that is not being
ported forward as a bug; it is simply not being introduced fresh here).
**Do NOT touch:** `pollInterval`/`fallbackPoll`'s own lifecycle — keep the existing
`if (evtSource) evtSource.close(); if (pollInterval) clearInterval(pollInterval);` cleanup pattern,
just renaming `evtSource` to `ws` and adding the one new `clearTimeout(reconnectTimeout)` line.
**Verify:** test_plan.md test 7 (`reconnects after WebSocket close` and `reconnects after
WebSocket error`, via `vi.useFakeTimers()` + `vi.advanceTimersByTime(2000)`). Covers AC 4.

### Step 5 — Replace the generic `sendControl` dispatcher with an explicit pause/resume branch
**Files:** `frontend/src/hooks/useSimulation.ts`
**Change:** Replace the current `sendControl` (lines 270-276: `fetch(`${API_BASE}/control/${action}`,
{ method: 'POST' })`) with:
```ts
const sendControl = useCallback(async (action: string) => {
  try {
    if (action === 'pause') {
      await fetch(`${API_BASE}/control/pause`, { method: 'POST' });
    } else if (action === 'resume') {
      await fetch(`${API_BASE}/control/resume`, { method: 'POST' });
    } else {
      console.error(`Unsupported control action: ${action}`);
    }
  } catch (e) {
    console.error('Control error:', e);
  }
}, []);
```
Both URLs are literal strings, not template-interpolated from `action` — this is what makes the
dispatcher non-generic (test 6 and the grep guard below both check for this specifically). See
Design Decision 4 for why `start`/`step`/`reset` fall to the `else` branch rather than getting a
route.
**Other writers to this function's call sites:** `frontend/src/components/ControlPanel.tsx` is the
only caller of `sendControl` in the repo (confirmed by grep) and is Out of Scope — not modified by
this ticket. Its 5 call sites (`sendControl('start'|'pause'|'resume'|'step'|'reset')`) all continue
to compile and run against the new signature unchanged; only 2 of the 5 now hit a real route (as 2
of 5 always did, even under the old generic dispatcher, since `/control/start` etc. never existed
server-side either).
**Do NOT touch:** `setSpeed` (lines 278-284) or `clearEvents` (lines 291-298) — both explicitly Out
of Scope, and structurally adjacent to `sendControl` in the same file, making them easy to
accidentally touch in a broad edit. Confirm post-edit that both still target `/api/v1/speed` and
`/api/v1/clear_events` unchanged.
**Verify:** test_plan.md test 5 (`sendControl('pause') POSTs exactly to /api/v1/control/pause,
sendControl('resume') POSTs exactly to /api/v1/control/resume`) and test 6 (`sendControl with an
unrecognized action does not construct a generic /api/v1/control/{action} URL`), plus the grep
guard `grep -n 'control/\${' frontend/src/hooks/useSimulation.ts` (must return nothing). Covers AC 3.

### Step 6 — Rewrite `frontend/src/test/useSimulation.test.tsx` against a mocked `WebSocket`
**Files:** `frontend/src/test/useSimulation.test.tsx`
**Change:** Replace the existing `MockEventSource` class and `globalThis.EventSource` mock
(current lines 10-27) with a `MockWebSocket` class assigned to `globalThis.WebSocket`, following
the same "spyable constructor, hand-driven event handlers via `act()`" pattern already used for
`MockEventSource` (this pattern is directly portable — jsdom provides a real `WebSocket` global to
override, confirmed in investigation.md's test-infra check). The mock needs `send = vi.fn()` (to
assert the handshake call), `close = vi.fn()`, and settable `onopen`/`onmessage`/`onclose`/
`onerror` handlers, plus a captured constructor `url` argument. Write all 8 tests named in
`test_plan.md`'s "New Tests Required" section (tests 1-8: handshake-first, WS-not-EventSource URL,
initial-full-state-vs-delta, delta-reducer ported assertions, pause/resume exact POST targets,
no-generic-dispatcher guard, reconnect-on-close, reconnect-on-error, plus the `loadInitial` regression
guard). Keep the existing `mockFetch` setup (lines 5-7, 30-44) — `loadInitial()`'s `/map`, `/static`,
`/manifest` fetches and `fallbackPoll`'s `/stats` fetch still go through `globalThis.fetch`,
unchanged by this ticket. Add a `/manifest` and `/static` response to the default `mockFetch` mock
alongside the existing `/map`-shaped one used by the second test, matching what `loadInitial()`'s
`Promise.all` (`useSimulation.ts:90-94`) actually awaits — the current test file's fetch mock only
covers the old two-call shape and will need a third response for `/manifest` to avoid an unhandled
rejection now that `loadInitial()` awaits three fetches, not two.
**Do NOT touch:** the `it('initializes with default values', ...)` test (lines 51-58) — its
assertions (`tick === 0`, `entities === []`, `status === 'CONNECTING'`, `aliveCount === 0`) are
transport-agnostic and remain valid as-is; only its surrounding mock setup (the `beforeEach` fetch
default) may need the `/manifest` addition noted above.
**Verify:** `cd frontend && npx vitest run src/test/useSimulation.test.tsx` — all 8 new/rewritten
tests plus the untouched `initializes with default values` test pass. This is the ticket's sole
required test command (test_plan.md's Scoped Test Commands section); no backend pytest command
applies (this ticket makes zero Python changes).

### Step 7 — Update `docs/engine/contracts/frontend.md`
**Files:** `docs/engine/contracts/frontend.md`
**Change:** §1's "Real-time: EventSource (SSE) for state deltas" bullet and §2B "Delta Sync (SSE)"
section (both currently describe the pre-rewire SSE transport with a disclosure note that the
rewire is tracked separately in this ticket, per investigation.md's Docs Requiring Update section)
must be rewritten to describe the real WebSocket client: `/api/v1/ws`, the
`{"type":"handshake","format":"json"}` handshake sent first (Design Decision 2), the initial
full-state-summary message received before the delta loop begins (Design Decision 3), and the
2000ms `onclose`/`onerror` reconnect behavior (Step 4) — then remove the disclosure note, since the
rewire is now done. §4's "Control Bar" line should gain a note that only `pause`/`resume` map to
real backend routes today (`start`/`step`/`reset` visible in `ControlPanel.tsx` have no backend
route — pre-existing, not introduced by this ticket, but now honestly documented since this ticket
is what defines `sendControl`'s real contract going forward).
**Other writers to this doc:** the two prior tickets in this batch
(`TCK-20260821-WS-ENTITY-DELTA-BROADCAST`, `TCK-20260821-REST-MAP-STATIC-STATS`) already edited
this same file (per their own Files Changed sections) to narrow the backend-capability half of the
known-gap callout — both are already merged/done, so there is no concurrent-edit race; this step
edits the frontend-consumption half of the same callout that those two left for this ticket to
close out.
**Do NOT touch:** `docs/parity_ledger/infrastructure.yaml` — investigation.md confirms no new/
updated parity-ledger entry is required (`INFRA-383`/`384`/`385` already fully document the backend
contracts this ticket only consumes; this ticket makes zero backend-behavior changes). Do not add
an entry here to "be thorough" — it would be an unrequired, unscoped edit.
**Verify:** No automated test covers doc content; verify by re-reading the updated section against
this plan's Design Decisions 2-4 for accuracy before Finalize.

### Step 8 — Required build gate: `npm run build` (architecture-review finding)

**Files:** none (verification only)

**Change:** Run `npm run build` (`tsc -b && vite build`, per `frontend/package.json`'s script) from
`frontend/` and confirm it exits 0 with no TypeScript errors. This is **required**, not optional —
`vitest`'s default transform (esbuild) does not perform full program type-checking, so test_plan.md's
vitest-only command would not catch a `strict: true` compile break on its own (this is exactly how
Step 1's original optional-fields design would have silently shipped a broken build, per
architecture-review). Run this after Steps 1-5 are complete, before Step 6's test rewrite, so any
compile error is caught and fixed while the diff is still small.

**Do NOT touch:** Any `tsconfig*.json` setting (e.g. relaxing `strict`) to make this pass — that
would be gaming the gate, not fixing the underlying issue. If `npm run build` fails, the fix is in
Steps 1/3's actual code (the default-value merge logic), never in loosening the compiler.

**Verify:** `npm run build` exit code 0, recorded in the ticket's Test Summary.

## Scope Guards

- Do not modify `frontend/src/components/GameCanvas.tsx` or `frontend/src/hooks/useCanvas.ts` —
  hard Out of Scope per the ticket. Verify with `git diff --stat` showing zero changes to either
  file (AC 5).
- Do not modify `loadInitial()`'s logic (`useSimulation.ts:86-116`) beyond what Step 6's test setup
  requires mocking for — the `/map`, `/static`, `/manifest` `Promise.all` fetch itself is unchanged
  code, already correct against the real backend, and not in this ticket's Scope.
- Do not modify `fallbackPoll` or its `/stats`/`/state` fetches — real, pre-existing gap
  (query-param-ignoring `/state` polling), explicitly out of this ticket's narrow Scope per both the
  ticket and investigation.md.
- Do not modify `setSpeed` or `clearEvents` — hard Out of Scope (`/speed`, `/clear_events` call
  sites named explicitly in the ticket's Out of Scope section).
- Do not reintroduce a generic `/api/v1/control/${action}`-style dispatcher in any form, including
  as a fallback for `start`/`step`/`reset` — AC 3 is explicit: "no generic dispatcher introduced."
- Do not add API-key/auth wiring anywhere in the frontend to work around the fail-closed-auth
  blocker — that is real scope expansion beyond this ticket's Scope line, flagged as a Known,
  Disclosed Gap above, not something to silently resolve.
- Do not add `ws: true` to `frontend/vite.config.ts`'s dev proxy — same reasoning; a real,
  tightly-coupled fix, but an infra-scope decision beyond this ticket's remit, flagged as a Known,
  Disclosed Gap above.
- Do not add a msgpack encoder/decoder dependency — Design Decision 2 picks `"json"` explicitly to
  avoid this.
- Do not touch `docs/parity_ledger/infrastructure.yaml` — no entry requires a change (see Step 7).
- Do not introduce new `SimStatus` values or any state-machine logic — `SimStatus` stays exactly
  `'CONNECTING' | 'RUNNING' | 'PAUSED' | 'STOPPED'`; that is `TCK-20260821-PHASED-LOADING-STATE-
  MACHINE`'s separate, not-yet-started scope.

## Dependency Map

- Step 1 (EntitySlim type) has no dependency on other steps and can be done first or in any order
  relative to Steps 2-5 — it only affects what compiles, not runtime behavior of the hook itself.
- Steps 2, 3, 4 all touch the same `useEffect` block in `useSimulation.ts` and are naturally
  sequential in the sense that Step 3's `onmessage` and Step 4's `onclose`/`onerror` are assigned
  inside the `connectWS` function Step 2 introduces — implement them together as one coherent edit
  to that effect, in the order presented (connection → message handling → reconnect), rather than
  as three separate isolated diffs.
- Step 5 (`sendControl`) is fully independent of Steps 2-4 — different function in the same file,
  no shared state or control flow.
- Step 6 (tests) depends on Steps 1-5 being complete, since it asserts against their behavior.
- **Step 8 (npm run build) executes between Step 5 and Step 6** — despite its numeric position last
  in this document (added by architecture-review after Steps 1-7 were already drafted) — so a
  compile error is caught and fixed while the diff is still small, before spending effort rewriting
  the test file against code that doesn't compile. Step 8's own step-text already states this; this
  entry makes the actual execution order explicit here too, since the two were previously
  inconsistent (architecture-review finding, second round).
- Step 7 (docs) depends on Steps 2-5 being finalized (documents their actual resulting behavior,
  not a plan of it) and should be done last, after Step 8 confirms the implementation is correct.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| hook opens WebSocket to /api/v1/ws (not EventSource/'/api/v1/stream'), sends handshake as first outgoing message before processing any data | Step 2 (connection + handshake), Step 3 (first-message shape guard ensures no data is "processed" before the handshake-triggered onopen fires) | test_plan.md tests 1, 2 |
| changed/removed/tick/events reducer logic behaviorally unchanged (ported test assertions: entities.length, entities[0].id, aliveCount, tick) | Step 3 | test_plan.md test 4 (and test 3 for the new first-message guard that makes this possible without corruption) |
| pause maps to single POST /api/v1/control/pause, resume to single POST /api/v1/control/resume, no generic dispatcher introduced | Step 5 | test_plan.md tests 5, 6 + grep guard |
| on WS close/error, hook reconnects (mirrors current onerror/setTimeout retry) | Step 4 | test_plan.md test 7 |
| GameCanvas.tsx and useCanvas.ts not modified (diff scope limited to useSimulation.ts + its test file) | N/A — a negative constraint honored by every step's Do NOT touch list, not implemented by any step | Manual diff-scope check (test_plan.md's Anti-Drift Test Guards): `git diff --stat` shows zero changes to either file; Step 8's `npm run build` confirms `useCanvas.ts` still compiles cleanly against the unchanged `EntitySlim` type (the new `WireEntitySlim` type never reaches it) |

## Anti-Drift Notes

- The single biggest real risk in this rewire is silently running the initial post-handshake
  full-state message through the delta reducer (Design Decision 3 / Step 3). Nothing in the old SSE
  code has any precedent for this — it is new logic. If the implementer copies the old `onmessage`
  body verbatim into the new `onmessage` without adding the `isDelta` shape guard first, `data.removed`
  will be `undefined` on the first message and `for (const id of data.removed)` will throw
  `TypeError: data.removed is not iterable`, which the existing `try/catch` will swallow — silently
  breaking the very first render after connect rather than crashing loudly. Watch for this
  specifically during review.
- `useSimulation.ts` is a shared file two other not-yet-started tickets
  (`TCK-20260822-DURABLE-SELECTION-STATE`, `TCK-20260822-ENTITY-LIST-SEARCH-RANK`) will also touch
  later, per investigation.md's Cross-Epic Sequencing Note. This plan does not need to coordinate
  with them (they haven't started), but the implementer should leave the file in a clean, complete
  state — not a half-migrated one — since those tickets will build on this ticket's post-rewire
  shape, not the pre-rewire one.
- `snapshot_as_of_tick` and `region_id` are real fields on every delta message
  (`src/api/ws/stream.py:72-74`) that this ticket's Scope does not ask the hook to consume. Do not
  add drift-detection or region-filtering logic using them — that would be scope expansion. The
  reducer must merely tolerate their presence without erroring (satisfied by construction in Step
  3's implementation, since it destructures only `tick`/`changed`/`removed`/`events`).
  `region_id` is always `null` today per `src/api/ws/stream.py:74` (`TCK-20260821-DELTA-ENVELOPE-
  SPATIAL-FIELD`'s addition) — not a live filtering capability yet regardless.
- Test 5's assertion style requires the *literal* URL string `/api/v1/control/pause` (not a
  substring or template match) — do not write `fetch(`${API_BASE}/control/${'pause'}`, ...)` as a
  "clever" way to reuse a string template; that still reads as a generic dispatcher pattern and
  defeats the intent of the no-generic-dispatcher AC and the grep guard.
- Two real blockers (fail-closed API-key auth, Vite proxy missing `ws: true`) will prevent this
  change from working against a real running dev server even once merged. This is expected and
  disclosed — do not attempt to "fix" either one inside this ticket's diff, and do not let a failed
  manual live-server smoke test block Finalize; the ticket's own AC and test_plan.md's Regression
  Surface do not require live verification, only the mocked-WebSocket vitest suite.
- Do not add a `"test"` script to `frontend/package.json` as part of this ticket unless it's
  trivial and uncontroversial — not requested by Scope, and `npx vitest run
  src/test/useSimulation.test.tsx` works fine without one (confirmed in test_plan.md's Scoped Test
  Commands section).

## Deviations

Implementation followed this plan exactly for all 8 steps, in the Dependency Map's stated execution
order (Step 1 -> Steps 2/3/4 as one coherent edit -> Step 5 -> Step 8 -> Step 6 -> Step 7). One
implementation-detail deviation, not a design/architecture deviation:

- **Test 7's fake-timer setup ordering**: the plan does not specify exactly when
  `vi.useFakeTimers()` should be called relative to the rest of the test's setup. A first attempt
  called it before awaiting the shared `renderConnectedHook()` helper (which internally uses
  `@testing-library/react`'s `waitFor` to confirm the mock `WebSocket` was constructed) — this hung
  both reconnect tests for the full 5000ms `testTimeout`, since `waitFor` polls via real timers and
  fake timers being active blocks that polling from ever resolving. Fix: `vi.useFakeTimers()` is
  called only after `renderConnectedHook()` has resolved, immediately before triggering
  `onclose`/`onerror` and calling `vi.advanceTimersByTime(2000)`. This does not change what is
  being verified (the same `scheduleReconnect`/2000ms `setTimeout` code path from Step 4), only the
  test harness's timer-mode sequencing.
- `npm install` was required before `npm run build`/`npx vitest` could run at all — this worktree
  had no `node_modules` present. Not a deviation from the plan's steps, just a prerequisite the
  plan did not need to call out since it assumes a normal dev environment.
