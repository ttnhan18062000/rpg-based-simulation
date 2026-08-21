---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260817-RUNTIMEMODE-BENCH-SCOPING
phase: done
date: 2026-08-17
tags: [performance, engine, documentation]
---

# TCK-20260817-RUNTIMEMODE-BENCH-SCOPING

## Title
Add RuntimeMode as a required Scoped-Claims dimension and enforce NORMAL-mode sampling in the perf-baseline CI gate

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
performance_contract.md §3.1 requires performance claims to bind to 4 dimensions (Runtime Profile, Hardware Class, Scenario, Execution Mode), none of which is RuntimeMode. RuntimeMode is recorded (long_run_harness.py:225) but never asserted on; the live CI gate (test_perf_regression_baseline.py) computes one blended avg_tick_compute_ms with no RuntimeMode==NORMAL check. A benchmark that degrades mid-run gets cheaper ticks blended into the average, potentially offsetting a real regression — this conflicts with the spirit of certification_contract.md §6's "no modification of kernel laws for benchmark vanity" discipline, which today only applies to full cert runs, not the everyday CI gate. RuntimeMode needs to be added as a required Scoped-Claims dimension, plus enforcement in the perf-baseline test that fails/flags a run if the Governor ever left NORMAL during sampling.

## Scope
- Add RuntimeMode as a required 5th dimension in performance_contract.md §3.1 Scoped Claims (alongside Runtime Profile, Hardware Class, Scenario, Execution Mode)
- Record Governor RuntimeMode per sampled tick inside BenchHarness.run_benchmark()'s tick loop (mirroring long_run_harness.py:225's active_mode pattern), exposed in the result dict (e.g. mode_sequence)
- Make tests/perf/test_perf_regression_baseline.py::test_regression_vs_baseline fail or explicitly non-silently flag when any sampled tick's RuntimeMode != NORMAL, independent of the avg_tick_compute_ms threshold result
- Add a new unit test that forces the Governor out of NORMAL mid-sample and asserts the gate surfaces the excursion rather than silently blending it into the average

## Out of Scope
- Extending PressureSignals (src/core/governance.py) with a mode field — it is explicitly FROZEN (Resource Phase 4 Milestone 1); implement via per-tick sampling inside BenchHarness instead, not a PressureSignals schema change
- Reusing/importing certification's ConformanceEvaluator degradation-order logic wholesale — decide only whether a simpler NORMAL-only assertion suffices for the fast CI gate
- Recalibrating the 26 scenario builders' warmup/sample tick counts, even if some legitimately dip out of NORMAL under real load — flag as a follow-up if found, don't silently loosen the gate to compensate

## Acceptance Criteria
- [x] performance_contract.md §3.1 Scoped Claims includes RuntimeMode as a required 5th dimension
- [x] BenchHarness.run_benchmark() (or its caller) records Governor RuntimeMode per sampled tick, exposed in the result dict (e.g. mode_sequence)
- [x] tests/perf/test_perf_regression_baseline.py::test_regression_vs_baseline fails or explicitly non-silently flags when any sampled tick's RuntimeMode != NORMAL, independent of whether avg_tick_compute_ms stayed within threshold
- [x] A new unit test forces the Governor out of NORMAL mid-sample and asserts the gate surfaces the excursion rather than silently blending it in

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC

## Related Docs
- docs/engine/performance_contract.md
- docs/engine/contracts/certification_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/perf/bench_harness.py
- src/perf/long_run_harness.py
- src/core/governance.py
- src/engine/runtime_status.py
- src/engine/kernel.py
- src/certification/conformance.py
- src/certification/models.py
- tests/perf/test_perf_regression_baseline.py
- tests/perf/test_bench_harness.py
- tests/perf/conftest.py

## Assumptions / Open Questions
- PressureSignals is frozen/slots — a narrower per-tick sampling fix inside BenchHarness (not touching PressureSignals) is the intended implementation route pending Plan-phase confirmation; if Plan disagrees and requires a PressureSignals schema change, this may need Architecture Review
- Whether to reuse certification's ConformanceEvaluator logic or write an independent simpler NORMAL-only assertion is an open Plan-phase decision
- Need to confirm the 26 scenario builders (10 warmup/50 sample ticks) don't already legitimately dip out of NORMAL under real load before enabling the gate as blocking, to avoid false positives

## Implementation Notes

Implemented all 6 plan steps in dependency order (Step 1 → 2 → 3 → 4 → 5 → 6).

**Step 1** — Added a new `**RuntimeMode**` bullet to `docs/engine/performance_contract.md` §3.1
Scoped Claims, immediately after `**Execution Mode**`, exact text as specified in the plan.

