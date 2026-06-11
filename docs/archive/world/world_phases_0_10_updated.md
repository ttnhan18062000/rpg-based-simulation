---
status: archive
authority: P2
audience: historical
layer: world
original_date: unknown
---

# Updated Implementation Plan: World Data Refactor and World Assembly Foundation

## Purpose

This document defines the updated phase implementation plan for the world data refactor, content catalog, module-based world assembly, validation, provenance, and future procedural generation foundation.

The plan incorporates the latest review corrections:

- `src/content_semantics` is used instead of `src/policies`.
- `CompileProfileResolver` lives in `src/worldassembly`.
- Profile fields must be consumed and tested, not left as dead schema stubs.
- Provenance is stored in a sidecar `ProvenanceManifest`, not in `EntityState` and not primarily in `identity.properties`.
- `worldspec.v1` stays clean; enriched metadata lives in sidecar artifacts.
- Resolver and assembly come before procedural generation.
- Phase 5 resolver performs structural validation only until Phase 6 introduces context-aware validation.
- `ASSEMBLY` validation context is explicitly defined.
- `GENERATED_WORLD` validation context is defined in Phase 6 but exercised after Phase 8.
- `quest_seeds` is deferred from the first module schema version.

The central architectural rule is:

```text
Content and module systems prepare the world.
WorldCompiler compiles only a clean validated worldspec.v1.
Runtime engine executes the simulation and must not depend on world generation internals.
```

---

## Non-Negotiable Architecture Rules

1. `WorldCompiler` must never receive `WorldCompositionSpec` directly.
2. `WorldCompiler` must never load catalog files, module files, or generation-intent files.
3. `worldspec.v1` remains clean and compiler-compatible.
4. Metadata such as `source_module_id`, `archetype_id`, `generation_step`, and fingerprints must live in sidecar artifacts.
5. Provenance must not be added directly to `EntityState` in this implementation track.
6. `src/content_semantics` interprets catalog meaning but does not execute runtime simulation logic.
7. `src/worldassembly` owns `CompileProfileResolver` and `WorldAssemblyResolver`.
8. Module validation is not the same as full-world validation.
9. Phase 5 resolver performs structural validation only; context-aware content validation is Phase 6.
10. Procedural generation outputs clean resolved world data, not runtime state.
11. Existing `worldspec.v1` and `worldtemplate.v1` workflows must remain supported.
12. Existing profile fields must become consumed behavior through controlled resolution.

---

# Phase 0: Architecture Inventory and Boundary Freeze

## Description

Phase 0 freezes the architecture before feature implementation begins. It maps current hardcoded assumptions, decides repository layout, confirms package ownership, and prevents accidental coupling between content systems, world assembly, compiler, and runtime engine.

This phase should not change runtime behavior.

## Notes

This phase is mandatory. The goal is to expose hidden coupling before implementation starts.

The most important mindset is that this feature is not just procedural generation. It is a world assembly platform. Procedural generation is only one future input mode.

## Tasks

### Task 0.1: Create world-data architecture decision record

#### Task description

Create an architecture decision record defining the approved boundaries for the world-data refactor.

#### Task technical description

The document must define ownership of the major packages:

```text
src/content
    Static reusable definitions and catalog schemas.

src/content_semantics
    Code-based interpretation of catalog meaning.

src/worldmodules
    Reusable structural world module schemas and repository.

src/worldassembly
    World composition resolver, CompileProfileResolver, bundle creation, provenance sidecar creation.

src/worldbuilding
    Existing concrete WorldSpec schema, repository, validation, compiler boundary.

src/worldgen
    Optional procedural generation layer, only after resolver exists.

src/engine
    Runtime simulation execution only.
```

The document must explicitly define forbidden dependencies:

```text
src/engine must not import src/worldgen.
src/engine must not import src/worldmodules.
src/core should not depend on world generation or composition.
WorldCompiler must not understand module composition.
WorldCompiler must not load catalogs directly.
worldspec.v1 remains clean.
provenance metadata remains sidecar-only.
```

#### Task notes

`CompileProfileResolver` belongs in `src/worldassembly` because it translates catalog/profile references into normalized compile-ready values. It does not belong in `src/content_semantics`, because that package interprets meaning. It does not belong inside `WorldCompiler`, because that would pollute the compiler boundary.

#### Task acceptance criteria

- Architecture decision record exists.
- Package responsibilities are explicitly defined.
- Forbidden dependency directions are listed.
- `CompileProfileResolver` location is decided as `src/worldassembly`.
- `worldspec.v1` is explicitly declared as clean compiler input.
- Provenance sidecar strategy is documented.

---

### Task 0.2: Inventory hardcoded semantic assumptions

#### Task description

Audit all hardcoded content assumptions that currently affect world compilation or runtime world behavior.

#### Task technical description

The inventory must include at minimum:

```text
Faction enum usage
EntityRole enum usage
get_faction_enum usage
get_role_enum usage
region type checks
terrain checks
spawn pool usage
resource type assumptions
building type assumptions
service type assumptions
quest kind assumptions
default entity HP / max HP
default entity attack / defense / readiness
default resource required_ticks
default building HP / max HP
default faction vault gold
default region ownership
direct Faction.HERO_GUILD checks
direct Faction.MONSTER_HORDE checks
```

Each inventory item should record:

```text
file path
function/class
current behavior
why it is hardcoded
migration target
risk level
whether it blocks Phase 1, 2, 3, 5, or 9
```

#### Task notes

Do not refactor while doing the inventory. This is a mapping exercise.

#### Task acceptance criteria

- Hardcoded semantic inventory exists.
- Compiler defaults are explicitly listed.
- Faction and role mapper usage is listed.
- Direct enum checks are listed.
- Each item has a proposed migration destination.

---

### Task 0.3: Decide repository layout for WorldCompositionSpec

#### Task description

Define where `worldcomposition.v1` files live and how they are discovered.

#### Task technical description

Use the existing world repository root and distinguish source type by `schema_version`.

Recommended source layout:

```text
data/worlds/<world_id>/world.yaml
```

