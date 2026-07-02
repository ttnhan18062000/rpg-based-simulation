---
status: authoritative
layer: guidelines
authority: P1
audience: developer
last_verified: 2026-06-27
tags: [content-authoring, world-modules, composition, scenario, dx, guide]
---

# Content Authoring Guide

**Who this is for:** A developer who has never touched `data/content/` before and wants to
add a world module, composition, or simulation scenario.

**What this is not:** A technical contract. For the full schema specification see
`docs/world/modules_contract.md`.

---

## 1. Introduction

There are three content types you can author:

| Type | Home directory | Schema |
|---|---|---|
| World module | `data/content/world_modules/` | `WorldModuleSpec` (Pydantic) |
| World composition | `data/content/world_compositions/` | `WorldCompositionSpec` (Pydantic) |
| Simulation scenario | `data/content/simulation_scenarios/` | `SimulationScenarioDefinition` (Pydantic) |

All three are YAML files discovered at load time. You do not register them anywhere — the
repository auto-discovers all `.yaml` and `.yml` files in these directories.

---

## 2. Quick Start — Add a World Module

### Step 1: Scaffold a starter YAML

```bash
make world-template WORLD=my_new_module
```

This generates a structurally valid YAML scaffold. Copy or rename it into
`data/content/world_modules/my_new_module.yaml`.

### Step 2: Fill in required fields

Every module must have at minimum:

```yaml
module_id: "my_new_module"          # unique across all module files
module_type: "settlement"           # see allowed types below
display_name: "My New Module"
```

See the full field reference in Section 3.

### Step 3: Validate

```bash
make world-validate WORLD=frontier_living_world
```

Schema errors (wrong field names, missing required fields) surface immediately.

> **Catalog ID errors** (wrong biome, ecology, population, faction IDs) do NOT surface
> during `make world-validate`. They surface at assembly time. See Sharp Edges (Section 7).

### Step 4: Include in a composition

Add your `module_id` to an existing composition's `modules` list (e.g.
`data/content/world_compositions/frontier_living_world.yaml`), or create a new composition
(Section 4).

### Step 5: Compile and inspect

```bash
make world-compile WORLD=frontier_living_world
make world-inspect WORLD=frontier_living_world
```

---

## 3. World Module Field Reference

Full `WorldModuleSpec` schema. The model uses `extra="forbid"` — unknown fields are rejected
with a clear error message.

### Identity fields

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `module_id` | str | yes | — | Unique across all YAML files; duplicate raises `ValueError` at load |
| `module_type` | str | yes | — | Must be one of 7 registered types (see below) |
| `display_name` | str (min 1) | yes | — | Human-readable label |
| `description` | str | no | `null` | Optional free-text description |
| `version` | str | no | `"1.0.0"` | Semver string |
| `schema_version` | str | no | `null` | Optional human label; not validated by schema |

### Allowed module types

```
terrain       settlement    ecology
economy       conflict      population    danger_zone
```

New types may be registered at runtime via `WorldModuleSpec.register_module_type()` — but
these 7 are the stable base set. If your content does not fit any type, contact the
maintainers before adding a new one.

### Dependency fields

| Field | Type | Default | Notes |
|---|---|---|---|
| `requires` | List[str] | `[]` | Module IDs that must be processed before this one; topological sort enforces order |
| `provides` | List[str] | `[]` | Semantic aliases this module advertises |
| `parameters` | List[ModuleParameterSpec] | `[]` | Exposed configurable variables |

### Structural contribution fields

| Field | Type | Notes |
|---|---|---|
| `regions` | List[RegionRecipeSpec] | Region layout recipes; each has `id`, `type`, `grid_bounds`, `terrain`, `hazard_level` |
| `population_recipes` | List[PopulationRecipeSpec] | Entity spawning recipes |
| `resource_recipes` | List[ResourceRecipeSpec] | Resource node recipes |
| `building_recipes` | List[BuildingRecipeSpec] | Building construct recipes |
| `observability_tags` | List[str] | Structural audit tags — **not** `tags` (see Sharp Edges) |
| `quest_definitions` | List[QuestDefinition] | Quest definitions; merged by WorldAssemblyResolver |

### Catalog reference fields

These must match IDs registered in the catalog. Mismatches surface at assembly time.

| Field | Notes |
|---|---|
| `biomes` | Biome layout template refs |
| `ecologies` | Ecology layout template refs |
| `populations` | Population template refs |
| `relationships` | Relationship layout refs |
| `factions` | Associated faction IDs |
| `resources` | Dict of resource type → count |
| `buildings` | Dict of building type → count |
| `services` | Dict of service type → count |

### Example minimal module

