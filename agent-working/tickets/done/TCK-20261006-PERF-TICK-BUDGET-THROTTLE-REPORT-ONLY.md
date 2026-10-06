---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY
phase: done
date: 2026-10-06
tags: [performance, determinism, engine, testing]
---

# TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY

## Title
The kernel's wall-clock tick-budget checks report overruns instead of dropping results or forcing DEGRADED (PERF-D1 inputs 2 and 3)

## Status
DONE

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
- `agent-working/stored_artifacts/TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY/` (investigation, plan, test_plan)

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
- **Change.** `Kernel._report_budget_overrun(elapsed_ms, threshold_ms, site, tick)` replaces both blocks. The
  mid-tick check (`_phase_resolution`) detects the overrun once per tick, records it, logs, raises the watchdog
  alert and keeps processing every result: no `break`, no `record_dropped_work`, no `force_mode`. The
  end-of-tick check records the same signal instead of `record_dropped_work(9999)`. The two sites use one
  helper, so `kernel.py` shrank (module 1419 -> 1393 lines; `_phase_resolution` and `_tick_once_inner`
  complexity down).
- **Typed signal.** `RuntimeStatus.budget_overrun_ms`, `budget_overrun_tick`, `total_budget_overruns`, set by
  `RuntimeStatus.record_budget_overrun(overrun_ms, tick)` (once per tick; a second report in the same tick keeps
  the larger). It is NOT on `PressureSignals`, so the governor's inputs and the signal history do not carry it,
  and no gated path (`state.py`) is touched. Tests assert the governor, `governance.py` and `state.py` sources do
  not mention it.
- **Tick number.** The end-of-tick check runs after `_phase_advancement` has moved `state.tick` on, so the first
  version counted one tick twice (9 overruns in 8 ticks). The helper now takes the tick explicitly and the end of
  tick passes the tick captured at its start (`tick_no`). The watchdog alert's `tick` for the end-of-tick check is
  therefore the tick that overran, where before it was the next one.
- **`ResourceGovernor.force_mode`** now has no caller in `src/`. Left in place (not asked to remove; tests
  and `governor.py` stay otherwise untouched). Only a comment in `governor.py` changed.
- **Finding: the default scheduler sheds nothing.** `DeterministicScheduler()` is built with no
  `PeriodicDefinition`, and nothing in `src/` registers one, so `dropped_count` is always 0 in shipped runs. The
  throttle and the 9999 sentinel were the only source of `dropped_work`. After this change `total_dropped_work` is
  0 in shipped runs; the planner's assumption "the scheduler still sheds under DEGRADED" holds only for a
  scheduler that has a non-authoritative periodic task. Recorded in DEV-014.
- **Follow-ups (perf-planner files them):** (1) surfacing `budget_overrun_*` in engine_manager, the live snapshot and Prometheus; (2) ~~`test_milestone_b_closure` failing on `origin/main`~~ resolved by #373 (tick-keyed fake clock); after merging `origin/main` (2026-10-07) it passes with this branch's kernel (3 passed), so no follow-up is needed; (3) no `src/` path registers a `PeriodicDefinition`, so governor shedding is a no-op in shipped runs (feeds PERF-M1-T05 and the governor-half design).
- **Not done.** Surfacing `budget_overrun_*` where `dropped_work_delta` is surfaced (engine_manager,
  live snapshot, Prometheus, `observability.py`): not small, left out. The overrun is visible in
  `RuntimeStatus` and as the watchdog alert.

