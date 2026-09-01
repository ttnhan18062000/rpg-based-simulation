---
status: authoritative
layer: mechanics
authority: P1
audience: agent
last_verified: 2026-06-13
tags: [damage-formula, combat, tactical-modifiers, durability, wound-infliction]
related_chapter: 02_combat_laws.md
---

# Damage Formula Contract

Companion sub-contract to `02_combat_laws.md`. That chapter names the combat laws and modifier categories; this doc gives the exact multi-step formula, precise modifier application order, wound infliction threshold, durability decay values, and AoE rules needed to safely implement or modify combat resolution.

> **Parity note:** Chapter 02 (`02_combat_laws.md`) states the wound infliction threshold as 40% of max HP. The authoritative source code (`src/engine/combat.py`, `_get_wound_infliction()`) uses **25%**. The source is authoritative per CLAUDE.md. This divergence is recorded in `docs/parity_ledger/combat_movement.yaml` as entry COMB-290 with `status: divergent`. Chapter 02 requires correction in a separate parity-repair ticket.

---

## Purpose

Define the complete damage resolution law: from raw attack/defense stats, through the fractional armor mitigation formula, through tactical modifiers, to wound infliction, durability decay, and kill rewards.

---

## RPG Meaning

Combat damage is not random — it is a deterministic function of attacker stats, defender stats, and environmental tactical factors. A stronger defender meaningfully reduces incoming damage (non-linearly), but can never completely negate it (minimum 1 damage). Wounds, durability loss, and kills all follow from this same resolved damage value.

---

## Inputs

| Field | Type | Description |
|---|---|---|
| `attacker` | `Entity` | Attacker snapshot with `combat.atk`, `combat.atk_mult`, `identity.properties`, `biological.sleep_debt`, `stamina` |
| `defender` | `Entity` | Defender snapshot with `combat.def_stat`, `combat.max_hp`, `combat.hp`, `identity.properties` |
| `world_state` | `WorldState` | Grid for terrain/elevation checks, ally positions for flanking/bond |

---

## Core Rules

1. **Minimum damage:** resolved damage is always at least 1. The formula can never produce 0.
2. **Integer truncation:** `int()` truncation applies before the minimum clamp.
3. **Additive modifiers apply before multiplicative ones** in the execution order (within `_get_tactical_multipliers`).
4. **Multiplicative modifiers can compound:** Shatter, Sleep Exhaustion, and Stamina Exhaustion multiply together.
5. **Wound requires survival:** wounds are only inflicted if `alive=True` after the hit (defender HP > 0).
6. **Wound threshold is 25%:** `damage > defender.combat.max_hp * 0.25` (source-authoritative).

---

## Formula / Decision Logic

### Step 1 — Tactical Modifier Collection

`_get_tactical_multipliers(attacker, defender, world_state)` returns `(atk_mult, def_mult)`. Starts at `atk_mult = 1.0`, `def_mult = 1.0`.

**Additive modifiers (applied first, in this order):**

| Modifier | Type | Delta | Condition |
|---|---|---|---|
| High Ground | additive ATK | `+0.20` | Attacker elevation > defender elevation |
| Flanking | additive ATK | `+0.15` | Defender's focus direction not toward attacker |
| Surrounded | additive ATK | `+0.25` | Multiple enemies adjacent to defender |
| Cover | additive DEF | `+0.30` | Defender adjacent to cover relative to attacker direction |
| Bond Synergy | additive ATK | `+0.10` | First adjacent ally of attacker with `familiarity > 0.5` |

**Multiplicative modifiers (applied after additive, in this order):**

| Modifier | Type | Multiplier | Condition |
|---|---|---|---|
| Frozen/Shatter | multiplicative ATK | `× 1.50` | `any(s.kind == "frozen" for s in defender.combat.status_effects)` truthy |
| Sleep Exhaustion | multiplicative ATK | `× 0.80` | `attacker.biological.sleep_debt > 80.0` |
| Stamina Exhaustion | multiplicative ATK | `× exhaust_mult` | `StaminaService.get_exhaustion_multiplier(attacker.stamina) < 1.0` only |

### Step 2 — Fractional Armor Mitigation

```python
atk_eff = float(attacker.combat.atk) * atk_mult
dfn_eff = float(defender.combat.def_stat) * def_mult
raw_damage = int(atk_eff * (atk_eff / (atk_eff + dfn_eff * 2.0 + 1.0)))
damage = max(1, raw_damage)
```

