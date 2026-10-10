---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261010-PERF-M2-T02B-RECORD
phase: done
date: 2026-10-09
tags: [performance, benchmarking, schema, determinism]
---

# TCK-20261010-PERF-M2-T02B-RECORD

## Title
PERF-M2-T02b: Schema adoption with a typed BenchmarkRecord and compare()

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add a typed, frozen BenchmarkRecord (schema 1.0) in a new src/perf/benchmark_record.py. It carries revalidation fields R-1 to R-5: signal_contract, work_model_version and cost_accounting_version are blocking, hash_scheme is an enum, and the debt wording is dropped. Also add an identity collector and compare(base, head, thresholds) -> Outcome that implements benchmark_identity_schema.md §4 with PASS/REGRESSION/INCONCLUSIVE/NOT_APPLICABLE plus a reason. Per OD-3, an excursion is REGRESSION under canonical and INCONCLUSIVE under live_bounded. compare() must not depend on perf-only fields, so the RPG gate report can reuse it later. BenchHarness emits a record next to its dict. Percentiles are nearest-rank (OD-1), the detected hardware class replaces the hard-coded CLASS_A (OD-4), and raw samples follow OD-6. In the schema doc, remove the 'provisional design draft' banner and write the decisions in. Gate behaviour does not change. The src/ lift covers only the listed perf/observability files and no core files. This is the foundation that T03, T04, T05, T07, T08 and X1 all depend on. Today nothing in src/ provides BenchmarkRecord or compare().

Source concern IDs: C1.

## Scope
- Create src/perf/benchmark_record.py with a frozen BenchmarkRecord (schema_version '1.0') and to_dict()/from_dict() serialization, including contract.signal_contract, contract.work_model_version, result.cost_accounting_version (all blocking) and validity.hash_scheme as an enum {flat-sha256-v1, flat-sha256-v2} that blocks only when both sides carry a hash
- Define the cost_accounting_version source as a constant in benchmark_record.py tied to DEV-017. No engine edit (OD-8).
- Add an identity collector that fills the §3.1 identity fields and gives an explicit, documented representation for unknown values (content_hash, builder_version, cpu_model, det_port_tier, observer.level, build_flavor), with a defined comparability policy for unknown == unknown
- Add compare(base, head, thresholds) -> Outcome(state, reason), generic over identity fields: blocking-field mismatch, a missing base, a MAJOR schema_version mismatch, or a missing cost_accounting_version gives INCONCLUSIVE with the field named. A head-side runtime_mode excursion against an all-NORMAL base gives REGRESSION under canonical and INCONCLUSIVE under live_bounded (OD-3).
- Change BenchHarness._calculate_stats in src/perf/bench_harness.py to nearest-rank ceil(q*n), record protocol.percentile_method = 'nearest_rank', and emit a BenchmarkRecord alongside the unchanged result dict. The tripwire record embeds raw tick_wall_ms samples, and capacity records use a {uri, sha256} pointer (OD-6).
- Replace the hard-coded HardwareClass.CLASS_A in src/perf/profiles.py make_perf_profile() with HardwareClassifier.detect_class() from src/certification/hardware.py. A declared class that does not match the detected one compares INCONCLUSIVE (OD-4).
- Rewrite docs/performance/benchmark_identity_schema.md: remove the provisional banner, write in R-1..R-5 and OD-1/3/4/6, reconcile the §4 runtime_mode_sequence rule with OD-3, and drop the §7 debt wording
- Update the parity ledger (docs/parity_ledger/infrastructure.yaml) and, if needed, docs/guidelines/intentional_divergences.md for the now-binding schema contract

## Out of Scope
- Any change to gate pass/fail behaviour or making any perf check blocking (OD-8)
- Edits to core files (state.py, apply.py, pipeline.py, kernel.py) or adding a cost_accounting_version constant in src/engine/
- Canonical profile variants (PERF-M2-T07)
- Tripwire paired comparison and retiring check_perf_regression.py (PERF-M2-T03)
- capacity_run tool and long_run_harness.py percentile migration (PERF-M2-T04)
- Baseline promotion/lifecycle tooling (PERF-M2-T05) and rerunning committed baselines (PERF-M2-T08)
- Deleting src/perf/regression_gate.py. Record a disposition only; the file is outside the OD-8 lift, so removing it needs its own owner lift

