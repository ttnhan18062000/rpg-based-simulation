RevoZ
revoz_r06
:ogu:

RevoZ [GDev],  — 30/05/2026 4:39 CH
# Next Phases Implementation Plan: Phase 11+

## Current diagnosis

The current implementation has achieved the **foundation layer**, but it has not completed the major feature.

worlf_plan_phase_11_19.md
42 KB
RevoZ [GDev],  — 31/05/2026 10:56 CH
https://gemini.google.com/app/795bebd5194f0cfb?hl=vi
Gemini
‎Google Gemini
Làm quen với Gemini, trợ lý AI của Google. Gemini có thể giúp bạn viết nội dung, lên kế hoạch, học tập và nhiều việc khác. Trải nghiệm sức mạnh của AI tạo sinh.

https://gemini.google.com/share/e2b8ac040edd
Gemini
‎Gemini - direct access to Google AI
Created with Gemini

# **Comprehensive Architectural Analysis of Layered Simulation Data Redesign: Logic, Execution, and Systemic Vulnerabilities**

## **Systemic Boundaries and Topological Focus**

The transition toward the Fresh Layered Simulation Data Design v3 signifies a radical ontological reconstruction of the underlying simulation architecture. The primary objective is to systematically deprecate rigid, top-down inheritance classifications in favor of a profoundly nuanced, bottom-up composable dependency graph.1 The immediate systemic boundaries of this redesign are strictly confined to the generation and management of simulation world elements.1 This encompasses the instantiation of entities, living beings, biological races, sociological factions, interactive relationships, functional roles, overarching archetypes, and broader environmental ecologies such as populations, physical materials, raw resources, constructed items, economic services, biomes, regions, world modules, and comprehensive simulation scenarios.1  
Crucially, this design intentionally quarantines external and observational mechanisms. The documentation explicitly excludes observability matrices, analysis dashboards, telemetry streams, expectation packs, and downstream reporting workflows from the current data schema.1 The strategic intention behind this exclusion is to establish a pristine, unpolluted data direction that purely supports a deep, emergent simulation model.1 By focusing exclusively on the internal logical consistency of the simulation topology, the architecture aims to seamlessly subsume existing functional logic while permitting small-to-medium systemic additions.1 This conservative approach to infrastructural expansion explicitly avoids the introduction of brand-new, computationally complex subsystems that are not immediately requisite for foundational behavioral modeling.1

research_plan_report.md
48 KB
RevoZ [GDev],  — 03/06/2026 5:25 CH
Attachment file type: archive
content.zip
32.70 KB
# Layered World Data Direction

## 1. Core direction

The project should move toward a bottom-to-top data model where high-level world concepts are built by inheriting, composing, and specializing lower dependency layers.

layered_data_direction.md
12 KB
RevoZ [GDev],  — 04/06/2026 1:46 SA
## Verdict

Your implementation plan is **directionally correct and necessary**, but the current source only implements the early “load/validate/index” layer. Most of the plan’s actual target — **resolved, projected, runtime-consumed content** — is still missing.

The uncomfortable truth: the current system can look green while silently ignoring the proposed data model. That is the main risk.

world_plan_phase_20_38_review.md
13 KB
Got it. The updated plan should focus on **how the proposed data under `data/content/` is actually used incorrectly or incompletely**, not just “add missing logic.”

So the plan below treats each component as a **data-usage pipeline**:

```text
data file

world_plan_phase_20_38.md
31 KB
RevoZ [GDev],  — 04/06/2026 5:31 CH
# Plan — Phase 40 to Phase 44

Plan focuses on:

```text
cleaning old enum assumptions

world_phase_40_44.md
22 KB
# Phase 20 — Content usage contract and test map

## Goal

Define exactly how every `data/content/` component is supposed to be used before changing more logic.

world_phase_20_28.md
31 KB
# Plan — Phase 29 to Phase 34

Plan focuses on making the resolved data actually enter the simulation runtime and proving it with careful tests.

