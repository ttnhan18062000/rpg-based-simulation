---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261026-PERF-CAPACITY-SIZING-PROBE-AT-10K-ENTITIES
phase: open
date: 2026-10-26
tags: [performance, benchmarking]
---

# TCK-20261026-PERF-CAPACITY-SIZING-PROBE-AT-10K-ENTITIES

## Title
One short capacity sizing probe at 10,000 entities, recorded against the kept bigger-world target in `optimization_architecture.md` §1 (CLASS_B host, not a CLASS_A verdict)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The owner kept the "10,000+ concurrent entities, a 50ms compute latency budget, and a 2GB memory footprint" claim in `docs/performance/optimization_architecture.md` §1 as the stated bigger-world target. The owner also asked that a perf capacity run measure it, so it stops being "Target, not enforced" with nothing checking it (#715 issuecomment-6409936521).

The owner chose option A for how to measure it now (#715 issuecomment-6420564226). Perf runs one short sizing probe and records the distance. The full capacity run waits for `TCK-20261026-COMBAT-ENGAGEMENT-CONSIDER-PER-PAIR-COST-AFTER-H1`.

Why only a probe:
- The 10k target is the `CLASS_A` row of `performance_contract.md` §5.1. `CLASS_A` means at least 16 logical cores and 32 GB (`certification_contract.md` §3). The development host is 6 cores and 9 GB, which is `CLASS_B`.
- `combat_engagement` grows about N^1.85: about 7.3 s per tick at movement 2000 (`tick_cost_growth.md`). That extrapolates to roughly 140 s per tick at 10k. So capacity_run's default of 100 warm-up plus 1000 sampled ticks would take about 40 hours.

## Scope
- On a heavy-run slot granted by lead-planner: one process, detached (`setsid`) with a watcher, under `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0`. Before starting, check that loadavg1 is below 1.5 and that at least 2.5 GB is available.
- Command (read the argparse in `tools/perf/capacity_run.py` first; never run it with `--help` to find out): `python3 tools/perf/capacity_run.py --scenario movement --entities 10000 --profile PERF_2GB_LOCAL --contract canonical --warmup 2 --ticks 3 --repetitions 1 --seed 42`.
  - If `PERF_2GB_LOCAL`'s `tick_budget_ms` or the governor sheds work at this scale, record that and say whether the reading is still a full tick.
  - Hard wall-clock cap: 60 min. If the cap is hit, record the ticks completed and the time each one took.
- Record:
  - the world build time;
  - ms per tick for each sampled tick;
  - RSS high-water;
  - the phase split if the harness gives it;
  - the commit, the host, `nproc`, total RAM, the hardware class the harness detects, and the dependency fingerprint if `TCK-20261025-PERF-RECORD-IDENTITY-PINS-INSTALLED-RUNTIME-DEPENDENCIES` has landed.
  An OOM under MemoryMax=3G is itself the memory reading: record it as "above 3 GB".
- Edit the §1 sentence of `docs/performance/optimization_architecture.md` so it states the measured distance (for example "measured 2026-10-NN: N s per tick and M GB RSS at 10,000 entities on a CLASS_B host (6 cores, 9 GB); not a CLASS_A verdict"). Cite this ticket. Keep "Target, not enforced" unless a check now enforces it; none does.
- Put the raw output in staging `evidence.md` and clean the run data by run id.

## Out of Scope
- A CLASS_A verdict, a pass/fail outcome, or a baseline record. This is a reading, not a baseline, so nothing is promoted.
- The full capacity run of 100 warm-up plus 1000 ticks. It waits for the `_consider` follow-up.
- Any `src/` change, or any edit to `performance_contract.md` (rpg-owned).

## Acceptance Criteria
- One probe run is recorded with the fields above, labelled "CLASS_B host, not a CLASS_A verdict" and PROVISIONAL.
- `optimization_architecture.md` §1 states the measured distance and cites this ticket.
- Run data is cleaned by run id; disk stays at or above 10 GB free.

## Related Tickets
- `TCK-20261010-PERF-M2-T04-CAPACITY-RUN` (the tool)
- `TCK-20261026-COMBAT-ENGAGEMENT-CONSIDER-PER-PAIR-COST-AFTER-H1` (gates the full run)
- `TCK-20261025-PERF-RECORD-IDENTITY-PINS-INSTALLED-RUNTIME-DEPENDENCIES`

## Related Docs
- `docs/performance/optimization_architecture.md` §1
- `docs/engine/performance_contract.md` §5.1
- `docs/engine/contracts/certification_contract.md` §3
- `docs/performance/tick_cost_growth.md`
- `docs/plans/design_enhancement/performance_optimization/performance_m6_gate_b_future_architecture_epic.md` (T05 inputs)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/perf/capacity_run.py`
- `src/perf/scenarios.py` (`build_movement_state`)
- `src/perf/profiles.py`

## Assumptions / Open Questions
- Whether `build_movement_state(10000)` fits the region layout is untested; a build failure is recorded as the finding.
- The 3-tick window is short. The number is an order-of-magnitude reading, not a steady-state average.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