The file may contain one of:

```text
worldspec.v1
worldtemplate.v1
worldcomposition.v1
```

For `worldcomposition.v1`, the repository indexes it as a composition source, not as a compiler-ready world.

Resolved outputs should be written separately:

```text
data/worlds/<world_id>/resolved/world.resolved.yaml
data/worlds/<world_id>/resolved/provenance_manifest.json
data/worlds/<world_id>/resolved/assembly_report.json
data/worlds/<world_id>/resolved/validation_report.json
data/worlds/<world_id>/resolved/compile_report.json
```

#### Task notes

Do not introduce a separate root repository yet. Keep the repository model simple.

Do not pass `worldcomposition.v1` directly to `WorldCompiler`.

#### Task acceptance criteria

- Repository layout decision is documented.
- `worldcomposition.v1` is treated as a source schema, not compiler input.
- Resolved output paths are defined.
- Existing `worldspec.v1` and `worldtemplate.v1` repository behavior remains supported.

---

## Phase 0 Acceptance Criteria

- Architecture boundary document completed.
- Hardcoded semantic inventory completed.
- `WorldCompositionSpec` repository strategy decided.
- `CompileProfileResolver` location decided.
- No runtime behavior changed.
- Existing tests still pass without modification.

---

# Phase 1: Content Catalog Foundation

## Description

Phase 1 introduces the static content definition layer. The catalog is where reusable world concepts live: factions, roles, profiles, archetypes, resources, buildings, services, terrain, spawn tables, and default compile profiles.

This phase creates content vocabulary. It does not yet change simulation runtime behavior.

## Notes

Phase 1 must complete before Phase 2. The content semantics layer depends on catalog schemas, repository, lookup APIs, and base catalog data.

The catalog must not become a programming language. It declares facts and classifications. Code interprets those facts later.

## Tasks

### Task 1.1: Define catalog schema family

#### Task description

Create schema definitions for the first version of the content catalog.

#### Task technical description

Define catalog schemas for:

```text
FactionDefinition
RoleDefinition
StatsProfileDefinition
CombatProfileDefinition
InventoryProfileDefinition
CognitionProfileDefinition
ResourceDefinition
BuildingDefinition
ServiceProfileDefinition
TerrainDefinition
SpawnTableDefinition
DefaultCompileProfile
```

Each definition should support:

```text
id
display_name
description
tags
schema_version
deprecated
metadata
```

Faction definitions should additionally support:

```text
alignment_bucket
influence_role
relationship_group
legacy_engine_bucket
```

Role definitions should additionally support:

```text
role_family
legacy_engine_role
default_stats_profile
default_inventory_profile
default_cognition_profile
```

#### Task notes

Keep the schema small. Do not try to model all future behavior.

The first catalog must be able to reproduce current behavior before it enables richer behavior.

#### Task acceptance criteria

- Catalog schema definitions exist.
- `FactionDefinition` supports `legacy_engine_bucket`.
- `RoleDefinition` supports `legacy_engine_role`.
- Profile definition schemas exist.
- No runtime system depends on the catalog yet.

---

### Task 1.2: Create catalog repository and loader

#### Task description

Create a catalog repository that loads content definitions from files and exposes validated lookup access.

#### Task technical description

Recommended layout:

```text
data/content/factions.yaml
data/content/roles.yaml
data/content/profiles/stats.yaml
data/content/profiles/combat.yaml
data/content/profiles/inventory.yaml
data/content/profiles/cognition.yaml
data/content/resources.yaml
data/content/buildings.yaml
data/content/services.yaml
data/content/terrain.yaml
data/content/spawn_tables.yaml
data/content/defaults.yaml
```

The repository should expose read-only lookup operations:

```text
get_faction(id)
get_role(id)
get_stats_profile(id)
get_combat_profile(id)
get_inventory_profile(id)
get_cognition_profile(id)
get_resource(id)
get_building(id)
get_service_profile(id)
get_terrain(id)
get_spawn_table(id)
get_default_profile(id)
```

It should also expose index-level information:

```text
all ids by type
deprecated ids
missing references
catalog fingerprint
catalog version
```

#### Task notes

The catalog repository must not depend on `WorldSpec`, `AuthoritativeState`, or runtime engine systems.

#### Task acceptance criteria

- Catalog repository can load all catalog files.
- Duplicate IDs are rejected.
- Missing required fields are rejected.
- Lookup by ID works.
- Catalog fingerprint is produced.
- Repository has no dependency on runtime engine systems.

---

### Task 1.3: Create minimal base catalog

#### Task description

Create a minimal base catalog that reproduces current behavior.

#### Task technical description

The base catalog should include definitions equivalent to current behavior:

```text
villagers-like faction -> HERO_GUILD bucket
monsters-like faction -> MONSTER_HORDE bucket
town-like faction -> TOWN_COUNCIL bucket
neutral-like faction -> NEUTRAL bucket

hero -> EntityRole.HERO
worker -> EntityRole.WORKER
monster -> EntityRole.MONSTER
citizen -> EntityRole.CITIZEN
guard -> EntityRole.GUARD
shopkeeper -> EntityRole.SHOPKEEPER
```

Base defaults should include:

```text
default entity hp / max_hp
default attack / defense / readiness
default building hp / max_hp
default resource required_ticks
default faction starting gold
```

#### Task notes

This phase preserves behavior. It does not enrich gameplay yet.

#### Task acceptance criteria

- Base catalog can reproduce current enum mapping behavior.
- Base catalog includes current compile defaults.
- Existing world examples can resolve against the base catalog.
- No simulation behavior change is expected.

---

### Task 1.4: Add catalog validation

#### Task description

Add catalog-level validation independent of world validation.

#### Task technical description

Catalog validation should catch:

```text
duplicate ids
missing legacy mappings where required
invalid legacy enum names
missing referenced profiles
deprecated definition references
invalid profile numeric ranges
invalid tag format
invalid default compile profile
```

It should return a structured report with warnings and errors.

#### Task notes

