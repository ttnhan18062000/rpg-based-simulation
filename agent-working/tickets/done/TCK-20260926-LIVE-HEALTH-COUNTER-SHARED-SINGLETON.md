---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260926-LIVE-HEALTH-COUNTER-SHARED-SINGLETON
phase: done
date: 2026-09-26
tags: [testing, observability]
---

# TCK-20260926-LIVE-HEALTH-COUNTER-SHARED-SINGLETON

## Title
Live health counter test shares a mutable singleton with live engine telemetry, and regression_policy's stated reason does not cover its observed failure

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
On PR #248, `tests/api/test_live_health_api.py::test_live_health_api_suite` failed in CI with
`assert 0 == 1`. The failure was initially classified as environment noise under
`docs/testing/regression_policy.md`'s "Live observability tests" soft row. That classification does
not hold, and the row's stated reason is what made it look like it did.

Established by assertion-order derivation: `assert 0 == 1` can only be line 91
(`counters["navigation_stuck_count"] == 1`) or line 92 (`counters["hard_law_violation_count"] == 1`).
Every assertion before those is a status-code assertion, and all of them must have passed to reach
line 91 — L33 health `== 200`, L45 UI `== 200`, L54/L60 redirects, **L74 and L84 both event
publishes `== 200`**, L88 health re-fetch `== 200`. So the server was running, serving, and
authenticating, and it accepted both anomaly publishes, and then the counter read back zero.

