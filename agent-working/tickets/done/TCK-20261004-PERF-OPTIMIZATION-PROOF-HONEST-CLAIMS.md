---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS
phase: done
date: 2026-10-04
tags: [performance, benchmarking]
---

# TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS

## Title
Optimization proof report: no invented baseline values, no comparison across mismatched identity, and no conclusion text that the data didn't produce

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Finding 1 of `docs/performance/benchmark_identity_schema.md` §1 (row F9). `tools/release/generate_optimization_proof.py` has three defects.
1. It fills in missing baseline data: `base.get("compute_tps", base.get("avg_tps", 1.0))`, and the same for p95 and peak RSS (lines ~102-104). A missing scenario or key becomes `1.0`, and the "speedup" becomes the raw TPS.
2. It compares across identities without checking. It runs every scenario under `PROD_DEFAULT`/`PROD_LARGE` with 50 sample ticks (10 in `--quick`), but `reports/perf/baseline.json` is produced from `run_perf_baseline.py`, which runs the same scenario names under `PERF_2GB_LOCAL`/`PERF_4GB_CONC` at its own tick counts. As configured today, none of its five comparisons is like for like, and nothing says so.
3. Its markdown states conclusions as fixed text whatever the data shows: "Across all five benchmark scenarios, the engine demonstrates consistent speedups and reduced tick latency", and "executed under strict isolation … preventing measurement jitter".

Under the RPG-core entry gate, any number this tool produces is provisional, and the report must say so.

## Scope
1. **Comparability check per scenario.** Before computing ratios, compare the baseline entry with the current run on scenario presence, `profile` (name), `sample_ticks`, and, where both records carry it, `warmup_ticks`. Any difference or missing field makes the scenario *not comparable*. Record it with `"status": "not_comparable"` and a `reason` naming the field and both values, and give it no `speedup_x` or `latency_reduction_x`. A comparable scenario gets `"status": "compared"`. Use the field names of the provisional schema (`docs/performance/benchmark_identity_schema.md` §3) where it names one. Do not import from that document or implement the schema
2. **No defaults for measured values.** Remove the `1.0` fallbacks. A missing TPS, p95 or RSS on either side makes the scenario not comparable, with a reason. A zero or negative divisor does too, instead of the `1.0` fallback on the ratio lines
3. **Baseline shape check.** If `baseline.json` is not a non-empty dict of dicts keyed by scenario name, exit non-zero with a clear message before running anything. This is the reader-side counterpart of `TCK-20261004-PERF-LATEST-JSON-SINGLE-WRITER`
4. **Report text from data only.**
   - Delete the fixed "Key Takeaway" and "strict isolation … preventing measurement jitter" sentences.
   - Replace the summary with computed facts: how many scenarios were compared and how many were not comparable (with reasons); for compared ones, the min and max speedup, and how many got faster or slower.
   - The audit section states only what the code actually set: profile per scenario, seed, warmup and sample ticks, `quick_test`, the replay and frame-pacing flags.
   - The opening lines say every number in it is provisional under the RPG-core entry gate, and that it is not a capacity claim.
   - Keep "Optimized" and "Baseline" as column labels.
5. **JSON output.** Add `metadata.provisional: true` and per-scenario `status`/`reason`. Keep existing keys for compared scenarios so current readers don't break
6. **Exit status.** If no scenario is comparable, `run_proof` still writes both reports, and the `__main__` entry point exits non-zero. A partial result exits 0
7. **Tests.** Add `tests/perf/test_optimization_proof_claims.py`, not marked `slow`. Patch `BenchHarness` (and the scenario builders, if they are expensive) with a stub returning fixed harness dicts, and point the module's report paths at `tmp_path`. Never run the engine. Cover:
   - a matching scenario is compared and its ratios are computed from the data;
   - a profile mismatch is not comparable, with a reason;
   - a `sample_ticks` mismatch is not comparable;
   - a missing baseline scenario is not comparable, not 1.0;
   - a missing key is not comparable;
   - a non-dict or empty baseline exits before running;
   - the markdown contains neither removed sentence, contains the provisional label, and its counts match the JSON;
   - all-not-comparable gives a non-zero exit from the entry point.
   
   Update `tests/perf/test_optimization_proof_report.py` (slow, skipped without a baseline) so its assertions match the new shape (`speedup_x` only on compared scenarios). Do not run it: it executes real benchmarks
8. **Docs.**
   - Add one line under §1 finding 1 and in the F9 row of `benchmark_identity_schema.md`: "fixed by this ticket", with what changed.
   - If `docs/performance/` or `docs/engine/certification*` describes this report's conclusions as evidence, correct that sentence. Find it with `grep -rn optimization_proof docs/`.
   - Check `docs/optimization_audit_ledger.md` and `docs/parity_ledger/infrastructure.yaml` for entries that cite this report as proof. Update their evidence wording to say the report is provisional, and list each one in Implementation Notes

## Out of Scope
- Changing `SCENARIO_CONFIGS` (profiles, tick counts, scenarios) to make comparisons line up. Record in Implementation Notes what alignment would require, and leave the choice to perf-planner
- Running the proof, a benchmark or a baseline for real, or committing anything under `reports/`
- Any edit under `src/`, including `BenchHarness` or the percentile method (finding 4 waits for the gate)
- Adopting the full provisional schema, or the `REGRESSION`/`INCONCLUSIVE` outcome vocabulary (that is `PERF-M2-T03`/`T04`)

