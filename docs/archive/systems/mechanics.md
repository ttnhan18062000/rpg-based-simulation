---
status: archive
authority: P2
audience: historical
layer: systems
original_date: unknown
---

> [!WARNING]
> **ARCHIVED 2026-08-10 — `TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT`.** The
> "Action Economy" section's `next_act_at`/`spd` delay formula (`Delay = 1.0 / max(0.1, spd/10.0)`)
> has zero real references anywhere in `src/` (confirmed via `grep`). The real system uses
> `combat.readiness`/`readiness_speed` — see `docs/engine/contracts/minimal_kernel.md` §5. Other
> sections of this doc were not individually re-verified; treat the whole file as unreliable and
> consult the Mechanics Bible (`docs/mechanics/`) instead. Kept for historical reference only.

# Gameplay Mechanics: Formulas & Progression

The simulation follows a deterministic RPG logic where stats, skills, and environment interact through a strictly defined mathematical pipeline.

---

## 1. The Action Economy

Simulation time is measured in **Ticks**. An entity's ability to act is governed by its `spd` (Speed) attribute.

### Action Delay Formula
After taking an action, an entity's `next_act_at` is incremented by:
$$Delay = \frac{1.0}{\max(0.1, \frac{spd}{10.0})}$$

- **10 Speed**: 1 action per tick.
- **5 Speed**: 1 action every 2 ticks.
- **20 Speed**: 2 actions per tick (theoretically, though the scheduler typically processes once per loop).

---

## 2. Combat Pipeline

Combat is resolved in 5 internal sub-phases during a single tick's **Resolution** phase.

### Phase A: Evasion & Luck
Before damage is calculated, the defender may evade based on their `evasion` stat and the attacker's `luck`.
$$EffectiveEvasion = \max(0.0, Evasion - (Luck \times 0.002))$$

### Phase B: Attack Power vs. Mitigation
The engine uses **Fractional Armor Mitigation** rather than a flat subtraction to prevent "Invincibility Walls."
- **Physical**: Uses `atk` vs. `def`.
- **Magical**: Uses `matk` vs. `mdef`.

$$RawDamage = \left\lfloor Atk \times \frac{Atk}{Atk + (Def \times 2) + 1} \right\rfloor$$

### Phase C: Variance & Elementals
- **Variance**: A $\pm 5\%$ random swing is applied (Deterministic via seed).
- **Elementals**: Multipliers (0.5x to 2.0x) are applied based on the defender's `elem_vuln` table.

### Phase D: Critical Hits
$$CritRate = BaseCrit + (Luck \times 0.003)$$
If a critical hit occurs, damage is multiplied by the attacker's `crit_dmg` (default 1.5x).

### Phase E: Shatter Status
Targets with the `FROZEN` status effect take **1.5x** total damage from any incoming hit, which simultaneously consumes the frozen effect.

---

## 3. Progression & Leveling

### XP Rewards
- **Base Kill**: 5 XP (if victim level $\leq$ killer level) or 10 XP (if higher).
- **Multiplier**: Total XP is multiplied by the entity's `ProgressionAspect.xp_mult`:
  $$XP_{mult} = 1.0 + (Wisdom \times 0.01) + (Intelligence \times 0.005)$$

### Level Thresholds
The XP required for the next level scales in brackets:
- **Lv 1-10**: 1.4x scaling.
- **Lv 11-20**: 1.6x scaling.
- **Lv 21+**: 2.0x scaling.

### Milestone Stat Growth
| Level Range | HP Gain | ATK/DEF/SPD |
| :--- | :--- | :--- |
| **1 - 10** | +5 | +1 |
| **11 - 20** | +3 | +1 |
| **21+** | +2 | +0 |

---

## 4. Attributes & Training

Entities possess 9 primary attributes that drive all derived combat stats.

| Attribute | Primary Derived Stats | Training Trigger |
| :--- | :--- | :--- |
| **STR** (Strength) | Attack, HP, Max Weight | ATTACK actions. |
| **AGI** (Agility) | Speed, Evasion, Crit | MOVE actions. |
| **VIT** (Vitality) | HP, HP Regen, Defense | Taking Damage. |
| **INT** (Intelligence) | Magic Attack, Max Mana | USE_SKILL actions. |
| **SPI** (Spirit) | Magic Defense, Mana Regen | Resting in Sanctuary. |
| **WIS** (Wisdom) | XP Multiplier, Skill Cooldown | Reading/Learning. |
| **END** (Endurance) | Stamina, Resistance | Long-distance travel. |
| **PER** (Perception) | Vision Range, Accuracy | Finding Hidden nodes. |
| **CHA** (Charisma) | Shop Prices, Fame | Social/Trade actions. |

---

## 5. Resource Regeneration

Stamina and HP regenerate every tick, flavored by the current `AIState`.

| State | Regen Multiplier | Logic |
| :--- | :--- | :--- |
| **EXHAUSTED** | 3 (Fixed) | Forced recovery state. |
| **RESTING** | 5 | Fastest steady recovery. |
| **TOWN_VISIT** | 4 | Comfortable recovery. |
| **ACTIVE** | 1 | Natural baseline. |
