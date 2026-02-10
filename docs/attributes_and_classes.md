# Attributes & Classes

Technical documentation for the 9 primary attributes, derived stats, stamina, hero classes, breakthroughs, skills, and mastery.

---

## Overview

Every entity can have an `Attributes` dataclass with **9 primary stats** that feed into derived combat and non-combat stats. Heroes are assigned a **class** at spawn that provides attribute bonuses, scaling grades, learnable skills, and a breakthrough path to an elite class.

**Primary files:** `src/core/attributes.py`, `src/core/classes.py`, `src/core/models.py`

---

## 1. Primary Attributes

| Attribute | Field | Effect |
|-----------|-------|--------|
| **STR** | `str_` | Physical ATK (+2%/pt), carry weight |
| **AGI** | `agi` | SPD (+0.4/pt), crit (+0.4%/pt), evasion (+0.3%/pt) |
| **VIT** | `vit` | Max HP (+2/pt), physical DEF (+0.3/pt) |
| **INT** | `int_` | XP gain (+1%/pt), MATK (+0.2/pt), cooldown reduction |
| **SPI** | `spi` | MATK (+0.6/pt), MDEF (+0.15/pt) — primary magic offense |
| **WIS** | `wis` | MDEF (+0.4/pt), luck (+0.3/pt), XP gain (+0.5%/pt) |
| **END** | `end` | Max stamina (+2/pt), max HP (+0.5/pt), HP regen |
| **PER** | `per` | Vision range (+0.3/pt), loot quality, detection |
| **CHA** | `cha` | Trade prices (+1%/pt), interaction speed, social influence |

### Attribute Caps

Each attribute has a cap (`AttributeCaps` dataclass):
- **Default cap:** 15 per attribute
- **Class bonuses:** Each class adds +5–10 to primary attribute caps
- **Level-up:** All caps increase by +5 per level

---

## 2. Derived Stats

Attributes feed into derived stats via formulas in `attributes.py`:

### Combat Stats

| Derived Stat | Formula |
|-------------|---------|
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

### Non-Combat Stats

| Derived Stat | Formula |
|-------------|---------|
| XP Multiplier | `1.0 + INT×0.01 + WIS×0.005` |
| Vision Range | `base + PER×0.3` |
| Loot Bonus | `1.0 + PER×0.008 + WIS×0.003` |
| Trade Bonus | `1.0 + CHA×0.01` |
| Interaction Speed | `1.0 + CHA×0.005 + INT×0.005` |
| Rest Efficiency | `1.0 + END×0.008 + WIS×0.004` |

### Derived Stats Recalculation

`recalc_derived_stats(stats, attrs)` in `attributes.py`:

| Mode | When Used | Behavior |
|------|-----------|----------|
| **Creation** (`old_attrs=None`) | `EntityBuilder.build()` | Adds attribute bonuses on top of raw base stats |
| **Delta** (`old_attrs` provided) | Level-up, training | Strips old contributions, applies new ones |

---

## 3. Attribute Training

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

Fractional accumulation (e.g. 67 attacks → +1 STR). Training never exceeds the cap. Uses a data-driven `_TRAIN_MAP`.

### Level-Up Attribute Gains

On each level-up (`level_up_attributes()`):
- All **9** primary attributes: **+2** (capped)
- All **9** attribute caps: **+5**

---

## 4. Stamina System

Every entity has `stamina` and `max_stamina` fields on `Stats`.

### Stamina Costs

| Action | Cost |
|--------|------|
| Attack | 3 |
| Move | 1 |
| Harvest | 2 |

### Stamina Regeneration (per tick)

| State | Regen |
|-------|-------|
| RESTING_IN_TOWN, IDLE | 5 |
| VISIT_SHOP, VISIT_BLACKSMITH, VISIT_GUILD, VISIT_CLASS_HALL, VISIT_INN | 4 |
| All other states | 1 |

Capped at `max_stamina`.

---

## 5. Hero Classes

### Scaling Grades

| Grade | Mult | Description |
|-------|------|-------------|
| E | 60% | Minimal benefit |
| D | 75% | Below average |
| C | 90% | Average |
| B | 100% | Baseline |
| A | 115% | Strong |
| S | 130% | Excellent — primary stat |
| SS | 150% | Outstanding — breakthrough |
| SSS | 180% | Legendary — reserved |

### Base Classes (Tier 1)

| Class | Primary Scaling | Bonuses | Cap Bonuses | Breakthrough |
|-------|----------------|---------|-------------|-------------|
| **Warrior** | STR=S, VIT=A | STR+3, VIT+2, END+1 | STR+10, VIT+5 | → Champion (Lv10, STR≥30) |
| **Ranger** | AGI=S, END=A | AGI+3, WIS+2, END+1 | AGI+10, WIS+5, PER+3 | → Sharpshooter (Lv10, AGI≥30) |
| **Mage** | SPI=S, WIS=A | INT+2, SPI+3, WIS+2 | SPI+10, INT+5, WIS+5 | → Archmage (Lv10, SPI≥30) |
| **Rogue** | AGI=S, STR=B | STR+2, AGI+2, WIS+1 | AGI+8, STR+5, WIS+3 | → Assassin (Lv10, AGI≥25) |

