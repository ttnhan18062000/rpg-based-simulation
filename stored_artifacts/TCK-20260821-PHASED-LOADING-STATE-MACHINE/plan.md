---
status: historical
layer: frontend
authority: P2
audience: agent
ticket_id: TCK-20260821-PHASED-LOADING-STATE-MACHINE
artifact_type: plan
tags: [websocket]
---

# Implementation Plan — TCK-20260821-PHASED-LOADING-STATE-MACHINE

## Summary

Replace `useSimulation.ts`'s single opaque `CONNECTING` status with a nine-member `SimStatus`
union (`INITIALIZING`, `FETCHING_WORLD_DATA`, `CONNECTING_LIVE`, `SYNCING`, `READY`, plus existing
`RUNNING`/`PAUSED`/`STOPPED`, plus a new terminal `LOAD_ERROR`), wire `setStatus` calls into four
exact anchor points that today set no status at all (`loadInitial()`'s start, and `connectWS()`'s
start / `onopen` / first-`isDelta`-message), bound `loadInitial()`'s retry with a `useRef` counter
capped at 5 attempts before transitioning to `LOAD_ERROR`, deliberately leave `scheduleReconnect()`
unbounded (stated rationale, not silent), extend `Header.tsx`'s exhaustive `STATUS_COLORS` Record
for the new members, and add a new `SimulationLoadingGate` wrapper component mounted in `App.tsx`
around the existing `<GameCanvas>` element — gating on a loading-status allowlist rather than literal
`status === 'READY'` equality, since `fallbackPoll` overwrites `READY` with
`RUNNING`/`PAUSED`/`STOPPED` within 500ms of reaching it and the gate must not re-hide `GameCanvas`
when that happens. `GameCanvas.tsx` and `useCanvas.ts` are not touched by any step.

## Steps

### Step 1 — Extend `SimStatus` and the initial hook state
**Files:** `frontend/src/hooks/useSimulation.ts`
**Change:** At `frontend/src/hooks/useSimulation.ts:17` (verified by direct read), replace
`export type SimStatus = 'CONNECTING' | 'RUNNING' | 'PAUSED' | 'STOPPED';` with:
```ts
export type SimStatus =
  | 'INITIALIZING'
  | 'FETCHING_WORLD_DATA'
  | 'CONNECTING_LIVE'
  | 'SYNCING'
  | 'READY'
  | 'RUNNING'
  | 'PAUSED'
  | 'STOPPED'
  | 'LOAD_ERROR';
```
`CONNECTING` is removed entirely (superseded by `INITIALIZING`/`FETCHING_WORLD_DATA`), not kept as
an alias — AC1 says the machine "starts at INITIALIZING not bare CONNECTING." At
`frontend/src/hooks/useSimulation.ts:78` (verified by direct read: `const [status, setStatus] =
useState<SimStatus>('CONNECTING');`), change the initial value to `'INITIALIZING'`.
**Do NOT touch:** Any other field in `SimulationState` (line 26-47) or the `DecodedMapData` interface.
**Verify:** The initial `useState<SimStatus>('INITIALIZING')` value (this step) is the literal
type-level/mount-time guarantee that AC1's "starts at INITIALIZING" requires — it is real and
briefly paintable in a live browser (React defers passive effects to after paint there), but it is
**not independently observable via a synchronous post-`renderHook()` assertion in this test
harness** — see the correction note added to Step 3 below (found during architecture review).
test_plan.md item 1 ("starts at INITIALIZING, not CONNECTING") must be implemented in Step 9 as an
assertion of `'FETCHING_WORLD_DATA'`, not `'INITIALIZING'` — see Step 9's corrected bullet.

### Step 2 — Add `LOAD_RETRY_LIMIT` constant and `retryCountRef`
**Files:** `frontend/src/hooks/useSimulation.ts`
**Change:** Add `const LOAD_RETRY_LIMIT = 5;` as a module-level constant near the top of the file
(after `const API_BASE = '/api/v1';` at line 4). **N = 5**, chosen because: at the existing fixed
1000ms retry delay (`useSimulation.ts:116`, unchanged by this plan), 5 attempts bound worst-case
silent-failure time to ~4 seconds before the user sees `LOAD_ERROR` — short enough not to feel hung
on a page load, long enough to absorb a single slow-backend blip or transient network hiccup without
flashing an error on a merely-slow-but-working connection. Inside `useSimulation()` (line 63-79), add
`const retryCountRef = useRef(0);` alongside the other refs (after `mapLoadedRef` at line 82) — a
`ref`, not `useState`, because the counter is read-and-incremented synchronously inside a `catch`
block that must not itself trigger a re-render, and does not need to drive rendering on its own (only
the derived `LOAD_ERROR` status transition needs to render).
**Do NOT touch:** `mapLoadedRef`/`staticLoadedRef`/`selectedIdRef`/`lastSelKeyRef` — leave their
existing declarations and usages untouched; only add the new ref alongside them.
**Verify:** Setup step for Step 3's test (test_plan.md item 6); no standalone test (the constant and
ref have no independent behavior until Step 3 wires them in).