Do not reuse `WorldValidator` directly. Catalog validation has different rules from full-world validation.

#### Task acceptance criteria

- Catalog validation report exists.
- Invalid catalog fails before world assembly.
- Warnings and errors are distinguishable.
- Validation can run from tests and future CLI.

---

## Phase 1 Acceptance Criteria

- Content catalog schemas exist.
- Catalog repository and loader exist.
- Minimal base catalog exists.
- Catalog validation exists.
- Catalog can represent current faction, role, and default behavior.
- Runtime simulation remains unchanged.

---

# Phase 2: Content Semantics Layer

## Description

Phase 2 introduces the semantic interpretation layer that converts catalog definitions into meaningful answers for worldbuilding and compilation.

This layer is code. It does not store runtime state and does not execute simulation ticks.

## Notes

Phase 2 depends on Phase 1. Do not start Phase 2 until catalog schema, repository, and lookup APIs are stable.

Use `src/content_semantics`. Do not use `src/policies`, because that name conflicts conceptually with engine runtime policy.

## Tasks

### Task 2.1: Create faction semantics service

#### Task description

Create a service that interprets faction definitions without exposing raw YAML to world systems.

#### Task technical description

The service should answer:

```text
get_legacy_faction_bucket(faction_id)
get_alignment_bucket(faction_id)
get_influence_role(faction_id)
is_hostile(faction_a, faction_b)
is_protector(faction_id)
is_invader(faction_id)
is_neutral(faction_id)
```

For the first version, `is_hostile` may use relationship group fallback or existing legacy bucket behavior.

#### Task notes

Do not yet replace every direct engine enum check. This service is the bridge.

#### Task acceptance criteria

- Faction semantics service exists.
- It resolves legacy `Faction` buckets from catalog definitions.
- It supports basic faction meaning lookups.
- Tests cover current villagers, monsters, town, and neutral behavior.

---

### Task 2.2: Create role semantics service

#### Task description

Create a service that interprets role definitions.

#### Task technical description

The service should answer:

```text
get_legacy_entity_role(role_id)
get_role_family(role_id)
get_default_stats_profile(role_id)
get_default_inventory_profile(role_id)
get_default_cognition_profile(role_id)
is_combatant(role_id)
is_civilian(role_id)
is_worker(role_id)
```

#### Task notes

This eventually replaces direct string parsing in `get_role_enum`, but the migration should be incremental.

#### Task acceptance criteria

- Role semantics service exists.
- It resolves legacy `EntityRole` values.
- It supports current role mapping behavior.
- Unknown roles have predictable validation or fallback behavior.

---

### Task 2.3: Create default semantics service

#### Task description

Create a service that resolves current compiler defaults from catalog definitions.

#### Task technical description

The service should provide normalized default values for:

```text
entity combat defaults
building durability defaults
resource harvest defaults
faction vault defaults
region ownership defaults
```

The service should reproduce current compiler behavior before it enables new behavior.

#### Task notes

This is not yet full profile wiring. It centralizes current default meaning.

#### Task acceptance criteria

- Default values are available through semantic service APIs.
- Values match current compiler behavior.
- Tests prove current default output remains stable.

---

### Task 2.4: Add compatibility adapters for existing mappers

#### Task description

Wrap current mapper behavior behind semantic services while keeping public helper behavior stable.

#### Task technical description

Current helpers should remain available:

```text
get_faction_enum(...)
get_role_enum(...)
get_quest_kind(...)
```

Faction and role resolution should be able to use catalog-backed semantics when a catalog is provided.

#### Task notes

Do not break existing tests that assert current mapper behavior.

#### Task acceptance criteria

- Existing mapper tests still pass.
- Catalog-backed semantic resolution is available.
- Existing direct callers do not require immediate migration.

---

## Phase 2 Acceptance Criteria

- `src/content_semantics` exists.
- Faction semantics exists.
- Role semantics exists.
- Default semantics exists.
- Current enum mapping behavior is preserved.
- Runtime engine remains unchanged.

---

# Phase 3: Profile Consumer Bridge

## Description

Phase 3 makes currently dead profile fields real. The goal is to create a controlled path from recipe/catalog profile references into compile-time values.

This is not a full rich profile system. It is a minimal bridge that prevents profile fields from remaining decorative schema.

## Notes

`CompileProfileResolver` lives in `src/worldassembly`.

The resolver translates catalog/profile references into normalized compile-ready values. It must not mutate runtime state and must not make `WorldCompiler` load catalog files.

## Tasks

### Task 3.1: Define normalized compile profile models

#### Task description

Define internal normalized models that represent compiler-ready profile results.

#### Task technical description

Create compile-facing models conceptually like:

```text
ResolvedEntityProfile
    legacy_role
    legacy_faction
    hp
    max_hp
    atk
    def_stat
    attack_range
    readiness
    inventory_seed
    cognition_seed

ResolvedBuildingProfile
    hp
    max_hp
    service_profile_id
    owner_faction

ResolvedResourceProfile
    required_ticks
    resource_type
    yield_policy

ResolvedFactionEconomyProfile
    starting_gold
```

These models are not YAML schemas. They are internal normalized outputs used by assembly and compiler integration.

#### Task notes

Keep the models close to compile needs. Do not mirror every catalog field.

#### Task acceptance criteria

- Normalized compile profile models exist.
- Models are separate from external YAML schemas.
- Models include enough fields to replace current hardcoded compiler defaults gradually.

---

### Task 3.2: Implement CompileProfileResolver

#### Task description

Create a resolver that merges role defaults, faction defaults, explicit recipe profile references, and global defaults into compiler-ready profiles.

#### Task technical description

Recommended resolution priority:

```text
1. explicit recipe/profile reference
2. role default profile
3. faction/type default profile when relevant
4. global default compile profile
```

The resolver should accept catalog and semantic services and output normalized compile profiles.

#### Task notes

Do not make the resolver mutate `WorldSpec`.

Do not let raw YAML values directly override runtime components without catalog validation.

#### Task acceptance criteria