The attached review’s main warning still applies: the system can look green while only loading/validating data, not consuming it. The real proof is still `file -> schema -> resolver -> compile/runtime projection -> simulation consumer -> test`.

world_phase_29_34.md
33 KB
# Plan — Phase 35 to Phase 39

Plan focuses on:

```text
make catalog-backed runtime the default

world_phase_35_39.md
22 KB
RevoZ [GDev],  — 05/06/2026 3:31 CH
# Implementation Repair Plan: Phase 20–28

## 1. Goal

Repair the current Phase 20–28 implementation so that the content pipeline is proven by real executable flow, not only by component existence, schema acceptance, or manually injected test objects.
... (1 KB left)

phase_20_28_repair_plan_ai_agent.md
51 KB
RevoZ [GDev],  — 08/06/2026 12:25 SA
# Remaining Repair Plan — After Full Source Review

## Goal

Finish the remaining cleanup after the Phase 20–28 repair so the implementation is safer for future AI-agent work.

another_repair_plan_phase_20_28.md
20 KB
﻿
# Plan — Phase 35 to Phase 39

Plan focuses on:

```text
make catalog-backed runtime the default
migrate selected arena/certification setup safely
replace bucket-only hostility in high-impact systems
shrink legacy fallback
expand fantasy content only after strict gates
```

The attached review’s warning still applies: the system can look correct while only loading/validating data, not consuming it. The real proof must remain `file -> schema -> resolver -> compile/runtime projection -> simulation consumer -> test`.

The attached test export already contains many API, arena, architecture, and runtime tests, so new tests should extend existing suites instead of duplicating broad behavior coverage.

---

# Phase 35 — Make catalog-backed mode the default runtime mode

## Goal

Switch normal startup to use catalog-backed content by default.

This phase depends on Phase 32 for `RuntimeContentMode`.

---

## Task 35.1 — Set normal startup default to `catalog_with_compatibility`

### Description

Change normal application startup so catalog-backed content is the default.

### Technical description

Default mode:

```text
catalog_with_compatibility
```

Not yet default:

```text
catalog_strict
```

because compatibility projections are still needed during migration.

Startup flow:

```text
read runtime config
select RuntimeContentMode
load catalog
validate catalog
resolve content
seed registries through adapters
apply compatibility projections if allowed
emit content source report
start simulation
```

### Rules

Do not silently downgrade from `catalog_with_compatibility` to `legacy_fallback`.

If catalog-backed startup fails, startup fails unless the operator explicitly selected `legacy_fallback`.

### TDD

Add focused startup test:

```text
server startup uses catalog_with_compatibility by default
```

Extend existing API/server startup smoke tests only if needed.

### Acceptance checklist

```text
[ ] Normal startup selects catalog_with_compatibility by default.
[ ] Startup does not auto-fallback to legacy.
[ ] Compatibility projection usage is visible.
[ ] Existing REST/API startup tests still pass.
[ ] Existing observability tests do not need rewriting.
```

---

## Task 35.2 — Add startup content source report

### Description

Expose a startup/debug report showing where runtime content came from.

### Technical description

Report fields:

```text
runtime_content_mode
catalog_path
loaded_families
resolved_families
registry_projection_counts
compatibility_projection_counts
hardcoded_fallback_counts
legacy_fallback_used
warnings
errors
fingerprint
```

### Rules

This is startup/configuration proof, not observability telemetry.

The report must be assertable in tests without running a long simulation.

### TDD

Add:

```text
tests/unit/runtime/test_content_source_report.py
```

Cases:

```text
catalog mode report contains loaded/resolved family counts
compatibility mode report contains projection counts
legacy mode marks fallback usage
strict mode report shows fallback error
report fingerprint is deterministic
```

### Acceptance checklist

```text
[ ] Report exists after runtime bootstrap.
[ ] Report includes runtime content mode.
[ ] Report includes registry projection counts.
[ ] Report distinguishes compatibility projection from hardcoded fallback.
[ ] Report can be asserted in tests.
[ ] Report is deterministic.
```

---

## Task 35.3 — Preserve explicit legacy/test modes

### Description

Keep existing arena, API, and direct-builder tests working by selecting the correct mode explicitly.

### Technical description

Rules:

```text
arena/certification legacy regression:
    may use test_manual or legacy_fallback depending on setup

