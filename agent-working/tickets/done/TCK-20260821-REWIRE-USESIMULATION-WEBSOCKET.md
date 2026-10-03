---
status: historical
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET
phase: done
date: 2026-08-21
tags: [websocket, engine]
---

# TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET

## Title
Rewire useSimulation.ts from SSE to the real /api/v1/ws WebSocket contract

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
useSimulation.ts was built against a backend contract (SSE transport, query-param-aware /state, generic control dispatch) that the real V2 backend never implements, so the renderer shows nothing. The author wants useSimulation.ts (only) swapped from EventSource to a real WebSocket client speaking the actual /api/v1/ws handshake, keeping the existing changed/removed reducer logic, and mapping pause/resume calls onto the two real existing control routes instead of a generic dispatcher.

## Scope
- Replace useSimulation.ts's EventSource('/api/v1/stream') usage with a real WebSocket client to /api/v1/ws
- Send the required {"type":"handshake","format":"json"|"msgpack"} message as the first outgoing message before processing any data; pick and document one format explicitly
- Keep existing changed/removed reducer logic unchanged, adapting it to consume the new {tick,changed,removed,events,snapshot_as_of_tick} delta shape
- Map pause/resume calls onto the two real existing routes: single POST /api/v1/control/pause, single POST /api/v1/control/resume -- remove the generic dispatcher
- On WS close/error, reconnect (mirroring the current onerror/setTimeout retry behavior)
- Rewrite frontend/src/test/useSimulation.test.tsx against a mocked WebSocket (both existing tests are written against the old EventSource/SSE contract and are not reusable as-is)

## Out of Scope
- GameCanvas.tsx and useCanvas.ts -- not modified by this ticket
- Any change to /speed or /clear_events call sites
- Building the state-machine loading UI (separate TCK-20260821-PHASED-LOADING-STATE-MACHINE ticket)

## Acceptance Criteria
- [x] hook opens WebSocket to /api/v1/ws (not EventSource/'/api/v1/stream'), sends handshake as first outgoing message before processing any data
- [x] changed/removed/tick/events reducer logic behaviorally unchanged (ported test assertions: entities.length, entities[0].id, aliveCount, tick)
- [x] pause maps to single POST /api/v1/control/pause, resume to single POST /api/v1/control/resume, no generic dispatcher introduced
- [x] on WS close/error, hook reconnects (mirrors current onerror/setTimeout retry)
- [x] GameCanvas.tsx and useCanvas.ts not modified (diff scope limited to useSimulation.ts + its test file)

## Related Tickets
- TCK-20260821-WS-ENTITY-DELTA-BROADCAST
- TCK-20260821-REST-MAP-STATIC-STATS
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- frontend/src/hooks/useSimulation.ts
- frontend/src/types/api.ts
- frontend/src/test/useSimulation.test.tsx
- src/api/ws/stream.py
- src/api/server.py
- frontend/src/components/GameCanvas.tsx
- frontend/src/hooks/useCanvas.ts

## Assumptions / Open Questions
- msgpack vs json handshake format choice is open -- this ticket should pick one explicitly and document why
- sendControl's current generic signature is used only for pause/resume today per scope, but call sites in GameCanvas.tsx/ControlPanel.tsx should be grepped before removing the generic path, even though those files aren't edited
- **Cross-epic sequencing note (2026-08-23), found while reconciling this batch against `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION`'s child tickets**: `TCK-20260822-DURABLE-SELECTION-STATE` and `TCK-20260822-ENTITY-LIST-SEARCH-RANK` (a separate epic, unrelated to this one in scope) both also list `frontend/src/hooks/useSimulation.ts` under their own Related Code Areas -- one extracts `selectedEntityId` state out of it into a shared model, the other reads/diffs its data for entity ranking. Neither of those tickets existed when this one was scoped. This ticket should land first: it rewrites `useSimulation.ts`'s internal transport and reducer shape (EventSource->WebSocket, old delta shape->new `{tick,changed,removed,events,snapshot_as_of_tick}` shape) wholesale, including a full rewrite of its test file -- any of that pair's work done against the pre-rewire hook would need re-doing against the post-rewire internals. Not a scope change to this ticket itself, just a recommended implementation order for whoever picks up either batch.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET/plan.md`'s 8 steps,
executed in the plan's Dependency Map order (Step 1 -> Steps 2/3/4 as one coherent edit -> Step 5 ->
Step 8 (build gate) -> Step 6 (tests) -> Step 7 (docs)):

- **Step 1** (`frontend/src/types/api.ts`): added `WireEntitySlim` immediately after the `EntitySlim`
  interface — `Omit<EntitySlim, 'state'|'tier'|'combat_target_id'|'loot_progress'|'loot_duration'>`
  plus those 5 fields optional, exactly as plan.md specifies. `EntitySlim` itself is untouched
  (confirmed via `git diff` — purely additive hunk).
