---
status: active
layer: engine
authority: P1
audience: agent
tags: [worldgen, worldmodules, worldassembly, composition, procedural, epic]
---

# World Generation: Strong Module Foundation — Epic Proposal

## Vision

A self-describing, parameterizable module system where worlds are composed from reusable building blocks. Strong enough for manual authoring today, structured enough for agent-driven world generation tomorrow. CLI is a thin wrapper over the core pipeline — the module schema and composition resolver are the product.

## Confirmed Decisions

| Decision | Choice |
|---|---|
| WorldModuleSpec versioning | Consolidate worldmodule.v1 + v2 into one unified format. No schema_version branching during implementation phase. |
| Parameter expressions | Full expression support — `"{base} + {scale} * 2"` valid in module recipe fields. Constraint validation (min/max, allowed_values) enforced at assembly time. |
| ID collision policy | Strict — duplicate IDs between modules are always a hard error. Module authors must be deliberate about IDs. |
| Quest scope | General `QuestDefinition` foundation schema only — structural, no runtime behavior, enables procedural generation later. |
| Procedural output | Generator writes `WorldCompositionSpec` YAML to disk under `data/content/world_compositions/generated/`. |
| Phase order | Foundation first → quest foundation → procedural → data expansion → scenario layer. CLI is support throughout. |

## Context: What Already Works

The following are complete and should NOT be re-implemented:

- **Direct compilation path**: `WorldSpec` YAML → `WorldCompiler.compile()` → `AuthoritativeState` ✅
- **Template expansion path**: `WorldTemplateSpec` recipes → `WorldTemplateExpander` → `WorldSpec` → compile ✅
- **Modular composition path**: `WorldCompositionSpec` + `WorldModuleSpec` v1 → `WorldAssemblyResolver.assemble()` → `ResolvedWorldBundle` → compile ✅
- **Topological sort**: Kahn's algorithm on `requires`/`provides` in `WorldAssemblyResolver` ✅
- **Provenance sidecar**: `ProvenanceManifest` with fingerprints and record origins ✅
- **Content catalog**: `CatalogRepository` loads all families (biomes, ecologies, factions, archetypes, etc.) ✅
- **10 world modules** in `data/content/world_modules/` (all worldmodule.v1) ✅
- **3 world compositions** in `data/content/world_compositions/` ✅

## Phase 1 — Unified Schema + Dead Code Activation

**Goal:** One canonical module format. Three schema-complete but never-called features actually work.

### WORLDMOD-UNIFY — Merge WorldModuleSpec into single format

**Scope:**
- Remove `schema_version` field from `WorldModuleSpec` (or fix it to one accepted value)
- Merge v2 fields (biomes, ecologies, services, relationships, populations) into the same class as v1 recipe fields (regions, population_recipes, resource_recipes, building_recipes)
- All fields optional/default empty — existing 10 modules stay valid without changes
- One resolver code path in `WorldAssemblyResolver.resolve_module_contribution()` — no v1/v2 branching
- Remove the brittle `_find_best_region_for_resource()` heuristic; replace with deterministic resolution via catalog resolvers
- Update `src/worldmodules/schema.py`, `src/worldmodules/normalizer.py`, `src/worldassembly/resolver.py`

**Acceptance criteria:**
- All 10 existing modules load and assemble without changes to their YAML
- A new module can declare biomes, ecologies, relationships, services alongside recipe fields
- `WorldAssemblyResolver` has one resolve path, not two

### WORLDMOD-PARAMS — Parameter expression engine

**Scope:**
- Implement expression evaluator in `src/worldmodules/` — accepts string template like `"{base} + {scale} * 2"`, substitutes declared parameter values, evaluates arithmetic
- Called inside `WorldAssemblyResolver.resolve_module_contribution()` before recipe field values are used
- Constraint validation at assembly time: `min`/`max` bounds and `allowed_values` checked against injected parameter values
- Hard fail with clear message if constraint violated: `"Module frontier_village_core: parameter population_scale=10 exceeds max=5"`
- Parameters not provided by composition ref use their declared `default`
- Update `src/worldassembly/resolver.py`, extend `src/worldmodules/schema.py` with `ModuleParameterSpec` evaluator

