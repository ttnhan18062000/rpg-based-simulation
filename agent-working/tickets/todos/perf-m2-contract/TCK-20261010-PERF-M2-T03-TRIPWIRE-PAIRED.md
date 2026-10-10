---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED
phase: open
date: 2026-10-10
tags: [performance, benchmarking, testing, regression]
---

# TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED

## Title
PERF-M2-T03: Tripwire projection as a paired base/head comparison

## Status
OPEN

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
- [ ] test_regression_vs_baseline no longer calls pytest.skip. Unit tests assert that a missing baseline record gives INCONCLUSIVE with a named reason, and that an incompatible identity (mismatched protocol.percentile_method or signal_contract) gives INCONCLUSIVE naming that field.
- [ ] The tripwire runs base and head each in its own subprocess over a declared scenario list (a module-level constant or YAML) and passes both BenchmarkRecords to compare(base, head, thresholds)
- [ ] A synthetic head slower than base by more than both the relative threshold and the absolute floor returns REGRESSION, and a delta inside the noise budget returns PASS
- [ ] When the first comparison is not PASS, at most one diagnostic retry runs, and the emitted report contains both the original and the retry outcome (a test asserts retry count <= 1)
- [ ] A non-PASS outcome does not fail the CI job: the tripwire test or step exits zero and emits the outcome as a report or annotation
- [ ] tools/perf/check_perf_regression.py, tools/perf/perf_ci.py and their tests and Makefile targets are deleted or replaced, and no remaining reference exists in the Makefile, tools/gate_checks/test_scope_coverage_static.py, tests/codebase/test_repo_root_allowlist.py or tools/perf_guard.py
- [ ] docs/engine/performance_contract.md §5 states the concrete threshold values, and §5.2 records the absorb-or-delete disposition of absolute ceilings and perf_baselines.json/PerfBudget

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
None.

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

## Test Summary

## Files Changed

## Completion Summary
