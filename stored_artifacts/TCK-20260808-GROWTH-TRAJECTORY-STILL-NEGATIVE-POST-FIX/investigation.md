---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX
artifact_type: investigation
phase: investigate
date: 2026-08-08
tags: [progression, simulation-quality]
---

# Investigation — TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX

## Real, current data: still negative in every world (confirmed post-fix, not stale)

Fresh 2000-tick, 6-world data (`docs/simulation_quality/long_run_observations/*.json`, generated
after `TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE`'s own fix landed):
`growth_trajectory` mean ranges -0.0031 to -0.0013 across all 6 worlds — confirmed still negative,
not a stale artifact.

## Real, direct measurement: the raw event counts behind the ratio

`growth_trajectory = (growth_event_count - stall_event_count) / path_length` counts **event
occurrences**, not XP magnitude. Two independent, real, live 2000-tick Kernel runs (not from the
committed snapshot — driven fresh, `dropped_count=0` both):

| World | `xp_granted` | `attribute_changed`/`level_up`/`skill_unlocked`/`recipe_learned`/`item_equipped` | `capability_growth_stalled` | `progression_plateau_detected` |
|---|---|---|---|---|
| `urban_political` | 4-5 | **0 (all 5)** | 30 | 34 |
| `resource_dense_basin` | 3 | **0 (all 5)** | 30 | 33 |

**`xp_granted` is the *only* one of the 6 `growth_trajectory_tags.positive` tags that ever fires**
— `level_up`, `skill_unlocked`, `recipe_learned`, `item_equipped`, `attribute_changed` are all
zero, population-wide, in both real runs. `capability_growth_stalled` +
`progression_plateau_detected` combined fire 63-64 times — a real **~13-21x imbalance** against
the 3-5 real growth events. This single, robust, twice-independently-confirmed imbalance is
sufficient to explain the negative population mean on its own — most of a 30-48-entity population
never receives a single growth-tagged event across 2000 ticks, while `capability_growth_stalled`
re-fires roughly every 300 ticks for any entity that hasn't grown, accumulating multiple stall
tags over a 2000-tick life with zero offsetting growth tags.

## Why `level_up` never fires even though `xp_granted` does: traced, not assumed

`xp_granted` fires per real kill (confirmed via `combat.py`'s own kill-XP computation, already
traced in the sibling fix ticket). Real per-kill XP: `defender.identity.evolution_level *
classification.xp_multiplier` — `10` for a monster kill at level 1 (`combat_rewards.py`). Real
level-1 threshold: `LevelingService.get_xp_required(1)` = `100 * 1^1.5` = **100 XP**. A single
kill delivers 10% of the way. With only 3-5 real kills total, population-wide, over 2000 ticks —
and XP going to whichever entity happens to land the kill, not concentrated on one attacker — **no
single entity in either real run accumulates enough XP to cross even the first level threshold**,
so `level_up` structurally cannot fire at this real kill rate/distribution. `skill_unlocked` is
gated behind level thresholds too, so it cascades to zero for the same reason.

`item_equipped`/`recipe_learned` are a separate, non-combat growth axis (equipment/crafting) —
zero in both probed worlds despite both having real civilian/shop content (unlike the monster-only
worlds), a real, disclosed but not-chased-further observation (crafting/equipment activity itself
appears sparse corpus-wide, consistent with this session's own earlier ECONOMY-pillar findings —
out of this ticket's own narrower scope).

## Real, evaluated fix candidate: raising the per-kill XP multiplier

Evaluated raising `combat_rewards.py`'s own `xp_multiplier` (10 for monster kills) so a single
kill crosses the level-1 threshold directly, converting each rare kill into 2 growth-tagged events
(`xp_granted` + `level_up`) instead of 1. **Real, honest conclusion: this would not flip the
population sign.** Even doubling the growth-event count (from ~4 to ~8 per 2000 ticks) remains
tiny against the real 63-64 stall-tag count — the imbalance is ~13-21x, not ~2x. This is also a
real, documented Mechanics Bible formula
(`docs/mechanics/attribute_progression_contract.md`, parity-verified) — changing it would require
a disclosed divergence entry for a change that demonstrably would not resolve the finding.

## Real conclusion: not a residual bug, a genuine balance/pacing observation

The orphaned-kill-reward fix (sibling ticket) was real, verified, and correctly wired — this
ticket's own investigation confirms the wiring is not the remaining cause. The remaining negative
`growth_trajectory` reflects **genuinely low real combat/kill frequency** across the corpus
(3-5 XP-granting kills population-wide per 2000 ticks) colliding with a stall-detector cadence
(300 ticks) calibrated as if growth-relevant activity should be roughly as common as general
activity — it structurally isn't, given real combat scarcity. This is the same class of finding as
`wilderness_survival`'s archetype-correct low diversity and `AGENCY=C` for non-routing worlds:
**a real, disclosed pacing characteristic of the current corpus, not a code defect** — and,
critically, not one a small parameter tweak in this ticket can responsibly resolve, since the
scale of the real imbalance (~13-21x) is far too large for a magnitude change alone to close.

**Not fixed in this ticket, per the evidence.** The real remedy — raising combat/kill frequency
corpus-wide, or reconsidering whether `capability_growth_stalled`'s own 300-tick cadence should be
lengthened to match genuinely slower-paced worlds — is a substantial balance initiative with its
own real risk (recalibrating `grade_anchors.json`, re-verifying dozens of scenarios), disclosed as
a real, evidenced recommendation for a future, appropriately-scoped ticket rather than forced
through here.

## Real quest-completion re-check at 2000 ticks (not inherited from the 1000-tick finding)

Direct real probe of `urban_political` at 2000 ticks (same live run used for the `entity_killed`/
`xp_granted` trace above): `quest_started` and `quest_completed` both **zero** — confirmed via
direct JSONL inspection, not inferred from the SimQ `NARRATIVE` pillar's own broader event count
(which scores other narrative-adjacent event types too and is non-zero in 3 of 6 worlds — a
different, broader signal, not conflated here). Quest dormancy is real and still current at 2000
ticks, matching the sibling ticket's own 1000-tick finding.

## Docs Requiring Update

- `docs/simulation_quality/entity_lifecycle_score.md`: record this real finding (the 6 growth
  tags' real fire rates, the imbalance, and why a magnitude fix was evaluated and rejected) as
  calibration-relevant context for anyone reading a negative `growth_trajectory` mean
