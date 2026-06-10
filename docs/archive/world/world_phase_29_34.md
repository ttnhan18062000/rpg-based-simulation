# Plan — Phase 29 to Phase 34

Plan focuses on making the resolved data actually enter the simulation runtime and proving it with careful tests.

The attached review’s main warning still applies: the system can look green while only loading/validating data, not consuming it. The real proof is still `file -> schema -> resolver -> compile/runtime projection -> simulation consumer -> test`.

---

# Phase 29 — EntityState construction bridge

## Goal

Connect resolved archetype data to actual runtime `EntityState` creation.

After Plan A, the system should have:

```text id="7zd494"
ResolvedEntityArchetype
ResolvedPopulation
CompileContext
ResolvedModuleContribution
```

But that is still not enough. The simulation runtime must be able to create real entities from this resolved data.

The current source already has a rich `EntityState` model and existing tests build entities through `V2EntityBuilder`, especially in arena and movement tests. These should remain valid migration safety tests.

---

## Task 29.1 — Define `ResolvedEntityRuntimeContract`

### Description

Create a clear contract for what a resolved archetype must provide before it can become a runtime entity.

### Technical description

Create a model like:

```python id="0qn9b1"
class ResolvedEntityRuntimeContract(BaseModel):
    archetype_id: str
    race_id: str
    faction_id: str
    role_id: str
    profession_id: str | None = None

    kind: str
    legacy_role: EntityRole | None = None
    legacy_faction: Faction | None = None

    hp: int
    max_hp: int
    atk: int
    def_stat: int
    attack_range: int
    readiness: float

    inventory_items: dict[str, int]
    starting_gold: float

    traits: tuple[str, ...]
    themes: tuple[str, ...]

    cognition_profile_id: str | None = None
    drive_profile_id: str | None = None
    need_profile_id: str | None = None
    sense_profile_id: str | None = None
    skill_profile_id: str | None = None
```

This model should be the boundary between catalog resolution and runtime entity creation.

### Note

Do not let `EntityState` directly load catalog files.
Do not let `V2EntityBuilder` know about YAML or repositories.
The bridge should receive already-resolved data.

### TDD

Add new tests under:

```text id="p7cfr9"
tests/unit/entities/test_resolved_entity_runtime_contract.py
```

Avoid duplicating arena tests. These tests only verify the contract object and mapping readiness.

### Acceptance checklist

- [ ] Contract includes clean identity: race, archetype, faction, role.
- [ ] Contract includes legacy role/faction only as projection fields.
- [ ] Contract includes runtime combat values.
- [ ] Contract includes inventory seed data.
- [ ] Contract includes profile source IDs.
- [ ] Contract is serializable to JSON.
- [ ] Contract does not import repository/catalog loader code.
- [ ] Contract does not include enemy/ally source-truth fields.

---

## Task 29.2 — Implement `ArchetypeEntityFactory`

### Description

Create a factory that converts `ResolvedEntityRuntimeContract` into `EntityState`.

### Technical description

Suggested class:

```python id="yi3hsk"
class ArchetypeEntityFactory:
    def build_entity(
        self,
        entity_id: int,
        contract: ResolvedEntityRuntimeContract,
        spawn: EntitySpawnContext,
    ) -> EntityState:
        ...
```

`EntitySpawnContext` should include:

```text id="woxowt"
position
spawn_region
initial_alive
initial_active
optional current_tick
optional name override
```

Mapping responsibility:

```text id="fl17gn"
identity:
    role, faction, kind, archetype/race metadata

combat:
    hp, max_hp, atk, def, range, readiness, alive

inventory:
    items, gold

social:
    faction/role relationship fields if currently supported

cognition:
    profile IDs / initial cognition hooks where currently supported

biological/lifecycle:
    alive/active/default survival state

navigation:
    spawn position / region-aware location
```

### Note

Keep the first version conservative. Do not force all new profiles into runtime behavior immediately. Store unresolved profile IDs in metadata or identity extension if needed, but do not silently lose them.

### TDD

Add focused unit tests:

```text id="483z03"
test_build_human_worker_entity_from_contract
test_build_wolf_entity_from_contract
test_build_goblin_raider_entity_from_contract
test_build_boss_like_entity_without_boss_class
test_entity_factory_does_not_require_enemy_type
```

