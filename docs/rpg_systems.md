# RPG Systems — Technical Documentation

This document describes all RPG mechanics implemented in the deterministic concurrent simulation engine, including the attribute system, classes, skills, skill effects, stamina, combat formulas, quests, and world structures.

---

## 1. Primary Attributes

Every entity can have an `Attributes` dataclass (`src/core/attributes.py`) with 6 primary stats:

| Attribute | Field | Effect |
|-----------|-------|--------|
| **STR** | `str_` | Boosts attack damage (+2% per point) |
| **AGI** | `agi` | Boosts SPD (+0.4/pt), crit (+0.4%/pt), evasion (+0.3%/pt) |
| **VIT** | `vit` | Boosts max HP (+2/pt), DEF (+0.3/pt) |
| **INT** | `int_` | Boosts XP gain (+1%/pt) |
| **WIS** | `wis` | Boosts XP gain (+0.5%/pt), luck (+0.3/pt) |
| **END** | `end` | Boosts max stamina (+2/pt), max HP (+0.5/pt) |

### 1.1 Attribute Caps

Each attribute has a cap (`AttributeCaps` dataclass) that limits growth:
- **Default cap**: 15 per attribute
- **Class bonuses**: Each class adds +5–10 to its primary attribute caps
- **Level-up**: All caps increase by +5 per level

### 1.2 Derived Stats

Attributes feed into derived combat stats via formulas in `attributes.py`:

| Derived Stat | Formula |
|-------------|---------|
| Max HP | `base + VIT×2 + END×0.5` |
| ATK | `base + STR×0.5` |
| DEF | `base + VIT×0.3` |
| SPD | `base + AGI×0.4` |
| Crit Rate | `base + AGI×0.004` |
| Evasion | `base + AGI×0.003` |
| Luck | `base + WIS×0.3` |
| Max Stamina | `base + END×2` |
| XP Multiplier | `1.0 + INT×0.01 + WIS×0.005` |

### 1.3 Attribute Training

Attributes grow fractionally through actions using `train_attributes()`:

| Action | Trained Attributes | Rate |
|--------|-------------------|------|
| `attack` | STR +0.015, VIT +0.005 |
| `move` | AGI +0.008, END +0.005 |
| `harvest` | STR +0.005, END +0.008 |
| `loot` | WIS +0.005 |
| `cast` | INT +0.012, WIS +0.005 |
| `rest` | END +0.01, WIS +0.003, VIT +0.005 |

Fractional accumulation: e.g. 67 attacks → +1 STR. Training never exceeds the cap.

### 1.4 Level-Up Attribute Gains

On each level-up (`level_up_attributes()`):
- All 6 primary attributes: **+2** (capped)
- All 6 attribute caps: **+5**

---

## 2. Stamina System

Every entity has `stamina` and `max_stamina` fields on `Stats`.

### 2.1 Stamina Costs

| Action | Stamina Cost |
|--------|-------------|
| Attack | 3 |
| Move | 1 |
| Harvest | 2 |

### 2.2 Stamina Regeneration

Regeneration occurs each tick in `WorldLoop._tick_stamina_and_skills()`:

| State | Regen/Tick |
|-------|-----------|
| RESTING_IN_TOWN, IDLE | 5 |
| VISIT_SHOP, VISIT_BLACKSMITH, VISIT_GUILD, VISIT_CLASS_HALL, VISIT_INN | 4 |
| All other states | 1 |

Stamina is capped at `max_stamina`.

---

## 3. Hero Classes

Defined in `src/core/classes.py`. Each hero is assigned a class at spawn.

### 3.1 Base Classes

| Class | STR | AGI | VIT | INT | WIS | END | Cap Bonuses | Breakthrough |
|-------|-----|-----|-----|-----|-----|-----|-------------|-------------|
| **Warrior** | +3 | +0 | +2 | +0 | +0 | +1 | STR+10, VIT+5 | → Champion |
| **Ranger** | +0 | +3 | +0 | +0 | +1 | +2 | AGI+10, END+5 | → Sharpshooter |
| **Mage** | +0 | +0 | +0 | +3 | +2 | +1 | INT+10, WIS+5 | → Archmage |
| **Rogue** | +1 | +2 | +0 | +0 | +1 | +2 | AGI+5, STR+5, WIS+5 | → Assassin |

### 3.2 Breakthroughs

