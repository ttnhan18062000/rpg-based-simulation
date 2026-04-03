# Test Plan - TCK-20260325-RPG_SIMULATION_REVIEW

## Unit Tests

### Flow Fields
- Verify Town/Camp field generation on world init.
- Test `FlowFieldManager.get_direction(pos, target_type)` returns correct vector.
- Test entity switches from Flow Field to A* correctly at the 15-tile boundary.

### Stamina Exhaustion
- Test `StatusEffectType.EXHAUSTED` application at 0 stamina.
- Test speed and ATK debuffs are applied during exhaustion.
- Test recovery happens at >20% stamina.

### Gold Sinks
- Test `EnhancementSystem` cost calculation for +1, +6, and +11 levels.
- Test material checks for Iron Ore, Enchanted Dust, and Calamity Essence.
- Test stat bonuses are applied correctly to the item template/instance.

### Purity Fixes
- Test `Guild.global_memory` updates only when a hero returns from exploration.
- Test `QuestGenerator` skips regions unknown to the Guild.
- Test `AuraSystem` applies debuffs only within 50 tiles of a Stronghold.
- Test `CombatAction` skips grudge gain if attacker is hidden in Fog of War.

## Integration Tests
- `tests/e2e/test_long_range_pathfinding.py`: Verify group of entities returning to town simultaneously without dropping tick rate.
- `tests/e2e/test_combat_exhaustion_loop.py`: Verify AI organic kiting/resting behavior when exhausted.

## Regression Surface
- Ensure A* tactical movement still works for HUNT targets.
- Ensure existing status effects (Poison, Stun) still function with the new Exhaustion effect.
- Ensure item durability or other legacy systems aren't broken by enhancement.
