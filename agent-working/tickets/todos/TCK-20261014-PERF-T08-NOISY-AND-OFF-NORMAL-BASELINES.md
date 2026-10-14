---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES
phase: open
date: 2026-10-14
tags: [performance, benchmarking]
---

# TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES

## Title
Finish the baselines PERF-M2-T08 could not promote: diagnose the intrinsic noise first, then re-record the NOISY and off-NORMAL records

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
PERF-M2-T08 (#591) promoted 5 of 15 records. The other 10 remain legacy references:
- **4 PENDING-NOISY:** `idle_100_local`, `movement_100_local`, `combat_10_local`, `simq_corpus_crowded_frontier`. They stayed above 15% spread even in a quiet window (load 0.6-1.3; `combat_10_local` 96.9%), so the noise is likely intrinsic to the run, not host contention.
- **6 off-NORMAL:** they are handled by `TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION` first.
- **2 promoted only on the retry window** after very wide first windows: `combat_10_concurrent` (137% → 9.6%) and `resource_100_concurrent` (74% → 12.5%). A bimodal path is not ruled out.

## Scope
1. **Diagnose before re-measuring.** From the per-tick samples T08 kept under `--keep-samples`, give each NOISY record and the two retry-promoted records:
   - per-run min, median, p95 and max tick ms;
   - whether the first sampled ticks dominate (warm-up);
   - whether the runs are bimodal (two clusters of averages);
   - whether a GC pause lines up with the outliers (`gc.callbacks`, or `PYTHONMALLOC` stats if needed).
   Do not ask for another quiet window until this analysis says the host is the cause.
2. **Fix the protocol, then re-record.** Pick the smallest change the analysis supports: longer sampling, a warm-up drop, or the median of more runs. It must stay comparable with the nightly tripwire lane for the two declared tripwire scenarios (`idle_100_local` and `movement_100_local` use `tripwire.TRIPWIRE_SCENARIOS`; changing that `RunSpec` is a tripwire change that needs testing-planner's agreement). Record the protocol change in `perf_baseline_policy.md` (P1: the owner approves) and the ledger. Then re-record through `tools/perf/rerun_baselines.py` and promote only through `baseline_lifecycle.py promote`.
3. **Retry-promoted pair:** if the analysis shows they are bimodal, demote or replace the v0001 records through the lifecycle tool, with a cause.
4. **Off-NORMAL records** (`strategic_100_*`, `mixed_200_*`, `simq_corpus_frontier_extended`, `simq_corpus_frontier_marches`): re-measure only after the tick-cost investigation and rpg's fixes, or after an owner decision on a larger profile (option i). Until then they stay "not a baseline under canonical" in the ledger. This ticket closes with them PENDING if that work has not landed. Do not hold the ticket open for it.
5. **`mixed_200` naming:** the state built for 200 has 140 entities. Either rename the record (a new name through the lifecycle tool) or document the count in the scenario docstring and the ledger. Do not change `build_mixed_state`'s output silently.

## Out of Scope
- The tick-cost attribution (`TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION`).
- Any `src/` change outside `src/perf/`.
- A/A calibration of the CI tripwire threshold (dispatched separately after #529 merges; it feeds T06).

## Acceptance Criteria
- AC1: The noise diagnosis for the 4 NOISY plus the 2 retry-promoted records is written up, with the per-run distributions and a named cause per record (warm-up, bimodal, GC, host, or unknown, with what was ruled out).
- AC2: Any protocol change is agreed (testing-planner for the tripwire RunSpec; the owner for the policy paragraph) before the re-record.
- AC3: Every record that meets the 15% rule under the agreed protocol is promoted. The rest stay PENDING with the reason in the ledger.
- AC4: The `mixed_200` naming is resolved.
- AC5: The same resource rule as T08 (one at a time, capped, lead-planner told before any run over about 3 GB).

## Related Tickets
- TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS (#591), TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION, TCK-20261011-PERF-M2-T03B-CI-PAIRED-STEP (#529, tripwire)

## Related Docs
- docs/performance/baseline_invalidation_ledger.md, docs/performance/perf_baseline_policy.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS/ (evidence.md, investigation.md)

## Related Code Areas
- tools/perf/rerun_baselines.py, tools/perf/baseline_lifecycle.py, tools/perf/tripwire.py, src/perf/scenarios.py

## Assumptions / Open Questions
- A1: T08's `reports/perf/t08/*/samples/` per-tick data is still on disk in ~/Work/rpg-perf. If it was cleaned, the diagnosis re-runs the 6 records with `--keep-samples` (seconds each).

## Implementation Notes
(to be filled)

## Test Summary
(to be filled)

## Files Changed
(to be filled)

## Completion Summary
(to be filled)
