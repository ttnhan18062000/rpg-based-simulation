# TCK-20260528-COG-PHASE3-DECISION

## Title

Phase 3 — Adventure Decision Layer

## Status

INPROGRESS

## Request Summary

Implement the adventure decision layer. Entities should choose an explainable route family based on self-model status and world opportunities, mapping that choice to a strategic project/objective and resolving the first intent.

## Scope

- Create `src/domains/adventure/` module
- Implemented `AdventureRouteOption`, `AdventureDecisionResult`, and `RejectedRoute` schemas
- Implemented `AdventureRouteGenerator` to suggest candidate routes
- Implemented Imperfect Decision Scoring with Personality Traits bias
- Implemented `AdventureDecisionService` to evaluate and select the best candidate route
- Implemented Route-to-Strategic-Project mapper
- Implemented `ObjectiveIntentResolver` to translate objectives to first action intents
- Implemented `AdventureDecisionPhase` and integrated it with Cadence-guided execution
- Created Unit, Integration, Scenario, and Performance test files
- Updated `docs/entity/entity_base.md` and aspect diagram

## Out of Scope

- Combat engagement cognition (Phase 4)
- Multi-day campaign routing lifecycle
- Coordinated party routing
- Deep rumor contradiction

## Acceptance Criteria

- Poor and weak entity does not buy unaffordable equipment
- Unknown material source correctly creates ask_information or scout route
- Low HP critical state overrides growth routes and forces recovery
- Known recipes create craft routes
- Bravery, caution, industry, curiosity, sociability, and greed traits dynamically alter route ranking
- Decision phase is highly bounded and stays well within budgets for 100+ entities
- Strategic baseline remains completely stable (166+ strategic tests pass)

## Related Tickets

- TCK-20260527-COG-PHASE2-SELFMODEL (done)

## Related Docs

- entity_enhance_phase3.md
- docs/entity/entity_base.md

## Related Stored Artifacts

- stored_artifacts/TCK-20260527-COG-PHASE2-SELFMODEL/

## Related Code Areas

- src/core/state.py
- src/core/self_model.py
- src/cognition/
- src/domains/adventure/

## Assumptions / Open Questions

- Route families are high-level strategies (recover, buy_upgrade, craft_upgrade, train_skill, take_easy_quest, hunt_weak_enemy, gather_resource, sell_loot_for_gold, ask_information, scout_location, form_party, return_town, defer_with_reason).
- No new fields added to `EntityState` itself; all decisions consume existing generic aspects.
- Impairment and death prevent decision updates.

## Implementation Notes

- Designed and implemented clean domain-driven architecture under `src/domains/adventure/` package.
- Built a typeguard-compliant mapper resolving subjective routing families to standard `StrategicComponent` projects and objectives.
- Resolved Personality component trait extraction with robust fallback normalisation to preserve absolute data isolation and opaque decisions.
- Created `ObjectiveIntentResolver` providing an optimized strategic-to-adapted `ActionIntent` bridge.
- Unified routing decisions with Cadence-controlled execution loop in `AdventureDecisionPhase` and verified locks.

## Test Summary

- Fully passing unit, integration, scenario, and performance budget tests.
- Total of 33 tests executed and validated across the entire module.
- Strategic baseline remains completely stable with 166/166 strategic tests passing.

## Files Changed

- `src/domains/adventure/scoring.py`
- `src/domains/adventure/service.py`
- `src/domains/adventure/resolver.py`
- `src/domains/adventure/phase.py`
- `tests/unit/domains/adventure/test_phase3_route_scoring.py`
- `tests/unit/domains/adventure/test_phase3_adventure_decision_service.py`
- `tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py`
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`
- `tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py`
- `tests/perf/test_phase3_adventure_decision_budget.py`
- `docs/entity/entity_base.md`
- `docs/entity/entity_aspect_relationship_diagram.mmd`

## Completion Summary

Phase 3 is 100% complete and fully verified. Adventurers now successfully construct and execute explainable, personality-biased strategic routing projects based strictly on subjective self-model needs and opportunities, completely decoupled from combat or quests generation.

