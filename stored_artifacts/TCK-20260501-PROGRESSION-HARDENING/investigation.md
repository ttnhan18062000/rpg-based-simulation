# Investigation: Progression, Skills, Equipment, and Crafting

## Current State Audit
- **XP**: `LevelingService` exists but is currently mixed with item rewards in some flows. Needs a clean separation.
- **Equipment**: `EquipmentComponent` exists but `EquipmentService` lacks a robust durability/repair lifecycle.
- **Crafting**: Scattered logic in `InteractionComponent` and legacy scripts. Needs a unified, authoritative `CraftingSystem`.
- **Scaling**: `SkillScalingService` is the right place for derived stats but needs to account for equipment weight and skill buffs.

## Architectural Constraints
- ALL progression changes must flow through `IdentityUpdate`.
- Durability repair MUST be a resource transaction.
- Derived stats (SPD, ATK, DEF) must be recalculated whenever equipment or level changes.

## Key Challenges
- **Weight Burden**: Calculating total inventory + equipment weight and applying a non-linear SPD penalty.
- **Recipe Gates**: Ensuring the simulation doesn't "cheat" by crafting unknown items.
