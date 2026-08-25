---
status: historical
layer: frontend
authority: P2
audience: agent
ticket_id: TCK-20260821-PHASED-LOADING-STATE-MACHINE
artifact_type: investigation
tags: [websocket]
---

# Investigation — TCK-20260821-PHASED-LOADING-STATE-MACHINE

## Ticket Staleness (read this first)

This ticket's own text was written **before** `TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET` (ticket
6 of 8 in this epic, already DONE — `tickets/done/TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET.md`)
landed. Ticket 6 completely rewired `frontend/src/hooks/useSimulation.ts` off
`EventSource('/api/v1/stream')` (SSE) onto a real `WebSocket` connection to `/api/v1/ws`. As a
result:

- This ticket's Scope line "existing SSE-stream/entity-processing behavior in
  `useSimulation.test.tsx` continues to pass unmodified" is stale — there is no SSE/EventSource
  anywhere in the current codebase. `useSimulation.test.tsx` was fully rewritten by ticket 6 against
  a mocked `WebSocket` (10/10 passing, confirmed by re-reading the file in full below).
- This ticket's Out of Scope / Assumptions line asking whether "the second, separate
  EventSource-reconnect infinite-retry loop" gets bounded-retry treatment is stale in its noun: the
  EventSource-reconnect loop no longer exists. The mechanism that question actually refers to today
  is `scheduleReconnect()` (`frontend/src/hooks/useSimulation.ts:132-138`), the WS
  `onclose`/`onerror` reconnect path ticket 6 built to explicitly mirror the old
  EventSource-era retry behavior (per ticket 6's own Scope: "On WS close/error, reconnect (mirroring
  the current onerror/setTimeout retry behavior)" — i.e. ticket 6 *intentionally* carried the
  unbounded-retry shape forward unchanged, it did not introduce a new mechanism).
- All four ACs and the one open Assumptions question are re-mapped below to the current
  WebSocket-based implementation. Plan should work from this section and the "Current Behavior"
  section, not from the ticket body's literal SSE wording.

None of this changes the ticket's underlying *intent* (replace the opaque single `CONNECTING` status
with a real phased state machine, bound `loadInitial`'s retry, add visible error UI, wrap
`GameCanvas` with a phase-aware loading component) — only the transport-specific details of how that
intent cashes out against the current code.

## Current Behavior

### `SimStatus` type — `frontend/src/hooks/useSimulation.ts:17`
```ts
export type SimStatus = 'CONNECTING' | 'RUNNING' | 'PAUSED' | 'STOPPED';
```
Four literals only. Initial hook state is set to `'CONNECTING'` at
`frontend/src/hooks/useSimulation.ts:78` (`useState<SimStatus>('CONNECTING')`). `CONNECTING` today
covers the *entire* pre-live sequence: the three parallel REST fetches in `loadInitial()`, the WS
handshake, and the wait for the first delta message — exactly the "one opaque bucket" problem the
epic plan doc's item 8 and this ticket's Request Summary describe.

`SimStatus` is also consumed at `frontend/src/components/Header.tsx:16-21`:
```ts
const STATUS_COLORS: Record<SimStatus, string> = {
  CONNECTING: 'text-accent-yellow',
  RUNNING: 'text-accent-green',
  PAUSED: 'text-accent-yellow',
  STOPPED: 'text-accent-red',
};
```
This is an **exhaustive `Record<SimStatus, string>`**. Extending the `SimStatus` union without also
adding entries here will fail `tsc` (TypeScript requires every key of the union to be present in an
exhaustive `Record`). `Header.tsx` is **not** listed in this ticket's Related Code Areas — see Risks
below.