### Acceptance checklist

- [ ] Factory creates valid `EntityState`.
- [ ] Combat values match resolved contract.
- [ ] Inventory values match resolved contract.
- [ ] Race/archetype IDs are preserved somewhere accessible.
- [ ] Legacy role/faction projection works where required.
- [ ] Boss-like archetype does not require special boss logic.
- [ ] Animal archetype does not require monster-specific source truth.
- [ ] Existing `V2EntityBuilder`-based tests still pass.

---

## Task 29.3 — Add migration-safe entity construction integration

### Description

Wire `ArchetypeEntityFactory` into world assembly or scenario setup without replacing all old entity construction paths at once.

### Technical description

Supported construction paths after this task:

```text id="u4nc0n"
legacy test/manual builder path
worldspec role/faction/count path
archetype-native resolved path
```

Priority for new content:

```text id="dgrdjk"
archetype-native resolved path
```

Fallback for old tests:

```text id="cefxat"
legacy builder path
```

### Note

Arena tests still use legacy enum assumptions such as `Faction.HERO_GUILD`, `Faction.MONSTER_HORDE`, and role-based combat setup. They should remain unchanged as safety tests, not rewritten into catalog tests immediately.

### TDD

Do not duplicate arena tests.

Add one integration smoke test:

```text id="xvbgnb"
catalog archetype -> resolved contract -> EntityState -> one tick smoke
```

### Acceptance checklist

- [ ] New path can build runtime entities from archetypes.
- [ ] Old builder tests still pass.
- [ ] Arena tests still pass.
- [ ] Entity construction path is deterministic.
- [ ] No runtime system imports `CatalogRepository`.
- [ ] Any fallback path is explicit and detectable in debug/report mode.

---

## Task 29.4 — Add `EntityIdentityResolver`

### Description

Create a single identity access layer that reads clean entity identity first and falls back to legacy enum identity only when necessary.

This must happen before high-impact systems such as combat, quests, and region threat classification start using relation projection.

### Technical description

Add:

```python
class EntityIdentityResolver:
    def resolve(self, entity: EntityState) -> ResolvedEntityIdentity:
        ...

class ResolvedEntityIdentity(BaseModel):
    entity_id: int | str
    archetype_id: str | None = None
    race_id: str | None = None
    faction_id: str
    role_id: str
    profession_id: str | None = None

    legacy_faction: Faction | None = None
    legacy_role: EntityRole | None = None

    source: Literal[
        "clean_metadata",
        "runtime_identity_extension",
        "compatibility_projection",
        "legacy_enum",
    ]
```

Resolution order:

```text
clean archetype/race/faction/role metadata
→ runtime identity extension
→ compatibility projection
→ legacy enum fields
```

### Rules

`EntityIdentityResolver` may depend on compatibility adapters.

`EntityIdentityResolver` must not load catalog files.

Runtime systems must use this resolver instead of inspecting legacy enum fields directly when clean classification is needed.

Missing identity should fail clearly unless the selected runtime mode explicitly allows unknown/manual test identity.

### TDD

Add:

```text
tests/unit/entities/test_entity_identity_resolver.py
```

Cases:

```text
entity built from clean archetype contract resolves clean identity
entity with clean faction/role only resolves clean identity
legacy-only arena entity resolves through legacy enum fallback
mixed clean + legacy entity prefers clean identity
missing faction/role fails clearly
resolver does not import CatalogRepository
```

### Acceptance checklist

```text
[ ] Clean archetype/race/faction/role IDs can be read from runtime entities.
[ ] Legacy enum-backed entities still resolve.
[ ] Clean identity wins when clean and legacy identity both exist.
[ ] Missing identity produces clear failure or explicit unknown result by mode.
[ ] Combat/quest/region systems can depend on identity resolver without catalog access.
[ ] Existing V2EntityBuilder and arena tests still pass unchanged.
```

---

# Phase 30 — Scenario setup resolver

## Goal

Make `simulation_scenarios/` useful as **simulation setup**, not observability or post-run analysis.

Scenario data should select:

```text id="12hb2x"
world composition
perspective
focus modules
initial conditions
initial pressures
```

