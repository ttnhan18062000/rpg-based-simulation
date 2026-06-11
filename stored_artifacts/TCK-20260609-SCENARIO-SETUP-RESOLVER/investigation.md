---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260609-SCENARIO-SETUP-RESOLVER
artifact_type: investigation
tags: [scenario, setup, resolver]
---


# Investigation

## Entry points

- `WorldAssemblyResolver.assemble(composition)` in `src/worldassembly/resolver.py` accepts a
  `WorldCompositionSpec | dict` and returns `ResolvedWorldBundle`.
- Compositions live as YAML files in `data/content/world_compositions/` (e.g. `frontier_living_world.yaml`).
- `WorldCompositionSpec.default_perspectives: List[str]` declares valid perspectives per composition.

## Key finding: perspective validation

`WorldCompositionSpec` already stores `default_perspectives`. If the list is non-empty, the resolver
validates the scenario's `perspective` against it. If the composition declares no perspectives,
any perspective is accepted (permissive-if-unspecified).

## Key finding: initial_conditions mapping

`initial_conditions: Dict[str, Any]` in `SimulationScenarioDefinition` maps category → value.
Each entry becomes one `StateSetupModifier(modifier_type=key, parameters={"value": value})`.
Applying these modifiers to live state is out-of-scope (TCK-20260609-SCENARIO-MODIFIER-APPLY).

## No new composition loading infrastructure needed

The resolver loads YAML directly using `yaml.safe_load` + `WorldCompositionSpec.model_validate`,
matching the pattern in `src/worldbuilding/repository.py:200-205`. A `compositions_dir` parameter
allows tests to point at real data without mocking.
