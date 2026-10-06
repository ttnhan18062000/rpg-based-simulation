---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261005-REGIONAL-TRAUMA-IS-PRODUCED-BY-A-BOSS-RESPAWN-AND-HAZARD-DEATH-LOOP-NOT-BY-FIGHTING
phase: done
date: 2026-10-05
tags: [world]
---

# investigation — TCK-20261005-REGIONAL-TRAUMA-IS-PRODUCED-BY-A-BOSS-RESPAWN-AND-HAZARD-DEATH-LOOP-NOT-BY-FIGHTING

Scopes 1, 3 and 4 only (measurement). Scope 5 (implementation) is not done and not authorised: the options below are reported with evidence and **no recommendation**. Nothing in `src/` changed.

The probes (`zones.py`, `contamination.py`, `analyse.py`, `geometry.py`) are copied into this directory's `probes/`; `zones.py` takes an optional `ZFLAGS` JSON env var that sets `state.feature_flags`. All runs: `audit_mode`, `max_tick_budget_ms=1e9`, seed 42, `PROD_SMALL`, 10,000 ticks, all 24 corpus worlds. Two bases: **PRE `54c31ee73`** (main `7a9f302db` incl. #347, plus the region-lookup unification) and **POSTFIX `06a0ce1cb`** (PRE plus Lane A's unmerged tip `ff88bd929`, the silent-no-op fix; merged cleanly in a throwaway checkout).

## 1. Victim faction at death vs catalog faction (asked first)
Every runtime-spawned monster in the 24 worlds carries **no catalog `faction_id`**. Across all PRE runs: 1,392 `world_boss`, 328 `orc_warrior`, 322 `goblin_warrior` spawns have no `faction_id` property (6 other spawns, same); the only entities with a `faction_id` are the compiled initial populations. A boss spawn row has `faction_enum = 1` (the `monster_horde` bucket) and properties `boss_region_id`, `boss_spawn_tick` only. The 68 warrior deaths on `frontier_living_world`: spawned at tick 1, 301, 601, ... (every 300 ticks), a `goblin_warrior` at (110,38) in `goblin_camp` and an `orc_warrior` at (87,50) (the `bandit_road`∩`near_forest`∩`wolf_den` zone); props empty; victim faction at death `monster_horde`. `goblin_warband` (the catalog faction a goblin would carry) is immune to `NATURAL_TERRAIN` (verified through `FactionSemanticsService.get_hazard_immunities`), and both regions are `NATURAL_TERRAIN`, so a catalog goblin would take zero drain. **So the planner's hypothesis holds: this is a spawn-path property, not boss-specific.** Runtime spawning does not give the monster its catalog faction identity, and so not its declared endurance. (The orc warriors' catalog counterpart was not checked.) Initial-population victims (4 `undead_remnants` sentinels, 2 `town_council` guards) do carry their catalog faction.

## 2. Contamination, per world (scope 3), 24 worlds, PRE
Deaths in 19 of 24 worlds (5 have none). **2,144 deaths: 2,112 `HAZARD` (98.5%), 31 `DEFEAT`, 1 `KILL`.** **1,392 (65%) are boss deaths; the boss loop is present in 15 of the 24 worlds.** Per-world rows: `probes/contamination_24_worlds_PRE_54c31ee73.jsonl`. Selected:
| world | deaths | HAZARD | DEFEAT | boss deaths |
|---|---|---|---|---|
| frontier_living_world | 233 | 232 | 1 | 158 |
| frontier_extended | 214 | 211 | 3 | 142 |
| simq_scale_stress_seed42 | 234 | 229 | 5 | 153 |
| frontier_marches | 229 | 227 | 1 | 154 |
| lifecycle_full_coverage_world | 211 | 206 | 5 | 132 |
| generated_frontier_3_42 | 99 | 96 | 3 | 63 |
| camp_maturity_calibration_pilot | 150 | 150 | 0 | 79 |
Boss cadence on `frontier_living_world`: first spawn tick 2101, then every 100 ticks in each of two regions (79 + 79): `bandit_road`'s boss at its region centre **(70,50), a tile inside `bandit_road`, `near_forest` and `wolf_den`**, and `goblin_camp`'s at (110,37). The same two spawn tiles recur in every boss world (e.g. 78/75 in `simq_scale_stress_seed42`).