### Step 3 — Bound `loadInitial()`'s retry with the counter; transition to `LOAD_ERROR`
**Files:** `frontend/src/hooks/useSimulation.ts`
**Change:** At `frontend/src/hooks/useSimulation.ts:93` (verified by direct read: `const loadInitial
= async () => {`), add `setStatus('FETCHING_WORLD_DATA');` as the very first statement inside the
function body, before the existing `try {` at line 94 — this is the exact anchor for AC1's
`FETCHING_WORLD_DATA` transition; it fires synchronously the moment `loadInitial()` is invoked (line
119, `loadInitial();`), before the `Promise.all` awaits anything, which is what test_plan.md item 2
needs to observe with a held-open mock fetch.

**Correction to test_plan.md item 1 / Step 1's originally-planned assertion (found during
architecture review — must be applied in Step 9, not the value test_plan.md item 1 originally
described):** because `setStatus('FETCHING_WORLD_DATA')` here runs synchronously, *before* the first
`await`, inside `loadInitial()`, which is itself invoked synchronously (no intervening `await`) from
the mount `useEffect`, and this project's test stack is React 19 + `@testing-library/react` 16
(confirmed via `frontend/package.json`) — whose `act()` (used internally by `renderHook`) flushes
passive effects *and* any synchronous state updates they trigger, before returning control —
`result.current.status` will already read `'FETCHING_WORLD_DATA'`, not `'INITIALIZING'`, immediately
after a non-awaited `renderHook(() => useSimulation())` call. This is a real timing fact, not a
hypothetical: there is no way to observe the hook in the literal `'INITIALIZING'` state through this
`renderHook()`-based harness, because the transition away from it happens inside the same synchronous
`act()` flush the test's first assertion runs after. (In the live browser this is different — passive
effects are scheduled after paint, so `'INITIALIZING'` is genuinely visible for one frame — but that
is not what the unit test harness exercises.) Step 9 must therefore assert
`expect(result.current.status).toBe('FETCHING_WORLD_DATA')` at the point test_plan.md item 1
describes as "immediate (pre-fetch-resolution)", not `'INITIALIZING'`. Do not attempt to work around
this by delaying the mock fetch (test_plan.md item 2's technique) — the
`setStatus('FETCHING_WORLD_DATA')` call is unconditional and precedes the `Promise.all` entirely, so
no fetch-timing control changes this outcome.

Replace the catch block at `frontend/src/hooks/useSimulation.ts:115-117` (verified by direct read:
```ts
} catch {
  if (!cancelled) setTimeout(loadInitial, 1000);
}
```
) with:
```ts
} catch {
  if (cancelled) return;
  retryCountRef.current += 1;
  if (retryCountRef.current >= LOAD_RETRY_LIMIT) {
    setStatus('LOAD_ERROR');
  } else {
    setTimeout(loadInitial, 1000);
  }
}
```
**`LOAD_ERROR` semantics — terminal, not auto-recoverable (resolves test_plan.md item 7's open
question):** once `retryCountRef.current` reaches `LOAD_RETRY_LIMIT`, no further `setTimeout(loadInitial,
...)` is scheduled — `loadInitial` is never invoked again for the remaining lifetime of this mount.
There is no retry button, no automatic re-attempt, and no code path that clears `retryCountRef` or
re-enters `FETCHING_WORLD_DATA` after `LOAD_ERROR`. Recovery requires a full page reload (which
remounts the hook and resets `retryCountRef` to 0 via a fresh `useRef(0)`). This is a deliberate
minimal-scope choice: the ticket's AC2 only requires the transition to happen, not a recovery UX, and
inventing a retry-button/auto-resume mechanism would be scope creep beyond "bound the retry and show
an error."
**Other writers to `status` this step must coexist with:** `fallbackPoll`'s
`setStatus('STOPPED'|'PAUSED'|'RUNNING')` (lines 231-237, unchanged — see Step 4) only starts once
`connectWS()` has been called (line 302, inside the second `useEffect` gated on `[mapData]`), which
itself only fires after `loadInitial()` has already succeeded (`mapData` is set at line 106). Since
`LOAD_ERROR` is only reachable when `loadInitial()` has *failed* 5 times, `mapData` is never set on
that path, the second `useEffect`'s guard (`if (!mapLoadedRef.current && !mapData) return;`, line
125) keeps it from ever running, and `fallbackPoll` never starts — there is no race between this
step's `LOAD_ERROR` write and `fallbackPoll`'s writes; they are mutually exclusive by construction of
the existing `mapData`-gated effect dependency.
**Do NOT touch:** The `Promise.all`/fetch calls themselves (lines 95-99), the success branch (lines
100-114), or the 1000ms retry delay value.
**Verify:** New test `loadInitial's fetch-retry loop is bounded and transitions to an ERROR-class
status after N failures` (test_plan.md item 6, AC2); new test for terminal semantics (test_plan.md
item 7, pinned to "no silent auto-recovery").

