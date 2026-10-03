---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E12C-BALANCE-TESTS
phase: done
date: 2026-06-20
tags: [balance, testing, regression, integration, phase-1]
---

# TCK-20260619-E12C-BALANCE-TESTS

## Title
Epic 1.2C · Balance Regression Test Suite

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Lock E12A-measured balance ratios into a CI regression suite. Closes D04 audit and completes Epic 1.2.

## Scope
- Created `tests/integration/scenarios/test_balance_regression.py` with 4 tests:
  1. `test_combat_attrition_urban_in_band` — attrition < 60% at tick 100 (E12A: 46.7%)
  2. `test_adventure_routing_defaults_off` — ENABLE_ADVENTURE_ROUTING defaults to OFF
  3. `test_blocker_penalty_not_near_binary` — skipped (E12B decision, revisit trigger documented)
  4. `test_scoring_formula_constants_stable` — confidence_bonus/personality_bias/blocker_penalty constants verified
- Promoted `docs/audits/D04_balance_tuning.md` status from `partial` to `done`

## Out of Scope
- Personality or combat constants (those have separate test suites)
- Faction-level metrics

## Acceptance Criteria
- [x] `tests/integration/scenarios/test_balance_regression.py` exists and all 4 tests pass (3 pass, 1 skipped per E12B)
- [x] `docs/audits/D04_balance_tuning.md` status = `done`
- [x] Threshold constants reference E12A measurements (not guesses)

## Related Tickets
- TCK-20260619-E12A-BALANCE-MEASURE (prerequisite — DONE)
- TCK-20260619-E12B-BLOCKER-RECAL (prerequisite — DONE)
- TCK-20260619-E12-BALANCE-BASELINE (parent epic — now complete)

## Related Docs
- `docs/audits/D04_balance_tuning.md` (promoted to done)
- `docs/mechanics/04_strategic_cognition.md` §6 (scoring constants referenced)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E12C-BALANCE-TESTS/` (plan, investigation, test_plan)

## Related Code Areas
- `tests/integration/scenarios/test_balance_regression.py` (new)
- `src/domains/adventure/scoring.py` (constants verified)
- `src/domains/optimization/feature_flags.py` (ENABLE_ADVENTURE_ROUTING default)

## Assumptions / Open Questions
- Test 3 skipped: blocker_penalty behavior is unobservable until urban_political has resource nodes. Revisit trigger in D04 §7 and scoring chapter §6.5.

## Implementation Notes
Thread leak fix required: call `kernel.shutdown()` after ticks in the integration test. `FeatureFlagManager` has no module-level `FEATURE_FLAGS` dict; must instantiate `FeatureFlagManager()` to read defaults.

## Test Summary
```
3 passed, 1 skipped in 52.17s
test_combat_attrition_urban_in_band     PASSED
test_adventure_routing_defaults_off     PASSED
test_blocker_penalty_not_near_binary    SKIPPED (E12B: keep 2.0)
test_scoring_formula_constants_stable   PASSED
```

## Files Changed
- `tests/integration/scenarios/test_balance_regression.py` — new (4 regression tests)
- `docs/audits/D04_balance_tuning.md` — status promoted to `done`

## Completion Summary
E12C complete. Balance regression suite locked. D04 promoted to done. Epic 1.2 (E12-BALANCE-BASELINE) is now fully complete with all 3 child tickets DONE.