direct V2EntityBuilder tests:
    use test_manual

legacy registry fallback tests:
    use legacy_fallback

catalog scenario tests:
    use catalog_with_compatibility or catalog_strict
```

### TDD

Add only focused mode-selection tests if existing suites fail.

### Acceptance checklist

```text
[ ] Old builder tests still pass.
[ ] Arena tests still pass unchanged.
[ ] API startup tests still pass.
[ ] Tests that require legacy fallback select it explicitly.
[ ] New catalog tests do not depend on legacy fallback.
```

---

# Phase 36 — Migrate selected arena/certification setup to clean archetype path

## Goal

Begin migrating scenario setup from direct legacy role/faction/entity construction to clean archetype-driven setup, without breaking existing certification tests.

Arena tests currently use direct `V2EntityBuilder`, legacy `Faction`, and legacy `EntityRole` assumptions. These should remain as regression protection while new catalog-driven setup is introduced beside them.

---

## Task 36.1 — Add catalog-backed scenario builder

### Description

Create a new builder that can construct certification/arena-style states from catalog archetypes and populations.

### Technical description

Suggested component:

```text
CatalogScenarioStateBuilder
```

Input:

```text
scenario_id
world_composition_id
perspective_id
population recipe refs
spawn layout
runtime content mode
```

Output:

```text
AuthoritativeState
ScenarioExpectations
ResolvedScenarioSetup
```

Internally:

```text
scenario
→ composition
→ module contributions
→ population resolver
→ archetype resolver
→ entity factory
→ AuthoritativeState
```

### Note

Do not replace `build_scenario_state()` yet. Add this beside it.

### TDD

Add focused tests:

```text
tests/unit/certification/test_catalog_scenario_state_builder.py
```

Cases:

```text
build small hero-vs-goblin state from archetypes
build worker/guard village state from population recipe
build animal ecology state from wolf population recipe
```

### Acceptance checklist

- [ ] Builder creates valid `AuthoritativeState`.
- [ ] Builder uses archetypes, not raw enemy IDs.
- [ ] Builder uses population recipes.
- [ ] Builder preserves selected perspective.
- [ ] Builder produces deterministic entity IDs or stable mapping.
- [ ] Builder does not replace existing certification builder yet.
- [ ] Existing arena tests still pass unchanged.

---

## Task 36.2 — Add clean-path arena smoke scenario

### Description

Add one small arena-like scenario that uses catalog archetypes.

### Technical description

Scenario example:

```text
CATALOG_ARENA_SMALL
```

Composition:

```text
frontier_village_core
goblin_camp_conflict
```

Participants:

```text
frontier_guard
goblin_raider
goblin_archer
```

Expected properties:

```text
entities spawn
combat values come from resolved archetypes
legacy role/faction projection exists only for runtime compatibility
simulation can tick
```

### Note

This is not a replacement for existing `COMBAT_ARENA_5V5` or stress tests.

### TDD

Add one integration smoke test:

```text
tests/integration/certification/test_catalog_arena_smoke.py
```

Avoid adding many catalog arena tests immediately.

### Acceptance checklist

- [ ] Scenario builds from catalog.
- [ ] Scenario has at least two factions.
- [ ] Entities have archetype/race/faction source IDs.
- [ ] Runtime combat can run at least one tick.
- [ ] No direct enemy source truth is required.
- [ ] Existing arena tests remain unchanged.
- [ ] Test is marked appropriately if slower than unit tests.

---

## Task 36.3 — Add migration comparison test

### Description

Compare a small legacy-built scenario and a catalog-built scenario at the semantic level.

### Technical description

Do not compare exact hashes because entity construction path may differ.

Compare:

```text
entity count
faction count
combat readiness
alive status
region ownership defaults
registry availability
tick execution success
```

### Note

This protects migration without forcing exact legacy parity.

### TDD

Add:

```text
tests/integration/certification/test_catalog_vs_legacy_scenario_semantics.py
```

### Acceptance checklist

- [ ] Legacy small scenario builds.
- [ ] Catalog small scenario builds.
- [ ] Both have valid entities.
- [ ] Both can run bounded ticks.
- [ ] Semantic comparison passes.
- [ ] Test does not require identical entity IDs or final hash.
- [ ] Differences are reported clearly.

---

# Phase 37 — Integrate relation projection into high-impact systems

## Goal

Use the already-defined `RelationProjectionService` in combat, quest, and region classification.

This phase must not define new relation semantics.

Phase 28 owns relation projection rules.

Phase 37 only wires existing projection into consumers.

---

## Phase 37 consumer boundary

Allowed in Phase 37:

```text
call EntityIdentityResolver
call RelationProjectionService
add projection result wrappers
add debug/source reporting
preserve legacy fallback path
extend existing combat/quest/region tests
```

Forbidden in Phase 37:

```text
adding new relationship axes
changing perspective schema
changing faction relationship schema
adding new enemy source-truth fields
rewriting combat resolution
rewriting quest system
rewriting regional ownership/influence logic
```

---

## Task 37.1 — Add relation projection wrapper to combat target selection

### Description

Make combat target filtering use `EntityIdentityResolver` and `RelationProjectionService` when clean identity is available.

### Technical description

Flow:

```text
source entity
→ EntityIdentityResolver.resolve(source)

