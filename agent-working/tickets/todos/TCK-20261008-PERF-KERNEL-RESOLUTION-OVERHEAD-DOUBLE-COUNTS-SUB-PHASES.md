---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261008-PERF-KERNEL-RESOLUTION-OVERHEAD-DOUBLE-COUNTS-SUB-PHASES
phase: open
date: 2026-10-08
tags: [performance, engine, determinism]
---

# TCK-20261008-PERF-KERNEL-RESOLUTION-OVERHEAD-DOUBLE-COUNTS-SUB-PHASES

## Title
The kernel counts some refine sub-phases twice in tick_compute_ms (combat_engagement, cooperation, faction phases are missing from the resolution_overhead whitelist), so Live runs degrade earlier than their thresholds intend

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by perf-implementer during Phase A step 1 (calibration) of
`TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY`, and verified by perf-planner on `main`
`28e304cbe`.

`Kernel._tick_once_inner` (`src/engine/kernel.py` about 432-435) computes
`resolution_overhead = res_total - sub_sum`. `sub_sum` sums only a whitelist of `_phase_costs` keys: `res_*`,
`trust_validity`, `contracts_production`, `locomotion`, `interaction`, `governance_ecology`, `economy` and
`final_integrity`. The refine pipeline also records `combat_engagement`, `cooperation`, the `faction_*` phases
and others. Those are left out of `sub_sum`, so they stay inside `resolution_overhead` **and** appear under
their own key. `_final_compute_ms = sum(_phase_costs.values())` therefore counts them twice. At idle with
n=1000 (cProfile), `combat_engagement` is about 4.85 s and `resolution_overhead` about 4.96 s.

`_final_compute_ms` becomes `tick_compute_ms`, which `ResourceGovernor._get_indicated_mode` compares with
`max_tick_budget_ms` (PERF-D1 input 1). It also feeds the rolling average, `PhaseBudgetGovernor`, the end-of-tick
report-only overrun check and every perf report. So **Live runs reach DEGRADED and SURVIVAL earlier than their
profile thresholds intend**, and every reported tick cost is overstated by the unlisted sub-phases.

**Owner decision 2026-10-08:** fix it inside Phase A (the core window, gate item 7), in the same batch as the
governor fix. It is a Live behaviour change, recorded as an intentional divergence.

## Scope
1. Compute `resolution_overhead` as the resolution wall time minus **every** sub-phase cost recorded during
   resolution, not a hand-kept whitelist. For example, snapshot the `_phase_costs` keys before `_phase_resolution`
   and subtract every key added or updated during it. Keep the key name `resolution_overhead`.
2. A test that, for a tick with several refine sub-phases, checks that `sum(_phase_costs.values())` equals
   the measured tick wall time within a small tolerance. Use a fake clock, never real timing. The test must fail on
   `main` before the fix. Also test that no sub-phase key's time appears twice.
3. An intentional-divergence entry: with load above the old inflated threshold but below the true one, Live
   runs now stay NORMAL where they used to degrade. Rationale class `Bug Fix`.
4. Check what consumed the inflated numbers:
   - committed perf baselines or reports that record `tick_compute_ms` or phase costs (feed PERF-M1-T05's
     ledger: mark affected baselines rerun or incomparable);
   - tests that drive modes through a fake clock (`test_milestone_b_closure` uses a tick-keyed fake clock and
     may cross thresholds differently). Fix each to test what it claims; never loosen a threshold to pass.
5. Docs: `docs/engine/kernel.md` or wherever the phase-cost accounting is described; the parity ledger.

## Out of Scope
- The Canonical proxies (the governor ticket). Its calibration fits on corrected costs, so this ticket goes
  first in the batch.
- Governor thresholds.
- The combat_engagement cost itself (Lane B's
  `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`).

## Acceptance Criteria
1. No refine sub-phase cost is counted twice. The sum test proves it and fails on `main`.
2. The intentional-divergence entry exists. The PR states that Live mode timing changes.
3. Every affected test is listed as fixed (how) or unaffected, and no threshold is loosened.
4. Affected baselines are listed for PERF-M1-T05.
5. `uv run make code-health` and `uv run make typecheck-py` report no new or worse finding.

## Related Tickets
- `TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY` (same batch; found during its step 1)
- `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY` (done; the end-of-tick overrun check reads this sum)
- PERF-M1-T05

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md` (gate item 7)
- `docs/engine/deterministic_execution.md`, `docs/engine/kernel.md`

## Related Stored Artifacts
- The governor ticket's staging `probes/` (profile_idle_n250.txt, profile_idle_n1000.txt)

## Related Code Areas
- `src/engine/kernel.py` (`_tick_once_inner`, `_phase_costs`), `src/engine/pipeline.py` (records sub-phase
  costs; read only, not in the window unless the planner approves)

## Assumptions / Open Questions
- If the sub-phase costs are recorded by the pipeline in a way the kernel can't see without editing
  `pipeline.py`, stop and ask the planner.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