It should not define diagnostics, metrics, scorecards, telemetry, or post-run interpretation.

---

## Task 30.1 — Define `SimulationScenarioDefinition`

### Description

Create a schema for scenario setup.

### Technical description

Suggested fields:

```python id="lq2h02"
class SimulationScenarioDefinition(BaseModel):
    id: str
    display_name: str | None = None
    world_composition: str
    perspective: str
    focus_modules: list[str] = []
    initial_conditions: dict[str, Any] = {}
    setup_tags: list[str] = []
```

Supported initial condition categories:

```text id="mpvrd3"
region_pressure
faction_activity
resource_scarcity
population_alertness
territorial_intrusion
trade_route_risk
danger_level_override
spawn_bias
```

### Note

No executable scripts in scenario YAML.
No behavior-specific hardcoded actions.
Scenario only configures starting world state and context.

### TDD

Add:

```text id="x43jlh"
tests/unit/scenarios/test_scenario_schema.py
```

Test unknown fields fail closed.

### Acceptance checklist

- [ ] Scenario references valid world composition.
- [ ] Scenario references valid perspective.
- [ ] Focus modules are valid if provided.
- [ ] Initial condition keys are from allowed categories.
- [ ] Unknown scenario fields fail.
- [ ] Scenario schema does not include observability/reporting fields.

---

## Task 30.2 — Implement `ScenarioSetupResolver`

### Description

Resolve scenario data into a runnable setup package.

### Technical description

Input:

```text id="b4kcnp"
SimulationScenarioDefinition
CatalogRepository
WorldModuleRepository
```

Output:

```python id="x1xblw"
class ResolvedScenarioSetup(BaseModel):
    scenario_id: str
    world_bundle: ResolvedWorldBundle
    perspective_id: str
    initial_relation_context: dict[str, Any]
    initial_state_modifiers: list[StateSetupModifier]
```

Flow:

```text id="s951hu"
scenario
→ world composition
→ normalized modules
→ resolved world bundle
→ perspective
→ initial condition modifiers
```

### Note

Do not apply modifiers directly inside schema parsing.
Parsing and applying should be separate.

### TDD

Add integration tests:

```text id="xm1u94"
scenario resolves world composition
scenario preserves perspective
scenario initial conditions become setup modifiers
invalid scenario composition fails
invalid scenario perspective fails
```

### Acceptance checklist

- [ ] Scenario resolves through existing composition resolver.
- [ ] Scenario preserves selected perspective.
- [ ] Scenario produces explicit setup modifiers.
- [ ] Scenario resolver does not run simulation.
- [ ] Scenario resolver does not import observability/reporting modules.
- [ ] Error messages include scenario ID.

---

## Task 30.3 — Apply setup modifiers safely

### Description

Convert scenario initial conditions into safe runtime setup modifications.

### Technical description

Examples:

```text id="m89qo9"
territorial_intrusion:
    marks target faction/entity group as inside claimed territory context

resource_scarcity:
    reduces available resource counts or increases pressure tags

faction_activity:
    changes initial activity/alertness level

population_alertness:
    sets initial readiness/awareness hints
```

Do not directly force actions like:

```text id="bfh6sb"
wolf attacks hero
goblin raids town immediately
merchant flees
```

### Note

This keeps scenarios as setup data, not behavior scripts.

### TDD

Add tests for modifier transformation only:

```text id="lkadul"
initial condition -> setup modifier
setup modifier -> deterministic state/context effect
unsupported modifier fails
```

### Acceptance checklist

- [ ] Setup modifiers are deterministic.
- [ ] Modifiers do not bypass entity behavior systems.
- [ ] Modifiers do not embed direct action scripts.
- [ ] Unsupported modifier types fail.
- [ ] Modifier application can be tested without running full simulation.

---

# Phase 31 — End-to-end strict compile matrix

## Goal

Prove that proposed data is not only valid but actually executable from content to runtime setup.

The attached review says current status is mostly loaded, partially validated, partially projected to legacy runtime, and not yet authoritative.

This phase creates the first strict matrix that proves end-to-end usage.

---

## Task 31.1 — Define strict world matrix

### Description

