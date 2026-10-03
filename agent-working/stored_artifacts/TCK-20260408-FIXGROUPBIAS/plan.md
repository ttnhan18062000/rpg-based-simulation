---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260408-FIXGROUPBIAS
artifact_type: plan
tags: [fixgroupbias]
---

# Plan: TCK-20260408-FIXGROUPBIAS

## Implementation Steps
1. **Modify `tests/integration/social/test_group_coordination.py`**:
    - Update `raider2` position from `Vector2(70, 70)` to `Vector2(60, 60)` to ensure a Manhattan distance of 20.
    - Wait! A distance of 20 results in `2.0 - (20/15) = 2.0 - 1.33 = 0.66` cohesion.
    - `cohesion_bonus = 0.66 * 0.5 = 0.33`. `weight = 1.33`. `1.33 > 1.2`!
    - Proximity bias: `dist = 20`. `20 > 5` is true. `(20-5)*0.2 = 3.0`. `weight = 4.0`. `4.0 > 1.2`!
    - So a distance of 10 to 20 tiles works well. I'll use `Vector2(60, 60)` (Manhattan distance 20).
2. **Cleanup `src/ai/brain.py`**:
    - Remove all `print` statements added for debugging group biases.
    - Re-comment or remove the original debug prints if appropriate. (I'll remove the ones I added).
3. **Cleanup `src/systems/social/group_system.py`**:
    - Remove all `print` statements related to group formation and cohesion.

## Affected Files
- [MODIFY] [test_group_coordination.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/social/test_group_coordination.py)
- [MODIFY] [brain.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/brain.py)
- [MODIFY] [group_system.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social/group_system.py)

## Intended Behavior
- Group biases correctly applied when cohesion is > 0.
- Proximity bias correctly applied when distance > 5.

## Rollback Notes
- If test still fails, revisit the `GroupSystem` maintenance loop to ensure `on_tick` correctly calculates `avg_dist`.
