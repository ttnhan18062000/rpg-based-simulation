# TCK-20260529-COG-PHASE15-COMMITMENT

## Title

Commitment, Obligation, and Reputation Domain Implementation

## Status

DONE

## Request Summary

Implement Phase 15 to make promises, contracts, accepted quests, party duties, and public reputation affect future behavior, preventing immediate greedy route switches and establishing clear social consequences for betrayal.

## Scope

- Implement `CommitmentPressureService` computing pressure to hold active commitments.
- Implement `AbandonmentEvaluator` distinguishing valid survival from greedy betrayal.
- Implement `ReputationUpdateService` updating public labels.
- Implement `CommitmentReputationRouteImpact` applying route score boosts and partner fit penalties.
- Implement unit, integration, and scenario tests under `tests/`.

## Out of Scope

- Dynamically triggering or mutating other components of social contracts outside explicit update phases.

## Acceptance Criteria

- Commitments prevent immediate greedy route switches unless survival is threatened.
- Abandonment has explainable reputation and trust consequences.
- All unit and scenario integration tests verify these requirements and pass cleanly.

## Related Tickets

- `TCK-20260529-COG-PHASE14-MOTIVATION`

## Related Docs

- `docs/entity/entity_base.md`

## Related Code Areas

- `src/domains/commitment/` (created)

## Test Summary

- 4 unit tests verifying services.
- 2 integration scenario tests verifying route commitment priority and betrayal partner penalties.
- All tests pass cleanly.

## Files Changed

- `src/domains/commitment/pressure.py`
- `src/domains/commitment/abandonment.py`
- `src/domains/commitment/reputation.py`
- `src/domains/commitment/impact.py`
- `src/domains/commitment/__init__.py`
- `tests/unit/domains/commitment/test_phase15_commitment_pressure.py`
- `tests/unit/domains/commitment/test_phase15_abandonment_evaluator.py`
- `tests/unit/domains/commitment/test_phase15_reputation_update.py`
- `tests/unit/domains/commitment/test_phase15_route_impact.py`
- `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`
- `docs/entity/entity_base.md`

## Completion Summary

All Phase 15 commitment, abandonment, and reputation services have been fully implemented under `src/domains/commitment/` and verified with comprehensive unit and scenario-driven integration tests, passing cleanly with zero regressions.