## 3. The three readings, side by side
1. **"Fights but misattributes" (wounded then drained): not supported.** For every `HAZARD` death the probe records the last attacker damage the victim took. **0 of 2,112 `HAZARD` deaths were wounded by an attacker at any earlier time, in any window** (50, 200, any), PRE and POSTFIX. Positive control: all 17 `DEFEAT` deaths in the five checked worlds do carry a last-hit record, so the tracker works.
2. **"Was prevented from fighting" (the combat-suppressing bugs): not supported at these bases.** `DEFEAT` totals across the 24 worlds: **31 PRE, 30 POSTFIX**; `KILL` 1 vs 0; `frontier_living_world` 1 vs 1; `frontier_marches` 1 vs 2; `lifecycle_full_coverage_world` 5 vs 3. Lane A's fix changes the withheld-attack counts (844 to 2 on `frontier_living_world`) but not how many entities die in combat. Limits: 10,000 ticks, seed 42, deaths only (not wounds that did not kill).
3. **"Barely fights": supported.** 2,112 of 2,144 deaths are environmental drain; combat deaths are 31 in 24 worlds times 10,000 ticks.

## 4. Parallel trauma series (scope 4)
Replay of the producer (+1.0 per death credited to a region, -0.0005 per tick, floor 0) over the recorded deaths. **Control:** the all-deaths replay is within 1.0 of the real per-region trauma in every world (real 110.012 / 111.0115, replay 111.0 / 112.0 on `frontier_living_world`: one death of difference, cause not isolated), so every arm below is accurate to about +-1.
| arm, trauma at tick 10,000 | frontier_living_world | simq_scale_stress_seed42 | frontier_extended |
|---|---|---|---|
| all deaths (as shipped) | road 111, camp 112 | road 109, camp 105 | road 111, camp 90 |
| **boss deaths removed** | road 32, camp 33 | road 31, camp 30 | road 32, camp 27 |
| **(d) only deaths with a killer** | **0, 0** | **0, 0** | **0, 0** |
| violent within 50 ticks (killer, or attacker damage in the last 50) | 0, 0 | 0, 0 | 0, 0 |
First tick over 50: all-deaths arm: `frontier_living_world` camp 5112 / road 5218, `simq_scale_stress_seed42` road 5404 / camp 5703, `frontier_extended` road 5218 / camp 6903; **every other arm never crosses 50** in any of the three. With the boss loop removed the 50 threshold is **never** reached; with bloodshed only, trauma is zero.

## 5. The `:226` dragonkin branch
Does not loop, because it **never fires**: **0 `dragonkin` spawns in any of the 48 runs.** `generated_frontier_3_42` and `simq_scale_stress_seed42` each have one `LAIR` place (`moon_cave_lair`, region `moon_cave`), and `moon_cave`'s trauma peaks at 0.0 in both (its deaths are passive starvation, which the trauma block ignores; `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`), so the shared gate (`maturity >= 2.0 and trauma >= 8.0`) never opens for it. The mechanism is identical to the region branch's, so the same loop would follow the moment that region's trauma reached 8: **untested, not observed.**

## 6. Options (a)-(e), with the evidence each rests on, no recommendation
- **(a) `monster_horde` should have hazard immunities.** The bucket is a `legacy_engine_bucket`, not a catalog faction (planner, verified). What the data adds: warriors lack a catalog faction too (section 1), so a bucket entry would cover bosses and warriors but not catalog identity.
- **(b) bosses should not spawn into a region whose hazard kills them.** Both loop regions are `NATURAL_TERRAIN` (3.0 and 2.0); the `bandit_road` boss spawns on a tile that three regions contain, so which hazard kills it depends on region precedence (owner decision 13).
- **(c) hazard drain should not apply to boss kinds.** Would stop the loop; the 68 warrior deaths would continue (they are not boss kinds).
- **(d) trauma should not count deaths with no killer. Retroactive.** Trauma on this corpus goes to 0 (section 4); bosses-only removal (not an option as written) would leave 27 to 33. No `HAZARD` death in 24 worlds had an attacker earlier, so a "violent within a window" variant changes nothing here.
- **(e) the boss branch should be inert while deferred. Retroactive for bosses only.** Removes the 1,392 boss deaths (65%); the 68-per-world warrior hazard deaths and everything else remain, and trauma stays at 27 to 33 in the loop regions (section 4, boss-removed arm). Consumers of `world_boss`/`ancient_sentinel`/`dragonkin` (a grep, not a trace; semantic search tools were unavailable here): `src/world/boss.py`, `src/world/calamity.py:50` (the **calamity** branch also creates `world_boss`), `src/world/threat.py:30`, `src/systems/world_systems/navigation.py:41`, `src/observability/entity_kind_constants.py` (boss kinds, spawn-cadence exclusions), `src/quests/generator.py`, `src/domains/optimization/feature_flags.py:168` (a flag already keyed to the world_boss spawn); about 16 test files (`tests/unit/world/test_boss_gate_reachability.py`, `test_world_dynamics.py`, observability extractor/shaper tests, `tests/integration/world/test_living_world_ph9.py`, `tests/helpers/presets.py`, ...); data: `entity_archetypes.yaml`, `species.yaml`, `species_relations.yaml`, `factions.yaml`, `moon_cult_ruins.yaml`. Each of these would need checking against an inert default.