**Properties of this formula:**
- As `dfn_eff` → ∞, damage → 0 (but clamped to 1)
- As `dfn_eff` = 0, damage → `int(atk_eff)` (no mitigation)
- Defense doubles its effective weight via the `* 2.0` term — defense is stronger than attack

### Step 3 — Durability Decay

`_get_durability_decay()` — applied to both attacker and defender on every resolved hit:

| Entity | Slot | Delta |
|---|---|---|
| Attacker | `MAIN_HAND` | `-1.0` durability (only if slot occupied) |
| Defender | `TORSO` | `-0.5` durability (only if slot occupied) |
| Defender | `LEGS` | `-0.5` durability (only if slot occupied) |
| Defender | `HEAD` | `-0.5` durability (only if slot occupied) |

Broken equipment (`durability <= 0`) provides zero stat bonuses — enforced in `LevelingService.recalculate_combat_stats()`.

### Step 4 — Wound Infliction

`_get_wound_infliction(damage, defender, alive)`:

```python
if alive and damage > defender.combat.max_hp * 0.25:
    wound = Wound(
        kind="SLASH" if attacker is HERO else "CRUSH",
        severity=damage / defender.combat.max_hp,
        atk_penalty=5.0,
        def_penalty=5.0
    )
```

**Threshold:** `damage > max_hp * 0.25` (25%) — this is the source-authoritative value.

> **Divergence from chapter 02:** `02_combat_laws.md` states the wound threshold as 40% of max HP. The source `combat.py:583` uses 25%. Source is authoritative. Chapter 02 must be corrected separately. Parity ledger entry: COMB-290 (divergent).

Permanent scars: 30% of original wound penalty retained permanently (stated in chapter 01; source function not traced in current investigation scope).

### Step 5 — Death Check

```python
new_hp = defender.combat.hp - damage
alive = new_hp > 0
```

If `new_hp <= 0` → kill/defeat. The `alive` flag drives all reward and lifecycle logic. There is no explicit minimum HP floor in `resolve_attack`.

### Step 6 — Kill Rewards

`CombatRewardClassificationService.classify_defeated_target()`:

1. First tries faction relation projection via `FactionSemanticsService.is_hostile_compat()` with `combat_engaged=True`
2. If hostile by faction: `xp_multiplier=10`, `gold_multiplier=5`, not rebirth eligible
3. Fallback by `EntityRole`:
   - `MONSTER`: xp×10, gold×5, not rebirth eligible
   - `HERO`: xp×20, gold×50, rebirth eligible
   - other: xp×0, gold×0

```
xp_gain = defender.identity.evolution_level * classification.xp_multiplier
gold_gain = defender.identity.evolution_level * classification.gold_multiplier
```

Hero rebirth:
- `generation < 4` → `generation_delta=1`, `outcome="REBIRTH"`
- `generation >= 4` → `is_permadeath_set=True`, `outcome="PERMADEATH"`

---

## AoE Splash

`resolve_aoe_attack()`:
- **Primary target:** full formula damage (Steps 1–5 above)
- **Splash victims** (enemy faction, within radius, with LOS from target_pos): `splash_damage = attacker.combat.atk // 2`, minimum 1
- **Friendly fire:** faction-matched entities are skipped entirely
- AoE bypasses faction-relation classification in rewards — XP/gold use hardcoded ×10/×5 multipliers, not `CombatRewardClassificationService`

---

## Lifecycle

Damage resolution runs in the kernel's **Resolution** stage. `CombatResolutionSystem` processes all pending `ATTACK_TARGET` intents during that stage. Results (HP updates, durability updates, wound updates, reward grants) are committed by the apply path in the subsequent **Persistence** stage.

---

## Mutation Rules

**What can change on a hit:**
- `defender.combat.hp` (damage applied)
- `defender.combat` weapon/armor slot durability
- `attacker` MAIN_HAND durability
- `defender.combat.wounds` (if wound inflicted)
- `attacker.identity.evolution_points` (XP reward on kill)
- `attacker.inventory.gold` (gold reward on kill)
- Rebirth/permadeath flags on defender lifecycle

**What does not change:**
- Base attributes (STR, VIT, etc.) do not change from a single hit
- Tactical modifiers (`atk_mult`, `def_mult`) exist only for the duration of damage calculation — they are not persisted

---

## Edge Cases