When level and attribute thresholds are met, heroes can advance to elite classes:

| From | To | Level Req | Attr Req | Talent |
|------|----|-----------|----------|--------|
| Warrior | Champion | 10 | STR ≥ 30 | Unyielding |
| Ranger | Sharpshooter | 10 | AGI ≥ 30 | Eagle Eye |
| Mage | Archmage | 10 | INT ≥ 30 | Mana Overflow |
| Rogue | Assassin | 10 | AGI ≥ 25 | Shadow Dance |

Breakthrough check: `can_breakthrough(hero_class, level, attributes)`

---

## 4. Skills

### 4.1 Skill Definitions (`SkillDef`)

Each skill has: `name`, `skill_type` (ACTIVE/PASSIVE), `target`, `power`, `stamina_cost`, `cooldown`, `level_req`, `class_req`, `gold_cost`, `description`.

### 4.2 Class Skills

| Warrior | Ranger | Mage | Rogue |
|---------|--------|------|-------|
| Power Strike (Lv1) | Quick Shot (Lv1) | Arcane Bolt (Lv1) | Backstab (Lv1) |
| Shield Wall (Lv3) | Evasive Step (Lv3) | Frost Shield (Lv3) | Shadowstep (Lv3) |
| Battle Cry (Lv5) | Mark Prey (Lv5) | Mana Surge (Lv5) | Poison Blade (Lv5) |

### 4.3 Race Skills

| Race | Skills |
|------|--------|
| Hero | Rally, Second Wind |
| Wolf | Pack Hunt, Feral Bite |
| Goblin | Ambush, Quickdraw |
| Orc | Berserker Rage, War Cry |
| Undead | Drain Life |

### 4.4 Skill Instances (`SkillInstance`)

Each entity holds `SkillInstance` objects with runtime state:
- `cooldown_remaining` — ticks until ready (ticked down each world tick)
- `mastery` — 0.0 to 100.0, gained by using the skill
- `times_used` — total use count

### 4.5 Mastery Tiers

| Tier | Mastery | Power Bonus | Stamina Reduction | Cooldown Reduction |
|------|---------|-------------|-------------------|--------------------|
| 0 | 0–24% | — | — | — |
| 1 | 25–49% | — | −10% | — |
| 2 | 50–74% | +20% | −10% | — |
| 3 | 75–99% | +20% | −20% | −1 tick |
| 4 | 100% | +35% | −25% | −1 tick |

### 4.6 Skill Modifiers & Effects

Skills can define stat modifiers that create temporary `StatusEffect`s on use:

| Modifier | Field | Description |
|----------|-------|-------------|
| ATK mod | `atk_mod` | % change to ATK (e.g. +0.2 = +20%) |
| DEF mod | `def_mod` | % change to DEF |
| SPD mod | `spd_mod` | % change to SPD |
| Crit mod | `crit_mod` | % change to crit rate |
| Evasion mod | `evasion_mod` | % change to evasion |
| HP mod | `hp_mod` | Instant heal as % of max HP (SELF skills) |
| Duration | `duration` | Ticks the buff/debuff lasts |

When a skill with `duration > 0` and at least one non-zero modifier is used:
- **SELF / AREA_ALLIES** targets → applies a `SKILL_BUFF` effect to caster/allies
- **SINGLE_ENEMY / AREA_ENEMIES** targets → applies a `SKILL_DEBUFF` effect to enemies

Modifiers are converted to multipliers: `atk_mod=0.2` → `atk_mult=1.2`, `atk_mod=-0.15` → `atk_mult=0.85`.

### 4.7 Status Effects (`StatusEffect`)

Defined in `src/core/effects.py`. Effects are temporary stat modifiers tracked on each entity.

| Field | Type | Description |
|-------|------|-------------|
| `effect_type` | `EffectType` | TERRITORY_BUFF/DEBUFF, SKILL_BUFF/DEBUFF, etc. |
| `remaining_ticks` | int | `-1` = permanent, `>0` = timed, `0` = expired |
| `source` | str | Human-readable origin (e.g. "Shield Wall") |
| `atk_mult` | float | ATK multiplier (1.0 = neutral) |
| `def_mult` | float | DEF multiplier |
| `spd_mult` | float | SPD multiplier |
| `crit_mult` | float | Crit rate multiplier |
| `evasion_mult` | float | Evasion multiplier |
| `hp_per_tick` | int | HP change per tick (+regen, −DoT) |

