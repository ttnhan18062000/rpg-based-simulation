---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260528-COG-PHASE4-COMBAT
phase: done
date: 2026-05-28
tags: [cog, phase4, combat]
---

# TCK-20260528-COG-PHASE4-COMBAT

## Title

Phase 4 — Combat Engagement Cognition

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement Phase 4 - Combat Engagement Cognition. Entities should evaluate potential opponents subjectively, choose dynamic combat postures (such as PROBE, AVOID, retreat, etc.), apply Personality traits, learn from losses, and adapt future behaviors dynamically.

## Scope

- Create `src/domains/combat_engagement/` module
- Implement canonical combat postures (`IGNORE`, `WATCH`, `AVOID`, `PROBE`, `THREATEN`, `ENGAGE`, `SKIRMISH`, `CALL_HELP`, `RETREAT`, `PANIC_FLEE`, `GUARD_ALLY`, `VENGEANCE_ENGAGE`)
- Implement `OpponentPerceptionService` to subjectively evaluate targets
- Implement `SelfCombatEstimateService` to evaluate current condition
- Implement `EngagementRiskEvaluator` combining wins confidence, death risks, objective pressure, and personality biases
- Implement `CombatPostureSelector` to choose optimal posture
- Implement Posture-to-Intent bridge
- Implement `CombatReassessmentService` for dynamic mid-combat changes (HP drops, visible skill reveals)
- Implement `CombatLearning` updating generalized and specific memory opponent models
- Integrate posture mapping into `CombatEngagementPhase` using sensory range checks
- Create Unit, Integration, Scenario, and Performance gate test files
- Update diagrams and docs

## Out of Scope

- Rewriting combat damage resolvers or legality checks
- Coordinated party combat maneuvers
- Advanced rumor systems
- Full biographical narration

## Acceptance Criteria

- Unknown equal target does not trigger immediate attack
- Cautious and brave entities select divergent traceable postures under identical parameters
- Active quest/objective pressure raises victory tolerance and justifies risk
- Lost combat updates generalized and specific memory, altering future perceived estimates and choices
- Hidden skill revealed mid-combat causes dynamic retreat/skirmish reassessment
- Badly wounded monster retreats or flees (self-preservation)
- Overhead stays highly bounded under 100+ entities (<5ms)
- Strategic baseline remains completely stable

## Related Tickets

- TCK-20260528-COG-PHASE3-DECISION (done)

## Related Docs

- entity_enhance_phase4.md

## Related Stored Artifacts

- None

## Related Code Areas

- src/core/state.py
- src/core/self_model.py
- src/domains/combat_engagement/
- src/engine/

## Assumptions / Open Questions

- Opponent model capacity and sensory ranges are capped to prevent memory leak and performance bottleneck.
- Memory structures reside in existing entity strategic components or identity properties rather than introducing new heavy schemas to EntityState.

## Implementation Notes

Implemented subjective opponent perception, self capability estimates, risk evaluation, selector mappings to postures, posture-to-intent bridging, mid-combat reassessment, and capacity-limited learning models under `src/domains/combat_engagement/`.

## Test Summary

36 automated test cases fully covering boundary behavior, enums, perception estimates, self estimates, risk evaluation, selectors, intent resolver, reassessments, learning updates, events, visibility phase updates, scenarios, and performance budgets (<5ms for 100+ entities). All tests passed successfully.

## Files Changed

- `src/domains/combat_engagement/schema.py`
- `src/domains/combat_engagement/perception.py`
- `src/domains/combat_engagement/self_estimate.py`
- `src/domains/combat_engagement/risk_evaluator.py`
- `src/domains/combat_engagement/selector.py`
- `src/domains/combat_engagement/resolver.py`
- `src/domains/combat_engagement/reassessment.py`
- `src/domains/combat_engagement/learning.py`
- `src/domains/combat_engagement/phase.py`
- `tests/unit/domains/combat_engagement/test_phase4_combat_engagement_boundary.py`
- `tests/unit/domains/combat_engagement/test_phase4_combat_postures.py`
- `tests/unit/domains/combat_engagement/test_phase4_opponent_perception.py`
- `tests/unit/domains/combat_engagement/test_phase4_self_combat_estimate.py`
- `tests/unit/domains/combat_engagement/test_phase4_engagement_risk.py`
- `tests/unit/domains/combat_engagement/test_phase4_posture_selector.py`
- `tests/unit/domains/combat_engagement/test_phase4_posture_to_intent.py`
- `tests/unit/domains/combat_engagement/test_phase4_combat_reassessment.py`
- `tests/unit/domains/combat_engagement/test_phase4_combat_learning.py`
- `tests/unit/domains/combat_engagement/test_phase4_combat_engagement_events.py`
- `tests/integration/domains/combat_engagement/test_phase4_combat_engagement_phase.py`
- `tests/integration/scenarios/test_phase4_combat_engagement_scenarios.py`
- `tests/perf/test_phase4_combat_engagement_budget.py`
- `docs/entity/entity_base.md`

## Completion Summary

Phase 4 Combat Engagement Cognition is successfully finished, verified with high-performance metrics under budget restrictions, and completely passing all unit and scenario test gates.
