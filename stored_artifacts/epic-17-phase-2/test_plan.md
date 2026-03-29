# Test Plan: Epic 17 Phase 2

## 1. F6 & F8: World Age Scaling
- **Target**: `test_generator_scaling`
- **Action**: Mock `world_day` to 0, generate an entity. Mock `world_day` to 400, generate an entity.
- **Expects**: The entity generated at day 400 should have roughly 2x the base HP, ATK, and DEF compared to the first entity, and significantly higher levels.

## 2. F7: Faction Raids
- **Target**: `test_raid_trigger`
- **Action**: Fast forward ticks to `raid_interval_days * 100`.
- **Expects**: The `CalamitySystem` (or equivalent) should spawn a raiding party matching the scaled size. They should all be assigned the `AIState.RAID` state and placed outside the town sanctuary threshold.

## 3. F10: Camp Reinforcements
- **Target**: `test_camp_reinforcements`
- **Action**: Create a `Location` representing an `enemy_camp`. Fast-forward 500 ticks.
- **Expects**: If the camp has 0 guards, it should spawn exactly 1 guard. If the camp is completely full (e.g. 3 guards matching config max), the `reinforcement_level` should increment instead. Next spawned guard should reflect the `reinforcement_level` added to its `difficulty_tier`.