```yaml
module_id: "desert_outpost"
module_type: "settlement"
display_name: "Desert Outpost"
description: "A small trade outpost on the edge of the desert."
regions:
  - id: "outpost_center"
    type: "town"
    grid_bounds: [5, 5, 20, 20]
    terrain: "sand"
    hazard_level: 0.2
factions: ["desert_traders"]
observability_tags: ["settlement", "trade"]
```

---

## 4. Adding a World Composition

A composition assembles a set of modules into a named world. File location:
`data/content/world_compositions/<world_id>.yaml`.

### Step 1: Create the composition file

```yaml
schema_version: "worldcomposition.v1"
world_id: "my_world"                       # unique world identifier
name: "My World"
description: "A short description."
modules:
  - "frontier_village_core"                # reference existing module IDs
  - "desert_outpost"                       # your new module
default_perspectives:
  - "hero_guild_perspective"
generation_seed: 42
```

`provided_features` belongs here (on the composition), not on individual module specs.

### Step 2: Validate and compile

```bash
make world-validate WORLD=my_world
make world-compile WORLD=my_world
make world-inspect WORLD=my_world
```

### Step 3: Inspect module load order

```bash
make world-list
```

---

## 5. Adding a Simulation Scenario

Scenarios are entries in a scenarios YAML file under
`data/content/simulation_scenarios/`. You append to an existing file or create a new one.

### Schema fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | str | yes | Unique scenario identifier |
| `world_composition` | str | yes | Must match an existing `world_id` |
| `perspective` | str | yes | Simulation perspective string |
| `focus_modules` | List[str] | yes | Must match loaded module IDs |
| `initial_conditions` | Dict[str, Any] | no | Keys must be in the allowed set |
| `template_id` | str | no | Optional; triggers template validation at load |

### Allowed `initial_conditions` keys

Only these 8 keys are valid. Any other key raises a `ValueError` at load time with a
clear message listing the allowed set. Source: `src/scenarios/schema.py:ALLOWED_INITIAL_CONDITION_CATEGORIES`.

```
region_pressure          faction_activity
resource_scarcity        population_alertness
territorial_intrusion    trade_route_risk
danger_level_override    spawn_bias
```

### Example scenario entry

```yaml
- id: "desert_outpost_pressure"
  world_composition: "my_world"
  perspective: "hero_guild_perspective"
  focus_modules: ["desert_outpost"]
  initial_conditions:
    region_pressure: "high"
    faction_activity: "medium"
```

### Run a sweep

```bash
make sim-sweep CONFIG=data/sweeps/default.json
```

---

## 6. Make Targets

| Target | When to use |
|---|---|
| `make world-template WORLD=<id>` | Starting point — generates a valid scaffold YAML for a new module |
| `make world-validate WORLD=<id>` | Check schema validity after editing a module or composition |
| `make world-compile WORLD=<id>` | Compile world to AuthoritativeState; surfaces catalog ID errors |
| `make world-resolve WORLD=<id>` | Resolve compositional specs to compiled assets |
| `make world-inspect WORLD=<id>` | Inspect structural metrics of an assembled world |
| `make world-list` | List all loaded world modules and their types |
| `make catalog-list` | List registered catalog IDs by type (biomes, ecologies, populations, factions, regions) |
| `make sim-sweep CONFIG=<path>` | Run a scenario sweep matrix across a CONFIG file |
| `make knowledge-index-update` | After adding docs — incremental reindex for semantic search |

---

## 7. Sharp Edges

### 7.1 `observability_tags` — not `tags`

The tag field on `WorldModuleSpec` is called `observability_tags`. There is no `tags` field.

```yaml
# WRONG — raises ValueError: extra inputs are not permitted
tags: ["settlement"]

# CORRECT
observability_tags: ["settlement"]
```

`extra="forbid"` on the Pydantic model rejects any unknown field with a clear error.

### 7.2 `provided_features` does not belong on modules

`provided_features` is a field on `WorldCompositionSpec`, not `WorldModuleSpec`. Adding it
to a module YAML raises `ValueError: extra inputs are not permitted`.

```yaml
# WRONG on a module file
provided_features: ["has_trade"]

# CORRECT — put it on the composition file instead
provided_features: ["has_trade"]   # in world_compositions/<id>.yaml
```

### 7.3 Catalog ID constraints

The fields `biomes`, `ecologies`, `populations`, `relationships`, and `factions` must
reference IDs that are registered in the catalog. There is no pre-flight check in
`make world-validate` — the error surfaces only when the assembly pipeline calls
`CatalogRepository.resolve()`.

**If you see `CatalogResolutionError` at compile time**, one of your catalog refs is not
registered. Run `make world-list` to see which IDs are loaded, then verify your refs.

