---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261010-PERF-M2-T02B-RECORD
phase: open
date: 2026-10-09
tags: [performance, benchmarking, schema, determinism]
---

# TCK-20261010-PERF-M2-T02B-RECORD

## Title
PERF-M2-T02b: Schema adoption with a typed BenchmarkRecord and compare()

## Status
OPEN

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
- [ ] src/perf/benchmark_record.py defines a frozen BenchmarkRecord with schema_version == '1.0'. Assigning to any field raises, and to_dict()/from_dict() round-trips to an equal record.
- [ ] BenchmarkRecord carries contract.signal_contract, contract.work_model_version and result.cost_accounting_version. validity.hash_scheme accepts only flat-sha256-v1/flat-sha256-v2 and rejects any other value at construction.
- [ ] compare(base, head, thresholds) returns Outcome PASS for identical identities within threshold and REGRESSION when head latency exceeds the threshold
- [ ] compare() returns INCONCLUSIVE, with the reason naming the field and never PASS, when any of seed, profile_hash, hardware_class, percentile_method or work_model_version differs, when base is None, when the MAJOR schema_version differs, or when cost_accounting_version is missing
- [ ] With a head-side non-NORMAL runtime_mode_sequence against an all-NORMAL base, compare() returns REGRESSION when the signal contract is canonical and INCONCLUSIVE when it is live_bounded
- [ ] A unit test shows that compare() reads no perf-only result fields beyond identity and threshold inputs: a record with extra or absent perf-only keys gives the same outcome
- [ ] BenchHarness.run_benchmark returns its existing dict keys unchanged and also emits a BenchmarkRecord. For samples [1..20], nearest-rank gives p95 == 19 (not 20), and protocol.percentile_method == 'nearest_rank'.
- [ ] make_perf_profile() takes hardware_class from HardwareClassifier.detect_class() (monkeypatched in a test to a non-CLASS_A value), and no hard-coded CLASS_A remains in src/perf/profiles.py
- [ ] The tripwire record embeds tick_wall_ms raw samples, and the identity collector represents an unavailable field with the documented unknown sentinel
- [ ] docs/performance/benchmark_identity_schema.md no longer contains the 'provisional design draft' banner, and its §4 runtime_mode_sequence rule matches OD-3
- [ ] Existing tests in tests/perf/test_bench_harness.py, tests/unit/perf/test_perf_regression_gate.py, tests/perf/test_perf_regression_baseline.py and tests/tools/test_corpus_perf_baseline.py pass, and check_perf_regression.py per-phase thresholds give the same pass/fail as before

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
None.

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

## Test Summary

## Files Changed

## Completion Summary