**Step 2** — `BenchHarness.run_benchmark()` (`src/perf/bench_harness.py`) now appends
`kernel.status.current_mode.name` to a new `mode_samples: List[str]` list on every sampled tick
(unthrottled, unlike the `i % 10 == 0`-gated RSS sampler), and exposes it as
`result["mode_sequence"]`.

**Step 3** — Added `_RUNTIME_MODE_HARD_SCENARIOS` (module-level frozenset) and
`_assert_runtime_mode_stayed_normal()` to `tests/perf/test_perf_regression_baseline.py`, and wired
the excursion check into `test_regression_vs_baseline` immediately after `run_benchmark()` returns
and before the existing `avg_tick_compute_ms` threshold block — independent of that check per AC3.

**Step 4 (the ticket's central empirical deliverable) — REAL findings, not assumed:**
Ran `pytest tests/perf/test_perf_regression_baseline.py -v -s -k test_regression_vs_baseline`
against all 6 live-parametrized scenarios (`idle_100_local`, `movement_100_local`,
`combat_10_local`, `simq_corpus_frontier_extended`, `simq_corpus_frontier_marches`,
`simq_corpus_crowded_frontier`) at the gate's real configuration (`warmup_ticks=10,
sample_ticks=50`), then ran `simq_corpus_crowded_frontier` a second time per the plan's decision
rule (the scenario flagged as most likely to excurse on RSS grounds).

**Result: all 6 scenarios showed `mode_sequence` == `['DEGRADED']` for every one of the 50 sampled
ticks, on every run, with zero variance** — including `idle_100_local` (100 idle entities,
trivial compute) and the second `simq_corpus_crowded_frontier` run (identical to the first).
This ruled out both hypotheses the plan anticipated (some scenarios legitimately RAM/compute-
pressured, others clean) — the excursion is universal and deterministic, not load-dependent.

Root cause traced (read-only investigation, no fix applied — out of scope):
`WorkerManager.get_stats()` (`src/engine/worker_manager.py:229-232`) computes
`worker_utilization = peak_active / max_workers if max_workers > 0 else 1.0`. Every
`PERF_*_LOCAL` profile (`src/perf/profiles.py`, `PERF_512MB_LOCAL` through `PERF_4GB_LOCAL`) sets
`workers=0` (`max_worker_count=0`), so `worker_utilization` is hardcoded to `1.0` on literally
every tick of every LOCAL-execution-mode benchmark, regardless of actual load.
`ResourceGovernor._get_indicated_mode()` (`src/engine/governor.py:88`,
`worker_utilization >= 0.9 -> DEGRADED`) therefore trips unconditionally from tick 1. Confirmed by
direct trace (constructed `Kernel` + `PressureSignals` inspection outside the test suite):
`work_debt=0`, `tick_ms` well under budget, `worker_util=1.0` on every single tick regardless of
scenario.

**Classification: `_RUNTIME_MODE_HARD_SCENARIOS` stays EMPTY.** Per the plan's decision rule
("leave every scenario that showed even one non-NORMAL entry out of the set"), none of the 6
scenarios qualifies for hard (`AssertionError`) gating — all 6 stay soft
(`PerformanceThresholdWarning`, visible in `pytest -rw`/warnings summary, non-blocking). This is
the correct, safe outcome given the finding: gating hard right now would immediately and
permanently fail 100% of LOCAL-mode perf-regression CI runs on every commit, for a reason
completely unrelated to any real engine regression.

**Follow-up ticket recommended (not opened by this ticket, per plan Step 4.5 / ticket
Out-of-Scope item 3):** File a ticket to fix `WorkerManager.get_stats()`'s `else 1.0` default for
`max_workers == 0` (LOCAL/inline execution) — it should plausibly be `else 0.0` (no configured
worker pool means no worker-driven pressure, not maximum pressure) or the Governor's
`worker_utilization` check should be skipped entirely for `max_workers == 0` profiles. Until that
lands, this ticket's new RuntimeMode excursion gate is real and wired correctly, but cannot
meaningfully distinguish "a benchmark genuinely regressed into DEGRADED mode" from "this is a
LOCAL-mode benchmark, which is always reported DEGRADED" — it is soft-only by necessity, not by
policy choice.

**Step 5** — Added all 3 new tests as specified, with one code-level deviation from the plan's
exact text (documented in `plan.md`'s new Deviations section): `test_run_benchmark_records_mode_sequence`
(5a, `tests/perf/test_bench_harness.py`) keeps the plan's assertions on `mode_sequence`
presence/length/valid-enum-names, but the plan's final `assert all(m == "NORMAL"...)` was removed
(not added) because the Step 4 empirical pass proved it deterministically false on any LOCAL
profile — not scenario-specific noise, a verified, repeatable fact. Removing it does not weaken
any Acceptance Criterion (5a is cited in the plan's own AC map only for "records Governor
RuntimeMode per sampled tick, exposed as mode_sequence", which the remaining assertions still
fully prove). `test_perf_regression_baseline_flags_runtime_mode_excursion` (5b) and
`test_performance_contract_lists_runtimemode_scoped_claim` (5c) were added exactly as specified,
no deviations.

**Step 6** — Re-checked the highest existing `INFRA-\d+` ID immediately before writing (still
`INFRA-367`, unchanged from Plan time — no collision with the concurrent
`TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP` ticket). Wrote `INFRA-368` via
`tools/parity_ledger_writer.write_entry()` (not raw Edit), with `text`/`v2_evidence` updated to
describe the actual all-soft classification and the WorkerManager root cause, not the plan's
placeholder wording. `write_entry()` rebuilt the derived parity index in-process; also ran the
visible `python3 tools/parity_index.py build` Bash call per `.claude/agents/parity-updater.md`
convention so the retro metric can see it.

**Scope Guards honored:** no changes to `PressureSignals`, `RuntimeStatus` schema,
`perf_baseline_policy.md`, `extended_certification_contract.md`, `ConformanceEvaluator` usage,
scenario profiles/tick-counts, or `tests/unit/domains/optimization/test_phase_budget_governor.py`
/ `tests/unit/resource/test_resource_governor_contract.py`. The `WorkerManager`/`Governor` root
cause was investigated read-only to write an accurate finding; no fix was applied to either file.

## Test Summary
Ran `.venv/bin/python3 -m pytest tests/perf/test_bench_harness.py tests/perf/test_perf_regression_baseline.py -v`
— **11 passed, 6 warnings, 0 failed** (warnings are the expected `PerformanceThresholdWarning`s
from all 6 soft-gated scenarios, per the Step 4 classification above — non-blocking by design).
Covers: existing `test_bench_harness_cpu_time_sampling` (unmodified, still green), new
`test_run_benchmark_records_mode_sequence` (5a), all 6 parametrized `test_regression_vs_baseline`
cases (now including the RuntimeMode excursion check, independent of `avg_tick_compute_ms`), new
`test_perf_regression_baseline_flags_runtime_mode_excursion[True/False]` (5b), new
`test_performance_contract_lists_runtimemode_scoped_claim` (5c).

## Files Changed
- `docs/engine/performance_contract.md` — Step 1, RuntimeMode Scoped-Claims bullet
- `src/perf/bench_harness.py` — Step 2, per-tick mode sampling + `mode_sequence` result key
- `tests/perf/test_perf_regression_baseline.py` — Step 3 (`_RUNTIME_MODE_HARD_SCENARIOS`,
  `_assert_runtime_mode_stayed_normal`, wired assertion in `test_regression_vs_baseline`) + Step 5b/5c
  new tests
- `tests/perf/test_bench_harness.py` — Step 5a new test (`test_run_benchmark_records_mode_sequence`)
- `docs/parity_ledger/infrastructure.yaml` — Step 6, new `INFRA-368` entry
- `docs/plans/kernel_concurrency_design_review_proposal.md` — Document-Update phase, added
  completion cross-link to C4 with the WorkerManager bug finding, matching the pattern used for
  every other closed ticket in this batch (C2/C3/C6/C7/C8)
- `staging_artifacts/TCK-20260817-RUNTIMEMODE-BENCH-SCOPING/plan.md` — Deviations section
  documenting the Step 4 empirical outcome and the Step 5a assertion change
- `tickets/inprogress/TCK-20260817-RUNTIMEMODE-BENCH-SCOPING.md` — this ticket, closed out

## Completion Summary
Added RuntimeMode as a 5th required Scoped-Claims dimension in the performance contract, wired
per-tick RuntimeMode sampling into `BenchHarness.run_benchmark()` (exposed as
`result["mode_sequence"]`), and added an independent excursion check to the perf-regression CI
gate. The empirical Step 4 measurement — the ticket's central deliverable — found all 6 live
scenarios stay `DEGRADED` for their entire sampled window on every run, traced to a pre-existing
`WorkerManager.get_stats()` defect (`worker_utilization` hardcoded to `1.0` whenever
`max_worker_count == 0`, which every `PERF_*_LOCAL` profile sets) rather than genuine per-scenario
load; `_RUNTIME_MODE_HARD_SCENARIOS` therefore correctly stays empty (all 6 gated soft) with a
follow-up ticket recommended to fix the WorkerManager/Governor signal defect itself. All 11
relevant tests pass (6 parametrized regression cases, 2 new hard/soft excursion-helper cases, and
3 other new/existing unit tests).
