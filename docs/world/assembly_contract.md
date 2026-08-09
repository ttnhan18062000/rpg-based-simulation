---
status: authoritative
layer: engine
authority: P0
audience: agent
last_verified: 2026-08-09
tags: [worldassembly, engine, contract, compilation, entity-spawning]
---

# World Assembly Contract

**Source:** `src/worldassembly/` (5 files: resolver.py, entity_spawner.py, models.py, schema.py, context.py)  
**Compliance namespace:** `WORLD-ASM-*`  
**Authoritative status:** NOT simulation state. World assembly is a **preprocessing pipeline** — it converts a `WorldCompositionSpec` into live `EntityState` objects and `AuthoritativeState`. The output enters `AuthoritativeState`; the assembly process itself does not.

See also:
- `docs/architecture/world_assembly_architecture.md` — architectural decision record
- `docs/architecture/world_repository_layout.md` — repository layout ADR
- `docs/world/compiler_contract.md` — upstream stage (produces `WorldCompositionSpec`)
- `docs/world/generator_contract.md` — upstream stage (generates world from spec)

---

## Assembly Pipeline

```
WorldCompositionSpec
    ↓
WorldCompositionNormalizer  [schema.py — WORLD-ASM-006/007]
    ↓
NormalizedWorldComposition
    ↓
WorldAssemblyResolver       [resolver.py — WORLD-ASM-008/009/010]
    ↓  (uses CatalogRepository + WorldModuleRepository + topological_sort_modules)
ResolvedWorldBundle
  ├── world_spec: WorldSpec
  └── compile_context: CompileContext  [context.py — WORLD-ASM-003]
        ├── entities: Dict[str, ResolvedEntityProfile]
        ├── buildings: Dict[str, ResolvedBuildingProfile]
        ├── resources: Dict[str, ResolvedResourceProfile]
        └── factions: Dict[str, ResolvedFactionEconomyProfile]
    ↓
WorldEntitySpawner           [entity_spawner.py]
    ↓
Dict[int, EntityState]       → loaded into AuthoritativeState
```

---

## Schema Contract (schema.py — WORLD-ASM-006, WORLD-ASM-007)

**`WorldCompositionSpec`** — the input document. Declares which world modules compose this world, their ordering constraints, and faction/region assignments.

**`NormalizedWorldComposition`** — output of `WorldCompositionNormalizer`; modules resolved to topological order, references validated.

**`WorldCompositionNormalizer`** — validates and normalises a `WorldCompositionSpec`. Raises on cycles in module dependencies or missing module references.

**`ResolvedModuleContribution`** — per-module resolved contribution record: what entities, buildings, and resources this module adds.

**`ProvenanceManifest` / `ProvenanceRecord`** — audit trail: which module contributed each entity/building/resource, used for debugging and determinism verification.

---

## Compile Context (context.py — WORLD-ASM-003)

`CompileContext` accumulates the resolved profiles for all entities, buildings, resources, and factions during resolution. It is the hand-off object from resolver to spawner.

| Attribute | Type | Description |
|---|---|---|
| `entities` | `Dict[str, ResolvedEntityProfile]` | Resolved entity profiles (keyed by spec index/id) |
| `buildings` | `Dict[str, ResolvedBuildingProfile]` | Resolved building profiles |
| `resources` | `Dict[str, ResolvedResourceProfile]` | Resolved resource profiles |
| `factions` | `Dict[str, ResolvedFactionEconomyProfile]` | Resolved faction economy profiles |
| `region_ownership` | `Dict[str, Faction]` | Region → owning Faction enum |
| `legacy_factions` | `Dict[str, Faction]` | Dynamic faction_id → legacy Faction enum |
| `legacy_roles` | `Dict[str, EntityRole]` | Dynamic role_id → legacy EntityRole enum |
| `perspectives` | `Dict[str, Any]` | Resolved PerspectiveDefinition records (keyed by ID) from WorldCompositionSpec.default_perspectives |

`CompileContext` is **not frozen** — the resolver populates it incrementally during module traversal. After resolution, it must not be modified.

---

## Resolved Profile Models (models.py — WORLD-ASM-001, WORLD-ASM-002)

Four resolved profile types, all passed through `CompileContext`:

- **`ResolvedEntityProfile`** — entity's fully resolved catalog attributes (race, body model, stats, cognition, role, faction)
- **`ResolvedBuildingProfile`** — building's resolved type, services, and durability parameters
- **`ResolvedResourceProfile`** — resource node's resolved kind, harvest parameters, and spawn table
- **`ResolvedFactionEconomyProfile`** — faction's resolved economy parameters (starting gold, vault limits)

---

## Resolver Contract (resolver.py — WORLD-ASM-008, WORLD-ASM-009, WORLD-ASM-010)

**Entry point:** `WorldAssemblyResolver` (or equivalent top-level function in resolver.py)

**Dependencies:**
- `CatalogRepository` — provides content catalog records (biomes, ecologies, regions, resources, buildings, population recipes)
- `WorldModuleRepository` — provides `NormalizedWorldModule` records
- `topological_sort_modules()` — from `src/worldmodules/utils.py`; ensures modules are processed in dependency order

**Resolution sequence (WORLD-ASM-008):**
1. Topological sort of modules from `NormalizedWorldComposition`
2. For each module in order: resolve biomes, ecologies, regions, resources, buildings, population recipes via content resolvers
3. Accumulate into `CompileContext`

**Failure contract (WORLD-ASM-009):**
- Any `ResolverError` during resolution aborts assembly — the world spec is invalid
- Missing catalog references are fatal (not silently skipped)

**Output (WORLD-ASM-010):**
- `ResolvedWorldBundle(world_spec, compile_context)` — handed off to `WorldEntitySpawner`

---

## Entity Spawner Contract (entity_spawner.py)

**Entry point:** `WorldEntitySpawner.spawn_from_context(ctx, catalog_repo, *, base_entity_id, default_position)`

**Primary path (archetype-native):**  
Profiles with `archetype_id` → `EntityArchetypeResolver` → `resolved_archetype_to_contract()` → `ArchetypeEntityFactory.build_entity()` → `EntityState`

**Legacy guard (non-archetype entities):**  
Profiles without `archetype_id` (e.g. town NPCs, synthetic entities) → `V2EntityBuilder` with explicit labelling.

**Entity ID assignment:** Sequential integers starting from `base_entity_id` (default 1). IDs are assigned in `CompileContext.entities` iteration order — deterministic if `CompileContext` was built deterministically.

**Output:** `Dict[int, EntityState]` — loaded into `AuthoritativeState` by the caller.

**Personality generation** (`TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY`): `spawn_from_context`
accepts a `seed: int = 42` parameter, used to seed real, per-entity `PersonalityComponent` values
(both the archetype-native path, via `ArchetypeEntityFactory.build_entity()`, and the legacy-guard
path) via `src/content_semantics/personality.py::build_personality_for_entity` — the same
`DeterministicRNG`/race-correlated-bravery/`ActionStyle` mechanism `WorldCompiler.compile()` uses.
Prior to this ticket, every entity spawned through this path kept `PersonalityComponent()`'s own
all-zero default regardless of race/faction.

**Determinism:** Given the same `CompileContext`, `base_entity_id`, and `seed`, `spawn_from_context`
produces bit-identical `EntityState` objects — the same real, verified guarantee as before, now
parameterized by `seed` rather than being seed-free (personality generation is the only source of
randomness in this pipeline, and it is `DeterministicRNG`-based, not entropy-based).

---

## Pack Validation Contract (WORLD-ASM-011)

`WorldCompositionSpec.pack_refs: List[str]` — optional list of named content pack IDs that must be present and enabled before assembly proceeds.

**Validation sequence** (runs at start of `WorldAssemblyResolver.assemble()`, before module traversal):

1. For each `pack_id` in `pack_refs`:
   - Load the pack manifest (YAML file in the packs directory).
   - If manifest is missing → raise `AssemblyPackError(f"Pack '{pack_id}' not found")`.
   - If `manifest["enabled"] == False` → raise `AssemblyPackError(f"Pack '{pack_id}' is disabled")`.
   - For each entry in `manifest["depends_on"]`: validate the dependency is also present and enabled.
     - Missing dependency → `AssemblyPackError`.
     - Disabled dependency → `AssemblyPackError`.
2. If `pack_refs` is empty, this step is skipped entirely.

**`AssemblyPackError(ValueError)`** — raised when a required pack is missing, disabled, or has unsatisfied dependencies. Not recoverable — assembly aborts.

---

## Quest Definitions Merge Contract (WORLD-ASM-012)

