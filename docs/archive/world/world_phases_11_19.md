---
status: archive
authority: P2
audience: historical
layer: world
original_date: unknown
---

# Next Phases Implementation Plan: Phase 11+

## Current diagnosis

The current implementation has achieved the **foundation layer**, but it has not completed the major feature.

You now have `data/content`, world modules, world assembly, provenance sidecars, context-aware validation, compile context models, procedural generation, and tests around these pieces. But the implementation has two serious unfinished areas:

First, the assembly path is not hard enough yet. `ResolvedWorldBundle` currently carries `world_spec`, `provenance_manifest`, and `assembly_report`, but not the `CompileContext`, even though compile-time profile resolution is the real bridge between module/profile data and the compiler. The current source shows `ResolvedWorldBundle` without `compile_context`.

Second, the runtime simulation content still lives in hardcoded registries. The report correctly identifies a “split-universe architecture”: declarative catalog data exists, but actual gameplay registries for items, enemies, recipes, and adventure regions are still seeded from hardcoded Python data, while tests also use hardcoded presets.

So the next phases must **freeze procedural generation temporarily** and close the catalog/runtime gap first.

---

# Updated phase direction

```text
Phase 11 — Assembly Hardening and CompileContext Integrity
Phase 12 — Resolve CLI, Artifact Contract, and Lab Integration
Phase 13 — Runtime Content Catalog Schema Expansion
Phase 14 — Legacy Runtime Data Export to Catalog
Phase 15 — Runtime Registry Bridge
Phase 16 — Catalog-vs-Legacy Runtime Parity Tests
Phase 17 — Procedural Generation Re-gating
Phase 18 — Observability Provenance Join
Phase 19 — Legacy Deprecation and Cleanup
```

Procedural generation already exists in the latest source, but it was added before the runtime content universe was unified. It should not be expanded until Phases 11–16 are complete. The generator currently builds regions, factions, resources, buildings, populations, provenance, and a clean `WorldSpec`, then validates with `GENERATED_WORLD`; that is useful, but it still depends on incomplete catalog/runtime integration.

---

# Phase 11 — Assembly Hardening and CompileContext Integrity

## Description

This phase fixes the most important gap in the current assembly pipeline: profile references from modules and compositions must survive assembly and become actual compile-time behavior.

The current danger is subtle. A module population recipe may contain `stats_profile`, but if assembly converts it into a clean `PopulationSpec` and drops profile metadata, the final compiler path may silently fall back to role defaults. That means profile fields look supported but are not reliably authoritative.

## Notes

`worldspec.v1` must remain clean. Do **not** add profile/provenance fields into `WorldSpec`.

The correct output is:

```text
ResolvedWorldBundle
    world_spec
    compile_context
    provenance_manifest
    assembly_report
    validation_report
```

`CompileContext` is the bridge, not `WorldSpec`.

## Phase acceptance criteria

```text
- ResolvedWorldBundle includes CompileContext.
- Explicit module profile references affect compiled entity stats.
- Clean worldspec.v1 remains unchanged.
- WorldAssemblyResolver does not duplicate profile-resolution logic.
- Resolver, validator, and report responsibilities are separated or at least cleanly staged.
- Existing legacy compile behavior still works without CompileContext.
```

---

## Task 11.1 — Add CompileContext to ResolvedWorldBundle

### Task description

Extend the resolved assembly output so it contains the compile-ready context.

### Task technical description

`ResolvedWorldBundle` should carry:

```text
world_spec: WorldSpec
compile_context: CompileContext
provenance_manifest: ProvenanceManifest
assembly_report: dict
validation_report: dict | optional
```

`compile_context` should include resolved entity, building, resource, faction economy, region ownership, and legacy enum mappings.

The compiler must still accept:

```text
WorldCompiler.compile(world_spec)
```

for legacy paths, and:

```text
WorldCompiler.compile(world_spec, context=bundle.compile_context)
```

for resolved assembly paths.

### Task notes

Do not make `WorldCompiler` load `CatalogRepository`, `WorldModuleRepository`, or `WorldCompositionSpec`.

### Task acceptance criteria

```text
- bundle.compile_context exists.
- bundle.world_spec remains schema_version == "worldspec.v1".
- WorldCompiler can compile bundle.world_spec with bundle.compile_context.
- Existing tests that compile without context still pass.
```