### Step 4 — Wire `CONNECTING_LIVE` / `SYNCING` / `READY` into `connectWS()`'s lifecycle
**Files:** `frontend/src/hooks/useSimulation.ts`
**Chosen boundary (resolves investigation.md Risk 4 — option (a)):** `CONNECTING_LIVE` covers from
`connectWS()`'s invocation until `ws.onopen` fires; `SYNCING` covers from `onopen` (handshake sent)
until the first `isDelta`-shaped message, regardless of the one-time non-delta initial summary
message received in between. This is the simpler of the two defensible boundaries investigation.md
lays out, anchors cleanly to three call sites already present in the code, and requires no new
bookkeeping (no "have we seen the summary message yet" flag).

**Exact anchors (all verified by direct read of the current file):**
1. `CONNECTING_LIVE` — inside `const connectWS = () => {` (`useSimulation.ts:140`), add
   `setStatus('CONNECTING_LIVE');` as the first line of the function body, before `ws = new
   WebSocket(...)` (line 141).
2. `SYNCING` — inside `ws.onopen = () => { ws!.send(...); }` (`useSimulation.ts:143-145`), add
   `setStatus('SYNCING');` as the line immediately after `ws!.send(JSON.stringify({ type:
   'handshake', format: 'json' }));` (line 144).
3. `READY` — inside `ws.onmessage`'s `isDelta` branch. The existing shape-guard is at
   `useSimulation.ts:156` (`const isDelta = Array.isArray(data.changed) &&
   Array.isArray(data.removed);`), followed by the non-delta early-return block at lines 157-162.
   Add `setStatus('READY');` as the first line **after** that early-return block (i.e. immediately
   before `setTick(data.tick);` at line 164) — this fires on every message that passes the
   `isDelta` guard, not gated behind a "first time only" flag. This is intentionally unconditional:
   calling `setStatus('READY')` on every subsequent delta message too is a no-op re-render skip in
   React once `status` is already `'READY'` (or once `fallbackPoll` has since overwritten it — see
   Known Constraints), so no extra ref/flag is needed to track "have we already transitioned."
   **This directly reuses the ticket-mandated `isDelta` shape-guard as the sole SYNCING→READY
   trigger** — no new detection mechanism is introduced (anti-drift guard from investigation.md).
4. `onclose`/`onerror` (`useSimulation.ts:207-214`) are **not** modified by this step — they call
   `scheduleReconnect()` exactly as today; see Step 5 for that decision.

