# TCK-20260414-STRAT-HARDENING

## Title
Strategic Cognition & Intel Capacity Hardening

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Harden strategic cognition pipeline by implementing richer capacity derivation and robust infrastructure isolation.

## Scope

- [x] Integrate internal stressors (HP, hunger, panic) into cognitive capacity derivation.
- [x] Implement cognitive overload observability in strategic artifacts.
- [x] Verify system resilience via infrastructure isolation tests (RabbitMQ/Kafka fallback).
- [x] Enhance strategic decision explainability with detailed switch reasons.

## Out of Scope

- Modifying the core strategic scoring algorithms (Priority: Derivation/Resilience).
- Implementing new frontend visualizations (Focus: Engine/Model integrity).

## Acceptance Criteria

- [x] Cognition capacity correctly penalized by low HP, high hunger, or panic.
- [x] Strategic updates contain `is_overloaded`, `overload_score`, and `primary_overload_source`.
- [x] Simulation runs correctly with `DISABLE_RABBITMQ=1` and `DISABLE_KAFKA=1`.
- [x] No regressions in strategic continuity and intel capacity replay suites.

## Related Tickets

- None

## Related Docs
- `strategy_implementation_updated_v2.md`
- `intel_capacity_implementation_updated.md`

## Implementation Notes
- Strategic continuity is sensitive to `judgment_stability` in the capacity profile.
- Mismatch between `StrategicEvaluator.evaluate` and `ObjectiveDerivationService.apply_derivation` identified and needs address in `brain.py`.

## Test Summary
- `pytest tests/integration/strategy/test_strategic_continuity_hardening.py` (PASSED)

## Files Changed
- `tests/integration/strategy/test_strategic_continuity_hardening.py`

## Completion Summary
TBD
