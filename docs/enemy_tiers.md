# Enemy Tier System

Technical documentation for the tiered enemy spawning system, stat multipliers, and spawn distribution.

---

## Overview

Enemies are spawned in four tiers with increasing difficulty. Each tier has a unique kind name, stat multipliers, starting equipment, AI behavior, and visual color in the frontend. The tier system drives combat difficulty scaling and loot progression.

**Primary files**: `src/core/enums.py` (`EnemyTier`), `src/systems/generator.py`, `src/core/items.py`

---

## Tier Definitions

```python
class EnemyTier(IntEnum):
    BASIC   = 0
    SCOUT   = 1
    WARRIOR = 2
    ELITE   = 3
```

---

## Stat Multipliers

Each tier modifies base goblin stats during spawning in `EntityGenerator.spawn()`:

| Tier | Kind Name | HP Mult | ATK Mult | Base DEF | SPD Mod | Start Level |
|------|-----------|---------|----------|----------|---------|-------------|
| BASIC (0) | `goblin` | 1.0× | 1.0× | 0 | +0 | 1 |
| SCOUT (1) | `goblin_scout` | 0.8× | 0.9× | 0 | +3 | 2 |
| WARRIOR (2) | `goblin_warrior` | 1.5× | 1.3× | 3 | -1 | 3 |
| ELITE (3) | `goblin_chief` | 2.5× | 1.8× | 6 | +0 | 5 |

### Base Stats (before multipliers)

Base goblin stats are rolled from RNG:
```
base_hp  = 15 + rng(0..10)   → range: 15–25
base_atk = 3 + rng(0..4)     → range: 3–7
base_spd = 8 + rng(0..4)     → range: 8–12
```

### Example Final Stats

| Tier | HP Range | ATK Range | DEF | SPD Range |
|------|----------|-----------|-----|-----------|
| BASIC | 15–25 | 3–7 | 0 | 8–12 |
| SCOUT | 12–20 | 3–6 | 0 | 11–15 |
| WARRIOR | 23–38 | 4–9 | 3 | 7–11 |
| ELITE | 38–63 | 5–13 | 6 | 8–12 |

Note: Elites start at level 5, so they also gain stat growth bonuses (+20 HP, +8 ATK, +4 DEF, +4 SPD from levels 1→5).

---

## Spawn Distribution

When spawning without a forced tier, the generator rolls a random tier:

| Tier | Probability | Weight |
|------|-------------|--------|
| BASIC | 55% | 55 |
| SCOUT | 25% | 25 |
| WARRIOR | 15% | 15 |
| ELITE | 5% | 5 |

```python
roll = rng.next_int(Domain.SPAWN, eid, tick, 0, 99)
if roll < 55:   tier = BASIC
elif roll < 80:  tier = SCOUT
elif roll < 95:  tier = WARRIOR
else:            tier = ELITE
```

### Forced Tier Spawning

Camp guards are spawned with explicit tiers:
- Camp chief: `generator.spawn(world, tier=EnemyTier.ELITE)`
- Camp guards: `generator.spawn(world, tier=EnemyTier.WARRIOR)`

The `near_pos` parameter spawns them adjacent to the camp center.

---

## Starting Equipment

Each tier spawns with predefined gear from `TIER_STARTING_GEAR`:

| Tier | Weapon | Armor | Accessory |
|------|--------|-------|-----------|
| BASIC | — | — | — |
| SCOUT | `goblin_blade` | — | — |
| WARRIOR | `goblin_blade` | `goblin_shield` | — |
| ELITE | `chief_axe` | `chief_plate` | — |

### Effective Stats with Equipment

| Tier | Effective ATK | Effective DEF | Notes |
|------|---------------|---------------|-------|
| BASIC | 3–7 | 0 | No equipment |
| SCOUT | 6–9 | 0 | +3 ATK from goblin_blade |
| WARRIOR | 7–12 | 5 | +3 ATK, +2 DEF from gear |
| ELITE | 13–21 | 16 | +8 ATK, +10 DEF from gear |

---

## Starting Potions

Entities may spawn with health potions:

| Tier | Potions |
|------|---------|
| BASIC | 1× small_hp_potion |
| SCOUT | 1× small_hp_potion |
| WARRIOR | 2× small_hp_potion |
| ELITE | 2× medium_hp_potion |

---

## Loot Tables

Each tier has a weighted loot table for additional random drops:

### BASIC
| Item | Weight |
|------|--------|
| `small_hp_potion` | 5 |
| `rusty_dagger` | 2 |
| `leather_vest` | 1 |

### SCOUT
| Item | Weight |
|------|--------|
| `small_hp_potion` | 4 |
| `goblin_blade` | 3 |
| `speed_ring` | 1 |

### WARRIOR
| Item | Weight |
|------|--------|
| `medium_hp_potion` | 3 |
| `goblin_blade` | 2 |
| `goblin_shield` | 2 |
| `chainmail` | 1 |

### ELITE
| Item | Weight |
|------|--------|
| `large_hp_potion` | 2 |
| `chief_axe` | 1 |
| `chief_plate` | 1 |
| `lucky_charm` | 1 |

The `roll_loot()` function performs weighted random selection using deterministic RNG.

---

## AI Behavior by Tier

| Tier | Initial State | Behavior |
|------|---------------|----------|
| BASIC | `WANDER` | Roams randomly, hunts on sight |
| SCOUT | `WANDER` | Roams randomly, hunts on sight, faster movement |
| WARRIOR | `WANDER` or `GUARD_CAMP` | Roams or guards camp, tanky fighter |
| ELITE | `WANDER` or `GUARD_CAMP` | Roams or guards camp, boss-tier threat |

Camp-spawned warriors and elites start in `GUARD_CAMP` state and patrol their camp radius.

---

## Frontend Visualization

Each tier has a distinct color for visual identification:

| Tier | Kind | Color | Hex |
|------|------|-------|-----|
| BASIC | goblin | Red | `#f87171` |
| SCOUT | goblin_scout | Orange | `#fb923c` |
| WARRIOR | goblin_warrior | Deep Red | `#dc2626` |
| ELITE | goblin_chief | Gold | `#fbbf24` |

All enemy tiers are rendered as circles. The hero is rendered as a diamond with a golden glow.

When inspecting an entity, the tier name is shown in brackets after the kind name:
```
#11 goblin_chief [Elite] Lv5
```

---

## XP Value by Tier

Kill XP scales with both level and tier:

```
xp = xp_per_kill_base × level × (1 + tier × 0.5)
```

| Tier | Level | XP Awarded |
|------|-------|------------|
| BASIC (0) | 1 | 25 |
| SCOUT (1) | 2 | 75 |
| WARRIOR (2) | 3 | 150 |
| ELITE (3) | 5 | 312 |

Higher-tier enemies are significantly more rewarding, incentivizing the hero to take on tougher fights.