**Other writers to `status` this step must coexist with:** `fallbackPoll`'s `setStatus('RUNNING'|
'PAUSED'|'STOPPED')` (lines 231-237) is driven by `setInterval(fallbackPoll, 500)` (line 302), which
starts immediately after `connectWS()` is first called (line 217) — i.e. **before** `ws.onopen` can
possibly fire (network round-trip), so `fallbackPoll`'s first 500ms tick can race ahead of
`CONNECTING_LIVE`/`SYNCING` and overwrite one of them with `RUNNING`/`PAUSED`/`STOPPED` before the
first delta ever lands (if `/stats` resolves before the WS handshake + first delta do). This is a
real, accepted race — documented in Known Constraints below — not fixed by this step: fixing it would
require making `fallbackPoll` respect the WS-lifecycle status, which is a `fallbackPoll` behavior
change outside this ticket's scope (ticket's Out of Scope: "Building the underlying WS connect
sequence — this ticket only wires status transitions to it").
**Do NOT touch:** `onmessage`'s entity-reduction logic (lines 166-201), the `onclose`/`onerror`
bodies themselves, or `fallbackPoll` (lines 221-300) in any way.
**Verify:** New tests `transitions to CONNECTING_LIVE...` (test_plan.md item 3), `transitions to
SYNCING on WS open...` (test_plan.md item 4), `transitions to READY exactly on the first
isDelta-shaped message...` (test_plan.md item 5) — all AC1.

### Step 5 — Document (do not change) the `scheduleReconnect()` decision
**Files:** `frontend/src/hooks/useSimulation.ts`
**Decision (resolves investigation.md Risk 1 / ticket's Out of Scope open question):**
`scheduleReconnect()` (`useSimulation.ts:132-138`) is **deliberately left unbounded** — no retry
counter, no `LOAD_ERROR`-equivalent transition on the WS-reconnect path. Rationale: `loadInitial()`
is a one-shot initial data load where infinite silent retry with no user feedback is a real defect
(AC2's whole premise); `scheduleReconnect()` is the steady-state live-view reconnect path for an
already-running dashboard-style client, where an infinite background reconnect attempt is the
*correct* behavior (matching what ticket 6, `TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET`, explicitly
built and documented as intentional — "mirroring the current onerror/setTimeout retry behavior").
Bounding it would mean the live view permanently gives up reconnecting after N drops, which is worse
UX for a long-lived simulation viewer than occasionally-noisy infinite retry. This ticket's own Scope
text only commits to bounding `loadInitial()`'s retry, not `scheduleReconnect()`'s.
**Change:** Add a short code comment directly above `const scheduleReconnect = () => {` (line 132)
stating this is an intentional, ticket-reviewed decision to leave it unbounded (for future-reader
discoverability), e.g.:
```ts
// Deliberately unbounded: unlike loadInitial()'s one-shot retry (see LOAD_ERROR below), this is
// the steady-state live-view reconnect path and should keep retrying indefinitely in the
// background. Decision recorded in TCK-20260821-PHASED-LOADING-STATE-MACHINE.
```
No behavioral change — `scheduleReconnect()`'s body, `onclose`/`onerror`'s calls into it, and the
2000ms delay all stay byte-for-byte as they are today aside from this comment.
**Do NOT touch:** The function body, the 2000ms constant, or either call site (`onclose`
line 207-209, `onerror` line 211-214).
**Verify:** Existing tests `reconnects after WebSocket close` / `reconnects after WebSocket error`
(`useSimulation.test.tsx:232-264`) continue to pass **unmodified** — this is itself the verification
that the decision was "leave alone," not "bound it."

### Step 6 — Extend `Header.tsx`'s `STATUS_COLORS` Record
**Files:** `frontend/src/components/Header.tsx`
**Change:** At `frontend/src/components/Header.tsx:16-21` (verified by direct read):
```ts
const STATUS_COLORS: Record<SimStatus, string> = {
  CONNECTING: 'text-accent-yellow',
  RUNNING: 'text-accent-green',
  PAUSED: 'text-accent-yellow',
  STOPPED: 'text-accent-red',
};
```
Replace with a 9-entry Record matching the new `SimStatus` union exactly (`CONNECTING` removed, since
it no longer exists in the union and TypeScript's excess-property check on this object literal would
reject it):
```ts
const STATUS_COLORS: Record<SimStatus, string> = {
  INITIALIZING: 'text-accent-yellow',
  FETCHING_WORLD_DATA: 'text-accent-yellow',
  CONNECTING_LIVE: 'text-accent-yellow',
  SYNCING: 'text-accent-yellow',
  READY: 'text-accent-green',
  RUNNING: 'text-accent-green',
  PAUSED: 'text-accent-yellow',
  STOPPED: 'text-accent-red',
  LOAD_ERROR: 'text-accent-red',
};
```
Reuses the same four Tailwind token classes already present in the file (no new color tokens
introduced): yellow for all pre-READY/in-progress phases (matching the existing `CONNECTING`/`PAUSED`
convention), green for `READY`/`RUNNING`, red for `STOPPED`/`LOAD_ERROR`.
**This is the single build-breaking gap if missed** (investigation.md Risk 2): `Record<SimStatus,
string>` is exhaustive, so extending `SimStatus` (Step 1) without this step fails `tsc -b` during
`npm run build`.
**Do NOT touch:** Anything else in `Header.tsx` — the `HeaderProps` interface (lines 6-14), the
component body (lines 23-64), imports, or JSX structure. This step changes only the `STATUS_COLORS`
object literal's contents; `Header.tsx` stays otherwise byte-for-byte identical.
**Verify:** `cd frontend && npm run build` exits 0 (test_plan.md's Build gate section; no dedicated
vitest test — `Header.tsx` has no existing unit test file).

### Step 7 — New `SimulationLoadingGate` wrapper component
**Files:** `frontend/src/components/SimulationLoadingGate.tsx` (new file)
**Change:** Create a new component that gates its `children` behind `status`, rendering
phase-specific loading text for pre-READY statuses, a distinct error UI for `LOAD_ERROR`, and
`children` for everything else:
```tsx
import type { ReactNode } from 'react';
import type { SimStatus } from '@/hooks/useSimulation';

interface SimulationLoadingGateProps {
  status: SimStatus;
  children: ReactNode;
}

type LoadingPhase = 'INITIALIZING' | 'FETCHING_WORLD_DATA' | 'CONNECTING_LIVE' | 'SYNCING';

const PHASE_LABELS: Record<LoadingPhase, string> = {
  INITIALIZING: 'Initializing...',
  FETCHING_WORLD_DATA: 'Fetching world data...',
  CONNECTING_LIVE: 'Connecting to live stream...',
  SYNCING: 'Syncing world state...',
};

const LOADING_STATUSES = new Set<string>(Object.keys(PHASE_LABELS));

export function SimulationLoadingGate({ status, children }: SimulationLoadingGateProps) {
  if (status === 'LOAD_ERROR') {
    return (
      <div className="flex items-center justify-center h-full text-accent-red text-sm">
        Failed to load simulation data. Please reload the page.
      </div>
    );
  }
  if (LOADING_STATUSES.has(status)) {
    return (
      <div className="flex items-center justify-center h-full text-text-secondary text-sm animate-pulse">
        {PHASE_LABELS[status as LoadingPhase]}
      </div>
    );
  }
  return <>{children}</>;
}
```
**Critical gating design note (resolves the naive AC3 reading, extends investigation.md Risk 5):**
the gate does **not** check `status === 'READY'` literally. It renders `children` for `READY` *and*
`RUNNING`/`PAUSED`/`STOPPED` (anything not in `LOADING_STATUSES` and not `LOAD_ERROR`). This is
required because `fallbackPoll` (`useSimulation.ts:231-237`, unchanged) overwrites `READY` with
`RUNNING`/`PAUSED`/`STOPPED` within 500ms of it being reached (see Known Constraints) — if the gate
checked `status === 'READY'` literally, `GameCanvas` would render for one poll interval and then
vanish again the instant `fallbackPoll` fires. Gating on "is this one of the four pre-READY loading
phases" (an allowlist of what to *hide* behind) rather than "is this exactly READY" (an allowlist of
what to *show*) is the only formulation that stays correct across the READY→RUNNING/PAUSED/STOPPED
handoff.
**Do NOT touch:** `GameCanvas.tsx`'s own `!mapData` branch (lines 421-424) — this component does not
patch, duplicate, or reference it. By construction, `mapData` is always non-null by the time this
gate renders `children` (the WS `useEffect` that reaches any pre-READY/READY status is itself gated
on `mapData` being set, `useSimulation.ts:125`), so that branch is unreachable dead code left in
place, not "fixed."
**Verify:** New tests `new wrapper component renders phase-specific text for each non-READY status`
and `distinct error UI is rendered when status is the new ERROR-class status` (test_plan.md items
8-9, AC3).

### Step 8 — Mount `SimulationLoadingGate` around `GameCanvas` in `App.tsx`
**Files:** `frontend/src/App.tsx`
**Change:** At `frontend/src/App.tsx:48-60` (verified by direct read), the current unconditional
`<GameCanvas ... />` element (mounted whenever `currentPage === 'simulation'`, regardless of
`sim.status`) is wrapped with the new gate:
```tsx
import { SimulationLoadingGate } from '@/components/SimulationLoadingGate';
```
(new import, added alongside the existing component imports at lines 3-6), and:
```tsx
<SimulationLoadingGate status={sim.status}>
  <GameCanvas
    mapData={sim.mapData}
    entities={sim.entities}
    selectedEntity={sim.selectedEntity}
    groundItems={sim.groundItems}
    buildings={sim.buildings}
    resourceNodes={sim.resourceNodes}
    regions={sim.regions}
    selectedEntityId={sim.selectedEntityId}
    onEntityClick={handleSelectEntity}
    onGroundItemClick={handleGroundItemClick}
    onBuildingClick={handleBuildingClick}
  />
</SimulationLoadingGate>
```
replacing the bare `<GameCanvas ... />` element in place (same props, unchanged, just now wrapped).
No other line in `App.tsx` changes — `<Header>` (lines 37-45), `<Sidebar>` (lines 61-75), and the
`currentPage === 'simulation'` branch structure (lines 46-79) stay as-is.
**Do NOT touch:** `GameCanvas`'s own prop list/values, `Sidebar`, `Header`, or the `ApiDocsPage`
branch.
**Verify:** Covered indirectly by Step 7's component tests (test_plan.md items 8-9) exercising the
gate in isolation; no new `App.tsx`-specific test is required by test_plan.md (no existing `App.tsx`
test file exists in `frontend/src/test/` to extend).

### Step 9 — Update `useSimulation.test.tsx` for the new status enum
**Files:** `frontend/src/test/useSimulation.test.tsx`
**Change:**
- Update the existing `initializes with default values` test (line 105-112): change
  `expect(result.current.status).toBe('CONNECTING')` (line 110) to
  `expect(result.current.status).toBe('FETCHING_WORLD_DATA')` — **not** `'INITIALIZING'` as
  test_plan.md item 1 originally described (AC4). `'INITIALIZING'` is the real `useState` initial
  value (satisfying AC1's "starts at INITIALIZING" at the type/mount level) but is not observable
  through a synchronous post-`renderHook()` assertion in this React 19 + RTL 16 harness, since the
  mount effect's synchronous `setStatus('FETCHING_WORLD_DATA')` call (Step 3) is already flushed by
  `act()` before this test's assertion runs — see Step 3's correction note.
- Add the 7 new hook-level tests from test_plan.md items 1-7 (items 1 and this bullet's edit
  together supersede the old assertion per test_plan.md's note: "Supersedes/replaces the existing
  `'initializes with default values'` assertion"): tests 2-7 need `vi.useFakeTimers()` +
  `vi.advanceTimersByTime` for the 1000ms `loadInitial` retry delay (test 6) and a controllable/
  delayed mock fetch to observe `FETCHING_WORLD_DATA` before `Promise.all` resolves (test 2), per
  test_plan.md's exact descriptions.
- All other existing tests (`sends handshake...`, `opens WebSocket to /api/v1/ws...`,
  `ignores/threads the initial full-state message...`, `reduces a real {...} delta correctly`,
  `sendControl(...)` x2, `reconnects after WebSocket close`/`error`, `loadInitial still fetches...`)
  must keep passing **unmodified** — none of Steps 1-6 change their preconditions or assertions.
**Do NOT touch:** The `MockWebSocket` class, `defaultMockFetch`, or `renderConnectedHook()` harness
(lines 1-91) — reuse as-is.
**Verify:** `cd frontend && npx vitest run src/test/useSimulation.test.tsx` — all tests (10 existing,
minus 1 superseded, plus 7 new = 16 total) pass.

### Step 10 — New `SimulationLoadingGate.test.tsx`
**Files:** `frontend/src/test/SimulationLoadingGate.test.tsx` (new file)
**Change:** Add component tests per test_plan.md items 8-9: for each of `INITIALIZING`,
`FETCHING_WORLD_DATA`, `CONNECTING_LIVE`, `SYNCING`, and `LOAD_ERROR`, render
`<SimulationLoadingGate status={...}><div data-testid="canvas-child">canvas</div></SimulationLoadingGate>`
and assert the phase-specific text (or error text) renders and `canvas-child` does **not**. For
`READY`, `RUNNING`, `PAUSED`, `STOPPED`, assert `canvas-child` **does** render (covering the
READY→RUNNING/PAUSED/STOPPED handoff case from Step 7's gating design, not just literal `READY`).
There is no existing component-test file in `frontend/src/test/` to mirror style from (only
`setup.ts` and `useSimulation.test.tsx` exist there today) — use `@testing-library/react`'s `render`
+ `screen` (already a project dependency per `useSimulation.test.tsx`'s `@testing-library/react`
import) and `vitest`'s `describe`/`it`/`expect`, matching the import style already used in
`useSimulation.test.tsx:1-2`.
**Do NOT touch:** `useSimulation.test.tsx` in this step (that's Step 9).
**Verify:** `cd frontend && npx vitest run src/test/SimulationLoadingGate.test.tsx`.

### Step 11 — Architecture guard (verification only, no code change)
**Files:** None (verification step).
**Change:** None.
**Do NOT touch:** N/A.
**Verify:** `git diff --stat -- frontend/src/components/GameCanvas.tsx frontend/src/hooks/useCanvas.ts`
must output nothing (empty diff) after Steps 1-10 are complete. Run during Test/Verify phase per
test_plan.md item 10.

### Step 12 — Update `docs/engine/contracts/frontend.md` (§2.A, §2.B) [added during architecture review]
**Files:** `docs/engine/contracts/frontend.md`
**Change:** investigation.md's "Docs Requiring Update" section explicitly flags this file as needing
updates once this ticket lands (§2.A needs the new bounded-retry behavior, §2.B needs the new
WS-lifecycle-driven `SimStatus` transitions), but no step for it existed in the original 11-step
plan — this closes that gap, per the project's Workflow Rule ("Update related docs" is required
After Work whenever behavior changes and docs describe it).
- §2.A ("Initial Load (Full State)", currently lines 30-39): add a short subsection documenting (a)
  the new `status` wiring — the hook mounts with `status` defaulting to `INITIALIZING`
  (`useState<SimStatus>('INITIALIZING')`), then `loadInitial()` sets `status` to
  `FETCHING_WORLD_DATA` as its first synchronous action, before the three fetches this section
  already describes are issued — and (b) the new bounded-retry behavior: `loadInitial()` now tracks
  a retry counter (`retryCountRef`), retries up to `LOAD_RETRY_LIMIT` (5) times at the existing fixed
  1000ms delay, and transitions `status` to the new terminal `LOAD_ERROR` value (no auto-recovery
  short of a full page reload/remount) if all attempts fail — superseding the current description,
  which today says nothing about `status`/retry/failure behavior at all.
- §2.B ("Delta Sync (WebSocket)", currently lines 41-73): document the new WS-lifecycle-driven
  `SimStatus` transitions — `CONNECTING_LIVE` set at the start of `connectWS()`, `SYNCING` set on
  `onopen` immediately after the handshake is sent, `READY` set on the first `isDelta`-shaped message
  (unconditionally on every subsequent delta too, not gated behind a first-time-only flag). Also
  record the Step 5 decision next to the existing "Reconnect" bullet: `scheduleReconnect()`'s
  2000ms reconnect remains deliberately unbounded, with no `LOAD_ERROR`-equivalent visible failure
  state, unlike `loadInitial()`'s new bounded path — state this as a stated, reviewed asymmetry, not
  an oversight.
- Add one bullet to §4 ("UI Components") noting `GameCanvas` is now gated behind the new
  `SimulationLoadingGate` phase-aware loading/error wrapper for all pre-`READY` statuses and
  `LOAD_ERROR`, per Steps 7-8.
**Do NOT touch:** §1 (Technology Stack), §2.C (Inspection Polling), §3 (Rendering Engine), §5 (State
Handling Strategy), or the top-of-file "Known gap" callout block (line 12) — none of them describe
loading-state/status behavior and none are affected by this ticket.
**Verify:** No automated test covers doc content; this is a manual-review artifact-completeness
check during Finalize. Since this is a `docs/` file change, run `make knowledge-index-update` during
Finalize per the project's Workflow Rule.

## Scope Guards

- `frontend/src/components/GameCanvas.tsx` and `frontend/src/hooks/useCanvas.ts` — byte-for-byte
  unmodified, including not touching the now-dead `!mapData` "Loading map..." branch (lines 421-424).
  Verified by Step 11's empty `git diff --stat`.
- `fallbackPoll` (`useSimulation.ts:221-300`) — its own conditional logic (lines 231-237) is not
  modified by any step; only the type it writes into (`SimStatus`) grows via Step 1.
- `scheduleReconnect()` (`useSimulation.ts:132-138`) — body, delay, and call sites unchanged; Step 5
  adds only a comment.
- No new WS message type, new detection heuristic, or change to the `isDelta` shape-guard
  (`useSimulation.ts:156`) — Step 4 reuses it as-is.
- No SSE/`EventSource` code of any kind — the transport is WebSocket-only (ticket 6's prior work);
  the existing `'opens WebSocket to /api/v1/ws, not EventSource'` test must keep passing unmodified.
- `Header.tsx`'s `HeaderProps` interface, component body, and JSX structure — only the
  `STATUS_COLORS` object literal's contents change (Step 6).
- No backend/`src/` Python changes — this ticket is `frontend/` TypeScript/React only.
- No `docs/parity_ledger/` entry changes — investigation.md confirms none apply.
- Building the underlying WS connect sequence itself is out of scope — this plan only wires status
  transitions onto the sequence ticket 6 already built.

## Dependency Map

Steps 1-8 are code changes; Steps 9-11 are verification/tests; Step 12 is a doc update. Ordering
dependencies:
- Step 1 (type extension) must land before Steps 3, 4, 6, 7, 8 — they all reference the new
  `SimStatus` members.
- Step 2 (constant + ref) must land before Step 3 (uses both).
- Steps 3, 4, 5 are independent of each other (different code regions of the same file: `loadInitial`
  vs. `connectWS` vs. `scheduleReconnect`) but all depend on Step 1.
- Step 6 depends only on Step 1 (needs the full new union to write an exhaustive Record) — otherwise
  independent of Steps 2-5.
- Step 7 (new component) depends only on Step 1 (imports `SimStatus`) — independent of Steps 2-6.
- Step 8 depends on Step 7 (imports `SimulationLoadingGate`).
- Step 9 (hook tests) depends on Steps 1-5 being complete (asserts their exact behavior).
- Step 10 (component tests) depends on Step 7.
- Step 11 (architecture guard) should run last, after all other steps, as a final check.
- Step 12 (doc update) depends on Steps 1-8 being complete (it documents their final shape) — can
  run any time after that, in parallel with Steps 9-11; order relative to them doesn't matter.

Recommended implementation order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| "SimStatus extended to superset covering INITIALIZING/FETCHING_WORLD_DATA/CONNECTING_LIVE/SYNCING/READY (plus existing RUNNING/PAUSED/STOPPED), starts at INITIALIZING not bare CONNECTING, transitions to READY only once first live snapshot (SYNCING handoff) has landed" | Steps 1, 4 | test_plan.md items 1, 3, 4, 5 (item 1's test is implemented per Step 9's corrected assertion — `'FETCHING_WORLD_DATA'`, not the literal `'INITIALIZING'` text test_plan.md item 1 describes; see Step 3's correction note) |
| "loadInitial()'s catch tracks a bounded retry counter (not unconditional setTimeout forever); after N failures, status transitions to new visible ERROR-class status" | Steps 2, 3 | test_plan.md item 6 |
| "new wrapper component (mounted in App.tsx around GameCanvas) renders phase-specific loading text/UI per non-READY status and distinct error UI, GameCanvas.tsx/useCanvas.ts remain byte-for-byte unmodified" | Steps 7, 8, 11 | test_plan.md items 8, 9, 10 |
| "existing SSE-stream/entity-processing behavior in useSimulation.test.tsx continues to pass unmodified aside from initial-status assertion" (re-mapped per investigation.md's Ticket Staleness section: no SSE exists; this means the existing WS-based tests) | Steps 4, 5, 9 (no changes to entity-reduction/WS-open/reconnect logic) | Step 9's regression run of all pre-existing tests except the one superseded assertion |

## Known Constraints

These are stated, intentional facts about the resulting behavior — not defects to fix later:

1. **`READY` is transient, not sticky.** Once `fallbackPoll`'s next 500ms tick runs (line 302,
   independent `setInterval`, unaffected by this plan), it unconditionally calls
   `setStatus('RUNNING'|'PAUSED'|'STOPPED')` (lines 231-237), overwriting `READY`. This is the
   intended final steady state: `READY` is a one-time transient handoff marker signaling "first live
   delta received," and `RUNNING`/`PAUSED`/`STOPPED` remain the permanent steady-state statuses
   exactly as the ticket's own Scope text lists them ("plus existing RUNNING/PAUSED/STOPPED"). Step 7's
   `SimulationLoadingGate` is designed around this: it renders `children` for `RUNNING`/`PAUSED`/
   `STOPPED` too, not only literal `READY`, so `GameCanvas` does not flicker away when this overwrite
   happens.
2. **`fallbackPoll` can race ahead of the WS lifecycle and pre-empt `CONNECTING_LIVE`/`SYNCING`
   before `READY` is ever reached.** `setInterval(fallbackPoll, 500)` starts immediately after
   `connectWS()` is first invoked (line 217/302), independent of whether the WS handshake has
   completed. If the `/stats` REST call resolves before the WS `onopen` + first delta round-trip
   does, `fallbackPoll` can overwrite `CONNECTING_LIVE` or `SYNCING` directly with `RUNNING`/`PAUSED`/
   `STOPPED`, skipping `READY` entirely for that page load. This is accepted, not fixed, in this plan:
   fixing it would require changing `fallbackPoll`'s own write conditions (e.g. gating it on `status`
   already being `READY`-or-later), which is a `fallbackPoll` behavior change outside this ticket's
   stated scope ("this ticket only wires status transitions to it," not "rebuilds the connect
   sequence's ordering guarantees"). Harmless for the wrapper's rendering behavior (Known Constraint 1
   already covers `RUNNING`/`PAUSED`/`STOPPED` as "show `GameCanvas`" states) but worth knowing if a
   future ticket wants to guarantee `READY` is always visibly reached.
3. **`LOAD_ERROR` is terminal for the lifetime of the mount** — no auto-retry, no retry button, no
   code path clears `retryCountRef` short of a full page reload/remount. See Step 3.
4. **`scheduleReconnect()` remains permanently unbounded** — a WS drop after `READY` (or after
   `fallbackPoll` has already moved past it) retries every 2000ms forever, with no equivalent
   `LOAD_ERROR`-style visible failure state. See Step 5.

## Anti-Drift Notes

- Do not touch `GameCanvas.tsx` or `useCanvas.ts` in any way, including removing the now-dead
  `!mapData` branch (investigation.md Anti-Drift Hazards, Risk 3). Step 11's `git diff --stat` is the
  hard gate for this.
- Do not silently bound `scheduleReconnect()` "for consistency" with `loadInitial()`'s new bound — the
  decision to leave it unbounded is explicit and reasoned in Step 5, not an oversight to "complete."
- Do not forget `Header.tsx`'s `STATUS_COLORS` Record (Step 6) — this is the most likely accidental
  build break, since `Header.tsx` was not in the ticket's own Related Code Areas list.
- Do not let `SimulationLoadingGate` duplicate or patch `GameCanvas.tsx`'s internal `!mapData`
  branch — the new phase-aware text lives entirely in the new wrapper component (Step 7), rendered
  *before* `GameCanvas` mounts, never alongside it.
- Do not invent a new `SYNCING`/`READY` detection mechanism (e.g. a new WS message type or an
  `isFirstDelta` flag) — Step 4 reuses the existing `isDelta` shape-guard
  (`Array.isArray(data.changed) && Array.isArray(data.removed)`, `useSimulation.ts:156`) as the sole
  trigger, unconditionally on every qualifying message.
- Do not resurrect `EventSource`/SSE anywhere in new code or new tests — the transport is WebSocket
  only (ticket 6's prior work); the existing `'opens WebSocket to /api/v1/ws, not EventSource'` test
  is the regression guard.
- Do not gate `SimulationLoadingGate` on literal `status === 'READY'` — must allow
  `RUNNING`/`PAUSED`/`STOPPED` through too, per Known Constraint 1, or `GameCanvas` will flicker away
  500ms after first appearing.