Multiple effects stack **multiplicatively** (e.g. two +20% ATK buffs → `1.2 × 1.2 = 1.44×`).

Factory function: `skill_effect(atk_mod, def_mod, ..., is_debuff)` in `src/core/effects.py`.

---

## 5. Quest System

Defined in `src/core/quests.py`. Heroes receive quests at the **Adventurer's Guild**.

### 5.1 Quest Types

| Type | Target | Completion Condition |
|------|--------|---------------------|
| **HUNT** | Enemy kind (e.g. "goblin") | Kill `target_count` enemies of that kind |
| **EXPLORE** | Map coordinate | Move within 2 tiles of `target_pos` |
| **GATHER** | Item ID (e.g. "herb") | Collect `target_count` items via loot or harvest |

### 5.2 Quest Model (`Quest`)

| Field | Type | Description |
|-------|------|-------------|
| `quest_id` | str | Unique identifier |
| `quest_type` | QuestType | HUNT, EXPLORE, or GATHER |
| `title` / `description` | str | Display text |
| `target_kind` | str | Enemy kind or item ID |
| `target_pos` | Vector2 \| None | For EXPLORE quests |
| `target_count` | int | Required kills/items |
| `progress` | int | Current count |
| `completed` | bool | True when done |
| `gold_reward` / `xp_reward` | int | Completion rewards |
| `item_reward` | str | Optional item reward |

### 5.3 Quest Templates

10 built-in templates with level gating:

| Template | Type | Min Level | Targets |
|----------|------|-----------|--------|
| hunt_goblin | HUNT | 1 | goblin, goblin_scout, goblin_warrior |
| hunt_wolf | HUNT | 1 | wolf, dire_wolf |
| hunt_bandit | HUNT | 2 | bandit, bandit_archer, bandit_chief |
| hunt_undead | HUNT | 3 | skeleton, zombie |
| hunt_orc | HUNT | 4 | orc, orc_warrior |
| gather_herbs | GATHER | 1 | herb |
| gather_ore | GATHER | 2 | iron_ore |
| gather_pelts | GATHER | 1 | wolf_pelt |
| explore_region | EXPLORE | 1 | random map coordinate |

Rewards scale with `count` and `hero_level` (×1.0 + level×0.1).

### 5.4 Quest Generation

`generate_quest(hero_level, existing_quest_ids, rng, grid_width, grid_height)` picks a random eligible template, rolls target kind, count, and rewards. Duplicate quest IDs are skipped.

### 5.5 Quest Limits

- **MAX_ACTIVE_QUESTS**: 3 per hero
- Completed quests are pruned periodically (every 50 ticks)

### 5.6 Quest Progress Tracking

| Quest Type | Hook Location | Trigger |
|-----------|--------------|--------|
| HUNT | `CombatAction.apply()` | On enemy kill, matches `defender.kind` |
| GATHER | `WorldLoop._process_item_actions()` | On LOOT or HARVEST, matches item ID |
| EXPLORE | `WorldLoop._tick_quests()` | Each tick, checks manhattan distance ≤ 2 |

On completion, rewards (gold + XP) are immediately added to the hero's stats.

### 5.7 Guild Integration

`VisitGuildHandler` in `src/ai/states.py`:
1. Hero walks to the Guild building
2. Reveals camp locations and resource nodes (intel)
3. If hero has fewer than 3 active quests → generates a new quest via `generate_quest()`
4. Provides material hints and terrain tips as goals

---

## 6. Enhanced Stats

Every entity has a `Stats` dataclass with:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `hp` / `max_hp` | int | 20 | Health |
| `atk` | int | 5 | Base attack |
| `def_` | int | 0 | Base defense |
| `spd` | int | 10 | Speed (action frequency) |
| `luck` | int | 0 | Crit/evasion modifier |
| `crit_rate` / `crit_dmg` | float | 0.05 / 1.5 | Critical hit stats |
| `evasion` | float | 0.0 | Dodge chance |
| `level` / `xp` / `xp_to_next` | int | 1/0/100 | Leveling |
| `gold` | int | 0 | Currency |
| `stamina` / `max_stamina` | int | 50 | Action resource |

---

## 7. Entity Model Extensions

`Entity` (`src/core/models.py`) now includes:

| Field | Type | Description |
|-------|------|-------------|
| `attributes` | `Attributes \| None` | Primary stats (STR, AGI, etc.) |
| `attribute_caps` | `AttributeCaps \| None` | Growth limits |
| `hero_class` | `int` | HeroClass enum value (0=NONE) |
| `skills` | `list[SkillInstance]` | Learned skills |
| `class_mastery` | `float` | 0.0–100.0 |
| `effects` | `list[StatusEffect]` | Active buffs/debuffs |
| `quests` | `list[Quest]` | Tracked quests |

---

## 8. Map Structures

### 8.1 New Tile Types

| Tile | Value | Walkable | Description |
|------|-------|----------|-------------|
| ROAD | 10 | Yes | Speed bonus (+30%) for movement |
| BRIDGE | 11 | Yes | Speed bonus, crosses water |
| RUINS | 12 | Yes | Explorable structures |
| DUNGEON_ENTRANCE | 13 | Yes | Future dungeon access point |
| LAVA | 14 | No | Impassable hazard |

### 8.2 Roads

Generated from town center to the 3 closest camps and 2 closest region centers using axis-aligned paths. Only placed on FLOOR tiles. Config: `road_from_town: bool`.

### 8.3 Ruins

4 scattered 3×3 ruins patches placed on FLOOR/ROAD tiles, at least 8 tiles apart and not too close to town. Config: `num_ruins: int`.

### 8.4 Dungeon Entrances

2 single-tile entrances placed in remote locations (FLOOR, MOUNTAIN, or FOREST), far from town. Config: `num_dungeon_entrances: int`.

---

## 9. Town Buildings

| Building | Position | Type | Service |
|----------|----------|------|---------|
| General Store | Top-left | `store` | Buy/sell items |
| Blacksmith | Top-right | `blacksmith` | Craft items from materials + gold |
| Adventurer's Guild | Bottom-center | `guild` | Intel about camps and materials |
| Class Hall | Bottom-left | `class_hall` | Learn class skills, attempt breakthroughs |
| Traveler's Inn | Bottom-right | `inn` | Rapid HP/stamina recovery |

### 9.1 New AI States

| State | Description |
|-------|-------------|
| `VISIT_CLASS_HALL` | Hero visits Class Hall to learn/upgrade skills |
| `VISIT_INN` | Hero rests at Inn for faster recovery |

---

## 10. Hero Spawn

Heroes spawn at town center with:
1. Random class assignment (Warrior/Ranger/Mage/Rogue)
2. Attributes: base 5 + class bonuses + small random variance (0–2)
3. Attribute caps: 15 + class cap bonuses
4. Stamina: 50 + END×2
5. Race skills (Rally, Second Wind) + first class skill at Lv1
6. Starting gear: iron_sword, leather_vest, 3× small_hp_potion

---

## 11. World Loop Integration

The `WorldLoop._step()` tick cycle now includes:

1. **Scheduling & AI decisions** — standard phases
2. **Conflict resolution** — including USE_SKILL action type
3. **Apply actions** — move, attack, harvest, loot, USE_SKILL (damage + buff/debuff application)
4. **Heal resting entities**
5. **Territory effects** — apply debuffs and alerts
6. **Status effects** — tick down durations, apply `hp_per_tick`, remove expired
7. **Resource nodes** — cooldown ticking
8. **Level-up checks** — including attribute level-up gains
9. **Stamina regen & skill cooldowns** — `_tick_stamina_and_skills()`
10. **Memory updates**
11. **Quest ticking** — EXPLORE completion checks, completed quest pruning
12. **Goal updates**

---

## 12. API & Frontend

### 12.1 API Schema Extensions

New fields on `EntitySchema`:
- `stamina`, `max_stamina` (int)
- `attributes` (`AttributeSchema` — str, agi, vit, int, wis, end)
- `attribute_caps` (`AttributeCapSchema`)
- `hero_class` (string: "warrior", "mage", etc.)
- `skills` (list of `SkillSchema` with mastery, cooldown, power)
- `class_mastery` (float)
- `active_effects` (list of `EffectSchema` — effect_type, source, remaining_ticks, atk/def/spd_mult)
- `quests` (list of `QuestSchema` — quest_id, quest_type, title, description, progress, target_count, rewards, completed)

### 12.2 Frontend Updates

