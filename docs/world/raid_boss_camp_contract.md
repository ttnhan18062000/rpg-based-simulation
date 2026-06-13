---
status: active
layer: engine
authority: P1
audience: agent
last_verified: 2026-06-13
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

### Camp clearing

A camp is cleared when all its associated monsters are killed. On clear:
- Camp entity is removed from world state
- `region.trauma_score -= 10`
- CAMP_CLEARED event broadcast (see [threat_and_consequences_contract.md](threat_and_consequences_contract.md))

**Known gap:** Camp-to-raid position anchoring is incomplete. The raid spawns at a hardcoded position (0,0) rather than near the camp's actual location. This is noted in camp.py comments as a Phase 1 stub.

---

## Raid — `raid.py`

### Trigger cadence

Raids are also checked every **500 ticks** independently of camp triggers. The camp-triggered path and the tick-cadence path can both fire.

### Raid composition

```
raid_size = 3 + camp.maturity  (integer — high-maturity camps send larger raids)
```

Raiders spawn as `goblin_raider` entities at `difficulty_tier=4`. Target: nearest settlement (currently hardcoded to position (0,0) — same anchor gap as camp position).

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
2. To add a new raid type: extend `raid.py` with a new raid composition. Fix the hardcoded (0,0) anchor before adding new raid types — position anchoring is a known gap.
3. To add a new boss type: add to `SPAWN_POOLS` and `DIFFICULTY_ZONES` in `spawn_config.py`. The idempotency lock is per region_id — if multiple boss types should coexist in one region, the locking mechanism needs extending.
4. To add a new spawn pool: extend `spawn_config.py`. Do not hardcode monster types in `spawn.py`.