### Breakthrough Classes (Tier 2)

| Class | From | Talent |
|-------|------|--------|
| **Champion** | Warrior | Unyielding — Below 25% HP → +30% DEF, +20% ATK for 5 ticks |
| **Sharpshooter** | Ranger | Precision — Crits deal +25% damage; Quick Shot range +1 |
| **Archmage** | Mage | Arcane Mastery — Skill durations +1 tick; cooldowns −1 tick |
| **Assassin** | Rogue | Lethal — Guaranteed crit vs targets below 30% HP; Backstab → 2.8× |

### Progression Tiers

```
Warrior  → Champion      → [Transcendence] (future)
Ranger   → Sharpshooter  → [Transcendence]
Mage     → Archmage      → [Transcendence]
Rogue    → Assassin      → [Transcendence]
```

---

## 6. Skills

### Skill Definitions (`SkillDef`)

Each skill has: `name`, `skill_type` (ACTIVE/PASSIVE), `target`, `power`, `stamina_cost`, `cooldown`, `level_req`, `class_req`, `gold_cost`, `description`, `mastery_req`, `mastery_threshold`.

### Learning Prerequisites

Skills form a prerequisite chain. To learn tier-2 or tier-3 skills:
1. Meet level requirement (`level_req`)
2. Have sufficient gold (`gold_cost`)
3. Know the prerequisite skill (`mastery_req`)
4. Have prerequisite at mastery ≥ threshold (default 25.0)

### Class Skills

| Warrior | Ranger | Mage | Rogue |
|---------|--------|------|-------|
| Power Strike (Lv1, 1.8×, CD4) | Quick Shot (Lv1, 1.5×, CD3, range 3) | Arcane Bolt (Lv1, 2.0×, CD4, range 4) | Backstab (Lv1, 2.2×, CD4, CRIT+15%) |
| Shield Wall (Lv3, DEF+50% 3t, CD8) | Evasive Step (Lv3, EVA+30% 3t, CD7) | Frost Shield (Lv3, DEF+40% 3t, CD8) | Shadowstep (Lv3, EVA+40% SPD+30% 2t, CD7) |
| Battle Cry (Lv5, AoE ATK+20% 3t, CD12) | Mark Prey (Lv5, DEF-25% 4t, CD10) | Mana Surge (Lv5, ATK+30% 4t, CD12) | Poison Blade (Lv5, DoT 4t, CD10) |

### Race Skills (Innate, Free)

| Race | Skills |
|------|--------|
| Hero | Rally (AoE ATK+10% DEF+10% 3t), Second Wind (Heal 20% max HP, CD20) |
| Wolf | Pack Hunt, Feral Bite |
| Goblin | Ambush, Quickdraw |
| Orc | Berserker Rage, War Cry |
| Undead | Drain Life |

### Skill Instances (`SkillInstance`)

Runtime state per entity:
- `cooldown_remaining` — ticks until ready
- `mastery` — 0.0 to 100.0, gained by using the skill
- `times_used` — total use count

### Mastery Tiers

| Tier | Mastery | Power Bonus | Stamina Reduction | Cooldown Reduction |
|------|---------|-------------|-------------------|--------------------|
| Novice | 0–24% | — | — | — |
| Apprentice | 25–49% | — | −10% | — |
| Adept | 50–74% | +20% | −10% | — |
| Expert | 75–99% | +20% | −20% | −1 tick |
| Master | 100% | +35% | −25% | −1 tick |

### Skill Modifiers & Effects

Skills can define stat modifiers that create temporary `StatusEffect`s:

| Modifier | Description |
|----------|-------------|
| `atk_mod` | % change to ATK (e.g. +0.2 = +20%) |
| `def_mod` | % change to DEF |
| `spd_mod` | % change to SPD |
| `crit_mod` | % change to crit rate |
| `evasion_mod` | % change to evasion |
| `hp_mod` | Instant heal as % of max HP (SELF skills) |
| `duration` | Ticks the buff/debuff lasts |

- **SELF / AREA_ALLIES** → `SKILL_BUFF` effect on caster/allies
- **SINGLE_ENEMY / AREA_ENEMIES** → `SKILL_DEBUFF` effect on enemies

Modifiers convert to multipliers: `atk_mod=0.2` → `atk_mult=1.2`. Multiple effects stack multiplicatively.

---

## 7. Enhanced Stats (`Stats` dataclass)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `hp` / `max_hp` | int | 20 | Health |
| `atk` | int | 5 | Base physical attack |
| `def_` | int | 0 | Base physical defense |
| `spd` | int | 10 | Speed |
| `luck` | int | 0 | Crit/evasion modifier |
| `crit_rate` / `crit_dmg` | float | 0.05 / 1.5 | Critical hit stats |
| `evasion` | float | 0.0 | Dodge chance |
| `matk` | int | 0 | Base magical attack |
| `mdef` | int | 0 | Base magical defense |
| `level` / `xp` / `xp_to_next` | int | 1/0/100 | Leveling |
| `gold` | int | 0 | Currency |
| `stamina` / `max_stamina` | int | 50 | Action resource |
| `vision_range` | int | 6 | Perception radius |
| `elem_vuln` | dict | {} | Element → vulnerability multiplier |
