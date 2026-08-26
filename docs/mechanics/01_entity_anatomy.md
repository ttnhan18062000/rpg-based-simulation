---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-08-26
---

# Chapter 1: Entity Anatomy

This chapter defines the biological, physical, and developmental laws that govern every actor within the simulation. 

---

## 1. Core Attributes
Every entity possesses nine core attributes that scale from **1 to 99**. These attributes are the foundation for all derived combat and survival stats.

| Attribute | Impact |
| :--- | :--- |
| **Strength (STR)** | Physical damage and carrying capacity. |
| **Agility (AGI)** | Evasion, movement speed, and attack speed (readiness). |
| **Vitality (VIT)** | Maximum Health (HP) and Physical Defense. |
| **Endurance (END)** | Maximum Stamina and HP scaling. |
| **Intelligence (INT)** | Magical damage and mana/skill efficiency. |
| **Spirit (SPI)** | Elemental resistance and magical recovery. |
| **Wisdom (WIS)** | Healing quality and tactical decision-making. |
| **Perception (PER)** | Critical hit chance and world discovery. |
| **Charisma (CHA)** | Social influence and trade prices. |

---

## 2. Derived Combat Stats
Combat stats are recalculated whenever attributes or equipment change.

### Primary Formulas
```python
# Health & Stamina
Max_HP = base_hp + (vitality * 2) + int(endurance * 0.5) + gear_hp
Max_Stamina = 50.0 + (endurance * 5.0)

# Offense & Defense
Attack = base_atk + int(strength * 0.5) + gear_atk
Defense = base_def + int(vitality * 0.3) + gear_def
Evasion = base_evasion + (agility * 0.001) + gear_evasion

# Movement
Move_Cost = max(5.0, 10.0 + (total_weight / 5.0) - (agility * 0.1))
```

### Tactical Role Selection
An entity's `TacticalRole` is derived from its highest attribute. To prevent "flickering" between roles, a **5-point hysteresis** is applied.
*   **VANGUARD**: Derived from **Strength**.
*   **SKIRMISHER**: Derived from **Agility**.
*   **PROTECTOR**: Derived from **Vitality**.

---

## 3. Class Registry
Base stats for the standard entity classes.

| Class | ID | Base HP | Base ATK | Base DEF | Starting Gear |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Novice** | `NOVICE` | 100 | 10 | 5 | None |
| **Warrior** | `WARRIOR` | 150 | 15 | 10 | Iron Sword, Leather Armor |
| **Mage** | `MAGE` | 80 | 20 | 2 | Wooden Staff |
| **Rogue** | `ROGUE` | 100 | 12 | 5 | Iron Dagger |

---

## 4. Biological Laws (Decay & Needs)
The simulation tracks biological "Pressures" that degrade over time.

### Passive Decay Rates
| Need | Decay (per tick) | Max Value | Penalty Threshold |
| :--- | :--- | :--- | :--- |
| **Hunger** | `+0.1` | 100.0 | **95.0**: Starvation (+2 HP damage/tick) |
| **Sleep Debt** | `+0.05` | 100.0 | **98.0**: Fatigue (+1 HP damage/tick) |
| **Stamina** | `-1.0` (per move) | `Max_Stamina` | **< Exhaustion Threshold**: Exhausted state |

### Stamina Service
*   **Attack Cost**: `stamina.ATTACK_COST` (Base: 5.0)
*   **Harvest Cost**: `stamina.HARVEST_COST` (Base: 2.0)
*   **Regeneration**: `min(rate, headroom)` (Resting: 2.0x faster)

---

## 5. Progression & Growth
Entities grow by accumulating Experience Points (XP).

### Experience (XP) Curve
The XP required to reach the **next** level scales exponentially.
```python
XP_Required = int(100 * (level ** 1.5))
```

### Level Up Rewards
*   **Attribute Points (AP)**: +5 AP per level.
*   **Level Cap**: 99.
*   **Skill Unlocks**:
    *   Level 2: `power_strike`
    *   Level 5: `swift_reflexes`
    *   Level 10: `fireball`

### Breakthroughs (Passive Perks)
Breakthroughs are milestone-earned passive perks, keyed by breakthrough ID rather than
level, registered in `BreakthroughService.REGISTRY` (`src/progression/breakthroughs.py`):

*   **`iron_will`**: `spirit +2`, `wisdom +2`.
*   **`fleet_foot`**: `agility +3`, plus a separate non-attribute `evasion_flat: 0.05` bonus.
    The `evasion_flat` bonus targets the derived evasion stat directly rather than a base
    attribute, and is not yet wired into the effective-stats path described below.
*   **`titan_grip`**: `strength +4`.

**Application rule**: an entity's active breakthrough IDs' `attribute_bonuses` are summed and
applied to its base `AttributeComponent` — via `BreakthroughService.apply_bonuses` — before
combat-stat derivation (Section 2's formulas). Bonus-adjusted attributes then flow into
`LevelingService.recalculate_combat_stats` the same way base attributes do; the formulas in
Section 2 are unchanged, only the attribute values feeding them are pre-adjusted.

---

## 6. Trauma: Wounds & Scars
Massive hits cause lasting physical trauma.

### Wound Infliction
A **Wound** is inflicted if a single hit deals damage **strictly greater than 25% of Max HP** (on a surviving defender).
```python
WOUND_THRESHOLD_RATIO = 0.25
is_wound = damage > (max_hp * WOUND_THRESHOLD_RATIO)  # strict >, only if defender survives
```

### Permanent Scars
When a wound is healed, it has a chance to leave a **Permanent Scar**, which carries **30%** of the original wound's stat penalties indefinitely.
```python
scar_penalty = wound_penalty * 0.3
```
