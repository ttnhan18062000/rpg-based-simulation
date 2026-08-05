---
name: progression-entities
description: Work in src/entities/ and src/progression/ — core attributes, derived combat stats, biological pressures, XP curve, level-up execution, and attribute-point allocation. Use when editing entity stats/leveling logic or debugging why a derived stat came out wrong.
source: project
date_added: "2026-08-05"
---

# Progression & Entities (This Repo)

Sourced from `docs/mechanics/01_entity_anatomy.md` (Mechanics Bible ch.1, P0 authoritative) and
`docs/mechanics/attribute_progression_contract.md`.

## Core Attributes & Derived Stats

Source: ch.1 §1-2. 9 core attributes, scale 1-99: **STR** (physical damage, carry capacity),
**AGI** (evasion, movement speed, attack speed/readiness), **VIT** (max HP, physical defense),
**END** (max stamina, HP scaling), **INT** (magical damage, mana/skill efficiency), **SPI**
(elemental resistance, magical recovery), **WIS** (healing quality, tactical decisions), **PER**
(critical hit chance, world discovery), **CHA** (social influence, trade prices).

Derived formulas (exact):
```python
Max_HP     = base_hp + (vitality * 2) + int(endurance * 0.5) + gear_hp
Max_Stamina = 50.0 + (endurance * 5.0)
Attack     = base_atk + int(strength * 0.5) + gear_atk
Defense    = base_def + int(vitality * 0.3) + gear_def
Evasion    = base_evasion + (agility * 0.001) + gear_evasion
Move_Cost  = max(5.0, 10.0 + (total_weight / 5.0) - (agility * 0.1))
```

## `TacticalRole` Hysteresis

Derived from the entity's highest attribute: **VANGUARD** (Strength), **SKIRMISHER** (Agility),
**PROTECTOR** (Vitality). A **5-point hysteresis** prevents role flickering — only switches if the
new role's score exceeds the current role's score by more than 5 (confirmed identical rule in both
source docs — see the recalculation-order section below for the exact code).

## Class Registry & Biological Decay

Source: §3-4. Real base stats: Novice (100 HP/10 ATK/5 DEF, no gear), Warrior (150/15/10, Iron
Sword + Leather Armor), Mage (80/20/2, Wooden Staff), Rogue (100/12/5, Iron Dagger).

Passive decay: Hunger `+0.1`/tick (95.0 threshold → Starvation, +2 HP dmg/tick), Sleep Debt
`+0.05`/tick (98.0 threshold → Fatigue, +1 HP dmg/tick), Stamina `-1.0`/move. Attack costs 5.0
stamina, harvest costs 2.0; regen `min(rate, headroom)`, 2x faster while resting.

## XP Curve, Level-Up, AP Allocation

Source: ch.1 §5 + `attribute_progression_contract.md`.

**Curve**: `XP_Required = int(100 * (level ** 1.5))`. Real threshold table (exact values):

| Level → Next | XP Required |
|---|---|
| 1 → 2 | 100 |
| 2 → 3 | 283 |
| 3 → 4 | 520 |
| 5 → 6 | 1,118 |
| 10 → 11 | 3,162 |
| 20 → 21 | 8,944 |
| 50 → 51 | 35,355 |
| 98 → 99 | ~969,440 |

Level cap: **99**. +5 AP per level. Skill unlocks: level 2 → `power_strike`, level 5 →
`swift_reflexes`, level 10 → `fireball`.

**`_execute_level_up`** (exact 5-step algorithm):
```
1. new_level = identity.evolution_level + 1
2. rem_xp = total_xp - int(100 * (current_level ** 1.5))  # carry excess XP
3. ap_gain = 5
4. unlocked = [] (append per the level-2/5/10 skill thresholds above)
5. return IdentityUpdate(evolution_level_set=new_level,
                         evolution_points_delta=rem_xp - identity.evolution_points,
                         unspent_ap_delta=5, learned_skills=unlocked)
```

**AP allocation** — 4 real gates checked in the apply path:
- `PROG-067`: entity has sufficient unspent AP
- `PROG-068`: attribute name is valid
- `PROG-069`: aptitude multiplier applied (class/race may modify AP efficiency)
- `PROG-070`: attribute value cap of 99 enforced

## `LevelingService.recalculate_combat_stats()` — Exact 6-Step Order

This order is **strict** — getting a step out of order silently produces wrong derived stats:

1. **Base Attributes**: `max_hp`, `atk`, `def_stat`, `evasion` from raw attributes (same formulas
   as above), `atk_range = 1` default.
2. **Equipment Bonuses** (non-broken slots only, `durability > 0`): adds `atk_bonus`/`def_bonus`/
   `hp_bonus`/`evasion_bonus` from equipped items; `MAIN_HAND`'s `range` overrides the default
   `atk_range`; accumulates `total_weight`.
3. **Passive Skill Bonuses** (`SkillKind.PASSIVE` only): e.g. `swift_reflexes` adds to `evasion`.
4. **Trait Bonuses**: `"Tough"` → `+20 max_hp`, `"Quick"` → `+0.02 evasion`, `"Strong"` → `+3 atk`.
5. **Movement Cost**: `move_cost = max(5.0, 10.0 + (total_weight/5.0) - (agility*0.1))` — uses the
   `total_weight` accumulated in step 2.
6. **Tactical Role Derivation** (with hysteresis): `scores = {VANGUARD: strength, SKIRMISHER:
   agility, PROTECTOR: vitality}`; switch only if `scores[new_role] > scores[current_role] + 5`.

## The Authoritative Pipeline Phases

Source: `docs/engine/authoritative_pipeline.md`. Phase 23 `evolution` ("Applies entity evolution
and stat boosts") and phase 24 `progression_conversion` ("Enhanced RPG: converts progression
points to levels/skills") — adjacent in the pipeline, `evolution` runs first.

## Debugging — Real Test Paths

`tests/unit/progression/test_leveling.py`, `test_attribute_growth.py`, `test_evolution.py`,
`test_classes_loadouts.py`, `test_progression_v2.py`.