### `loadInitial()`'s fetch-retry behavior — `frontend/src/hooks/useSimulation.ts:93-121`
```ts
const loadInitial = async () => {
  try {
    const [rawMap, staticData, manifestData] = await Promise.all([
      fetchJSON<MapData>('/map'),
      fetchJSON<StaticData>('/static'),
      fetchJSON<Manifest>('/manifest'),
    ]);
    if (!cancelled) { /* ...sets mapData/buildings/resourceNodes/treasureChests/regions/manifest... */ }
  } catch {
    if (!cancelled) setTimeout(loadInitial, 1000);
  }
};
```
Exact lines: the `catch` block is `useSimulation.ts:115-117`. There is **no retry counter anywhere**
— on any fetch failure (any of `/map`, `/static`, `/manifest` rejecting or `fetchJSON` throwing on a
non-`ok` response, see `fetchJSON` at lines 11-15), it unconditionally re-invokes `loadInitial` after
a fixed 1000ms, forever, with zero user-visible signal. This confirms the ticket's Request
Summary/AC2 claim: retries silently forever, no bound, no error status.

### WS connection status-transition behavior — `frontend/src/hooks/useSimulation.ts:124-309`
The WS `useEffect` (dependency `[mapData]`, so it only starts once `loadInitial` has succeeded and
`mapData` is set — line 125's guard `if (!mapLoadedRef.current && !mapData) return;`) defines
`connectWS()` (lines 140-215) and a `scheduleReconnect()` helper (lines 132-138).

**Critical finding: nowhere in `connectWS()`'s `onopen`/`onmessage`/`onclose`/`onerror` handlers is
`setStatus` ever called.** Grep confirms no `setStatus(` call exists in the entire WS lifecycle
block (lines 140-215). The *only* place `status` is set today is inside the separate `fallbackPoll`
function (the secondary 500ms `/stats` poll, lines 221-300), specifically:
```ts
if (!stats.running) {
  setStatus('STOPPED');
} else if (stats.paused) {
  setStatus('PAUSED');
} else {
  setStatus('RUNNING');
}
```
(`useSimulation.ts:231-237`). So today, `status` transitions from its initial `'CONNECTING'` to
`RUNNING`/`PAUSED`/`STOPPED` only once the *first* `/stats` REST poll succeeds — entirely decoupled
from the WS lifecycle (`onopen`, handshake sent, first delta received) and decoupled from whether
`loadInitial` has even finished (though in practice the WS effect can't start until it has, per the
`[mapData]` dependency).

This is the concrete gap AC1 targets: today there is no status transition tied to WS `onopen`,
handshake completion, or first-delta receipt at all — `SYNCING`/`CONNECTING_LIVE`/`READY` (as
distinct, WS-lifecycle-driven states) do not exist in any form; the closest analog, `RUNNING`, is
driven by an unrelated polling loop.

### `scheduleReconnect()` — `frontend/src/hooks/useSimulation.ts:132-138`
```ts
const scheduleReconnect = () => {
  if (reconnectTimeout) return;
  reconnectTimeout = setTimeout(() => {
    reconnectTimeout = null;
    connectWS();
  }, 2000);
};
```
Called unconditionally from both `ws.onclose` (line 207-209) and `ws.onerror` (line 211-214, which
also force-closes the socket first). **No retry counter, no bound, no distinct terminal/error
state** — this is a fixed-2000ms, infinite-retry loop, structurally identical in shape to
`loadInitial`'s unbounded retry, just on the WS side instead of the REST side.

**Resolving the ticket's open Assumptions question**: "whether the second, separate
EventSource-reconnect infinite-retry loop also gets bounded-retry treatment" — the EventSource
loop it refers to literally no longer exists; the mechanism occupying that role today is
`scheduleReconnect()` above. Ticket 6's own Scope explicitly chose to carry the *old* SSE-era
unbounded-retry behavior forward unchanged ("mirroring the current onerror/setTimeout retry
behavior") rather than bound it — ticket 6's AC4 confirms this shipped as designed
(`tickets/done/TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET.md` AC: "on WS close/error, hook
reconnects (mirrors current onerror/setTimeout retry)"). This ticket (8) is therefore the first
place any bound is considered for *either* retry loop. The ticket's own Scope line only commits to
bounding `loadInitial()`'s retry ("Bound `loadInitial()`'s fetch-retry loop with a retry counter");
it does **not** commit to bounding `scheduleReconnect()`. This is a real, unresolved open decision —
see Risks and Open Questions below; it should not be silently assumed either way by Plan.

### GameCanvas.tsx loading text — `frontend/src/components/GameCanvas.tsx:421-424`
```tsx
{!mapData ? (
  <div className="flex items-center justify-center h-full text-text-secondary text-sm animate-pulse">
    Loading map...
  </div>
) : (
  ...
)}
```
This branches on `!mapData` (a prop passed down from `useSimulation()`), **not** on `status` —
`GameCanvas.tsx` does not import or reference `SimStatus`/`status` anywhere (confirmed via grep:
zero matches for "status" in the whole file). This is the "one generic 'Loading map...' string with
no phase information" the Request Summary describes.

Consequence for AC3's "new wrapper component... rendering phase-specific loading text/UI per
non-READY status": if the new wrapper only mounts `<GameCanvas>` once `status === 'READY'`, then by
construction `mapData` will already be non-null by that point (map data loads well before any
WS/delta activity, since the WS effect itself depends on `mapData` being set — line 125). This means
`GameCanvas.tsx`'s own `!mapData` branch (lines 421-424) becomes dead code post-implementation — it
will never render. This is an accepted, known side effect, **not** a defect to "fix": the ticket's
Out of Scope explicitly requires `GameCanvas.tsx` to remain byte-for-byte unmodified, so this dead
branch must be left in place, not removed.

### App.tsx — `frontend/src/App.tsx`
Exists (85 lines). Renders `<Header>` (passing `sim.status` among other props, line 42), then
branches on `currentPage`: if `'simulation'`, renders a flex row containing `<GameCanvas>` and
`<Sidebar>` (lines 47-76); otherwise renders `<ApiDocsPage>`. `useSimulation()` is called once at the
top (line 10) and its full return value (`sim`) is threaded down as props. There is currently no
loading/error wrapper of any kind around `<GameCanvas>` — it is mounted unconditionally whenever
`currentPage === 'simulation'`, regardless of `sim.status`.

## Mechanics / Engine Constraints

This ticket touches no `docs/mechanics/` or `docs/engine/` simulation-law content — it is a
client-side (frontend-only) UI/state-machine change with zero backend/`AuthoritativeState` mutation.
The one relevant contract is `docs/engine/contracts/frontend.md` (not a Mechanics Bible chapter but
the authoritative description of this hook's external behavior — see Docs Requiring Update below),
specifically:
- §2.A (Initial Load) — describes `loadInitial()`'s three-fetch `Promise.all`; does not currently
  describe any retry/failure behavior at all, so it is silently inaccurate on the exact gap this
  ticket fixes.
- §2.B (Delta Sync (WebSocket)) — describes the handshake, initial-message shape guard, and
  `scheduleReconnect`'s 2000ms reconnect; does not mention `status`/`SimStatus` anywhere. This
  section will need updating once `SimStatus` transitions are wired into the WS lifecycle (AC1).

No `docs/parity_ledger/` entry constrains this work (see Parity Ledger Overlap below) — it is a
frontend UI-state concern, not a simulation-behavior parity item.

## Docs Requiring Update

- `docs/engine/contracts/frontend.md`: §2.A needs to document `loadInitial()`'s new bounded-retry
  behavior and the new ERROR-class status; §2.B needs to document the new WS-lifecycle-driven
  `SimStatus` transitions (`CONNECTING_LIVE` on `connectWS()` start / `onopen`, `SYNCING` once the
  handshake completes and the hook is waiting for the first delta, `READY` once the first
  `isDelta`-shaped message is processed) and needs a decision recorded on whether
  `scheduleReconnect()` also gets bounded-retry treatment (currently undocumented as unbounded — see
  Risks below).

The `docs/parity_ledger/*.yaml` files (`substrate.yaml`, `combat_movement.yaml`,
`strategic_cognition.yaml`, `town_resource.yaml`, `progression.yaml`, `social_narrative.yaml`,
`world_dynamics.yaml`, `infrastructure.yaml`) were checked (grepped for `CONNECTING`, `SimStatus`,
"loading state", "reconnect") and none contain an entry describing this frontend loading
state-machine behavior — `infrastructure.yaml`'s only "reconnect" hits are an unrelated observability
stream-consumer backoff test (`test_stream_consumer_resilience.py`) and an unrelated cache-migration
note, neither about `useSimulation.ts`. No parity ledger entry needs to change for this ticket; none
is required to be added either, since this is UI/state-machine polish over an already-parity-tracked
transport (the WS delta contract itself was already covered by ticket
`TCK-20260821-WS-ENTITY-DELTA-BROADCAST`'s own parity work, which this ticket does not alter).

No other `docs/` path (Mechanics Bible chapters, `docs/architecture/`, `docs/guidelines/`) needs to
change for this ticket: none of them describe frontend hook-level loading/retry/status behavior at
this granularity, and this ticket makes no simulation-law or backend-contract change.

## Parity Ledger Overlap

None. This ticket is a purely client-side UI/state-machine change (new `SimStatus` values, bounded
retry counter, a new wrapper component) with zero backend/`AuthoritativeState` behavior change.
Checked all 8 `docs/parity_ledger/*.yaml` files for `CONNECTING`/`SimStatus`/"loading state"/
"reconnect" — the only hits are unrelated (observability stream-consumer backoff, an unrelated cache
note); no entry needs a status/evidence update, and no P0 entry is implicated.

## Prior Work

- `tickets/done/TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET.md` +
  `stored_artifacts/TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET/` (`investigation.md`, `plan.md`) —
  the ticket that rewired `useSimulation.ts` off SSE onto WebSocket. Its Implementation Notes are the
  ground truth for exactly what `connectWS()`/`scheduleReconnect()`/the `onmessage` shape-guard do
  today (matches what was independently re-verified by reading the live file above). Its own Out of
  Scope explicitly deferred "Building the state-machine loading UI" to this ticket
  (`TCK-20260821-PHASED-LOADING-STATE-MACHINE`), confirming this ticket's scope boundary is
  intentional, not an oversight.
- `tickets/done/TCK-20260821-WS-ENTITY-DELTA-BROADCAST.md` +
  `stored_artifacts/TCK-20260821-WS-ENTITY-DELTA-BROADCAST/` — the ticket that added
  `changed`/`removed`/`tick`/`snapshot_as_of_tick` to the WS delta payload and fixed the connect-time
  listener-registration race (register tick-listener callback before taking the map/static
  snapshot). This is the "entity-delta broadcast ticket's connect-time atomic-handoff window" this
  ticket's AC1 refers to — concretely, the window between the WS handshake completing and the first
  `isDelta`-shaped message (`Array.isArray(data.changed) && Array.isArray(data.removed)`,
  `useSimulation.ts:156`) being processed in `onmessage`.
- `docs/plans/live_map_reconnection_epic.md` (item 8, lines ~221-231) — the epic-level source of this
  ticket's intent; already reflects the current WebSocket-based implementation (unlike this ticket's
  own body text), confirming the epic plan doc is the accurate reference to cross-check ACs against,
  not this ticket's literal wording.
- `frontend/src/test/useSimulation.test.tsx` (as ticket 6 left it) — 10/10 passing tests against a
  mocked `WebSocket`, including two reconnect tests (`'reconnects after WebSocket close'`,
  `'reconnects after WebSocket error'`, lines 232-264) that assert `scheduleReconnect()`'s current
  2000ms/unbounded behavior. These will need updating if `scheduleReconnect()` is bounded; will stay
  correct as-is if it is deliberately left unbounded (see Risks below).

## Risks and Open Questions

1. **Open decision (ticket's own Assumptions section, re-mapped, not resolved by this investigation
   — Plan must decide and record it, not silently pick one):** does `scheduleReconnect()`
   (`useSimulation.ts:132-138`) also get bounded-retry + visible-error treatment, or is it
   deliberately left as unbounded reconnect (arguably correct for a long-lived live-view app — you
   generally do want an infinite background-reconnect attempt for a dashboard-style client, unlike a
   one-shot initial data load)? This ticket's own Scope text only explicitly commits to bounding
   `loadInitial()`. If left unbounded, the ticket needs an explicit stated rationale (not silence) per
   its own Out of Scope wording ("must state, not silently resolve").
2. **`Header.tsx`'s `STATUS_COLORS: Record<SimStatus, string>` (line 16-21) is not in this ticket's
   Related Code Areas but will hard-fail `tsc` (`npm run build`) if `SimStatus` gains new members
   without a corresponding entry added here.** This is a real gap in the ticket's stated scope, not a
   hypothetical — TypeScript's structural typing makes this a compile error, not a runtime surprise
   discovered later. Plan must add `frontend/src/components/Header.tsx` to scope (at minimum, extend
   `STATUS_COLORS` with entries for every new status) or the build gate will fail.
3. **`GameCanvas.tsx`'s own `!mapData` loading branch (lines 421-424) becomes unreachable dead code**
   once the new wrapper gates `GameCanvas` on `status === 'READY'` (since `mapData` is always set by
   then). This is expected and must **not** be "cleaned up" — doing so would violate the explicit
   byte-for-byte-unmodified constraint on `GameCanvas.tsx`.
4. **Where exactly does `CONNECTING_LIVE` begin vs. `SYNCING`?** Two defensible boundaries: (a)
   `CONNECTING_LIVE` = from `connectWS()` invocation until `ws.onopen` fires; `SYNCING` = from
   `onopen` (handshake sent) until the first `isDelta` message; or (b) `CONNECTING_LIVE` covers the
   whole handshake round-trip (open + handshake ack implied by receiving the non-delta initial
   summary message) and `SYNCING` is strictly the wait for the *first delta after* that summary. The
   epic plan doc's item 8 phrasing ("tick listener registered, waiting for/applying the first
   snapshot") reads as closer to (a)/(b) blended — SYNCING starts once the connection is live and
   ends when the first delta lands, regardless of the one-time non-delta summary message in between.
   Plan should pick one explicitly and state the exact `onopen`/`onmessage` line each transition
   fires from, since the current code has no `status`-setting hooks in this path at all to anchor to.
5. **`fallbackPoll`'s existing `RUNNING`/`PAUSED`/`STOPPED` transitions (lines 231-237) run on every
   500ms poll tick, unconditionally overwriting `status`.** Once `READY` is reached, the next
   `fallbackPoll` tick (which starts immediately via `setInterval(fallbackPoll, 500)` at line 302,
   independent of WS state) will overwrite `READY` with `RUNNING`/`PAUSED`/`STOPPED` within 500ms.
   This is very likely the *intended* final steady state (READY is a transient handoff marker, not a
   permanent one — RUNNING/PAUSED/STOPPED remain the steady-state statuses, exactly as the ticket's
   own Scope says: "plus existing RUNNING/PAUSED/STOPPED"), but Plan should state this explicitly
   since it's easy to misread AC1's "transitions to READY only once... has landed" as meaning READY
   is sticky.

## Anti-Drift Hazards

- Do not touch `GameCanvas.tsx` or `useCanvas.ts` in any way, including to remove the now-dead
  `!mapData` branch — this is an explicit, repeatedly-stated Out of Scope boundary shared with
  ticket 6.
- Do not silently bound `scheduleReconnect()` as a "natural" extension of bounding `loadInitial()` —
  it is a separate, only-partially-scoped decision (see Risk 1) that must be stated, not assumed.
- Do not forget `Header.tsx`'s `STATUS_COLORS` Record — it is the single most likely place a build
  break happens if missed, since it is not in the ticket's own Related Code Areas list.
- Do not let the new wrapper component duplicate or replace `GameCanvas.tsx`'s existing
  `!mapData` "Loading map..." text — the ticket wants the new phase-aware text to *precede*
  `GameCanvas` mounting, not to coexist with or patch its internal branch.
- Do not conflate this ticket's `SYNCING`/first-delta-received concept with `fallbackPoll`'s separate
  `/stats`-driven RUNNING/PAUSED/STOPPED transitions — they are two independent mechanisms (WS delta
  stream vs. REST poll) that happen to both write to the same `status` state variable; sequencing
  between them (does READY get overwritten by the next fallbackPoll tick, and is that fine) should be
  reasoned about explicitly, not left as an accident of `setState` ordering.
- Do not invent a new `SYNCING` detection mechanism (e.g. a new WS message type) — the ticket
  explicitly requires reusing the existing `isDelta` shape-guard
  (`Array.isArray(data.changed) && Array.isArray(data.removed)`, already at
  `useSimulation.ts:156`) as the SYNCING→READY trigger, not a newly invented one.
