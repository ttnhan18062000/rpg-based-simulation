---
status: archive
authority: P2
audience: historical
layer: world
original_date: unknown
---

# Phase 20 — Content usage contract and test map

## Goal

Define exactly how every `data/content/` component is supposed to be used before changing more logic.

The current design direction says data should form a layered dependency graph: foundation catalogs, profiles, identities, archetypes, populations/regions/ecologies, modules, world compositions, scenarios, and perspectives.

This phase turns that into a concrete implementation contract.

---

## Task 20.1 — Create `ContentUsageMatrix`

### Description

Create a document or generated report that shows the lifecycle of every content family.

### Technical description

For each family, define:

```text
file path
schema class
repository index
validator coverage
resolver component
compile/runtime consumer
test coverage
current state
target state
```

Families to cover:

```text
foundation/*
living/*
social/*
entities/*
world/*
compatibility/*
world_modules/*
world_compositions/*
simulation_scenarios/*
```

### Note

Do not manually describe every data point. Describe the **component family contract**.

Example:

```text
entities/entity_archetypes.yaml
    must be loaded
    must be validated
    must resolve through EntityArchetypeResolver
    must be consumed by PopulationResolver
    must project into CompileContext/runtime entity construction
```

### TDD

Add a lightweight test that fails until the matrix/report exists and contains all declared content families.

Suggested test:

```text
tests/unit/content/test_content_usage_matrix.py
```

### Acceptance checklist

- [x] Matrix includes every current `data/content/` family.
- [x] Each family has a declared schema.
- [x] Each family has a declared validator responsibility.
- [x] Each family has a declared resolver or is explicitly marked design-only.
- [x] Each active family has a declared runtime/compile consumer.
- [x] Compatibility data is clearly marked as adapter-only.
- [x] No active component is described only as “loaded.”

---

## Task 20.2 — Define implementation states

### Description

Standardize data usage states so the team knows whether a file is only parsed, validated, resolved, projected, or consumed.

### Technical description

Use implementation states such as:

```text
LOADED_ONLY
VALIDATED_ONLY
RESOLVED_PARTIALLY
PROJECTED_TO_LEGACY
RUNTIME_AUTHORITATIVE
DESIGN_ONLY
```

These are internal implementation states, separate from YAML comments like:

```yaml
# STATE: EXISTING-LOGIC
# STATE: LEGACY-EXPORT
# STATE: REDESIGNED-CORE
# STATE: ADDITIONAL
# STATE: FUTURE-EXTENSION
# STATE: COMPATIBILITY
```

### Note

YAML state comments explain content maturity.
Implementation states explain engine usage.

### TDD

Add tests that assert no active content family is missing implementation-state classification.

### Acceptance checklist

- [x] Every content family has exactly one implementation state.
- [x] `COMPATIBILITY` content cannot be marked `RUNTIME_AUTHORITATIVE`.
- [x] `REDESIGNED-CORE` content cannot stay `LOADED_ONLY`.
- [x] State report is deterministic.
- [x] Missing state classification fails the test.

---

# Phase 21 — Content family registry and strict load report

## Goal

Make the repository loader explicit and fail-visible.

The review says the loader currently loads many canonical families, but it is still passive and missing files can be treated too quietly.

---

## Task 21.1 — Add `ContentFamilySpec`

### Description

Create a central registry that describes each content family.

### Technical description

Example structure:

```python
ContentFamilySpec(
    family="entities.entity_archetypes",
    path="entities/entity_archetypes.yaml",
    schema=EntityArchetypeDefinition,
    repository_index="entity_archetypes",
    required=True,
    state_policy="active",
)
```

The repository should load based on this registry, not scattered hardcoded file logic.

### Note

This does not change simulation behavior yet. It makes loading auditable.

### TDD

Extend existing catalog tests instead of duplicating them:

```text
tests/unit/content/test_catalog.py
```

Existing `test_base_catalog_loading` already verifies baseline repository loading. Extend it to check family registry coverage.

### Acceptance checklist

- [x] All canonical content families are declared in `ContentFamilySpec`.
- [x] Repository loading uses `ContentFamilySpec`.
- [x] Unknown declared required family fails in strict mode.
- [x] Optional family is reported if absent.
- [x] Ignored files are reported.
- [x] Duplicate family paths fail.
- [x] Existing `test_base_catalog_loading` still passes.

---

## Task 21.2 — Add strict load report

### Description

`CatalogRepository.load_all()` should return or store a load report.

### Technical description

