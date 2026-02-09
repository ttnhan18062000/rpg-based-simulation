# RPG Systems — Technical Documentation

This document describes all RPG mechanics implemented in the deterministic concurrent simulation engine, including the attribute system, classes, skills, skill effects, stamina, combat formulas, quests, and world structures.

---

## 1. Primary Attributes

Every entity can have an `Attributes` dataclass (`src/core/attributes.py`) with **9 primary stats**:

| Attribute | Field | Effect |
|-----------|-------|--------|
| **STR** | `str_` | Boosts physical ATK (+2% per point), carry weight |
| **AGI** | `agi` | Boosts SPD (+0.4/pt), crit (+0.4%/pt), evasion (+0.3%/pt) |
| **VIT** | `vit` | Boosts max HP (+2/pt), physical DEF (+0.3/pt) |
| **INT** | `int_` | Boosts XP gain (+1%/pt), MATK (+0.2/pt), cooldown reduction |
| **SPI** | `spi` | Boosts MATK (+0.6/pt), MDEF (+0.15/pt) — primary magic offense |
| **WIS** | `wis` | Boosts MDEF (+0.4/pt), luck (+0.3/pt), XP gain (+0.5%/pt) |
| **END** | `end` | Boosts max stamina (+2/pt), max HP (+0.5/pt), HP regen |
| **PER** | `per` | Boosts vision range (+0.3/pt), loot quality, detection |
| **CHA** | `cha` | Boosts trade prices (+1%/pt), interaction speed, social influence |

### 1.1 Attribute Caps

Each attribute has a cap (`AttributeCaps` dataclass) that limits growth:
- **Default cap**: 15 per attribute
- **Class bonuses**: Each class adds +5–10 to its primary attribute caps
- **Level-up**: All caps increase by +5 per level

### 1.2 Derived Stats

Attributes feed into derived combat and non-combat stats via formulas in `attributes.py`:

**Combat Stats:**

| Derived Stat | Formula |
|-------------|----------|
| Max HP | `base + VIT×2 + END×0.5` |
| ATK | `base + STR×0.5` |
| DEF | `base + VIT×0.3` |
| MATK | `base + SPI×0.6 + INT×0.2` |
| MDEF | `base + WIS×0.4 + SPI×0.15` |
| SPD | `base + AGI×0.4` |
| Crit Rate | `base + AGI×0.004` |
| Evasion | `base + AGI×0.003` |
| Luck | `base + WIS×0.3` |
| Max Stamina | `base + END×2` |
| HP Regen | `1.0 + END×0.15 + VIT×0.05` |
| Cooldown Reduction | `max(0.5, 1.0 - INT×0.005 - WIS×0.003)` |

**Non-Combat Stats:**

| Derived Stat | Formula |
|-------------|----------|
| XP Multiplier | `1.0 + INT×0.01 + WIS×0.005` |
| Vision Range | `base + PER×0.3` |
| Loot Bonus | `1.0 + PER×0.008 + WIS×0.003` |
| Trade Bonus | `1.0 + CHA×0.01` |
| Interaction Speed | `1.0 + CHA×0.005 + INT×0.005` |
| Rest Efficiency | `1.0 + END×0.008 + WIS×0.004` |

### 1.3 Attribute Training

Attributes grow fractionally through actions using `train_attributes()`:

| Action | Trained Attributes |
|--------|-------------------|
| `attack` | STR +0.015, AGI +0.008 |
| `magic_attack` | SPI +0.015, INT +0.008 |
| `move` | AGI +0.008, END +0.005, PER +0.003 |
| `harvest` | END +0.010, WIS +0.005, PER +0.004 |
| `loot` | WIS +0.005, PER +0.006 |
| `skill` | INT +0.010, WIS +0.005, SPI +0.008 |
| `rest` | WIS +0.006, END +0.003 |
| `trade` | CHA +0.012, WIS +0.003 |
| `explore` | PER +0.010, AGI +0.005 |
| `interact` | CHA +0.008, INT +0.004 |
| `defend` | VIT +0.010, END +0.008 |

