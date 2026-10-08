---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: report
ticket_id: TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY
date: 2026-10-08
tags: [performance, determinism, engine, testing]
---

# Phase A step 1: calibration of WORK_MODEL_V1 (PROVISIONAL)

No behaviour change in this step. Probes, raw rows and fit scripts are in `probes/`.

## Frozen result

`WORK_MODEL_V1 = {entity_ms: 0.68, lead_ms: 7.42}`, **PROVISIONAL**. Unit: reference-millisecond.
`tick_cost = entity_ms * active_entities + lead_ms * leads`, both counted from `AuthoritativeState` before the tick (pre-policy demand).
Frozen by perf-planner's approval on 2026-10-08. Store the weights as constants with the version name, to two decimals exactly as above, so a later fit cannot drift silently.

Least-squares values behind the rounding: 0.681 and 7.421.

## What was measured

- Base: RPG-core `28e304cbe` (contains #395 attack symmetry and wild_beast_pack spawns / CONFLICT-03, #394 cooperation pending-offer index, #387 salience fix) plus
  perf `df2f34f43` (the kernel double-count fix, `TCK-20261008-PERF-KERNEL-RESOLUTION-OVERHEAD-DOUBLE-COUNTS-SUB-PHASES`).
- Host class: this VM, Intel i5-11400H, 6 vCPU, 11 GB, run under `nice 10` and a 2 GB memory cap; one process at a time.
- Matrix: scenarios idle, movement, resource, strategic (`src/perf/scenarios.py`) x n = 100, 250, 500, 1000 entities x executors sequential
  (`max_worker_count=0`) and thread (`max_worker_count=2`); 331 rows after 3 warm-up ticks per configuration; seed 7; all ticks in `NORMAL`.
  Budget large enough that no mode change occurred; frame pacing and replay off.
- Target: `_final_compute_ms` minus the `combat_engagement` bucket (the kernel now counts each sub-phase once, so one subtraction).
- Demand counters read from state before each tick: active entities, entities with a navigation target ("movers"), total leads. The dirty-set size inside
  `refine` was read by wrapping `AuthoritativeApplyPipeline.refine` from the probe; `pipeline.py` was not edited.

## Exclusions

- **combat_engagement bucket excluded** because of the open Lane B defect `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`: `CombatEngagementPhase._consider`
  runs about n^2 times (861,200 calls at n = 1000; hostility projection `is_hostile_compat` -> `project_relation`), 25 ms at n = 100 and about 2.2 s at n = 1000 per tick.
  V2 refits with combat included after that fix lands.
- **Thin rows**: the strategic family at n = 500 has 8-9 ticks and at n = 1000 only 3 ticks per executor (per-configuration 40 s wall budget), so those rows are thin.

## Fit

Non-negative least squares, pooled over all rows:

| Model | Pooled R^2 |
|---|---|
| entities + leads (**chosen**) | **0.874** (gate 0.85: met) |
| entities + movers + leads | 0.874 (movers weight 0.037, dropped) |
| entities + movers + leads + dirty-set size | 0.877 (no gain, dropped) |

Chosen model, actual / predicted (sum over rows) and within-family R^2:

| Family | actual/predicted | within-family R^2 |
|---|---|---|
| idle | 0.58 | 0.28 |
| movement | 0.81 | 0.88 |
| resource | 1.35 | 0.71 |
| strategic | 0.86 | 0.83 |

Acceptance band 0.5-2.0 per family: met. Executors: sequential 0.92, thread 0.83 (the proxy does not depend on the executor).

## Out-of-sample honesty

- Leave-one-family-out (weights fitted on three families, ratio on the fourth): idle **0.49** (on the edge), movement 0.77, resource **1.75**.
- `lead_ms` is identified only by the strategic family (leads exist nowhere else in the matrix), so it is **untested out of sample**.
- Canonical is a rough reference-millisecond estimator, which is what the plan accepts (it models overload; it does not measure it).
- Per-entity cost depends on perceived-neighbour density (profiled: `filter_saliency` makes about 50 hostility checks per brain call at n = 250 and about 172 at n = 1000
  because `build_idle_state` places entity i at (i % 100, i // 100), a fixed 100-wide grid that deepens with n). Entities and leads cannot see this. See `probes/profile_idle_cumulative_n250.txt` and `..._n1000.txt`.

## Not comparable with earlier probe weights

The first probe weights (1.10 / 4.79 / 7.80 and the 1.02 / 15.77 re-fit) were fitted before the kernel double-count fix (`df2f34f43`) and are **not comparable** with V1.

## V2 triggers and candidates

- Outstanding trigger: Lane B's `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP` (refit with combat included).
- If any RPG change later moves population or movement demand, re-check the band.
- Candidate feature: a deterministic neighbour-pair count (ordered pairs of active entities within the perception radius 10.0, `engine/domain/cognition.py:57`). The probe is ready
  (`neighbour_pairs()` in `probes/calibrate_step1.py`, one-pass tile hash, times itself); not run, because the baseline already meets the gate. Its gain and per-tick cost are unmeasured.

## Per-phase rules under Canonical (decision, perf-planner 2026-10-08)

Neither `PhaseBudgetGovernor` per-phase rule has a pre-policy counter, so under Canonical **both are dropped** and only the tick-level compaction rule remains:

- rule 1, `locomotion`: best pre-policy counter (movers) R^2 0.23; the post-policy `movement_candidates` reaches 0.77 pooled but is post-policy, so unusable under the feedback-loop rule (plan section 2).
- rule 2, `final_integrity`: best counter reaches R^2 0.46 (dirty-set size 0.37; dirty-set + leads + entities 0.46), below the 0.6 bar.

Live is unchanged (owner chose the opt-in Canonical contract). Step 4 records this as an intentional-divergences entry and a parity entry, Canonical only.

## Findings routed out of this step

- Kernel `resolution_overhead` double-count: fixed in Phase A as `TCK-20261008-PERF-KERNEL-RESOLUTION-OVERHEAD-DOUBLE-COUNTS-SUB-PHASES` (DEV-017, INFRA-425, `df2f34f43`).
- Combat hostility projection cost: already filed (Lane B).

## Files

`probes/calibrate_step1.py` (matrix probe), `probes/calibration_rows_step1.json` (331 rows), `probes/fit_step1.py` (fit), `probes/profile_idle_step1.py` and the four
`probes/profile_idle*.txt` outputs. The earlier design-time probe is `probes/calibrate_work_units.py` / `calibration_rows.json` (pre-fix, superseded).
