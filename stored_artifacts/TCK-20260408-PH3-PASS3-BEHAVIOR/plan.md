# Implementation Plan - Phase 3 Pass 3: Behavioral Integration

## Implementation Steps
1. **Enhance RoutineService**: Update `src/core/logic/routine_service.py` to iterate through `routine_profiles` and apply biases based on `ideal_goal` and `priority` when within the schedule window.
2. **Add Disruption Check**: Implement logic to suppress routine biases if `disrupted_until_tick` is in the future or `emotion.panic` is high (> 0.4).
3. **Integrate Place Bias**: Update `RoutineService` or `AIBrain` to inject `PlaceAttachment` metadata into goal biases, making `REST`/`SLEEP` favor `HOME` locations.
4. **Group Coordination**: Implement a new `src/core/logic/group_coordinator.py` (or update `AIBrain`) to scan nearby cluster members and apply a small "consensus bias" to goal selection.
5. **Update AIBrain**: Wire the new coordinated logic into `_memory_appraisal_phase`.

## Affected Files
- `src/core/logic/routine_service.py`
- `src/ai/brain.py`
- `src/ai/goals/evaluator.py` (if place-based target selection is needed)

## Rollback Notes
- If AI becomes non-responsive, revert `RoutineService` changes to the biological-only baseline.
