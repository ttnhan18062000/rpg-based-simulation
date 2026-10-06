---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261006-USE-SIMULATION-CONNECTING-LIVE-TEST-READS-STATE-BEFORE-FLUSH
phase: done
date: 2026-10-06
tags: [testing, investigation]
---

# TCK-20261006-USE-SIMULATION-CONNECTING-LIVE-TEST-READS-STATE-BEFORE-FLUSH

## Title
`useSimulation` "transitions to CONNECTING_LIVE" test reads the status before React has flushed it

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Reported by `test-architecture-reviewer` (relayed by hand): `Tests` run 37451854131 on `main` (#375, which changed no frontend files) failed the `Frontend` job: `frontend/src/test/useSimulation.test.tsx` "transitions to CONNECTING_LIVE once map/static/manifest load and the WS connection attempt begins" expected `CONNECTING_LIVE` and got `FETCHING_WORLD_DATA` (15 ms). It was the only `Frontend` failure in about 14 recent main runs. Triage per `docs/testing/regression_policy.md` §6.1, with the failure rate measured before any quarantine. The CI run itself was not re-read by the implementer.

## Scope
Reproduce locally with repeats, find the cause, measure the rate, fix the test if the cause is in the test.

## Out of Scope
Quarantine (not applied: the rate was measured and the root cause is a one-line test fix), any change to `useSimulation.ts`, rerunning the main job (it would re-trigger the 2 h slow job), and the three pre-existing `no-explicit-any` ESLint errors in this file (they fail identically on `origin/main`).

## Acceptance Criteria
- [x] The failure reproduces locally and its rate is measured.
- [x] The cause is identified from the code, not guessed.
- [x] The test no longer shows the failure in a comparable repeat run (0 of 60 file runs against 4 of 60).
- [x] The frontend test file passes (19 of 19).

## Related Tickets
- TCK-20260821-PHASED-LOADING-STATE-MACHINE (the status states under test)

## Related Docs
- `docs/testing/regression_policy.md` §6.1 (bounded quarantine; not applied)

## Related Stored Artifacts
- None. The measurement scripts were scratch files and are described below.

## Related Code Areas
- `frontend/src/test/useSimulation.test.tsx`, `frontend/src/hooks/useSimulation.ts` (read only)

## Assumptions / Open Questions
- The CI failure is the same race: same assertion, same two statuses. This is inferred from the signature, not checked against that run's log.

## Implementation Notes
**Cause (read from the code):** in `useSimulation.ts`, `connectWS()` calls `setStatus('CONNECTING_LIVE')` and then `new WebSocket(...)` from an async continuation (after the `/map`, `/static` and `/manifest` fetches resolve), outside `act()`. The test waits for the `WebSocket` mock instance to exist (`waitFor(... mock.instances.length > 0)`) and then reads `result.current.status` synchronously. The mock instance can exist before React has flushed the status update, so the test sometimes still sees `FETCHING_WORLD_DATA`. The test waited on a side effect and read the state, instead of waiting on the state.

**Measured failure rate (local, unloaded, vitest 4, same machine):**
- Real test file, 100 separate vitest processes: 1 failure of the CONNECTING_LIVE test (run 88). Other 99 runs passed.
- Scratch probe with N copies of the same test (each with the same `beforeEach`/`afterEach`): 2 of 10 file runs failed at N≥300 (both at test index #1, early in the file); 3 file runs of N=2000 (6000 test executions) had 0 failures. The race fires early in a process (cold start), not uniformly.
- A/B on the probe at N=20 (60 file runs each): current assertion 4 of 60 file runs failed (6.7%); with `await waitFor(() => expect(result.current.status).toBe('CONNECTING_LIVE'))` 0 of 60. With the same rate the chance of 0 of 60 is about 1.6%, so the fix is supported but not proven by this sample alone.
- CI: 1 failure in about 14 recent main runs (the reviewer's count).

**Fix:** the final assertion of that test is now `await waitFor(...)` on the status. The other status assertions in the file follow an `act()` or fake timers and are not affected. No quarantine (§6.1) was applied: the root cause is fixed in the test itself.

## Test Summary
`npx vitest run src/test/useSimulation.test.tsx`: 19 passed. The measurements above are the repeat runs. ESLint: the same 3 pre-existing `no-explicit-any` errors before and after.

## Files Changed
- `frontend/src/test/useSimulation.test.tsx`

## Completion Summary
The flaky `Frontend` failure is a race in the test: it read `result.current.status` right after the `WebSocket` mock appeared, before React flushed `CONNECTING_LIVE`. The test now waits on the status. Measured: about 1% of real file runs and 6.7% of early-in-process runs failed before the change, 0 of 60 after in the A/B run. Whether the CI failure was this race rests on its identical signature, not on the CI log.