- **TypeScript types**: `EntityAttributes`, `EntityAttributeCaps`, `EntitySkill`, `EntityEffect`, `EntityQuest` interfaces
- **InspectPanel sections**:
  - **Stamina bar** — colored progress bar
  - **Attributes** — 6-stat grid with caps/bars + class mastery bar
  - **Skills** — cooldowns, mastery, ready/CD status
  - **Active Effects** — buff (▲ green) / debuff (▼ red) with stat modifiers and remaining ticks
  - **Equipment** — weapon, armor, accessory, inventory bag
  - **Quests** — title, type badge, progress bar, gold/XP reward display, completion checkmark
  - **Goals & Thoughts** — AI decision context
- **Tile colors**: ROAD (#5a5040), BRIDGE (#4a6050), RUINS (#4a4035), DUNGEON_ENTRANCE (#6a3040), LAVA (#8a3000)
- **State colors**: VISIT_CLASS_HALL (#c084fc), VISIT_INN (#fb923c)
- **Legend**: Added Class Hall, Inn, Road, Ruins, Dungeon entries

---

## 13. File Map

| File | Changes |
|------|---------|
| `src/core/attributes.py` | **New** — Attributes, AttributeCaps, derived stats, training, level-up gains |
| `src/core/classes.py` | **New** — HeroClass, SkillDef, SkillInstance, ClassDef, BreakthroughDef, registries |
| `src/core/enums.py` | Added ROAD/BRIDGE/RUINS/DUNGEON_ENTRANCE/LAVA tiles, USE_SKILL action, VISIT_CLASS_HALL/VISIT_INN states |
| `src/core/models.py` | Added attributes, attribute_caps, hero_class, skills, class_mastery, stamina/max_stamina to Entity/Stats |
| `src/core/grid.py` | Updated walkability for new tiles, added is_road/is_bridge/is_ruins/is_dungeon_entrance/is_lava helpers |
| `src/core/buildings.py` | Updated docs for class_hall and inn building types |
| `src/config.py` | Added num_ruins, num_dungeon_entrances, road_from_town |
| `src/core/effects.py` | SKILL_BUFF/SKILL_DEBUFF effect types, `skill_effect()` factory, fixed expiry semantics (`-1`=permanent, `0`=expired) |
| `src/core/quests.py` | **New** — Quest, QuestType, QuestTemplate, generate_quest(), QUEST_TEMPLATES |
| `src/actions/combat.py` | Attribute-enhanced damage, stamina cost, attribute training, XP multiplier, HUNT quest progress on kill |
| `src/actions/move.py` | Road speed bonus, stamina cost, attribute training (AGI/END) |
| `src/engine/conflict_resolver.py` | Added USE_SKILL action passthrough |
| `src/engine/world_loop.py` | _tick_stamina_and_skills(), attribute training, level-up gains, USE_SKILL processing (damage+buffs+debuffs), _tick_effects (hp_per_tick), _tick_quests (EXPLORE completion, pruning), GATHER quest progress on loot/harvest |
| `src/systems/generator.py` | Entities spawn with attributes, caps, stamina, race skills |
| `src/api/schemas.py` | AttributeSchema, AttributeCapSchema, SkillSchema, EffectSchema, QuestSchema, extended EntitySchema |
| `src/api/routes/state.py` | Serialization of attributes, skills, class, stamina, active_effects, quests |
| `src/api/engine_manager.py` | Hero spawn with class/attributes/skills, class hall + inn buildings, roads/ruins/dungeons |
| `src/__main__.py` | Mirrored hero spawn with class/attributes/skills for CLI mode |
| `frontend/src/types/api.ts` | EntityAttributes, EntityAttributeCaps, EntitySkill, EntityEffect, EntityQuest interfaces |
| `frontend/src/constants/colors.ts` | Tile colors for new tiles, state colors for new AI states, legend entries |
| `frontend/src/components/InspectPanel.tsx` | Stamina bar, Attributes, Skills, Active Effects, Quests, Equipment sections |
| `tests/test_attributes.py` | **New** — 20 tests for derivation, caps, training, level-up |
| `tests/test_classes.py` | **New** — 37 tests for skills, classes, breakthroughs, mastery, race skills |
| `tests/test_combat.py` | **New** — 30 tests for entity attributes, damage formula, stamina mechanics, skill usage, skill effects |
| `tests/test_quests.py` | **New** — 18 tests for quest model, generation, tracking, completion, entity integration |
