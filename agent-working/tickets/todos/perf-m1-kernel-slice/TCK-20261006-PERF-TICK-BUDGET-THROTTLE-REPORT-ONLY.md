---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY
phase: open
date: 2026-10-06
tags: [performance, determinism, engine, testing]
---

# TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY

## Title
The kernel's wall-clock tick-budget checks report overruns instead of dropping results or forcing DEGRADED (PERF-D1 inputs 2 and 3)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Released by the owner on 2026-10-06 (roadmap gate item 6). This ticket supersedes rpg's
`TCK-20261005-TICK-BUDGET-THROTTLE-MAKES-NON-AUDIT-RUNS-WALL-CLOCK-DEPENDENT`. That ticket lives on an
unmerged rpg branch, and rpg closes it as superseded. Its evidence is cited here.

PERF-D1 (owner-approved 2026-10-03, `docs/engine/deterministic_execution.md`, "Canonical contract")
already decides the behaviour. Under the Canonical contract the cutoff is driven by a work-unit budget
or is off. Under Live, any decision that changes what is computed must be recorded in a control trace,
and none exists yet. So report-only is the only behaviour that satisfies both contracts today.

Live code on `main` (2026-10-06):

- **Mid-tick throttle, `src/engine/kernel.py` about lines 618-640** (`_phase_resolution`). Every 10
  results it compares elapsed wall-clock time with `profile.max_tick_budget_ms`. Outside `audit_mode`,
  once over budget, it drops the remaining results, calls `record_dropped_work(n)`, and calls
  `self._governor.force_mode(RuntimeMode.DEGRADED, ...)`. This is the path that changes outcomes.
- **End-of-tick check, about lines 463-485.** After tick 5, if `_final_compute_ms` is over
  `min(hard_cap, max(20, 2 * last tick_compute_ms))`, it calls `record_dropped_work(9999)` and routes
  a watchdog alert. The `9999` is a sentinel, not dropped work. Only telemetry reads it
  (`engine_manager`, the live snapshot, Prometheus, `observability.py`), and the governor does not
  read `dropped_work_delta`.

Evidence (from the rpg ticket): `frontier_living_world`, same seed, 8 vs 10 deaths at tick 500 with
`audit_mode` off. `generated_frontier_3_42` is stable. With `audit_mode` on, the runs repeated exactly.

**Not closed here:** PERF-D1 input 1. The governor still chooses `RuntimeMode` from measured
`tick_compute_ms` (`src/engine/governor.py` about lines 78-105). Runs with `audit_mode` off stay
host-dependent through the governor. That half waits for the full no-touch window.

## Scope
1. **Mid-tick throttle:** stop dropping results and stop calling `force_mode(DEGRADED)`. Detect the
   overrun at the same point (elapsed time past `max_tick_budget_ms`), record it once per tick as a
   typed signal (step 3), log it, and keep processing every result.
2. **End-of-tick check:** stop calling `record_dropped_work(9999)`. Keep the watchdog alert. Record
   the overrun as the same typed signal. After this, `dropped_work` counts only work the scheduler
   actually shed (`_phase_scheduling`).
3. **Typed signal:** add a budget-overrun record readable from `RuntimeStatus` and the signals the
   governor history stores (for example `budget_overrun_ms: float` and a per-run counter). Name it as
   telemetry. It must not feed any governor decision or any value in `AuthoritativeState` (PERF-D1
   amendment A1). Surface it wherever `dropped_work_delta` is surfaced today, if that is a small
   change. Otherwise record it as a follow-up.
