# Plan — Phase 40 to Phase 44

Plan focuses on:

```text
cleaning old enum assumptions
broadening scenario authoring
making drive/need/sense data affect behavior carefully
adding the second gated content pack
retiring legacy fallback as default-supported logic
```

The attached review’s key warning still applies: the system must not stop at loading and validating YAML. Each active data component must reach resolver, compile/runtime projection, simulation consumer, and tests.

---

# Phase 40 — Gradual cleanup of old enum assumptions

## Goal

Reduce direct dependency on old hardcoded concepts after clean identity access already exists.

This phase does not create `EntityIdentityResolver`.

It adopts it broadly and prevents new enum coupling from spreading.

---

## Task 40.1 — Replace direct enum checks in high-impact systems

### Description

Move high-impact systems away from direct enum comparisons where clean identity is available.

### Technical description

Initial target systems:

```text
combat target classification
quest target matching
regional threat classification
reward attribution
faction influence update
```

Replace patterns like:

```python
entity.identity.faction == Faction.MONSTER_HORDE
entity.identity.role == EntityRole.MONSTER
```

with:

```python
identity = EntityIdentityResolver.resolve(entity)
projection = RelationProjectionService.project_relation(...)
```

or compatibility wrappers where clean projection is not yet available.

### Rules

Do not rewrite calculation logic in the same task.

Only replace identity lookup/classification boundaries.

### TDD

Extend existing system tests where already covered.

Add focused compatibility tests:

```text
legacy enum entity still behaves the same
clean archetype entity follows clean relation path
mixed clean and legacy entities work together
```

### Acceptance checklist

```text
[ ] Combat classification no longer requires direct monster enum checks where clean identity exists.
[ ] Quest target matching can use clean faction/archetype identity.
[ ] Regional classification can use clean faction ID.
[ ] Legacy entities still work through fallback.
[ ] Existing quest and arena tests still pass.
[ ] New tests prove clean and legacy entities can coexist.
```

---

## Task 40.2 — Add enum usage linter with allowlist

### Description

Prevent new direct enum usage from spreading while migration is ongoing.

### Technical description

Create architecture test:

```text
tests/architecture/test_legacy_enum_usage_boundaries.py
```

Allowed direct enum usage:

```text
compatibility adapters
legacy fallback modules
old tests
migration map
enum definitions
explicit legacy-mode tests
```

Forbidden direct enum usage:

```text
new clean resolvers
new catalog-driven systems
new world assembly logic
new relation projection logic
new scenario setup resolver
new content pack systems
```

### Acceptance checklist

```text
[ ] Architecture test scans source files.
[ ] Allowlist is explicit and documented.
[ ] New clean modules cannot directly depend on old enum buckets.
[ ] Existing legacy paths remain allowed during migration.
[ ] Test failure explains which adapter/resolver should be used instead.
[ ] CI can run this test in the architecture suite.
```

---

## Task 40.3 — Add enum migration backlog report

### Description

Create a report showing remaining direct enum usage by category.

### Technical description

Report categories:

```text
allowed legacy fallback
allowed test-only usage
compatibility projection usage
migration target
forbidden new usage
```

Fields:

```text
file
line
enum symbol
category
suggested replacement
migration status
```

### TDD

Architecture test should assert:

```text
report can be generated
forbidden category is empty
allowed categories are explicitly listed
```

### Acceptance checklist

```text
[ ] Remaining enum usage is visible.
[ ] Forbidden enum usage fails CI.
[ ] Allowed enum usage is documented.
[ ] Report distinguishes tests from runtime source.
[ ] Report gives replacement guidance.
```

---

# Phase 41 — Broaden scenario authoring from clean data

## Goal

Make scenario authoring use clean world composition, perspective, population, and initial-condition data.

Phase 30 introduced scenario setup. Phase 41 expands it so scenarios can cover many simulation situations without becoming scripts.

---

## Task 41.1 — Add scenario authoring templates

### Description

Define reusable scenario templates for common simulation setups.

### Technical description

Templates:

```text
territorial_pressure
raider_conflict
trade_route_risk
resource_recovery
settlement_defense
cult_ritual_pressure
undead_containment
wildlife_intrusion
caravan_escort
mine_reopening
```

Template schema:

```python
class ScenarioTemplateDefinition(BaseModel):
    id: str
    required_world_features: list[str]
    required_perspective_types: list[str]
    allowed_initial_conditions: list[str]
    allowed_focus_modules: list[str]
```

### Note

Templates define allowed structure, not scripted behavior.

### TDD

Add:

```text
tests/unit/scenarios/test_scenario_templates.py
```

