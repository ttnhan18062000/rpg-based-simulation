---
status: historical
layer: frontend
authority: P2
audience: agent
ticket_id: TCK-20260821-PHASED-LOADING-STATE-MACHINE
artifact_type: test_plan
tags: [websocket]
---

# Test Plan — TCK-20260821-PHASED-LOADING-STATE-MACHINE

## Regression Surface

All existing coverage is in one file, already rewritten against a mocked `WebSocket` by ticket 6
(`TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET`) — there is no separate SSE-era test file to worry
about; it no longer exists.

**Unit / hook-integration** (`cd frontend && npx vitest run src/test/useSimulation.test.tsx`) — 10
tests, currently all passing:
- `initializes with default values` — **will need updating**: currently asserts
  `result.current.status` toBe `'CONNECTING'` (`useSimulation.test.tsx:110`); this is exactly the
  ticket's own AC4 target ("Update ... initial-status assertion (`status==='CONNECTING'`)"). Per
  AC1 ("starts at INITIALIZING not bare CONNECTING"), this must become
  `expect(result.current.status).toBe('INITIALIZING')`.
- `sends handshake as the first outgoing message before processing any data` — must keep passing
  unmodified; asserts `mockWS.send` call shape, unrelated to `status`.
- `opens WebSocket to /api/v1/ws, not EventSource` — must keep passing unmodified.
- `ignores/threads the initial full-state message distinctly from delta messages` — must keep
  passing unmodified; this is the exact `isDelta` shape-guard boundary the new SYNCING→READY
  transition hooks into, so it is the highest-risk existing test for accidental breakage if the
  `onmessage` handler is touched carelessly.
- `reduces a real {tick,changed,removed,events,snapshot_as_of_tick,region_id} delta correctly` —
  must keep passing unmodified.
- `sendControl(pause) POSTs exactly to /api/v1/control/pause, sendControl(resume) POSTs exactly to
  /api/v1/control/resume` — must keep passing unmodified; unrelated subsystem.
- `sendControl with an unrecognized action does not construct a generic /api/v1/control/{action}
  URL` — must keep passing unmodified.
- `reconnects after WebSocket close` / `reconnects after WebSocket error` (lines 232-264) — must
  keep passing **only if Plan decides to leave `scheduleReconnect()` unbounded** (see
  investigation.md Risk 1). If Plan bounds it, these two tests need updating to reflect the new
  bounded behavior (e.g. asserting no further reconnect attempt after N consecutive failures, and/or
  an ERROR-class status transition) — this is a real design decision to make in Plan, not something
  this test plan can pre-resolve.
- `loadInitial still fetches /map, /static, /manifest via one Promise.all` — must keep passing
  unmodified.

**Build gate** (regression, not new): `cd frontend && npm run build` (`tsc -b && vite build`) must
still exit 0. This is the test most likely to silently catch a missed spot — in particular
`frontend/src/components/Header.tsx`'s `STATUS_COLORS: Record<SimStatus, string>`
(`Header.tsx:16-21`), which is exhaustive over `SimStatus` and will fail `tsc` if new `SimStatus`
members are added without a corresponding entry. See investigation.md Risk 2 — `Header.tsx` is not
in the ticket's stated Related Code Areas, so this needs to be added to scope, not just relied on
"the build will catch it."

**No backend/Python regression surface applies** — this ticket makes zero `src/` changes (pure
`frontend/` TypeScript/React), matching ticket 6's precedent (no backend pytest command needed).

## New Tests Required

All new tests live in `frontend/src/test/useSimulation.test.tsx` unless noted, using the same
`MockWebSocket`/`mockFetch`/`renderConnectedHook()` harness already established there.

1. **`starts at INITIALIZING, not CONNECTING`**
   - Category: unit
   - Verifies: `renderHook(() => useSimulation())`'s immediate (pre-fetch-resolution)
     `result.current.status` is `'INITIALIZING'`. Supersedes/replaces the existing
     `'initializes with default values'` assertion (AC1, AC4).
   - Location: `frontend/src/test/useSimulation.test.tsx`

