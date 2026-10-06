---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY
date: 2026-10-06
tags: [performance, determinism, engine, testing]
---

# Test plan: TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY

For the eventual implementation (design only now; nothing is written or run). Assumes Option 1 of `plan.md` section 3. Read-only checks run
for the design itself: the inventory `--check`, the counter probe (`probes/calibrate_work_units.py`, 180 rows), and greps of the tests
that drive modes (`investigation.md` section 5).

## 1. Canonical hash-equality test (the one #379 had to remove)

`tests/integration/kernel/test_canonical_signal_contract.py::test_canonical_runs_are_hash_and_mode_identical`

- Scenario: `build_movement_state(entity_count=120)`, seed 7, 10 ticks, `signal_contract=CANONICAL`, `audit_mode` off, a profile whose
  `max_tick_budget_ms` is low enough that the modelled cost crosses a threshold within the run (so the mode changes). Real governor, real
  `PhaseBudgetGovernor`, no governor override.
- Per tick record `(tick, mode, phase_budgets, CanonicalStateHasher.get_hash(state))`.
- Run it **10 times** (a loop inside one test, so one test run is the proof): runs 1 to 5 under the real clock; runs 6 to 10 with
  `time.perf_counter_ns` patched to a seeded jittering clock (steps drawn per run from `random.Random(run)`; some runs 50x slower, some 50x
  faster). All 10 sequences must equal run 1.
- Non-vacuity: assert the mode sequence contains at least two distinct modes, and at least one `PhaseBudgets` differs from the baseline
  budgets. A run that never leaves `NORMAL` fails the test.
- Acceptance (ticket AC 4): 10 of 10 in one run, and the whole test passes 10 of 10 times under CI-like conditions (record each repetition).

## 2. A test that varies `perf_counter_ns` and asserts the same mode and budgets

`test_canonical_governors_ignore_the_clock`
- Build `PressureSignals` through `CanonicalSignalSource` for a fixed state under three patched clocks (frozen, 1x, 1000x). Assert equal
  `tick_cost`, `phase_cost`, and equal `ResourceGovernor.evaluate` and `PhaseBudgetGovernor.evaluate` results (mode and `PhaseBudgets`).
- Mutation proof: temporarily make `CanonicalSignalSource` read `time.perf_counter_ns()`; the test must fail for that reason. Record the
  mutant and its failure in the ticket.

## 3. Static guard

`test_canonical_modules_import_no_clock_or_host_module`: parse `src/engine/work_units.py` and the Canonical class's module; assert no import of
`time`, `psutil`, `os`, `threading`, `datetime`. Fails on any new read. Also assert `tick_cost` is never
assigned from `perf_counter_ns` in the Canonical branch.

## 4. Executor independence of the units

`test_work_units_are_identical_across_executors`: same scenario and seed under the sequential executor, the thread pool (2 workers) and
the process pool; assert identical `tick_cost`, `phase_cost` and queue/worker proxies per tick. Extends the existing parity tests
(`tests/unit/kernel/test_executor_parity.py`, `test_worker_equivalence.py`).

## 5. Live is unchanged (golden)

`test_live_signals_are_bit_identical_after_the_move`: with a deterministic fake clock and a fixed state, record the full `PressureSignals`
sequence and mode sequence of a LIVE run before the move (committed fixture) and assert the same after. Guards the "moved code, no behaviour
change" claim for `LiveSignalSource`.

## 6. Unit tests

- `PressureSignals` fallback: built with only `tick_compute_ms`, the governor decides exactly as today (existing tests prove it unchanged).
- `ResourceGovernor` and `PhaseBudgetGovernor` produce the same decisions for `(cost, budget)` in ms and in reference-ms for equal ratios.
- Recovery (dwell, confidence window, watermark) in `tick_cost`.
- `RuntimeProfile.signal_contract`: default `LIVE`; invalid values rejected; the contract and `WORK_MODEL_V1` appear in the run manifest.
- Precedence: `audit_mode` set with `signal_contract=CANONICAL` gives zeroed signals (Option 1).
- Canonical drops memory and replay backlog: a huge RSS and a full replay buffer do not change the mode.
- Queue and worker proxies: zero workers gives 0.0; saturation gives 1.0; never above 1.0 (PERF-D1 range).
- `final_integrity` fallback path (if chosen): `PhaseBudgetGovernor` rule 2 off under Canonical, on under Live.

## 7. Calibration acceptance (step 1 of the work, not a CI test)
Stored fit and per-family error; pooled R^2 >= 0.85 and actual-to-predicted within 0.5 to 2.0; locomotion R^2 >= 0.75; `final_integrity`
R^2 >= 0.6 or the documented fallback. Re-run on two hosts and compare the fitted weights.

## 8. Existing tests, and what happens to each (Option 1)
Unchanged: `test_milestone_b_closure`, `test_camp_raid_targeting`, `test_tick_budget_report_only`, `test_catalog_entity_spawn_wiring`,
`test_work_debt_stays_empty_in_production` (until retro step 2), the five tests that build `PressureSignals(tick_compute_ms=...)`,
`test_resilience_recovery`. To re-evaluate by `test-architecture-reviewer`: the two long-run CI skips. Run the whole set
(`tests/unit/kernel`, `tests/unit/resource`, `tests/unit/domains/optimization`, `tests/integration/kernel`, `tests/certification` minus the long run)
before and after each step.

## 9. Feedback-loop stability
- `test_cost_is_demand_not_work_done`: run the same state for one tick with the governor pinned to `NORMAL` and then pinned to `DEGRADED`
  (the existing `_get_indicated_mode` seam); assert identical `tick_cost`, `phase_cost` and queue/worker proxies. This is the direct test of the
  pre-policy claim in `plan.md` section 2. It fails if any post-policy count (results after cadence gating, throttled-scan candidates) leaks in.
- `test_canonical_mode_transitions_stay_within_anti_thrash_bounds`: a scenario whose modelled cost crosses the DEGRADED threshold, 60 ticks,
  real governor. Record the mode sequence and assert: (a) every de-escalation happens at least `dwell_time_ticks` after the previous transition;
  (b) the number of transitions is at most `ceil(ticks / dwell_time_ticks) + 2`; (c) no `DEGRADED -> NORMAL -> DEGRADED` pair within the
  confidence window plus the dwell time (`profile.confidence_window_ticks + profile.dwell_time_ticks`). Run it on two profiles (a short dwell and the
  default), and on a scenario sitting just above and just below the threshold. These bounds are the existing ones (`governor.py:114-155`); the test
  proves the proxy does not defeat them.

## 10. Gates
`wall_clock_inventory --check` after regeneration; `uv run make code-health` and `uv run make typecheck-py` with no new or worse finding
(kernel.py ceiling 1,419 lines); `tests/docs`.