Cases:

```text
template validates allowed initial condition keys
scenario using matching template passes
scenario using unsupported initial condition fails
template does not contain action scripts
```

### Acceptance checklist

- [ ] Scenario templates exist.
- [ ] Templates restrict allowed setup fields.
- [ ] Templates do not define direct entity actions.
- [ ] Scenario can declare a template.
- [ ] Invalid scenario/template combination fails.
- [ ] Existing scenario resolver still works without template if allowed.

---

## Task 41.2 — Add scenario-to-world feature validation

### Description

Ensure scenarios only reference features provided by their selected world composition.

### Technical description

Validation examples:

```text
scenario requires wolf_den_ecology
→ selected composition must include module/ecology providing it

scenario requires merchant trade route
→ composition must include trade route module

scenario requires undead containment
→ composition must include undead battlefield/related ecology
```

Implementation:

```python
ScenarioWorldFeatureValidator.validate(
    scenario,
    resolved_world_composition
)
```

### Note

This prevents scenarios from referencing modules or pressures that are not present in the world.

### TDD

Add tests:

```text
scenario feature exists in composition → pass
scenario feature missing from composition → fail
focus module not in composition → fail
required perspective missing → fail
```

### Acceptance checklist

- [ ] Scenario requirements are checked against composition outputs.
- [ ] Missing feature fails before runtime.
- [ ] Missing focus module fails before runtime.
- [ ] Missing perspective fails before runtime.
- [ ] Error includes scenario ID and missing feature.
- [ ] Validation is deterministic.

---

## Task 41.3 — Add scenario catalog matrix

### Description

Create a matrix of scenario definitions that proves the scenario authoring model works across different world setups.

### Technical description

Initial scenario matrix:

```text
wolf_territory_pressure
goblin_camp_pressure
merchant_trade_route_risk
old_mine_recovery
undead_battlefield_containment
moon_cult_ruins_pressure
settlement_defense
forest_warden_patrol
```

Each scenario must prove:

```text
scenario loads
template validates
composition resolves
perspective resolves
initial conditions normalize
setup modifiers are produced
no simulation script is embedded
```

### Note

Do not run long simulations here. This is setup validation.

### TDD

Add integration test:

```text
tests/integration/scenarios/test_scenario_catalog_matrix.py
```

### Acceptance checklist

- [ ] Every scenario in matrix loads.
- [ ] Every scenario references valid composition.
- [ ] Every scenario references valid perspective.
- [ ] Every scenario passes feature validation.
- [ ] Every scenario produces setup modifiers.
- [ ] No scenario embeds direct behavior scripts.
- [ ] Test is data-driven.

---

# Phase 42 — Add deeper behavior consumers for drives, needs, and senses

## Goal

Make `drive_profiles`, `need_profiles`, and `sense_profiles` affect behavior carefully, without building a large emotion/AI subsystem too early.

This phase is important because living data should not remain decorative. But implementation must be incremental.

---

## Task 42.1 — Add pressure model from needs and drives

### Description

Convert need/drive profiles into generic pressure values that can influence goal selection.

### Technical description

Add:

```python
class MotivationPressureResolver:
    def resolve_pressures(entity, context) -> MotivationPressureSet:
        ...
```

Input data:

```text
need_profile
drive_profile
current state
region context
relationship context
```

Output examples:

```text
hunger_pressure
safety_pressure
territory_pressure
duty_pressure
wealth_pressure
curiosity_pressure
aggression_pressure
```

### Note

Do not implement complex emotional simulation. Use normalized pressure values first.

### TDD

Add tests:

```text
territorial predator produces territory/hunger pressure
cautious commoner produces safety/duty pressure
merchant produces wealth/trade pressure
undead purpose-bound profile produces purpose pressure
```

### Acceptance checklist

- [ ] Need profiles are consumed.
- [ ] Drive profiles are consumed.
- [ ] Output is normalized and deterministic.
- [ ] Missing profile fails or falls back explicitly by mode.
- [ ] Pressures do not directly force actions.
- [ ] Resolver does not contain race-specific scripts.

---

## Task 42.2 — Add sense profile to perception gating

### Description

Make sense profiles influence what entities can detect.

### Technical description

Add or extend perception service:

```python
class PerceptionGate:
    def can_perceive(source_entity, target_or_event, context) -> PerceptionResult:
        ...
```

Inputs:

```text
sense_profile
distance
terrain/region context
target visibility/noise/scent/magic signal
current alertness
```

Output:

```text
perceived: bool
confidence
signals_used
profile_source
```

### Note

Start with simple categories:

```text
vision
hearing
smell
magic_sense
life_sense
vibration
social_reading
```

No need for complex sensory physics.

### TDD

Add tests:

```text
wolf detects scent better than normal humanoid
spider detects vibration context
arcane profile detects magic signal
normal humanoid cannot detect magic signal without profile
```

### Acceptance checklist

- [ ] Sense profiles are consumed by perception.
- [ ] Perception result includes source profile.
- [ ] Perception is deterministic for same input.
- [ ] Perception does not bypass relation projection.
- [ ] Existing movement/combat tests still pass.
- [ ] No race-specific perception script is introduced.

---

## Task 42.3 — Connect pressure and perception to goal/target selection

### Description

Use pressures and perception as inputs to existing decision points.

### Technical description

High-impact first consumers:

```text
combat target eligibility
territorial response
avoidance/flee decision
resource-seeking priority
service/trade seeking
```

Flow:

```text
perception gate
→ relation projection
→ motivation pressure
→ target/goal scoring
```

### Note

Do not rewrite the entire behavior engine. Add scoring inputs where decision points already exist.

### TDD

Add focused behavioral tests:

```text
entity cannot target unperceived enemy
territorial animal scores intruder higher inside territory
merchant avoids high-threat target when safety pressure high
guard scores duty-related threat higher
```

Keep tests small and deterministic.

### Acceptance checklist

- [ ] Perception affects target eligibility.
- [ ] Motivation pressure affects scoring.
- [ ] Relation projection remains part of classification.
- [ ] Existing combat tests still pass.
- [ ] New behavior tests are deterministic.
- [ ] No direct scripted behavior is added.

---

# Phase 43 — Introduce second content pack after first pack proves stable

## Goal

Add a second gated content pack only after `frontier_extended_pack` passes the Phase 39 pack matrix.

This phase must reuse the Phase 34 pack manifest schema and validation pipeline.

It must not redefine pack schema or add new pack infrastructure unless Phase 39 exposed a proven gap.

---

## Phase 43 entry criteria

Before starting Phase 43:

```text
Phase 34 pack contract passes
frontier_extended_pack manifest validates
frontier_extended_pack strict matrix passes
base-only strict matrix still passes
base + first pack strict matrix passes
content source report distinguishes base and pack records
hardcoded fallback guard still passes
```

---

## Phase 43 rule

The second pack may add horizontal content.

It may not add new vertical systems.

Forbidden in this phase:

```text
new diplomacy engine
new weather engine
new combat engine
new scripting language
new condition DSL
new pack manifest schema
new registry bootstrap mode
```

---

## Task 43.1 — Select second content pack theme

### Description

Choose one pack theme that reuses existing mechanisms.

Recommended options:

```text
swamp_border_pack
frozen_peak_pack
volcanic_dragon_pass_pack
spirit_grove_pack
```

Pick one only.

### Technical description

Pack must reuse existing systems:

```text
races
factions
archetypes
materials
resources
items
recipes
biomes
modules
scenarios
relationship models
```

It must not introduce:

```text
full diplomacy
weather system
lineage/history
large-scale politics
new combat engine
complex condition language
```

### Note

For safe implementation, I recommend:

```text
swamp_border_pack
```

because it can reuse:

```text
lizardfolk
swamp tribe
venom materials
swamp terrain
territorial relationship
resource conflict
trade-route risk
```

### Acceptance checklist

- [ ] One pack theme selected.
- [ ] Pack uses existing mechanisms.
- [ ] Pack has clear module/composition/scenario consumers.
- [ ] Pack does not require new vertical subsystem.
- [ ] Pack dependencies are listed.
- [ ] Pack fits strict content gate.

---

## Task 43.2 — Implement second content pack manifest and data

### Description

Add the selected content pack with manifest-first workflow.

### Technical description

Required files:

```text
content_packs/<pack_id>/manifest.yaml
content_packs/<pack_id>/content/living/*
content_packs/<pack_id>/content/social/*
content_packs/<pack_id>/content/entities/*
content_packs/<pack_id>/content/world/*
content_packs/<pack_id>/content/world_modules/*
content_packs/<pack_id>/content/world_compositions/*
content_packs/<pack_id>/content/simulation_scenarios/*
```

Required content categories:

```text
at least one faction
at least one population
at least one module
at least one composition
at least one scenario
```

### Note

Do not add foundation concepts unless required. Prefer using existing foundation IDs.

### TDD

Add pack validation tests:

```text
pack manifest validates
pack dependencies resolve
pack active data is reachable
pack strict matrix passes
pack disabled does not affect base world
```

