---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-06-06
---

# Chapter 2: Combat Laws

This chapter details the mathematical and logical sequence of combat resolution. The simulation follows a deterministic, non-random resolution for all primary attacks.

---

## 1. The Damage Formula
The simulation uses a **Fractional Armor Mitigation** model. This ensures that every point of Attack matters, and Defense provides diminishing returns rather than a flat reduction.

```python
# Raw Core Formula
Damage = Atk * (Atk / (Atk + Def * 2.0 + 1.0))
```

*   **Minimum Damage**: Every successful hit deals at least **1 damage**, regardless of Defense.
*   **Rounding**: Damage is always cast to an integer (`int`) after calculations.

---

## 2. Tactical Modifiers
Before damage is calculated, the base `Atk` and `Def` values are modified by the tactical context.

| Modifier | Impact | Condition |
| :--- | :--- | :--- |
| **High Ground** | `+0.20` Atk | Attacker is at a higher elevation than the target. |
| **Flanking** | `+0.15` Atk | Attacker is behind the target's current focus. |
| **Surrounded** | `+0.25` Atk | Target is surrounded by multiple enemies. |
| **Cover** | `+0.30` Def | Target is behind environmental cover relative to the attacker. |
| **Shatter** | `x1.50` Atk | Target is currently in the `Frozen` state. |
| **Exhaustion** | `x0.80` Atk | Attacker's `Sleep Debt` is greater than 80. |
| **Bond Synergy** | `+0.10` Atk | Adjacent ally has >0.5 Familiarity with the attacker. |

---

## 3. Durability & Decay
Equipment degrades with every combat engagement. Broken equipment (0 durability) provides **zero** stat bonuses.

*   **Attacker**: `-1.0` durability to the `MAIN_HAND` item.
*   **Defender**: `-0.5` durability to `HEAD`, `TORSO`, and `LEGS` items.

---

## 4. Victory & Rewards
When an entity's HP reaches 0, the resolution system determines the final outcome based on the target's role and lifecycle.

### Kill Rewards
Rewards are granted to the attacker (or their group) based on the target's level (`LVL`).

| Target Role | XP Reward | Gold Reward |
| :--- | :--- | :--- |
| **Monster** | `LVL * 10` | `LVL * 5` |
| **Hero** | `LVL * 20` | `LVL * 50` |

### The Hero's Journey (Generations)
Heroes are uniquely resilient compared to monsters or NPCs.
1.  **Defeat**: HP reaches 0.
2.  **Rebirth**: If the Hero is in Generation 1-3, they are reborn (Generation increments).
3.  **Permadeath**: If the Hero is in Generation 4, they are permanently removed from the simulation.

---

## 5. Wound Infliction
A **Wound** is inflicted on a surviving defender when a single hit deals damage **strictly greater than 25% of the defender's Max HP**.
```python
is_wound = damage > (defender.max_hp * 0.25) and defender.alive
```
- Wound type: `SLASH` for Hero attackers, `CRUSH` otherwise.
- Wound severity: `damage / defender.max_hp` (proportional).
- Wound penalty: −5 ATK, −5 DEF (applied as long as wound is active).
- Permanent Scars: when a wound heals, it has a 30% chance to leave a scar (`scar_penalty = wound_penalty * 0.3`).

---

## 6. Area of Effect (AoE) Logic
For skills with a `splash_radius`:
1.  **Primary Target**: Receives 100% of the calculated skill damage.
2.  **Splash Victims**: All other entities in the radius receive **50%** of the attacker's base ATK as damage.
3.  **Line of Sight**: Splash damage is blocked by solid walls/terrain.
4.  **Friendly Fire**: Faction allies do not take splash damage from their teammates.