Report should include:

```text
loaded_families
loaded_files
record_counts
missing_required_files
missing_optional_files
ignored_files
duplicate_ids
schema_errors
fingerprint
```

### Note

This gives developers a clear diagnostic before resolver/runtime stages.

### TDD

Add test cases using a temporary catalog:

```text
missing required file
unknown extra file
empty family
duplicate family path
valid minimal catalog
```

### Acceptance checklist

- [x] Load report is available after `load_all()`.
- [x] Load report includes record counts by family.
- [x] Missing required files fail in strict mode.
- [x] Unknown files are reported.
- [x] Empty active families are reported.
- [x] Fingerprint changes when loaded content changes.
- [x] Existing catalog validation tests do not need rewriting.

---

# Phase 22 — Fail-closed schema and authoring-form normalization

## Goal

Prevent meaningful YAML fields from being silently ignored.

The review specifically flags dangerous mismatches such as composition using `modules` while executable schema expects `module_refs`, and module data using v2-like fields while current executable module schema still expects older v1 fields.

---

## Task 22.1 — Add fail-closed schema mode

### Description

All active schemas should reject unknown fields unless they are explicitly allowed under a controlled metadata/extension block.

### Technical description

For Pydantic models:

```python
model_config = ConfigDict(extra="forbid")
```

or equivalent.

For migration-only schemas:

```text
allow unknown fields only under:
metadata
extension
design_notes
```

### Note

This task should not fix all fields. It prevents false confidence.

### TDD

Add schema tests for:

```text
unknown field in active model → fail
unknown field under metadata → allowed if model permits
unknown field in compatibility model → allowed only if declared
```

### Acceptance checklist

- [x] Active schemas fail on unknown top-level fields.
- [x] Migration-only extension fields are explicitly isolated.
- [x] No current active YAML field is silently ignored.
- [x] Error messages include file/family/record ID.
- [x] Existing validator tests still pass after schema updates.

---

## Task 22.2 — Normalize world composition authoring forms

### Description

Support author-friendly composition data while preserving executable schema compatibility.

### Technical description

Current tests use:

```python
WorldCompositionSpec(
    module_refs=[
        ModuleRefSpec(module_id="plains_layout", enabled=True, order=0)
    ]
)
```

New data may use:

```yaml
modules:
  - frontier_village_core
  - wolf_den_near_forest
```

Add a normalizer:

```text
modules shorthand → module_refs structured form
```

### Note

Do not make `WorldCompiler` understand both. Normalize before assembly.

### TDD

Extend `tests/unit/worldassembly/test_assembly.py`.

Add cases:

```text
module_refs existing format still works
modules shorthand normalizes correctly
both modules and module_refs together fail
default_perspectives handled separately, not silently dropped
```

### Acceptance checklist

- [x] Existing `module_refs` tests still pass.
- [x] `modules` shorthand is accepted through normalization.
- [x] Mixed authoring forms fail clearly.
- [x] Unknown composition fields fail clearly.
- [x] Normalized composition is deterministic.
- [x] Provenance fingerprint remains stable for equivalent input.

---

## Task 22.3 — Normalize world module v1/v2 forms

### Description

Add a boundary between old executable module format and proposed lower-layer composition format.

### Technical description

Current module tests use v1-style recipes and region specs.

New module data uses concepts like:

```text
biomes
ecologies
populations
relationships
resources
buildings
services
```

Add:

```text
WorldModuleAuthoringNormalizer
```

Output:

```text
NormalizedWorldModule
```

### Note

Do not rewrite world assembly immediately. First make both forms explicit and fail-closed.

### TDD

Extend world module tests with:

```text
v1 module remains supported
v2 module normalizes to internal contribution
unknown v2 field fails
unsupported module_type fails unless registered
```

### Acceptance checklist

- [x] v1 modules still pass existing tests.
- [x] v2 module fields are not silently ignored.
- [x] Normalizer produces a stable internal model.
- [x] Unsupported module types fail with clear error.
- [x] Module resolver does not run full-world validation on partial modules.

---

# Phase 23 — Global content reference graph and active-data validation

## Goal

Upgrade validation from “broken references in selected rules” to a global component-level proof.

Current tests already cover many broken relational rules, including archetypes, projections, recipes, regions, races, biomes, and ecologies.

This phase builds on that instead of duplicating it.

---

## Task 23.1 — Build `ContentReferenceGraph`

### Description

Create a graph of all content IDs and references.

### Technical description

Node format:

```text
family:id
```

