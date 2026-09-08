---
status: active
layer: engine
authority: P1
audience: agent
last_verified: 2026-09-04
---

# Raid, Boss, and Camp Contract

**Source:** `src/world/raid.py`, `src/world/boss.py`, `src/world/camp.py`, `src/world/spawn.py`, `src/world/spawn_config.py`
**Related docs:** [ecology_and_calamity_contract.md](ecology_and_calamity_contract.md), [threat_and_consequences_contract.md](threat_and_consequences_contract.md), [docs/mechanics/05_world_evolution.md](../mechanics/05_world_evolution.md)

---

## Purpose

Camps are hostile entity clusters that grow over time. When camps reach maturity they trigger raids against the nearest settlement. Raids are coordinated monster attacks. Bosses are elite entities that spawn when a region reaches both high maturity and high trauma.

---

## Camp — `camp.py`

### Growth

Camps grow passively each tick:

```
maturity += 0.05 per tick
maturity += 0.05 × 1.5 = 0.075 per tick if region.trauma > 50
```

### Monster spawning

Camps spawn monsters up to a per-camp cap:

```
monster_cap = max(2, int(camp.maturity / 10))
```

Spawn runs every **50 ticks** (see spawn section). If the camp's current monster count is below cap, new monsters are spawned using the region's difficulty zone table.

### Raid trigger

When `camp.maturity >= 80`, the camp triggers a raid. After triggering, maturity resets to 50 (partial reset — camp does not fully dissolve unless cleared).

