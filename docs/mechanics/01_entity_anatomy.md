---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-08-28
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

### Elder Attribute Modifiers
When an entity's age (`lifecycle.age_ticks`) crosses the elder bracket threshold
(`age_ticks >= 7000`), `LifecycleSystem.resolve_lifecycle()` applies a one-time attribute
modifier via `compute_elder_attribute_update()` (`src/domains/demographics/cohort.py`), gated on
the same forward-transition edge that flips `identity.life_stage` to `ELDER` — the modifier fires
exactly once, on the tick of the transition, never again on subsequent ticks:

```python
# combat_effectiveness *= 0.7
strength_delta  = -int(attrs.strength * 0.3)
agility_delta   = -int(attrs.agility  * 0.3)
# mortality_rate *= 2.0 (increased biological mortality pressure)
vitality_delta  = -int(attrs.vitality  * 0.5)
endurance_delta = -int(attrs.endurance * 0.5)
# knowledge_reputation_weight *= 1.3
wisdom_delta    = int(attrs.wisdom   * 0.3)
charisma_delta  = int(attrs.charisma * 0.3)
```

All deltas are integer-truncated toward zero and applied via a typed `AttributeUpdate` merged
into the entity's `EntityUpdate` — never a direct mutation of the frozen `EntityState`.

### Birth Record (Reproduction Schema)
`LifecycleComponent` carries a per-entity birth record: `parent_a_entity_id`,
`parent_b_entity_id` (`Optional[int]`, both `None` for a parentless natural-creature/magical
spawn), `birth_tick` (`int`, `0` is the "no birth record" sentinel for world-assembled or
pre-existing entities — mirrors `heir_entity_id: Optional[int] = None`'s existing "unset"
convention), `birth_city_id` (`Optional[int]`, a bare identifier with no referential-integrity
validation against the region/building registry), and `reproduction_cooldowns`
(`Dict[int, int]`, partner entity ID → cooldown-expiry tick, merged per-key so two same-tick
writers updating different partners cannot clobber each other's entry).

These fields are populated only at entity-construction time, via
`V2EntityBuilder.birth_record()` — never mutated afterward except `reproduction_cooldowns`,
which reproduction-trigger logic updates through `LifecycleUpdate.reproduction_cooldowns_add`
and the normal `LifecyclePatch.apply` authoritative path (Section 1's frozen-state law applies
here identically to `heir_entity_id`). `birth_record()` also seeds the new entity's own
`SocialBond` toward each parent at `familiarity=0.8`, `sentiment=0.8` (`role` stays at its
`NEUTRAL` default) — the module-level `build_parent_bond_updates_for_birth()` helper produces
the parents' reciprocal `EntityUpdate`s at the same 0.8/0.8 values, for a caller to apply through
the standard `SocialUpdate.bond_updates` path.

Reproduction (idea 32) is explicitly decoupled from Marriage (idea 33): no marriage/contract
precondition gates any part of this schema or its write path.

---

## 6. Trauma: Wounds & Scars
Massive hits cause lasting physical trauma.

### Wound Infliction
A **Wound** is inflicted if a single hit deals damage **strictly greater than 25% of Max HP** (on a surviving defender).
```python
WOUND_INFLICTION_RATIO = 0.25
is_wound = damage > (max_hp * WOUND_INFLICTION_RATIO)  # strict >, only if defender survives
```

### Wound Penalty
A wound's stat penalty is **severity-scaled**, not a flat value. Severity is the proportion of Max HP
dealt by the inflicting hit, capped at 1.0:
```python
severity = min(1.0, damage / max_hp)
atk_penalty = int(severity * 3)
def_penalty = int(severity * 2)
speed_penalty = int(severity * 2)
max_hp_penalty = int(severity * 10)
```
`atk_penalty`, `def_penalty`, and `max_hp_penalty` reduce the entity's effective ATK, DEF, and Max HP
for as long as the wound is active (`SkillScalingService.get_effective_stats()`, `src/engine/rpg_depth.py`).
`speed_penalty` is computed and stored on the wound but is **not yet applied** to any effective
stat — wiring it into `get_effective_stats()` is a tracked follow-up, not part of this formula.

### Permanent Scars
Wounds are permanent under the current implementation — no code path heals a wound.
`WoundState.healed` never transitions `False → True` in production: the only `WoundUpdate`
constructor (`CombatResolutionSystem._get_wound_infliction()`, `src/engine/combat.py:605-617`)
never populates `wounds_heal`, and `WoundUpdate.wounds_heal`/`scars_add` both default to an empty
list (`src/core/updates.py:604-609`). A wound's penalty applies indefinitely unless a future
Scar-formation mechanic — tracked by `TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`, not yet built —
converts it into a **Permanent Scar**, a lesser, persistent penalty:
```python
scar_penalty = wound_penalty * 0.3
```
This formula describes the intended future scar mechanic, not currently active behavior.
