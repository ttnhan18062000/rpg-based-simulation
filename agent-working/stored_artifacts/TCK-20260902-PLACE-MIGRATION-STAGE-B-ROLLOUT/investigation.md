---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT
artifact_type: investigation
tags: [content, determinism]
---

# Investigation — TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT

`hero_guild_routing` composes 5 modules: `frontier_village_core` (CITY, already migrated in Stage A),
`hero_adventurers`, `mountain_pass`, `ruins_mystery_quest`, `goblin_camp_conflict`. Real union of worlds
affected by all 3 originally-edited modules confirmed via `grep -l`: 19 of 21 (not 17 — `dungeon_crawl`
and `quest_dense_frontier` use `goblin_camp_conflict`/`ruins_mystery_quest` without using
`frontier_village_core`). Only `highland_traverse` and `wilderness_survival` used none of the three.

Investigated those 2 remaining worlds directly rather than leaving them out:
- `highland_traverse` composes `settled_quarter` (`type: settlement`, real content, `hometown` region) —
  added a CITY Place.
- `wilderness_survival` composes `survivor_camp_shelter` (a wilderness outpost with a `healer_hut`) and
  `undead_battlefield` (a second, independent `haunted_battlefield`-named RUIN candidate, different
  `grid_bounds` from `ruins_mystery_quest`'s) — added CAMP and RUIN Places respectively.

Also checked `wolf_den_near_forest`'s `wolf_den` region (name suggests LAIR) and confirmed it should NOT
get a Place: `PlaceState.occupant_entity_id` (LAIR-kind) anchors a specific boss/creature, reusing the
real `boss_region_id` pattern — no such anchor exists in this generic wildlife-ecology content, and the
module's own description explicitly frames it as "proving contextual hostility instead of enemy-by-type."
