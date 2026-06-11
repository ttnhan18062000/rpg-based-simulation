---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260528-COG-PHASE3-DECISION
artifact_type: test_plan
tags: [cog, phase3, decision]
---

# Phase 3 Test Plan

## Unit Testing
We will add 7 specific unit test files under `tests/unit/domains/adventure/`:
1. `test_phase3_adventure_decision_boundary.py`: Verifies no adventure components exist in EntityState and the service runs with mocked aspects.
2. `test_phase3_route_families.py`: Verifies enum definitions, project mappings, and trace metadata.
3. `test_phase3_route_generator.py`: Verifies generator suggests expected routes (recover, buy_upgrade, craft_upgrade, earn_gold, ask_info, defer).
4. `test_phase3_route_scoring.py`: Verifies trait biases (bravery, greed, caution, curiosity, industry) and critical survival priorities.
5. `test_phase3_adventure_decision_service.py`: Verifies route selection, rejected reasons, and trace serialization.
6. `test_phase3_route_to_project_mapper.py`: Verifies deterministic mapping to `ProjectState` and `ObjectiveState`.
7. `test_phase3_objective_intent_resolver.py`: Verifies mapping of first objectives to executable `ActionIntent` payloads.

## Integration Testing
We will add 1 integration phase test:
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`: Verifies running cadence, skipped dead/active/stunned entities, feature flag toggles, and `StrategicUpdate` extraction.

## Scenario TDD Testing
We will add 1 scenario test:
- `tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py`:
  - **Scenario 3.1**: Poor + weak warrior earns gold (easy quest, harvesting) rather than buying impossible weapon.
  - **Scenario 3.2**: Known recipe + known material source leads to crafting/harvesting project.
  - **Scenario 3.3**: Recipe with unknown moon_resin source drives ask_information query, preserving information opacity.
  - **Scenario 3.4**: Critical low HP overrides upgrade desires and forces recover.
  - **Scenario 3.5**: Brave, cautious, and industrious archetypes select different valid routes for the same world scenario.

## Performance Timings Testing
- `tests/perf/test_phase3_adventure_decision_budget.py`: Verifies execution constraints for 10, 100, and 500 entities over ticks, validating dirty-check and active-project skipping.
