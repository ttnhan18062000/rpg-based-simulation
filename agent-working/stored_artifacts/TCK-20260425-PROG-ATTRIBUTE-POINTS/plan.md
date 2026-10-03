---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260425-PROG-ATTRIBUTE-POINTS
artifact_type: plan
tags: [prog, attribute, points]
---

# Implementation Plan — PH8 M5: Attribute Points and Manual Growth

This milestone implements the Attribute Point (AP) system and manual growth for Heroes, while maintaining automatic scaling for Monsters.

## Proposed Changes

### Core State & Models

#### [MODIFY] [state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- Add `AttributeComponent` dataclass.
- Update `IdentityComponent` to include `unspent_ap: int = 0`.
- Update `EntityState` to include an `attributes` field.

#### [MODIFY] [builder.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/builder.py)
- Update `V2EntityBuilder` to initialize and build the `AttributeComponent`.
- Ensure attributes are persisted in the final `EntityState`.

---

### Progression Logic

#### [MODIFY] [leveling.py](file:///home/vboxuser/Work/rpg-based-simulation/src/progression/leveling.py)
- Update `scale_combat_stats` to skip Hero scaling.
- Implement `grant_ap(identity, amount)` or similar logic.
- Implement `recalculate_combat_stats(attributes, base_combat)` to derive combat values from attributes.

---

### Actions & Authority

#### [NEW] [attributes.py](file:///home/vboxuser/Work/rpg-based-simulation/src/actions/attributes.py)
- Implement `AllocateAttributeAction`.

#### [MODIFY] [apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)
- Handle `AllocateAttributeAction` in the apply path.
- Trigger `CombatUpdate` upon attribute allocation.

---

## Verification Plan

### Automated Tests
- Run `pytest tests/progression/test_attribute_growth.py` (to be created).
- Verify:
    - Heroes get 5 AP on level up.
    - Monsters do NOT get AP but scale by 1.1x.
    - Allocation increases attributes and reduces AP.
    - Combat stats (HP/ATK/DEF) update immediately after allocation.
    - Aptitude multipliers are applied (PROG-015).
    - Attribute cap of 100 is respected (PROG-046).

### Manual Verification
- Inspect replay traces to see AP allocation and stat shifts.