- **Steps 2-4** (`frontend/src/hooks/useSimulation.ts`, same `useEffect` block, dependency
  `[mapData]`): replaced `EventSource('/api/v1/stream')` with `new WebSocket(`${wsBase()}/ws`)`
  (`wsBase()` derives an absolute `ws://`/`wss://` URL from `window.location`, since `WebSocket`
  cannot resolve a bare relative path the way `fetch` does). Handshake
  (`{"type":"handshake","format":"json"}`) is sent in `onopen`. `onmessage` branches on
  `Array.isArray(data.changed) && Array.isArray(data.removed)` to separate the initial
  full-state-shaped summary message from real per-tick deltas (a no-op for the former). For deltas,
  each `WireEntitySlim` in `data.changed` is explicitly defaulted into a fully-populated
  `EntitySlim` (`state ?? ''`, `tier ?? 0`, `combat_target_id ?? null`, `loot_progress ?? 0`,
  `loot_duration ?? 0`) before being stored into `entities` state, matching plan.md's Step 3 code
  block verbatim. `onclose`/`onerror` both call a shared `scheduleReconnect()` (guarded against
  double-scheduling) that reconnects after 2000ms, mirroring the old `onerror`/`setTimeout` pattern;
  the effect's cleanup now also clears any in-flight `reconnectTimeout`.
- **Step 5** (`sendControl`): replaced the generic `fetch(`${API_BASE}/control/${action}`, ...)`
  dispatcher with an explicit `if (action === 'pause') ... else if (action === 'resume') ... else
  console.error(...)` branch — both real URLs are literal strings, no template interpolation of
  `action` anywhere. `setSpeed`/`clearEvents` were not touched (confirmed unchanged in the diff).
- **Step 8** (build gate, run before Step 6 per the plan's explicit execution-order override):
  `npm install` (no `node_modules` existed in this worktree) then `npm run build` (`tsc -b && vite
  build`) — **exit 0, zero TypeScript errors**, on the first attempt, since Step 1/3 followed
  plan.md's `WireEntitySlim`/explicit-defaulting design precisely rather than the two previously-
  rejected approaches (optional fields directly on `EntitySlim`, or a runtime-only default with no
  type-level fix). Re-ran after Step 6's test rewrite too — still exit 0.
- **Step 6** (`frontend/src/test/useSimulation.test.tsx`): fully rewritten against a `MockWebSocket`
  class assigned to `globalThis.WebSocket` (same spyable-constructor pattern the old
  `MockEventSource` used). All 8 `test_plan.md` tests written, plus the pre-existing
  "initializes with default values" test carried forward unchanged. `mockFetch` was extended with a
  path-aware default (`/map`, `/static`, `/manifest`, else the stats shape) since `loadInitial()`
  now awaits 3 fetches, not 2. `cd frontend && npx vitest run src/test/useSimulation.test.tsx` -> 10
  passed, 0 failed.
  - One deviation from a literal reading of plan.md's test-order assumption: the two reconnect tests
    (`vi.useFakeTimers()`) needed to enable fake timers *after* `renderConnectedHook()`'s internal
    `waitFor` calls resolve, not before — `@testing-library/react`'s `waitFor` polls via real
    timers, so enabling fake timers first hung both tests for the full 5000ms `testTimeout`. This is
    a test-harness ordering detail, not a behavioral deviation from the plan's reconnect design
    (still `vi.advanceTimersByTime(2000)` against the same `scheduleReconnect`/2000ms code path).
- **Step 7** (`docs/engine/contracts/frontend.md`): rewrote §1's transport bullet, §2B (renamed
  "Delta Sync (SSE)" -> "Delta Sync (WebSocket)") to describe the real handshake, initial-message
  shape guard, defaulting behavior, and reconnect timing, and appended a note to the top-of-file
  known-gap callout marking the frontend half closed while re-disclosing the two live-verification
  blockers. §4's Control Bar line now notes only pause/resume map to real routes. Did not touch
  `docs/parity_ledger/infrastructure.yaml` (no entry required — zero backend changes).

No conflicts with the plan were found; no architectural issues were encountered. Both disclosed
blockers (fail-closed API-key auth with zero frontend key-wiring; Vite dev proxy missing
`ws: true`) were left unfixed, as instructed — they make live E2E verification against a real
running backend impossible in this environment, but do not block this ticket's own AC or test
gates.

## Test Summary

- `cd frontend && npx vitest run src/test/useSimulation.test.tsx` — **10 passed, 0 failed**
  (the 8 tests named in `test_plan.md` plus the pre-existing "initializes with default values"
  test). Exercises the hook only against a mocked `globalThis.WebSocket` and mocked
  `globalThis.fetch` — no real socket or real HTTP call is made.