## Acceptance Criteria
- [x] src/perf/benchmark_record.py defines a frozen BenchmarkRecord with schema_version == '1.0'. Assigning to any field raises, and to_dict()/from_dict() round-trips to an equal record.
- [x] BenchmarkRecord carries contract.signal_contract, contract.work_model_version and result.cost_accounting_version. validity.hash_scheme accepts only flat-sha256-v1/flat-sha256-v2 and rejects any other value at construction.
- [x] compare(base, head, thresholds) returns Outcome PASS for identical identities within threshold and REGRESSION when head latency exceeds the threshold
- [x] compare() returns INCONCLUSIVE, with the reason naming the field and never PASS, when any of seed, profile_hash, hardware_class, percentile_method or work_model_version differs, when base is None, when the MAJOR schema_version differs, or when cost_accounting_version is missing
- [x] With a head-side non-NORMAL runtime_mode_sequence against an all-NORMAL base, compare() returns REGRESSION when the signal contract is canonical and INCONCLUSIVE when it is live_bounded
- [x] A unit test shows that compare() reads no perf-only result fields beyond identity and threshold inputs: a record with extra or absent perf-only keys gives the same outcome
- [x] BenchHarness.run_benchmark returns its existing dict keys unchanged and also emits a BenchmarkRecord. For samples [1..20], nearest-rank gives p95 == 19 (not 20), and protocol.percentile_method == 'nearest_rank'.
- [x] make_perf_profile() takes hardware_class from HardwareClassifier.detect_class() (monkeypatched in a test to a non-CLASS_A value), and no hard-coded CLASS_A remains in src/perf/profiles.py
- [x] The tripwire record embeds tick_wall_ms raw samples, and the identity collector represents an unavailable field with the documented unknown sentinel
- [x] docs/performance/benchmark_identity_schema.md no longer contains the 'provisional design draft' banner, and its §4 runtime_mode_sequence rule matches OD-3
- [x] Existing tests in tests/perf/test_bench_harness.py, tests/unit/perf/test_perf_regression_gate.py, tests/perf/test_perf_regression_baseline.py and tests/tools/test_corpus_perf_baseline.py pass, and check_perf_regression.py per-phase thresholds give the same pass/fail as before — **partly verified:** the four named test files pass; the same-pass/fail clause is NOT verified on committed data. Nearest-rank can only lower a head p95 against old-method baselines, so the check can only become more lenient (DEV-020), not stricter

## Related Tickets
- TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA
- TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE
- TCK-20261004-PERF-REGRESSION-CHECK-NO-SILENT-PASS
- TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS
- TCK-20261004-PERF-LATEST-JSON-SINGLE-WRITER
- TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE

## Related Docs
- docs/performance/benchmark_identity_schema.md
- docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md
- docs/plans/design_enhancement/performance_optimization/rpg_core_handoff.md
- docs/engine/performance_contract.md
- docs/engine/contracts/certification_contract.md
- docs/parity_ledger/infrastructure.yaml
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261010-PERF-M2-T02B-RECORD/ (plan.md, investigation.md, test_plan.md)

## Related Code Areas
- src/perf/bench_harness.py
- src/perf/profiles.py
- src/perf/regression_gate.py
- src/perf/long_run_harness.py
- src/certification/hardware.py
- src/config/profiles.py
- src/engine/work_units.py
- docs/performance/benchmark_identity_schema.md