Fractional accumulation: e.g. 67 attacks → +1 STR. Training never exceeds the cap.
The `_apply_train()` function uses a data-driven `_TRAIN_MAP` for all 9 attributes.

### 1.4 Level-Up Attribute Gains

On each level-up (`level_up_attributes()`):
- All **9** primary attributes: **+2** (capped)
- All **9** attribute caps: **+5**

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

| Class | STR | AGI | VIT | INT | SPI | WIS | END | PER | CHA | Key Caps | Breakthrough |
|-------|-----|-----|-----|-----|-----|-----|-----|-----|-----|----------|-------------|
| **Warrior** | +3 | - | +2 | - | - | - | +1 | - | - | STR+10, VIT+5 | → Champion |
| **Ranger** | - | +3 | - | - | - | +2 | +1 | +1 | - | AGI+10, WIS+5, PER+3 | → Sharpshooter |
| **Mage** | - | - | +1 | +2 | +3 | +2 | - | - | - | SPI+10, INT+5, WIS+5 | → Archmage |
| **Rogue** | +2 | +2 | - | - | - | +1 | - | - | - | AGI+8, STR+5, WIS+3 | → Assassin |

### 3.2 Breakthroughs

When level and attribute thresholds are met, heroes can advance to elite classes:

| From | To | Level Req | Attr Req | Talent |
|------|----|-----------|----------|--------|
| Warrior | Champion | 10 | STR ≥ 30 | Unyielding |
| Ranger | Sharpshooter | 10 | AGI ≥ 30 | Precision |
| Mage | Archmage | 10 | SPI ≥ 30 | Arcane Mastery |
| Rogue | Assassin | 10 | AGI ≥ 25 | Lethal |

Breakthrough check: `can_breakthrough(hero_class, level, attributes)`

---

## 4. Skills

### 4.1 Skill Definitions (`SkillDef`)

Each skill has: `name`, `skill_type` (ACTIVE/PASSIVE), `target`, `power`, `stamina_cost`, `cooldown`, `level_req`, `class_req`, `gold_cost`, `description`, `mastery_req`, `mastery_threshold`.

### 4.2 Skill Learning Requirements

Skills form a **prerequisite chain** within each class. To learn a tier-2 or tier-3 skill, the hero must:
1. Meet the **level requirement** (`level_req`)
2. Have sufficient **gold** (`gold_cost`)
3. **Know** the prerequisite skill (`mastery_req`)
4. Have the prerequisite skill at **mastery ≥ threshold** (`mastery_threshold`, default 25.0)

The `can_learn_skill(sdef, level, known_skills)` function checks all requirements.

### 4.3 Class Skills

| Warrior | Ranger | Mage | Rogue |
|---------|--------|------|-------|
| Power Strike (Lv1) | Quick Shot (Lv1) | Arcane Bolt (Lv1) | Backstab (Lv1) |
| Shield Wall (Lv3, req: Power Strike 25%) | Evasive Step (Lv3, req: Quick Shot 25%) | Frost Shield (Lv3, req: Arcane Bolt 25%) | Shadowstep (Lv3, req: Backstab 25%) |
| Battle Cry (Lv5, req: Shield Wall 25%) | Mark Prey (Lv5, req: Evasive Step 25%) | Mana Surge (Lv5, req: Frost Shield 25%) | Poison Blade (Lv5, req: Shadowstep 25%) |

### 4.4 Race Skills

| Race | Skills |
|------|--------|
| Hero | Rally, Second Wind |
| Wolf | Pack Hunt, Feral Bite |
| Goblin | Ambush, Quickdraw |
| Orc | Berserker Rage, War Cry |
| Undead | Drain Life |

### 4.5 Skill Instances (`SkillInstance`)

