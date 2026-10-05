---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261005-HAZARD-GROWTH-CAPPED-BELOW-EVERY-AUTHORED-COMBAT-REGION
phase: done
date: 2026-10-05
tags: [world]
---

# investigation — TCK-20261005-HAZARD-GROWTH-CAPPED-BELOW-EVERY-AUTHORED-COMBAT-REGION

Scope 1-3 evidence from the first pass is in the ticket's Implementation Notes (documents conflict; 25 of 104 region instances authored below 1.0; reader table).

## Scope 2 premise re-taken under the unified region lookup (branch `region-lookup-unification`)
Claim carried: no region authored below 1.0 reaches trauma 50, so the growth branch was dead in every measured region. Re-measured (capped code, unified lookup, 10,000 ticks, seed 42, trauma sampled every 500 ticks):
- `frontier_living_world`: `hometown` 0.0, `trading_hometown` peak 1.82 at a sample. Credited deaths are an upper bound on trauma (each adds 1.0, decay only subtracts): `hometown` 12 credited deaths in 10,000 ticks (one run; this world is not reproducible, see below), so trauma <= 12.
- `generated_frontier_3_42`: `hometown` peak 0.0 at a sample, 12 credited deaths, so <= 12.
- Margin: at least 38 below the threshold of 50. The premise holds under the new rule. The unification raised `hometown` credit from 7 to 12 deaths, which cannot close a gap of this size. Two worlds only; 22 not measured.

## Behavioural consequence of removing the cap
Growth is about +0.01 per tick and unbounded while trauma stays above 50 (decay is 0.0005 per tick).
- `generated_frontier_3_42` (deterministic: three runs identical pre-growth; paired capped/uncapped runs identical until tick 6911): `goblin_camp` grows from tick 6911 to 33.89 at tick 10,000 (authored 3.0). Death count and cause mix are identical in both arms (138 deaths, 96 `HAZARD`, 1 `DEFEAT`, 2 `STARVATION`, 39 none): no measurable change in deaths inside 10,000 ticks.
- `frontier_living_world`: growth starts at tick 5217 (`bandit_road`) and 5211 (`goblin_camp`) and reaches 49.83 and 50.89 at tick 10,000. **Not a paired comparison**: this world is not reproducible run to run (below), so its death counts (265 capped vs 275 uncapped) cannot be attributed to the cap.
- Drain is `hazard * (1 + calamity) * 10` HP per tick (`world/environment.py`), so a region at hazard 34-50 drains 340-500 HP per tick for any entity without the matching `hazard_kind` immunity.
- Window: 10,000 ticks. The earlier `generated_frontier_3_42` evidence in the overlap ticket's first pass used 5,000.

## Finding: `frontier_living_world` is not reproducible
Same code, same world, same seed, run alone: `probes/determinism_check_fl_2000_run1.jsonl` has 8 deaths at tick 500 and `..._run2.jsonl` has 10. `generated_frontier_3_42` was identical across all runs (`determinism_check_gf342_*`). Cause not established: candidates are the kernel's time-based throttle (`should_throttle` mid-tick abort, `Tick N exceeded budget` warnings appear on this machine) and anything else timing-dependent. Consequence: every single-run figure on `frontier_living_world` in this session and the overlap ticket (trauma crossing ticks, death counts) is an indication, not a reproducible measurement, and the paired comparison for this ticket uses `generated_frontier_3_42`. Not investigated further here; for the planner to route.

## Readers
`events.py` danger urgency (`min(1.0, (h - 0.7) / 0.3)`) saturates at 1.0, so every region authored at or above 1.0 reads the same urgency, and growth above 1.0 changes nothing for it. Left unchanged: its output is an urgency in [0, 1], and a different mapping would be a new curve with no stated reason. The other readers use hazard as a linear multiplier and need no change; `domains/world_emergence/models.py` clamps the sum.