Examples:

```text
race:wolf
trait:territorial
archetype:hungry_wolf
biome:old_mine
module:wolf_den_near_forest
```

Edge format:

```text
source -> target
```

Examples:

```text
archetype:hungry_wolf -> race:wolf
archetype:hungry_wolf -> faction:wild_beast_pack
biome:old_mine -> material:iron_ore
ecology:wolf_den_ecology -> population:wolf_pack_small
```

### Note

This should be generic. Do not hardcode one check per data point.

### TDD

Extend or add near:

```text
tests/unit/content/test_layered_catalog.py
```

because that file already validates layered dependency rules.

### Acceptance checklist

- [x] Graph includes all loaded content records.
- [x] Graph includes all declared references.
- [x] Broken references produce family-aware errors.
- [x] Reverse reference lookup is supported.
- [x] Graph output is deterministic.
- [x] Existing `CAT-REL-*` tests still pass.

---

## Task 23.2 — Add “no dead active data” rule

### Description

Detect active data that is loaded and valid but never consumed by any higher component.

### Technical description

Rule applies to:

```text
EXISTING-LOGIC
LEGACY-EXPORT
REDESIGNED-CORE
```

These must have at least one downstream usage path unless explicitly exempted.

Allowed inactive states:

```text
ADDITIONAL
FUTURE-EXTENSION
DESIGN_ONLY
```

### Note

This is not about deleting unused content. It prevents pretending active content is implemented.

### TDD

Add tests:

```text
active archetype with no population/projection → warning or error
active material with no resource/item/recipe usage → warning or error
active module with no composition → warning
future-extension record unused → allowed
```

### Acceptance checklist

- [x] Active unused records are detected.
- [x] Future/design records may be unused if marked correctly.
- [x] Compatibility records must point to clean source records.
- [x] Errors/warnings include record ID and family.
- [x] No duplicate one-off tests are needed for every record.

---

# Phase 24 — Resolver layer for foundation, living, and social defaults

## Goal

Make lower-layer data actually affect resolved higher-layer data.

The new direction defines race, material, attributes, traits, theme, and relationship axes as foundation layers; entity archetypes should inherit from race, class/profession, faction, stats, cognition, drives, need, inventory, traits, and theme.

---

## Task 24.1 — Add `FoundationResolver`

### Description

Provide validated access to foundation concepts.

### Technical description

Resolver APIs:

```python
resolve_attribute(id)
resolve_material(id)
resolve_trait(id)
resolve_theme(id)
resolve_element(id)
resolve_relationship_axis(id)
```

Also expose batch helpers:

```python
resolve_traits(ids)
resolve_themes(ids)
resolve_materials(ids)
```

### Note

This should not run behavior. It only resolves stable dependency concepts.

### TDD

Use graph validator tests plus unit tests for resolver behavior.

### Acceptance checklist

- [x] Foundation IDs resolve through one component.
- [x] Missing foundation ID fails clearly.
- [x] Batch resolution preserves deterministic order.
- [x] Resolver does not import runtime simulation systems.
- [x] Existing catalog tests still pass.

---

## Task 24.2 — Add `LivingDefaultsResolver`

### Description

Resolve race-level defaults into a reusable bundle.

### Technical description

Input:

```text
race_id
```

Output:

```text
ResolvedLivingDefaults:
    body_model
    need_profile
    sense_profile
    cognition_profile
    drive_profile
    natural_traits
    attribute_tendencies
    compatible_roles
```

### Note

This is the first place where `race` becomes more than a string label.

### TDD

Add tests:

```text
race resolves all default profiles
race natural traits are resolved
race compatible role list is resolved
missing body/need/sense/cognition/drive references fail
```

Reuse existing layered catalog validation where possible; add resolver-specific tests only for behavior not already covered.

### Acceptance checklist

- [x] Race defaults resolve into one object.
- [x] Race does not contain enemy/ally labels.
- [x] Race compatible roles are validated.
- [x] Race natural traits are inherited later by archetypes.
- [x] Missing lower-layer references fail before assembly.

---

## Task 24.3 — Add `SocialDefaultsResolver`

### Description

Resolve role/faction defaults and relationship metadata.

### Technical description

Resolver APIs:

```python
resolve_role_defaults(role_id)
resolve_faction_defaults(faction_id)
resolve_faction_relationship(source, target)
resolve_perspective(perspective_id)
```

### Note

Do not replace existing legacy faction semantics immediately. Add this as the clean path.

### TDD

