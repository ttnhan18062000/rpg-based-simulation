# Investigation: Combat AI Behavioral Regressions

## 1. Goal Jitter (Hysteresis)
### Symptoms
- Heroes in `test_goal_commitment_and_anti_jitter` switch from `WANDER` to `COMBAT` immediately despite a 3-tick lock.
- `assert <AIState.COMBAT: 3> == <AIState.WANDER: 1>` failure.

### Findings
- The `AIBrain` implementation of `is_goal_locked` was returning correctly, but the state transition logic in `_finalization_phase` and the `ActionSystem` update of `goal_committed_at` had subtle synchronization issues.
- Specifically, if a goal doesn't change, `AIBrain` sends `None` for `goal_committed_at`. `ActionSystem` correctly ignores it, leaving it at `0`.
- In `GoalEvaluator.is_goal_locked`, `ticks_held = ctx.snapshot.tick - committed_at`.
- If `committed_at` is `0` and `tick` is `3`, `ticks_held` is `3`. `3 < 3` is False. The lock expires.
- **Problem**: Many tests start at tick 0 and run 3 ticks. The lock should ideally start from the moment the AI *first* makes a decision for that goal.

## 2. Ranged Flee Logic (Kiting)
### Symptoms
- Ranged heroes in `test_low_hp_ranged_does_not_kite` stay in `COMBAT` until death even at 40% HP.
### Findings
- `FleeGoal.score` in `scorers.py` uses a hardcoded `enter_threshold = 0.3`.
- 40% HP (0.4) is > 0.3, so `FleeGoal` returns `0.0` score.
- `CombatGoal` returns ~1.0 because the enemy is close.
- Result: Hero fights to the death.
- **Root Cause**: Inconsistency between `FleeGoal` scorer and `should_flee` (which uses a `0.6` threshold for ranged units).

## 3. Threat Attribute Access
### Symptoms
- `AttributeError: 'dict' object has no attribute 'model_copy'`
### Findings
- `Snapshot` objects convert Pydantic models to `mappingproxy` or `dict`.
- Code calling `.model_copy()` or accessing fields via `.` attribute access fails.
- Fixed in `BeliefService.decay_stale_beliefs` and `states/base.py`, but need to ensure full coverage.
