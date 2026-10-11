---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED
phase: done
date: 2026-10-10
tags: [performance, benchmarking, testing, regression]
---

# TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED

## Title
PERF-M2-T03: Tripwire projection as a paired base/head comparison

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Run base and head paired on the same runner in one job (OD-2), over a small declared scenario set, each side in a fresh process, through compare(). Use a relative threshold, an absolute floor and a noise budget. Allow one recorded diagnostic retry. A missing or incompatible baseline is INCONCLUSIVE, not pytest.skip. Outcomes are reported, not blocking. Decide the tripwire-adjacent debt in contract §5.2: absolute ceilings, PerfBudget/perf_baselines.json, and retiring check_perf_regression.py and perf_ci.py. This touches the perf tests and conftest, tools/perf/, the performance_contract.md §5 threshold (rpg-owned P1, owner approves), and the CI selector in test.yml (tell the testing-planner first). Depends on T02b, T05 and T07. Today the live tripwire still uses max(5ms, 1.25x) with pytest.skip, and three conflicting tolerances exist.

Source concern IDs: C4.

## Scope
- Replace the tests/perf/test_perf_regression_baseline.py::test_regression_vs_baseline pytest.skip path with an INCONCLUSIVE outcome and a named reason for a missing or incompatible baseline
- Add a paired tripwire runner (tools/perf/) that runs base and head each in a fresh subprocess on the same runner over a declared scenario list, and passes both BenchmarkRecords to compare(base, head, thresholds)
- Define one threshold (relative + absolute floor + noise budget) that replaces max(5ms,1.25x), max(1.15x,+3ms) and the 5/10/15% percentile bands, and write it into docs/engine/performance_contract.md §5 with owner approval
- Add at most one diagnostic retry on a non-PASS result, recording both the original and retry outcomes
- Report or annotate non-PASS outcomes without failing CI. Update the .github/workflows/test.yml perf selector after notifying the testing-planner.
- Retire tools/perf/check_perf_regression.py and tools/perf/perf_ci.py with their tests and Makefile targets, removing references in tools/gate_checks/test_scope_coverage_static.py, tests/codebase/test_repo_root_allowlist.py and tools/perf_guard.py
- Absorb or delete perf_baselines.json/PerfBudget and the absolute ceilings, recording each disposition in performance_contract.md §5.2

## Out of Scope
- Making any tripwire outcome blocking (OD-8)
- Capacity-run claims or the capacity_run tool (PERF-M2-T04)
- Rerunning committed baselines in tests/perf/baselines or docs/observability/baselines (PERF-M2-T08)
- Building the gate_conformance.yaml map (PERF-M2-T06)
- Changing BenchmarkRecord/compare() semantics (PERF-M2-T02b)

