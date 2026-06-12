---
status: authoritative
layer: engine
authority: P0
audience: agent
last_verified: 2026-06-12
tags: [worldassembly, engine, contract, compilation, entity-spawning]
---

# World Assembly Contract

**Source:** `src/worldassembly/` (5 files: resolver.py, entity_spawner.py, models.py, schema.py, context.py)  
**Compliance namespace:** `WORLD-ASM-*`  
**Authoritative status:** NOT simulation state. World assembly is a **preprocessing pipeline** — it converts a `WorldCompositionSpec` into live `EntityState` objects and `AuthoritativeState`. The output enters `AuthoritativeState`; the assembly process itself does not.

See also:
- `docs/architecture/world_assembly_architecture.md` — architectural decision record
- `docs/architecture/world_repository_layout.md` — repository layout ADR
- `docs/worldbuilding/compiler_contract.md` — upstream stage (produces `WorldCompositionSpec`)
- `docs/worldgeneration/generator_contract.md` — upstream stage (generates world from spec)

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

**Determinism:** Given the same `CompileContext` and `base_entity_id`, `spawn_from_context` produces bit-identical `EntityState` objects. No randomness is introduced during spawning.

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

Note: WORLD-ASM-004 and WORLD-ASM-005 are not present in the current source — either retired or reserved.