- `CompileProfileResolver` exists under `src/worldassembly`.
- It resolves explicit profile references.
- It falls back to role/global defaults.
- It returns normalized compile-ready profile objects.
- Missing profile references produce validation/resolution errors, not silent defaults.

---

### Task 3.3: Wire profile resolver into compilation path without breaking existing worlds

#### Task description

Allow the compile path to consume resolved profiles while preserving current behavior for old worlds.

#### Task technical description

Preferred model:

```text
WorldAssembly creates CompileContext.
CompileContext includes resolved profiles.
WorldCompiler receives WorldSpec + optional CompileContext.
If no CompileContext is provided, current defaults are used.
```

#### Task notes

Do not make `WorldCompiler` load catalogs itself.

Compiler may consume resolved values, but should not know how they were derived.

#### Task acceptance criteria

- Existing compile calls still work.
- New compile path can provide resolved profile data.
- Profile-backed entity stats can differ from old defaults in controlled tests.
- Old world outputs remain stable when no profile context is supplied.

---

### Task 3.4: Add profile consumer tests

#### Task description

Add tests proving profile fields are consumed.

#### Task technical description

Tests should cover:

```text
population recipe with stats_profile affects compiled entity stats
role default profile applies when no explicit stats_profile is provided
explicit profile overrides role default
missing profile reference fails validation/resolution
service_profile affects resolved building profile
old world with no profiles preserves old defaults
```

#### Task notes

Phase 3 is successful only when tests prove profile fields affect output.

#### Task acceptance criteria

- Tests prove profile fields are consumed.
- Tests prove fallback behavior.
- Tests prove old behavior remains stable.

---

## Phase 3 Acceptance Criteria

- `CompileProfileResolver` exists in `src/worldassembly`.
- Profile fields are consumed.
- Current compiler defaults can be reproduced through profiles/defaults.
- Existing worlds still compile.
- Profile-backed worlds can intentionally produce different compiled stats.

---

# Phase 4: World Module Schema

## Description

Phase 4 introduces reusable structural modules for composing worlds without creating giant YAML files.

A module is not a full world. It is a reusable content/structure package that can contribute regions, populations, resources, buildings, constraints, and observability tags.

## Notes

This phase does not include procedural generation.

`quest_seeds` is deferred from the first module schema version. Quest seed design touches triggers, objectives, rewards, completion conditions, and quest state transitions; it should be handled later as a dedicated `QuestModuleSpec` or equivalent design.

## Tasks

### Task 4.1: Define WorldModuleSpec v1

#### Task description

Create the schema for reusable world modules.

#### Task technical description

First version fields:

```text
schema_version
module_id
module_type
display_name
description
version
requires
provides
parameters
regions
population_recipes
resource_recipes
building_recipes
constraints
observability_tags
```

Module types should include at least:

```text
terrain
settlement
ecology
economy
conflict
population
```

Quest contribution is intentionally out of scope for v1.

#### Task notes

A module may be incomplete. For example, a terrain module does not need resources or buildings. This is why module validation cannot behave like full-world validation.

#### Task acceptance criteria

- `WorldModuleSpec` schema exists.
- Module type is explicit.
- Requires/provides sections exist.
- Parameter schema exists.
- Module can declare partial world contributions.
- Quest seed fields are not implemented in v1.

---

### Task 4.2: Define module parameter model

#### Task description

Allow modules to expose controlled parameters without becoming scripts.

#### Task technical description

Parameters should support:

```text
name
type
default
required
allowed_values
min/max for numbers
description
```

Supported parameter types:

```text
string
integer
float
boolean
enum
id_reference
```

#### Task notes

No executable expressions.

No embedded logic language.

#### Task acceptance criteria

- Modules can declare parameters.
- Parameter values can be validated.
- Invalid parameter types are rejected.
- No executable expressions are supported.

---

### Task 4.3: Define module dependency and merge rules

#### Task description

Specify how modules are ordered, validated structurally, and merged.

#### Task technical description

Use deterministic module resolution:

```text
1. explicit order in WorldCompositionSpec
2. dependency graph validation
3. topological sort for dependency safety
4. explicit order wins where valid
5. stable alphabetical module_id tie-breaker
```

Merge rules must define behavior for:

```text
duplicate region IDs
duplicate population IDs
duplicate resource IDs
duplicate building IDs
duplicate provided aliases
conflicting parameters
missing required provides
namespace prefixes
```

Default behavior:

```text
conflicting IDs are errors unless an explicit namespace or override rule exists
```

#### Task notes

Silent overwrite is forbidden.

#### Task acceptance criteria

- Module resolution order is deterministic.
- Dependency validation is documented.
- Duplicate ID behavior is documented.
- Silent overwrite is forbidden.

---

### Task 4.4: Create module repository

#### Task description

Create a repository for loading reusable modules.

#### Task technical description

Recommended layout:

```text
data/world_modules/terrain/*.yaml
data/world_modules/settlements/*.yaml
data/world_modules/ecology/*.yaml
data/world_modules/economy/*.yaml
data/world_modules/conflicts/*.yaml
data/world_modules/populations/*.yaml
```

The repository should expose:

```text
get_module(module_id)
list_modules()
list_modules_by_type(type)
validate_module(module_id)
module_fingerprint(module_id)
```

#### Task notes

Keep this separate from `WorldRepository`. `WorldRepository` owns world sources. `WorldModuleRepository` owns reusable modules.

#### Task acceptance criteria

- Module repository exists.
- Modules can be loaded by ID.
- Modules can be listed by type.
- Module fingerprint is available.
- Invalid module schema fails module validation.

---

## Phase 4 Acceptance Criteria

- `WorldModuleSpec` v1 exists.
- Module parameters exist.
- Module dependency and merge rules are defined.
- Module repository exists.
- Modules are not yet required to generate or compile worlds.
- Quest seed contribution is deferred.

---

# Phase 5: WorldCompositionSpec and Structural Assembly Resolver

## Description

Phase 5 creates the world assembly pipeline. It allows a world source to reference catalog definitions and modules, resolve them deterministically, and produce a clean `worldspec.v1` plus sidecar reports.