## Acceptance Criteria
- [x] test_regression_vs_baseline no longer calls pytest.skip. Unit tests assert that a missing baseline record gives INCONCLUSIVE with a named reason, and that an incompatible identity (mismatched protocol.percentile_method or signal_contract) gives INCONCLUSIVE naming that field.
- [x] The tripwire runs base and head each in its own subprocess over a declared scenario list (a module-level constant or YAML) and passes both BenchmarkRecords to compare(base, head, thresholds)
- [x] A synthetic head slower than base by more than both the relative threshold and the absolute floor returns REGRESSION, and a delta inside the noise budget returns PASS
- [x] When the first comparison is not PASS, at most one diagnostic retry runs, and the emitted report contains both the original and the retry outcome (a test asserts retry count <= 1)
- [x] A non-PASS outcome does not fail the CI job: the tripwire test or step exits zero and emits the outcome as a report or annotation
- [x] tools/perf/check_perf_regression.py, tools/perf/perf_ci.py and their tests and Makefile targets are deleted or replaced, and no remaining reference exists in the Makefile, tools/gate_checks/test_scope_coverage_static.py, tests/codebase/test_repo_root_allowlist.py or tools/perf_guard.py
- [x] docs/engine/performance_contract.md §5 states the concrete threshold values, and §5.2 records the absorb-or-delete disposition of absolute ceilings and perf_baselines.json/PerfBudget  (done after the owner's decision of 2026-10-10: values approved as provisional, dispositions accepted)

## Related Tickets
- TCK-20261003-PERF-M2-CLAUSE-INVENTORY
- TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA
- TCK-20261004-PERF-REGRESSION-CHECK-NO-SILENT-PASS
- TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT
- TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE
- TCK-20260624-PERF-GUARD-INFRA
- TCK-20261003-IMPLEMENT-TICKET-PERF-REMINDER-CITATION
- TCK-20261004-PERF-SCENARIO-MIXED-STATE-SPAWN-COLLISION

## Related Docs
- docs/engine/performance_contract.md
- docs/performance/benchmark_identity_schema.md
- docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED/ (plan.md, investigation.md, test_plan.md)

## Related Code Areas
- tests/perf/test_perf_regression_baseline.py
- tests/perf/conftest.py
- tests/tools/perf_assertions.py
- tools/perf/check_perf_regression.py
- tools/perf/perf_ci.py
- tools/perf_guard.py
- perf_baselines.json
- src/perf/bench_harness.py
- src/perf/profiles.py
- src/perf/regression_gate.py (read-only: outside the OD-8 lift; T03 may propose retiring it, and removal needs an owner lift)
- .github/workflows/test.yml
- Makefile

## Assumptions / Open Questions
- Lift boundary (roadmap RPG-core gate item 8, owner 2026-10-09): `src/` edits are limited to `src/perf/bench_harness.py`, `src/perf/profiles.py`, `src/perf/long_run_harness.py`, new `src/perf/benchmark_record.py`, `src/observability/reporting/baseline_comparator.py` and `sweep_report.py`. Any other `src/` path listed under Related Code Areas is read-only here; editing it needs a new owner lift.
- Blocked until PERF-M2-T02b (BenchmarkRecord/compare), PERF-M2-T05 and PERF-M2-T07 land
- The §5 threshold value needs rpg owner approval (P1 doc) before the ticket can close
- A paired run needs a base-commit checkout in the perf-cert-arena job, roughly doubling its runtime. The testing-planner must agree to the selector change.
- Each absolute-ceiling test (tests/perf and tests/arena phase budget tests, test_perf_idle, test_perf_stress) needs an absorb-or-delete decision, which T06 later depends on
- Fresh-process timing on shared runners may make the noise budget too tight, so INCONCLUSIVE outcomes may be frequent
- Nightly or local use of the pre-DEV-017 committed baselines continues until T08

## Implementation Notes
- Plan, investigation and test plan: `agent-working/stored_artifacts/TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED/`.
- **Built:** `tools/perf/tripwire.py` (declared `TRIPWIRE_SCENARIOS`, paired runner, one diagnostic retry that runs head first and is skipped when a side failed to spawn, non-blocking report and `::warning` annotations, an alternating-order A/A `calibrate`, `load_baseline` / `compare_with_baseline` for the nightly lane); the nightly test reports `INCONCLUSIVE` with a named reason instead of `pytest.skip`; `check_perf_regression.py`, `perf_ci.py` and the tools' own test are removed with their two scope-map entries.
- **The owner decided on 2026-10-10 (relayed by perf-planner):** section 5 approved **as provisional** (`max(5 ms, base x 1.40)`, paired, one retry, never blocking, to be recalibrated on the CI runner once the CI step lands); section 5.2: absolute ceilings stay as soft smoke bounds, `PerfBudget` / `perf_baselines.json` / `perf_guard.py` are deleted in a follow-up (`TCK-20261010-PERF-M2-PERFBUDGET-RETIRE`, filed, not started), `regression_gate.py` retires under its own later lift. Applied to `docs/engine/performance_contract.md` (§3.3, §5, §5.2), together with T04's §3.3 text. The file's owner is rpg-planner; merging this PR approves the §3.3 descriptive text.
- **The evidence was corrected after the decision.** The decision cited a noise budget of 0.31 from 28 A/A pairs. A third calibration (order alternated, 44 pairs in all) found a same-code deviation of 0.352, so `NOISE_BUDGET` is 0.35 and the contract states it. The approved 1.40 rule still clears the worst average pair (1.352) but the margin is 0.05; this is flagged in the PR for the owner. The value of the rule was **not** changed.
- **Measured noise:** with identical code on both sides on this 6-vCPU VM, head/base average latency deviated by up to 0.352; the median was no steadier (up to 0.397). On this host the tripwire detects only changes above about 40%. The number is this VM's; recalibrate on the CI runner.
- **Held:** `.github/workflows/test.yml` is untouched (testing-planner to agree, issue #488; the proposed step is in the PR body).
- The ticket's reference list was partly wrong: the Makefile, `tests/codebase/test_repo_root_allowlist.py` and `tools/perf_guard.py` do not reference the retired tools. The real references were `tools/gate_checks/test_scope_coverage_static.py` and `tests/tools/test_test_scope_coverage_static.py` (owners: agent-working-planner, rpg-planner).
- The combat scenario and the corpus worlds are not in the declared set (the combat builder takes team sizes, not an entity count); they are PERF-M2-T08's.

## Test Summary
- New: `tests/unit/perf/test_tripwire.py` (21: 20 default, 1 real fresh-process run marked `slow`); `tests/perf/test_perf_regression_baseline.py` rewritten (reports INCONCLUSIVE for the legacy references). With `tests/unit/perf`, the scope-map tests, the paths guard and the repo-root allowlist test: passing.
- Calibration (A/A, this VM, three runs, 44 pairs): see Implementation Notes and `investigation.md`.
- Not run: the full suite; the tripwire against a real base branch checkout in CI (test.yml is held).

## Files Changed
- New: `tools/perf/tripwire.py`, `tests/unit/perf/test_tripwire.py`.
- Edited: `tools/perf/capacity_run.py` (RunSpec tier and projection), `tests/perf/test_perf_regression_baseline.py`, `tools/gate_checks/test_scope_coverage_static.py` and `tests/tools/test_test_scope_coverage_static.py` (two stale entries removed), `docs/performance/perf_baseline_policy.md`, `docs/performance/benchmark_identity_schema.md`, `docs/performance/baseline_invalidation_ledger.md`, `docs/guidelines/intentional_divergences.md` (DEV-022), `docs/parity_ledger/infrastructure.yaml` (INFRA-433).
- Removed: `tools/perf/check_perf_regression.py`, `tools/perf/perf_ci.py`, `tests/tools/test_check_perf_regression.py`.

## Completion Summary
`tools/perf/tripwire.py` is the CI-fast tripwire: base and head paired on one runner, each in a fresh process, through `compare()`, one head-first diagnostic retry, never blocking, with `INCONCLUSIVE` and a named reason in place of `pytest.skip`; the retired `check_perf_regression.py` and `perf_ci.py` are gone. `docs/engine/performance_contract.md` states the owner-approved provisional threshold (`max(5 ms, base x 1.40)`) and the section 5.2 dispositions. Left open: the CI step (`test.yml`, issue #488), recalibration on the CI runner, the `PerfBudget` deletion (`TCK-20261010-PERF-M2-PERFBUDGET-RETIRE`), and the thin margin between the noise (0.35) and the threshold (0.40), flagged for the owner.
