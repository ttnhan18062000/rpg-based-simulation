---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260805-PROGRESSION-ENTITIES-SKILL
artifact_type: investigation
tags: [skills, progression]
---

# Investigation — TCK-20260805-PROGRESSION-ENTITIES-SKILL

## Real Content Grounded

### `docs/mechanics/01_entity_anatomy.md` (Mechanics Bible ch.1, P0 authoritative)
- **9 core attributes** (1-99 scale): STR, AGI, VIT, END, INT, SPI, WIS, PER, CHA — each with a
  real one-line impact description.
- **Derived combat stat formulas** (exact): `Max_HP = base_hp + (vitality*2) + int(endurance*0.5)
  + gear_hp`; `Max_Stamina = 50.0 + (endurance*5.0)`; `Attack = base_atk + int(strength*0.5) +
  gear_atk`; `Defense = base_def + int(vitality*0.3) + gear_def`; `Evasion = base_evasion +
  (agility*0.001) + gear_evasion`; `Move_Cost = max(5.0, 10.0 + (total_weight/5.0) -
  (agility*0.1))`.
- **`TacticalRole`** derived from highest attribute, **5-point hysteresis** to prevent flickering:
  VANGUARD (Strength), SKIRMISHER (Agility), PROTECTOR (Vitality).
- **Class Registry**: Novice/Warrior/Mage/Rogue with real base HP/ATK/DEF/starting gear.
- **Biological decay**: Hunger `+0.1`/tick (95.0 threshold → +2 HP dmg/tick), Sleep Debt
  `+0.05`/tick (98.0 threshold → +1 HP dmg/tick), Stamina `-1.0`/move.
- **XP curve**: `XP_Required = int(100 * (level ** 1.5))`. Level cap 99. +5 AP/level. Skill
  unlocks at level 2 (`power_strike`), 5 (`swift_reflexes`), 10 (`fireball`).

### `docs/mechanics/attribute_progression_contract.md`
- **Real XP threshold table** (exact values): 1→2: 100, 2→3: 283, 3→4: 520, 5→6: 1,118, 10→11:
  3,162, 20→21: 8,944, 50→51: 35,355, 98→99: ~969,440.
- **`_execute_level_up`** algorithm (5 real steps, exact): new_level increment, carry excess XP
  (`rem_xp = total_xp - int(100 * (current_level**1.5))`), `ap_gain = 5`, real skill-unlock
  thresholds, returns `IdentityUpdate(...)`.
- **4 real AP-allocation gates** with Compliance IDs: `PROG-067` (sufficient unspent AP),
  `PROG-068` (valid attribute name), `PROG-069` (aptitude multiplier), `PROG-070` (99 cap).
- **`LevelingService.recalculate_combat_stats()`**: 6-step strict-order recalculation (Base
  Attributes → Equipment Bonuses [non-broken slots only] → Passive Skill Bonuses → Trait Bonuses
  → Movement Cost → Tactical Role Derivation with hysteresis) — exact code for each step,
  including the same 5-point-hysteresis rule as ch.1, confirming consistency between the two docs.

### `docs/engine/authoritative_pipeline.md`
Phase 23 `evolution` ("Applies entity evolution and stat boosts") and phase 24
`progression_conversion` ("Enhanced RPG: converts progression points to levels/skills") — the
ticket's own cited phases, confirmed by grep, adjacent in the pipeline order (23 then 24).

### Real file/test confirmation
`src/progression/`: `leveling.py` (matches `LevelingService`), `evolution.py` (matches
`evolution_level`), `breakthroughs.py`, `skills.py`, `veterancy.py`. `src/entities/`:
`archetype_factory.py`, `identity_resolver.py`, `contract_builder.py`, `runtime_contract.py`. Real
tests: `tests/unit/progression/test_leveling.py`, `test_attribute_growth.py`,
`test_evolution.py`, `test_classes_loadouts.py`.

## Scope Decision
One skill, `progression-entities`, covering both files' real content — core attributes/derived
stats/biological pressures (ch.1) and the exact XP/level-up/AP-allocation mechanics (the
companion contract doc) — since they're tightly coupled (the derived-stat recalculation order in
the contract doc directly operationalizes ch.1's formulas).

## Unresolved Questions
None — all cited content verified against 2 real docs, real phase names, and real file/test paths.