---

## Task 11.2 — Preserve explicit profile references through assembly

### Task description

Make explicit module-level profile references authoritative.

### Task technical description

When module population recipes include:

```text
stats_profile
inventory_profile
cognition_profile
```

assembly must not lose them when creating clean `PopulationSpec`.

Instead, the resolver should use those recipe fields before stripping them from the final `WorldSpec`.

Resolution priority should be:

```text
1. explicit recipe/module profile
2. role default profile
3. faction/type default profile if applicable
4. global default compile profile
```

The resolved values go into `CompileContext`.

### Task notes

This is not optional. Without this, profile fields remain half-dead.

### Task acceptance criteria

```text
- A module with stats_profile = "elite_guard" produces elite stats in CompileContext.
- The clean WorldSpec does not contain stats_profile.
- Compiled EntityState reflects the explicit stats profile.
- A test proves explicit profile beats role default.
```

---

## Task 11.3 — Split assembly stages internally

### Task description

Prevent `WorldAssemblyResolver` from becoming an all-in-one god object.

### Task technical description

The pipeline should be staged conceptually:

```text
WorldAssemblyResolver
    load modules
    sort modules
    merge structural contributions
    produce draft world data

WorldAssemblyValidator
    run catalog/module/composition/assembly/world validation

WorldAssemblyReportBuilder
    build assembly_report and validation_report

CompileProfileResolver
    build CompileContext
```

You can keep a facade method like:

```text
assemble(composition) -> ResolvedWorldBundle
```

But internally, the responsibilities must be separable.

### Task notes

This matters because procedural generation, validation, provenance, and lab integration will all attach here later. If `WorldAssemblyResolver` owns everything, the next change will become messy.

### Task acceptance criteria

```text
- Resolver logic is not responsible for every validation/report detail.
- Structural assembly can be tested separately from validation.
- Validation report generation can be tested separately.
- CompileProfileResolver remains the only profile-resolution owner.
```

---

## Task 11.4 — Clarify module `requires` / `provides` semantics

### Task description

Define whether `requires` means module IDs or provided capabilities.

### Task technical description

Current examples imply `requires` is a module ID dependency: `standard_villagers` requires `plains_layout`, while `plains_layout` provides `baseline_layout`. That means `provides` is currently descriptive, not dependency-driving.

For now, choose:

```text
requires = module IDs
provides = descriptive tags / capabilities for documentation and future use
```

Rename later if needed:

```text
requires_modules
provides_tags
```

or document the current names explicitly.

### Task notes

Do not implement capability-based dependency resolution unless you are ready to enforce it fully.

### Task acceptance criteria

```text
- Module dependency rules are documented.
- Tests prove requires uses module_id dependencies.
- provides is either documented as metadata or enforced properly.
- No ambiguous mixed behavior remains.
```

---

## Task 11.5 — Fix provenance determinism model

### Task description

Separate deterministic identity from operational timestamps.

### Task technical description

Do not make full provenance JSON byte-identical by hardcoding timestamps for test IDs.

Use:

```text
content_fingerprint: deterministic
created_at: operational timestamp, allowed to vary
```

Tests should assert deterministic fingerprints and deterministic content fields, not full JSON equality including `created_at`.

### Task notes

The current `_test` timestamp hack hides real non-determinism.

### Task acceptance criteria

```text
- Provenance manifest has deterministic content_fingerprint.
- created_at may vary without breaking determinism tests.
- Tests compare deterministic fields/fingerprints, not operational timestamps.
```

---

# Phase 12 — Resolve CLI, Artifact Contract, and Lab Integration

## Description

This phase makes the assembly pipeline usable as a real workflow.

Right now, the architecture expects a clear resolve step:

```text
worldcomposition.v1 -> resolved/world.resolved.yaml + sidecars
```

But the workflow is not strong enough until there is a first-class resolve command and artifact contract.

## Notes

Do not let `compile` silently resolve and hide side effects.

A composition source is not compiler-ready. It must be resolved first or explicitly resolved as part of a visible command.

## Phase acceptance criteria