## Acceptance Criteria
- [x] No `1.0` (or other) fallback stands in for a measured value anywhere in `generate_optimization_proof.py`
- [x] Every scenario in the JSON output is `compared` or `not_comparable` with a reason; ratios exist only for `compared`
- [x] The two fixed-text claims are gone; every summary statement is computed from the comparison data, and a test checks the counts against the JSON
- [x] The report says, in its opening lines, that it is provisional and not a capacity claim
- [x] `pytest tests/perf/test_optimization_proof_claims.py tests/tools/test_test_scope_coverage_static.py tests/static -q` passes in well under a minute, with no benchmark executed
- [x] Each ledger or doc sentence that cited the report as proof is corrected or listed with a reason
- [x] No file under `reports/` or `data/runs/` is committed; `git diff` touches no file under `src/`

## Related Tickets
- TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA (finding 1, row F9)
- TCK-20261004-PERF-LATEST-JSON-SINGLE-WRITER (writer side; land it first)
- TCK-20260518-OPTIMIZATION-PROOF-REPORT (created the report)

## Related Docs
- `docs/performance/benchmark_identity_schema.md` §1, §3, §4
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md` (RPG-core stability entry gate)
- `docs/optimization_audit_ledger.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260518-OPTIMIZATION-PROOF-REPORT/`

## Related Code Areas
- `tools/release/generate_optimization_proof.py`, `tests/perf/test_optimization_proof_report.py`, `tools/perf/run_perf_baseline.py` (read only)

## Assumptions / Open Questions
- Owner approved this tools-only batch on 2026-10-04 while the entry gate and the `src/` freeze hold.
- Test owner: `tools/gate_checks/test_scope_coverage_static.py` already maps `generate_optimization_proof.py` to `tests/perf/`, which is where the new test goes. No map change is needed.

## Implementation Notes
- `generate_optimization_proof.py` now has pure `compare_scenario()` and `summarize()`; `run_proof()` reuses `tools.perf.perf_baseline.validate_latest` for the baseline shape check (the import is stdlib-only, no cost or cycle) and exits 1 before building any harness. `main()` returns 1 when no scenario was compared; both reports are still written. JSON adds `metadata.provisional`, `metadata.run_flags`, `metadata.seeds` (read from the builder's default with `inspect`; null when not determinable), per-scenario `status`/`reason`, and a top-level `summary`. Ratios exist only on compared scenarios.
- **As configured, every scenario is not_comparable** (profile): the proof uses PROD_DEFAULT/PROD_LARGE, the baseline run uses PERF_2GB_LOCAL/PERF_4GB_CONC. That is the intended honest result.
- **What alignment would take** (left to perf-planner; `SCENARIO_CONFIGS` unchanged): same profile names on both sides; same warmup (proof 20, baseline run 10) and flags (proof sets no_replay and no_frame_pacing, baseline run uses defaults); and same workload. **New finding:** `RESOURCE_1000` is built with 700 entities and 300 nodes in the proof but 1000 and 500 in `run_perf_baseline.py`. The comparison cannot see that, because the harness dict carries no workload cardinality, so a matching profile and tick count would still not make it like for like. Fixing that needs cardinality in the result record (`workload.entity_count` in the provisional schema) or aligned counts.
- Ledgers and docs: `docs/optimization_audit_ledger.md` and `docs/parity_ledger/infrastructure.yaml` have no entry citing this report; `docs/plans/scripts_tools_governance_epic.md` names the generator without presenting its output as evidence; `docs/archive/profiling_performance/perf_plan_v2.md` is archived and untouched. Nothing to correct.
- `tests/perf/test_optimization_proof_report.py` (slow) assertions updated to the new shape; not run (it executes real benchmarks).
- Schema doc: `Fixed by` lines under finding 1 and in the F9 row.
- Review follow-up: "compared" means only that profile and sample_ticks matched, so the report now states the limits of its own check. `UNCHECKED_IDENTITY` (workload cardinality as builder kwargs, warmup_ticks, run flags) is written to `metadata.unchecked_identity` and named in the Summary sentence (always shown); each scenario's builder kwargs are recorded under `optimized.workload`. Cardinality is deliberately not part of the comparison rule, because the baseline has nothing to compare it with. Two tests added (20 in the file).

## Test Summary
129 passed in 4.5 s: tests/perf/test_optimization_proof_claims.py (18 new, stub-only, not slow), test_test_scope_coverage_static.py, test_perf_baseline_tool.py, tests/static. No benchmark, baseline or proof was run.

## Files Changed
- tools/release/generate_optimization_proof.py
- tests/perf/test_optimization_proof_claims.py (new), tests/perf/test_optimization_proof_report.py (assertions only)
- docs/performance/benchmark_identity_schema.md (two Fixed-by lines)
- this ticket, its stored artifacts, docs/REGISTRY.yaml, monitoring shards

## Completion Summary
The optimization proof report compares only like with like, defaults nothing, writes its text from the data, and says it is provisional.
