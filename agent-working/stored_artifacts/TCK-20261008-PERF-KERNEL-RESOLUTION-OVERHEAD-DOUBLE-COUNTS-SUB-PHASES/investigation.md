---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261008-PERF-KERNEL-RESOLUTION-OVERHEAD-DOUBLE-COUNTS-SUB-PHASES
date: 2026-10-08
tags: [performance, engine, determinism]
---

# Investigation: TCK-20261008-PERF-KERNEL-RESOLUTION-OVERHEAD-DOUBLE-COUNTS-SUB-PHASES

Tree: `origin/main` `28e304cbe` plus the planner's ticket commit `a08ae92d0`.

## Cause
`Kernel._tick_once_inner` (`src/engine/kernel.py:431-435`) sets `resolution_overhead = resolution wall time - sub_sum`, where
`sub_sum` adds only a hand-kept whitelist of `_phase_costs` keys (`res_*`, `trust_validity`, `contracts_production`, `locomotion`,
`interaction`, `governance_ecology`, `economy`, `final_integrity`). `AuthoritativeApplyPipeline.refine` also records
`combat_engagement`, `cooperation`, `faction_*`, `information_*`, `memory_update`, `self_model` and others. Their time stays inside
`resolution_overhead` and is also stored under their own key, and `_final_compute_ms = sum(self._phase_costs.values())`
(`kernel.py:463`) counts both.

## Evidence
- movement scenario, 120 entities, one tick, fake nothing (real clock): wall 76.7 ms, `sum(_phase_costs.values())` 121.6 ms;
  `resolution_overhead` 55.4 ms against `combat_engagement` 44.6 ms (about 10.8 ms of the rest is the other unlisted keys).
- idle, n=1000, cProfile: `combat_engagement` 4,852 ms, `resolution_overhead` 4,958 ms.
- Where the numbers go: `tick_compute_ms` (the previous tick's `_final_compute_ms`) -> `ResourceGovernor` thresholds (1.5 / 1.0 / 0.7 x budget),
  the rolling average, `PhaseBudgetGovernor` compaction (0.8 x budget), the end-of-tick report-only overrun check
  (`kernel.py:466-470`), `RuntimeStatus.signal_history` and every perf report.

## Where the sub-phase keys come from (no pipeline.py edit needed)
`_phase_resolution` merges `refined_update.sub_phase_costs` into `_phase_costs` (`kernel.py:659-660`) and ends with
`self._current_update = refined_update`. `_current_update` is cleared only at advancement, so after `_phase_resolution()` returns the
kernel can read exactly the sub-phase keys the pipeline recorded, with no whitelist and no `pipeline.py` change.

## Second finding: `_phase_costs` is never cleared
`self._phase_costs = {}` is set once (`kernel.py:244`). A key a tick does not record keeps its old value. Refine writes its full `costs`
dict every tick, so today this does not bite, but the sum is only correct while that stays true. Not changed here (out of scope);
the sum test runs two ticks so a regression is visible.

## Consumers of the inflated numbers (for PERF-M1-T05)
Files that mention `resolution_overhead` or record phase-cost totals: `tests/perf/baselines/simq_corpus_{frontier_extended,crowded_frontier,frontier_marches}.json`,
`docs/observability/baselines/*.json` (matrix_full, latest and the per-scenario files), `tests/perf/test_perf_metropolis.py`,
`docs/performance/performance_clause_inventory.md`, `docs/plans/.../performance_m4_baseline_gate_a_epic.md`. The baselines are recorded
timing, not asserted equalities; they are listed as "incomparable for tick-total comparisons" in the ticket.
