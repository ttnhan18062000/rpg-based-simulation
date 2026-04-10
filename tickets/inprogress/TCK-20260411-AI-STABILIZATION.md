# TCK-20260411-AI-STABILIZATION

## Title
Stabilizing Combat AI Decision Loop & Behavioral Resilience

## Status
INPROGRESS

## Request Summary
Resolve remaining E2E combat failures and harden AI decision logic against state jitter and behavioral regressions.

## Scope
- [x] Fix `AttributeError` in `BeliefService` (Defensive coercion)
- [x] Harden Redis connection in `ActionSystem` and `PersistencePhase`
- [ ] Unify `FleeGoal` scorer with `should_flee` tactical heuristic
- [ ] Fix Hysteresis state lock in `AIBrain` and `GoalEvaluator`
- [ ] Ensure `goal_committed_at` persistence across all decision paths
- [ ] Strengthen nemesis fear bias and tactical flee thresholds (Ranged: 60%, Melee: 30%)
- [ ] Remove all remaining unauthorized `print` statements in test suite

## Out of Scope
- Refactoring the entire `GoalEvaluator` architecture
- Implementing new AI states or goals beyond fixing current regressions

## Acceptance Criteria
- [ ] 100% pass rate for `tests/e2e/test_combat_arena_e2e.py`
- [ ] 100% pass rate for `tests/component/systems/test_calamity_system.py`
- [ ] No `AttributeError` or `RuntimeError` during long-running combat simulations
- [ ] Zero unauthorized debug prints in JSON-compliant logs

## Related Tickets
- TCK-20260411-CORE-STABILIZATION (Previous phase)

## Related Docs
- docs/architecture.md (AOA Pillars)

## Implementation Notes
- **Hysteresis**: Use `ctx.snapshot.tick` to update `goal_committed_at` only when a goal *changes*.
- **Tactical Thresholds**: Ranged units (Ranger/Mage) will use a `0.6` threshold for `FleeGoal` to satisfy kiting regressions.
- **Defensive Access**: Continue using `hasattr` or `.get()` for threat fields as snapshots freeze models into `mappingproxy`.

## Test Summary
- Run `pytest tests/e2e/test_combat_arena_e2e.py`
- Run `pytest tests/unit/ai/`

## Files Changed
- [MODIFY] [brain.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/brain.py)
- [MODIFY] [base.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/goals/base.py)
- [MODIFY] [scorers.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/goals/scorers.py)
- [MODIFY] [base.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/states/base.py)
