# Test Plan - Simulation Regression Fix

## Objective
Restore 100% stability to the simulation regression suite.

## Automated Tests

### Unit Tests
- `pytest tests/unit/ai/test_goals.py`: Verify goal scoring logic and base utilities.
- `pytest tests/unit/ai/test_pathfinding.py`: (If applicable) Verify fix for maze navigation.

### Integration Tests
- `pytest tests/integration/infrastructure/test_chaos.py`: Verify enum resolution and resilience logic.
- `pytest tests/integration/test_chaos.py`: Duplicate check.

### E2E Tests
- `pytest tests/e2e/test_combat_arena_e2e.py`:
    - `TestAIRefinementE2E::test_goal_commitment_and_anti_jitter`: Verify jitter prevention.
    - `TestAoESkillsE2E::test_ai_prefers_aoe_when_clustered`: Verify AoE prioritization.
    - `TestMultiEntityCombatE2E::test_ranged_and_melee_hero_vs_mob`: Verify ranged engagement.

### Benchmarks
- `pytest tests/benchmarks/test_scaling_bench.py`: Verify TPS thresholds.

## Manual Verification
- None.
