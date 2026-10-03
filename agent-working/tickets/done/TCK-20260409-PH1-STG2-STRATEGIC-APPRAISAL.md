---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260409-PH1-STG2-STRATEGIC-APPRAISAL
phase: done
date: 2026-04-09
tags: [ph1, stg2, strategic, appraisal]
---

# Ticket TCK-20260409-PH2-STRATEGIC-APPRAISAL

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement Phase 2: Strategic Appraisal & Project Selection. This involves the cognitive logic that bridges the gap between raw biological needs (Concerns) and high-level directives, resulting in a durable "Project" commitment that biases tactical utility scoring.

## Scope
- Implement `StrategicEvaluatorService` for project selection and interruption logic.
- Integrate biological needs (Hunger/Energy) as authoritative Strategic Concerns.
- Insert `_strategic_appraisal_phase` into `AIBrain`.
- Map Strategic Objectives to tactical GoalType multipliers (Goal Biasing).
- Update CLI inspector for strategic explainability.
- Establish regression test suite for strategic commitment.

## Out of Scope
- Faction-level coordination (Phase 3).
- Social contract negotiations (Phase 4).

## Acceptance Criteria
- AI entities correctly prioritize survival (EAT/SLEEP) when Concerns are salient.
- Tactical goals are correctly biased by the active strategic objective.
- Strategic state changes are visible and explained in the CLI inspector.
- `tests/ai/test_strategic_biasing.py` passes.

## Related Tickets
- TCK-20260409-PH1-STG1-STRATEGIC-STATE (DONE)

## Related Docs
- thinking_high_level_implementation.md
- thinking_implementation_phase_1.md (actually covers Phase 1-3)

## Current Status
DONE (2026-04-10)

## Implementation Summary
- Implemented `StrategicEvaluatorService` for the pre-tactical cognitive pass.
- Linked `RoutineState` (Hunger/Sleep) to `StrategicState.concerns`.
- Implemented `AIBrain._strategic_appraisal_phase` for authoritative project selection.
- Added Strategic Objective biasing in `GoalEvaluator`.
- Verified deterministic logic in `tests/ai/test_strategic_biasing.py`.