candidate entity
→ EntityIdentityResolver.resolve(candidate)

source identity + candidate identity + context + perspective
→ RelationProjectionService.project_relation(...)

if projection is available:
    classify target using projected labels
else:
    use legacy fallback classification
```

Projected hostile labels:

```text
enemy
threat
intruder
prey
```

Non-hostile labels:

```text
ally
neutral
protected
ignored
opportunity_only
```

### Rules

Race alone must not determine enemy status.

Legacy monster/horde logic must remain available only through fallback.

Combat damage/resolution is out of scope.

### TDD

Add focused tests:

```text
hero perspective treats goblin warband as enemy
hero perspective treats merchant league as neutral
wild beast context produces threat only with territory context
legacy monster/horde still works through fallback
projection source appears in debug result
```

### Acceptance checklist

```text
[ ] Combat target classification uses identity resolver.
[ ] Combat target classification can use clean projection.
[ ] Legacy fallback still works.
[ ] Existing arena combat tests still pass.
[ ] Race alone does not determine enemy status.
[ ] Projection source is included in debug/result object.
```

---

## Task 37.2 — Add relation projection to quest target interpretation

### Description

Make quest target semantics support clean projected labels.

### Technical description

Quest target model may support:

```text
target_archetype_id
target_faction_id
target_projected_label
target_relationship_model
legacy_enemy_type
```

Resolution order:

```text
clean archetype/faction target
→ perspective projection
→ compatibility enemy projection
→ legacy enemy type fallback
```

### Rules

Do not remove old quest target support.

Do not require `enemy` as source truth.

### TDD

Add focused tests:

```text
quest can target goblin_warband through projected enemy relation
quest can target wildlife as contextual threat
legacy hunt quest still works
unresolved clean quest target fails clearly
```

### Acceptance checklist

```text
[ ] Quest target can resolve from clean faction/archetype.
[ ] Quest target can resolve through projected relation.
[ ] Legacy enemy quest still works.
[ ] Existing quest progression tests still pass.
[ ] Quest model does not require enemy as source truth.
[ ] Error messages explain unresolved target source.
```

---

## Task 37.3 — Add relation projection to region threat classification

### Description

Make region safety/threat evaluation use faction relationships, perspective, and context.

### Technical description

Inputs:

```text
region controlling faction
active populations
resolved entity/faction identities
selected perspective
danger level
territorial context
resource conflict context
```

Output:

```text
safe
neutral
contested
threatened
hostile
unknown
```

### Rules

Do not mutate region ownership.

Do not rewrite regional influence or conquest logic.

### TDD

Add tests near regional control/region semantics tests:

```text
town-controlled region is safe from hero perspective
goblin camp is hostile from hero perspective
wolf den is contextual threat
merchant road is contested when bandit module active
legacy region tests still pass
```

### Acceptance checklist

```text
[ ] Region threat classification uses perspective.
[ ] Faction relationship affects classification.
[ ] Contextual wildlife threat is supported.
[ ] Existing regional control tests still pass.
[ ] Classification does not mutate ownership.
[ ] Classification is deterministic.
```

---

# Phase 38 — Shrink legacy fallback maps safely

## Goal

Reduce hardcoded gameplay truth after catalog-backed and compatibility-backed paths are stable.

Do this only after catalog mode is default and strict matrix is passing.

---

## Task 38.1 — Move legacy records behind migration map

### Description

Every hardcoded gameplay record must be mapped to catalog or compatibility data.

### Technical description

Migration map fields:

```text
legacy_family
legacy_id
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

