---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E12C-BALANCE-TESTS
phase: open
date: 2026-06-20
tags: [balance, testing, regression, integration, phase-1]
---

# TCK-20260619-E12C-BALANCE-TESTS

## Title
Epic 1.2C · Balance Regression Test Suite

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Lock empirically-measured balance ratios (from E12A) into a CI regression test suite so future changes that break economic or combat balance are caught automatically. This closes the D04 audit and fulfills the E12 epic's primary acceptance criterion.

**Depends on:** TCK-20260619-E12A-BALANCE-MEASURE (for measured threshold values) + TCK-20260619-E12B-BLOCKER-RECAL (for final scoring constants)

## Scope
- Create `tests/integration/scenarios/test_balance_regression.py` with 4 tests:
  1. `test_harvesting_rate_in_band` — assert `LOW < harvesting_events/entity/100ticks < HIGH` (thresholds from E12A)
  2. `test_combat_attrition_urban_in_band` — assert combat attrition < 60% at tick 1000
  3. `test_blocker_penalty_not_near_binary` — assert minor-blocked high-urgency route outscores mediocre unblocked route (skip if E12B kept penalty=2.0)
  4. `test_gold_accumulation_non_zero` — assert ≥1 entity has gold > 0 by tick 1000
- All tests: seed=42, `urban_political`, tick_limit=1000
- Mark `@pytest.mark.slow` + `@pytest.mark.integration`
- Promote `docs/audits/D04_balance_tuning.md` status field from `partial` to `done`
- Run `make knowledge-index-update`

## Out of Scope
- Personality or combat constants (those have separate test suites)
- Faction-level metrics

## Acceptance Criteria
- `tests/integration/scenarios/test_balance_regression.py` exists and all 4 tests pass
- `docs/audits/D04_balance_tuning.md` status = `done`
- Threshold constants at the top of the test file reference E12A measurements (not guesses)

## Related Tickets
- TCK-20260619-E12A-BALANCE-MEASURE (prerequisite — must be DONE; provides threshold values)
- TCK-20260619-E12B-BLOCKER-RECAL (prerequisite — must be DONE; provides final constants)
- TCK-20260619-E12-BALANCE-BASELINE (parent epic — completes when this ticket is DONE)

## Related Docs
- `docs/audits/D04_balance_tuning.md` (promote to done)
- `docs/testing/v2_test_taxonomy.md` (integration/slow markers)

## Related Code Areas
- `tests/integration/scenarios/` (new file here)
- `src/observability/reporting/metric_recorder.py` (metric collection used in tests)

## Assumptions / Open Questions
- What's the fastest way to extract per-entity per-100-tick harvesting rate from a simulation run? Check if `metric_recorder.py` or `BalanceDiagnosisEngine` already surfaces this.
- Does `tests/integration/scenarios/` directory already exist? If not, create with `__init__.py`.

## Implementation Notes
Threshold constants should be named and declared at the top of the test file:
```python
# Thresholds measured from E12A: seed=42, urban_political, 1000 ticks
HARVESTING_RATE_LOW = 0.05   # per entity per 100 ticks (replace with E12A value)
HARVESTING_RATE_HIGH = 0.80  # (replace with E12A value)
ATTRITION_CAP = 0.60
```
These should be filled in from E12A data, not guessed.

## Test Summary
All 4 tests in `tests/integration/scenarios/test_balance_regression.py`.
Run: `pytest tests/integration/scenarios/test_balance_regression.py -v --timeout=180`

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
