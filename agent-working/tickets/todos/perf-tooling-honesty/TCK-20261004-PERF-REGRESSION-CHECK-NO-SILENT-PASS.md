---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-PERF-REGRESSION-CHECK-NO-SILENT-PASS
phase: open
date: 2026-10-04
tags: [performance, benchmarking]
---

# TCK-20261004-PERF-REGRESSION-CHECK-NO-SILENT-PASS

## Title
`check_perf_regression.py`: refuse to compare runs of different length or profile, and stop passing when nothing was compared

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Finding 3 of `docs/performance/benchmark_identity_schema.md` §1 (row F6). `tools/perf/check_perf_regression.py` compares each `tests/perf/baselines/<name>.json` with `reports/perf/<name>.json` and has three defects:
- It never checks that the two runs are comparable. The committed baselines were taken at 20 or 1000 sample ticks, and a report can have any length or profile.
- A missing report is a warning followed by a skip.
- With zero scenarios checked it prints "PASSED" and exits 0.

The tool is not wired into CI, Make or any test (`docs/performance/performance_clause_inventory.md`), but `tools/perf/perf_ci.py` calls it, and a silent pass is exactly the defect the M2 regression-signal policy forbids. This ticket fixes the tool's own honesty. It does not wire it in or choose its thresholds.

## Scope
1. Before comparing a scenario, check `profile` and `sample_ticks` on both sides, plus `warmup_ticks` if both carry it. A mismatch or missing field makes the scenario *not comparable*. Print the field and both values, and do not compare it
2. A missing report for a baseline also counts as not comparable, not as a silent skip
3. Outcome and exit code:
   - any regression → `FAILED`, exit 1;
   - no regression but at least one scenario not comparable, or zero compared → `NOT COMPARABLE`, exit 2;
   - every baseline compared with no regression → `PASSED`, exit 0.

   Print the counts (compared, not comparable, regressed). Keep the thresholds and the improvement messages unchanged
4. Guard the reads: a baseline or report missing `tick_ms.avg` or `mem_rss_mb.max` makes the scenario not comparable, instead of raising `KeyError`
5. `tools/perf/perf_ci.py` runs the checker with `check=True`. Make sure exit 2 is reported as "not comparable", not as a crash. Make the smallest change that does it
6. Tests, in `tests/tools/test_check_perf_regression.py` (new). Build baseline and report directories under `tmp_path` and `chdir` into it (or parametrize the paths if you make them arguments); never run a benchmark. Cover:
   - all matching → exit 0;
   - a regression → 1;
   - a `sample_ticks` mismatch → 2 with the field named;
   - a profile mismatch → 2;
   - a missing report → 2;
   - zero baselines with reports → 2;
   - a missing key → 2, not an exception.
7. Register the new owner: add `"check_perf_regression.py": "tests/tools/"` to `_TOOLS_PERF_BASENAME_MAP` in `tools/gate_checks/test_scope_coverage_static.py`, and update the `tools/perf/*.py` row in `.claude/agents/test-scoper.md` to match (move the module from the no-dedicated-test list to the `tests/tools/` overrides). If `perf_ci.py` gains a test, do the same for it. Update any test pinning either list
8. Add one line under §1 finding 3 and in the F6 row of `benchmark_identity_schema.md`: "fixed by this ticket", with what changed. Do not edit `performance_contract.md`: its §5 sentence about this tool's thresholds stays true

## Out of Scope
- Changing any threshold, or wiring the tool into CI, Make or a test lane (`PERF-M2-T03`)
- Running a benchmark or committing anything under `reports/`
- Any edit under `src/` or to `tests/perf/baselines/`
- The live tripwire `tests/perf/test_perf_regression_baseline.py`: it has the same length mismatch, but fixing it means re-baselining, which waits for the entry gate

## Acceptance Criteria
- [ ] The checker never prints `PASSED` or exits 0 unless every baseline was compared and none regressed
- [ ] Length and profile mismatches are reported as not comparable, naming the field
- [ ] Exit codes 0, 1 and 2 behave as specified, and the tests prove each
- [ ] `pytest tests/tools/test_check_perf_regression.py tests/tools/test_test_scope_coverage_static.py tests/tools/test_tools_orphan_check.py tests/static -q` passes
- [ ] `git diff` touches no file under `src/`, `reports/` or `tests/perf/baselines/`

## Related Tickets
- TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA (finding 3, row F6)
- TCK-20261003-PERF-M2-CLAUSE-INVENTORY (recorded the tool as unwired)

## Related Docs
- `docs/performance/benchmark_identity_schema.md` §1, §4
- `docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md` ("Regression-signal policy")

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/perf/check_perf_regression.py`, `tools/perf/perf_ci.py`, `tools/gate_checks/test_scope_coverage_static.py`, `.claude/agents/test-scoper.md`

## Assumptions / Open Questions
- Owner approved this tools-only batch on 2026-10-04 while the entry gate and the `src/` freeze hold.
- Exit code 2 is a local convention for this unwired tool. `PERF-M2-T03` replaces it with the contract's outcome vocabulary.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