```text
- There is a first-class resolve workflow.
- Resolved artifacts are written to disk.
- Compile can consume resolved artifacts.
- Lab orchestration can reference resolved artifact paths.
- Composition source is never passed directly to WorldCompiler.
```

---

## Task 12.1 — Add explicit resolve command/workflow

### Task description

Add a user-visible command or workflow for resolving a composition world.

### Task technical description

Command shape:

```text
rpg-world resolve <world_id>
```

or equivalent.

It should:

```text
load worldcomposition.v1
load catalog
load modules
assemble ResolvedWorldBundle
run validation
write resolved artifacts
```

### Task notes

Do not overload `compile` as the only entry point.

### Task acceptance criteria

```text
- resolve command exists.
- resolve fails clearly on invalid composition.
- resolve writes all expected artifacts.
- resolve does not run simulation.
```

---

## Task 12.2 — Define resolved artifact contract

### Task description

Standardize the resolved output layout.

### Task technical description

Expected output:

```text
data/worlds/<world_id>/resolved/world.resolved.yaml
data/worlds/<world_id>/resolved/compile_context.json
data/worlds/<world_id>/resolved/provenance_manifest.json
data/worlds/<world_id>/resolved/assembly_report.json
data/worlds/<world_id>/resolved/validation_report.json
```

Optional after compile:

```text
data/worlds/<world_id>/resolved/compile_report.json
```

### Task notes

`compile_context.json` is important. Without it, resolved worlds lose profile semantics when compiled later.

### Task acceptance criteria

```text
- Artifact paths are documented.
- resolve writes clean worldspec.v1 YAML.
- resolve writes compile context.
- resolve writes provenance and reports.
- Artifacts can be loaded back without source composition.
```

---

## Task 12.3 — Compile from resolved bundle

### Task description

Allow compilation to use resolved artifacts.

### Task technical description

The compile workflow should support:

```text
compile <world_id> --from-resolved
```

or automatically detect the resolved artifact if the indexed source is `worldcomposition.v1`.

The compile path must load:

```text
world.resolved.yaml
compile_context.json
```

Then call:

```text
WorldCompiler.compile(world_spec, context=compile_context)
```

### Task notes

If `compile_context.json` is missing, fail loudly or require `--legacy-fallback`. Do not silently compile with wrong defaults.

### Task acceptance criteria

```text
- Resolved world compiles with CompileContext.
- Missing CompileContext causes a controlled error unless fallback is explicit.
- Compile report references resolved artifact paths.
```

---

## Task 12.4 — Lab orchestrator resolved-world awareness

### Task description

Make lab execution aware of resolved world artifacts.

### Task technical description

When a scenario points to a world whose source is `worldcomposition.v1`, the lab orchestrator should either:

```text
1. require resolved artifacts to exist
```

or:

```text
2. trigger resolve explicitly and record that resolution occurred
```

The run manifest should record:

```text
source_world_path
resolved_world_path
compile_context_path
provenance_manifest_path
assembly_report_path
validation_report_path
compile_report_path
catalog_fingerprint
module_fingerprints
```

### Task notes

Do not load provenance into runtime state.

### Task acceptance criteria

```text
- Lab run manifest references resolved artifacts.
- Lab execution does not bypass the resolve step.
- Artifact paths are available for later analysis.
```

---

# Phase 13 — Layered Content Catalog Schema Expansion

## Description
This phase extends the content catalog schemas to adopt the Layered World Data Direction. We define foundational layers (materials, traits, themes, relationship axes, attributes), living profiles (races, need profiles, sense profiles, drive profiles, cognition profiles), and entity/social construction layers (archetypes, perspectives, faction relationships) in the Python schemas.

## Phase acceptance criteria
- `RaceDefinition`, `MaterialDefinition`, `TraitDefinition`, `ThemeDefinition`, `RelationshipAxisDefinition`, and `AttributeDefinition` exist in `src/content/schema.py`.
- `NeedProfileDefinition`, `SenseProfileDefinition`, `DriveProfileDefinition`, `CognitionProfileDefinition`, and `SkillProfileDefinition` exist.
- `PerspectiveDefinition` and `FactionRelationshipDefinition` exist.
- `EntityArchetypeDefinition` exists, replacing the flat `EnemyDefinition`.
- `LegacyEnemyProjectionDefinition` exists to map archetypes back to legacy runtime models.
- `CatalogRepository` is updated to load all layered directories/files from `data/content/`.
- `CatalogValidator` validates cross-references across these layered models.

