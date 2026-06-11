---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260410-PH5-STRATEGIC-CONSEQUENCES
phase: done
date: 2026-04-10
tags: [ph5, strategic, consequences]
---

# TCK-20260410-PH5-STRATEGIC-CONSEQUENCES

## Title

Event-Driven Reprioritization and Durable Consequences

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Phase 5: Transform the existing consequence substrate—interpreted life events, turning points, and regional scars—into actionable strategic pressure. Shift from emotional theater to durable behavioral mutation.

## Scope

- Create `StrategicConsequenceService` to coordinate strategic shifts from events.
- Implement `ConcernGenerationService` for event-driven interrupts (e.g., Ally Death -> Retreat).
- Implement `DirectiveMutationService` for turning-point to directive transformation.
- Implement `PlaceAppraisalService` for location-based threat appraisal (using scars/danger).
- Upgrade Project Interruption logic to support SUSPENDED, ABANDONED, and MUTATED states.
- Integrate world scars and regional consequences into strategic appraisal.
- Ensure private narrative shifts stay private.

## Out of Scope

- New economic systems.
- Advanced faction AI (Reserved for Phase 6).
- Changes to raw combat mechanics.

## Acceptance Criteria

- [x] `StrategicConsequenceService` correctly translates `InterpretedLifeEvent` into `StrategicUpdate`.
- [x] Major turning points (e.g., "Near Death") generate high-priority "Survival" concerns.
- [x] Turning points can mutate long-term entity directives.
- [x] Project switching correctly suspends or abandons projects based on interruption policy.
- [x] Entities respond strategically to regional scars (e.g., avoiding recent battlefields).
- [x] Integration tests validate end-to-end consequence propagation.

## Related Tickets

- TCK-20260410-PH4-SOCIAL-CONTRACTS (Done)

## Related Docs

- thinking_implementation_phase_5.md

## Related Code Areas

- `src/core/logic/social_state_applicator.py`
- `src/ai/strategy/interruption.py`
- `src/ai/brain.py`
- `src/systems/world/regional_consequence_system.py`

## Assumptions / Open Questions

- We assume existing interpretation kindnesses (NEAR_DEATH, etc.) are sufficient for initial testing.
- We assume `interruption_policy` "default" allows for project suspension.

## Implementation Notes

- Use `StrategicUpdate` for all strategic state mutations to maintain AOA purity.
- Chaining: Action -> Interpreter -> SocialApplicator -> StrategicConsequenceService -> State Mutation.
## Test Summary

- New integration test suite: `tests/integration/strategy/test_strategic_consequences.py`
- Verified: NEAR_DEATH concern generation, Project suspension, Directive mutation, Home-defense appraisal.

## Files Changed

- `src/core/models/strategy.py`
- `src/core/logic/strategic_consequence_service.py`
- `src/core/logic/concern_generation.py`
- `src/core/logic/directive_mutation_service.py`
- `src/core/logic/place_threat_appraisal.py`
- `src/core/logic/project_mutation_service.py`
- `src/core/logic/world_consequence_interpretation.py`
- `src/core/logic/social_state_applicator.py`
- `src/ai/strategy/strategic_evaluator.py`
- `src/ai/brain.py`
- `src/ui/cli/inspector.py`

## Completion Summary

- Implemented `StrategicConsequenceService` to translate narrated life events into strategic state mutations.
- Upgraded `ProjectRecord` and `ConcernRecord` with Phase 5 fields for history-sensitive recovery and detailed semantics.
- Integrated `DirectiveMutationService` for identity shifts from salient turning points.
- Integrated `PlaceThreatAppraisalService` for attachment-aware concern generation during regional trauma.
- Upgraded `StrategicEvaluator` to handle formal project suspension and interruption tracking.
- Integrated `WorldConsequenceInterpretationService` into `AIBrain` for environmental strategic pressure based on world scars.
- Verified all systems with a new integration test suite `test_strategic_consequences.py`.