| Scenario | Behavior |
|---|---|
| Zero-defense defender | `dfn_eff = 0` → `damage = int(atk_eff * 1.0)` (full attack, no mitigation) |
| Extremely high defense | damage → 1 (minimum clamp prevents 0) |
| Shatter + Sleep Exhaustion + Stamina Exhaustion all active | All three multiply together: `atk_eff = base_atk * atk_mult_additive * 1.50 * 0.80 * exhaust_mult` |
| Defender survives with exactly 1 HP | `alive=True`; wound infliction check still runs based on damage value |
| Damage exactly equals 25% max HP | `damage > max_hp * 0.25` is strict greater-than; exactly 25% does **not** trigger a wound |
| AoE hits attacker's ally | Faction check skips ally; ally takes no AoE damage |
| Hero at generation 4 killed | `is_permadeath_set=True` — no rebirth; `outcome="PERMADEATH"` |

---

## Examples

### Basic melee attack

```
Attacker: atk=20, bravery=0.6
Defender: def_stat=15, max_hp=100, hp=100

Tactical modifiers: none (no high ground, flanking, cover, frozen, sleep, stamina, bond)
atk_mult=1.0, def_mult=1.0

atk_eff = 20.0 * 1.0 = 20.0
dfn_eff = 15.0 * 1.0 = 15.0
raw_damage = int(20.0 * (20.0 / (20.0 + 15.0 * 2.0 + 1.0))) = int(20.0 * (20.0/51.0)) = int(7.84) = 7
damage = max(1, 7) = 7

Wound check: 7 > 100 * 0.25 = 25.0? No → no wound
```

### High-ground flanking attack with Shatter

```
Attacker: atk=30
Defender: def_stat=10, max_hp=80, hp=80, status_effects=[StatusEffectState(kind="frozen")]

Additive: high_ground → atk_mult += 0.20 → 1.20
          flanked → atk_mult += 0.15 → 1.35
Multiplicative: shatter → atk_mult *= 1.50 → 2.025

atk_eff = 30.0 * 2.025 = 60.75
dfn_eff = 10.0 * 1.0 = 10.0
raw_damage = int(60.75 * (60.75 / (60.75 + 20.0 + 1.0))) = int(60.75 * (60.75/81.75)) = int(45.07) = 45
damage = max(1, 45) = 45

Wound check: 45 > 80 * 0.25 = 20.0? Yes → wound inflicted
  severity = 45/80 = 0.5625, atk_penalty=5.0, def_penalty=5.0
```

---

## Source Areas

| Module | Role |
|---|---|
| `src/engine/combat.py` | `CombatResolutionSystem` — primary damage formula |
| `src/engine/combat.py:583` | `_get_wound_infliction()` — wound threshold (25%) |
| `src/engine/combat_rewards.py` | `CombatRewardClassificationService` — XP/gold classification |
| `src/engine/rpg_depth.py` | `StaminaService.get_exhaustion_multiplier()` — stamina ATK modifier |
| `src/progression/leveling.py` | `LevelingService.recalculate_combat_stats()` — broken equipment zero-out |

---

## Regression Tests

| Test / Group | Verified Law |
|---|---|
| COMB-071 `test_wound_infliction_massive_hit` | Wound triggers at >25% max HP (source-verified) |
| COMB-072 `test_wound_stat_impact` | Wound penalties apply to CombatComponent |
| COMB-073 / COMB-104 `test_scar_permanence` | Scar persistence after wound healing |
| COMB-021 `test_high_ground_bonus` | +0.20 ATK modifier |
| COMB-022 / COMB-055 `test_flanking_bonus` | +0.15 ATK modifier |
| COMB-024 `test_ranged_cover_bonus` | +0.30 DEF modifier |
| COMB-122 `test_shatter_combo` | Shatter multiplicative ×1.50 |
| COMB-074 `test_stamina_drain_on_attack` | Stamina consumed on attack |
| COMB-075 `test_exhaustion_penalty_application` | Stamina exhaustion reduces ATK |
| COMB-200 | Damage calculation math consistent with legacy rules |
| Parity ledger `combat_movement.yaml` COMB-290 | Wound threshold divergence (chapter=40%, source=25%) |

---

## Extension Rules

To add a new tactical modifier:
1. Implement the check function in `src/engine/combat.py` `_get_tactical_multipliers`
2. Determine whether it is additive or multiplicative, and add it in the correct phase (additive before multiplicative)
3. Document the modifier in this doc's modifier table and modifier sources table
4. Add regression tests covering: modifier applies when condition met, modifier does not apply when condition absent, interaction with existing multiplicative modifiers (compounding)
5. Update `02_combat_laws.md` if the modifier represents a new gameplay law
6. Update parity ledger with a verified entry once tests pass