---

## Task 13.1 — Add Layered Pydantic Definitions
Add all the new schemas (Race, Material, Trait, Theme, RelationshipAxis, Attribute, Profiles, Perspectives, FactionRelationships, Archetypes, and LegacyEnemyProjection) to `src/content/schema.py`.

## Task 13.2 — Update CatalogRepository to load layered layout
Modify `CatalogRepository` in `src/content/repository.py` to recursively load all files under `data/content/` (including subdirectories `foundation`, `living`, `social`, `entities`, `world`, etc.), build the appropriate indexes, and compute a deterministic fingerprint of the entire catalog.

## Task 13.3 — Implement Relational Validation Checks in CatalogValidator
Extend `CatalogValidator` in `src/content/validator.py` to ensure all relational connections validate:
- Entity archetypes reference existing races, factions, roles, profiles, traits, and themes.
- Faction relationships reference valid source/target factions.
- Perspectives reference valid chosen factions.
- Legacy enemy projections reference valid archetypes, items, and regions.
- Recipes and regions reference valid items/archetypes/services.

---

# Phase 14 — Adopting Layered Catalog and Populating Baseline Profiles

## Description
Copy the designed YAML files from `new_data_design/` to `data/content/` (overwriting and reorganizing the catalog directory structure) and populate all necessary baseline profiles (combat, cognition, needs, senses) for all races and archetypes.

## Phase acceptance criteria
- `data/content/` contains all the new layered configuration files.
- All empty lists in `profiles/combat.yaml` and `profiles/cognition.yaml` are replaced with full definitions for all standard classes and animals.
- `CatalogRepository` successfully loads the entire directory structure.
- `CatalogValidator` validates the entire catalog with zero errors.

---

# Phase 15 — Runtime Registry Bridge with Legacy Projection

## Description
Implement a translation bridge in `src/core/registries.py` that loads the catalog database and uses the `LegacyEnemyProjectionDefinition` + `EntityArchetypeDefinition` + `StatProfileDefinition` to dynamically construct and seed the legacy runtime registries (`EnemyRegistry`, `ItemRegistry`, `RecipeRegistry`, `RegionRegistry`, `ServiceRegistry`).

## Phase acceptance criteria
- `seed_phase1_content()` can load directly from `CatalogRepository`.
- It uses the `LegacyEnemyProjection` to reconstruct legacy `EnemyDef` objects.
- It maps items, recipes, regions, and services dynamically from the catalog.
- Legacy hardcoded backup seeding still exists but can be completely bypassed in catalog mode.
- Existing gameplay systems querying the registries query the projected values successfully.

---

## Task 15.1 — Implement Registry Adapter Mapping & Projection
### Task description
Convert catalog definitions to legacy `ItemDef`, `EnemyDef`, `RecipeDef`, `RegionDef`, and `ServiceDef` dataclasses inside `src/core/registries.py`.

### Task technical description
Write a mapper function that joins `LegacyEnemyProjectionDefinition` with `EntityArchetypeDefinition` (getting HP, Atk, Def from the linked `StatProfileDefinition`) to populate `EnemyDef`. Map `RecipeDefinition` list ingredients to the `RecipeDef` input dict and ensure exactly one output exists. Extract the first category in `categories` as `use_kind` for `ItemDef`.

---

## Task 15.2 — Bootstrap for ItemRegistry in core/items.py
### Task description
Allow `ItemRegistry` in `src/core/items.py` to be populated dynamically from the Content Catalog.

### Task technical description
Add `bootstrap(cls, data: Dict[str, ItemDefinition])` to `src/core/items.py`'s `ItemRegistry` class. When catalog seeding is active, map dynamic `ItemDefinition` catalog items into this registry, converting string categories to the correct `ItemKind` and `EquipSlot` enums (e.g., mapping category `"weapon"` to `ItemKind.WEAPON` and `"melee"` or `"magic"` or `"ranged"` to properties like weapon slots). Ensure properties (like `atk_bonus`, `def_bonus`, `heal_amount`) match the expected keys so that existing equipment/inventory logic works flawlessly.

