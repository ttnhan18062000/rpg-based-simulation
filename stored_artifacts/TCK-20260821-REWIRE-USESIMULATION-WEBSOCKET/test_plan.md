---
status: historical
layer: frontend
authority: P2
audience: agent
ticket_id: TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET
artifact_type: test_plan
tags: [websocket, engine]
---

# Test Plan — TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET

## What Can and Cannot Be Automated-Tested Here (read first)

**Frontend test infrastructure is real and already used, not absent.** `frontend/package.json` has
`vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, and
`jsdom` as working devDependencies; `frontend/vite.config.ts`'s `test` block and
`frontend/src/test/setup.ts` are already configured; `frontend/src/test/useSimulation.test.tsx`
already exercises this exact hook today (against the old SSE contract) via `renderHook` +
mocked `globalThis.fetch`/`globalThis.EventSource`. jsdom provides a real `WebSocket` global too, so
the same mocking pattern (assign a hand-rolled mock class to `globalThis.WebSocket`, drive its
`onopen`/`onmessage`/`onclose`/`onerror` handlers directly via `act()`) is directly portable from the
existing `MockEventSource` pattern. **This CAN be fully unit/integration-tested at the hook level.**

**What CANNOT be automated-tested in this codebase today:**
- **No Playwright/e2e/browser-automation config exists anywhere under `frontend/`.** There is no way
  to automatedly verify the hook actually connects to a real running backend process, receives a
  real WS upgrade, or renders real pixels — only vitest+jsdom's simulated/mocked WebSocket.
- **No automated verification of live-server end-to-end connectivity is possible even manually
  without further work**: per investigation.md's Risk 1, the real backend's `/api/v1/ws` and every
  REST route this hook calls are gated by fail-closed API-key auth
  (`TCK-20260823-HTTP-API-KEY-AUTH`), and the frontend has no key-wiring anywhere. A real dev-server
  smoke test (`npm run dev` + a live `python -m src serve`) would 401/1008 today regardless of this
  ticket's own correctness, and separately, `frontend/vite.config.ts`'s dev proxy lacks `ws: true`
  (Risk 2), so even with a key it would not proxy the WS upgrade in dev. **Neither gap is in this
  ticket's scope to fix** — disclosed here so "tests pass" is never conflated with "verified against
  a live server," which is not achievable in this environment as configured today.
- `loadInitial()`'s `Promise.all` fetch wiring itself has the same disclosed gap
  `TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT` already noted: no existing test harness exercises it at
  the "does the real network request actually get made with the right method/headers" level beyond
  what `mockFetch` assertions can verify (URL/call-count, not real HTTP semantics).

## Regression Surface

**Frontend (unit/integration, vitest+jsdom):**
- `frontend/src/test/useSimulation.test.tsx` — being rewritten per this ticket's own Scope (both
  existing tests are SSE-shaped and not reusable as-is). The "regression" here is the *behavioral*
  assertions being carried forward, not the file's literal contents: `entities.length`,
  `entities[0].id`, `aliveCount`, `tick` must still be correctly derived from a
  `changed`/`removed`-shaped payload after the rewire.
- No other frontend test file imports or exercises `useSimulation.ts`, `GameCanvas.tsx`, or
  `useCanvas.ts` — confirmed by directory listing of `frontend/src/test/` (exactly two files:
  `useSimulation.test.tsx`, `setup.ts`). Blast radius for regression purposes is this one file.

**Backend:** None. This ticket makes zero Python source changes (Scope is
`frontend/src/hooks/useSimulation.ts` + `frontend/src/types/api.ts` + its test file only). No
backend pytest command is required for this ticket's own verification. If a future diff for this
ticket accidentally touches any backend file, that is itself a scope violation to flag, not a
regression surface to test around — but as a defensive minimum in that case, re-run
`tests/unit/api/ tests/api/test_ws_protocol.py tests/api/test_manifest_api.py
tests/architecture/test_api_read_model_guard.py` (the suites covering `INFRA-386`/`384`/`385`) to
confirm the backend contract this hook depends on is unchanged.

## New Tests Required

All new tests live in `frontend/src/test/useSimulation.test.tsx` (integration-level, `renderHook` +
mocked `globalThis.WebSocket`/`globalThis.fetch`), category: unit/integration (no architecture-guard
tooling exists for frontend in this repo — see note in Anti-Drift Test Guards for the closest
available substitute).

1. **`sends handshake as the first outgoing message before processing any data`**
   Category: integration. Verifies: on hook mount (after `loadInitial()` resolves), a `WebSocket` is
   constructed pointing at `/api/v1/ws` (not `/api/v1/stream`), and the very first call to the mock
   socket's `send()` is `JSON.stringify({type:"handshake", format:"json"})` (or the chosen format) —
   asserted as the first call, not merely "was called at some point." Covers AC 1.

2. **`opens WebSocket to /api/v1/ws, not EventSource`**
   Category: integration. Verifies: `globalThis.EventSource` (if still present/mocked) is never
   constructed; `globalThis.WebSocket` mock's constructor URL argument resolves to `/api/v1/ws`
   (absolute `ws://`/`wss://` origin-qualified, given `WebSocket` — unlike `fetch` — cannot resolve a
   bare relative path the way the browser resolves relative REST URLs). Covers AC 1.

