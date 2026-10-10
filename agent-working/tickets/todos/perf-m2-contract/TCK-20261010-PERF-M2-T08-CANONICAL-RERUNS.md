---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS
phase: open
date: 2026-10-10
tags: [performance, benchmarking, regression]
---

# TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS

## Title
PERF-M2-T08: M1 baseline reruns under the canonical variants

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Re-run baseline invalidation ledger §5 steps 1, 2, 3 and 5 under the T07 canonical variants, as schema records labelled provisional. Step 4 (baseline_5k.json) stays with RPG's behavioural 5k rebaseline ticket and is out of scope. Label combat-heavy scenarios WORK_MODEL_V1. Run tactical and combat-heavy scenarios after RPG's hunting batch lands, or label them pre-hunting. The mixed_200_* reruns wait for TCK-20261004-PERF-SCENARIO-MIXED-STATE-SPAWN-COLLISION. Step 6: replace docs/observability/baselines/* with T03-format records and point compare-sweep at them. Promotion goes through T05's tool. Depends on T03, T05, T07 and X1. This replaces the pre-DEV-017 baselines that are currently incomparable.

Source concern IDs: C6.

## Scope
- Recapture the three tests/perf/baselines/simq_corpus_*.json files and the *_local/*_concurrent files as benchmark-identity schema records under the canonical variants (identity.contract.signal_contract=canonical, provisional label, all-NORMAL mode_sequence), promoted through tools/perf/baseline_lifecycle.py
- Before replacing each *_local file, run pytest tests/perf/test_perf_regression_baseline.py -m slow against the old file (perf_baseline_policy.md 2.2 step 4)
- Label combat_10_* and fighting corpus-world records WORK_MODEL_V1, and add a pre-hunting label for tactical and combat-heavy records unless the hunting batch merged first
- Defer the mixed_200_local/mixed_200_concurrent reruns until the spawn-collision ticket is done, marking them pending in the ledger
- Run the step 5 evaluate_simq grade-anchor check and record the diff result (commit nothing if empty)
- Replace docs/observability/baselines/latest.json and the matrix files with T03-format records, and point compare-sweep, gate and guide commands at the new path
- Records are nearest-rank (DEV-020): until this rerun, check_perf_regression.py's per-phase p95 against the old-method files is more lenient. Correct DEV-020 consequences (1) and (3) in docs/guidelines/intentional_divergences.md, which name PERF-M2-T05 as the re-recorder: T05 builds the promotion tool and this ticket re-records (perf-planner review of #483)
- Update the baseline_invalidation_ledger.md §3/§5 status column for steps 1, 2, 3, 5 and 6, and mark step 4 as owned by the behavioural 5k rebaseline ticket

## Out of Scope
- Step 4: baseline_5k.json (TCK-20261007-BEHAVIORAL-5K-REBASELINE-AFTER-THE-STARVATION-CHAIN-LANDS)
- mixed_200_* reruns before the spawn-collision fix lands
- WORK_MODEL_V2 / combat_engagement cost accounting
- Making any check blocking (OD-8)
- Changing tripwire or capacity semantics (PERF-M2-T03/T04)

## Acceptance Criteria
- [ ] The three tests/perf/baselines/simq_corpus_*.json files and the non-mixed *_local/*_concurrent files are benchmark-identity schema records, each with identity.contract.signal_contract=canonical, a provisional label and an all-NORMAL mode_sequence, and each promotion recorded before and after identities via tools/perf/baseline_lifecycle.py
- [ ] Every combat_10_* record and every fighting corpus-world record carries a WORK_MODEL_V1 label. Tactical and combat-heavy records also carry a pre-hunting label unless the hunting batch merged before the capture commit.
- [ ] mixed_200_local.json and mixed_200_concurrent.json are unchanged unless TCK-20261004-PERF-SCENARIO-MIXED-STATE-SPAWN-COLLISION is in done/, and the ledger status column lists them as pending until then
- [ ] docs/observability/baselines/latest.json and the matrix files are replaced by T03-format records. Running `python3 -m src compare-sweep` against the replacement gives a tick-cost verdict, not 'baseline incomparable', and tests/integration/observability/test_baseline_comparison_flow.py passes.
- [ ] baseline_invalidation_ledger.md §3/§5 status is updated for steps 1, 2, 3, 5 and 6, step 4 names its owning ticket, and the step 5 evaluate_simq diff result is recorded

## Related Tickets
- TCK-20261010-PERF-M2-T02B-RECORD (done, #483: renamed contract.determinism to identity.contract.signal_contract; DEV-020)
- TCK-20261009-PERF-M1-T05-BASELINE-INVALIDATION-LEDGER
- TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE
- TCK-20261007-BEHAVIORAL-5K-REBASELINE-AFTER-THE-STARVATION-CHAIN-LANDS
- TCK-20261004-PERF-SCENARIO-MIXED-STATE-SPAWN-COLLISION
- TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA
- TCK-20261004-MEASUREMENTS-TAKEN-VIA-A-NON-RUNNING-WORLD-DEFINITION

## Related Docs
- docs/performance/baseline_invalidation_ledger.md
- docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md
- docs/performance/perf_baseline_policy.md
- docs/performance/benchmark_identity_schema.md
- docs/engine/performance_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/perf/profiles.py
- src/cli/entry.py
- src/observability/reporting/baseline_comparator.py
- src/observability/reporting/sweep_report.py
- tools/bench_corpus_world.py
- tools/perf/run_benchmarks.py
- tools/evaluate_simq.py
- tools/perf/check_perf_regression.py
- docs/performance/baseline_invalidation_ledger.md
- docs/observability/baselines/latest.json
- docs/observability/baselines/matrix_full.json

## Assumptions / Open Questions
- Lift boundary (roadmap RPG-core gate item 8, owner 2026-10-09): `src/` edits are limited to `src/perf/bench_harness.py`, `src/perf/profiles.py`, `src/perf/long_run_harness.py`, new `src/perf/benchmark_record.py`, `src/observability/reporting/baseline_comparator.py` and `sweep_report.py`. Any other `src/` path listed under Related Code Areas is read-only here; editing it needs a new owner lift.
- Blocked until PERF-M2-T07 (canonical profiles), PERF-M2-T05 (baseline_lifecycle.py), PERF-M2-T03 (record format) and X1 (TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE) land
- The mixed_200_* reruns need a partial-completion path or a follow-up split, because the spawn-collision ticket is open
- If the hunting batch lands after T08, tactical and combat records need a later rerun
- Captures are host-dependent and rely on hardware-class identity (certification_contract.md §3)
- Step 6 may need a code change if T03 records differ in shape from the legacy format. `baseline_comparator.py` and `sweep_report.py` are in the OD-8 lift; `src/cli/entry.py` is **not**. If entry.py must change, stop and ask the owner for a lift first.
- T06 depends on this ticket, so delays block P1 publication

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