---

## Task 15.3 — Update seed_phase1_content to support catalog bootstrapping
### Task description
Connect the catalog repository to the registries seeding pipeline.

### Task technical description
Modify `seed_phase1_content(catalog_repo: Optional[CatalogRepository] = None)` to optionally bootstrap all registries dynamically when `catalog_repo` is supplied. Log which content source was used (`catalog` vs `legacy_hardcoded`). Make fallback behavior observable.

---

## Task 15.4 — Keep fallback visible, not invisible
### Task description
Make fallback behavior observable in tests and runtime logs.

### Task technical description
When catalog-backed seeding fails or is unavailable, log:
`runtime_content_source = "legacy_hardcoded"`
When catalog-backed seeding succeeds, log:
`runtime_content_source = "catalog"`
`catalog_fingerprint = ...`

---

# Phase 16 — Catalog-vs-Legacy Runtime Parity Tests

## Description
## Task 16.1 — Registry content parity tests

### Task description

Compare registry contents between legacy and catalog modes.

### Task technical description

Compare:

```text
item count
enemy count
recipe count
region count
item IDs
enemy IDs
recipe IDs
region IDs
```

Then compare key fields:

```text
item category / rarity / base value
enemy max_hp / atk / def / danger / loot
recipe ingredients / outputs / service / gold cost
region tags / danger level
```

### Task notes

Do not compare only counts. Counts can match while data is wrong.

### Task acceptance criteria

```text
- Legacy and catalog item data match.
- Legacy and catalog enemy data match.
- Legacy and catalog recipe data match.
- Legacy and catalog runtime region data match.
```

---

## Task 16.2 — Cross-reference behavior tests

### Task description

Verify that catalog-backed content supports the same downstream behaviors.

### Task technical description

Test these flows in catalog mode:

```text
enemy drops valid loot
crafting recipe consumes valid ingredients
crafting recipe produces valid outputs
service requirement can be resolved
inventory profile starting items exist
spawn region references exist
```

### Task notes

These tests catch invalid but parseable YAML.

### Task acceptance criteria

```text
- Loot references resolve.
- Recipe references resolve.
- Inventory references resolve.
- Service references resolve.
- Spawn/adventure region references resolve.
```

---

## Task 16.3 — Simulation smoke test in catalog mode

### Task description

Run a minimal simulation using catalog-seeded registries.

### Task technical description

Use a small deterministic scenario:

```text
seed catalog runtime content
compile resolved world
run small tick count
assert no hard-law violations
assert basic registry-backed systems can operate
```

### Task notes

Keep it small. This is a smoke test, not a balance test.

### Task acceptance criteria

```text
- Simulation starts with catalog-backed registries.
- No registry lookup errors occur.
- No hard-law violations caused by missing content.
- Test is deterministic.
```

---

## Task 16.4 — Legacy fallback tests

### Task description

Prove fallback still works, but only when explicitly expected.

### Task technical description

Test:

```text
missing catalog -> legacy fallback works
invalid catalog -> controlled failure or explicit fallback depending mode
strict catalog mode -> invalid catalog fails, no fallback
```

### Task notes

You need two modes:

```text
catalog_required = true
catalog_optional = true
```

### Task acceptance criteria

```text
- Optional mode can fallback.
- Required mode fails on missing/invalid catalog.
- Fallback is visible in bootstrap report.
```

---

# Phase 17 — Procedural Generation Re-gating

## Description

This phase repairs and re-gates procedural generation after catalog/runtime unification.

The current procedural generator should be treated as a prototype until it can generate against the unified catalog and resolved artifact contract.

## Notes

Do not expand generation complexity. First make it respect the new contracts.

## Phase acceptance criteria

```text
- Generator outputs ResolvedWorldBundle with CompileContext.
- Generator uses catalog definitions for resources/buildings/populations.
- Generator provenance uses deterministic fingerprinting.
- Generated world can compile with CompileContext.
- Generated world can run with catalog-backed runtime registries.
```

---

## Task 17.1 — Make generator emit CompileContext

### Task description

Update procedural generation output to include compile context.

### Task technical description

Generated populations/resources/buildings should pass through the same `CompileProfileResolver` path as module assembly.

Output:

```text
ResolvedWorldBundle(
    world_spec=...,
    compile_context=...,
    provenance_manifest=...,
    assembly_report=...,
    validation_report=...
)
```

### Task notes

No special generator-only compile path.

### Task acceptance criteria

```text
- Generated bundle includes CompileContext.
- Generated world compiles with context.
- Generated world no longer relies only on compiler fallbacks.
```

---

## Task 17.2 — Replace hardcoded generated content IDs with catalog-driven selection

### Task description

Make generator choose content from catalog and modules instead of hardcoded IDs where possible.

### Task technical description

Current generator-style IDs like:

```text
villagers
monsters
wood
iron
shop
town_hall
```

should be selected through catalog/module constraints.

The generator can still use defaults, but defaults should come from catalog definitions.

### Task notes

Hardcoded baseline IDs are acceptable only as named default presets, not buried inside generator logic.

### Task acceptance criteria

```text
- Generator validates selected faction IDs against catalog.
- Generator validates selected resource/building IDs against catalog.
- Generator fails clearly on missing required catalog definitions.
```

---

## Task 17.3 — Rework generator determinism tests

### Task description

Update generator determinism tests to use deterministic fingerprints, not full JSON with timestamps.

### Task technical description

Assert:

```text
same input + seed -> same world fingerprint
same input + seed -> same provenance content_fingerprint
different seed -> allowed structural difference
```

Do not assert byte-identical `created_at`.

### Task notes

This aligns generator testing with Phase 11 provenance changes.

### Task acceptance criteria

```text
- Determinism tests do not rely on fake timestamps.
- Generator fingerprints are stable.
- Different seed test remains meaningful.
```

---

## Task 17.4 — Generated runtime smoke test

### Task description

Run a generated world with catalog-backed runtime registries.

### Task technical description

Flow:

```text
load catalog
seed runtime registries from catalog
generate world
compile generated world with CompileContext
run small simulation
assert no missing registry content
```

### Task notes

This is the point where procedural generation becomes legitimate again.

### Task acceptance criteria

```text
- Generated world compiles and runs under catalog-backed runtime.
- No missing item/enemy/recipe/region lookup errors occur.
- Provenance and compile reports are produced.
```

---

# Phase 18 — Observability Provenance Join

## Description

This phase connects resolved world provenance with post-run analysis.

The goal is to answer not only “what happened,” but “which content/module/profile caused it.”

## Notes

Do not put provenance into `EntityState`.

Join through sidecar artifacts and run manifests.

## Phase acceptance criteria

```text
- Run records reference provenance manifests.
- Analysis can join entity/region/resource/building IDs to provenance.
- Reports can group findings by module, profile, faction, and generator seed.
```

---

## Task 18.1 — Register provenance artifacts in run manifests

### Task description

Record resolved artifacts in lab run metadata.

### Task technical description

Add fields or metadata for:

```text
resolved_world_path
compile_context_path
provenance_manifest_path
assembly_report_path
validation_report_path
compile_report_path
runtime_content_source
catalog_fingerprint
module_fingerprints
```

### Task notes

This builds on Phase 12.

### Task acceptance criteria

```text
- Run manifest contains resolved artifact references.
- Analysis tools can locate provenance from a run ID.
```

---

## Task 18.2 — Add provenance lookup service

### Task description

Create a query-side service for provenance lookup.

### Task technical description

Support lookups:

```text
entity_id or population_id -> source module/profile/faction/role
region_id -> source module/generator step
resource_id -> source module/resource profile
building_id -> source module/building profile
```

### Task notes

This service reads sidecars. It does not affect runtime simulation.

### Task acceptance criteria

```text
- Provenance lookup works from manifest path.
- Missing provenance is handled gracefully.
- Lookup service is covered by unit tests.
```

---

## Task 18.3 — Add provenance-aware analysis grouping

### Task description

Let investigation reports group anomalies by source content.

### Task technical description

Examples:

```text
NavigationStuck by source_module
CombatNeverEnds by enemy profile
ResourceCrowding by resource module
Economy issues by service/recipe profile
```

### Task notes

This is where your observability starts paying off.

### Task acceptance criteria

```text
- At least three analysis views use provenance grouping.
- Reports identify source module/profile where possible.
- Unknown provenance is reported explicitly, not hidden.
```