## Assumptions / Open Questions
- Lift boundary (roadmap RPG-core gate item 8, owner 2026-10-09): `src/` edits are limited to `src/perf/bench_harness.py`, `src/perf/profiles.py`, `src/perf/long_run_harness.py`, new `src/perf/benchmark_record.py`, `src/observability/reporting/baseline_comparator.py` and `sweep_report.py`. Any other `src/` path listed under Related Code Areas is read-only here; editing it needs a new owner lift.
- The OD-8 owner lift for bench_harness.py, profiles.py, long_run_harness.py, benchmark_record.py, baseline_comparator.py and sweep_report.py is granted before implementation
- Switching to nearest-rank percentiles may shift p50/p95/p99 values in the harness dict and in committed tests/perf/baselines/*.json comparisons. Confirm that the gate outcome does not change.
- cost_accounting_version lives as a constant in benchmark_record.py tied to DEV-017. X1 depends on the field name chosen here.
- detect_class() makes PERF_* profiles host-dependent and may change governor or budget behaviour on smaller hosts
- Whether to deprecate src/perf/regression_gate.py (a second comparison path with no consumer) or leave it for T03 is decided and recorded in this ticket
- graphify query was unavailable during investigation, so the code-structure cross-check relied on search_docs and targeted reads

## Implementation Notes
- Decisions where the ticket left a choice are in `agent-working/stored_artifacts/TCK-20261010-PERF-M2-T02B-RECORD/plan.md`. The ones a reviewer should look at: the record is on `BenchHarness.last_record`, not in the result dict (so committed baselines and their readers are untouched); the contract field is `contract.signal_contract` with values `live`/`canonical` (the draft's `determinism` is replaced; `live_bounded` in OD-3 means `live`); `samples` embeds `tick_wall_ms` and `tick_compute_ms`; `unknown` against `unknown` is comparable and listed as unverified in a `PASS` reason.
- **Disposition of `src/perf/regression_gate.py`** (the ticket asks for it to be decided and recorded): retire, replaced by `compare()`. It has no consumer and is a second comparison path. It is not deleted here because it is outside the OD-8 lift; deletion needs its own owner lift (recorded in the schema doc §6).
- **Risk found, not in the ticket:** with the hard-coded `CLASS_A` gone, `OptimizationProfileResolver` returns `LOW_MEMORY` for a `PERF_*` run on a `CLASS_C` host (under 4 cores or 8 GB). This host is `CLASS_B` and no `CLASS_C` run was made. Recorded in `DEV-020`; the CI tripwire (`PERF-M2-T03`) needs to know the runner's class.
- Nearest-rank can only lower a percentile, so `check_perf_regression.py`'s per-phase p95 check is more lenient against old-method baselines (`DEV-020`). Not re-run through the old method on committed data.
- The code-health ratchet is strict for new code. The first version had 9 new and 2 worse violations; the final has 0 new and 0 worse, and the baseline file was not touched. Several `bench_harness.py` baseline rows now read below their ceilings (`tighten` belongs to the codebase domain).
- `docs/performance/wall_clock_inventory.{json,md}` regenerated with its own tool: the five new reads are measurement-side.

## Test Summary
- New: `tests/unit/perf/test_benchmark_record.py`, `test_bench_harness_record.py`, `test_perf_profiles_canonical.py`.
- Run together with `tests/perf/test_bench_harness.py`, `test_profiler_integrity.py`, `test_perf_regression_baseline.py`, `tests/unit/engine/test_signal_contract_foundation.py`, `tests/tools/test_corpus_perf_baseline.py`, `tests/tools/test_perf_inventories_committed_in_sync.py`: 152 passed.
- Wider: `tests/tools -k "perf or baseline"` and `tests/unit/perf` passed in an earlier run (192 and 122 passed, 4 skipped); the only failure in it was the wall-clock inventory, fixed by regeneration.
- `python3 -m codebase.health check`: 0 new, 0 worse. mypy on `src/`: no errors in the three edited files. Parity-ledger schema gate: OK. `tests/docs` + `tests/codebase -k "parity or diverg or frontmatter or registry"`: 123 passed.
- Not run: the full suite (project rule), a `CLASS_C` host, a timing comparison before and after.

## Files Changed
- Code: `src/perf/benchmark_record.py` (new), `src/perf/bench_harness.py`, `src/perf/profiles.py`.
- Tests: `tests/unit/perf/test_benchmark_record.py`, `test_bench_harness_record.py`, `test_perf_profiles_canonical.py` (all new).
- Docs: `docs/performance/benchmark_identity_schema.md`, `docs/performance/wall_clock_inventory.json`, `docs/performance/wall_clock_inventory.md`, `docs/guidelines/intentional_divergences.md` (DEV-020), `docs/parity_ledger/infrastructure.yaml` (INFRA-430).
- Tickets and artifacts: this ticket, `TCK-20261010-PERF-M2-T07-CANONICAL-VARIANTS`, `agent-working/stored_artifacts/TCK-20261010-PERF-M2-T02B-RECORD/`.

## Completion Summary
Schema 1.0 is binding and implemented: a frozen `BenchmarkRecord` with the revalidation fields R-1 to R-5, an identity collector, and `compare(base, head, thresholds)` returning PASS, REGRESSION, INCONCLUSIVE or NOT_APPLICABLE with a reason, including the OD-3 excursion split. `BenchHarness` emits a record on `last_record` and its percentiles are nearest-rank; `PERF_*` profiles take a detected hardware class. The schema doc lost its provisional banner and carries the decisions. No gate behaviour changed and no check became blocking. Left open and said so: no `CLASS_C` run, `regression_gate.py` not deleted (outside the lift), `long_run_harness.py` not migrated (T04), and `compare()` is not yet called by any gate (T03 to T05).