### Note

Do not delete records first. Map them first.

### TDD

Add architecture test:

```text
tests/architecture/test_legacy_content_migration_map.py
```

### Acceptance checklist

- [ ] Every legacy item has mapping.
- [ ] Every legacy recipe has mapping.
- [ ] Every legacy region has mapping.
- [ ] Every legacy enemy has archetype/projection mapping.
- [ ] Unmapped legacy gameplay records fail.
- [ ] Non-gameplay constants are excluded.
- [ ] Migration map is machine-readable.

---

## Task 38.2 — Add hardcoded gameplay guard

### Description

Prevent new hardcoded gameplay IDs from being added without catalog mapping.

### Technical description

Static scan targets:

```text
registry seed fallback blocks
enemy registry fallback
item registry fallback
recipe registry fallback
region/service fallback
test-only content factories if they define gameplay IDs
```

Allowed:

```text
test fixture IDs
non-gameplay constants
explicit migration exemptions
```

### Note

This is a guardrail, not a cleanup task.

### TDD

Add or extend architecture test:

```text
tests/architecture/test_no_new_hardcoded_gameplay_truth.py
```

### Acceptance checklist

- [ ] New unmapped gameplay ID fails.
- [ ] Existing mapped IDs pass.
- [ ] Test-only fixture IDs are allowed only in test paths.
- [ ] Failure message points to migration map.
- [ ] Guard runs in normal CI.
- [ ] Guard does not scan generated artifacts.

---

## Task 38.3 — Convert fallback warnings into strict errors by mode

### Description

Fallback behavior should depend on runtime content mode.

### Technical description

Behavior:

```text
catalog_strict:
    fallback usage = error

catalog_with_compatibility:
    compatibility projection = allowed
    hardcoded fallback = warning or error depending family

legacy_fallback:
    fallback usage = allowed

test_manual:
    fallback irrelevant unless registry seeding is requested
```

### Note

This makes hidden fallback impossible in strict mode.

### TDD

Add tests:

```text
strict mode fails on fallback enemy
compat mode allows legacy enemy projection
legacy mode allows fallback maps
```

### Acceptance checklist

- [ ] Strict mode fails on hardcoded fallback.
- [ ] Compatibility projection is not treated as hardcoded fallback.
- [ ] Legacy mode still works.
- [ ] Report clearly distinguishes projection from fallback.
- [ ] Existing tests choose correct mode explicitly.

---

# Phase 39 — First gated content pack implementation

## Goal

Implement the first horizontal content pack using the Phase 34 pack contract.

