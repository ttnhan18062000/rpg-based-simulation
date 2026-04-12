# Investigation - Regression Suite Failures

## Failures Summary

### 1. `test_chaos_mode_resilience`
- **Error**: `AttributeError: type object 'InterpretedLifeEventKind' has no attribute 'HOMECOMING'`
- **Cause**: The `HOMECOMING` enum member was recently introduced in business logic/events but not added to the central `enums.py`.

### 2. `test_scaling_500_entities` (Remediation)
- **Error**: `NameError: name 'run_bench' is not defined`
- **Cause**: Missing import in `tests/remediation/test_behavioral_realism_remediation.py`.

### 3. `test_explore_goal_baseline`
- **Error**: `AssertionError: assert 0.4 <= 0.3`
- **Cause**: `ExploreGoal` base score was increased to `0.4` in Phase 4, but the unit test still expects `0.3`.

### 4. `test_goal_commitment_and_anti_jitter`
- **Error**: `AssertionError: assert <AIState.COMBAT: 3> == <AIState.WANDER: 1>`
- **Cause**: AI brain is likely ignoring the goal lock. Investigation revealed that `AIBrain` and `CombatArena` use separate `FactionRegistry` instances, which can lead to inconsistent hostile status checks in tests.

### 5. `test_scaling_1000_entities`
- **Error**: `AssertionError: 0.084 > 0.1`
- **Cause**: TPS fell below the 0.1 threshold. This is likely due to the increased overhead of Phase 3/4 strategic and routine logic.

### 6. `test_ai_prefers_aoe_when_clustered`
- **Error**: `AssertionError: AI should prefer Whirlwind when 2 enemies adjacent`
- **Cause**: Skill utility calculation in `Combat` state or `SkillScorer` is not correctly weighing regional/cluster targets for AoE.
