# TCK-20260418-STRAT-LEARNING-REGRESSION

## Title
Resolve Strategic Learning Regression

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Resolved a persistence regression where LeadRecord flags (tested, is_exhausted) were incorrectly reverted during simulation ticks.

## Scope
- [x] Consolidate updates in `navigation.py`
- [x] Harden `StrategicState.apply_update` in `strategy.py`
- [x] Verify fix with regression tests
- [x] Cleanup diagnostic code and artifacts

## Out of Scope
- Rebuilding the entire state merging logic in `base.py` (found redundant and problematic).

## Acceptance Criteria
- [x] LeadRecord flags are monotonic (cannot revert to False).
- [x] Multiple updates in the same tick are consolidated correctly.
- [x] 100% pass rate on `tests/ai/test_learning_social.py::test_intel_refutation_by_exhaustion`.

## Related Tickets
- TCK-20260418-COMBAT-MOVEMENT-CORRECTION (related overhaul)

## Related Docs
- [overhaul_spec.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/overhaul_spec.md)

## Related Stored Artifacts
- [walkthrough.md](file:///home/vboxuser/Work/rpg-based-simulation/stored_artifacts/TCK-20260418-STRAT-LEARNING-REGRESSION/walkthrough.md)
- [plan.md](file:///home/vboxuser/Work/rpg-based-simulation/stored_artifacts/TCK-20260418-STRAT-LEARNING-REGRESSION/plan.md)

## Related Code Areas
- `src/ai/states/navigation.py`
- `src/core/models/strategy.py`

## Implementation Notes
- Hardening logic in `strategy.py` ensures that once `tested` or `is_exhausted` is True, it stays True regardless of subsequent stale updates.
- Consolidated update generation in `navigation.py` prevents redundant merges and potential state loss during action selection.

## Test Summary
- `pytest tests/ai/test_learning_social.py -k test_intel_refutation_by_exhaustion` (PASSED)
- Full AI test suite (78 tests PASSED)

## Files Changed
- `src/ai/states/navigation.py`
- `src/core/models/strategy.py`

## Completion Summary
Strategic learning persistence has been restored and hardened against stale state updates. The fix uses monotonic flag protection at the model layer and update consolidation at the navigation layer, ensuring reliable tracking of intelligence refutation and lead exhaustion.