### Acceptance checklist

- [ ] Pack manifest exists.
- [ ] Pack dependencies resolve.
- [ ] Pack can be disabled.
- [ ] Pack can be enabled.
- [ ] Pack has at least one scenario.
- [ ] Pack has at least one composition.
- [ ] All active records have consumer paths.
- [ ] Base strict matrix unchanged when pack disabled.

---

## Task 43.3 — Pack interaction test

### Description

Verify that two packs can coexist without accidental ID collisions or unresolved references.

### Technical description

Test modes:

```text
base only
base + frontier_extended_pack
base + second_pack
base + frontier_extended_pack + second_pack
```

Validate:

```text
ID uniqueness
reference graph
composition resolution
scenario setup
registry projection
strict matrix
```

### Note

This prevents horizontal scaling from creating hidden coupling.

### TDD

Add:

```text
tests/integration/content_packs/test_multi_pack_composition.py
```

### Acceptance checklist

- [ ] Base only passes.
- [ ] First pack only passes.
- [ ] Second pack only passes.
- [ ] Both packs together pass.
- [ ] ID collision fails clearly.
- [ ] Pack dependency error fails clearly.
- [ ] Disabled pack content is not accidentally consumed.

---

# Phase 44 — Final legacy fallback retirement plan

## Goal

Define and execute the final steps to retire legacy fallback as normal behavior.

This does not mean deleting every old test. It means old hardcoded gameplay content is no longer a normal source of truth.

---

## Task 44.1 — Define final fallback retirement criteria

### Description

Create explicit criteria for retiring fallback.

### Technical description

Fallback can be retired when:

```text
catalog-backed mode is default
strict mode passes
core scenario matrix passes
first content pack passes
second content pack passes
legacy mapping is complete
arena smoke has clean catalog equivalent
relation projection used in high-impact systems
hardcoded gameplay guard passes
```

### Note

This is a gate, not an implementation change.

### Acceptance checklist

- [ ] Retirement criteria documented.
- [ ] Each criterion maps to a test or CI job.
- [ ] Missing criterion blocks retirement.
- [ ] Criteria distinguish compatibility projection from hardcoded fallback.
- [ ] Criteria are accepted before deleting fallback code.

---

## Task 44.2 — Convert legacy fallback to test-only or explicit debug mode

### Description

Restrict fallback usage to controlled contexts.

### Technical description

Allowed contexts after retirement:

```text
test_manual
legacy_fallback explicitly selected
debug migration tool
compatibility verification tests
```

Forbidden contexts:

```text
normal startup
catalog_with_compatibility mode
catalog_strict mode
content pack validation
scenario strict matrix
```

### Note

Compatibility projections may remain. Hardcoded fallback should not.

### TDD

Add tests:

```text
normal startup cannot use fallback
catalog_with_compatibility cannot use hardcoded fallback
legacy_fallback mode still works when explicitly selected
strict matrix fails if fallback used
```

### Acceptance checklist

- [ ] Normal startup fails if fallback is required.
- [ ] Compatibility projection still works.
- [ ] Explicit legacy mode still works for debugging.
- [ ] Test manual mode still supports direct builders.
- [ ] Report marks fallback as retired outside allowed modes.
- [ ] Existing old regression tests are either migrated or marked legacy-mode.

---

## Task 44.3 — Remove fallback records gradually

### Description

Delete or quarantine fallback records only after mapping and tests prove replacement.

### Technical description

Removal order:

```text
items
recipes
services
regions
enemy projections
legacy enemy registry fallback
legacy role/faction-only content
```

For each family:

```text
verify catalog equivalent
verify adapter equivalent if needed
verify tests pass
remove fallback record
update migration map
run strict matrix
```

### Note

Do not delete everything in one ticket. Use one ticket per family.

### TDD

For each family, run:

```text
registry parity tests
strict matrix
legacy compatibility test if adapter remains
arena smoke
scenario setup matrix
```

### Acceptance checklist

- [ ] Family has complete catalog replacement.
- [ ] Family has passing registry parity.
- [ ] Family has passing strict matrix.
- [ ] Fallback records removed or quarantined.
- [ ] Migration map updated.
- [ ] Existing tests still pass in intended modes.
- [ ] No hidden fallback usage remains.

---

# Plan summary

```text
Phase 40 — Gradual cleanup of old enum assumptions
Phase 41 — Broaden scenario authoring from clean data
Phase 42 — Add deeper behavior consumers for drives, needs, and senses
Phase 43 — Introduce second content pack after first pack proves stable
Phase 44 — Final legacy fallback retirement plan
```