## 7. Which figures survive
- **Survive:** the geometry (partial overlaps, owned-tile shares); the death-split verdict (H3 on own ground, H1 narrowly) and the three `haunted_battlefield` pair readings; the `generated_frontier_3_42` hazard-growth pair (deaths identical capped vs uncapped).
- **Do not mean what they read as:** every "trauma crossed 50" tick, every per-region trauma value, and `ENV-06` reachability: they are the boss-loop's counter (without bosses trauma peaks at 27 to 33). The hazard-growth ticket's consequence is the loop's: growth starts at the loop-driven crossing. The panic ticket's regional trauma input is the same counter.
- **Need re-reading:** the unification ticket's "trauma credited per region" figures (credit moved, but the credited quantity is loop deaths); owner decision 15's "trauma falls to roughly zero" is **supported** on both bases measured (arm (d) is zero; DEFEAT does not rise post-fix).

## 8. Implementation of owner decisions 14 and 15, before and after (audit_mode, budget disabled, seed 42, 10,000 ticks)
Base for "before": `origin/main` `58aa22f67` (no change). "After": that base plus decisions 14 (default-OFF flag `ENABLE_WORLD_BOSS_SPAWN` over all three boss branches) and 15 (rule `ENV-07`, violent-cause-only trauma incl. the building `+2.0`). Outputs: `probes/b1_*.jsonl`.
| run | deaths | HAZARD | DEFEAT | boss deaths | trauma at tick 10,000 | max trauma during the run |
|---|---|---|---|---|---|---|
| `frontier_living_world` before | 235 | 233 | 2 | 158 | `bandit_road` 110.0, `goblin_camp` 110.0 | 110.0 |
| `frontier_living_world` after, defaults (flag OFF) | 80 | 72 | 7 | 0 | **0 in every region** | `bandit_road` 4.42 |
| `frontier_living_world` after, **flag ON** | 80 | 72 | 7 | 0 | 0 in every region | `bandit_road` 4.42 |
| `simq_scale_stress_seed42` before | 231 | 227 | 4 | 150 | `bandit_road` 104.0, `goblin_camp` 104.0 | 104.0 |
| `simq_scale_stress_seed42` after, defaults | 75 | 71 | 4 | 0 | 0 in every region | `bandit_road` 1.96 |
Result: trauma on both worlds goes to **0**, never above 4.42, and the 50 threshold is never crossed. **With or without decision 14 the result is identical**: with the flag ON (confirmed active in the kernel state) no boss spawns either, because the boss gate needs region trauma >= 8.0 and violent-cause-only trauma peaks at 4.42. So decision 15 alone stops the loop; decision 14 additionally makes the deferral independent of trauma. The 72 remaining `HAZARD` deaths (about 68 of them the runtime-spawned warriors) are unchanged by either decision, and no longer feed anything. Caveat: one seed, two worlds; before/after differ in more than the loop (death counts also change because the loop's entities and their trauma-driven hazard growth are gone). The 24-world split was measured earlier on a different base (`54c31ee73`).
Seven existing tests asserted a boss spawn and now set the flag ON explicitly: `test_boss_gate_reachability.py` (2), `test_calamity_magical_demonic_reproduction.py` (2), `test_world_dynamics.py` (3); the other boss-related tests that passed vacuously with the flag OFF were given the flag too, so they keep their meaning.