Extend existing `content_semantics` tests instead of duplicating. Older tests verify bucket mapping; new tests should verify clean resolver behavior separately.

### Acceptance checklist

- [x] Role defaults can be resolved.
- [x] Faction defaults can be resolved.
- [x] Faction relationship records resolve by source/target.
- [x] Perspective records resolve by ID.
- [x] Legacy bucket mapping remains available but is not the clean resolver’s source truth.

---

# Phase 25 — Entity archetype and population resolution

## Goal

Make `entity_archetypes.yaml` and `populations.yaml` the preferred spawn authoring path.

The direction says entity archetype is the first spawnable template, while population recipes instantiate groups from archetypes.

---

## Task 25.1 — Add `ResolvedEntityArchetype`

### Description

Resolve one clean archetype into a compile/runtime-ready entity template.

### Technical description

Input:

```text
EntityArchetypeDefinition
```

Resolution order:

```text
race defaults
+ role defaults
+ faction defaults
+ explicit archetype profiles
+ explicit archetype traits/themes
= ResolvedEntityArchetype
```

Output:

```text
identity:
    archetype_id
    race_id
    faction_id
    role_id

profiles:
    stat_profile
    combat_profile
    cognition_profile
    drive_profile
    need_profile
    sense_profile
    inventory_profile
    skill_profile

merged:
    traits
    themes

projection:
    worldspec role/faction
    compile context entity profile
    optional compatibility projection
```

### Note

Do not add enemy/boss logic here. Boss-like entities are just archetypes with strong stats, traits, and role.

### TDD

Add tests:

```text
human worker resolves with race + role defaults
wolf resolves with race natural traits
goblin raider resolves with explicit archetype profiles
boss-like archetype resolves without special boss class
invalid race-role compatibility fails or warns by policy
```

### Acceptance checklist

- [x] Every archetype can resolve.
- [x] Race defaults affect archetype output.
- [x] Role defaults affect archetype output.
- [x] Faction defaults affect archetype output.
- [x] Explicit archetype fields override defaults.
- [x] Traits/themes merge deterministically.
- [x] No archetype stores enemy/ally labels.
- [x] Compatibility projection is separate.

---

## Task 25.2 — Add `PopulationRecipeResolver`

### Description

Resolve population recipes into world assembly contributions.

### Technical description

Input:

```text
PopulationRecipeDefinition
target region/module context
```

Output:

```text
expanded population specs
resolved archetype profiles
compile context mappings
```

Preferred authoring:

```yaml
members:
  hungry_wolf: 4
  alpha_wolf: 1
```

Compatibility authoring:

```text
role + faction + count
```

can still be normalized, but should not be the preferred new path.

### Note

Do not duplicate existing world assembly tests. Extend them to include archetype-native population input.

### TDD

Extend:

```text
tests/unit/worldassembly/test_assembly.py
```

Add cases:

```text
module uses population recipe
population expands into old WorldSpec-compatible populations
CompileContext receives resolved archetype profile mappings
existing role/faction/count module still works
```

### Acceptance checklist

- [x] Population recipe resolves all archetype refs.
- [x] Preferred region refs are validated.
- [x] Expansion is deterministic.
- [x] Output remains compatible with `WorldSpec`.
- [x] CompileContext contains resolved archetype-driven profile data.
- [x] Old module population style remains supported as compatibility.

---

# Phase 26 — World content projection and runtime registry adapters

## Goal

Make world content families such as items, recipes, regions, resources, services, and buildings move through explicit adapters, not scattered heuristics.

The review notes that registry seeding is catalog-backed but still heuristic-heavy.

---

## Task 26.1 — Extract registry adapters

### Description

Move conversion logic out of `seed_phase1_content()` into dedicated adapters.

### Technical description

Create:

```text
CatalogToItemRegistryAdapter
CatalogToRecipeRegistryAdapter
CatalogToServiceRegistryAdapter
CatalogToRegionRegistryAdapter
CatalogToResourceRegistryAdapter
ArchetypeToEnemyRegistryAdapter
```

### Note

`seed_phase1_content()` should orchestrate only:

```text
load catalog
validate catalog
run adapters
seed registries
report source
```

### TDD

Extend existing runtime catalog tests instead of duplicating.

Current tests already verify runtime catalog expansion loading.

Add adapter-specific tests only where conversion behavior is new.

### Acceptance checklist

