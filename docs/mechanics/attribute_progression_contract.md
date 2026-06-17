---
status: authoritative
layer: mechanics
authority: P1
audience: agent
last_verified: 2026-06-13
tags: [attribute-progression, xp, leveling, derived-stats, skill-scaling, breakthrough]
related_chapter: 01_entity_anatomy.md
---

# Attribute Progression Contract

Companion sub-contract to `01_entity_anatomy.md`. That chapter covers the biological and physical foundation of entities; this doc gives the exact XP threshold formula, level-up execution steps, derived stat recalculation order, skill advancement scaling, and breakthrough placeholder status needed to safely implement or modify progression logic.

---

## Purpose

Define the complete attribute progression law: how entities accumulate XP, when and how level-ups fire, how derived stats are recalculated, how skills scale with attributes, and what the current implementation status of breakthroughs is.

---

## RPG Meaning

Entities grow through experience. XP is earned by defeating enemies and completing quests. Each level requires progressively more XP (power law). On level-up, entities gain 5 Attribute Points and unlock specific skills at milestone levels. All derived stats (HP, ATK, DEF, evasion, move cost, tactical role) are recalculated deterministically whenever attributes or equipment change.

---

## Inputs

| Field | Type | Description |
|---|---|---|
| `entity.identity.evolution_points` | `int` | Accumulated XP |
| `entity.identity.evolution_level` | `int` | Current level (1–99) |
| `entity.identity.unspent_ap` | `int` | Unspent attribute points |
| `entity.combat.attributes` | `AttributeAspect` | STR, AGI, VIT, INT, WIS, SPI, END |
| `entity.equipment` | `EquipmentAspect` | Equipped items by slot, with durability |
| `entity.identity.learned_skills` | `List[SkillId]` | Known skills |

---

## Core Rules

1. **XP accumulates in `identity.evolution_points`.** It is granted via the authoritative conservation path (`source_kind="COMBAT"` or `"QUEST"`) as an `IdentityUpdate(evolution_points_delta=xp_reward)`.

2. **Level threshold formula:**
   ```python
   XP_required_to_reach_next_level = int(100 * (level ** 1.5))
   ```
   Edge case: `level <= 0` returns 100.

3. **Level cap is 99.** At `current_level >= 99`, XP still accumulates but no level-up fires.

4. **Level-up does not chain.** `_execute_level_up` fires once per call. Excess XP carries over, but if the carry-over XP meets the next threshold, a second level-up does not fire in the same call — it fires on the next evaluation.

5. **+5 Attribute Points per level, always.** `unspent_ap_delta = 5` on every level-up regardless of level.

6. **Skill unlocks are level-gated:**
   - Level 2: `power_strike`
   - Level 5: `swift_reflexes`
   - Level 10: `fireball`

7. **Stat recalculation is triggered** whenever attributes or equipment change (level-up, AP spend, item equip/unequip, durability break).

8. **Biological pressures are combat-only modifiers** — they do not alter base stat values in `recalculate_combat_stats()`.

---

## Formula / Decision Logic

### XP Gain Sources

| Source | XP Grant |
|---|---|
| Monster kill | `defender.identity.evolution_level * 10` |
| Hero kill | `defender.identity.evolution_level * 20` |
| Quest reward | `evolution_points_delta` from `QUEST` source kind in conservation path |

XP source is traceable via `trace["REWARD_SOURCE"]` in `CombatUpdate`.

### XP Threshold Table

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

### Level-Up Execution (`_execute_level_up`)

```
1. new_level = identity.evolution_level + 1
2. rem_xp = total_xp - int(100 * (current_level ** 1.5))  # carry excess XP
3. ap_gain = 5
4. unlocked = []
   if new_level == 2: unlocked.append("power_strike")
   if new_level == 5: unlocked.append("swift_reflexes")
   if new_level == 10: unlocked.append("fireball")
5. return IdentityUpdate(
       evolution_level_set=new_level,
       evolution_points_delta=rem_xp - identity.evolution_points,
       unspent_ap_delta=5,
       learned_skills=unlocked
   )
```

### Attribute Point Allocation Gates

AP spend is validated in the apply path with four gates:
1. `PROG-067`: entity has sufficient unspent AP
2. `PROG-068`: attribute name is valid
3. `PROG-069`: aptitude multiplier applied (entity class/race may modify AP efficiency)
4. `PROG-070`: attribute value cap of 99 enforced

### Derived Stat Recalculation Order

`LevelingService.recalculate_combat_stats()` executes the following steps in strict order:

**Step 1 — Base Attributes:**
```python
max_hp    = base_hp + (vitality * 2) + int(endurance * 0.5)
atk       = base_atk + int(strength * 0.5)
def_stat  = base_def + int(vitality * 0.3)
evasion   = base_evasion + (agility * 0.001)
atk_range = 1  # default
```

**Step 2 — Equipment Bonuses (non-broken slots only, `durability > 0`):**
```python
atk       += item.properties["atk_bonus"]
def_stat  += item.properties["def_bonus"]
max_hp    += item.properties["hp_bonus"]
evasion   += item.properties["evasion_bonus"]
atk_range  = MAIN_HAND.properties["range"]   # overrides default if present
total_weight += item.weight
```

**Step 3 — Passive Skill Bonuses (`SkillKind.PASSIVE` only):**
```python
# swift_reflexes:
evasion += skill.power
# other passives added as new skills registered
```

**Step 4 — Trait Bonuses:**
```python
if "Tough" in traits:  max_hp  += 20
if "Quick" in traits:  evasion += 0.02
if "Strong" in traits: atk     += 3
```

**Step 5 — Movement Cost:**
```python
move_cost = max(5.0, 10.0 + (total_weight / 5.0) - (agility * 0.1))
```

**Step 6 — Tactical Role Derivation (with hysteresis):**
```python
scores = {VANGUARD: strength, SKIRMISHER: agility, PROTECTOR: vitality}
new_role = max(scores, key=scores.get)
# Hysteresis: only switch if new_role_score > current_role_score + 5
if scores[new_role] > scores[current_role] + 5:
    current_role = new_role
```

---

## Skill Advancement Scaling

`SkillScalingService` applies attribute-driven scaling to skill power at use time:

| Skill Type | Scaled Power Formula |
|---|---|
| `PHYSICAL` | `skill.power * (1.0 + attributes.strength * 0.02)` |
| `MAGICAL` | `skill.power * (1.0 + attributes.intelligence * 0.03)` |
| `ELEMENTAL` | `skill.power * (1.0 + attributes.spirit * 0.025 + attributes.wisdom * 0.01)` |
| `PASSIVE` (swift_reflexes) | `skill.power * (1.0 + attributes.agility * 0.01)` |

---

## Biological Pressure Interaction with Progression

Biological pressures affect combat multipliers but do **not** alter base stat values in `recalculate_combat_stats()`:

| Pressure | Effect |
|---|---|
| `sleep_debt > 80.0` | `atk_mult *= 0.80` in combat resolution only |
| Hunger = 100.0 (starvation) | 5 damage per tick — no stat reduction on attributes |
| Stamina exhaustion | `exhaust_mult < 1.0` applied to atk in combat via `StaminaService` |

---

## Breakthroughs

`BreakthroughService.REGISTRY` defines 3 breakthroughs:

| Breakthrough | Bonuses |
|---|---|
| `iron_will` | +2 spirit, +2 wisdom |
| `fleet_foot` | +3 agility, +0.05 flat evasion |
| `titan_grip` | +4 strength |

**Current status:** `apply_bonuses()` is a placeholder — full synergy logic is **not yet implemented**. A placeholder comment in `src/progression/breakthroughs.py` confirms this is deferred work. Breakthroughs should not be cited as active gameplay mechanics until `apply_bonuses()` is implemented. Agents extending this area must implement it before relying on breakthrough effects.

---

## Lifecycle

Progression evaluation runs in the **lifecycle systems phase** after combat resolution:
- XP grants are emitted as `IdentityUpdate(evolution_points_delta=...)` from combat/quest resolution
- `LevelingService` evaluates accumulated XP against threshold — level-up fires if threshold crossed
- `recalculate_combat_stats()` is triggered by the apply path after any `IdentityUpdate` that modifies `evolution_level`, `attributes`, or equipment

---

## Mutation Rules

**What changes on level-up:**
- `identity.evolution_level` (incremented by 1)
- `identity.evolution_points` (carry-over XP only)
- `identity.unspent_ap` (+5)
- `identity.learned_skills` (new unlocks appended)
- All derived combat stats (via `recalculate_combat_stats()`)

**What does not change on level-up:**
- Base attributes (STR, VIT, etc.) — these change only when AP is spent
- Equipment (unchanged by level-up)
- Biological pressure accumulators (hunger, sleep_debt, stamina)

---

## Edge Cases