Create a small set of representative world builds.

### Technical description

Matrix rows:

```text id="xgmhrx"
frontier_village_core
frontier_village + wolf_den
frontier_village + goblin_camp
frontier_village + old_mine
frontier_village + bandit_road
frontier_village + undead_battlefield
frontier_village + moon_cult_ruins
```

Each row must execute:

```text id="v6f37a"
load catalog
validate catalog
normalize composition
normalize modules
resolve archetypes
resolve populations
resolve world content
resolve perspectives
produce WorldSpec
produce CompileContext
seed runtime registries
optionally create EntityState smoke setup
```

### Note

This is not a performance test. It is a correctness gate.

### TDD

Add:

```text id="5myi2u"
tests/integration/content/test_strict_world_matrix.py
```

Keep it separate from unit tests. Mark slow only if needed.

### Acceptance checklist

- [ ] Every matrix row loads successfully.
- [ ] Every matrix row validates successfully.
- [ ] Every matrix row produces `WorldSpec`.
- [ ] Every matrix row produces `CompileContext`.
- [ ] Every matrix row seeds runtime registries.
- [ ] Every matrix row has no unresolved active references.
- [ ] Every matrix row has deterministic fingerprint.
- [ ] No row uses hidden legacy fallback unless explicitly marked.

---

## Task 31.2 — Add active-data consumer gate

### Description

Ensure active proposed data is actually consumed.

### Technical description

For records marked:

```text id="llyek7"
EXISTING-LOGIC
LEGACY-EXPORT
REDESIGNED-CORE
```

the matrix should prove a path to at least one of:

```text id="7f96gc"
resolver output
compile context
runtime registry
runtime entity construction
world/module composition
scenario setup
```

For records marked:

```text id="yl2v2j"
ADDITIONAL
FUTURE-EXTENSION
```

allow inactive status only if explicitly excluded from strict mode.

### Note

This directly addresses the “content graveyard” risk from the review.

### TDD

Add data-driven tests using the reference graph from Phase 23.

### Acceptance checklist

- [ ] Active unused content fails strict mode.
- [ ] Future content can be skipped only with explicit state.
- [ ] Compatibility content must project to legacy target or be marked inactive.
- [ ] Failure message shows family, ID, and missing consumer path.
- [ ] Test is generic, not one test per data record.

---

## Task 31.3 — Preserve existing worldassembly tests

### Description

Ensure new strict matrix does not duplicate or replace existing worldassembly tests.

### Technical description

Existing tests already verify:

```text id="o58p1y"
WorldAssemblyResolver merges modular regions/populations/buildings
WorldSpec remains clean
duplicate region collision fails
provenance manifest is deterministic
CompileContext serialization works
CLI resolve/compile integration works
```

Plan B tests should extend these behaviors only where new responsibilities exist.

### Acceptance checklist

- [ ] Existing worldassembly tests remain unchanged unless necessary.
- [ ] New tests cover v2 normalization and archetype path only.
- [ ] Provenance determinism remains tested in the existing provenance suite.
- [ ] CompileContext serialization remains tested in the existing suite.
- [ ] No duplicate “basic assembly works” test is added.

---

# Phase 32 — Runtime content source modes and fallback guard

## Goal

Define how runtime content is sourced and make hidden hardcoded fallback impossible.

This phase owns `RuntimeContentMode`.

Later phases may change the default mode, but they must not redefine the mode model.

---

## Task 32.1 — Define `RuntimeContentMode`

### Description

Add one runtime configuration model that controls how simulation content is sourced.

### Technical description

Supported modes:

```text
catalog_strict
catalog_with_compatibility
legacy_fallback
test_manual
```

Mode behavior:

```text
catalog_strict:
    load catalog
    validate catalog
    resolve catalog
    seed registries from catalog adapters only
    fail on missing required content
    fail on hardcoded gameplay fallback
    allow no silent fallback

catalog_with_compatibility:
    use clean catalog as source truth
    allow compatibility projections
    warn or fail on hardcoded fallback by family policy
    expose compatibility usage in report

legacy_fallback:
    allow old hardcoded registry fallback
    require explicit configuration
    mark fallback usage in report

test_manual:
    allow tests to build states directly with builders
    do not require catalog load unless registry seeding is requested
```

