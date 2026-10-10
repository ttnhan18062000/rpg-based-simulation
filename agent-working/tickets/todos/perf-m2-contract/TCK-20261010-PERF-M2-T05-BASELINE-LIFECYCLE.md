---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE
phase: open
date: 2026-10-09
tags: [performance, benchmarking, testing, regression]
---

# TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE

## Title
PERF-M2-T05: Baseline and known-debt lifecycle

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Rewrite perf_baseline_policy.md as lifecycle rules that cite testing's shared baseline_change_policy.md. That doc may not exist yet, so this depends on it or on TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS or its policy-doc child. Keep only the perf preconditions: refuse dirty_src and a non-NORMAL sequence, record the before and after identities, and accept a re-baseline that cites a behaviour PR or a divergence id (OD-3). The known-debt ledger is split out to TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER. Add a tools/perf/baseline_lifecycle.py promotion tool, and a test that every tests/perf/baselines/ file is either a schema record or a listed legacy tripwire reference. No src/ change. Depends on T02b. The reason: under the canonical contract a deliberate behaviour change shows up as REGRESSION, so re-baselines need a cited cause, and a missing or incompatible baseline must never silently pass.

Source concern ids: C3.

## Scope
- Rewrite docs/performance/perf_baseline_policy.md as lifecycle rules citing the shared baseline_change_policy.md, keeping only the perf-specific preconditions
- Add tools/perf/baseline_lifecycle.py with a promote command. It refuses dirty_src=true, a non-NORMAL mode_sequence, a missing cost_accounting_version, or no cited cause. It writes a new versioned record without overwriting the prior one and records the before and after identities using T02b field names.
- Add a test that enumerates tests/perf/baselines/*.json and requires each file to be a valid BenchmarkRecord or listed in a legacy-tripwire allowlist (today all 15 files)
- Add tests for the promotion refusals and successful versioned promotion

## Out of Scope
- Any change under src/ (OD-8)
- Making any perf check blocking
- Writing the testing-owned baseline_change_policy.md or extracting the known-reds module, if a testing-owned ticket covers it (coordinate, don't duplicate)
- Rerunning or replacing committed baselines (PERF-M2-T08)
- docs/performance/known_debt_ledger.yaml and its expected_signature format: split out to TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER (2026-10-10), which waits for the shared known-reds module
- Tripwire comparison logic (PERF-M2-T03)

## Acceptance Criteria
- [ ] tools/perf/baseline_lifecycle.py promote exits non-zero with a named reason when the candidate record has engine.dirty_src=true, and leaves tests/perf/baselines/ unchanged
- [ ] promote exits non-zero with a named reason when the candidate's mode_sequence holds any value other than NORMAL, and leaves tests/perf/baselines/ unchanged
- [ ] promote exits non-zero when no cause (ticket, divergence id or behaviour PR) is cited, or when the record lacks cost_accounting_version
- [ ] A successful promotion writes a new versioned record, leaves the prior version file byte-identical, and records the before identity, the after identity and the cited cause
- [ ] A test enumerating tests/perf/baselines/*.json fails when a file is neither a valid BenchmarkRecord nor named in the legacy-tripwire allowlist, and passes on the current tree
- [ ] The ticket's git diff touches no file under src/

## Related Tickets
- TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE
- TCK-20261007-BEHAVIORAL-5K-REBASELINE-AFTER-THE-STARVATION-CHAIN-LANDS
- TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED
- TCK-20261009-SLOW-REGRESSION-OFF-HOUR-AND-SKIP-UNCHANGED-MAIN
- TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION
- TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE
- TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE
- TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS

## Related Docs
- docs/performance/perf_baseline_policy.md
- docs/performance/benchmark_identity_schema.md
- docs/performance/baseline_invalidation_ledger.md
- docs/engine/performance_contract.md
- docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/performance/perf_baseline_policy.md
- tools/test_architecture/slow_regression_report.py
- tools/test_architecture/slow_known_reds.yaml
- tools/perf/perf_baseline.py
- tools/perf/run_benchmarks.py
- tools/bench_corpus_world.py
- src/perf/bench_harness.py
- src/perf/profiles.py
- tests/perf/test_perf_regression_baseline.py

## Assumptions / Open Questions
- Blocked until PERF-M2-T02b lands src/perf/benchmark_record.py
- docs/plans/test_architecture/reference/baseline_change_policy.md does not exist yet. The testing-owned policy doc must land first, or the citation is a forward reference agreed with the testing planner.
- No ticket files exist yet for TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE or TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS. The known-reds logic is still inline in slow_regression_report.py. Coordinate with the testing planner so the module is extracted only once.
- The expected_signature format (regex, scenario+phase key, or clause id) is undecided and must be fixed before tests are written
- The legacy allowlist is a migration ledger that shrinks as T08 reruns replace files

## Implementation Notes
- 2026-10-10 (perf-planner): split. The known-debt ledger scope and its acceptance criterion moved to TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER, which waits for TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE. Do not write an interim known-reds loader in perf. T05 starts now. The policy rewrite cites docs/plans/test_architecture/reference/baseline_change_policy.md as a forward reference (testing-planner agreed the shared policy on #475), labelled "pending" until that doc lands.

## Test Summary

## Files Changed

## Completion Summary
