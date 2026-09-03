---
status: authoritative
layer: engine
authority: P0
audience: agent
last_verified: 2026-08-28
tags: [worldbuilding, compiler, engine, contract, schema]
---

# World Building Compiler Contract

**Source:** `src/worldbuilding/` (7 files: compiler.py, schema.py, recipe.py, validator.py, repository.py, cli.py, `__init__.py`)  
**Compliance namespaces:** `WORLD-050/051/052` (schema + compiler), `WORLD-060/061/062` (repository), `WORLD-070/071/072` (validator + recipe + CLI)  
**RPG topology laws:** `docs/mechanics/06_worldbuilding_foundation.md` — do not duplicate here.

---

## Two Compilation Paths

The worldbuilding module supports two distinct compilation paths:

| Path | Input | Output | Used by |
|---|---|---|---|
| **Direct** | `WorldSpec` (YAML) | `AuthoritativeState` | Simple scenarios, legacy, lab runs |
| **Composition** | `WorldCompositionSpec` | `CompileContext` → `AuthoritativeState` via WorldAssembly | Complex multi-module worlds |

This contract covers the **direct path** (`WorldSpec` → `AuthoritativeState` via `WorldCompiler`). For the composition path see `docs/world/assembly_contract.md`.

---

## Direct Compilation Pipeline

```
WorldSpec (YAML file)
    ↓
WorldRepository.load()       [repository.py — WORLD-060/061/062]
    ↓
WorldValidator.validate()    [validator.py — WORLD-070/071/072]
    ↓ (abort if ERROR severity issues found)
WorldCompiler.compile()      [compiler.py — WORLD-050/051/052]
    ↓  (reads: TopologySpec, RegionSpec, FactionSpec, PopulationSpec,
        ResourceNodeSpec, BuildingSpec; uses V2EntityBuilder, RoleSemanticsService)
AuthoritativeState
    └── StateFingerprinter.fingerprint()  (hash computed immediately after compile)
```

---

## Schema Contract (schema.py — WORLD-050, WORLD-051, WORLD-052)

**`WorldSpec`** — the root declarative specification for a world. Contains:
- `TopologySpec` — grid dimensions, region layout
- `List[RegionSpec]` — region definitions (type, terrain, terrain_variants, hazard_level, grid_bounds, tags, `places: List[PlaceSpec]` — idea 66, empty for content not yet migrated to Place-shaped form)
- `List[FactionSpec]` — faction definitions and starting parameters
- `List[PopulationSpec]` — entity population groups per region
- `List[ResourceNodeSpec]` — resource node placements
- `List[BuildingSpec]` — building placements
- `quest_definitions: List[QuestDefinition]` — typed quest definitions (default `[]`). Populated by `WorldAssemblyResolver` when composing from modules (see WORLD-ASM-012); can also be authored directly in YAML. Legacy `quests:` key is migrated to `quest_definitions` via a `@model_validator(mode="before")`.

**`QuestDefinition`** (frozen Pydantic model, defined in `src/worldbuilding/schema.py`):

| Field | Type | Default | Description |
|---|---|---|---|
| `id` | `str` | required | Unique quest ID |
| `type` | `Literal["escort","hunt","fetch","explore","defend","investigate"]` | required | Quest category |
| `required_participant_tags` | `List[str]` | `[]` | Entity tag requirements |
| `required_location_tags` | `List[str]` | `[]` | Region tag requirements |
| `reward_budget` | `int` | `100` | Nominal reward value |
| `procedural_hints` | `Dict[str, Any]` | `{}` | Freeform procedural hints |
| `tags` | `List[str]` | `[]` | Searchable labels |
| `source_module` | `Optional[str]` | `None` | Set by assembly; never authored in YAML |

All sub-specs are validated by Pydantic at construction time. `InvalidWorldSpecError` is raised on schema violations.

`load_world_spec_from_yaml(path)` — loads a `WorldSpec` from a YAML file. Raises `InvalidWorldSpecError` on parse or schema failure.

---

## Compiler Contract (compiler.py — WORLD-050, WORLD-051, WORLD-052)

**Entry point:** `WorldCompiler.compile(world_spec, catalog_repo=None, context=None) → AuthoritativeState`

**Compilation sequence:**
1. Create empty `AuthoritativeState`
2. Instantiate `RegionState` objects from `TopologySpec` and `List[RegionSpec]`
2a. Derive `town_center` as the centroid of the first `RegionSpec` with `type == "town"` encountered in `spec.regions` order; left at the `AuthoritativeState` default `(0.0, 0.0)` if no town-type region exists.
3. Spawn entities from `PopulationSpec` using `V2EntityBuilder` (or archetype-native if `context` provided)
4. Instantiate `BuildingState` objects from `List[BuildingSpec]`
5. Instantiate `ResourceNodeState` objects from `List[ResourceNodeSpec]`
6. Assign faction and role enums via `get_role_enum()` / `RoleSemanticsService`
7. Generate initial `QuestState` for hero entities
8. Compute `StateFingerprinter` hash

**Role resolution (`get_role_enum`):**
Priority order:
1. `context.legacy_roles[role_str]` — if a `CompileContext` is provided with pre-resolved roles
2. `RoleSemanticsService(catalog_repo).get_legacy_entity_role(role_str)` — if a `CatalogRepository` is provided
3. Keyword fallback on uppercase role string: HERO→EntityRole.HERO, SHOP/STORE→SHOPKEEPER, MONSTER→MONSTER, CITIZEN/CIVILIAN→CITIZEN, WORKER/PEASANT→WORKER, GUARD→GUARD

**Determinism:** The compiler uses `random` for some entity placement — callers requiring bit-identical output must seed `random` before calling `compile()`.

