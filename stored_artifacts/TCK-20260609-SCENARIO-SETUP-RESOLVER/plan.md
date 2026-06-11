---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260609-SCENARIO-SETUP-RESOLVER
artifact_type: plan
tags: [scenario, setup, resolver]
---


# Plan

## New files

- `src/scenarios/resolver.py` — `StateSetupModifier`, `ResolvedScenarioSetup`, `ScenarioSetupResolver`
- `tests/integration/scenarios/test_scenario_setup_resolver.py` — 5+ integration tests

## `StateSetupModifier`

Frozen Pydantic model: `modifier_type: str`, `parameters: Dict[str, Any]`.

## `ResolvedScenarioSetup`

Frozen Pydantic model (`arbitrary_types_allowed=True`): `scenario_id`, `world_bundle`,
`perspective_id`, `initial_relation_context`, `initial_state_modifiers`.

## `ScenarioSetupResolver`

```
__init__(catalog, module_repo, compositions_dir=None)
resolve(scenario) -> ResolvedScenarioSetup
  _load_composition(scenario) -> WorldCompositionSpec
  _validate_perspective(scenario, composition)
  _build_modifiers(initial_conditions) -> List[StateSetupModifier]
```

Error messages always include `[scenario={id!r}]` prefix.
`_validate_perspective` is a no-op when `composition.default_perspectives` is empty.

## Tests

1. Valid scenario with `frontier_living_world` → bundle returned, scenario_id preserved
2. Perspective ID preserved in output
3. Initial conditions become `StateSetupModifier` list with correct modifier_type and value
4. Invalid composition ID → `ValueError` with scenario ID in message
5. Invalid perspective → `ValueError` with scenario ID in message
6. Empty `initial_conditions` → empty modifiers list
7. Resolver does not import observability modules