Each entity holds `SkillInstance` objects with runtime state:
- `cooldown_remaining` — ticks until ready (ticked down each world tick)
- `mastery` — 0.0 to 100.0, gained by using the skill
- `times_used` — total use count

### 4.6 Mastery Tiers

| Tier | Mastery | Power Bonus | Stamina Reduction | Cooldown Reduction |
|------|---------|-------------|-------------------|--------------------|
| 0 | 0–24% | — | — | — |
| 1 | 25–49% | — | −10% | — |
| 2 | 50–74% | +20% | −10% | — |
| 3 | 75–99% | +20% | −20% | −1 tick |
| 4 | 100% | +35% | −25% | −1 tick |

### 4.7 Skill Modifiers & Effects

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
  - `EntitySkill` extended with `damage_type` and `element` fields
  - `EntityEffect` extended with `crit_mult`, `evasion_mult`, `hp_per_tick` fields
  - `Entity` extended with `base_atk`, `base_def`, `base_spd`, `base_matk`, `base_mdef` for stat breakdown
- **InspectPanel tabs**: stats, class, quests, events, effects, ai
  - **Header stats** — HP/stamina bars, ATK/DEF/MATK/MDEF/SPD/Gold in colored grid
  - **Stats tab**:
    - **Attributes** — 9-stat grid with caps/bars, hover tooltips showing full name, scaling description, and training progress
    - **Detailed Stats** — base + equipment + buff breakdown for ATK/DEF/SPD/MATK/MDEF, plus CRIT/EVA/LUCK
    - **Equipment** — weapon, armor, accessory, inventory bag
  - **Class tab** — class info, skills with damage type (PHY/MAG) and element badges, mastery bars
  - **Quests tab** — title, type badge, progress bar, gold/XP reward display, completion checkmark
  - **Events tab** — timestamped event history with category color-coding
  - **Effects tab** — dedicated buff/debuff display with stat modifier badges (ATK/DEF/SPD/CRIT/EVA), HP per tick, remaining duration
  - **AI tab** — current AI state with description, personality traits with colors/descriptions, utility AI goals explanation, craft target, memory & vision