**Terrain fill (step 2):** Each region is painted as either a flat single-terrain fill (default — unchanged legacy behavior) or, when the region's `RegionSpec.terrain_variants` is populated, a seeded per-tile noise-fill via `DeterministicRNG.weighted_choice()` keyed under `Domain.INIT` (distinct from `Domain.WORLD`'s entity/resource/building draw order, eliminating RNG-namespace collision by construction). The existing bounds-clamp and `town_tiles` membership rule (`r_spec.type == "town"`) apply identically to both branches. Full law and formula: `docs/mechanics/06_worldbuilding_foundation.md` § Noise-Fill Terrain Law — not duplicated here.

---

## Repository Contract (repository.py — WORLD-060, WORLD-061, WORLD-062)

`WorldRepository` — file-based YAML repository for `WorldSpec` documents.

**Operations:**
- `load(world_id)` → `WorldSpec` — loads a world spec by ID from the worlds root directory
- `save(world_spec)` — serialises and writes a `WorldSpec` to YAML
- `list()` → list of world IDs
- Index tracking: maintains an index file for fast listing

**Safety:** All file operations are scoped to the configured worlds root directory. Path traversal is rejected by design (`WorldRepositoryError` raised on invalid paths).

`WorldRepositoryError` — base exception for all repository operations.

---

## Validator Contract (validator.py — WORLD-070, WORLD-071, WORLD-072)

`WorldValidator` runs pluggable `WorldValidationRule` instances against a `WorldSpec`.

**ValidationContext enum** — scopes when a rule is evaluated:

| Context | When applied |
|---|---|
| `CATALOG` | Content catalog consistency |
| `MODULE` | World module structure |
| `COMPOSITION` | WorldCompositionSpec validation |
| `ASSEMBLY` | Assembly pipeline validation |
| `GENERATED_WORLD` | Post-generation world state |
| `WORLD` | WorldSpec structural validation |
| `COMPILE` | Pre-compile validation |
| `EXPERIMENT` | Lab experiment validation |

**ValidationIssue** fields: `rule_id`, `severity` (`ERROR`/`WARNING`/`INFO`), `message`, `path`.

**Abort rule:** Any `ERROR`-severity issue aborts the compilation pipeline — the world spec is rejected. `WARNING` and `INFO` issues are reported but do not abort.

---

## Recipe Contract (recipe.py — WORLD-070, WORLD-071, WORLD-072)

`RegionRecipeSpec` — a frozen Pydantic model for declaring a region in recipe-driven world building.

Fields: `id`, `type`, `grid_bounds: (min_x, min_y, max_x, max_y)`, `terrain` (default `"GRASS"`), `terrain_variants: Optional[List[TerrainVariantSpec]]` (default `None` — when populated, `WorldCompiler` noise-fills the region per-tile instead of flat-filling with `terrain`; see Compiler Contract below), `hazard_level` (default `0.0`).

**Validation rules (enforced at construction):**
- `min_x ≤ max_x` — width must be non-negative
- `min_y ≤ max_y` — height must be non-negative

After building a `WorldSpec` from recipes, `WorldValidator` is run before compilation.

---

## CLI Contract (cli.py — CLI-002, WORLD-070, WORLD-071, WORLD-072)

The CLI (`cli.py`) provides a command-line interface to `WorldRepository`, `WorldValidator`, and `ProceduralCompositionGenerator`. It is the entry point for operator-driven world management.

**Subcommands:** `list`, `validate`, `compile`, `resolve`, `inspect`, `create-template`, `generate`.

**`generate` subcommand** — procedurally generates a `WorldCompositionSpec` YAML from intent parameters:

| Flag | Default | Description |
|---|---|---|
| `--danger-level` | `1.0` | Hazard scalar (float) |
| `--settlement-style` | `"frontier"` | Settlement layout style; `"none"` skips settlement module selection |
| `--seed` | `42` | RNG seed for deterministic generation |
| `--terrain-style` | `"temperate"` | Climatic style label |
| `--resource-density` | `0.5` | Resource node density scalar |
| `--population-scale` | `1.0` | Population count scalar |

Output: writes `data/content/world_compositions/generated/{world_id}.yaml`. World ID format: `generated_{settlement_style}_{int(danger_level)}_{seed}`.

CLI-002 governs the CLI's operational contract (argument parsing, exit codes, error reporting format).

---

## Compliance ID Index

| ID | File | Line | Description |
|---|---|---|---|
| WORLD-050 | src/worldbuilding/compiler.py, schema.py, `__init__.py` | 1 | WorldSpec schema and compiler entry contract |
| WORLD-051 | src/worldbuilding/compiler.py, schema.py, `__init__.py` | 1 | Compilation sequence and entity construction |
| WORLD-052 | src/worldbuilding/compiler.py, schema.py, `__init__.py` | 1 | Role/faction resolution and state fingerprinting |
| WORLD-060 | src/worldbuilding/repository.py | 1 | WorldRepository load/save contract |
| WORLD-061 | src/worldbuilding/repository.py | 1 | Repository index tracking |
| WORLD-062 | src/worldbuilding/repository.py | 1 | Path safety and WorldRepositoryError contract |
| WORLD-070 | src/worldbuilding/validator.py, recipe.py, cli.py | 1 | WorldValidator and ValidationContext |
| WORLD-071 | src/worldbuilding/validator.py, recipe.py, cli.py | 1 | ValidationIssue and abort-on-ERROR rule |
| WORLD-072 | src/worldbuilding/validator.py, recipe.py, cli.py | 1 | RegionRecipeSpec and CLI contract |
| CLI-002 | src/worldbuilding/cli.py | 1 | CLI operational contract |