Use namespace prefixes to avoid collision with IDs from other modules (e.g.
`desert:desert_traders` rather than `desert_traders`).

### 7.4 `hazard_level` is a region field, not a top-level template field

`hazard_level` belongs inside the `regions` list on an individual region, not at the
module's top level:

```yaml
# CORRECT
regions:
  - id: "outpost_center"
    terrain: "sand"
    hazard_level: 0.2    # here, on the region

# WRONG — top-level hazard_level is not a recognized module field
hazard_level: 0.2
```

### 7.5 ContentUsageMatrix — no manual registration needed

As of TCK-20260627-P2K-CONTENT-MATRIX, `ContentUsageMatrix` is auto-discovered. Any
`.yaml` file you add under `data/content/` is automatically picked up. You do not need
to manually register new files in `src/content/matrix.py`.

### 7.6 Duplicate `module_id`

If two YAML files (in any subdirectory of `data/content/world_modules/`) declare the same
`module_id`, `WorldModuleRepository.load_all()` raises `ValueError` at startup. Ensure your
`module_id` is globally unique.

---

## 8. FAQ

**Q: `make world-validate` passes but `make world-compile` fails with a catalog error.**

A: Validate checks schema only. Catalog ref resolution (biomes, ecologies, populations,
factions) happens at assembly/compile time. Verify your catalog IDs are registered.

**Q: I added a YAML file but the module doesn't appear in `make world-list`.**

A: Confirm the file is under `data/content/world_modules/` and that it has a `module_id`
field. Files missing `module_id` are skipped with a `ValueError`.

**Q: Pydantic says "extra inputs are not permitted" for a field I think is valid.**

A: Check the exact field name. Common mistakes: `tags` instead of `observability_tags`;
`provided_features` on a module instead of a composition; any typo in a field name.

**Q: My scenario fails to load with "Unknown initial_condition categories".**

A: Only the 8 keys in Section 5 are allowed. Remove or rename the unrecognized key.

**Q: Where do I find valid catalog IDs for biomes, ecologies, factions?**

A: Run `make catalog-list` — it prints all registered IDs by type without requiring
world assembly. See Section 9 for details.

---

## 9. Catalog ID Browser

The `make catalog-list` target prints all registered catalog IDs grouped by type.
No world assembly is required — it reads `data/content/` directly.

```bash
make catalog-list
```

Sample output:

```
=== biomes (4) ===
  coastal_wetlands
  deep_forest
  highland_plains
  ...

=== ecologies (6) ===
  coastal_fauna
  ...

=== populations (12) ===
  ...
```

### Options

```bash
# Show only specific types
python3 tools/catalog_list.py --types biomes factions

# Show all catalog types (terrain, buildings, resources, items, ...)
python3 tools/catalog_list.py --all
```

### When to use

Run `make catalog-list` before authoring a new world module to find valid values for:

- `biomes` field → use IDs from the **biomes** section
- `ecologies` field → use IDs from the **ecologies** section
- `populations` field → use IDs from the **populations** section
- `factions` field → use IDs from the **factions** section
- `regions` field → use IDs from the **regions** section (runtime region definitions)

> **Tip:** Catalog IDs are validated only at assembly time (`make world-compile`), not
> at `make world-validate`. Use `make catalog-list` to verify your refs before compiling.

---

## 10. Scenario Templates Reference

A scenario may declare a `template_id` to opt into template-based validation.
Templates define allowed structure (required world features, perspective types,
initial condition keys, focus modules) — they do not contain scripted behavior.

Source: `src/scenarios/templates.py`

### 10.1 Template registry

Ten built-in templates are available:

| Template ID | World Type | When to Use |
|---|---|---|
| `territorial_pressure` | Faction + ecology | Faction competition for territory; ecology drives pressure |
| `raider_conflict` | Faction + combat | Raid-and-defence loop; escalating danger |
| `trade_route_risk` | Trade + faction | Merchant route threatened by factions; escort/secure |
| `resource_recovery` | Resource node + ecology | Depleted resource node recovery; contested harvest |
| `settlement_defense` | Settlement + faction + combat | Settlement under sustained threat; fortification focus |
| `cult_ritual_pressure` | Ruins + cult faction | Cult activity in ruins escalates; investigative response |
| `undead_containment` | Undead ecology + battlefield | Undead lifecycle pressure; containment and purge |
| `wildlife_intrusion` | Wildlife ecology | Wildlife encroaches on territory; ecological conflict |
| `caravan_escort` | Trade route + faction | Escort a caravan against faction and danger threats |
| `mine_reopening` | Resource node + faction territory | Contested reopening of a depleted extraction site |

### 10.2 Template details

