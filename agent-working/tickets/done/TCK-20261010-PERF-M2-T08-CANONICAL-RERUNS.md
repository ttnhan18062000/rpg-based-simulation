---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS
phase: done
date: 2026-10-10
tags: [performance, benchmarking, regression]
---

# TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS

## Title
PERF-M2-T08: M1 baseline reruns under the canonical variants

## Status
DONE

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
- Note: docs/observability/baselines/latest.json is a perf matrix keyed by profile that `src gate` and `compare-sweep` cannot parse today (pydantic ValidationError, exit 1); the replacement must be a file they can read
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
- [ ] **Partly met.** 5 of the 13 non-mixed records are benchmark-identity schema records (canonical, provisional, all-NORMAL, promoted through `baseline_lifecycle`, before/after identities in each `promotion`): `resource_100_local`, `idle_100_concurrent`, `movement_100_concurrent`, `combat_10_concurrent`, `resource_100_concurrent`. The other 8 are not: 4 PENDING-NOISY (`idle_100_local`, `movement_100_local`, `combat_10_local`, `simq_corpus_crowded_frontier`: spread above 15 % in both windows) and 4 leave NORMAL under canonical (`strategic_100_local`, `strategic_100_concurrent`, `simq_corpus_frontier_extended`, `simq_corpus_frontier_marches`), so `promote` refuses them (contract 3.1). Each is named in the ledger with its measurement. perf-planner accepted this outcome (2026-10-13) and files a follow-up for the leftovers.
- [x] Records carry `WORK_MODEL_V1` (`contract.work_model_version`, set for every record); no pre-hunting label because the hunting batch (#536) is on the measured main (06aa3a20c).
- [x] `mixed_200_local.json` and `mixed_200_concurrent.json` are unchanged and the ledger lists them as PENDING until `TCK-20261004-PERF-SCENARIO-MIXED-STATE-SPAWN-COLLISION` (#544, approved) merges.
- [ ] **Partly met.** `docs/observability/baselines/latest.json` is replaced by a generated `BaselineConfig` and the 14 matrix files and `matrix_full.json` are deleted (deviation from "T03-format records", see Implementation Notes): `python3 -m src compare-sweep` and `python3 -m src gate` exit 0 on it with a tick-cost verdict, not 'baseline incomparable'. `tests/integration/observability/test_baseline_comparison_flow.py` **fails on this loaded VM** (3 of 3 here, and on a clean `origin/main` 06aa3a20c in a scratch worktree: `WARNING != PASS` at line 55, a comparison of real tick timings), but CI collects it (`pytest tests/integration -m "not slow and not extra_slow"`, job `Integration`) and passes on main: run 38434570715, job 115425246123, `1075 passed, 6 skipped, 59 deselected`; it reads neither `latest.json` nor any deleted file (no `docs/observability` path in it). So the acceptance evidence is the Integration job of this branch's own PR run, not a local run (the PR body says so); it is not edited.
- [x] `baseline_invalidation_ledger.md` sections 3.1 to 3.3 and 5 carry the status of steps 1, 2, 3, 5 and 6; step 4 names `TCK-20261007-BEHAVIORAL-5K-REBASELINE-AFTER-THE-STARVATION-CHAIN-LANDS`; the step 5 `evaluate_simq` result is recorded (130 of 630 pillars REGRESS, diff not empty, nothing committed). DEV-020 consequences (1) and (3) are corrected.

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
- agent-working/stored_artifacts/TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS/ (plan, investigation, test_plan, evidence, commands/)

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
- Step 6 deviates from the ticket text (T03-format records): see Implementation Notes.
- Lift boundary (roadmap RPG-core gate item 8, owner 2026-10-09): `src/` edits are limited to `src/perf/bench_harness.py`, `src/perf/profiles.py`, `src/perf/long_run_harness.py`, new `src/perf/benchmark_record.py`, `src/observability/reporting/baseline_comparator.py` and `sweep_report.py`. Any other `src/` path listed under Related Code Areas is read-only here; editing it needs a new owner lift.
- Blocked until PERF-M2-T07 (canonical profiles), PERF-M2-T05 (baseline_lifecycle.py), PERF-M2-T03 (record format) and X1 (TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE) land
- The mixed_200_* reruns need a partial-completion path or a follow-up split, because the spawn-collision ticket is open
- If the hunting batch lands after T08, tactical and combat records need a later rerun
- Captures are host-dependent and rely on hardware-class identity (certification_contract.md §3)
- Step 6 may need a code change if T03 records differ in shape from the legacy format. `baseline_comparator.py` and `sweep_report.py` are in the OD-8 lift; `src/cli/entry.py` is **not**. If entry.py must change, stop and ask the owner for a lift first.
- T06 depends on this ticket, so delays block P1 publication

## Implementation Notes
- **Deviation from the ticket text (step 6), 2026-10-13, approved in perf-planner's review of plan.md:** the ticket says the matrix files and `latest.json` are replaced "by T03-format records". `python3 -m src gate` and `compare-sweep` model-validate a `BaselineConfig` (`baseline_v1`, written by `generate-baseline` from a sweep), which a schema-1.1 `BenchmarkRecord` is not, so `latest.json` is replaced by a generated `BaselineConfig` carrying the current `cost_accounting_version`, and the per-profile matrix files (no consumer, investigation.md section A) are deleted. The acceptance criterion's actual test (the CLI gives a tick-cost verdict, not 'baseline incomparable') is kept.
- Every record is measured 3 times in fresh processes and the median avg is promoted; a spread above 15 % is not promoted and is marked NOISY (perf-planner condition, host is loaded).

## Test Summary
- `tests/unit/perf/test_rerun_baselines.py` (16) and `tests/unit/perf/test_sweep_gate_baseline.py` (3) new; `tests/unit/perf/test_baseline_lifecycle.py` updated (legacy set 15 to 10). Scoped run (`tests/unit/perf`, `tests/static -k "perf or baseline or ci_"`, paths guard, `test_corpus_perf_baseline`, `tests/perf/test_perf_regression_baseline.py`): 304 passed. `-k parity_ledger`: 100 passed.
- `tests/perf/test_perf_regression_baseline.py -m slow` against the old files (policy 2.2 step 4): INCONCLUSIVE "legacy tripwire reference" for both declared scenarios (the old files have no identity); output in `commands/old_file_slow_test.txt`.
- FAIL on this host only: `tests/integration/observability/test_baseline_comparison_flow.py::test_baseline_comparison_and_cli_flow` (3 of 3 here, 1 of 1 on a clean `origin/main`; host-timing comparison); passes in CI on main (run 38434570715, job `Integration` 115425246123). Not changed; this branch's PR run is the acceptance evidence.
- FAIL (reported, not a defect of this ticket): `tools/evaluate_simq.py` exit 1, 130 of 630 pillars REGRESS vs the committed anchors; nothing committed.
- Measurements: 13 records x 3 fresh-process runs, plus the quiet-window retry of 6; peak RSS and wall per run in `evidence.md`; `compare-sweep` and `gate` outputs in `commands/`.

## Files Changed
- New: `tools/perf/rerun_baselines.py`, `tests/unit/perf/test_rerun_baselines.py`, `tests/unit/perf/test_sweep_gate_baseline.py`, `docs/observability/baselines/README.md`, `tests/perf/baselines/{resource_100_local,idle_100_concurrent,movement_100_concurrent,combat_10_concurrent,resource_100_concurrent}.v0001.json`.
- Changed: `tools/perf/baseline_lifecycle.py` (legacy set), `tests/unit/perf/test_baseline_lifecycle.py`, `docs/observability/baselines/latest.json` (replaced), `docs/guides/observability.md`, `docs/guides/simulation.md`, `docs/performance/baseline_invalidation_ledger.md`, `docs/performance/perf_baseline_policy.md`, `docs/guidelines/intentional_divergences.md` (DEV-020), `docs/parity_ledger/infrastructure.yaml` (INFRA-436), this ticket.
- Deleted: the 5 promoted legacy files under `tests/perf/baselines/`; under `docs/observability/baselines/`: 13 per-profile files, `matrix_full.json`, `test_perf_idle_baseline.json`.

## Completion Summary
Measured every non-mixed baseline under the canonical variants (3 fresh-process runs each, median promoted, NOISY above 15 % spread) and replaced 5 of the 15 legacy files with schema records through `baseline_lifecycle promote`. 4 records are PENDING-NOISY (still above 15 % in the one quiet-window retry) and 4 leave NORMAL under the canonical contract (the tick has grown about 12x to 38x since May; a larger-budget canonical profile is an owner decision, not made); the ledger names each and perf-planner files a follow-up. `mixed_200_*` stay PENDING on #544. The sweep-gate baseline `latest.json` is now a generated `BaselineConfig` that `src gate` and `compare-sweep` parse (both exit 0); the 14 consumer-less matrix files are deleted. Step 5 found 130 of 630 SimQ pillars REGRESS (nothing committed). **Known gaps:** `test_baseline_comparison_flow.py` fails on this loaded VM (also on a clean `origin/main`) but passes in CI on main, so its acceptance evidence is the PR's CI run; per-tick latencies of the noisy runs were not kept (`--keep-samples` now exists); all numbers are provisional, from one loaded host, and claim nothing about capacity. Owner gate: new baselines and the deletions need the owner's approval before the push.