- **Tile colors**: ROAD (#5a5040), BRIDGE (#4a6050), RUINS (#4a4035), DUNGEON_ENTRANCE (#6a3040), LAVA (#8a3000)
- **State colors**: VISIT_CLASS_HALL (#c084fc), VISIT_INN (#fb923c)
- **Legend**: Added Class Hall, Inn, Road, Ruins, Dungeon entries

---

## 13. File Map

| File | Changes |
|------|---------|
| `src/core/attributes.py` | 9 primary attributes (added SPI, PER, CHA), new derived formulas (MATK, MDEF, vision, loot, trade, etc.), data-driven `_TRAIN_MAP` |
| `src/core/classes.py` | ClassDef/BreakthroughDef expanded for 9 attrs, scaling grades for all 9, Mage primary attr → SPI |
| `src/core/enums.py` | Added DamageType, Element, TraitType enums |
| `src/core/models.py` | Stats: added matk, mdef, elem_vuln, vision_range, loot_bonus, trade_bonus, etc. Entity: added traits list, effective_matk/mdef, elemental_vulnerability, has_trait |
| `src/core/items.py` | ItemTemplate: added matk_bonus, mdef_bonus, damage_type, element. New magic weapons/armor/accessories |
| `src/core/traits.py` | **New** — TraitDef, TRAIT_DEFS registry, incompatibility rules, race biases, assign_traits(), aggregate utilities |
| `src/actions/combat.py` | Dual damage type (PHY/MAG), elemental vulnerability multiplier, weapon-based damage type detection |
| `src/ai/goal_evaluator.py` | **New** — Utility AI goal scoring (9 goals), weighted random selection, trait-influenced utilities |
| `src/ai/brain.py` | Hybrid architecture: goal evaluator for decision states, state machine for execution states |
| `src/ai/states.py` | Updated _item_power for magic stats, breakthrough handler for 9 attribute caps |
| `src/systems/generator.py` | Spawn with 9 attributes + traits for all entity types |
| `src/api/schemas.py` | Extended for spi/per/cha, matk/mdef, traits |
| `src/api/routes/state.py` | Serialization of 9 attrs, matk/mdef, traits |
| `src/api/engine_manager.py` | Hero spawn with 9 attrs + traits |
| `src/__main__.py` | Hero spawn with 9 attrs + traits |
| `src/engine/world_loop.py` | Fixed "cast" → "skill" training action |
| `frontend/src/types/api.ts` | Added spi/per/cha to EntityAttributes, matk/mdef/traits to Entity |
| `frontend/src/components/InspectPanel.tsx` | 6-tab layout (stats/class/quests/events/effects/ai), detailed stats breakdown, attribute tooltips with scaling, element/damage badges on skills, Effects tab, AI state/traits display |

---

## 14. Damage Types & Elements

Defined in `src/core/enums.py`.

### 14.1 Damage Types (Strategy Pattern)

Damage calculation uses the **Strategy pattern** (`src/actions/damage.py`).
Each damage type is a `DamageCalculator` subclass registered in `DAMAGE_CALCULATORS`.

| Type | Calculator Class | Stat Pair | Attribute Scaling |
|------|-----------------|-----------|-------------------|
| **PHYSICAL** | `PhysicalDamageCalculator` | ATK vs DEF | STR boosts attack (+2%/pt), VIT boosts defense (+1%/pt) |
| **MAGICAL** | `MagicalDamageCalculator` | MATK vs MDEF | SPI boosts attack (+2%/pt), WIS boosts defense (+1%/pt) |

The weapon's `damage_type` field selects the calculator via `get_damage_calculator()`. To add a new type (e.g. TRUE damage), create a `DamageCalculator` subclass and register it.

Training action is `attack` for physical, `magic_attack` for magical (resolved by each calculator's `DamageContext`).

### 14.2 Elements

| Element | Value | Notes |
|---------|-------|-------|
| NONE | 0 | Default, no modifier |
| FIRE | 1 | |
| ICE | 2 | |
| LIGHTNING | 3 | |
| DARK | 4 | |
| HOLY | 5 | |

Each entity has an `elem_vuln` table on `Stats` (dict mapping Element → float). Values > 1.0 = weakness, < 1.0 = resistance, 0.0 = immune. Default is 1.0 for all elements.

---

## 15. Trait System

Defined in `src/core/traits.py`. Rimworld-style discrete personality traits.

### 15.1 Trait Assignment

- Each entity gets **2–4 traits** at spawn via `assign_traits()`
- Incompatible pairs enforced (e.g. AGGRESSIVE + CAUTIOUS cannot coexist)
- Race-biased selection: certain races are more likely to get specific traits

### 15.2 Trait Categories

| Category | Traits |
|----------|--------|
| **Combat** | Aggressive, Cautious, Brave, Cowardly, Bloodthirsty |
| **Social** | Greedy, Generous, Charismatic, Loner |
| **Work Ethic** | Diligent, Lazy, Curious |
| **Combat Style** | Berserker, Tactical, Resilient |
| **Magic** | Arcane Gifted, Spirit Touched, Elementalist |
| **Perception** | Keen-Eyed, Oblivious |

### 15.3 Trait Effects (Typed Dataclasses)

Traits modify two things via **typed dataclasses** (no more string-keyed dicts):
1. **`UtilityBonus`** — additive bonuses to goal evaluation (`.combat`, `.flee`, `.explore`, `.loot`, `.trade`, `.rest`, `.craft`, `.social`)
2. **`TraitStatModifiers`** — multiplicative/additive passive stat modifiers (`.atk_mult`, `.def_mult`, `.matk_mult`, `.mdef_mult`, `.crit_bonus`, `.evasion_bonus`, `.vision_bonus`, `.hp_regen_mult`, `.interaction_speed_mult`, `.flee_threshold_mod`)

Aggregation functions:
- `aggregate_trait_utility(traits) -> UtilityBonus`
- `aggregate_trait_stats(traits) -> TraitStatModifiers`

---

## 16. Utility AI Goal Evaluation (Plugin Pattern)

Defined in `src/ai/goals/` package. Integrated into `src/ai/brain.py`.
Legacy shim at `src/ai/goal_evaluator.py` re-exports for backward compatibility.

### 16.1 Architecture (Hybrid)

1. **Decision states** (IDLE, WANDER, RESTING_IN_TOWN, GUARD_CAMP): `GoalEvaluator` iterates all registered `GoalScorer` instances, picks one via weighted random from top 3
2. **Execution states** (HUNT, COMBAT, FLEE, LOOTING, VISIT_*, etc.): State handler runs directly

### 16.2 Plugin System

Each goal is a `GoalScorer` subclass (`src/ai/goals/scorers.py`) with:
- `name` — unique goal identifier
- `target_state` — `AIState` to transition to
- `score(ctx)` — returns float utility score

Scorers are registered in `GOAL_REGISTRY` via `src/ai/goals/registry.py`.
To add a new goal: create a subclass, register it in `register_all_goals()`.

### 16.3 Built-in Goals

| Goal | Scorer Class | Maps to AIState | Key Factors |
|------|-------------|----------------|-------------|
| COMBAT | `CombatGoal` | HUNT | Enemy proximity, power comparison, HP ratio, traits |
| FLEE | `FleeGoal` | FLEE | HP ratio vs flee threshold (trait-modified), enemy presence |
| EXPLORE | `ExploreGoal` | WANDER | HP/stamina health, no enemies, trait curiosity |
| LOOT | `LootGoal` | LOOTING | Ground items nearby, inventory space |
| TRADE | `TradeGoal` | VISIT_SHOP | Sellable items, buying needs |
| REST | `RestGoal` | RESTING_IN_TOWN | Low HP, low stamina |
| CRAFT | `CraftGoal` | VISIT_BLACKSMITH | Recipes, materials available |
| SOCIAL | `SocialGoal` | VISIT_GUILD | Intel needs, class hall needs |
| GUARD | `GuardGoal` | GUARD_CAMP | Non-hero, home territory proximity |

---

## 17. Entity Builder

Defined in `src/core/entity_builder.py`. Fluent builder pattern for entity construction.

### 17.1 Usage

```python
hero = (
    EntityBuilder(rng, eid, tick=0)
    .kind("hero")
    .at(pos)
    .home(town_center)
    .faction(Faction.HERO_GUILD)
    .with_base_stats(hp=50, atk=10, def_=3, spd=10, luck=3)
    .with_randomized_stats()
    .with_hero_class(HeroClass.WARRIOR)
    .with_race_skills("hero")
    .with_class_skills(HeroClass.WARRIOR, level=1)
    .with_inventory(max_slots=20, max_weight=100, weapon="iron_sword")
    .with_starting_items(["small_hp_potion"] * 3)
    .with_traits(race_prefix="hero")
    .build()
)
```

### 17.2 Key Methods

| Method | Purpose |
|--------|---------|
| `kind(str)` | Set entity kind |
| `at(Vector2)` / `home(Vector2)` | Set position / home |
| `faction(Faction)` / `tier(int)` | Set faction / tier |
| `with_base_stats(...)` | Set HP, ATK, DEF, SPD, etc. |
| `with_randomized_stats()` | Add RNG variance to base stats |
| `with_hero_class(HeroClass)` | Set class + derive attributes |
| `with_mob_attributes(base, tier)` | Generate mob-style attributes |
| `with_race_attributes(base, tier, ...)` | Generate race-specific attributes |
| `with_race_skills(race)` / `with_class_skills(cls, lvl)` | Add skills |
| `with_inventory(...)` / `with_existing_inventory(inv)` | Create or attach inventory |
| `with_starting_items(list)` | Add items to inventory |
| `with_home_storage(max_slots)` | Create home storage for hero |
| `with_traits(race_prefix)` | Assign personality traits |
| `build()` | Construct final Entity |

On `build()`, `recalc_derived_stats(stats, attrs)` is called to apply all attribute-derived bonuses to the entity's stats. HP and stamina are set to their derived maximums.

---

## 18. Derived Stats System

Defined in `src/core/attributes.py` via `recalc_derived_stats()`.

### 18.1 Modes

| Mode | When Used | Behavior |
|------|-----------|----------|
| **Creation** (`old_attrs=None`) | `EntityBuilder.build()` | Adds attribute bonuses on top of raw base stats |
| **Delta** (`old_attrs` provided) | Level-up, training | Strips old attribute contributions, then applies new ones |

### 18.2 Call Sites

- **`EntityBuilder.build()`** — creation mode, sets initial derived stats
- **`_check_level_ups()`** — delta mode after `level_up_attributes()`
- **`train_attributes()`** — delta mode when any attribute actually increments

All `train_attributes()` calls pass the entity's `stats` object so derived stats update automatically.

---

## 19. Item Power & Auto-Equip

### 19.1 Item Power Heuristic

`_item_power(template)` in `src/core/items.py` sums all stat bonuses:

```
power = atk + def + spd + max_hp + matk + mdef + crit_rate*50 + evasion*50 + luck
```

### 19.2 Auto-Equip Best

`Inventory.auto_equip_best(item_id)` compares an item's power against the currently equipped item in the same slot:
- **Empty slot** → always equip
- **Occupied** → equip only if new item has higher power
- **Non-equipment items** → ignored

Used during: loot pickup, shop purchases.

---

## 20. Home Storage System

Defined in `src/core/items.py` (`HomeStorage` dataclass). Heroes have persistent storage at their home position.

### 20.1 Storage Tiers

| Level | Max Slots | Upgrade Cost |
|-------|-----------|-------------|
| 0 | 30 | Free (starting) |
| 1 | 50 | 200g |
| 2 | 80 | 500g |

### 20.2 AI Behavior (`VISIT_HOME` state)

Heroes visit home when:
- Inventory is nearly full (≥ max - 2) and storage has space
- They can afford an upgrade

At home, the `VisitHomeHandler` performs:
1. **Upgrade** storage if affordable
2. **Store** low-priority items: materials (not needed for crafting), weaker equipment, excess consumables (keep 2)

### 20.3 Integration

- `EntityBuilder.with_home_storage()` creates storage on hero spawn
- `Entity.home_storage` field, deep-copied in `Entity.copy()`
- `hero_should_visit_home()` scorer in `states.py`
- Exposed via API: `home_storage_used`, `home_storage_max`, `home_storage_level`

---

## 21. Expanded Shop

Defined in `src/core/buildings.py` (`SHOP_INVENTORY`).

### 21.1 Shop Categories

| Category | Items |
|----------|-------|
| **Healing** | Small/Medium/Large HP Potion, Herbal Remedy |
| **Buff Potions** | ATK/DEF/SPD Elixir, Critical Elixir, Antidote |
| **Weapons** | Wooden Club → Bandit Dagger → Iron Sword → Orc Axe → Steel Greatsword |
| **Magic Weapons** | Apprentice Staff, Fire Staff |
| **Armor** | Leather Vest → Chainmail → Orc Shield → Plate Armor |
| **Magic Armor** | Cloth Robe, Silk Robe |
| **Accessories** | Lucky Charm, Speed Ring, Mana Crystal, Spirit Pendant |
| **Materials** | Mana Shard, Silver Ingot, Phoenix Feather |

### 21.2 AI Purchase Priorities

`hero_wants_to_buy()` uses a priority system:
1. **Healing potions** if total < 2 (best tier affordable)
2. **Equipment upgrades** — best power gain across all slots
3. **Buff potions** if none owned
4. **Craft materials** for active craft target

---

## 22. Treasure Chest System

Defined in `src/core/items.py` (`TreasureChest` dataclass). Chests are placed near camps during world generation.

### 22.1 Chest Tiers

| Tier | Loot Quality | Respawn Time | Guard Tier |
|------|-------------|-------------|------------|
| 1 (Common) | Basic potions, ore, leather | 200 ticks | WARRIOR |
| 2 (Rare) | Medium potions, buff elixirs, steel, accessories | 250 ticks | ELITE |
| 3 (Legendary) | Large potions, rare materials, elite gear | 300 ticks | ELITE |

### 22.2 Mechanics

- **Guards**: Each chest has a guard entity (spawned from local terrain race). Guard must be defeated before looting.
- **Looting**: When a hero performs a LOOT action at a chest's position and the guard is dead/absent, loot is generated from `CHEST_LOOT_TABLES` and dropped on the ground.
- **Respawning**: `_tick_treasure_chests()` checks each tick. When `respawn_at` is reached, the chest becomes available again and a new guard is spawned.

### 22.3 Loot Table Format

```python
CHEST_LOOT_TABLES[tier] = [
    (item_id, drop_chance, min_count, max_count),
    ...
]
```

### 22.4 Integration

- Spawned in `engine_manager.py` during world init (near each camp)
- `WorldState.treasure_chests` dict
- `Snapshot.treasure_chests` tuple (immutable copy)
- API: `TreasureChestSchema` with `chest_id`, position, `tier`, `looted`, `guard_entity_id`

---

## 23. Speed & Action Delay System

Defined in `src/core/attributes.py` via `speed_delay()`. Replaces the old linear `1.0/spd` formula with logarithmic diminishing returns and action-type multipliers.

### 23.1 Formula

```
delay = action_mult / (1.0 + ln(max(spd, 1)))
```

Clamped to `[0.15, 2.0]` seconds.

### 23.2 SPD → Delay Table (move action)

| SPD | Delay | Actions/tick |
|-----|-------|-------------|
| 1 | 1.00 | 1.0 |
| 5 | 0.53 | 1.9 |
| 10 | 0.38 | 2.6 |
| 15 | 0.34 | 2.9 |
| 20 | 0.31 | 3.2 |
| 30 | 0.27 | 3.7 |
| 50 | 0.24 | 4.2 |

### 23.3 Action-Type Multipliers

| Action | Multiplier | Effect |
|--------|-----------|--------|
| **Move** | ×1.0 | Baseline |
| **Attack** | ×0.9 | Slightly faster than moving |
| **Skill** | ×1.2 | Slower (powerful abilities have cooldown cost) |
| **Loot** | ×0.7 | Fast pickup |
| **Harvest** | ×0.7 | Fast gathering |
| **Use Item** | ×0.6 | Fastest (potions should be quick) |
| **Rest** | ×1.0 | Same as baseline |

For non-combat actions (loot, harvest, use_item, rest), the `interaction_speed` derived stat further scales the delay.

### 23.4 Engagement Lock (Anti-Kite)

Tracked via `Entity.engaged_ticks`, incremented each tick an entity is adjacent (Manhattan ≤ 1) to a hostile. Reset to 0 when no hostiles are adjacent.

**Mechanic**: When `engaged_ticks >= 2`, moving away costs **double** the normal delay. This prevents fast entities from trivially escaping melee combat, similar to D&D opportunity attacks.

- Slow tanky builds can pin down fast enemies
- Fast builds still act more often overall, but can't kite indefinitely
- The penalty is paid once per disengage, then `engaged_ticks` resets
