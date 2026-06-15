---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260614-WORLDGEN-COMPOSE
artifact_type: investigation
tags: [worldgen, procedural, composition, generator]
---

# Investigation — TCK-20260614-WORLDGEN-COMPOSE

## Key Schema Findings

### WorldModuleSpec (`src/worldmodules/schema.py`)
- `module_id: str`
- `module_type: str` — validated against REGISTERED_MODULE_TYPES
- `requires: List[str]` — IDs of required modules
- `provides: List[str]` — semantic aliases provided (plain strings, no exclusive flag)
- `observability_tags: List[str]` — audit tags (used by scorer for danger classification)
- `resource_recipes: List[ResourceRecipeSpec]` — used by scorer for resource_density dim
- NO `provided_features` field on WorldModuleSpec — `provided_features` lives on WorldCompositionSpec

### WorldCompositionSpec (`src/worldassembly/schema.py`)
- Required fields: `schema_version` (must be "worldcomposition.v1"), `world_id`, `name`
- `module_refs: List[ModuleRefSpec]` — structured refs
- `generation_seed: int` — default 42
- `provided_features: List[str]` — composition-level feature tags
- `modules: Optional[List[str]]` — shorthand (mutually exclusive with module_refs)
- `frozen=True`, `extra="forbid"`

### ModuleRefSpec
- `module_id: str`, `enabled: bool=True`, `order: int=0`, `parameters: Dict`, `namespace: Optional[str]`
- `frozen=True`, `extra="forbid"`

### WorldModuleRepository (`src/worldmodules/repository.py`)
- Method: `list_modules()` returns `List[WorldModuleSpec]` — NOT `get_all()`
- Also: `get_module(module_id)`, `list_modules_by_type(module_type)`
- Must call `load_all()` first to populate

### GenerationIntentSpec (`src/worldgeneration/schema.py`)
- `generation_id`, `seed`, `terrain_style`, `settlement_style`, `danger_level`, `resource_density`, `population_scale`, `required_modules`, `constraints`, `budget_profile`
- No `budget` field — default 6 is hardcoded in the generator

### ModuleScorer (`src/worldgeneration/scorer.py`)
- `ModuleScorer.score(intent, modules) -> Dict[str, ModuleScore]`
- Keys by `module_id`, value has `.score` (float 0-1)

## Conflict Detection
WorldModuleSpec.provides is `List[str]` with no `exclusive` field. Conflict check must
be implemented by comparing `provides` strings across selected modules — if two modules
claim the same string in `provides`, that is treated as a conflict. The test for conflict
will inject this via stub modules.

## Output Path
`data/content/world_compositions/generated/{world_id}.yaml`
world_id = f"generated_{intent.settlement_style}_{int(intent.danger_level)}_{intent.seed}"

## Repository Method Confirmed
`WorldModuleRepository.list_modules()` — confirmed in source.