2. **`transitions through FETCHING_WORLD_DATA while loadInitial's fetches are in flight`**
   - Category: unit
   - Verifies: status is `'FETCHING_WORLD_DATA'` (or equivalent, per whatever exact transition point
     Plan defines) after `loadInitial()` starts and before the `Promise.all` resolves — needs a
     controllable/delayed mock fetch (e.g. an unresolved promise held open until the assertion
     fires) to observe the intermediate state before advancing.
   - Location: `frontend/src/test/useSimulation.test.tsx`

3. **`transitions to CONNECTING_LIVE once map/static/manifest load and the WS connection attempt begins`**
   - Category: unit
   - Verifies: after `loadInitial()` resolves (mapData set) and the WS `useEffect` fires
     `connectWS()`, status becomes `'CONNECTING_LIVE'` — before `mockWS.onopen?.()` is invoked.
   - Location: `frontend/src/test/useSimulation.test.tsx`

4. **`transitions to SYNCING on WS open (handshake sent), stays SYNCING through the non-delta initial summary message`**
   - Category: unit
   - Verifies: after `act(() => mockWS.onopen?.())`, status becomes `'SYNCING'`; then feeding the
     non-delta initial summary message (`{tick, world_time, entities_count, maturity, seed}`, same
     shape as the existing `'ignores/threads the initial full-state message...'` test) through
     `mockWS.onmessage` does **not** advance status past `SYNCING` — this pins down exactly which
     message the SYNCING→READY transition is keyed on (the first `isDelta`-shaped message, per
     `useSimulation.ts:156`'s existing shape-guard), not the non-delta summary. This is the direct
     regression guard for AC1's "SYNCING corresponds exactly to the connect-time atomic-handoff
     window."
   - Location: `frontend/src/test/useSimulation.test.tsx`

5. **`transitions to READY exactly on the first isDelta-shaped message, not before`**
   - Category: unit
   - Verifies: feeding a real delta payload (`{tick, changed, removed, events, snapshot_as_of_tick,
     region_id}`, same shape as the existing `'reduces a real {...} delta correctly'` test) through
     `mockWS.onmessage` transitions status to `'READY'`. Combine with test 4 in the same test body
     (summary message first → still SYNCING, then delta → now READY) for a single ordered assertion
     that pins the exact boundary, rather than two independently-passable tests that could each pass
     for the wrong reason.
   - Location: `frontend/src/test/useSimulation.test.tsx`

6. **`loadInitial's fetch-retry loop is bounded and transitions to an ERROR-class status after N failures`**
   - Category: unit
   - Verifies: with `mockFetch` rejecting/erroring on every call (using `vi.useFakeTimers()` and
     `vi.advanceTimersByTime` to fast-forward the existing 1000ms retry delay), after the chosen N
     retry attempts, status transitions to the new ERROR-class status (exact name TBD by Plan, e.g.
     `LOAD_ERROR`) and `loadInitial` stops being invoked again (assert `mockFetch` call count does
     not keep growing past the Nth attempt's expected count). Directly verifies AC2.
   - Location: `frontend/src/test/useSimulation.test.tsx`

7. **`a later successful fetch after ERROR does not silently resurrect without explicit retry` (or documents the opposite, if Plan chooses auto-recovery)**
   - Category: unit
   - Verifies: whatever Plan decides the ERROR state's terminal/recoverable semantics are (does the
     hook offer/attempt any recovery once ERROR is reached, or is it a dead end requiring a page
     reload) — write the test to pin whichever behavior Plan actually specifies. Flagged here as
     required precisely because the ticket's AC2 does not say what happens *after* the ERROR
     transition, only that it happens.
   - Location: `frontend/src/test/useSimulation.test.tsx`

8. **`new wrapper component renders phase-specific text for each non-READY status`**
   - Category: unit (component test, likely a new file)
   - Verifies: for each of `INITIALIZING`/`FETCHING_WORLD_DATA`/`CONNECTING_LIVE`/`SYNCING`/the new
     ERROR status, the wrapper renders distinguishable phase-specific text/UI (not one generic
     string) and does **not** render `<GameCanvas>`'s children/canvas elements. For `READY`, verifies
     the wrapper renders `<GameCanvas>` (or passes through to it).
   - Location: a new test file colocated with the new wrapper component (e.g.
     `frontend/src/test/<WrapperComponentName>.test.tsx`), mirroring the project's existing
     component-test conventions (check `frontend/src/test/` for an existing component-test example
     to match style/harness before creating this file).

9. **`distinct error UI is rendered when status is the new ERROR-class status`**
   - Category: unit (component test, same file as test 8)
   - Verifies: the ERROR-class status renders UI visibly distinct from the ordinary loading-phase
     text (per AC3's "and a distinct error UI" — not just another phase label reusing the same
     loading-spinner treatment).
   - Location: same new test file as test 8.

10. **Architecture guard — `GameCanvas.tsx`/`useCanvas.ts` remain byte-for-byte unmodified**
    - Category: architecture guard (script/CI-level, not a vitest unit test)
    - Verifies: `git diff --stat -- frontend/src/components/GameCanvas.tsx
      frontend/src/hooks/useCanvas.ts` is empty after implementation — mirrors exactly how ticket 6
      verified the same constraint (see `tickets/done/TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET.md`
      Test Summary's last bullet). Run this as a literal `git diff --stat` check during Verify, not
      as a vitest test.
    - Location: run as a Bash check during the ticket's Test/Verify phase; not a file to write.

## Scoped Pytest Commands

This ticket makes zero Python/backend changes — there is no scoped `pytest` command. Verification is
entirely `npm`/`vitest`-based, matching ticket 6's precedent exactly:

```
cd frontend && npx vitest run src/test/useSimulation.test.tsx
cd frontend && npx vitest run src/test/<WrapperComponentName>.test.tsx   # once the new wrapper's test file is named
cd frontend && npm run build   # tsc -b && vite build — the gate that catches Header.tsx's exhaustive Record
```

Never `pytest tests/` for this ticket — there is nothing for it to scope to.

## Anti-Drift Test Guards

- **`Header.tsx`'s `STATUS_COLORS` exhaustiveness**: the `npm run build` gate above is the guard —
  if `Header.tsx` is not updated alongside the `SimStatus` extension, this fails loudly at compile
  time rather than silently at runtime. Treat a build failure here as confirmation the ticket's scope
  needs `Header.tsx` added, not as a bug to route around.
- **`GameCanvas.tsx`/`useCanvas.ts` untouched** (test 10 above): guards against the specific,
  plausible scope-creep of "fixing" the now-dead `!mapData` branch in `GameCanvas.tsx` once it
  becomes unreachable (see investigation.md Risk 3) — that dead branch must be left alone.
- **`fallbackPoll`'s RUNNING/PAUSED/STOPPED transitions stay reachable and correct** (existing
  behavior, no new test needed beyond confirming no regression): after adding the new pre-READY
  states, `fallbackPoll`'s own `setStatus('STOPPED'|'PAUSED'|'RUNNING')` logic
  (`useSimulation.ts:231-237`) must remain intact and untouched in its own conditional logic — only
  the type it writes into (`SimStatus`) grows. A quick regression check: after READY is reached and
  a `fallbackPoll` tick runs with `stats.running === true, stats.paused === false`, status should
  read `RUNNING` (not stay pinned at `READY`) — confirms READY is correctly transient, not sticky
  (see investigation.md Risk 5). Add this as an explicit assertion in whichever new test exercises
  the full INITIALIZING→READY sequence, rather than leaving it implicit.
- **The `isDelta` shape-guard (`useSimulation.ts:156`) stays the single source of truth for the
  SYNCING→READY boundary** — tests 4/5 above exist specifically so that a future change to the
  delta-detection logic can't silently decouple the loading-state machine's READY transition from
  the actual entity-delta reducer's own notion of "a real delta arrived," which is what AC1's "not a
  newly invented mechanism" requirement is guarding against.
- **No SSE/EventSource resurrection**: if any new code or test references `EventSource` anywhere,
  that is itself a regression signal — ticket 6 removed it entirely and this ticket must not
  reintroduce it (mirrors the existing `'opens WebSocket to /api/v1/ws, not EventSource'` test's own
  `expect((globalThis as any).EventSource).toBeUndefined()` assertion at
  `useSimulation.test.tsx:125`).
