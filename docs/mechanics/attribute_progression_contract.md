---
status: authoritative
layer: mechanics
authority: P1
audience: agent
last_verified: 2026-08-26
tags: [attribute-progression, xp, leveling, derived-stats, skill-scaling, breakthrough]
related_chapter: 01_entity_anatomy.md
---

# Attribute Progression Contract

Companion sub-contract to `01_entity_anatomy.md`. That chapter covers the biological and physical foundation of entities; this doc gives the exact XP threshold formula, level-up execution steps, derived stat recalculation order, skill advancement scaling, and breakthrough bonus-application rules needed to safely implement or modify progression logic.

---

## Purpose

Define the complete attribute progression law: how entities accumulate XP, when and how level-ups fire, how derived stats are recalculated, how skills scale with attributes, and how breakthrough attribute bonuses are applied.

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

AP spend is validated across two layers, not uniformly "in the apply path" — each gate's actual
current enforcement location (see `DEV-004`, `docs/guidelines/intentional_divergences.md`):
1. `PROG-067`: entity has sufficient unspent AP — enforced in the domain-handler layer,
   `core_actions.py::execute_allocate_ap`, not the apply path.
2. `PROG-068`: attribute name is valid — **not enforced on the live path** (see the corrected
   `PROG-068` entry in `docs/parity_ledger/progression.yaml`).
3. `PROG-069`: aptitude multiplier applied (entity class/race may modify AP efficiency) — **not
   enforced on the live path** (see the corrected `PROG-069` entry in
   `docs/parity_ledger/progression.yaml`).
4. `PROG-070`: attribute value cap of 100 enforced in the apply path, `AttributePatch.apply`
   (`src/engine/patches.py:570-585`).

### Derived Stat Recalculation Order

`LevelingService.recalculate_combat_stats()` executes the following steps in strict order. When
called via `SkillScalingService.get_effective_stats()` (the live apply-path entry point), the
`attributes` argument it receives is **already breakthrough-bonus-adjusted** —
`get_effective_stats()` calls `BreakthroughService.apply_bonuses(active_breakthroughs, attributes)`
first and passes the result in. `recalculate_combat_stats()` itself has no breakthrough awareness;
Step 1 below reads whatever `attributes` it is given.

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

**Current status:** `apply_bonuses(breakthrough_ids, current_attributes) -> AttributeComponent` is
implemented (`src/progression/breakthroughs.py`). It is a pure function: given a set of
breakthrough IDs and a base `AttributeComponent`, it sums each active breakthrough's
`attribute_bonuses` and returns a new `AttributeComponent` via `dataclasses.replace()`. Unknown
IDs are ignored; an empty ID set returns `current_attributes` unchanged.

It is wired into the live effective-stats path: `SkillScalingService.get_effective_stats()`
(`src/engine/rpg_depth.py`) takes an `active_breakthroughs` parameter, calls `apply_bonuses()` on
it before calling `recalculate_combat_stats()` (see Derived Stat Recalculation Order above), and
`ApplyPath._apply_entity_update_to_dict()` (`src/engine/apply.py`) passes the entity's
post-patch `identity.active_breakthroughs` into that call.

**Known gap:** `fleet_foot`'s `evasion_flat: 0.05` bonus is **not applied** — it targets the
derived evasion stat directly rather than `attribute_bonuses`, and `apply_bonuses()`'s signature
(`Set[str], AttributeComponent -> AttributeComponent`) has no channel for a derived-stat bonus.
Only `fleet_foot`'s `attribute_bonuses: {agility: 3}` portion is applied. This is a scoped,
intentional gap (TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION), not a defect.

**Separately unimplemented:** nothing in production/gameplay code constructs
`IdentityUpdate(breakthroughs_add=[...])` — the mechanic that grants a breakthrough (populating
`identity.active_breakthroughs`) is fully wired end-to-end (`IdentityUpdate` → `IdentityPatch` →
state) but is never invoked outside tests (see `TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION`).
Bonus *application* (this section) is independent of bonus *granting* and does not require it.

---

## Lifecycle

Progression evaluation runs in the **lifecycle systems phase** after combat resolution:
- XP grants are emitted as `IdentityUpdate(evolution_points_delta=...)` from combat/quest resolution
- `LevelingService` evaluates accumulated XP against threshold — level-up fires if threshold crossed
- `recalculate_combat_stats()` is triggered by the apply path (`ApplyPath._apply_entity_update_to_dict`'s `stats_dirty` gate) after any `IdentityUpdate` that modifies `evolution_level`, `attributes`, equipment, `learned_skills`, `traits_add`/`traits_remove`, or `breakthroughs_add`

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
| Attribute reaches cap (100) + AP spend attempted | Gate PROG-070 rejects; unspent AP unchanged |
| Equipment breaks during combat | `durability <= 0` → stat contribution zeroed on next `recalculate_combat_stats()` call |
| Passive skill (`swift_reflexes`) equipped before level-up | Evasion bonus applies in Step 3 of recalc on the next stat recalculation |
| Role score tie (e.g. VANGUARD and PROTECTOR equal) | `max()` returns first matched key — tie-breaking is implementation-defined by dict iteration order |
| Entity has `active_breakthroughs` populated | `apply_bonuses()` sums matching registry `attribute_bonuses` and applies them before `recalculate_combat_stats()` runs |
| `active_breakthroughs` is empty or `None` | `apply_bonuses()` returns `current_attributes` unchanged (no-op) |
| Unknown breakthrough ID in `active_breakthroughs` | Ignored, no error raised |
| `fleet_foot` active | Its `agility +3` is applied; its `evasion_flat: 0.05` is not (unwired, see Breakthroughs section) |

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
| `src/progression/breakthroughs.py` | `BreakthroughService` — registry + `apply_bonuses()` (implemented) |
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
| `tests/unit/progression/test_breakthroughs.py` | `apply_bonuses()` sum/empty/unknown/mixed-ID behavior; parity ledger PROG-024 |
| `tests/unit/core/test_rpg_depth.py` | `active_breakthroughs` wiring through `get_effective_stats()` and the apply path's `stats_dirty` gate |

---

## Extension Rules

To add a new skill unlock:
1. Add the level and skill ID to the conditional in `_execute_level_up` in `src/progression/leveling.py`
2. Register the skill in the skill registry with correct `SkillKind` (PASSIVE or ACTIVE)
3. If PASSIVE: add stat contribution logic to Step 3 of `recalculate_combat_stats()`
4. If ACTIVE: add to `SkillScalingService` with the correct type formula
5. Add regression tests covering: unlock fires at correct level, stat contribution applies, scaling formula verified
6. Update this doc and `01_entity_anatomy.md` if the skill changes progression gameplay

To add a new breakthrough:
1. Register the ID in `BreakthroughService.REGISTRY` (`src/progression/breakthroughs.py`) with
   an `attribute_bonuses` dict keyed by `AttributeComponent` field name
2. If the bonus targets a derived stat rather than a base attribute (like `fleet_foot`'s
   `evasion_flat`), it will **not** apply automatically — `apply_bonuses()` only sums
   `attribute_bonuses` onto `AttributeComponent`; a derived-stat bonus needs its own wiring
   (currently unimplemented, see the Breakthroughs section's Known gap above)
3. Update the Breakthroughs section's registry table above and `01_entity_anatomy.md`
   Section 5's Breakthroughs subsection
4. Add or update parity ledger entries in `progression.yaml` with a real `test_path`
