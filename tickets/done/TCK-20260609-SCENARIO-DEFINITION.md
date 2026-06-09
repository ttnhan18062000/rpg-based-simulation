# TCK-20260609-SCENARIO-DEFINITION

## Title
Define SimulationScenarioDefinition schema for scenario setup

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The simulation_scenarios/ directory currently lacks a clear schema separating setup data from observability or post-run analysis. SimulationScenarioDefinition creates that boundary: a typed schema that selects world composition, perspective, focus modules, and initial conditions from a fixed category set (region_pressure, faction_activity, resource_scarcity, population_alertness, territorial_intrusion, trade_route_risk, danger_level_override, spawn_bias). No executable scripts, no behavior-specific hardcoded actions — scenarios only configure starting world state and context.

## Scope
- Create `SimulationScenarioDefinition` as a Pydantic BaseModel with fields: id, display_name, world_composition, perspective, focus_modules, initial_conditions, setup_tags
- Restrict initial_conditions keys to the allowed category set; unknown keys must fail validation
- Add `tests/unit/scenarios/test_scenario_schema.py` testing: valid scenario loads, unknown fields fail closed, unknown initial_condition keys fail, observability/reporting fields are absent

## Out of Scope
- Implementing the resolver that consumes this schema (see TCK-20260609-SCENARIO-SETUP-RESOLVER)
- Loading YAML files from disk
- Defining perspectives (existing concept)

## Acceptance Criteria
- [ ] SimulationScenarioDefinition exists with all specified fields
- [ ] initial_conditions keys are validated against the allowed category set
- [ ] Unknown scenario-level fields fail validation
- [ ] Schema does not include observability, metrics, scoring, or telemetry fields
- [ ] Unit tests pass: valid scenario, unknown fields fail, unknown condition keys fail

## Related Tickets
- TCK-20260609-SCENARIO-SETUP-RESOLVER (successor — resolves this schema)

## Related Docs
- docs/mechanics/05_world_evolution.md
- docs/mechanics/06_worldbuilding_foundation.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/scenarios/schema.py (new)
- tests/unit/scenarios/test_scenario_schema.py (new)

## Assumptions / Open Questions
- Allowed initial_condition categories are fixed at: region_pressure, faction_activity, resource_scarcity, population_alertness, territorial_intrusion, trade_route_risk, danger_level_override, spawn_bias

## Implementation Notes
Created src/scenarios/ package with SimulationScenarioDefinition as a frozen Pydantic model with extra="forbid". Initial condition keys validated via model_validator against 8 allowed categories. No observability/reporting/metrics fields present.

## Test Summary
11 passed — tests/unit/scenarios/test_scenario_schema.py

## Files Changed
- src/scenarios/__init__.py (new)
- src/scenarios/schema.py (new)
- tests/unit/scenarios/__init__.py (new)
- tests/unit/scenarios/test_scenario_schema.py (new)

## Completion Summary
SimulationScenarioDefinition schema defined with fail-closed unknown fields and validated initial_condition category set. 11 tests pass.
