---
status: historical
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260821-PHASED-LOADING-STATE-MACHINE
phase: done
date: 2026-08-21
tags: [websocket]
---

# TCK-20260821-PHASED-LOADING-STATE-MACHINE

## Title
Replace opaque CONNECTING status with a phased loading state machine

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Today the frontend's SimStatus type has only a single CONNECTING state covering the entire pre-live sequence, its fetch-failure path retries silently forever with no visible error, and GameCanvas shows one generic "Loading map..." string with no phase information. The author wants a real state machine (INITIALIZING -> FETCHING_WORLD_DATA -> CONNECTING_LIVE -> SYNCING -> READY) plus a visible error state after repeated failures, without touching GameCanvas.tsx/useCanvas.ts themselves.

## Scope
- Extend SimStatus to a superset covering INITIALIZING -> FETCHING_WORLD_DATA -> CONNECTING_LIVE -> SYNCING -> READY (plus existing RUNNING/PAUSED/STOPPED), starting at INITIALIZING not bare CONNECTING
- Make SYNCING correspond exactly to the entity-delta broadcast ticket's connect-time atomic-handoff window (first live snapshot received), not a newly invented mechanism
- Bound loadInitial()'s fetch-retry loop with a retry counter; after N failures, transition to a new visible ERROR-class status instead of retrying silently forever
- Add a new wrapper component (mounted in App.tsx around GameCanvas) rendering phase-specific loading text/UI per non-READY status and a distinct error UI
- Update frontend/src/test/useSimulation.test.tsx's initial-status assertion (status==='CONNECTING') and other affected assertions for the new enum