This phase performs structural validation only. Context-aware content validation is introduced in Phase 6.

## Notes

This phase depends on Phase 3. `WorldAssemblyResolver` must delegate profile resolution to `CompileProfileResolver` and must not implement a duplicate profile resolver.

`worldcomposition.v1` can live in:

```text
data/worlds/<world_id>/world.yaml
```

But it is not compiler input.

## Tasks

### Task 5.1: Define WorldCompositionSpec

#### Task description

Create the schema for a compositional world source.

#### Task technical description

The schema should include:

```text
schema_version: worldcomposition.v1
world_id
name
description
catalog_refs
module_refs
module_parameters
topology_overrides
global_parameters
generation_seed
validation_profile
output_policy
```

Module references should support:

```text
module_id
enabled
order
parameters
namespace
```

#### Task notes

Do not duplicate full module contents inside `WorldCompositionSpec`.

It should assemble, not define everything inline.

#### Task acceptance criteria

- `WorldCompositionSpec` schema exists.
- It can reference modules by ID.
- It can provide module parameters.
- It can define generation seed.
- It does not pass directly to `WorldCompiler`.

---

### Task 5.2: Implement WorldAssemblyResolver with structural validation only

#### Task description

Create the resolver that transforms `WorldCompositionSpec` into `ResolvedWorldBundle`.

#### Task technical description

Resolver responsibilities in Phase 5:

```text
load catalog
load referenced modules
validate module existence
validate dependency graph
validate no circular dependencies
validate required provides are available
validate parameter shape and type
apply deterministic module order
merge module contributions
detect ID conflicts
resolve catalog references
resolve profiles through CompileProfileResolver
produce clean WorldSpec
produce provenance manifest shell/initial records
produce assembly report
```

Important: Phase 5 resolver validation is structural only.

Allowed structural checks:

```text
module exists
dependency graph valid
no circular dependency
required provides available
parameters valid
ID conflicts detected
merge order deterministic
```

Not allowed in Phase 5 structural validation:

```text
NoResourcesWarningRule
NoBuildingsWarningRule
final runnable-world completeness checks
economy completeness checks
quest completeness checks
full-world strict validation rules
```

Those rules belong to Phase 6 context-aware validation.

Output:

```text
ResolvedWorldBundle
    world_spec: clean worldspec.v1
    provenance_manifest
    assembly_report
    validation_inputs
    fingerprints
```

#### Task notes

Requires Phase 3 `CompileProfileResolver`.

The resolver should not compile.

The resolver should not mutate runtime state.

The resolver must not import engine runtime systems.

#### Task acceptance criteria

- Resolver produces a clean `WorldSpec`.
- Resolver produces sidecar provenance shell/initial records.
- Resolver produces assembly report.
- Resolver performs structural validation only.
- Resolver does not run full-world content rules during module/module-composition validation.
- Resolver delegates profile resolution to `CompileProfileResolver`.
- Resolver does not import engine runtime systems.
- Resolver does not call `WorldCompiler`.

---

### Task 5.3: Keep worldspec.v1 clean

#### Task description

Ensure no enrichment metadata is injected into the `WorldSpec` passed to validation/compiler.

#### Task technical description

The resolver must strip or sidecar all enrichment fields:

```text
source_module_id
source_recipe_id
archetype_id
generation_step
catalog_fingerprint
module_fingerprint
```

These fields go into the provenance sidecar, not the clean `WorldSpec`.

#### Task notes

This preserves the existing `worldspec.v1` schema boundary.

#### Task acceptance criteria

- Resolved `WorldSpec` validates as `worldspec.v1`.
- No unknown top-level enrichment fields are present.
- Provenance data exists only in sidecar reports.
- Strict world validation does not fail due to enrichment metadata.

---

### Task 5.4: Extend repository and CLI for composition sources

#### Task description

Allow repository and CLI to recognize and resolve `worldcomposition.v1`.

#### Task technical description

Repository behavior:

```text
rebuild_index detects worldcomposition.v1
index records source_type = composition
composition is not marked compiler-ready until resolved
```

CLI behavior should support:

```text
list
validate
resolve
compile
inspect
```

Expected flow:

```text
validate world_id
    validates source schema and structural assembly feasibility

resolve world_id
    writes resolved/world.resolved.yaml and sidecars

compile world_id
    if source is composition, resolve first or use existing resolved artifact based on flag/policy
```

#### Task notes

Do not break existing `worldspec.v1` and `worldtemplate.v1` CLI behavior.

#### Task acceptance criteria

- Repository indexes `worldcomposition.v1`.
- CLI can validate composition source structurally.
- CLI can resolve composition source.
- Existing `worldspec.v1` and `worldtemplate.v1` CLI flows still work.
- Compile never passes composition source directly to `WorldCompiler`.

---

## Phase 5 Acceptance Criteria

- `WorldCompositionSpec` exists.
- `WorldAssemblyResolver` exists.
- `ResolvedWorldBundle` exists.
- Resolver outputs clean `worldspec.v1` plus sidecars.
- Resolver performs structural validation only.
- Repository and CLI understand composition sources.
- Existing direct worldspec/template workflows remain valid.

---

# Phase 6: Context-Aware Validation System

## Description

Phase 6 upgrades validation from global strict mode into scoped validation contexts.

The current validation model is too blunt for module-based assembly. A terrain module without resources may be valid as a module, while a final runnable world without resources may be incomplete.

## Notes

Do not remove strict mode. Make strict mode context-aware.

The new model is:

```text
validation_context + severity + strictness
```

not just:

```text
strict = true
```

`GENERATED_WORLD` context is defined in this phase for architecture completeness, but it is only exercised by tests after Phase 8 introduces procedural generation.

## Validation Context Definitions