That is not the case the policy row describes ("Require a running server; environment-dependent;
failures indicate deployment issues, not code regressions"). The row's only carve-out is 401/403,
and this is correctly not that — but a failure outside the carve-out is not automatically the
generic case. The row itself records that `TCK-20260823-LIVE-TEST-API-KEY-AUTH` already fixed this
file set once "after two prior tickets misdiagnosed the same failures as this row's generic
environment-dependent case." This is a third approach to that trap from a new angle.

The specific cause of this failure is NOT established, and this ticket must not claim otherwise.
The exact failing line number is unrecoverable: the logs and annotations endpoints were TLS-blocked,
`gh run rerun --failed` reuses the run ID, and the original attempt was superseded before it could
be read.

Mechanisms investigated and RULED OUT by reading the code:
- Async/queued publish. `/api/v1/test/publish_event` → `LiveEventPublisher.publish()` →
  `LiveAnomalyCounter.push()` is fully synchronous, same call stack, no queue, no thread hop, and no
  `EventRecorder` in this path (`EventRecorder`'s batch flush is a separate on-disk-persistence
  subsystem). When the endpoint returns 200 the increment has already happened.
- Multi-worker singleton fragmentation. `uvicorn.run(app, host=..., port=...)` in
  `src/cli/entry.py` passes no `workers=` — single process.

Mechanism CONFIRMED REAL, but which probably does not explain this specific failure:
`V2EngineManager.start()` runs in the FastAPI `lifespan` hook, so a real simulation ticks in a
background thread from server boot (`_run_loop` → `kernel.tick_once()`). Under the default
`local-dev` profile the stream backend is `InProcessEventStreamAdapter`, which forwards every
recorded tick event into the *same* `LiveEventPublisher`/`LiveAnomalyCounter` singleton the test's
manual injections use. `LiveAnomalyCounter.push()` resets ALL counters whenever `event.run_id`
differs from `self.current_run_id`; real engine events carry the kernel's run_id, the test's
injected events carry `run_id=None`. A real engine event arriving between the test's second publish
and its health re-fetch would zero the counters — matching the symptom exactly. The reason this
probably isn't the explanation: the reset fires only on a run_id *change*, which for one unchanging
kernel run happens once, on the first real event, almost certainly during the test's own 4-second
startup sleep.

The hazard is worth fixing whether or not it caused this failure: a test asserting exact counter
values against a singleton that live engine telemetry concurrently writes to, and which
self-resets on a run_id change, is not a test that can hold its meaning over time.

## Scope
- Isolate the test's counter assertions from live engine telemetry, so the assertion measures only
  what the test injected. Prefer isolating the test's view of the counter over weakening the
  assertion.
- Correct `docs/testing/regression_policy.md`'s "Live observability tests" row so its stated reason
  matches what the row actually covers. A counter-value failure occurring after successful 200s is
  not a "requires a running server" failure and must not read as one.
- Record the run_id-reset hazard where a future reader of either the test or the counter will meet
  it.

## Out of Scope
- Changing `LiveAnomalyCounter`'s reset-on-run_id-change semantics as production behavior. It may
  well be correct for the live dashboard; this ticket is about a test observing a shared singleton,
  not about redesigning the counter.
- Retroactively determining this specific CI failure's cause. The evidence is gone; do not
  manufacture a conclusion to close the ticket.
- Weakening or skipping the assertion to make CI pass. Explicitly forbidden — see CLAUDE.md.

## Acceptance Criteria
1. The test's counter assertions cannot be perturbed by live engine telemetry, demonstrated rather
   than asserted — e.g. the isolation holds with the background engine actively ticking.
2. The assertions remain exact-value (`== 1`), not loosened to `>= 1` or removed. If exact values
   prove genuinely unachievable, that finding is reported for a decision rather than worked around.
3. `docs/testing/regression_policy.md`'s Live observability row states a reason that matches the
   failures legitimately filed under it, and distinguishes the counter-failure case from the
   server-absent case.
4. The run_id-reset interaction is documented at the point of use.
5. Existing `tests/api/` tests pass unchanged, or any change is justified in Implementation Notes.
6. No test is edited to make a gate pass; the substance is fixed.

## Related Tickets
- `TCK-20260823-LIVE-TEST-API-KEY-AUTH` — fixed this same file set after two prior misdiagnoses
  under the same policy row. Direct precedent for the failure-classification half of this ticket.
- `TCK-20260926-HOTFIX-AGENT-MONITORING-SCOPE-BOUNDARY-DOC` — the PR (#248) whose CI surfaced this.
  Unrelated in substance; the failure was not caused by that change.

## Related Docs
- `docs/testing/regression_policy.md` — the row being corrected.
- `docs/architecture/http_api_key_authentication.md` — referenced by the row's 401/403 carve-out.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tests/api/test_live_health_api.py` (L74–L94, the publish-then-assert window)
- `src/cli/entry.py` (`uvicorn.run`, no `workers=`; `V2EngineManager.start()` in `lifespan`)
- The `LiveEventPublisher` / `LiveAnomalyCounter` singleton and
  `InProcessEventStreamAdapter` — confirm exact module paths during investigation rather than
  trusting this list, per the repeated "file list was incomplete" finding in this subsystem.

## Assumptions / Open Questions
- **Which isolation mechanism.** — **RESOLVED, see plan.md**: `SIM_STREAM_BACKEND=null` in the
  test's own subprocess env. This works because the test's manual anomaly injection
  (`POST /test/publish_event` → `LiveEventPublisher.publish()` directly) and the live engine's own
  telemetry (`EventRecorder` → `get_event_stream_adapter().publish()`) are two genuinely separate
  code paths that only converge inside `LiveAnomalyCounter`. Redirecting the stream-adapter path to
  `NullEventStreamAdapter` severs the engine's telemetry without touching the test's own injection
  path or the counter's production reset semantics — both explicitly Out of Scope.
- Whether `tests/api/test_live_observability_status.py`, the row's other named file, has the same
  exposure. — **RESOLVED: checked by reading the file in full.** Its assertions are enum-membership
  and pause/resume state-transition checks; it never asserts an exact `LiveAnomalyCounter` value and
  does not share this exposure. No change made there.
- The specific cause of the observed `assert 0 == 1` remains undetermined and may stay that way. —
  Confirmed: not re-investigated further here; this ticket fixes the test-isolation hazard the
  original triage found real regardless of whether it explains that one CI failure.

## Implementation Notes
Full reasoning in `staging_artifacts/TCK-20260926-LIVE-HEALTH-COUNTER-SHARED-SINGLETON/
{investigation,plan}.md`. Confirmed by direct code reading, not assumed: `publish_test_event`
(`src/api/server.py`) calls `LiveEventPublisher.get_instance().publish(event)` directly, bypassing
`get_event_stream_adapter()` entirely — so the `SIM_STREAM_BACKEND=null` env var change only ever
touches the live engine's own telemetry, never the test's own injected anomalies. The background
engine (`V2EngineManager`, started in the FastAPI `lifespan` hook) keeps running unmodified; only
its event stream now lands on a no-op sink. Confirmed AC5 (no regression) against the full
`tests/api/` suite plus the counter's own unit tests, not just the two directly-named files.

## Test Summary
- `python3 -m pytest tests/api/test_live_health_api.py -v` — **1 passed**, 5x in a row (repeat run,
  not a single lucky pass) to build confidence against the original race shape.
- `python3 -m pytest tests/api/test_live_observability_status.py -v` — **2 passed** (unmodified;
  confirms this ticket's change doesn't touch its exposure).
- Full regression: `python3 -m pytest tests/api/ tests/unit/observability/
  test_live_anomaly_counter.py -q -m "not slow and not extra_slow"` — **154 passed**, 0 failed.
- `docs/testing/regression_policy.md`'s row change verified by re-reading it against the three
  failure shapes it now names (server-absent, 401/403, counter-value-after-200s) — no test, per
  test_plan.md (documentation-only change).

## Files Changed
- `tests/api/test_live_health_api.py` — `SIM_STREAM_BACKEND=null` env var added, with an inline
  comment explaining why; no assertion changed.
- `src/observability/live/anomaly_counter.py` — docstring added to `push()` documenting the shared-
  singleton/reset-on-run_id-change hazard at its point of use; no behavior changed.
- `docs/testing/regression_policy.md` — "Live observability tests" row rewritten to name three
  failure shapes instead of one generic case plus a single carve-out.
- `staging_artifacts/TCK-20260926-LIVE-HEALTH-COUNTER-SHARED-SINGLETON/
  {investigation,plan,test_plan}.md` (new).
- `docs/REGISTRY.yaml` — regenerated as part of ticket close (routine, unconditional per the
  Finalize rule).

## Completion Summary
Isolated `test_live_health_api_suite`'s exact-value counter assertions from the live-ticking
engine's own telemetry, both of which shared one process-wide `LiveAnomalyCounter` singleton that
self-resets on a run_id change. Fixed by redirecting the engine's own event stream to a no-op sink
(`SIM_STREAM_BACKEND=null`) rather than weakening the assertions or the counter's production
semantics — the test's own manual anomaly injection never touched that code path to begin with, so
the fix has zero effect on what the test actually verifies. Documented the hazard at both points of
use: the test's own env-var comment, and a new docstring on `LiveAnomalyCounter.push()` for any
future caller. Corrected `docs/testing/regression_policy.md`'s row, which previously implied only
one failure shape (server-absent) plus one carve-out (401/403) — a counter-value failure after every
status-code assertion already passed is a third, distinct shape, and the row now says so explicitly
so it isn't misdiagnosed a fourth time.

Did not determine the original CI failure's specific cause — that evidence is gone, and this ticket
never claimed it would recover it. Full `tests/api/` and the counter's own unit-test suite pass
(154 passed, 0 failed). No known material gap.
