---
content_type: doc
status: historical
layer: core
authority: P2
audience: agent
tags: [prog, attribute, points]
---

# Walkthrough - Attribute Points and Manual Growth (PH8 M5)

I have successfully implemented the Attribute Points (AP) and Manual Growth system for the V2 engine. This implementation follows the **Authoritative Apply Path** (M8 Law) and introduces a **Hybrid Growth Model** as requested.

## Key Changes

### 1. State Persistence
Added `AttributeComponent` to [state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py) and updated `IdentityComponent` to track `unspent_ap`.
```python
@dataclass(frozen=True, slots=True)
class AttributeComponent:
    strength: int = 5
    agility: int = 5
    # ... all 9 attributes
```

### 2. Authoritative Updates
Introduced `AttributeUpdate` in [updates.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/updates.py) and expanded `EntityUpdate` to include it.

### 3. Hybrid Leveling Logic
Updated [leveling.py](file:///home/vboxuser/Work/rpg-based-simulation/src/progression/leveling.py) to differentiate between Heroes and Monsters:
- **Monsters**: Continue to scale automatically (+10% stats per level).
- **Heroes**: Automatic scaling is disabled; they receive **5 Attribute Points (AP)** per level instead.

### 4. Deterministic Recalculation
Implemented `recalculate_combat_stats` in `LevelingService` to derive combat stats (HP, ATK, DEF, Evasion) from base attributes using the approved formulas. This is automatically triggered in the [ApplyPath](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py) whenever attributes change.

### 5. Manual Allocation Action
Created [AllocateAttributeAction](file:///home/vboxuser/Work/rpg-based-simulation/src/actions/attributes.py) which allows entities to spend AP. It respects **Aptitude multipliers (PROG-015)** and **Attribute caps (PROG-046)**.

## Verification Results

I created a comprehensive test suite in [test_attribute_growth.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/progression/test_attribute_growth.py) which verifies:
- Heroes gain 5 AP on level up.
- Monsters scale stats automatically without gaining AP.
- Attribute allocation correctly recalculates combat stats.
- Aptitude multipliers correctly scale the points granted per AP.
- Attributes are capped at 100.

### Test Execution Output
```text
tests/progression/test_attribute_growth.py .....                      [100%]
============================== 5 passed in 0.20s ===============================
```

> [!IMPORTANT]
> The engine now strictly enforces the Hybrid model. If you notice Heroes are too weak compared to Monsters, ensure they are spending their AP via the `AllocateAttributeAction`.
