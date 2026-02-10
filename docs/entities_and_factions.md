# Entities & Factions

Technical documentation for the entity model, faction system, races, tiers, territory intrusion, and status effects.

---

## Overview

Every agent in the simulation is an `Entity`. Each entity belongs to exactly one **Faction**. Factions define inter-group relationships (hostile, neutral, allied) and territory ownership. The system is **data-driven** — adding new factions or races requires only registry configuration, not code changes in AI, combat, or movement logic.

**Primary files:** `src/core/models.py`, `src/core/faction.py`, `src/core/effects.py`, `src/core/enums.py`, `src/systems/generator.py`

---

## Entity Model (`src/core/models.py`)

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique, monotonic, never reused |
| `kind` | str | Type name (e.g. "hero", "goblin", "wolf") |
| `pos` | Vector2 | Current grid position |
| `stats` | Stats | HP, ATK, DEF, SPD, level, gold, stamina, etc. |
| `ai_state` | AIState | Current FSM state |
| `next_act_at` | float | Absolute time this entity can act again |
| `alive` | bool | Gate for scheduling |
| `faction` | Faction | Which faction this entity belongs to |
| `tier` | int | Enemy difficulty tier (0–3) |
| `home_pos` | Vector2 \| None | Spawn/respawn position |

### Extended Fields

| Field | Type | Description |
|-------|------|-------------|
| `inventory` | Inventory \| None | Items carried + equipment slots |
| `home_storage` | HomeStorage \| None | Hero's persistent home storage |
| `attributes` | Attributes \| None | 9 primary attributes (STR, AGI, etc.) |
| `attribute_caps` | AttributeCaps \| None | Attribute growth limits |
| `hero_class` | int | HeroClass enum value (0=NONE) |
| `skills` | list[SkillInstance] | Learned skills with runtime state |
| `class_mastery` | float | 0.0–100.0 |
| `effects` | list[StatusEffect] | Active buffs/debuffs |
| `traits` | list[TraitType] | Personality traits (2–4 per entity) |
| `quests` | list[Quest] | Tracked quests (hero only) |
| `known_recipes` | list[str] | Recipe IDs learned from blacksmith |
| `craft_target` | str \| None | Current crafting goal |
| `terrain_memory` | set[tuple] | Explored tile positions |
| `entity_memory` | dict | Last-seen positions of other entities |
| `vision_range` | int | Perception radius (Manhattan distance) |
| `engaged_ticks` | int | Consecutive ticks adjacent to a hostile |

### Effective Stat Methods

Equipment bonuses and status effects flow through `effective_*()` methods:

```python
entity.effective_atk()       # base + equipment + effects
entity.effective_def()
entity.effective_spd()
entity.effective_max_hp()
entity.effective_crit_rate()
entity.effective_evasion()
entity.effective_matk()      # magical attack
entity.effective_mdef()      # magical defense
```

### EntityRole

| Role | Value | Description |
|------|-------|-------------|
| HERO | 0 | Can use town buildings, AI goal-driven |
| MOB | 1 | Wild creature/enemy, guards territory |
| NPC | 2 | Town resident (future) |

---

## Faction System (`src/core/faction.py`)

### Faction Identity

| Faction | Value | Territory Tile |
|---------|-------|---------------|
| HERO_GUILD | 0 | TOWN |
| GOBLIN_HORDE | 1 | CAMP |
| WOLF_PACK | 2 | FOREST |
| BANDIT_CLAN | 3 | DESERT |
| UNDEAD | 4 | SWAMP |
| ORC_TRIBE | 5 | MOUNTAIN |

### Faction Relations

| Relation | Value | Behavior |
|----------|-------|----------|
| ALLIED | 0 | Will not attack; may cooperate |
| NEUTRAL | 1 | Ignore each other (unless provoked) |
| HOSTILE | 2 | Attack on sight |

**Default relations:** All factions are HOSTILE to every other faction. Same-faction entities are implicitly ALLIED.

### FactionRegistry

Data-driven registry that maps factions to territories and relations. Queried at runtime:

```python
reg = FactionRegistry.default()
reg.is_hostile(Faction.HERO_GUILD, Faction.GOBLIN_HORDE)  # True
reg.is_allied(Faction.HERO_GUILD, Faction.HERO_GUILD)     # True
reg.owns_tile(Faction.WOLF_PACK, Material.FOREST)         # True
reg.tile_owner(Material.CAMP)                              # Faction.GOBLIN_HORDE
reg.is_enemy_territory(Faction.HERO_GUILD, Material.CAMP)  # True
```

