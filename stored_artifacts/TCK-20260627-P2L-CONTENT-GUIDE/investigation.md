# Investigation — TCK-20260627-P2L-CONTENT-GUIDE

## Current Behavior

`docs/content/` does not exist. There is no authoring walkthrough for adding modules,
compositions, or scenarios. The only reference is `docs/world/modules_contract.md`, which
is a technical contract aimed at agents, not content authors.

**Data directories observed:**
- `data/content/world_modules/` — 19 module YAML files (frontier_village_core.yaml, etc.)
- `data/content/world_compositions/` — 5 compositions (frontier_living_world.yaml, etc.)
- `data/content/simulation_scenarios/` — 4 scenario YAML files

**Related ticket status:**
- TCK-20260627-P2K-CONTENT-MATRIX — DONE. `_auto_discover_extra_entries()` added to
  `src/content/matrix.py`. New YAML files added anywhere under `data/content/` are now
  auto-detected. Manual `ContentUsageMatrix` registration is no longer required for standard
  content authors. This changes the sharp edges: the guide must say "no manual registration
  needed" rather than "register in ContentUsageMatrix."

## Mechanics / Engine Constraints

No behavior change. This is a docs-only ticket. Engine contracts are referenced for accuracy:
- `docs/world/modules_contract.md` — authoritative schema reference (WORLD-MOD-001 to 007)
- `docs/content/pipeline_contract.md` — ContentPathConfig governs discovery roots
- `src/worldmodules/schema.py` — REGISTERED_MODULE_TYPES, WorldModuleSpec fields
- `src/scenarios/schema.py` — ALLOWED_INITIAL_CONDITION_CATEGORIES

## Parity Ledger Overlap

No parity entries are affected. This ticket creates documentation only.

## Prior Work

- `stored_artifacts/TCK-20260614-WORLDDAT-COMPOSE/` — composition authoring investigation;
  confirms composition schema (world_id, modules list, default_perspectives, generation_seed).
- D16 audit (`docs/audits/D16_scenario_authoring_dx.md`) — primary source; all DX gaps,
  sharp edges, and task assessments documented here drive the guide's structure.
- D17 (Documentation Currency) — identifies modules_contract.md as technical contract not
  a guide; no authoring guide is in D17 scope, confirming this ticket owns it.

## Key Findings

### WorldModuleSpec fields (from modules_contract.md + schema.py)

Identity:
- `module_id` (str, required, unique)
- `module_type` (str, required) — one of: `terrain`, `settlement`, `ecology`, `economy`,
  `conflict`, `population`, `danger_zone`
- `display_name` (str, min_length=1, required)
- `description` (str, optional)
- `version` (str, default "1.0.0")
- `schema_version` (str, optional, not validated)

Dependency:
- `requires` (List[str]) — module IDs that must be processed first
- `provides` (List[str]) — semantic aliases this module advertises
- `parameters` (List[ModuleParameterSpec]) — exposed configurable variables

Structural:
- `regions`, `population_recipes`, `resource_recipes`, `building_recipes` — recipe lists
- `observability_tags` (List[str]) — NOT `tags`; `extra="forbid"` rejects unknown fields
- `quest_definitions` (List[QuestDefinition])
- `biomes`, `ecologies`, `populations`, `relationships`, `factions` — catalog refs

FORBIDDEN field on WorldModuleSpec: `provided_features` — belongs to WorldCompositionSpec only.

### WorldCompositionSpec fields (from composition YAML + frontier_living_world.yaml)

- `world_id` (str, required)
- `name` (str)
- `description` (str)
- `modules` (List[str]) — module IDs to include
- `default_perspectives` (List[str])
- `generation_seed` (int)
- `provided_features` — belongs here, not on module specs

### SimulationScenarioDefinition fields (from schema.py)

- `id` (str)
- `world_composition` (str) — must match an existing composition ID
- `perspective` (str)
- `focus_modules` (List[str]) — must match loaded module IDs
- `initial_conditions` (Dict[str, Any]) — keys must be in allowed set
- `template_id` (str, optional) — triggers template validation

ALLOWED_INITIAL_CONDITION_CATEGORIES (from src/scenarios/schema.py:12-19):
`region_pressure`, `faction_activity`, `resource_scarcity`, `population_alertness`,
`territorial_intrusion`, `trade_route_risk`, `danger_level_override`, `spawn_bias`

### Make targets (from Makefile + D16)

| Target | Description |
|---|---|
| `make world-template WORLD=<id>` | Generate scaffold module YAML (best entry point) |
| `make world-validate WORLD=<id>` | Validate world spec against compile constraints |
| `make world-compile WORLD=<id>` | Compile world to AuthoritativeState |
| `make world-resolve WORLD=<id>` | Resolve compositional specs to compiled assets |
| `make world-inspect WORLD=<id>` | Inspect assembled world structure |
| `make world-list` | List all loaded world modules |
| `make sim-sweep CONFIG=<path>` | Run a scenario sweep matrix |
| `make knowledge-index-update` | Incremental reindex of docs |

### Sharp Edges

1. `observability_tags` not `tags` — Pydantic `extra="forbid"` rejects `tags`
2. `provided_features` is NOT on WorldModuleSpec — only on WorldCompositionSpec
3. Catalog refs (biomes, ecologies, populations, relationships, factions) must match
   registered catalog IDs; no pre-flight warning; error surfaces only at assembly
4. `hazard_level` is a region field inside `regions[].hazard_level`, NOT a top-level
   template field
5. ContentUsageMatrix — now auto-discovered (P2K complete); no manual registration needed
6. Duplicate `module_id` across any YAML files raises ValueError at load time
7. `make world-validate` validates schema only; catalog ID mismatches surface at assembly

## Risks and Open Questions

None. All acceptance criteria map directly to documented source of truth.

## Anti-Drift Hazards

- If module types are expanded via `WorldModuleSpec.register_module_type()`, the guide's
  type list will drift. Mitigate: note that 7 types are the base set.
- If initial_condition categories are extended in schema.py, the guide's category list
  will drift. Mitigate: cite src/scenarios/schema.py:ALLOWED_INITIAL_CONDITION_CATEGORIES
  as the authoritative source.