**Acceptance criteria:**
- A module with `population_count: "{base} + {scale} * 2"` and params `base=5, scale=3` resolves to 11
- Assembly fails with clear error if constraint violated
- Existing modules with no parameters are unaffected

### WORLDMOD-RELATIONS — Wire relationship resolver into assembly

**Scope:**
- `RelationshipResolver` exists in `src/content/resolver.py` but is never called during assembly
- In `WorldAssemblyResolver.resolve_module_contribution()`, resolve each relationship ID from the module's `relationships` list via `RelationshipResolver`
- Resolved `FactionRelationshipDefinition` records stored in `CompileContext`
- `WorldCompiler.compile()` consumes relationships from `CompileContext` and stores them in `AuthoritativeState` (faction relationship registry)
- Update `src/worldassembly/resolver.py`, `src/worldassembly/context.py`, `src/worldbuilding/compiler.py`

**Acceptance criteria:**
- `goblin_camp_conflict` module's `town_to_goblin_warband` relationship resolves and appears in compiled `AuthoritativeState`
- Assembly with an unknown relationship ID fails with `ResolverError` (consistent with other resolver failures)

### WORLDMOD-PACKS — Content pack validation at assembly time

**Scope:**
- When `WorldCompositionSpec.catalog_refs` references a pack, load and validate `ContentPackManifest`
- Check: pack exists, pack `enabled=True`, all pack `dependencies` are also enabled
- Hard fail at assembly start if any required pack is missing or disabled
- Update `src/worldassembly/resolver.py`

**Acceptance criteria:**
- Assembly of a composition referencing a disabled pack fails with clear error naming the pack
- Assembly of a composition with no pack refs is unaffected

---

## Phase 2 — Quest Definition Foundation

**Goal:** Modules can contribute quests. Assembly merges them. This is the structural authoring layer — no quest runtime behavior.

### WORLDMOD-QUEST-SCHEMA — QuestDefinition foundation schema

**Scope:**
- Define `QuestDefinition` dataclass in `src/worldbuilding/schema.py`:
  - `id: str` — unique identifier
  - `type: str` — one of: `escort`, `hunt`, `fetch`, `explore`, `defend`, `investigate`
  - `required_participant_tags: List[str]` — entity tags that must exist in world (e.g. `["hostile", "humanoid"]`)
  - `required_location_tags: List[str]` — region/biome tags required (e.g. `["wilderness", "dungeon"]`)
  - `reward_budget: int` — relative reward weight for procedural reward generation
  - `procedural_hints: Dict[str, Any]` — open-ended dict for procedural generation signals (e.g. `{difficulty: 3, escalation: true}`)
  - `tags: List[str]` — freeform tags for filtering and scoring
  - `source_module: Optional[str]` — set by assembly resolver, not authored
- Add `quest_definitions: List[QuestDefinition] = []` to `WorldSpec`
- No runtime behavior — `QuestDefinition` is authoring data only

**Acceptance criteria:**
- `WorldSpec` serializes/deserializes with `quest_definitions`
- A hand-authored `QuestDefinition` in a WorldSpec YAML loads without errors

### WORLDMOD-QUEST-MODULE — Module quest contribution and assembly merge

**Scope:**
- Add `quest_definitions: List[QuestDefinition] = []` to `WorldModuleSpec`
- `WorldAssemblyResolver.resolve_module_contribution()` collects quest definitions from each module
- Assembly merger deduplicates by `id` (same collision rule: duplicate ID = hard error)
- Sets `source_module` on each merged `QuestDefinition` for provenance
- `WorldSpec.quest_definitions` populated from merged module contributions after assembly
- Update `src/worldmodules/schema.py`, `src/worldassembly/resolver.py`

**Acceptance criteria:**
- A module declaring a `QuestDefinition` with id `mine_fetch_ore` produces a compiled world with that quest definition
- Two modules declaring quests with the same id fail assembly with collision error
- `source_module` field is set correctly on all merged definitions

---

## Phase 3 — Procedural Generation Pipeline

**Goal:** `generate --intent ...` produces a `WorldCompositionSpec` YAML. Output is a first-class file, inspectable and editable.

### WORLDGEN-SCORING — Module scoring against GenerationIntentSpec

