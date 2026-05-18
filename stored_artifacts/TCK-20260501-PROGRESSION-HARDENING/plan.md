# Plan: Phase E4.5 — Progression, Skills, Equipment, and Crafting Completion

This phase hardens the core RPG loop by ensuring that character growth and equipment are authoritative, impactful, and transactionally sound.

## Proposed Changes

### [Component] Progression & Attributes
#### [MODIFY] [leveling.py](file:///home/vboxuser/Work/rpg-based-simulation/src/progression/leveling.py)
- Ensure XP rewards are separated from item/gold rewards in `process_reward`.
- Enforce level caps and attribute allocation rules.
- Implement skill unlocking when reaching specific level thresholds.

### [Component] Equipment & Durability
#### [MODIFY] [equipment_service.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/equipment_service.py)
- Implement `apply_durability_loss` during combat or work.
- Implement `repair_equipment` transactional logic (requires gold/materials).
- Ensure broken equipment (durability = 0) provides zero stat bonuses.

### [Component] Crafting & Recipes
#### [NEW] [crafting.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/crafting.py)
- Implement `CraftingSystem` to enforce gates:
    - **Recipe Check**: Offerer must know the recipe.
    - **Material Check**: Consumes correct `ItemStacks`.
    - **Skill Check**: Minimum level/attribute requirements.
    - **Output Check**: Enough inventory space for the result.

### [Component] Derived Stat Scaling
#### [MODIFY] [rpg_depth.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/rpg_depth.py)
- Update `SkillScalingService.get_effective_stats` to include:
    - Equipment weight burden (SPD penalty).
    - Skill-based modifiers (e.g., +5 ATK from "Sword Mastery").
    - Durability scaling.

## Verification Plan

### Automated Tests
- `pytest tests/engine/test_progression_lifecycle.py`
    - Test: XP gain with full inventory.
    - Test: Equipment durability loss and repair transaction.
    - Test: Crafting rejections (missing materials, unknown recipe).
    - Test: Stat derivation with burden and skills.

### Manual Verification
- Verify `IdentityUpdate` records in logs show correct AP/SP allocation.
