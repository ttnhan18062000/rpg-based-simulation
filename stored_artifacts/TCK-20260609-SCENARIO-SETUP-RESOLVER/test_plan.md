---
ticket: TCK-20260609-SCENARIO-SETUP-RESOLVER
phase: test_plan
---

# Test Plan

## Integration tests — `tests/integration/scenarios/test_scenario_setup_resolver.py`

All tests use `scope="module"` fixtures for CatalogRepository + WorldModuleRepository.
Composition: `frontier_living_world`; perspective: `hero_guild_perspective`.

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_resolver_produces_resolved_setup` | Returns `ResolvedScenarioSetup` with correct `scenario_id` |
| 2 | `test_perspective_preserved_in_output` | `perspective_id == "hero_guild_perspective"` |
| 3 | `test_initial_conditions_become_modifiers` | Dict entry → `StateSetupModifier` with matching `modifier_type` + `parameters` |
| 4 | `test_invalid_composition_fails_with_scenario_id` | `ValueError` message contains `scenario.id` |
| 5 | `test_invalid_perspective_fails_with_scenario_id` | `ValueError` message contains `scenario.id` |
| 6 | `test_empty_initial_conditions_produces_no_modifiers` | Modifiers list is empty |
| 7 | `test_resolver_does_not_import_observability` | AST check: no observability/reporting import |