Entity `kind` strings are registered to factions:

| Kind | Faction |
|------|---------|
| `hero` | HERO_GUILD |
| `goblin`, `goblin_scout`, `goblin_warrior`, `goblin_chief` | GOBLIN_HORDE |
| `wolf`, `dire_wolf`, `alpha_wolf` | WOLF_PACK |
| `bandit`, `bandit_archer`, `bandit_chief` | BANDIT_CLAN |
| `skeleton`, `zombie`, `lich` | UNDEAD |
| `orc`, `orc_warrior`, `orc_warlord` | ORC_TRIBE |

---

## Territory System

Each faction owns a tile type via `TerritoryInfo`:

| Field | Type | Description |
|-------|------|-------------|
| `tile` | Material | The territory tile type |
| `atk_debuff` | float | Multiplier on intruder ATK (e.g. 0.7 = 30% reduction) |
| `def_debuff` | float | Multiplier on intruder DEF |
| `spd_debuff` | float | Multiplier on intruder SPD |
| `alert_radius` | int | How far intrusion alerts propagate |

### Default Territory Debuffs

| Faction | Tile | ATK Debuff | DEF Debuff | SPD Debuff | Alert Radius |
|---------|------|-----------|-----------|-----------|-------------|
| HERO_GUILD | TOWN | 0.6× | 0.6× | 0.8× | 6 |
| GOBLIN_HORDE | CAMP | 0.7× | 0.7× | 0.85× | 6 |
| WOLF_PACK | FOREST | 0.7× | 0.7× | 0.85× | 6 |
| BANDIT_CLAN | DESERT | 0.7× | 0.7× | 0.85× | 6 |
| UNDEAD | SWAMP | 0.7× | 0.7× | 0.85× | 6 |
| ORC_TRIBE | MOUNTAIN | 0.7× | 0.7× | 0.85× | 6 |

### Territory Intrusion

When an entity steps on hostile territory, `WorldLoop._process_territory_effects()` triggers:

1. **Stat Debuff** — `TERRITORY_DEBUFF` StatusEffect applied, refreshed each tick while on hostile tile, removed when entity leaves. Duration: `territory_debuff_duration` (3 ticks).

2. **Alert Propagation** — Same-faction defenders within `alert_radius` switch to `AIState.ALERT`, then seek and engage the intruder.

3. **Town Aura Damage** — Hostile entities on TOWN tiles lose `town_aura_damage` (2) HP/tick.

---

## Status Effect System (`src/core/effects.py`)

Generic system for temporary stat modifiers tracked on each entity.

### StatusEffect Fields

| Field | Type | Description |
|-------|------|-------------|
| `effect_type` | EffectType | Category |
| `remaining_ticks` | int | Duration; -1 = permanent, 0 = expired |
| `source` | str | Human-readable origin |
| `atk_mult` | float | ATK multiplier (1.0 = neutral) |
| `def_mult` | float | DEF multiplier |
| `spd_mult` | float | SPD multiplier |
| `crit_mult` | float | Crit rate multiplier |
| `evasion_mult` | float | Evasion multiplier |
| `hp_per_tick` | int | Flat HP change/tick (+regen, −DoT) |

### EffectType Enum

| Type | Value | Usage |
|------|-------|-------|
| TERRITORY_DEBUFF | 0 | Stat penalty for hostile territory |
| TERRITORY_BUFF | 1 | Stat bonus for home territory |
| POISON | 2 | DoT |
| BERSERK | 3 | ATK up, DEF down |
| SHIELD | 4 | Temporary DEF boost |
| HASTE | 5 | SPD boost |
| SLOW | 6 | SPD penalty |
| SKILL_BUFF | 7 | Buff from skill use |
| SKILL_DEBUFF | 8 | Debuff from enemy skill |

### Effect Lifecycle

1. **Applied:** Territory effects refreshed each tick; skill effects applied on use
2. **Ticked:** `remaining_ticks` decremented each tick, `hp_per_tick` applied
3. **Expired:** Effects with `remaining_ticks < 0` pruned automatically
4. **Queried:** `Entity.effective_*()` methods aggregate all active multipliers (multiplicative stacking)