## Out of Scope
- GameCanvas.tsx and useCanvas.ts -- remain byte-for-byte unmodified (verifiable via git diff)
- Building the underlying WS connect sequence -- this ticket only wires status transitions to it
- Whether the EventSource-style reconnect loop (separate from loadInitial's fetch retry) also gets bounded-retry treatment is an explicit open decision this ticket must state, not silently resolve

## Acceptance Criteria
- [x] SimStatus extended to superset covering INITIALIZING/FETCHING_WORLD_DATA/CONNECTING_LIVE/SYNCING/READY (plus existing RUNNING/PAUSED/STOPPED), starts at INITIALIZING not bare CONNECTING, transitions to READY only once first live snapshot (SYNCING handoff) has landed
- [x] loadInitial()'s catch tracks a bounded retry counter (not unconditional setTimeout forever); after N failures, status transitions to new visible ERROR-class status
- [x] new wrapper component (mounted in App.tsx around GameCanvas) renders phase-specific loading text/UI per non-READY status and distinct error UI, GameCanvas.tsx/useCanvas.ts remain byte-for-byte unmodified
- [x] existing SSE-stream/entity-processing behavior in useSimulation.test.tsx continues to pass unmodified aside from initial-status assertion (re-mapped per investigation.md: no SSE exists anymore — all pre-existing WS-based tests pass unmodified except the one superseded assertion)

## Related Tickets
- TCK-20260821-WS-ENTITY-DELTA-BROADCAST
- TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- frontend/src/hooks/useSimulation.ts
- frontend/src/components/GameCanvas.tsx
- frontend/src/App.tsx
- frontend/src/test/useSimulation.test.tsx

## Assumptions / Open Questions
- whether the second, separate EventSource-reconnect infinite-retry loop also gets bounded-retry+visible-error treatment, or is deliberately left alone, is not resolved by investigation and should be an explicit decision in this ticket
- no existing frontend retry-count utility exists anywhere -- new local state, keep minimal
- layer registered as new value `frontend` (registries/layer_registry.jsonl) since no existing entry covers frontend/React client code distinct from backend engine/systems layers; this layer should be reused by sibling tickets in the live-map-reconnection epic

## Implementation Notes

Implemented per the approved `staging_artifacts/TCK-20260821-PHASED-LOADING-STATE-MACHINE/plan.md`,
Steps 1-12 in order, against the current WebSocket-based `useSimulation.ts` (investigation.md's
re-mapping from the ticket's stale SSE-era wording).

- **Step 1**: `SimStatus` (`frontend/src/hooks/useSimulation.ts`) replaced with the 9-member union
  `INITIALIZING | FETCHING_WORLD_DATA | CONNECTING_LIVE | SYNCING | READY | RUNNING | PAUSED |
  STOPPED | LOAD_ERROR`. `CONNECTING` removed entirely (not aliased). Initial `useState` value
  changed to `'INITIALIZING'`.
- **Step 2**: Added module-level `LOAD_RETRY_LIMIT = 5` and a `retryCountRef` (`useRef(0)`) alongside
  the hook's other refs.
- **Step 3**: `loadInitial()` now calls `setStatus('FETCHING_WORLD_DATA')` as its first statement.
  The `catch` block increments `retryCountRef`; below `LOAD_RETRY_LIMIT` it keeps the existing
  1000ms `setTimeout(loadInitial, 1000)` retry, at/above the limit it sets `status` to the new
  terminal `LOAD_ERROR` and schedules no further retry (no auto-recovery short of a full
  page-reload remount).
- **Step 4**: `connectWS()` gets exactly 3 new `setStatus` calls: `CONNECTING_LIVE` as the first
  line of the function body (before `new WebSocket(...)`), `SYNCING` in `onopen` immediately after
  the handshake `send()`, and `READY` in `onmessage` immediately after the existing `isDelta`
  shape-guard's early-return block (fires unconditionally on every qualifying delta, not
  first-time-only).
- **Step 5**: `scheduleReconnect()` got only a code comment recording the deliberate decision to
  leave it unbounded (steady-state live-view reconnect path, as opposed to `loadInitial()`'s
  one-shot load) — no behavioral change; body, 2000ms delay, and both call sites untouched.
- **Step 6**: `Header.tsx`'s exhaustive `STATUS_COLORS: Record<SimStatus, string>` extended to all 9
  new members (yellow for the four pre-READY phases, green for READY/RUNNING, red for
  STOPPED/LOAD_ERROR) — this is the build-breaking gap the investigation flagged since `Header.tsx`
  wasn't in the ticket's original Related Code Areas.
- **Step 7**: New `frontend/src/components/SimulationLoadingGate.tsx` — gates `children` behind a
  `LOADING_STATUSES` allowlist (`INITIALIZING`/`FETCHING_WORLD_DATA`/`CONNECTING_LIVE`/`SYNCING`),
  a distinct `LOAD_ERROR` UI, and passes `children` through for everything else
  (`READY`/`RUNNING`/`PAUSED`/`STOPPED`) — deliberately not `status === 'READY'` literal equality,
  since `fallbackPoll` overwrites `READY` with `RUNNING`/`PAUSED`/`STOPPED` within 500ms.
- **Step 8**: `App.tsx` now wraps the existing `<GameCanvas>` element in `<SimulationLoadingGate
  status={sim.status}>` with all `GameCanvas` props preserved unchanged.
- **Step 9**: `useSimulation.test.tsx`'s `initializes with default values` test's status assertion
  changed to `'FETCHING_WORLD_DATA'` (not the literal `'INITIALIZING'` value, per the plan's Step 3
  correction: `setStatus('FETCHING_WORLD_DATA')` runs synchronously inside the same `act()` flush
  `renderHook()` performs in this React 19 + RTL 16 harness, so `'INITIALIZING'` is never
  independently observable post-`renderHook()` here even though it is the real initial value and is
  briefly paintable in a live browser). Added 7 new tests covering: immediate
  `FETCHING_WORLD_DATA`; in-flight `FETCHING_WORLD_DATA` with a held-open `/map` fetch;
  `CONNECTING_LIVE` once the WS connection attempt begins; `SYNCING` on `onopen` staying `SYNCING`
  through the non-delta initial summary message; `READY` on the first `isDelta`-shaped message;
  bounded-retry-to-`LOAD_ERROR` after 5 failures (via `vi.useFakeTimers()` +
  `vi.advanceTimersByTimeAsync`); and `LOAD_ERROR` terminal/no-auto-recovery semantics (further
  time passing plus a subsequently-succeeding fetch never re-invokes `loadInitial`). One test's
  original design (resolving a held-open promise mid-test) produced a pre-existing-pattern React
  `act()` console warning identical to 6 warnings already present in the original file before this
  ticket's changes (confirmed via `git stash` comparison against the pre-ticket file) — resolved by
  never resolving the held-open promise instead (the effect's own `cancelled` guard makes this safe
  across test-cleanup unmount).
- **Step 10**: New `frontend/src/test/SimulationLoadingGate.test.tsx` (9 tests) — phase-specific
  text for each of the 4 loading statuses, the distinct `LOAD_ERROR` UI, and pass-through rendering
  for `READY`/`RUNNING`/`PAUSED`/`STOPPED` (confirming the allowlist gating, not literal `READY`
  equality).
- **Step 11**: Architecture guard verified: `git diff --stat -- frontend/src/components/GameCanvas.tsx
  frontend/src/hooks/useCanvas.ts` is empty.
- **Step 12**: `docs/engine/contracts/frontend.md` updated — §2.A documents the `INITIALIZING` →
  `FETCHING_WORLD_DATA` wiring and the new bounded-retry/`LOAD_ERROR` behavior; §2.B documents the
  `CONNECTING_LIVE`/`SYNCING`/`READY` WS-lifecycle transitions and records the Step 5 asymmetry
  (`scheduleReconnect()` stays unbounded, unlike `loadInitial()`); §4 adds a bullet noting
  `GameCanvas` is now gated behind `SimulationLoadingGate`. §1, §2.C, §3, §5, and the top-of-file
  "Known gap" callout were left untouched per the plan.

No deviations from the plan. `staging_artifacts/TCK-20260821-PHASED-LOADING-STATE-MACHINE/plan.md`
required no corrections beyond what it had already self-corrected during its own review rounds.

## Test Summary

- `cd frontend && npx vitest run src/test/useSimulation.test.tsx` — 17/17 passed (10 pre-existing
  minus 1 superseded assertion, plus 7 new).
- `cd frontend && npx vitest run src/test/SimulationLoadingGate.test.tsx` — 9/9 passed (new file).
- `cd frontend && npm run build` (`tsc -b && vite build`) — exit 0, no type errors (this is the gate
  that would have caught a missed `Header.tsx` `STATUS_COLORS` entry).
- `git diff --stat -- frontend/src/components/GameCanvas.tsx frontend/src/hooks/useCanvas.ts` —
  empty, confirming the Out-of-Scope constraint held.
- No backend/Python changes; no `pytest` command applies to this ticket (frontend-only, per
  test_plan.md).

## Files Changed

- `frontend/src/hooks/useSimulation.ts` — `SimStatus` union, `LOAD_RETRY_LIMIT`/`retryCountRef`,
  bounded `loadInitial()` retry + `LOAD_ERROR` transition, `connectWS()` status wiring,
  `scheduleReconnect()` comment.
- `frontend/src/components/Header.tsx` — `STATUS_COLORS` extended to the 9-member union.
- `frontend/src/components/SimulationLoadingGate.tsx` (new) — phase-aware loading/error gate.
- `frontend/src/App.tsx` — mounts `SimulationLoadingGate` around `GameCanvas`.
- `frontend/src/test/useSimulation.test.tsx` — 1 changed assertion + 7 new tests.
- `frontend/src/test/SimulationLoadingGate.test.tsx` (new) — 9 tests.
- `docs/engine/contracts/frontend.md` — §2.A, §2.B, §4 updated.
- `staging_artifacts/TCK-20260821-PHASED-LOADING-STATE-MACHINE/investigation.md`,
  `plan.md`, `test_plan.md` — pre-existing from this ticket's Investigate/Plan phases (read and
  followed in this Implement run; not rewritten).

## Completion Summary

Replaced the single opaque `CONNECTING` status with a 9-member `SimStatus` state machine
(`INITIALIZING` → `FETCHING_WORLD_DATA` → `CONNECTING_LIVE` → `SYNCING` → `READY`, plus existing
`RUNNING`/`PAUSED`/`STOPPED`, plus terminal `LOAD_ERROR`), wired into `useSimulation.ts`'s
`loadInitial()`/`connectWS()` lifecycle at four exact anchor points that previously set no status at
all. `loadInitial()`'s fetch retry is now bounded at 5 attempts before transitioning to a
user-visible `LOAD_ERROR`; `scheduleReconnect()` was deliberately left unbounded with a rationale
comment. A new `SimulationLoadingGate` component renders phase-specific loading/error UI and wraps
`GameCanvas` in `App.tsx`, gated on a loading-status allowlist (not literal `READY` equality) to
survive `fallbackPoll` overwriting `READY` within 500ms. `GameCanvas.tsx` and `useCanvas.ts` remain
byte-for-byte unmodified. All 4 acceptance criteria are met; build gate and both test files pass in
full.