| Scenario | Behavior |
|---|---|
| Entity at level cap (99) gains XP | `evolution_points_delta` recorded, no level-up fires |
| XP carry-over meets next threshold | Second level-up fires on next evaluation cycle, not in same call |
| Attribute reaches cap (99) + AP spend attempted | Gate PROG-070 rejects; unspent AP unchanged |
| Equipment breaks during combat | `durability <= 0` → stat contribution zeroed on next `recalculate_combat_stats()` call |
| Passive skill (`swift_reflexes`) equipped before level-up | Evasion bonus applies in Step 3 of recalc on the next stat recalculation |
| Role score tie (e.g. VANGUARD and PROTECTOR equal) | `max()` returns first matched key — tie-breaking is implementation-defined by dict iteration order |
| Breakthrough triggered at level-up | `apply_bonuses()` placeholder returns without applying bonuses — no effect until implemented |

---

## Examples

### Level 3 → 4 level-up

```
Current XP: 523, current_level=3
Threshold for level 4: int(100 * 3**1.5) = int(100 * 5.196) = 519

523 > 519 → level-up fires
new_level = 4
rem_xp = 523 - 519 = 4 XP carry-over
ap_gain = 5
unlocked = []  (level 4 has no skill unlock)

IdentityUpdate(evolution_level_set=4, evolution_points_delta=4-523=-519, unspent_ap_delta=5)
```

### Stat recalculation after leveling STR to 20 (vitality=15, agility=10, endurance=8)

```
Step 1 (base attributes):
  max_hp = 80 + (15*2) + int(8*0.5) = 80 + 30 + 4 = 114
  atk = 10 + int(20*0.5) = 10 + 10 = 20
  def_stat = 5 + int(15*0.3) = 5 + 4 = 9
  evasion = 0.05 + (10*0.001) = 0.06
  atk_range = 1

Step 2 (equipment — iron sword MAIN_HAND durability=100, atk_bonus=5, range=1):
  atk += 5 → 25
  atk_range = 1 (no change from weapon range property)
  total_weight += 3.0

Step 3 (passives — swift_reflexes power=0.02):
  evasion += 0.02 → 0.08

Step 4 (traits — "Strong" present):
  atk += 3 → 28

Step 5 (movement cost):
  move_cost = max(5.0, 10.0 + (3.0/5.0) - (10*0.1)) = max(5.0, 10.0 + 0.6 - 1.0) = max(5.0, 9.6) = 9.6

Step 6 (role — STR=20, AGI=10, VIT=15 → VANGUARD leads):
  scores = {VANGUARD:20, SKIRMISHER:10, PROTECTOR:15}
  new_role = VANGUARD; if VANGUARD_score > current_role_score + 5 → switch
```

---

## Source Areas

| Module | Role |
|---|---|
| `src/progression/leveling.py` | `LevelingService` — threshold formula, level-up execution, stat recalc |
| `src/progression/skills.py` | `SkillScalingService` — attribute-driven skill power scaling |
| `src/progression/breakthroughs.py` | `BreakthroughService` — registry + placeholder `apply_bonuses()` |
| `src/progression/evolution.py` | Entity evolution on level cap events |
| `src/systems/lifecycle_systems/` | Lifecycle system invoking LevelingService per tick |

---

## Regression Tests

| Test / Group | Verified Law |
|---|---|
| `tests_v2/parity/test_progression_parity.py` | XP threshold formula, level cap, AP grants |
| COMB-082 `test_attribute_synergy_xp_mult` | Wisdom/Intelligence XP multiplier |
| COMB-081 `test_well_rested_effect_application` | Well-Rested buff affects max HP |
| Parity ledger `progression.yaml` | `xp_threshold_formula` (verified), `level_cap_enforced` (verified) |
| Parity ledger `progression.yaml` PROG-067–PROG-070 | AP allocation gates |
| `tests_v2/test_skill_scaling.py` | PHYSICAL/MAGICAL/ELEMENTAL scaling formulas |

---

## Extension Rules

To add a new skill unlock:
1. Add the level and skill ID to the conditional in `_execute_level_up` in `src/progression/leveling.py`
2. Register the skill in the skill registry with correct `SkillKind` (PASSIVE or ACTIVE)
3. If PASSIVE: add stat contribution logic to Step 3 of `recalculate_combat_stats()`
4. If ACTIVE: add to `SkillScalingService` with the correct type formula
5. Add regression tests covering: unlock fires at correct level, stat contribution applies, scaling formula verified
6. Update this doc and `01_entity_anatomy.md` if the skill changes progression gameplay

To implement breakthroughs:
1. Replace the placeholder in `BreakthroughService.apply_bonuses()` with actual attribute delta logic
2. Hook `apply_bonuses()` into the level-up or event trigger path
3. Add a `recalculate_combat_stats()` call after breakthrough application
4. Update this doc's Breakthroughs section from "placeholder" to "authoritative"
5. Add parity ledger entries in `progression.yaml` with `status: verified`
