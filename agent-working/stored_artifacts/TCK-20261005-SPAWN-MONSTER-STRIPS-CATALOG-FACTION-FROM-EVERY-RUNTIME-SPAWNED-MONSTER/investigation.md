# Investigation: runtime spawns lose their catalog faction, and a restored faction exposes the spawn-tile stack

Lane B, rpg-implementer-2, 2026-10-06. Base `origin/main` `9299891a9` (rebased before the final measurement).

## Run configuration (both arms)
`audit_mode` ON, `max_tick_budget_ms=1e9`, seed 42, 10,000 ticks, all 24 corpus worlds, `probes/zones_ab.py` (the contested-zone
`zones.py` probe plus one switch). **before** = `NOFIX=1`: `SPAWN_KIND_CATALOG_FACTION` cleared and `free_spawn_position`
replaced by identity, i.e. current `main` behaviour. **after** = this branch. Same seed, same worlds, same profile in both arms.
Raw rows: `probes/zones_24_worlds_{before,after}.tar.gz`; per-world summary: `probes/summary_24_worlds.jsonl`.

## Mechanism (why a faction tag removed ~640 deaths)
A "hazard death" is a death whose lethal update carries `outcome_kind == HAZARD`: region hazard drain
(`EnvironmentService.calculate_hazard_drain`, `hazard_level * (1 + calamity) * 10` HP per application) finished the entity.
It is not cross-faction combat and not a trauma/hazard-accrual effect. `calculate_hazard_drain` returns 0 when the entity's
catalog faction (`get_faction_id_str` -> `identity.properties["faction_id"]`) declares the region's `hazard_kind` in
`hazard_immunities`. Runtime-spawned goblins/orcs had no `faction_id`, so the id fell back to `monster_horde`, a bucket with no catalog
definition and no declared endurance, and they took the full drain in their own camp's `NATURAL_TERRAIN` region. With `faction_id`
`goblin_warband` / `orc_clan` (both declare `NATURAL_TERRAIN`) the drain is 0. No other path changed in that arm for those deaths.

## Results, 24 worlds
| | before (main) | after (branch) |
|---|---|---|
| deaths | 734 | 84 |
| HAZARD deaths | 686 | 46 |
| DEFEAT deaths | 44 | 38 |
| HAZARD deaths of runtime goblin/orc warriors | 637 | 0 |
| ticks with a `LAW-OCCUPANCY-COLLISION` | 3 | 0 |

(`frontier_living_world`: 77 -> 9 deaths, 67 -> 0 goblin/orc hazard deaths.) The 46 remaining HAZARD deaths are non-spawned
entities (guards, sentinels, workers). The pre-fix 2,144 / 2,112 figures included ~1,392 world-boss deaths; bosses are inert since #356, so
"before" is already a different base from those figures.

## Occupancy (TCK-20261005-LAW-OCCUPANCY-COLLISION-HARD-LAW-ERRORS-ON-MAIN)
Verdict: **enforcement is at fault, the law is right.** `spawn_monster` placed a spawn at a fixed tile (camp position) without checking occupancy.
- Discriminator: on `frontier_living_world`, entity 52 (goblin) spawned onto (110,38) at tick 300 while entity 22 held it: collision at tick 301.
- With the faction restored spawns survive and pile onto the camp tile: 837 collision errors in one run (vs 2 on `main`, where drain killed them first).
- Exact-tile free placement cut that to 12 (6 events). Remaining cause, traced tick by tick (`probes/trace.py`): entity 52 patrols (110,37)<->(110,38); at spawn time it was on (110,37), the spawn took (110,38), and 52 stepped onto (110,38) in the same tick (both computed from the prior state).
- Shipped policy: a tile is clear only when no live entity and no earlier same-tick spawn is within one tile (the max one-tile move per tick); nearest clear tile in ring/y/x order (no RNG), search radius 5, `RuntimeError` when none is clear. Result: 0 collisions in all 24 worlds. This is a placement policy that avoids the same-tick race, not a change to movement/spawn ordering.
- Tile (87,50) is the `orc_warrior` respawn tile of `frontier_living_world`'s camp; it is incidental to region overlap.

## Hostility check (the ruling's hard constraint)
`probes/host.py`, real `LegalityServiceV2.verify_attack_legality`, hero vs spawned monster, both directions:
goblin_warrior, orc_warrior, dragonkin, bandit: legal both ways with the faction restored. wolf/bear/golem mapped to `wild_beast_pack`:
hero->mob legal, **mob->hero `FRIENDLY_FIRE_ILLEGAL`** (`legality.py:252-272` routes through `is_hostile_compat`; wild_beast_pack is a contextual threat).
Owner decision 2026-10-06: hold wolf/slime/bear/harpy/golem out (stay `MONSTER_HORDE`, no `faction_id`) and file
`TCK-20261006-WILD-BEAST-PACK-LEGALITY-IS-ONE-WAY-HERO-CAN-ATTACK-IT-IT-CANNOT-ATTACK-HERO`.

## ENV-07 trigger measurement (wounded-within-window), re-run
HAZARD deaths with an earlier attacker-damage record: **before 2 of 686, after 0 of 46.** Both "before" cases are `undead_remnants` sentinels
(`frontier_living_world` t906, `simq_scale_stress_seed42` t230) whose lethal update carries hazard damage 30 AND attacker damage (`ago` 0, goblin attacker):
a same-tick mix, not damage from an earlier tick. They disappear in the "after" arm. Designer ruling: a same-tick mix counts as violent (`environment.md:263-264`), so these are known instances of the ENV-07 wounded-then-drained gap, recorded on its ticket. Base commits: before `9299891a9`, after = that plus this branch.