- [x] Registry seeding no longer contains category/class-fit/resource heuristics inline.
- [x] Each registry has one adapter.
- [x] Each adapter has unit tests.
- [x] Existing hardcoded fallback still works in fallback mode.
- [x] Catalog-backed mode is deterministic.
- [x] Adapter errors include source record ID.

---

## Task 26.2 — Add registry parity tests

### Description

Prove that every active catalog record reaches the matching runtime registry.

### Technical description

Generic parity test pattern:

```text
for every ItemDefinition:
    assert ItemRegistry contains equivalent item

for every RecipeDefinition:
    assert RecipeRegistry contains equivalent recipe

for every RuntimeRegionDefinition:
    assert RegionRegistry contains equivalent region

for every compatibility enemy projection:
    assert EnemyRegistry contains equivalent enemy
```

### Note

This avoids writing one custom test per item/enemy/recipe.

### TDD

Place under:

```text
tests/unit/content/test_runtime_catalog.py
```

or:

```text
tests/unit/runtime/test_registry_projection.py
```

Do not create a second unrelated runtime catalog suite.

### Acceptance checklist

- [x] All active item records project to ItemRegistry.
- [x] All active recipe records project to RecipeRegistry.
- [x] All active service records project to ServiceRegistry.
- [x] All active region records project to RegionRegistry.
- [x] Compatibility enemy projections project to EnemyRegistry.
- [x] Fallback-only records are excluded or marked clearly.
- [x] Test is data-driven, not hand-written per record.

---

# Phase 27 — World module and composition usage correction

## Goal

Make modules and compositions consume lower-layer data properly.

The direction says modules should compose lower definitions and not invent primitive meaning.

---

## Task 27.1 — Add `ResolvedModuleContribution`

### Description

Normalize module v1/v2 data into a single internal contribution format.

### Technical description

Output fields:

```text
regions
factions
population_refs
resolved_population_specs
resource_refs
building_refs
service_refs
relationship_refs
biome_refs
ecology_refs
```

The resolver should call component resolvers:

```text
PopulationRecipeResolver
EcologyResolver
RegionResolver
ResourceResolver
BuildingResolver
RelationshipResolver
```

### Note

Avoid a huge resolver function that manually interprets everything.

### TDD

Extend existing `test_structural_world_assembly_resolver`.

Current test already verifies assembly of regions, entities, provenance, and collision prevention.

### Acceptance checklist

- [x] v1 modules normalize correctly.
- [x] v2 modules normalize correctly.
- [x] Module cannot define unknown primitive data inline.
- [x] Module refs resolve through component resolvers.
- [x] Duplicate region collision still fails.
- [x] Normalized output is deterministic.
- [x] Module resolver does not run full-world completeness validation on partial modules.

---

## Task 27.2 — Add `WorldCompositionNormalizer`

### Description

Normalize composition input before assembly.

### Technical description

Supported input forms:

```yaml
module_refs:
  - module_id: frontier_village_core
    enabled: true
    order: 0
```

and:

```yaml
modules:
  - frontier_village_core
  - wolf_den_near_forest
```

Normalize to:

```text
NormalizedWorldComposition
```

### Note

This is where `default_perspectives` should be preserved, not silently ignored.

### TDD

Extend world assembly tests:

```text
module_refs format works
modules shorthand works
default perspectives preserved
mixed format fails
unknown fields fail
```

### Acceptance checklist

- [x] Existing composition tests still pass.
- [x] Shorthand module list works.
- [x] Mixed authoring forms fail.
- [x] Default perspectives survive normalization.
- [x] Composition fingerprint is deterministic.
- [x] Resolver receives one normalized format only.

---

## Task 27.3 — Keep provenance deterministic

### Description

Any new resolver path must preserve deterministic provenance.

### Technical description

The existing provenance tests assert manifest structure and deterministic content.

Extend those tests, do not duplicate.

Add provenance for:

```text
archetype source
population recipe source
biome/ecology source
relationship activation source
compatibility projection source
```

### Note

Do not embed this into `EntityState` yet. Keep sidecar provenance unless a later phase explicitly changes that.

### Acceptance checklist

- [x] Existing provenance tests still pass.
- [x] New module v2 path emits provenance.
- [x] Archetype expansion emits provenance.
- [x] Population expansion emits provenance.
- [x] Provenance output is deterministic.
- [x] EntityState structure is not changed in this phase.

---

# Phase 28 — Perspective/relation usage and legacy-safe migration

## Goal

Make perspective-derived relation labels available to simulation without rewriting all old systems at once.