### Rules

Do not auto-fallback from catalog mode into legacy mode.

Compatibility projection is not the same as hardcoded fallback.

```text
allowed:
clean catalog → compatibility projection → legacy registry shape

forbidden in catalog_strict:
catalog failure → hardcoded legacy record
```

### TDD

Add:

```text
tests/unit/runtime/test_runtime_content_mode.py
```

Cases:

```text
catalog_strict fails if required catalog projection is missing
catalog_strict fails on hardcoded fallback usage
catalog_with_compatibility allows compatibility projection
catalog_with_compatibility reports projection usage
legacy_fallback works only when explicitly selected
test_manual allows direct builder-based state creation
```

### Acceptance checklist

```text
[ ] Runtime content mode is defined in one place.
[ ] Strict mode never silently uses hardcoded gameplay fallback.
[ ] Compatibility mode allows adapter projection only.
[ ] Legacy fallback requires explicit configuration.
[ ] Manual test mode preserves direct builder tests.
[ ] Failure messages include selected mode and failing component.
[ ] Existing arena/API tests can select compatible mode without rewrite.
```

---

## Task 32.2 — Apply runtime mode to registry bootstrap

### Description

Make registry seeding respect `RuntimeContentMode`.

### Technical description

Bootstrap flow:

```text
read RuntimeContentMode
load catalog if mode requires catalog
validate catalog if mode requires catalog
resolve content if mode requires resolved content
run catalog registry adapters
run compatibility projections if allowed
run hardcoded fallback only if mode allows it
emit content source report
```

### Mode-specific behavior

```text
catalog_strict:
    adapter failure = error
    missing required projection = error
    hardcoded fallback = error

catalog_with_compatibility:
    adapter failure = error unless family marked optional
    compatibility projection = allowed
    hardcoded fallback = warning or error by migration policy

legacy_fallback:
    hardcoded fallback = allowed
    catalog may be skipped or loaded only for diagnostics

test_manual:
    registry bootstrap optional
```

### TDD

Add tests near runtime/bootstrap tests:

```text
strict mode registry bootstrap fails on fallback enemy
compatibility mode allows legacy enemy projection
legacy mode allows fallback maps
manual mode does not require catalog registry seeding
```

### Acceptance checklist

```text
[ ] Registry bootstrap reads runtime content mode.
[ ] Registry bootstrap does not decide fallback implicitly.
[ ] Compatibility projection and fallback are reported separately.
[ ] Strict mode fails on fallback.
[ ] Legacy mode still works.
[ ] Manual tests remain possible.
```

---

## Task 32.3 — Add hardcoded gameplay guard

### Description

Prevent new gameplay content from being added only to Python fallback maps.

### Technical description

Create architecture test:

```text
tests/architecture/test_no_new_hardcoded_gameplay_truth.py
```

Static scan targets:

```text
enemy registry fallback
item registry fallback
recipe registry fallback
region fallback
service fallback
test-only content factories that define gameplay IDs
```

Allowed:

```text
enum definitions
test fixture IDs inside tests
compatibility adapters
migration map entries
non-gameplay constants
```

Forbidden:

```text
new gameplay ID in source fallback map with no catalog/compatibility mapping
new enemy/item/recipe/region/service record only in Python
```

### Acceptance checklist

```text
[ ] Existing fallback records are allowed through migration map.
[ ] New unmapped gameplay IDs fail.
[ ] Test-only fixture IDs are allowed only in test paths.
[ ] Failure message points to migration map or catalog family.
[ ] Guard does not scan generated artifacts.
[ ] Guard runs in architecture suite.
```

---

## Task 32.4 — Create machine-readable migration map

### Description

Track legacy-to-catalog migration explicitly.

### Technical description

Create:

```text
data/content/compatibility/migration_map.yaml
```

Fields:

```text
legacy_id
legacy_family
catalog_family
catalog_id
adapter
status
fallback_allowed
notes
```

Statuses:

```text
catalog_authoritative
compat_projected
fallback_only
deprecated
removed
```

Required families:

```text
items
recipes
regions
services
legacy enemies
legacy factions
legacy roles
```

### Acceptance checklist