Do not redefine `ContentPackManifest` here.

This phase proves that the content system can scale horizontally after strict gates pass.

---

## Task 39.1 — Implement `frontier_extended_pack` manifest

### Description

Create the first real content pack manifest using the schema from Phase 34.

### Technical description

Pack ID:

```text
frontier_extended_pack
```

Suggested additions:

```text
orc clan
bandit route
dwarven mine
undead battlefield
forest wardens
merchant caravan
moon cult ruin
```

Required manifest fields:

```text
pack_id
display_name
version
dependencies
added_families
required_modules
required_compositions
required_scenarios
compatibility_projections
strict_gate_required
enabled_by_default
```

### Rules

Manifest must use the existing Phase 34 schema.

No new manifest fields are invented in Phase 39.

### TDD

Add:

```text
tests/integration/content_packs/test_frontier_extended_pack_manifest.py
```

Cases:

```text
manifest validates against Phase 34 schema
dependencies resolve
declared added families exist
required modules exist
required compositions exist
required scenarios exist
```

### Acceptance checklist

```text
[ ] frontier_extended_pack manifest exists.
[ ] Manifest uses Phase 34 schema.
[ ] Dependencies resolve.
[ ] Added families match pack content files.
[ ] Required modules/compositions/scenarios exist.
[ ] Pack can be disabled.
```

---

## Task 39.2 — Add first pack content data

### Description

Add the pack content using only existing mechanisms.

### Technical description

Required pack content folders:

```text
content_packs/frontier_extended_pack/content/living/*
content_packs/frontier_extended_pack/content/social/*
content_packs/frontier_extended_pack/content/entities/*
content_packs/frontier_extended_pack/content/world/*
content_packs/frontier_extended_pack/content/world_modules/*
content_packs/frontier_extended_pack/content/world_compositions/*
content_packs/frontier_extended_pack/content/simulation_scenarios/*
```

Required content categories:

```text
at least one faction
at least one population
at least one module
at least one composition
at least one scenario
```

### Rules

Pack may add content, not new engine systems.

Do not add:

```text
full diplomacy
weather system
lineage/history
large-scale politics
new combat engine
complex condition language
```

### TDD

Add pack validation tests:

```text
pack active data is reachable
pack reference graph passes
pack no-dead-active-data rule passes
pack resolver coverage passes
pack disabled does not affect base strict matrix
```

### Acceptance checklist

```text
[ ] Pack content loads when enabled.
[ ] Pack content is ignored when disabled.
[ ] Active pack data has consumer paths.
[ ] Pack references resolve.
[ ] Pack does not require new vertical subsystem.
[ ] Base strict matrix unchanged when pack disabled.
```

---

## Task 39.3 — Add first pack strict matrix rows

### Description

Add strict matrix rows proving the first pack is executable.

### Technical description

Example matrix rows:

```text
frontier_extended: bandit route pressure
frontier_extended: undead battlefield containment
frontier_extended: merchant caravan risk
frontier_extended: moon cult ruins pressure
frontier_extended: dwarven mine recovery
```

Each row must execute:

```text
load base + pack catalog
validate merged catalog
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

### TDD

Add:

```text
tests/integration/content_packs/test_frontier_extended_pack_strict_matrix.py
```

### Acceptance checklist

```text
[ ] Every first-pack matrix row loads.
[ ] Every row validates.
[ ] Every row produces WorldSpec.
[ ] Every row produces CompileContext.
[ ] Every row seeds runtime registries.
[ ] No row uses hidden legacy fallback.
[ ] Fingerprints are deterministic.
```

---

# Plan summary

```text
Phase 35 — Make catalog-backed mode the default runtime mode
Phase 36 — Migrate selected arena/certification setup to clean archetype path
Phase 37 — Replace bucket-only hostility in high-impact systems
Phase 38 — Shrink legacy fallback maps safely
Phase 39 — Larger fantasy content expansion, gated by consumer paths
```