3. **`ignores/threads the initial full-state message distinctly from delta messages`**
   Category: integration, new (no old-SSE precedent — see investigation.md Risk 5). Verifies: the
   first message received after the handshake (shaped like `manager.get_state()`'s full-state
   payload, not `{changed,removed}`) does not crash the reducer and does not corrupt subsequent delta
   processing — feed a full-state-shaped first message, then a real delta-shaped second message, and
   assert the delta's `entities`/`tick`/`aliveCount` are exactly what the second message implies (not
   polluted by the first).

4. **`reduces a real {tick,changed,removed,events,snapshot_as_of_tick,region_id} delta correctly`**
   Category: integration, ported assertions. Verifies: `entities.length`, `entities[0].id`,
   `aliveCount`, `tick` — the exact four assertions named in this ticket's AC — against a payload
   shaped exactly like the real `ReadModelCache.compute_tick_delta` + `stream_ws` output (including
   the always-`null` `region_id` and a `snapshot_as_of_tick` field, so the reducer is proven to
   ignore/tolerate the two fields it doesn't need rather than erroring on their presence). Covers AC
   2.

5. **`sendControl('pause') POSTs exactly to /api/v1/control/pause, sendControl('resume') POSTs
   exactly to /api/v1/control/resume`**
   Category: unit. Verifies: two separate calls, each asserted individually — `fetch` called with
   `/api/v1/control/pause` (POST) and, separately, `/api/v1/control/resume` (POST) — and that no call
   ever constructs a URL via string interpolation of an arbitrary action (i.e. assert the exact,
   literal URL string was used, not a template match). Covers AC 3.

6. **`sendControl with an unrecognized action ('start'/'step'/'reset') does not construct a generic
   /api/v1/control/{action} URL`**
   Category: unit, anti-drift-flavored. Verifies: calling `sendControl('start')` never results in a
   `fetch` call to any `/api/v1/control/start`-shaped URL (matches today's already-broken,
   already-silent behavior for these three actions — this test guards against a generic dispatcher
   being reintroduced to "fix" them, which the AC explicitly forbids). Covers AC 3 (the "no generic
   dispatcher introduced" half).

7. **`reconnects after WebSocket close`** and **`reconnects after WebSocket error`**
   Category: integration, ported behavior. Verifies: triggering the mock socket's `onclose`/`onerror`
   handler results in a new `WebSocket` construction after the same delay shape the old
   `onerror`/`setTimeout(connectStream, 2000)` used (assert via `vi.useFakeTimers()` +
   `vi.advanceTimersByTime(2000)`, not a real wait). Covers AC 4.

8. **`loadInitial still fetches /map, /static, /manifest via one Promise.all`**
   Category: integration, regression guard (protects ticket 2's prior work from being lost in this
   ticket's broad rewrite of the same file — not a new AC, but a real risk given the scope of this
   change). Verifies: all three fetches are in flight concurrently (not sequential awaits), matching
   the existing structural-only verification style `TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT`'s own
   Test Summary already used for this same constraint.

## Scoped Test Commands

**Frontend (the real scoped command for this ticket):**
```
cd frontend && npx vitest run src/test/useSimulation.test.tsx
```
Not: a bare `npx vitest run` (whole suite) — though today `useSimulation.test.tsx` is in practice the
only frontend test file that exists, so the distinction is currently moot; name it explicitly anyway
per this project's scoping convention, since a future ticket could add sibling test files this one
should not accidentally sweep in.

**Backend:** None applicable — see Regression Surface above. Do not run `pytest tests/` for this
ticket; there is no backend surface to scope a pytest command to.

## Anti-Drift Test Guards

- **Diff-scope check (manual/review-time, not a vitest assertion)**: confirm
  `frontend/src/components/GameCanvas.tsx` and `frontend/src/hooks/useCanvas.ts` have zero diff
  after implementation — the ticket's own AC 5 names this explicitly. No frontend architecture-guard
  tooling (e.g. an AST-import-scanner) exists in this repo the way
  `tests/architecture/test_api_read_model_guard.py` exists for the backend; this remains a
  git-diff-based check, not an automated test.
- **Grep guard**: `grep -n 'control/\${' frontend/src/hooks/useSimulation.ts` (or equivalent
  template-literal pattern for a dynamic control action) should return nothing after
  implementation — a lightweight, repeatable way to confirm the generic dispatcher is genuinely gone,
  complementing test 6 above.
- Test 3 above (initial full-state message handling) is itself an anti-drift guard against the most
  likely real bug in this rewire — silently reusing the delta reducer against the initial full-state
  payload — since nothing in the old SSE code or this ticket's AC wording calls this shape difference
  out explicitly.
- Test 8 above guards against this ticket's broad rewrite of `useSimulation.ts` silently dropping
  `TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT`'s `/manifest` fetch or `manifest` state.
- Confirm (via the same `mockFetch` assertions already used in the existing test file) that
  `setSpeed`/`clearEvents` still target `/api/v1/speed`/`/api/v1/clear_events` unchanged — cheap
  regression insurance that this ticket's `sendControl` rewrite didn't collaterally touch the two
  explicitly-Out-of-Scope sibling functions in the same file.