```text
[ ] Items are mapped.
[ ] Recipes are mapped.
[ ] Regions are mapped.
[ ] Services are mapped.
[ ] Legacy enemies map to archetypes or compatibility projections.
[ ] Legacy factions/roles map to clean IDs where needed.
[ ] Hardcoded gameplay guard uses this map.
[ ] Unmapped gameplay fallback fails outside legacy mode.
```

---

# Phase 33 — Regression alignment and test budget control

## Goal

Keep existing tests meaningful while adding the catalog-driven path.

The test base already contains API, arena, architecture, runtime, catalog, worldassembly, movement, and certification tests. New tests must extend the right suite instead of duplicating broad behavior coverage.

---

## Task 33.1 — Create test ownership map

### Description

Document which test suites own which behavior.

### Technical description

Create:

```text
docs/testing/content_migration_test_ownership.md
```

Ownership examples:

```text
tests/unit/content/test_catalog.py:
    catalog base load
    basic relational validator

tests/unit/content/test_layered_catalog.py:
    layered dependency and reference validation

tests/unit/content/test_runtime_catalog.py:
    runtime catalog expansion loading

tests/unit/worldassembly/test_assembly.py:
    module assembly
    duplicate ID prevention
    WorldSpec output

tests/unit/worldassembly/test_provenance.py:
    provenance structure
    deterministic manifests

tests/unit/content_semantics/test_semantics.py:
    legacy semantic mapping
    compatibility behavior

tests/arena/*:
    legacy simulation behavior regression

tests/certification/*:
    scenario/certification regression

tests/architecture/*:
    import boundaries
    forbidden dependency checks
    hardcoded gameplay guard
    enum usage boundaries
```

### Acceptance checklist

```text
[ ] Test ownership map exists.
[ ] Each new planned test points to an owner suite.
[ ] Existing regression suites are preserved.
[ ] Duplicate test categories are identified.
[ ] Observability tests are out of scope unless directly touched.
```

---

## Task 33.2 — Add migration test markers

### Description

Tag tests by migration responsibility so CI can run targeted jobs.

### Technical description

Suggested markers:

```text
catalog
content_graph
worldassembly
registry_projection
entity_construction
scenario_setup
perspective
legacy_compat
content_pack
strict_matrix
architecture
```

### TDD

Update pytest config with marker declarations.

### Acceptance checklist

```text
[ ] New markers are declared in pytest config.
[ ] Existing relevant tests are tagged where useful.
[ ] CI can run catalog-only tests.
[ ] CI can run worldassembly-only tests.
[ ] CI can run strict matrix tests.
[ ] CI can run legacy compatibility tests.
[ ] Slow tests are not added to fast unit jobs by accident.
```

---

## Task 33.3 — Define no-duplication test policy

### Description

Prevent test explosion.

### Technical description

Rules:

```text
new resolver:
    3–6 focused unit tests

new authoring form:
    extend existing schema/normalizer tests

new registry adapter:
    adapter-specific unit tests + generic parity test

new full pipeline:
    one matrix integration test, data-driven

new content record:
    covered by data-driven graph/matrix tests
    no one-test-per-record

legacy behavior:
    preserve existing arena/certification tests
    do not rewrite them into catalog tests

observability/API:
    do not touch unless runtime startup behavior changes
```

### Acceptance checklist

```text
[ ] New PRs must identify owner suite.
[ ] New PRs must justify new test files.
[ ] Data-driven coverage is preferred for content records.
[ ] No duplicate “basic catalog loads” tests are added.
[ ] No duplicate “basic world assembly works” tests are added.
[ ] Existing legacy tests remain regression protection.
```

---

## Task 33.4 — Add test delta budget

### Description

Set a hard budget for how many tests each phase should add.

### Technical description

Default budget:

```text
small resolver/task:
    3–6 tests

medium integration feature:
    1–2 integration tests

strict matrix:
    1 data-driven matrix test

content pack:
    1 manifest test
    1 validation pipeline test
    1 strict matrix test

architecture guard:
    1 architecture test
```

Any task exceeding the budget must explain:

```text
why existing tests cannot be extended
what unique behavior is being protected
whether test can be data-driven instead
```

### Acceptance checklist