4. **Tests that relied on the old behaviour.** Run each one and fix it to test what it claims, not the
   old side effect:
   - `tests/integration/world/test_camp_raid_targeting.py` (rpg's R3 ask): it must reach `DEGRADED`
     explicitly, through the governor (patched timings, as in `test_milestone_b_closure.py`) or a test
     seam, and **assert that it did**. Otherwise it passes vacuously under `NORMAL` and stops covering
     `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`. rpg-planner reviews this change.
   - `tests/integration/kernel/test_work_debt_stays_empty_in_production.py`, around line 80: the
     precondition `total_dropped_work > 0` holds only if the scheduler still sheds under the
     governor's `DEGRADED`. If it no longer holds, drive the shedding through the governor, and do not
     weaken the precondition.
   - `tests/integration/kernel/test_milestone_b_closure.py`, around line 80: confirm the governor
     (100 ms and 150 ms thresholds) drives `DEGRADED` there, not the throttle.
   - Certification tests with `max_tick_budget_ms=10.0` (`test_allowed_failure_truth.py`,
     `test_envelope_violations.py`, `test_harness_contract.py`, `test_resilience_recovery.py`): check
     whether each asserts dropped work or `DEGRADED`, and fix any that depended on the throttle.
   - Grep for other readers of the sentinel or the throttle, and check each one:
     `tests/unit/engine/test_resource_budget_gate.py`, `tests/unit/api/test_engine_manager.py`,
     `tests/unit/observability/test_obs_backpressure.py`,
     `tests/integration/test_observatory_stream_outage.py`, `tests/unit/core/test_watchdog.py`.
5. **Regression test:** with `audit_mode=False` and a forced overrun (patched clock), a tick processes
   every result, the mode is not forced to `DEGRADED`, and the overrun signal is recorded. The test
   must fail on today's `main`. Add a determinism test too, if one fits in the CI budget: two runs of
   a short scenario with an injected overrun give the same canonical hash at every tick.
6. **Docs and parity:**
   - `docs/engine/deterministic_execution.md`: inputs 2 and 3 move from "breaks today" to "report-only
     since this ticket".
   - The code comment at the throttle that calls it a "known, still-deferred determinism issue".
   - `docs/guidelines/intentional_divergences.md`: an entry for the behaviour change (slow hosts no
     longer shed work mid-tick), class `Stabilized` or `Bug Fix`.
   - A parity-ledger entry in `docs/parity_ledger/infrastructure.yaml`, with `test_path` set to the
     regression test.
7. **Wall-clock inventory:** regenerate it with the tool if the read sites move
   (`tools/perf/wall_clock_inventory.py`, see `rpg_core_handoff.md` Ask 2). Never edit it by hand.

## Out of Scope
- The governor's `tick_compute_ms` input (PERF-D1 input 1) and any `governor.py` change. They wait for
  the full window.
- A work-unit budget for the cutoff. Add one only if a measurement shows it is needed.
- A Live control trace.
- Frame pacing (`time.sleep` to the target tick time). It sets wall time, not outcomes.
- `src/core/state.py`, `src/engine/apply.py`, `src/engine/pipeline.py` (still gated).
- The salience coupling (Lane A, rebases on this batch).
- Lifting the CI skips in `test_long_run_stability.py` and `test_cert_long_run_stability.py:106`.
  `test-architecture-reviewer` decides that (AC 9).

## Acceptance Criteria
1. With `audit_mode=False` and an overrun, no result is dropped by wall-clock time and `force_mode`
   is not called. The regression test proves both and fails on `main` before the change.
2. `record_dropped_work(9999)` is gone. `dropped_work` counts only work the scheduler shed.
3. The overrun is recorded as a typed telemetry signal. A test shows nothing in the governor or in
   `AuthoritativeState` reads it.
4. `test_camp_raid_targeting.py` reaches `DEGRADED` explicitly, asserts it, and still proves the
   raiders move. rpg-planner has reviewed the change.
5. `test_work_debt_stays_empty_in_production.py` keeps a non-vacuous precondition (work really
   dropped, mode really left `NORMAL`) and passes.
6. Every test listed in Scope 4 was run. The ticket records, for each one: unaffected, fixed (how),
   or not runnable locally (why).
7. Docs, the intentional-divergence entry and the parity ledger are updated, and
   `wall_clock_inventory --check` passes.
8. `uv run make code-health` and `uv run make typecheck-py` report no new or worse finding (blocking on
   `main` since 2026-10-05).
9. **On merge, notify `test-architecture-reviewer`** (requested through rpg-planner on PR #355) to
   re-evaluate the two throttle-caused CI skips: `tests/integration/world/test_long_run_stability.py`
   and `tests/certification/test_cert_long_run_stability.py:106`. Notify by a note in the PR body and
   a message to the user, who relays it. Governor input 1 is the deciding risk.

## Related Tickets
- `TCK-20261005-TICK-BUDGET-THROTTLE-MAKES-NON-AUDIT-RUNS-WALL-CLOCK-DEPENDENT` (rpg, superseded by
  this one, holds the evidence)
- `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION` (covered by `test_camp_raid_targeting`)
- `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING` (PERF-D1 input 4; Lane A, after this batch)
- `TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION`
- `TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER` (same batch)

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (PERF-D1, amendment A1)
- `docs/engine/deterministic_execution.md`
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md` (gate item 6)
- `docs/plans/design_enhancement/performance_optimization/rpg_core_handoff.md` (Responses, 2026-10-06)

## Related Stored Artifacts
- none

## Related Code Areas
- `src/engine/kernel.py` (`_phase_resolution`, the end-of-tick check)
- `src/engine/runtime_status.py`, `src/core/governance.py` (signal records)
- `tests/integration/world/test_camp_raid_targeting.py`, `tests/integration/kernel/`

## Assumptions / Open Questions
- The planner assumes the governor still enters `DEGRADED` on load without the throttle, so the
  scheduler still sheds. Verify this in the work-debt test (Scope 4).
- Where the typed signal lives is the implementer's call within Scope 3. Tell the planner before
  adding a field to `PressureSignals` that `AuthoritativeState` stores, because that path is gated.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