---

# Phase 19 — Legacy Deprecation and Cleanup

## Description

This phase removes ambiguity after catalog-backed runtime mode is proven.

Do not do this before Phases 15–16 pass.

## Notes

The goal is not to delete all legacy paths immediately. The goal is to prevent hidden fallback from becoming permanent.

## Phase acceptance criteria

```text
- Catalog-backed mode is default for new workflows.
- Legacy fallback is explicitly marked compatibility-only.
- New tests use catalog mode unless specifically testing fallback.
- Hardcoded content maps are isolated and scheduled for removal.
```

---

## Task 19.1 — Mark legacy registry data as compatibility fallback

### Task description

Make legacy hardcoded content visibly non-authoritative.

### Task technical description

Add documentation and code comments showing:

```text
legacy hardcoded seed data exists only for compatibility
catalog-backed mode is authoritative for new content
```

### Task notes

Do not delete it yet.

### Task acceptance criteria

```text
- Legacy seed path is documented as fallback.
- New implementation does not add more hardcoded content.
```

---

## Task 19.2 — Switch default development path to catalog mode

### Task description

Make normal dev/test workflows use catalog-backed runtime where safe.

### Task technical description

Update fixtures, CLI, or startup configuration so new world assembly tests and generated world tests use catalog-backed registries by default.

Legacy tests can still opt into fallback mode.

### Task notes

This is a controlled default flip.

### Task acceptance criteria

```text
- New tests default to catalog-backed runtime.
- Legacy fallback tests still exist.
- Missing catalog errors surface early.
```

---

## Task 19.3 — Add hardcoded-content regression guard

### Task description

Prevent new runtime content from being added only in Python.

### Task technical description

Add a test or static check that flags new item/enemy/recipe/region definitions added to hardcoded seed maps without catalog equivalents.

### Task notes

This prevents regression into split-universe architecture.

### Task acceptance criteria

```text
- Hardcoded content without catalog equivalent is flagged.
- Existing legacy exceptions are allowlisted.
- New content must be added to catalog first.
```

---

# Revised dependency order

```text
Phase 11 must happen before any serious generator work.
Phase 12 depends on Phase 11.
Phase 13 can start after Phase 11 design stabilizes.
Phase 14 depends on Phase 13.
Phase 15 depends on Phase 13 and Phase 14.
Phase 16 depends on Phase 15.
Phase 17 depends on Phase 11, Phase 12, Phase 15, and Phase 16.
Phase 18 depends on Phase 12 and Phase 17.
Phase 19 depends on Phase 16.
```

The real blocker chain is:

```text
Assembly hardening
    -> runtime catalog schema expansion
    -> data export
    -> registry bridge
    -> parity tests
    -> procedural generation re-gating
```

---

# Non-negotiable rules for Phase 11+

```text
1. Do not put profile/provenance metadata into worldspec.v1.
2. Do not put provenance into EntityState.
3. Do not let WorldCompiler load catalog/module/generator files.
4. Do not expand procedural generation until runtime catalog parity is proven.
5. Do not silently fallback from catalog mode to legacy mode.
6. Do not let resolver become validator + compiler + reporter + generator.
7. Do not add new hardcoded gameplay content without catalog equivalent.
8. Do not compare determinism using operational timestamps.
```

---

# Priority Plan

## What must change in mindset

You are not finishing “world generation” now. You are finishing **data authority**.

Right now the catalog is not yet the source of truth. It is only a source of compile-time scaffolding. The actual runtime truth still lives in Python registries. That is the issue that must be killed next.

## Immediate actions

Start with Phase 11:

```text
- Add CompileContext to ResolvedWorldBundle.
- Preserve explicit module profile references.
- Split resolver responsibilities.
- Fix provenance determinism.
```

Then do Phase 13–16 before touching generator expansion.

## What to stop

Stop adding procedural generation features while items, enemies, recipes, runtime regions, combat profiles, and cognition profiles are incomplete or hardcoded elsewhere.

## Consequence if you ignore this

You will build a procedural world generator that creates maps and populations, but the real combat, economy, loot, crafting, and adventure behavior will still be controlled by hidden Python data. That is not data-driven simulation. That is a better-looking shell around the same hardcoded core.
