# Investigation: TCK-20260408-FIXGROUPBIAS

## Findings
- `test_brain_group_behavior_bias` was failing because the `raider2` entity was placed at `(70, 70)` while the leader `raider1` was at `(50, 50)`.
- Manhattan distance of 40 resulted in `cohesion_level` of `0.0` based on the formula `2.0 - (avg_dist / 15.0)`.
- Cohesion of `0.0` led to a `shared_goal_bias` of `1.0` (no effect), causing the assertion `> 1.2` to fail.
- Debug instrumentation in `AIBrain` and `GroupSystem` confirmed this state.

## Reused Patterns
- `GroupRecord` and `AIBrain` integration follows the multiplicative bias pattern used for personality and social appraisal.

## Assumptions
- A distance of 10 tiles should provide sufficient cohesion (~1.33) and trigger both shared goal and proximity biases.

## Risks
- Cohesion logic might be too aggressive for larger groups; but for this tactical phase, 15 tiles is a reasonable threshold for "scattered" groups.
