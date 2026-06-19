---
ticket_id: TCK-20260618-AUDIT-D16-DX
type: investigation
date: 2026-06-18
---
# D16 Investigation

## Authoring Surface

### World modules (data/content/world_modules/)
14 live modules. Schema: WorldModuleSpec (Pydantic, extra="forbid"). Required: module_id, module_type, display_name. Catalog refs must match registered IDs. Sharp edges: observability_tags (not tags), no provided_features field.

### World compositions (data/content/world_compositions/)
5 compositions. Schema: world_id, name, modules list, default_perspectives, generation_seed. Simple.

### Simulation scenarios (data/content/simulation_scenarios/)
1 file with 8 scenarios. Schema: SimulationScenarioDefinition (6 fields). 8 allowed initial_condition categories.

### Make targets
world-validate, world-list, world-compile, world-resolve, world-inspect, world-template — solid CLI surface.
sim-sweep — scenario matrix runner.

### Templates
10 scenario templates in src/scenarios/templates.py (territorial_pressure, raider_conflict, trade_route_risk, resource_recovery, ...). Optional: scenarios can reference template_id for structural validation.

### Documentation
Only doc: docs/world/modules_contract.md — technical contract, not an author guide.
No single-page "how to add a module" guide exists.
ContentUsageMatrix (src/content/content_usage_matrix.py or similar) must be updated when new content families added — not documented anywhere for authors.

## Key Pain Points
1. ContentUsageMatrix drift: only caught by CI test, not at authoring time
2. Allowed initial_condition categories documented only in schema.py
3. Catalog ID validation deferred to assembly (not at YAML save time)
4. No authoring guide / README for content authors
5. world-template make target exists but is undiscovered (not in docs)
