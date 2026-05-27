# Plan: Phase 4 — Combat Engagement Cognition

This document outlines the detailed architecture and implementation sequence for the Phase 4 Combat Engagement Cognition layer.

## Proposed Changes

### Component: `src/domains/combat_engagement`

We will create a modular combat engagement domain keeping simulation logic authoritative and decision logic subjective.

#### [NEW] `schema.py`
- Define `CombatPosture` enum: `IGNORE`, `WATCH`, `AVOID`, `PROBE`, `THREATEN`, `ENGAGE`, `SKIRMISH`, `CALL_HELP`, `RETREAT`, `PANIC_FLEE`, `GUARD_ALLY`, `VENGEANCE_ENGAGE`
- Define `PerceivedOpponentEstimate` schema
- Define `SelfCombatEstimate` schema
- Define `EngagementRiskEvaluation` schema
- Define `OpponentModel` memory model

#### [NEW] `perception.py`
- Implement `OpponentPerceptionService` to calculate estimated power based on target's level, equipment, faction, and prior memories, with uncertainty penalties from low perception or high panic/stress.

#### [NEW] `self_estimate.py`
- Implement `SelfCombatEstimateService` returning derived combat power adjusted for current HP, wounds, stamina, and weapon durability.

#### [NEW] `risk_evaluator.py`
- Implement `EngagementRiskEvaluator` calculating risk vs benefit score leveraging victory confidence, death risks, objective quest pressure, and personality trait biases.

#### [NEW] `selector.py`
- Implement `CombatPostureSelector` mapping risk-benefit profile to a posture, and bridge to strategic/tactical `ActionIntent` triggers.

#### [NEW] `reassessment.py`
- Implement `CombatReassessmentService` evaluating mid-combat updates (HP drops, visible skill updates) to dynamically trigger retreat or skirmishing.

#### [NEW] `learning.py`
- Implement `CombatLearning` updates after combat results, storing memory models to guide future encounters.

#### [NEW] `phase.py`
- Implement `CombatEngagementPhase` integrating trigger conditions (hostile enters sensory range, attacked) with decision logic under strict execution limits.

## Verification Plan

### Automated Tests
We will add 13 TDD unit, integration, scenario, and performance budget tests matching all criteria in the spec:
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