#### `territorial_pressure`
- **Required world features:** `faction_territory`, `ecology_module`
- **Perspective types:** `territorial`
- **Allowed initial_conditions:** `region_pressure`, `faction_activity`, `population_alertness`, `territorial_intrusion`
- **Focus modules:** `territory_control`, `faction_influence`
- **Use when:** Two or more factions are competing for ecologically rich territory.

#### `raider_conflict`
- **Required world features:** `faction_territory`, `combat_module`
- **Perspective types:** `militant`, `defensive`
- **Allowed initial_conditions:** `region_pressure`, `faction_activity`, `danger_level_override`, `spawn_bias`
- **Focus modules:** `combat_resolution`, `faction_influence`, `raid_response`
- **Use when:** Modelling raid-and-counter-raid cycles with escalating danger levels.

#### `trade_route_risk`
- **Required world features:** `trade_route`, `faction_territory`
- **Perspective types:** `merchant`, `defensive`
- **Allowed initial_conditions:** `trade_route_risk`, `faction_activity`, `danger_level_override`
- **Focus modules:** `trade_economics`, `faction_influence`, `route_security`
- **Use when:** A trade route passes through contested territory; threat level modulates trade flow.

#### `resource_recovery`
- **Required world features:** `resource_node`, `ecology_module`
- **Perspective types:** `resource_seeker`, `territorial`
- **Allowed initial_conditions:** `resource_scarcity`, `region_pressure`, `population_alertness`
- **Focus modules:** `resource_ecology`, `harvesting_economics`
- **Use when:** A depleted resource node is recovering and multiple factions seek access.

#### `settlement_defense`
- **Required world features:** `settlement`, `faction_territory`, `combat_module`
- **Perspective types:** `defensive`, `militant`
- **Allowed initial_conditions:** `region_pressure`, `faction_activity`, `danger_level_override`, `population_alertness`, `spawn_bias`
- **Focus modules:** `settlement_protection`, `faction_influence`, `combat_resolution`
- **Use when:** A settlement faces sustained external threat; focus on fortification and reinforcement.

#### `cult_ritual_pressure`
- **Required world features:** `ruins_ecology`, `cult_faction`
- **Perspective types:** `investigative`, `defensive`
- **Allowed initial_conditions:** `region_pressure`, `faction_activity`, `danger_level_override`
- **Focus modules:** `cult_activity`, `faction_influence`
- **Use when:** A cult is performing rituals in ruins with escalating effect on the surrounding region.

#### `undead_containment`
- **Required world features:** `undead_ecology`, `battlefield_terrain`
- **Perspective types:** `defensive`, `militant`
- **Allowed initial_conditions:** `region_pressure`, `danger_level_override`, `spawn_bias`, `population_alertness`
- **Focus modules:** `undead_lifecycle`, `combat_resolution`, `faction_influence`
- **Use when:** Undead are spreading from a battlefield; containment is the primary objective.

#### `wildlife_intrusion`
- **Required world features:** `wildlife_ecology`, `ecology_module`
- **Perspective types:** `territorial`, `defensive`
- **Allowed initial_conditions:** `territorial_intrusion`, `region_pressure`, `population_alertness`
- **Focus modules:** `wildlife_behavior`, `territory_control`
- **Use when:** Wildlife encroaches on settled or faction-held territory; ecological conflict.

#### `caravan_escort`
- **Required world features:** `trade_route`, `faction_territory`
- **Perspective types:** `merchant`, `defensive`, `militant`
- **Allowed initial_conditions:** `trade_route_risk`, `faction_activity`, `danger_level_override`, `spawn_bias`
- **Focus modules:** `trade_economics`, `route_security`, `combat_resolution`
- **Use when:** Escorting high-value cargo through dangerous or contested trade corridors.

#### `mine_reopening`
- **Required world features:** `resource_node`, `faction_territory`
- **Perspective types:** `resource_seeker`, `defensive`
- **Allowed initial_conditions:** `resource_scarcity`, `region_pressure`, `faction_activity`, `danger_level_override`, `spawn_bias`
- **Focus modules:** `resource_ecology`, `faction_influence`, `territory_control`
- **Use when:** An exhausted mine is being reclaimed; factions compete for extraction rights.

### 10.3 Using a template in a scenario

```yaml
- id: "frontier_raiders"
  world_composition: "frontier_living_world"
  perspective: "hero_guild_perspective"
  focus_modules: ["combat_resolution", "faction_influence"]
  initial_conditions:
    region_pressure: "high"
    danger_level_override: "elevated"
  template_id: "raider_conflict"   # triggers template validation at load
```

Template validation fires at load time — if `initial_conditions` contains a key
not in the template's `allowed_initial_conditions`, a clear `ValueError` is raised.