```text
[ ] Test delta budget is documented.
[ ] CI/review checklist references the budget.
[ ] Excessive new test files require justification.
[ ] Content expansion uses matrix coverage, not per-record tests.
```

---

## Task 33.5 — Define migration CI lanes

### Description

Create targeted CI lanes for this migration.

### Technical description

Suggested lanes:

```text
catalog-fast:
    content schema
    catalog loader
    reference graph
    no-dead-active-data

worldassembly-fast:
    normalizers
    module/composition assembly
    provenance

runtime-projection:
    registry adapters
    entity construction
    runtime content mode

strict-matrix:
    representative end-to-end content builds

legacy-regression:
    arena
    certification
    legacy compatibility tests

architecture:
    import boundaries
    enum usage boundaries
    hardcoded gameplay guard
```

### Acceptance checklist

```text
[ ] CI can run targeted migration lanes.
[ ] Strict matrix can be run separately.
[ ] Legacy regression remains visible.
[ ] Architecture guards run in normal CI.
[ ] Slow tests are isolated from fast feedback lanes.
```

---

# Phase 34 — Horizontal content expansion gate

## Goal

Allow more fantasy-world content only after the usage path is proven.

The review explicitly warns to stop adding more catalog records until current records have a proven consumer path.

This phase defines when it is safe to add more races, factions, archetypes, regions, modules, and scenarios.

---

## Task 34.1 — Define content expansion readiness gate

### Description

Before adding large new data packs, require the current data to pass strict usage.

### Technical description

Gate checklist:

```text id="js1x3z"
content family registry complete
fail-closed schema active
reference graph passes
no dead active data
archetypes resolve
populations expand
modules normalize
compositions normalize
registry adapters project
scenario setup resolves
relation projection works
strict world matrix passes
```

### Note

Horizontal data is good, but only after current data has consumer paths.

### Acceptance checklist

- [ ] Gate command exists.
- [ ] Gate checks all active families.
- [ ] Gate fails on unused active data.
- [ ] Gate fails on unknown active fields.
- [ ] Gate passes current baseline before expansion starts.
- [ ] Gate output is readable enough for development tickets.

---

## Task 34.2 — Add content pack format

### Description

Define how new horizontal content should be added.

### Technical description

Content pack should include:

```text id="j58vpr"
foundation additions if needed
living additions
social additions
entity archetypes
populations
world content
modules
scenarios
compatibility projections only if needed
```

Each pack must include:

```text id="ce1wuq"
pack manifest
state markers
required dependencies
strict validation mode result
world matrix sample
```

### Note

This prevents random content files from appearing without integration.

### Acceptance checklist

- [ ] Content pack manifest schema exists.
- [ ] Pack dependencies are validated.
- [ ] Pack can be enabled/disabled.
- [ ] Pack has at least one scenario or composition consuming it.
- [ ] Pack does not introduce new mechanisms without explicit design ticket.
- [ ] Pack passes strict gate before merge.

---

## Task 34.3 — First allowed horizontal pack

### Description

After the gate passes, add one controlled expansion pack.

Recommended first pack:

```text id="vpgjna"
frontier_extended_pack
```

It may include:

```text id="o5b3lv"
orc clan
bandit route
dwarven mine
undead battlefield
forest wardens
merchant caravan
moon cult ruin
```

### Note

Do not add dragon/volcanic/frozen/swamp all at once unless each has a consuming module/scenario.

### TDD

Add one matrix row per included module, not one test per record.

### Acceptance checklist

- [ ] Pack has manifest.
- [ ] Pack has at least one composition.
- [ ] Pack has at least one scenario.
- [ ] All archetypes are consumed by populations.
- [ ] All populations are consumed by modules/ecologies.
- [ ] All modules are consumed by composition.
- [ ] Strict matrix passes.
- [ ] No new vertical mechanism is introduced silently.

---

# Plan summary

```text id="8j2y3u"
Phase 29 — EntityState construction bridge
Phase 30 — Scenario setup resolver
Phase 31 — End-to-end strict compile matrix
Phase 32 — Legacy hardcoded truth deprecation
Phase 33 — Regression alignment with current tests
Phase 34 — Horizontal content expansion gate
```