- `cd frontend && npm run build` (`tsc -b && vite build`) — **exit 0, zero TypeScript errors**, run
  twice (once immediately after Steps 1-5 per the plan's required execution order, once again after
  Step 6's test rewrite). This is the gate that 4 architecture-review rounds were spent getting
  right (the `WireEntitySlim`/explicit-defaulting design in Steps 1/3).
- No backend pytest command applies — this ticket makes zero Python/backend changes (confirmed by
  `git diff --stat`: only `frontend/src/hooks/useSimulation.ts`, `frontend/src/types/api.ts`,
  `frontend/src/test/useSimulation.test.tsx`, and `docs/engine/contracts/frontend.md` changed,
  besides the auto-written `agent-monitoring/tools.jsonl`).
- **Honest scope disclosure**: live end-to-end verification (a real `npm run dev` session
  connecting to a real running `python -m src serve` backend and rendering live entities) is **not
  possible in this environment**, for two real, disclosed, out-of-scope blockers: (1) fail-closed
  API-key auth (`TCK-20260823-HTTP-API-KEY-AUTH`) gates every route this hook calls, and the
  frontend has zero API-key wiring anywhere; (2) `frontend/vite.config.ts`'s dev proxy does not set
  `ws: true`, so even with a key the dev proxy would not forward the WebSocket upgrade. This
  ticket's Verify phase is scoped to what CAN be automated — the mocked-WebSocket vitest suite and
  `npm run build` — not live connectivity, per plan.md's own "Known, Disclosed Gaps to Live
  Verification" section.
- `git diff --stat -- frontend/src/hooks/useCanvas.ts frontend/src/components/GameCanvas.tsx` —
  empty (zero changes to either file, confirming AC 5).
- `grep -n 'control/\${' frontend/src/hooks/useSimulation.ts` — no matches (confirms the generic
  dispatcher pattern is genuinely gone).

## Files Changed

- `frontend/src/types/api.ts` — added `WireEntitySlim` type (additive only; `EntitySlim` unchanged)
- `frontend/src/hooks/useSimulation.ts` — EventSource -> WebSocket transport rewire, new
  handshake/onmessage-shape-guard/reconnect logic, explicit pause/resume `sendControl` branch
- `frontend/src/test/useSimulation.test.tsx` — fully rewritten against a mocked `WebSocket`
- `docs/engine/contracts/frontend.md` — §1, §2B, §4, and the top-of-file known-gap callout rewritten
  to describe the real WebSocket contract and the two remaining disclosed live-verification
  blockers
- `staging_artifacts/TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET/plan.md` — added a Deviations
  section (test-timer-ordering detail only; no design/architecture deviation)
- `tickets/inprogress/TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET.md` — this file (Implementation
  Notes, Test Summary, Files Changed, Completion Summary, Acceptance Criteria checkboxes, Status)

No backend/Python files were changed (`src/api/ws/stream.py`, `src/api/server.py` were read-only
references, per the plan). `frontend/src/hooks/useCanvas.ts` and
`frontend/src/components/GameCanvas.tsx` were not modified (confirmed by `git diff --stat`).

## Completion Summary

Rewired `useSimulation.ts` off the nonexistent `EventSource('/api/v1/stream')` onto the real
`/api/v1/ws` WebSocket contract: it now sends the `{"type":"handshake","format":"json"}` handshake
in `onopen`, distinguishes the server's initial full-state summary message from real per-tick
deltas by shape (`Array.isArray(data.changed) && Array.isArray(data.removed)`) rather than message
order, ports the existing `changed`/`removed`/`tick`/`events` reducer unchanged for the delta path
(explicitly defaulting the 5 fields `present_entity_slim` never sends via a new `WireEntitySlim`
wire-parsing type, while `EntitySlim` itself stays fully required and byte-for-byte unchanged), and
reconnects after 2000ms on `onclose`/`onerror`. `sendControl` now branches explicitly to the two
real routes (`/control/pause`, `/control/resume`) with no generic dispatcher. The test file was
rewritten end-to-end against a mocked `WebSocket` (10/10 passing), and `npm run build` passes with
zero TypeScript errors — the critical gate 4 architecture-review rounds were spent getting right.
`GameCanvas.tsx`/`useCanvas.ts` remain completely unmodified. Two real, disclosed blockers (no
frontend API-key wiring against fail-closed backend auth; Vite dev proxy missing `ws: true`) make
live end-to-end verification against a running backend impossible in this environment — this was
not fixed here, per the plan's explicit scope guard, and is honestly reported in Test Summary above
rather than silently treated as "verified."
