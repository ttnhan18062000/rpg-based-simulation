---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260529-COG-PHASE14-MOTIVATION
phase: done
date: 2026-05-29
tags: [cog, phase14, motivation]
---

# TCK-20260529-COG-PHASE14-MOTIVATION

## Title

Motivation, Identity Doctrine, and Role-Fit Domain Implementation

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement Phase 14 to prevent entities from converging on identical strategic route decisions by defining structured schemas (`IdentityDoctrine`, `ValuePreferenceProfile`, `RoleFitPreference`) and services (`DoctrineResolver`, `RoleFitEvaluator`, `MotivationBiasService`) that apply stable cognitive biases to route evaluations.

## Scope

- Define and refine `IdentityDoctrine`, `ValuePreferenceProfile`, and `RoleFitPreference` dataclass definitions in `src/core/cognition.py`.
- Implement `DoctrineResolver` yielding custom class preference profiles based on actor types (warrior, ranger, mage).
- Implement `RoleFitEvaluator` scoring weapon/armor slots and tactical role configurations.
- Implement `MotivationBiasService` acting as an adapter bias scoring layer for the strategic route selections.
- Implement unit, integration, and scenario tests under `tests/`.

## Out of Scope

- Dynamically changing doctrines or mutating structural value metrics after tick occurrences.

## Acceptance Criteria

- Motivation schemas fully implemented in `src/core/cognition.py`.
- `DoctrineResolver`, `RoleFitEvaluator`, and `MotivationBiasService` implemented and verified.
- Unit and scenario integration tests verify class routes and gear preference choices pass.

## Related Tickets

- `TCK-20260529-COG-PHASE11-HIERARCHY`
- `TCK-20260529-COG-PHASE12-PERCEPTION`
- `TCK-20260529-COG-PHASE13-MEMORY`

## Related Docs

- `docs/entity/entity_base.md`

## Related Code Areas

- `src/domains/motivation/` (created)
- `src/core/cognition.py`

## Test Summary

- 10 unit tests added verifying schemas, DoctrineResolver, RoleFitEvaluator, and MotivationBiasService.
- 1 scenario-driven integration test verifying custom class route preferences.
- All tests pass cleanly.

## Files Changed

- `src/domains/motivation/resolver.py`
- `src/domains/motivation/evaluator.py`
- `src/domains/motivation/service.py`
- `src/domains/motivation/__init__.py`
- `tests/unit/domains/motivation/test_phase14_motivation_models.py`
- `tests/unit/domains/motivation/test_phase14_doctrine_resolver.py`
- `tests/unit/domains/motivation/test_phase14_role_fit_evaluator.py`
- `tests/unit/domains/motivation/test_phase14_bias_service.py`
- `tests/integration/scenarios/test_phase14_motivation_doctrine_scenarios.py`
- `docs/entity/entity_base.md`

## Completion Summary

All Phase 14 motivation components, resolvers, and scorers have been fully implemented under `src/domains/motivation/` and verified with comprehensive unit and scenario-driven integration tests, which are passing cleanly with zero regressions.