`WorldModuleSpec.quest_definitions: List[QuestDefinition]` — each module may declare typed quest definitions. The resolver merges them into `WorldSpec.quest_definitions` during module traversal.

**Merge rules** (executed in `resolve_module_contribution()` for each module):

1. For each `QuestDefinition` in the module's `quest_definitions`:
   - `source_module` is stamped with the current `module_id` via `qd.model_copy(update={"source_module": m_id})`.
   - If the quest `id` already appears in the accumulated `quest_defs` dict → raise `AssemblyCollisionError` with both module IDs.
   - Otherwise, add to the accumulator dict keyed by `id`.
2. After all modules are traversed, `quest_defs.values()` is written to `WorldSpec.quest_definitions`.

**`AssemblyCollisionError(ValueError)`** — raised when two modules contribute a quest with the same `id`. Not recoverable — assembly aborts.

**`QuestDefinition` model** (defined in `src/worldbuilding/schema.py`, frozen Pydantic):

| Field | Type | Default | Description |
|---|---|---|---|
| `id` | `str` | required | Unique quest identifier |
| `type` | `Literal["escort","hunt","fetch","explore","defend","investigate"]` | required | Quest category |
| `required_participant_tags` | `List[str]` | `[]` | Entity tag requirements for participants |
| `required_location_tags` | `List[str]` | `[]` | Region/location tag requirements |
| `reward_budget` | `int` | `100` | Nominal reward budget |
| `procedural_hints` | `Dict[str, Any]` | `{}` | Freeform hints for procedural instantiation |
| `tags` | `List[str]` | `[]` | Searchable labels |
| `source_module` | `Optional[str]` | `None` | Set by assembly; never authored in YAML |

**Access pattern:** After assembly, use `bundle.world_spec.quest_definitions` to read merged quest definitions. `AuthoritativeState` does not carry quest definitions directly.

---

## WorldAssemblyValidator Parametric Contract (WORLD-ASM-013)

`WorldAssemblyValidator.validate(module, params)` runs pre-assembly validation on a module's recipe fields. For parametric recipe counts (e.g. `count: "{merchant_count}"`), it resolves the expression using the **module's default parameter values** rather than an empty dict.

**Why:** Passing an empty param dict to `ModuleParameterEvaluator.evaluate_field()` for a parametric expression raises `AssemblyParameterError` because the substitution key is absent. The validator uses defaults so that template modules with no injected params can still be validated.

```python
default_param_vals = {p.name: p.default for p in module.parameters if p.default is not None}
count = ModuleParameterEvaluator.evaluate_field(recipe.count, default_param_vals)
```

---

## Compliance ID Index

| ID | File | Line | Description |
|---|---|---|---|
| WORLD-ASM-001 | src/worldassembly/models.py | 1 | ResolvedEntityProfile and ResolvedBuildingProfile schemas |
| WORLD-ASM-002 | src/worldassembly/models.py | 1 | ResolvedResourceProfile and ResolvedFactionEconomyProfile schemas |
| WORLD-ASM-003 | src/worldassembly/context.py | 1 | CompileContext accumulation contract |
| WORLD-ASM-006 | src/worldassembly/schema.py | 1 | WorldCompositionSpec and NormalizedWorldComposition schemas |
| WORLD-ASM-007 | src/worldassembly/schema.py | 1 | WorldCompositionNormalizer and ProvenanceManifest contract |
| WORLD-ASM-008 | src/worldassembly/resolver.py | 1 | Resolver resolution sequence (topological sort + module traversal) |
| WORLD-ASM-009 | src/worldassembly/resolver.py | 1 | Failure contract (ResolverError is fatal, no silent skips) |
| WORLD-ASM-010 | src/worldassembly/resolver.py | 1 | ResolvedWorldBundle output contract |
| WORLD-ASM-011 | src/worldassembly/resolver.py | 1 | pack_refs validation — AssemblyPackError on missing/disabled packs |
| WORLD-ASM-012 | src/worldassembly/resolver.py | 1 | quest_definitions merge — source_module stamping and AssemblyCollisionError |
| WORLD-ASM-013 | src/worldassembly/resolver.py | 1 | WorldAssemblyValidator parametric validation using module defaults |

Note: WORLD-ASM-004 and WORLD-ASM-005 are not present in the current source — either retired or reserved.