**Nest fork (`TCK-20260904-CAMP-NEST-CLASSIFICATION`, `ENABLE_CAMP_NEST_SPREAD`, default OFF):**
inside this same raid-trigger gate, a camp classified as Nest kind (see "Camp/Nest classification"
below) takes a spread outcome instead of a raid when the flag is ON: `CampService.process_camps()`
spawns one parentless same-kind offspring via `EntityGenerator.spawn_natural_creature_offspring()`
rather than calling `RaidService.check_for_raid()`. The cost is identical to the raid outcome it
replaces — `maturity_delta=-20.0` (a relative delta applied against whatever `camp.maturity` is
at trigger time, **not** an absolute set-to-50 — see the raid outcome's own imprecise "resets to
50" phrasing above) and `last_raid_tick_set` reset to the current tick, reusing the same 500-tick
cooldown. Camp-classified camps (goblin, orc) always take the raid outcome, flag or no flag.

### Camp/Nest classification

Race kinds resolve to City / Camp / Nest / Excluded based on `data/content/living/races.yaml`
`natural_traits`/`drive_profile`/`cognition_profile` — see
[docs/mechanics/05_world_evolution.md §6](../mechanics/05_world_evolution.md) "Camp/Nest
Classification & Nest Spread" for the full 13-race table and goblin-contradiction resolution. The
only code projection is `CampService.NEST_RACE_KINDS = frozenset({"wolf", "spider", "troll",
"slime"})` — City and Excluded races never populate `CampState.kind`, so no code-side City/Excluded
constant exists.

### Camp clearing

A camp is cleared when all its associated monsters are killed. On clear:
- Camp entity is removed from world state
- `region.trauma_score -= 10`
- CAMP_CLEARED event broadcast (see [threat_and_consequences_contract.md](threat_and_consequences_contract.md))

**Resolved (`TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX`):** camp-triggered raids now spawn anchored
at the camp's own position and target the nearest real `PlaceKind.CITY` place in `state.places`,
via `RaidService.spawn_raid(origin, target, raid_size)`. If no CITY place exists to target, the
raid is skipped entirely for that tick — no raiders, no maturity cost, no cooldown reset. The
global (non-camp) tick-cadence raid path (`RaidService.check_for_raid()`) is unchanged and still
uses the `(0,0)` anchor — see "Raid — `raid.py`" below.

### World-gen construction (`TCK-20260904-CAMPSTATE-PLACE-BRIDGE`)

`CampState` instances are constructed at world-compile time, not authored directly. A content
region declaring a `PlaceSpec(kind=CAMP` or `NEST, creature_kind=<race>)` causes
`WorldCompiler.compile()` to build a companion `CampState`, keyed by the same id as its
`PlaceState` counterpart (`state.places[place_id]` and `state.camps[place_id]` share one key),
with `CampState.kind` set to the declared `creature_kind`. `CampState`'s other fields
(`maturity`, `active`, `faction`, `last_raid_tick`, `totem_tier`, `stockpile`,
`palisade_integrity`) are left at their dataclass defaults — no content-schema field carries
values for them yet.

`creature_kind` is `Optional[str]`, `None` by default, and validated against the Camp+Nest race
set (`{goblin, orc, wolf, spider, troll, slime}`) from
[docs/mechanics/05_world_evolution.md §6](../mechanics/05_world_evolution.md). It is opt-in: a
`CAMP`/`NEST`-kind `PlaceSpec` that doesn't set it produces a `PlaceState` with no companion
`CampState` — the bridge is inert unless content explicitly declares the field. No content on
disk sets it today (including `hero_guild_routing`'s `goblin_camp_place`), so `state.camps`
remains `{}` for every currently-compiled world; a future ticket migrating real content to set
`creature_kind` is the point `CampService`/`CreatureTerritoryService` first receive non-empty
`state.camps` data in a real compiled world.

`CampService` and `CreatureTerritoryService` themselves are unchanged by this bridge — both
already read `state.camps` unconditionally every tick (see "Growth"/"Monster spawning"/"Raid
trigger" above), they simply had nothing to iterate before this ticket gave `state.camps` a real
construction path.

### Faction EXPAND_TERRITORY consumption (`TCK-20260904-FACTION-EXPAND-DIRECTIVE`)

`CampService.process_camps()` takes a new trailing-optional `faction_directives: list | None =
None` parameter, threaded in from `WorldDynamicsSystem.resolve_dynamics()` (itself threaded from
`pipeline.py`'s `refine()`, which computes `faction_directives` via `FactionDecisionPhase.execute()`
at the earlier `faction_decision` phase, same tick). Inside the existing per-camp loop, immediately
after the "Growth" maturity-evolution step and before "Monster spawning": if any directive in
`faction_directives` has `directive_kind == "EXPAND_TERRITORY"` and `target_region` equal to the
camp's own region id, that camp's `maturity_delta` is additively boosted by
`CampService.EXPAND_TERRITORY_MATURITY_BOOST` (`1.0`) via `dataclasses.replace()` on the existing
`CampUpdate` — the trauma-scaled growth delta from "Growth" above is preserved, not overwritten.

**Interaction with raid trigger:** if the same camp also crosses the raid-trigger gate
(`maturity >= 80`) in the same tick, the raid-trigger step's own unconditional
`CampUpdate(maturity_delta=-20.0, ...)` runs later in the same loop iteration and **overwrites**
(not merges) the entry — the EXPAND_TERRITORY boost is silently discarded that tick. This is the
same pre-existing overwrite behavior the raid-trigger step already applies to the plain "Growth"
delta; EXPAND_TERRITORY introduces no new hazard here.

**Real-content reachability:** as with the world-gen construction bridge above, `state.camps` is
`{}` in every currently-compiled real world today (no content sets `creature_kind`), so this
consumption branch is real and unit-tested (constructing `state.camps` directly, matching this
file's existing test pattern) but has zero observable effect in any real compiled world today —
wired but content-gap-inert, not a defect.

---

## Raid — `raid.py`

### Trigger cadence

Raids are also checked every **500 ticks** independently of camp triggers. The camp-triggered path and the tick-cadence path can both fire.

### Raid composition

```
raid_size = 3 + camp.maturity  (integer — high-maturity camps send larger raids)
```

Raiders spawn as `goblin_raider` entities at `difficulty_tier=4`. Target: nearest settlement —
**camp-triggered raids** now resolve this to the real nearest `PlaceKind.CITY` place
(`TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX`, see "Camp — `camp.py`" above). The **global
(non-camp) tick-cadence path** (`RaidService.check_for_raid()`) still hardcodes both origin and
target to `(0,0)` — deliberately left unchanged by that ticket's own Out of Scope, since it
already has real, observable behavior tied to it and changing it was not required to fix the
camp-triggered discard bug.

### Raid outcome

- Raid reaches settlement → settlement takes damage, faction influence decreases
- Raiders killed before reaching settlement → raid suppressed; trauma reduced

---

## Boss — `boss.py`

### Spawn conditions

Two conditions must both be met:

1. `camp.maturity >= 50`
2. `region.trauma >= 20`

Both gates must pass simultaneously. If only one is met, no boss spawns.

### Idempotency

Boss spawn is idempotent: `boss_region_id` is stored in the boss entity's properties at spawn time. Before spawning, the system checks whether a boss with `boss_region_id == region.id` already exists in the world. If one exists (alive), no second boss spawns.

Idempotency is tracked by entity properties, not by entity position — moving the boss to another region does not cancel the idempotency lock.

**Lair — Place-scoped generalization (`TCK-20260904-LAIR-ENTITY-ANCHOR`):** `BossService.check_for_lair_spawn` is a direct sibling of `check_for_boss_spawn`, generalizing the same entity-property idempotency pattern from per-`region_id` keying to per-`place_id` keying, so multiple LAIR-kind Places within one Region each get an independent, idempotent spawn slot (the collision the plain region-scoped mechanism couldn't handle). It reuses the exact same spawn gate (`state.maturity >= 50`, `region.trauma_score >= 20`, read from the LAIR Place's parent Region) and the exact same `difficulty_tier=5` convention, but keys occupancy off `identity.properties["lair_place_id"]` (set to the occupying Place's `place_id`) instead of `boss_region_id`, and spawns `kind="dragonkin"` occupants directly at the Place's own `position` rather than a computed region-center. `PlaceState.occupant_entity_id` is *not* written by this mechanism — the lock lives on the occupant entity's identity properties, mirroring `check_for_boss_spawn`'s own pattern exactly; `occupant_entity_id` remains a schema-only, write-never field pending a future ticket (plausibly idea 48's dissolution-on-death mechanism) that would need to durably read "which entity occupies this Place."

### Boss stats

World bosses spawn at `difficulty_tier=4`. Specific stat tables are in `spawn_config.py` under `DIFFICULTY_ZONES`.

### Boss defeat

On death, the boss triggers the consequence chain in `consequences.py` (trauma −30, retaliation reset). See [threat_and_consequences_contract.md](threat_and_consequences_contract.md).

---

## Spawn — `spawn.py` + `spawn_config.py`

### Cadence

Spawn runs every **50 ticks**.

### Density formula

```
density = max(2, int((region.area / 10_000) * 2.0 * (1 + region.hazard_level)))
```

Regions with higher hazard spawn more monsters up to density cap.

### Spawn pools

`spawn_config.py` defines `SPAWN_POOLS` (monster types by biome) and `DIFFICULTY_ZONES` (stat tiers by difficulty_tier value 1–5). Spawn draws from the pool matching the region's biome, then applies the difficulty zone stats.

### Faction-aware spawning

Monsters spawned in monster-controlled regions (influence ≤ −50) receive a faction alignment tag. This affects how the threat classifier labels them for entity routing.

---

## Regression tests

- `tests/integration/world/test_long_run_stability.py` — maturity growth, monster cap, raid trigger threshold
- `tests/integration/world/test_long_run_stability.py` — raid size formula, raid outcome (suppressed vs successful)
- `tests/certification/test_cert_long_run_stability.py` — spawn condition gating, idempotency, boss defeat consequences
- `tests/unit/worldgeneration/test_generator.py` — density formula, spawn pool selection, difficulty zone application

---

## Extension rules

1. To add a new camp type: extend `camp.py` with a new camp variant and growth rate. Monster cap formula should remain `max(2, maturity/10)` unless the variant has a documented reason to differ.
   - **Precedent (`TCK-20260904-CAMP-NEST-CLASSIFICATION`):** the Nest spread outcome above is a
     variant of the raid-trigger step, not the monster-cap/growth-rate steps — it substitutes the
     trigger's *outcome* for Nest-classified camps while reusing the unmodified growth rate,
     monster cap, and cadence constants verbatim.
2. To add a new raid type: extend `raid.py` with a new raid composition. Reuse
   `RaidService.spawn_raid(origin, target, raid_size)` (`TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX`)
   for the actual composition step rather than duplicating it — the global tick-cadence path's own
   `(0,0)` anchor is a deliberate, scoped-out-of-that-ticket choice, not a gap to fix reflexively;
   only change it with a real reason and its own regression coverage.
3. To add a new boss type: add to `SPAWN_POOLS` and `DIFFICULTY_ZONES` in `spawn_config.py`. The idempotency lock is per region_id — if multiple boss types should coexist in one region, the locking mechanism needs extending.
   - **Addressed for LAIR-kind Places (`TCK-20260904-LAIR-ENTITY-ANCHOR`):** `check_for_lair_spawn` closes this gap specifically for LAIR-kind Places via a parallel per-`place_id` lock (`identity.properties["lair_place_id"]`), so multiple LAIR Places can coexist in one Region without colliding. The original `world_boss`/`ancient_sentinel` mechanism (`check_for_boss_spawn`) is unchanged and remains region-scoped by design — a Region should still have at most one `world_boss`.
4. To add a new spawn pool: extend `spawn_config.py`. Do not hardcode monster types in `spawn.py`.