---

## Races & Tiers

### Enemy Tiers

| Tier | Enum | Spawn Weight | Start Level |
|------|------|-------------|-------------|
| BASIC | 0 | 55% | 1 |
| SCOUT | 1 | 25% | 2 |
| WARRIOR | 2 | 15% | 3 |
| ELITE | 3 | 5% | 5 |

### Tier Stat Multipliers (Goblin Base)

| Tier | Kind | HP Mult | ATK Mult | Base DEF | SPD Mod |
|------|------|---------|----------|----------|---------|
| BASIC | `goblin` | 1.0× | 1.0× | 0 | +0 |
| SCOUT | `goblin_scout` | 0.8× | 0.9× | 0 | +3 |
| WARRIOR | `goblin_warrior` | 1.5× | 1.3× | 3 | -1 |
| ELITE | `goblin_chief` | 2.5× | 1.8× | 6 | +0 |

### Race Variants

Each race has three tier names:

| Race | Basic (T0) | Mid (T1–T2) | Elite (T3) |
|------|-----------|-------------|-----------|
| Goblin | `goblin` | `goblin_scout` / `goblin_warrior` | `goblin_chief` |
| Wolf | `wolf` | `dire_wolf` | `alpha_wolf` |
| Bandit | `bandit` | `bandit_archer` | `bandit_chief` |
| Undead | `skeleton` | `zombie` | `lich` |
| Orc | `orc` | `orc_warrior` | `orc_warlord` |

### Race Stat Modifiers (`RACE_STAT_MODS`)

Applied on top of tier multipliers:

| Race | HP Mult | ATK Mult | DEF Mod | SPD Mod | Crit | Evasion | Luck |
|------|---------|----------|---------|---------|------|---------|------|
| Wolf | 0.8× | 1.0× | +0 | +2 | 10% | 10% | 0 |
| Bandit | 1.0× | 0.9× | +1 | +1 | 8% | 5% | 2 |
| Undead | 1.3× | 0.8× | +3 | -2 | 3% | 0% | 0 |
| Orc | 1.2× | 1.2× | +2 | -1 | 5% | 2% | 1 |

### Spawning

**Goblins:** `EntityGenerator.spawn()` — tier-based stat multipliers, starting gear, loot tables.

**Race mobs:** `EntityGenerator.spawn_race(world, race, tier, near_pos)` — applies race stat mods on top of tier multipliers, picks kind name from `RACE_TIER_KINDS`, equips race-specific gear, sets faction from `RACE_FACTION`.

---

## Hero Spawn

Heroes spawn at town center with:

1. Random class assignment (Warrior/Ranger/Mage/Rogue)
2. Attributes: base 5 + class bonuses + small random variance (0–2)
3. Attribute caps: 15 + class cap bonuses
4. Stamina: 50 + END×2
5. Race skills (Rally, Second Wind) + first class skill
6. Starting gear: `iron_sword`, `leather_vest`, 3× `small_hp_potion`
7. Home storage (30 slots)

Uses the `EntityBuilder` fluent API (see `design_patterns.md`).

---

## Extending the System

### Adding a New Faction

```python
# 1. Add to Faction enum
class Faction(IntEnum):
    ...
    NEW_FACTION = 6

# 2. Register in FactionRegistry.default()
reg.set_relation(Faction.NEW_FACTION, Faction.HERO_GUILD, FactionRelation.HOSTILE)
reg.set_territory(Faction.NEW_FACTION, TerritoryInfo(
    tile=Material.NEW_TERRAIN,
    atk_debuff=0.7, def_debuff=0.7, spd_debuff=0.85, alert_radius=6,
))
reg.register_kind("new_mob", Faction.NEW_FACTION)
```

No changes to AI handlers, combat logic, or movement code.

### Adding a New Status Effect

```python
# 1. Add to EffectType enum
# 2. Create a factory function
# 3. Apply in combat or ability code
entity.effects.append(my_effect())
```

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `territory_debuff_duration` | 3 | Ticks debuff lasts after leaving |
| `territory_alert_radius` | 6 | Intrusion alert propagation range |
| `town_aura_damage` | 2 | HP lost/tick by hostiles in town |
| `town_passive_heal` | 1 | HP regained/tick by heroes in town |
| `hero_heal_per_tick` | 3 | HP regained/tick by resting heroes |
