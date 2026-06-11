---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260528-COG-PHASE5-BELIEF
phase: done
date: 2026-05-28
tags: [cog, phase5, belief]
---

# TCK-20260528-COG-PHASE5-BELIEF

## Title

Phase 5 — Information / Belief / Source-Trust Loop

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement Phase 5 - Information, Belief, and Source-Trust loop. Entities should handle uncertain information subjectively (routing queries, processing partial leads and rumors, detecting contradictions with direct observations, adapting source trust metrics gradually, and redirecting adventure route goals dynamically).

## Scope

- Create `src/domains/information/` module
- Define `InformationSourceProfile` scopes and properties
- Implement `InformationQueryRouter` filtering candidates by town, scope, trust, and cost
- Implement `InformationResponseNormalizer` converting raw responses to standard formats
- Implement `InformationAssimilationService` updating facts/unknowns with capacity limits
- Implement `BeliefContradictionService` checking claim matches vs observations
- Implement `SourceTrustUpdateService` adjusting trust slowly and clamped between 0 and 1
- Implement `ObservationBeliefBridge` translating world observations to high-certainty beliefs
- Connect assimilated facts and resolved blockers to Phase 3 Adventure Route scorer
- Implement `InformationIntentResolver` generating `ASK_INFORMATION` or `MOVE_TO` intents
- Integrate bounded `InformationBeliefPhase` behind a feature flag
- Add Event Tracing and diagnostic events
- Add Scenarios 5.1 to 5.6 and performance budget gates

## Out of Scope

- Full multi-agent gossip network propagation
- Deceptive economic networks
- Complex rumor spread models
- Long-term biography memory schemas

## Acceptance Criteria

- Common resource sources can be learned from guide queries
- Rare resources generate partial/approximate leads, not precise facts
- Contradicting or failed claims weaken certainty and decrease traveler/source trust gradually
- Direct observations override low-certainty rumors
- Two conflicting sources disagree without immediate absolute truth resolution
- Highly trusted sources are preferred during future routing queries
- Bounded memory limits and spatial sensory checks keep update overhead strictly <5ms

## Related Tickets

- TCK-20260528-COG-PHASE4-COMBAT (done)

## Related Docs

- entity_enhance_phase5.md

## Related Stored Artifacts

- None

## Related Code Areas

- src/core/state.py
- src/core/self_model.py
- src/core/strategic.py
- src/domains/adventure/
- src/domains/information/

## Assumptions / Open Questions

- Memory growth from facts/unknowns is bounded using standard capacity limits.
- Source trust entries represent slow, gradual modifiers clamped strictly inside [0.0, 1.0].

## Implementation Notes

Implemented subjective candidate routing, response standardizations, memory-bounded assimilation, direct observations bridges, contradiction checkers, gradual trust modifiers, and route scorers bridges under `src/domains/information/`.

## Test Summary

25 automated test cases fully covering primitive boundary, profiles, routers, normalizers, assimilations, contradictions, trust updates, observation bridges, route impact hints, intent resolvers, events, integration phase updates, scenarios, and performance budgets (<5ms for 100+ entities). All tests passed successfully.

## Files Changed

- `src/domains/information/schema.py`
- `src/domains/information/router.py`
- `src/domains/information/normalizer.py`
- `src/domains/information/assimilation.py`
- `src/domains/information/contradiction.py`
- `src/domains/information/trust.py`
- `src/domains/information/bridge.py`
- `src/domains/information/route_impact.py`
- `src/domains/information/resolver.py`
- `src/domains/information/phase.py`
- `tests/unit/domains/information/test_phase5_information_boundary.py`
- `tests/unit/domains/information/test_phase5_information_source_profile.py`
- `tests/unit/domains/information/test_phase5_information_query_router.py`
- `tests/unit/domains/information/test_phase5_information_response_normalizer.py`
- `tests/unit/domains/information/test_phase5_information_assimilation.py`
- `tests/unit/domains/information/test_phase5_belief_contradiction.py`
- `tests/unit/domains/information/test_phase5_source_trust_update.py`
- `tests/unit/domains/information/test_phase5_observation_belief_bridge.py`
- `tests/unit/domains/information/test_phase5_belief_route_impact.py`
- `tests/unit/domains/information/test_phase5_information_intent_resolver.py`
- `tests/unit/domains/information/test_phase5_information_events.py`
- `tests/integration/domains/information/test_phase5_information_belief_phase.py`
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py`
- `tests/perf/test_phase5_information_belief_budget.py`
- `docs/entity/entity_base.md`

## Completion Summary

Phase 5 - Information, Belief, and Source-Trust loop is successfully finished, fully verified under the 5ms gate budget, and completely passing all TDD automated test checkpoints.