```text
CATALOG
    Validates reusable content definitions.

MODULE
    Validates an individual reusable module in isolation.

COMPOSITION
    Validates the requested worldcomposition.v1 source before merge.

ASSEMBLY
    Validates the merged post-module world draft before final worldspec.v1 emission.

GENERATED_WORLD
    Validates procedurally generated output. Defined in Phase 6, exercised after Phase 8.

WORLD
    Validates a final concrete worldspec.v1 intended for compilation.

COMPILE
    Validates compiler-readiness and CompileContext consistency.

EXPERIMENT
    Validates scenario, experiment, and run constraints.
```

The distinction between `COMPOSITION`, `ASSEMBLY`, and `WORLD` is important:

```text
COMPOSITION = validate the assembly request.
ASSEMBLY = validate the merged result of that request before final clean WorldSpec emission.
WORLD = validate the final concrete worldspec.v1.
```

## Tasks

### Task 6.1: Define validation context model

#### Task description

Create explicit validation contexts and rule applicability metadata.

#### Task technical description

Each validation rule should declare:

```text
applicable contexts
default severity per context
strict behavior per context
```

#### Task notes

Some rules are errors everywhere. Some are only warnings for full worlds. Some should not apply to modules.

`GENERATED_WORLD` may not have full tests until Phase 8.

#### Task acceptance criteria

- Validation context enum/model exists.
- Rules can declare applicable contexts.
- Strict mode behavior can differ by context.
- `ASSEMBLY` context is documented.
- `GENERATED_WORLD` is defined but marked Phase-8-testable.

---

### Task 6.2: Refactor validation rule execution

#### Task description

Update validation execution so rules are selected and interpreted by context.

#### Task technical description

The validator should:

```text
receive validation_context
select applicable rules
execute selected rules
apply context-specific severity
apply strict failure logic after severity mapping
return structured report
```

Example:

```text
NoResourcesWarningRule:
    MODULE: not applicable or INFO
    ASSEMBLY: INFO or WARNING depending profile
    WORLD: WARNING
    GENERATED_WORLD: WARNING/ERROR depending validation profile
```

#### Task notes

Do not hardcode random exceptions. Encode rule applicability.

#### Task acceptance criteria

- Module validation does not fail due to full-world-only warnings.
- Full world validation still catches incomplete runnable worlds.
- Strict mode still works, but context-aware.

---

### Task 6.3: Add assembly validation report

#### Task description

Create a structured report across validation layers.

#### Task technical description

Assembly validation report should include:

```text
catalog_validation
module_validation
composition_validation
assembly_validation
world_validation
summary
blocking_errors
warnings
fingerprints
```

#### Task notes

This report should be written beside the resolved bundle.

#### Task acceptance criteria

- Assembly validation report is generated.
- Report separates validation layers.
- Blocking errors are clearly listed.
- Warnings are preserved even when non-blocking.

---

### Task 6.4: Add validation tests

#### Task description

Add tests for context-specific validation behavior.

#### Task technical description

Tests should cover:

```text
terrain module with no resources passes MODULE validation
final world with no resources produces warning or failure based on profile
duplicate IDs fail module/composition validation
unknown catalog reference fails composition validation
strict mode only fails on context-applicable warnings/errors
```

`GENERATED_WORLD`-specific tests are deferred to Phase 8.

#### Task notes

This phase kills false-positive validation failures.

#### Task acceptance criteria

- Context-specific validation tests exist.
- Strict mode behavior is predictable.
- Existing world validation tests are preserved or intentionally updated.
- `GENERATED_WORLD` test gap is explicitly documented until Phase 8.

---

## Phase 6 Acceptance Criteria

- Validation contexts exist.
- Rule applicability is context-aware.
- Module validation no longer behaves like full-world validation.
- Assembly validation report exists.
- Existing strict world validation remains meaningful.
- `GENERATED_WORLD` context is defined but Phase-8 exercised.

---

# Phase 7: Provenance Manifest and Report Integration

## Description

Phase 7 makes resolved content traceable without polluting runtime state.

The sidecar provenance manifest records where regions, entity groups, populations, buildings, resources, and profile-derived values came from.

## Notes

This phase must not add fields to `EntityState`.

Phase 7 validates catalog/module/profile provenance only. Generator-specific provenance fields such as `generator_version` and `generation_step` are defined but populated and tested in Phase 8.

## Tasks

### Task 7.1: Define ProvenanceManifest schema

#### Task description

Define sidecar schema for assembly and compile provenance.

#### Task technical description

The manifest should include:

```text
manifest_id
world_id
source_schema_version
catalog_fingerprint
module_fingerprints
composition_fingerprint
resolver_version
generator_version
seed
created_at
records
```

Records should support:

```text
region_id -> source module / recipe / parameters
population_id -> source module / role / faction / profiles
entity_id range or generated entity group -> source population
building_id -> source module / building profile
resource_node_id -> source module / resource profile
faction_id -> catalog definition
profile_id -> catalog definition
```

#### Task notes

For generated individual entities, avoid huge manifests when possible. Support grouped provenance records where entity ranges come from the same source population.

Generator-specific fields may be empty until Phase 8.

#### Task acceptance criteria

- `ProvenanceManifest` schema exists.
- It supports regions, populations/entities, resources, buildings, factions, and profiles.
- It can represent grouped entity provenance.
- It does not require `EntityState` changes.
- Generator fields can exist but remain optional until Phase 8.

---

### Task 7.2: Generate provenance during assembly

#### Task description

Make the resolver emit provenance records while producing the clean `WorldSpec`.

#### Task technical description

The resolver should record:

```text
which module contributed each region
which module/profile contributed each population
which catalog faction/role/profile each reference resolved to
which parameters affected each merged contribution
which defaults were applied when explicit profiles were missing
```

#### Task notes

Provenance must be deterministic.

Generator provenance is not expected to be populated yet.

#### Task acceptance criteria

- Provenance is emitted during assembly.
- Provenance links module/catalog/profile decisions to resolved world objects.
- Same input and seed produce same provenance.
- Generator-specific provenance is explicitly marked as pending Phase 8.

---

### Task 7.3: Integrate compile report with resolved bundle

#### Task description

Preserve compiler reports and attach them to the resolved bundle output path.

#### Task technical description

Resolved bundle output should include:

```text
assembly_report.json
validation_report.json
provenance_manifest.json
compile_report.json
```

The compile report should reference:

```text
resolved world fingerprint
provenance manifest path
catalog fingerprint
module fingerprints
state hash
```

#### Task notes

Do not require full observability warehouse integration yet. First make artifacts stable.

#### Task acceptance criteria

- Compile report is stored beside resolved bundle.
- Compile report references provenance manifest.
- State hash and world fingerprint are preserved.
- Existing compile report behavior is not broken.

---

## Phase 7 Acceptance Criteria

- `ProvenanceManifest` exists.
- Provenance is sidecar-only.
- Resolver emits module/catalog/profile provenance.
- Compile report is preserved with resolved artifacts.
- No `EntityState` structural change is required.
- Generator provenance fields are reserved for Phase 8.

---

# Phase 8: Simple Procedural Generation Foundation

## Description

Phase 8 introduces simple procedural generation after catalog, modules, resolver, validation, and provenance exist.

This phase creates a replaceable generator contract. It supports basic terrain, region, and placement generation only.

## Notes

Procedural generation is not the core feature. World assembly is the core feature.

Generator output must become a normal resolved `worldspec.v1` and pass validation.

## Tasks

### Task 8.1: Define GenerationIntentSpec

#### Task description

Create a schema for high-level generation intent.

#### Task technical description

Generation intent should support:

```text
generation_id
seed
target_world_size
terrain_style
settlement_style
danger_level
resource_density
population_scale
required_modules
constraints
budget_profile
```

#### Task notes

Do not support arbitrary procedural scripts.

#### Task acceptance criteria

- `GenerationIntentSpec` exists.
- It is deterministic by seed.
- It references modules/catalog definitions instead of embedding logic.

---

### Task 8.2: Implement basic terrain and region generator

#### Task description

Add simple generation for region shapes and terrain placement.

#### Task technical description

Supported generation should include:

```text
rectangular regions
simple irregular bounds if already supported safely
terrain assignment
region adjacency hints
region size limits
spawn-safe region marking
```

#### Task notes

Keep this intentionally simple. Do not attempt advanced roguelike generation yet.

#### Task acceptance criteria

- Generator creates valid regions.
- Same seed produces same region layout.
- Generated regions pass validation.
- Region output can be traced in provenance.

---

### Task 8.3: Implement simple placement generators

#### Task description

Generate simple placements for buildings, resources, and population groups.

#### Task technical description

Supported placement:

```text
resource count by density
building slots inside settlement regions
population groups by region
spawn distribution references
basic distance/bounds checks
```

#### Task notes

Generated results must remain budget-bounded.

#### Task acceptance criteria

- Generated resources stay inside valid regions.
- Generated buildings stay inside valid regions.
- Generated populations reference valid spawn regions.
- Generated world passes generated-world validation.

---

### Task 8.4: Add generator determinism tests

#### Task description

Prove generator stability.

#### Task technical description

Tests should verify:

```text
same seed + same input = same WorldSpec fingerprint
same seed + same input = same provenance fingerprint
different seed may change layout
generated world validates
generated world compiles
```

#### Task notes

Use deterministic RNG patterns. Do not introduce global random usage into runtime paths.

#### Task acceptance criteria

- Determinism tests exist.
- Generated world fingerprint is stable for same seed.
- Generated world compiles.
- Runtime engine remains unaffected.

---

## Phase 8 Acceptance Criteria

- `GenerationIntentSpec` exists.
- Simple terrain/region generation exists.
- Simple placement generation exists.
- Generated output becomes clean `worldspec.v1`.
- Generated worlds are deterministic and validated.
- Generator-specific provenance is populated and tested.

---

# Phase 9: Compiler Integration Hardening

## Description

Phase 9 reduces compiler hardcoding by routing compile-time defaults through resolved profiles and semantic services.

This is not a compiler rewrite. It makes the compiler consume resolved compile context instead of owning content defaults.

## Notes

`WorldCompiler` consumes:

```text
WorldSpec
optional CompileContext
```

It must not know:

```text
module files
catalog files
generation intent
composition schema
```

## Tasks

### Task 9.1: Define CompileContext

#### Task description

Create a compile-time context object that carries resolved profiles and semantic mappings.

#### Task technical description

`CompileContext` should include:

```text
resolved entity profiles by population/entity group
resolved building profiles
resolved resource profiles
resolved faction economy profiles
resolved region ownership decisions
legacy faction mapping
legacy role mapping
provenance manifest reference
```

#### Task notes

`CompileContext` is optional for backward compatibility.

#### Task acceptance criteria

- `CompileContext` exists.
- `WorldCompiler` can accept no context and preserve current defaults.
- `WorldCompiler` can accept context and use resolved values.

---

### Task 9.2: Move entity defaults behind CompileContext

#### Task description

Replace hardcoded entity combat defaults where context is available.

#### Task technical description

Compiler should use resolved profile values for:

```text
hp
max_hp
atk
def_stat
attack_range
readiness
```

Fallback behavior must preserve current output when no context exists.

#### Task notes

This is the highest-value compiler cleanup because population profile fields should visibly affect compiled entities.

#### Task acceptance criteria

- Profile-backed compile path uses resolved entity stats.
- No-context compile path remains compatible.
- Tests cover both paths.

---

### Task 9.3: Move resource/building/faction defaults behind CompileContext

#### Task description

Replace additional compiler hardcoded defaults where context is available.

#### Task technical description

Move these behind context-aware resolution:

```text
resource required_ticks
building hp / max_hp
town owner faction
faction starting gold
```

#### Task notes

Do this after entity defaults. It has broader impact.

#### Task acceptance criteria

- Resource `required_ticks` can come from resolved profile.
- Building durability can come from resolved profile.
- Faction starting gold can come from resolved economy profile.
- Region ownership can come from resolved semantics.
- Legacy fallback remains stable.

---

### Task 9.4: Add compiler compatibility tests

#### Task description

Ensure old and new compilation paths both remain safe.

#### Task technical description

Tests should cover:

```text
old WorldSpec compile without CompileContext
old WorldTemplate expansion and compile
composition-resolved WorldSpec compile with CompileContext
state hash stability for same input
profile effect on compiled state
legacy fallback behavior
```

#### Task notes

This phase is allowed to update tests, but not by weakening them.

#### Task acceptance criteria

- Existing worldbuilding compile tests pass.
- New context-backed compile tests pass.
- Same resolved input produces same state hash.
- Compiler does not import catalog/module/generator repositories.

---

## Phase 9 Acceptance Criteria

- `CompileContext` exists.
- Compiler hardcoded defaults are reduced.
- Existing compile behavior remains compatible.
- Profile-backed compilation works.
- Compiler boundary remains clean.

---

# Phase 10: Observability Join and Migration Cleanup

## Description

Phase 10 connects world assembly provenance to observability and cleans up migration debt.

This should not be attempted before sidecar artifacts and compile reports are stable.

## Notes

Keep provenance query-side. Do not affect tick execution.

## Tasks

### Task 10.1: Register resolved world artifacts with run records

#### Task description

Make simulation runs aware of the resolved world artifact set.

#### Task technical description

A run should be able to reference:

```text
resolved_world_path
provenance_manifest_path
assembly_report_path
validation_report_path
compile_report_path
catalog_fingerprint
module_fingerprints
state_hash
```

#### Task notes

Do not load full provenance into runtime state.

#### Task acceptance criteria

- Run record can reference resolved world artifacts.
- Artifacts are discoverable after a run.
- Runtime state remains unchanged.

---

### Task 10.2: Add observability provenance lookup

#### Task description

Allow analysis tools to join behavior/events with source module/catalog/profile metadata.

#### Task technical description

Analysis should support questions like:

```text
which module produced this entity group?
which profile produced this entity's stats?
which faction definition applied?
which seed/layout produced this region?
which module produced unstable behavior?
```

This should be done through sidecar lookup, not runtime mutation.

#### Task notes

Keep this query-side.

#### Task acceptance criteria

- Analysis can resolve entity/group provenance from sidecar.
- Analysis can resolve region/building/resource provenance.
- Runtime behavior is unchanged.

---

### Task 10.3: Mark legacy adapters and migration debt

#### Task description

Make remaining compatibility adapters explicit.

#### Task technical description

Mark these as migration surfaces:

```text
get_faction_enum direct use
get_role_enum direct use
direct Faction.HERO_GUILD checks
direct Faction.MONSTER_HORDE checks
compiler fallback defaults
```

Add documentation showing:

```text
current use
desired replacement
migration risk
whether replacement is required now
```

#### Task notes

Do not remove all legacy adapters yet. Remove only when consumers have migrated safely.

#### Task acceptance criteria

- Migration debt is documented.
- Legacy adapter usage is intentional.
- No hidden direct enum checks are added in new world assembly code.

---

## Phase 10 Acceptance Criteria

- Run records reference resolved world artifacts.
- Observability can join against provenance sidecar.
- Migration debt is documented.
- Runtime engine remains decoupled from world assembly and generation.

---

# Phase Dependency Summary

```text
Phase 0 must happen first.

Phase 1 creates the catalog schema, repository, and base catalog.

Phase 2 depends on Phase 1 and builds content_semantics on top of catalog lookup APIs.

Phase 3 depends on Phase 1 and Phase 2 and makes profile fields real through CompileProfileResolver.

Phase 4 creates module schemas and module repository.

Phase 5 depends on Phase 3 and Phase 4 and creates composition plus structural resolver.

Phase 6 adds context-aware validation and upgrades strict-mode behavior.

Phase 7 adds sidecar provenance and report integration for module/catalog/profile provenance.

Phase 8 adds simple procedural generation and populates generator-specific provenance.

Phase 9 hardens compiler integration through CompileContext.

Phase 10 connects provenance to observability and cleans migration debt.
```

Do not move Phase 8 earlier. Procedural generation before resolver, validation, and provenance is premature.

---

# Recommended Execution Focus

## First implementation batch

```text
Phase 0
Phase 1
Phase 2
Phase 3
```

Reason: this establishes catalog, semantics, and profile consumption. It removes dead profile fields and gives future module/generation work a stable foundation.

## Second implementation batch

```text
Phase 4
Phase 5
Phase 6
Phase 7
```

Reason: this establishes module composition, structural assembly, context-aware validation, and provenance artifacts.

## Third implementation batch

```text
Phase 8
Phase 9
Phase 10
```

Reason: this adds simple generation, hardens compiler integration, and connects provenance to observability after the foundation is stable.

---

# Key Failure Modes To Avoid

## Failure mode 1: Resolver becomes validator

The resolver assembles. It should not own full-world content validation. Phase 5 structural validation is allowed. Full context-aware validation belongs in Phase 6.

## Failure mode 2: YAML becomes fake code

Data should declare meaning, not executable behavior.

## Failure mode 3: Compiler becomes content registry

`WorldCompiler` should not load catalogs, modules, or generation input. It should receive a clean `WorldSpec` plus optional `CompileContext`.

## Failure mode 4: Provenance pollutes runtime state

Do not add provenance fields to `EntityState` in this track. Use sidecar manifests.

## Failure mode 5: Quest seeds sneak into v1 module schema

Quest seeds are deferred. Do not add half-designed quest module fields to the first version.

## Failure mode 6: Procedural generation starts too early

Generation must come after catalog, modules, resolver, validation, and provenance. Otherwise it will be built on unstable schema boundaries.

---

# Final Implementation Principle

The correct abstraction is not:

```text
YAML -> Compiler -> Runtime
```

The correct abstraction is:

```text
Catalog + Modules + Composition + Optional Generation
    -> WorldAssemblyResolver
    -> ResolvedWorldBundle
        -> clean worldspec.v1
        -> provenance sidecar
        -> validation report
        -> assembly report
    -> WorldCompiler + optional CompileContext
    -> AuthoritativeState
    -> Runtime Simulation
```

This is the structure that prevents the future rewrite.