The direction’s critical rule is: enemy is a relationship, not an entity type, and perspective determines chosen side and derived hostility.

---

## Task 28.1 — Add `RelationProjectionService`

### Description

Provide one clean service to project relationship labels.

### Technical description

API:

```python
project_relation(
    perspective_id: str,
    source_faction_id: str,
    target_faction_id: str,
    context: RelationContext,
) -> RelationProjection
```

Output:

```text
label
axes
confidence
relationship_model
source_records
```

Labels:

```text
ally
neutral
enemy
threat
intruder
opportunity
prey
ignored
protected
```

### Note

Do not build a full condition language yet. Use named relationship models.

### TDD

Extend current semantic tests rather than replacing them.

Current `content_semantics` tests already check old bucket-based semantics in earlier test exports.

Add new tests beside them:

```text
perspective projects goblin warband as enemy from hero perspective
wild beast pack projects as contextual threat, not enemy-by-race
merchant league projects as trade/neutral
legacy is_hostile wrapper still works
```

### Acceptance checklist

- [x] Projection works from perspective + faction relationship.
- [x] Race is not used as enemy source truth.
- [x] Contextual threat is supported.
- [x] Legacy hostility wrapper still passes old tests.
- [x] Projection output includes source relationship model.
- [x] No behavior script is introduced.

---

## Task 28.2 — Add compatibility wrapper for old consumers

### Description

Old systems that call `is_hostile()` or use legacy monster/hero buckets should not be rewritten all at once.

### Technical description

Wrapper:

```python
is_hostile_compat(source, target, context=None)
```

Internally:

```text
try clean projection
fallback to legacy bucket semantics
```

### Note

This prevents breaking combat, quest, and arena tests immediately.

The current arena tests still use legacy `Faction.HERO_GUILD`, `Faction.MONSTER_HORDE`, and `EntityRole.MONSTER` patterns.

### TDD

Do not duplicate arena tests.

Instead:

```text
keep existing arena tests unchanged
add focused unit tests for wrapper fallback
add one integration smoke test using clean projection path
```

### Acceptance checklist

- [x] Existing arena tests still pass.
- [x] Existing quest/combat tests still pass.
- [x] Clean projection path is used when data exists.
- [x] Legacy fallback is used only when clean data is unavailable.
- [x] Logs/report indicate fallback usage in debug mode.
- [x] No direct dependency from clean data to compatibility data.

---

# TDD strategy for the whole plan

## 1. Test pyramid

Use this structure:

```text
Unit tests:
    schemas
    repository loading
    reference graph
    resolvers
    adapters

Integration tests:
    catalog -> resolver -> world assembly
    catalog -> registry projection
    module -> composition -> compile context

Regression tests:
    existing catalog tests
    existing worldassembly tests
    existing provenance tests
    existing arena/combat/economy tests
```

---

## 2. Avoid duplicate tests

Do not create new tests that repeat current coverage.

Reuse/extend:

```text
tests/unit/content/test_catalog.py
tests/unit/content/test_layered_catalog.py
tests/unit/content/test_runtime_catalog.py
tests/unit/worldassembly/test_assembly.py
tests/unit/worldassembly/test_provenance.py
tests/unit/content_semantics/test_semantics.py
tests/arena/*
```

Existing catalog tests already cover baseline loading and relational validator behavior.

Existing world assembly tests already cover module resolver structure, collision prevention, and provenance.

Existing arena tests cover legacy combat/regional assumptions and should be preserved as migration safety tests.

---

## 3. Add new tests only for new responsibility

New tests should target gaps like:

```text
unknown fields fail closed
content family registry completeness
no dead active data
archetype resolver output
population recipe expansion
module v2 normalization
composition shorthand normalization
registry adapter parity
relation projection
legacy fallback wrapper
```

---

## 4. Test before implementation

For each ticket:

```text
1. Add failing test.
2. Implement minimal logic.
3. Confirm existing tests still pass.
4. Add one regression case if behavior touches old paths.
5. Avoid broad rewrites.
```

---

# Plan A summary

```text
Phase 20 — Content usage contract and test map
Phase 21 — Content family registry and strict load report
Phase 22 — Fail-closed schema and authoring-form normalization
Phase 23 — Global content reference graph and active-data validation
Phase 24 — Resolver layer for foundation, living, and social defaults
Phase 25 — Entity archetype and population resolution
Phase 26 — World content projection and runtime registry adapters
Phase 27 — World module and composition usage correction
Phase 28 — Perspective/relation usage and legacy-safe migration
```