**Scope:**
- `GenerationIntentSpec` already exists in `src/worldgeneration/schema.py` with: `seed`, `target_world_size`, `terrain_style`, `settlement_style`, `danger_level`, `resource_density`, `population_scale`, `required_modules`, `constraints`, `budget_profile`
- Implement `ModuleScorer` in `src/worldgeneration/generator.py`:
  - Score each module in `WorldModuleRepository` against the intent
  - Scoring dimensions: module `type` vs `settlement_style`/`terrain_style`, danger proxies (module tags, hazard-level resource nodes), resource density (count of resource recipes)
  - Output: `Dict[str, float]` — module_id → score
  - `required_modules` from intent always score maximum regardless

**Acceptance criteria:**
- `ModuleScorer.score(intent, module_repository)` returns scores for all available modules
- A `danger_level=3` intent scores `goblin_camp_conflict` and `undead_battlefield` higher than `frontier_village_core`
- `required_modules` appear in the output with maximum score

### WORLDGEN-COMPOSE — Composition generator from scored modules

**Scope:**
- Implement `ProceduralCompositionGenerator` in `src/worldgeneration/generator.py`:
  - Takes `GenerationIntentSpec` + scored module list
  - Selects modules: at least one `terrain` module, one `settlement` module (if settlement_style != "none"), fills remaining slots with highest-scoring compatible modules
  - Resolves `requires`/`provides` dependency graph — add dependency modules automatically
  - Emits `WorldCompositionSpec` with selected modules as `module_refs`, setting `order` deterministically from selection rank
  - Writes output to `data/content/world_compositions/generated/{world_id}.yaml`
  - `world_id` derived from intent fields + seed: e.g. `generated_frontier_danger3_s42`
- Expose via `src/worldbuilding/cli.py` as `world generate --danger-level 3 --settlement-style frontier --seed 42`

**Acceptance criteria:**
- Running the generator with a given intent and seed always produces the same YAML file
- Output YAML is a valid `WorldCompositionSpec` that assembles without errors
- At least one module of each required type is included
- Dependency modules are automatically included

### WORLDGEN-SEED-PARAMS — Seed-based parameter randomization

**Scope:**
- In `ProceduralCompositionGenerator`, for each selected module, sample parameter values using `generation_seed` + module position in selection order (deterministic RNG chain)
- Only parameters with `min` and `max` defined are randomized — parameters without bounds keep their default
- Sampled values set in `ModuleRefSpec.parameters` in the output composition YAML
- Same seed always produces the same parameter values for the same module

**Acceptance criteria:**
- Two runs with same seed and intent produce identical parameter values in output YAML
- Two runs with different seeds produce different parameter values
- Parameters without min/max bounds are not sampled

---

## Phase 4 — Data Expansion

**Goal:** Populate the now-solid schema with real content that exercises every new field.

### WORLDDAT-MIGRATE — Migrate existing modules to unified schema

**Scope:**
- Update all 10 existing modules in `data/content/world_modules/` to use the unified schema
- Add appropriate ecology/biome/relationship/service fields where they make domain sense:
  - `frontier_village_core`: add marketplace ecology reference, merchant_league relationship
  - `goblin_camp_conflict`: add `town_to_goblin_warband` relationship wired to catalog
  - `old_mine_resource_loop`: add a `mine_fetch_ore` quest definition
  - `wolf_den_near_forest`: add forest_edge biome reference
- Remove `schema_version` field from all YAML files

**Acceptance criteria:**
- All 10 modules load and assemble correctly after migration
- At least 4 modules have non-empty relationship, ecology, or biome fields
- At least 2 modules have quest_definitions
- Integration tests still pass

### WORLDDAT-NEWMODS — New modules demonstrating full schema

**Scope:**
- Write 4 new modules in `data/content/world_modules/`:
  - `forest_deep_ecology.yaml` — ecology-first, no recipes, rich biome/ecology fields, provides `deep_wilderness` feature
  - `ruins_mystery_quest.yaml` — quest-seeding focus, 2-3 `QuestDefinition` entries of type `investigate`/`explore`, requires `terrain` module
  - `trading_company_hub.yaml` — relationship-network focus, 3+ faction relationships, settlement type
  - `scalable_bandit_camp.yaml` — parameter-heavy, `population_count: "{base} + {danger_scale} * 3"` with min/max bounds, conflict type
- Each module must include `tags` for scoring and `provides` for dependency resolution

