---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261006-BEHAVIORAL-5K-REGRESSION-URBAN-POLITICAL-DRIFTED-FROM-THE-2026-08-19-BASELINE-ATTRIBUTE-EACH-METRIC
phase: done
date: 2026-10-07
tags: [testing, world, investigation]
---

# Investigation — TCK-20261006-BEHAVIORAL-5K-REGRESSION-URBAN-POLITICAL-DRIFTED-FROM-THE-2026-08-19-BASELINE-ATTRIBUTE-EACH-METRIC

## Method
urban_political, seed 42, 5,000 ticks, adventure routing ON, exactly as `tests/regression/test_behavioral_5k.py` runs it, but under `audit_mode` with `max_tick_budget_ms=1e9` (`probes/probe5k.py`). A plain (non-audit) run on main gives identical numbers, so the kernel's wall-clock throttle is not a factor here. Series compared, not endpoints. Candidates bisected over the 344 first-parent commits between the baseline commit d2816ab6c and main 7aa6f997b (`probes/scan.log`, `probes/bisect2.log`; index = position in that list, oldest first).

## Baseline reproduces
d2816ab6c under the baseline's own config gives 13.30 / 584.16 / 0.0 exactly. The baseline was not an early-ended run.

## Result table
| Metric | Baseline | Now (7aa6f997b) | Moved by | Mechanism | Intended? |
|---|---|---|---|---|---|
| alive_avg | 13.30 | 5.36 | #303 (1a40d22d1, idx 255): 12.96 -> 4.96 (parent 558802cc7 still 12.96) | The global world-clock raid spawned goblin_raiders (ids 31-36, at about t=500 and t=1000). They were the ONLY survivors of the t=1000-1100 collapse in the baseline. #303 retired the raid on purpose, so on main the population is 27 until t~1000 and 0 from t~1100. | Intended removal; the resulting extinction exposes a defect (below) |
| gold_avg | 584.16 | 0.18 (exactly 0.0 from idx 320, 7366d7985) | #303: 584.34 -> 0.18 | The baseline's gold was carried only by those raiders (29 and 40 gold each, 207 at t=1100). Original workers, guards and merchants hold 0 gold. gold_avg is the sum of inventory.gold over all entities (metrics.py:33) sampled every 100 ticks. It reaches exactly 0.00 when no entity holding gold is left, not because an economy stopped. The 0.18 is 9 gold over three early samples (5, 3, 1). Later 0.18 -> 0.54 -> 0.78 -> 0.18 -> 0.0 wobbles (idx 273, 285-290, 300-320) are sub-gold-unit early-tick effects, not attributed individually. | Follows from #303 |
| quest_active_count | 0.0 | 1.02 | #182 (0499db145, idx 147): 0 -> 0.62; #291 (f4146ddbb, idx 273): 0.62 -> 0.84; #333 (898c6f35a, idx 285): 0.84 -> 1.0; 1.0 -> 1.02 between idx 285 and 300 (not narrowed further) | Quests now stay ACTIVE (5-6 entities from t=100 to t~1000, until they starve); the baseline never had one active at a sample. Only the three narrowed steps were bisected. | Not judged a defect on its own; all four steps are small |

## The finding behind the alive collapse (applies to baseline AND main)
Starvation, synchronised, in both. Baseline: 28 deaths at t=1000-1099; main: 27 STARVATION deaths at t=900-1099 (20 recorded with death_reason STARVATION, 7 with only a passive cause; 2 HAZARD, 1 DEFEAT). Zero eat events and zero sleep events (a live entity's hunger or sleep_debt dropping between ticks) in 2,000 ticks, in both (`probes/deaths_*.json`). Hunger accumulates at 0.1 per tick for every entity and reaches the 95 starvation line at about t=950 (apply.py:90-100). Other lanes traced the cause on standard worlds: EatScorer targets only a tavern, and no world has one; the capacity gate counts terminal projects. So the 2026-08-19 baseline's 13.3 alive / 584 gold was never a living town: it was the respawning goblin raid. The raid was retired on purpose (#303), which removed the only survivors.

## Recommendation (to the owner)
Do NOT rebaseline now. The metric is currently measuring the starvation bug. Take the honest baseline after the biology child (SURV-05/06) and the capacity-gate fix land, then run `make regression-baseline`. Baseline untouched.