### Scope 4: each test run
| Test | Result |
|---|---|
| `tests/integration/world/test_camp_raid_targeting.py` | **fixed**: it reached DEGRADED only by accident through the throttle. It now uses `_DegradedGovernor` (indicated mode DEGRADED, a seam through the governor) and asserts `kernel.status.current_mode is DEGRADED`; raiders still move. rpg-planner reviews this change (relayed by perf-planner). |
| `tests/integration/kernel/test_work_debt_stays_empty_in_production.py` | **fixed**: the precondition `total_dropped_work > 0` failed (0) because the throttle was the only source. The runs now pass a scheduler with one non-authoritative periodic task, which the governor's SURVIVAL policy sheds. The precondition is unchanged and holds; the claim is unchanged. |
| `tests/integration/kernel/test_milestone_b_closure.py` | **(update 2026-10-07: #373 rewrote it to a tick-keyed fake clock; after merging `origin/main` it passes with this branch's kernel, 3 passed.)** At the time of writing it **failed the same on `origin/main`** (checked in a throwaway worktree of `origin/main`): under its mock clock a tick takes 164 ms (82 clock reads at 2 ms; its comment says ~63 and ~126 ms), which is SURVIVAL, not DEGRADED. Governor-driven, not the throttle, so this ticket does not cause it. Marked `slow`. Not changed. |
| `tests/certification/test_allowed_failure_truth.py`, `test_envelope_violations.py`, `test_harness_contract.py`, `test_resilience_recovery.py` | **unaffected**: pass. `test_harness_contract.py::test_certification_detects_semantic_drift` failed once in a large parallel-load batch and passed 3 of 3 alone and in a 86-test rerun; not reproduced, wall-clock flake (10 ms budget), not attributed. |
| `tests/unit/engine/test_resource_budget_gate.py`, `tests/unit/api/test_engine_manager.py`, `tests/unit/observability/test_obs_backpressure.py`, `tests/integration/test_observatory_stream_outage.py`, `tests/unit/core/test_watchdog.py` | **unaffected**: pass; none depends on the throttle or the sentinel (they set dropped-work values directly). |
| `tests/unit/kernel/`, `tests/unit/core/test_signal_truth.py`, `test_signal_hardening.py`, the two inventory sync test files | pass |

## Test Summary
- New: `tests/integration/kernel/test_tick_budget_report_only.py` (4 tests). Its first two fail on `main` before
  the change: `force_mode` called every tick, no overrun field.
  No end-to-end determinism test: I wrote one (two overrunning runs, same canonical hash at every tick) and it diverged
  in 1 of 3 runs, at tick index 2. Cause: `PhaseBudgetGovernor` (`src/engine/phase_governor.py`) still reads per-phase
  wall-clock costs and `tick_compute_ms` in every mode, a remaining input already listed in `deterministic_execution.md`
  and out of scope here, so a non-audit hash-equality test cannot be reliable until that input goes. Removed rather
  than loosened. The first two tests are the proof that the throttle no longer changes outcomes (they fail on `main`).
- Scope 4 list: see the table above. 178 passed in the combined run, plus the one flake.
- `make code-health`: 0 new, 0 worse, 9 improved (kernel.py). `make typecheck-py`: no new error.
- `wall_clock_inventory --check` passes after regenerating with the tool.
- Not run locally: `tests/integration/world/test_long_run_stability.py` and `tests/certification/test_cert_long_run_stability.py`
  (CI-skipped for the throttle; AC 9 hands them to `test-architecture-reviewer`).

## Files Changed
- `src/engine/kernel.py`, `src/engine/runtime_status.py`, `src/engine/governor.py` (comment only)
- `tests/integration/kernel/test_tick_budget_report_only.py` (new)
- `tests/integration/world/test_camp_raid_targeting.py`, `tests/integration/kernel/test_work_debt_stays_empty_in_production.py`
- `docs/engine/deterministic_execution.md`, `docs/guidelines/intentional_divergences.md` (DEV-014), `docs/parity_ledger/infrastructure.yaml` (INFRA-423)
- `docs/performance/wall_clock_inventory.{json,md}` (regenerated)

## Completion Summary
The kernel's two wall-clock budget checks are report-only (PERF-D1 inputs 2 and 3): no mid-tick drop, no forced
DEGRADED, no 9999 sentinel. Overruns are `RuntimeStatus.budget_overrun_*` telemetry that nothing in the governor or
`AuthoritativeState` reads. Tests that leaned on the old behaviour were fixed (camp-raid reaches DEGRADED through a
governor seam; work-debt sheds through a real non-authoritative periodic task). DEV-014, INFRA-423 and the wall-clock
inventory are updated. Findings and follow-ups are recorded in Implementation Notes. Not verified locally:
`test_milestone_b_closure` (fails the same on `main`) and the two long-run stability tests (CI-skipped).