**Acceptance criteria:**
- All 4 modules load from `WorldModuleRepository`
- `scalable_bandit_camp` assembles with different `danger_scale` values producing different entity counts
- `ruins_mystery_quest` produces quest_definitions in assembled WorldSpec
- `trading_company_hub` contributes resolved relationships to CompileContext

### WORLDDAT-COMPOSITIONS — New world archetype compositions

**Scope:**
- Write 3 new compositions in `data/content/world_compositions/`:
  - `wilderness_survival.yaml` — no settlement module, ecology-heavy, high danger, 4-5 modules
  - `urban_political.yaml` — high faction relationship density, 2+ settlement modules, low danger
  - `dungeon_crawl.yaml` — uses `ruins_mystery_quest`, high danger, ecology-sparse, quest-dense
- Each composition must use `module_refs` (structured form, not shorthand `modules` list) to demonstrate parameter injection

**Acceptance criteria:**
- All 3 compositions assemble to valid `ResolvedWorldBundle`
- Each composition compiles to `AuthoritativeState` and simulation can tick for 10 ticks without error
- `dungeon_crawl` compiled world has non-empty `quest_definitions`

---

## Phase 5 — Scenario Foundation (Agent-Ready Layer)

**Goal:** A `ScenarioSpec` gives agents and the CLI a machine-readable contract for world requirements.

### WORLDSCEN-SCHEMA — ScenarioSpec schema

**Scope:**
- Define `ScenarioSpec` in `src/worldbuilding/schema.py` (or new `src/worldassembly/scenario.py`):
  - `scenario_id: str`
  - `name: str`, `description: str`
  - `required_features: List[str]` — features the world composition must provide
  - `forbidden_features: List[str]` — features the world must NOT provide
  - `min_tick_budget: int` — minimum ticks the scenario needs
  - `seed: int` — simulation seed
  - `world_refs: List[str]` — compatible composition IDs (optional; omit = any valid composition)
  - `observation_config: Dict[str, Any]` — open-ended, for simulation observation setup
  - `tags: List[str]`
- Store scenario YAML files under `data/content/simulation_scenarios/`
- Schema version: `simulationscenario.v1`
- Add 2-3 example scenario files covering the new world archetypes

**Acceptance criteria:**
- `ScenarioSpec` loads from YAML
- Example scenario files validate against schema

### WORLDSCEN-VALIDATE — Feature validation at assembly time

**Scope:**
- When assembling with a `ScenarioSpec` context, validate `WorldCompositionSpec.provided_features` satisfies all `required_features` and contains none of `forbidden_features`
- Hard fail with clear message: `"Scenario dungeon_crawler requires feature 'quest_seeding' not provided by composition 'frontier_living_world'"`
- Validation runs after `WorldAssemblyResolver.assemble()`, before `WorldCompiler.compile()`
- Optional at CLI: `world compile <world_id> --scenario <scenario_id>`

**Acceptance criteria:**
- Assembly with a non-matching scenario fails with a feature gap message
- Assembly with a matching scenario passes
- Assembly without `--scenario` flag is unaffected

### WORLDSCEN-PERSPECTIVES — Perspective resolution into CompileContext

**Scope:**
- `WorldCompositionSpec.default_perspectives` contains faction perspective IDs
- In `WorldAssemblyResolver.assemble()`, resolve each perspective ID via catalog `PerspectiveDefinition` records
- Store resolved perspectives in `CompileContext`
- `WorldCompiler.compile()` passes perspectives to `AuthoritativeState` (or observation config)

**Acceptance criteria:**
- A composition with `default_perspectives: ["hero_guild_perspective"]` produces a `CompileContext` with that perspective resolved
- Unknown perspective ID fails with `ResolverError`

---

## Out of Scope (explicit deferrals)

- Module version migration — no versioning during implementation phase
- Composition inheritance (`extends:`) — revisit after Phase 4 data proves the need
- Conflict resolution strategies other than `"error"` — strict is correct now
- Agent-facing world generation workflow — Phase 5 creates the ScenarioSpec contract; agent orchestration is a separate epic
- Advanced terrain (heightmaps, noise functions, moisture maps) — deferred indefinitely

## Ticket Output Folder

`tickets/todos/worldgen-module-epic/`
