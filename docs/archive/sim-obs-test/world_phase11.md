# Phase 11 — Data-Driven Worldbuilding Foundation

Phase 11 should start a new major component:

```text
Worldbuilding Framework
```

Its purpose:

```text
store world topology and setup as file-based specifications
validate world definitions
compile them into AuthoritativeState
support future Scenario Lab workflows
```

This is **not yet the full lab**.

Phase 11 should focus on:

```text
world definition
world validation
world compilation
world storage
basic tooling
extensibility
```

Not yet:

```text
automatic long-run experiment workflow
massive world generation
visual editor
database storage
full mutation lab
full balancing workflow
AI world generation
```

---

# Phase 11 Main Objective

Build a file-based system where users/tools can define worlds like:

```text
world topology
regions
factions
entities
resources
buildings
quests
strategic setup
observability intent
validation rules
```

Then the system can:

```text
load world spec
validate world spec
compile world spec into simulation state
run existing simulation engine
connect to Observatory later
```

---

# Important architecture idea

Separate these three things:

```text
WorldSpec
ScenarioSpec
ExperimentSpec
```

They are related but not the same.

## 1. WorldSpec

Defines the world itself.

Example:

```text
map size
regions
terrain
resources
buildings
factions
entity population
spawn rules
```

## 2. ScenarioSpec

Defines what we want to test in that world.

Example:

```text
resource economy pressure
combat balance
quest progression
pathing bottleneck
strategic overload
```

## 3. ExperimentSpec

Defines how to run it.

Example:

```text
seeds
ticks
repeat count
observability mode
mining mode
baseline comparison
```

Phase 11 should mainly implement **WorldSpec**.

ScenarioSpec and ExperimentSpec can be prepared as extension points.

---

# Phase 11 Milestones

```text
Milestone 67 — WorldSpec File Schema
Milestone 68 — World Repository and Versioning
Milestone 69 — World Validation Layer
Milestone 70 — World Compiler to AuthoritativeState
Milestone 71 — World Template and Recipe System
Milestone 72 — World CLI / Tooling
Milestone 73 — Worldbuilding Test Strategy
Milestone 74 — Resource and Storage Guardrails
```

---

# Milestone 67 — WorldSpec File Schema

## Goal

Define the first stable world definition format.

Recommended first format:

```text
YAML or JSON
```

My recommendation:

```text
YAML for humans
JSON schema internally for validation
```

File layout:

```text
worlds/
  resource_valley/
    world.yaml
    README.md
  combat_arena/
    world.yaml
  village_sandbox/
    world.yaml
```

---

## Minimal WorldSpec structure

```yaml
schema_version: worldspec.v1
world_id: resource_valley_basic
name: Resource Valley Basic
description: Basic resource economy world for worker/resource/shop testing.

topology:
  width: 100
  height: 100
  coordinate_system: grid

regions:
  - id: village
    type: settlement
    bounds: [0, 0, 30, 30]

factions:
  - id: villagers
    type: civilian

entities:
  populations:
    - id: workers
      count: 50
      role: worker
      faction: villagers
      spawn_region: village

resources:
  nodes:
    - id: wood_zone
      resource_type: wood
      count: 20
      region: forest

buildings:
  - id: village_shop
    type: shop
    region: village

quests: []

validation:
  expected_min_entities: 1
  allow_overlapping_regions: false
```

Do not make the schema too complex yet.

---

## Core sections

Phase 11 should support these sections:

```text
metadata
topology
regions
factions
entities
resources
buildings
quests
strategic_setup
validation
tags
```

Keep these optional where possible:

```text
quests
strategic_setup
observability_intent
mutation_rules
```

---

## Required tests

```text
tests/unit/worldbuilding/test_worldspec_schema.py
```

Test cases:

```text
[ ] valid minimal world spec loads
[ ] missing schema_version is rejected
[ ] missing world_id is rejected
[ ] invalid topology size is rejected
[ ] duplicate IDs are rejected
[ ] unknown top-level section is rejected or warned based on policy
[ ] optional sections can be omitted
```

Important anti-drift test:

```text
[ ] schema test does not compile world into engine state
```

Schema validation and compilation must be separate.

---

# Milestone 68 — World Repository and Versioning

## Goal

Create a file-based world storage layer.

Component:

```text
WorldRepository
```

Responsibilities:

```text
list worlds
load world spec
save world spec
validate path safety
track schema version
resolve world asset paths
```

---

## Recommended directory

```text
data/worlds/
  resource_valley_basic/
    world.yaml
    assets/
    notes.md
  combat_arena_basic/
    world.yaml
  village_sandbox_basic/
    world.yaml
```

Later:

```text
data/worlds_generated/
data/worlds_experiments/
data/worlds_archived/
```

---

## World manifest

Add optional top-level index:

```text
data/worlds/world_index.json
```

Fields:

```text
world_id
name
path
schema_version
tags
created_at
updated_at
status
```

Status:

```text
DRAFT
VALIDATED
DEPRECATED
BROKEN
```

---

## Required tests

```text
tests/unit/worldbuilding/test_world_repository.py
```

Test cases:

```text
[ ] repository lists worlds
[ ] repository loads world by ID
[ ] missing world returns clear error
[ ] duplicate world_id is rejected
[ ] path traversal is blocked
[ ] invalid YAML returns clear error
[ ] world_index can be rebuilt from files
```

Critical security test:

```text
[ ] world_id="../../etc/passwd" is rejected
```

---

# Milestone 69 — World Validation Layer

## Goal

Prevent users/tools from creating impossible or misleading worlds.

This is not full game logic validation yet.

It is a **high-level world integrity layer**.

Component:

```text
WorldValidator
```

---

# Validation levels

Use levels:

```text
ERROR
WARNING
INFO
```

## ERROR

World cannot compile or should not run.

Examples:

```text
duplicate entity IDs
entity references unknown faction
resource node outside topology
region bounds outside map
building references unknown region
spawn region does not exist
negative entity count
invalid coordinate
quest references missing entity/resource
```

## WARNING

World can run, but may be suspicious.

Examples:

```text
no resources
no buildings
no factions
all entities spawn in one tile
very dense region
unreachable-looking resource zone
shop has zero gold
combat scenario has no enemies
resource scenario has no workers
```

## INFO

Useful metadata.

Examples:

```text
large world
high entity count
many resources
long expected run
```

---

# Core validation categories

```text
identity validation
reference validation
topology validation
population validation
region validation
resource validation
building validation
quest validation
strategic setup validation
balance sanity validation
storage budget validation
```

---

## Important concept: extensible rules

Validation should use pluggable rules:

```text
WorldValidationRule
```

Each rule:

```text
rule_id
severity
description
applies_to
validate(world_spec)
```

Example:

```text
WORLD-REF-001: entity faction must exist
WORLD-TOPO-001: region bounds must fit inside map
WORLD-POP-001: population count must be non-negative
WORLD-RES-001: resource region must exist
```

This keeps future extension clean.

---

## Required tests

```text
tests/unit/worldbuilding/test_world_validator.py
tests/unit/worldbuilding/test_world_validation_rules.py
```

Test cases:

```text
[ ] unknown faction reference is ERROR
[ ] duplicate region ID is ERROR
[ ] region outside topology is ERROR
[ ] negative population count is ERROR
[ ] no resources in resource world is WARNING
[ ] high entity density is WARNING
[ ] valid world has no ERROR
[ ] validation result is deterministic
[ ] validation rule IDs are stable
```

Anti-misdirection tests:

```text
[ ] validator does not silently auto-fix invalid world
[ ] warnings do not block compilation unless strict mode is enabled
[ ] unknown future section is handled by policy, not ignored accidentally
```

---

# Milestone 70 — World Compiler to AuthoritativeState

## Goal

Convert validated `WorldSpec` into engine state.

Component:

```text
WorldCompiler
```

Input:

```text
WorldSpec
seed
compile_options
```

Output:

```text
AuthoritativeState
WorldCompileReport
```

---

# Compiler should be deterministic

Same world spec + same seed should produce same state.

That is critical.

```text
world.yaml + seed 42 -> same AuthoritativeState every time
```

---

## Compiler stages

```text
1. compile topology
2. compile regions
3. compile factions
4. compile resources
5. compile buildings
6. compile entities
7. compile quests
8. compile strategic setup
9. run post-compile validation
10. produce compile report
```

---

## Compile report

Write:

```text
world_compile_report.json
```

Fields:

```text
world_id
seed
entity_count
region_count
resource_node_count
building_count
quest_count
warnings
compile_duration_ms
state_hash
```

---

## Required tests

```text
tests/unit/worldbuilding/test_world_compiler.py
tests/integration/worldbuilding/test_world_compile_to_state.py
tests/certification/test_world_compile_determinism.py
```

Test cases:

```text
[ ] minimal world compiles
[ ] entities are created with correct faction
[ ] resources are placed inside topology
[ ] buildings are placed inside valid regions
[ ] quests reference valid entities/resources
[ ] same seed produces same state hash
[ ] different seed can produce different placement
[ ] invalid world cannot compile
[ ] compile report is written
```

Critical parity test:

```text
[ ] compiled world can run for N ticks without immediate structural failure
```

---

# Milestone 71 — World Template and Recipe System

## Goal

Allow worlds to be created with recipes instead of manually listing everything.

Example:

```yaml
entities:
  populations:
    - role: worker
      count: 500
      faction: villagers
      spawn_distribution:
        type: region_random
        region: village
```

This is better than requiring 500 entity records.

---

# Recipe types

Start with simple recipes:

## Population recipes

```text
count
role
faction
spawn_region
stats_profile
inventory_profile
cognition_profile
```

## Resource recipes

```text
resource_type
count
region
density
respawn_policy optional
```

## Building recipes

```text
building_type
count
region
service_profile
```

## Region recipes

```text
grid_bounds
type
terrain
hazard_level
```

---

# Do not overbuild yet

Do not implement:

```text
procedural terrain generator
complex road network generator
biome simulation
visual map editor
multi-layer world editor
```

Phase 11 needs basic recipes only.

---

## Required tests

```text
tests/unit/worldbuilding/test_world_recipes.py
```

Test cases:

```text
[ ] population recipe expands to expected entity count
[ ] resource recipe expands to expected node count
[ ] building recipe expands to expected building count
[ ] recipe expansion is deterministic by seed
[ ] recipe cannot create objects outside topology
[ ] recipe IDs are stable or traceable
```

Anti-misdirection test:

```text
[ ] recipe expansion does not bypass validation
```

Recipe output must still pass validation.

---

# Milestone 72 — World CLI / Tooling

## Goal

Make worldbuilding usable without writing code.

Add CLI commands:

```text
rpg-world list
rpg-world validate <world_id>
rpg-world compile <world_id> --seed 42
rpg-world inspect <world_id>
rpg-world create-template <template_name> <world_id>
```

Or if you prefer one CLI:

```text
rpg-observe world list
rpg-observe world validate <world_id>
rpg-observe world compile <world_id> --seed 42
```

---

## CLI behavior

```text
validate
  -> shows ERROR/WARNING/INFO

compile
  -> refuses if ERROR
  -> allows WARNING unless --strict
  -> writes compile report
```

---

## Required tests

```text
tests/cli/test_world_cli.py
```

Test cases:

```text
[ ] list worlds
[ ] validate valid world
[ ] validate invalid world returns non-zero
[ ] compile valid world
[ ] compile invalid world fails
[ ] strict mode treats warnings as failure
[ ] create-template writes valid starter world
```

---

# Milestone 73 — Worldbuilding Test Strategy

## Goal

Avoid misdirection during implementation.

This is important because worldbuilding can easily become fake-complete: files exist, but generated worlds are invalid or useless.

---

# Required test layers

## 1. Schema tests

Validate file shape only.

```text
WorldSpec loads / rejects invalid shape
```

## 2. Validation rule tests

Validate high-level logic.

```text
unknown faction
bad region bounds
invalid spawn region
```

## 3. Compiler tests

Validate conversion to engine state.

```text
WorldSpec -> AuthoritativeState
```

## 4. Determinism tests

Validate same spec + seed.

```text
same hash every time
```

## 5. Smoke simulation tests

Validate compiled world can run.

```text
compile world -> run 10 ticks -> no structural crash
```

## 6. Observatory integration tests

Not full Phase 12 yet, but one smoke test:

```text
compiled world -> run -> artifacts exist
```

---

# Anti-misdirection test rules

Must add tests that prevent fake success:

```text
[ ] validation must fail before compilation for ERRORs
[ ] compiler must not silently drop invalid references
[ ] compiler must not auto-create missing factions/regions
[ ] generated entity count must match requested count
[ ] same seed must produce same state hash
[ ] warnings must be visible in report
[ ] unknown schema version must fail clearly
[ ] future fields must be preserved or rejected by policy
```

---

# Milestone 74 — Resource and Storage Guardrails

## Goal

Prevent worldbuilding from creating impossible workloads.

Since later the lab will run many worlds/seeds/ticks, Phase 11 needs early guardrails.

---

# Budget fields

Add optional budget section:

```yaml
budgets:
  max_entities: 1000
  max_regions: 50
  max_resource_nodes: 500
  max_buildings: 100
  max_expected_artifact_mb: 500
```

---

# Validation warnings/errors

Examples:

```text
entity count > max_entities -> ERROR or WARNING based on profile
resource nodes too high -> WARNING
world area too large -> WARNING
expected artifact size too high -> WARNING
```

---

# Profiles

Use simple profiles:

```text
local_dev
ci
long_run_lab
```

Example:

| Profile        | Entity limit | Purpose             |
| -------------- | -----------: | ------------------- |
| `local_dev`    |        1,000 | fast iteration      |
| `ci`           |          500 | stable CI           |
| `long_run_lab` |       10,000 | heavier experiments |

---

## Required tests

```text
tests/unit/worldbuilding/test_world_budget_guardrails.py
```

Test cases:

```text
[ ] local_dev rejects oversized world
[ ] long_run_lab allows larger world
[ ] estimated artifact size warning appears
[ ] budget report is included in validation result
```

---

# Phase 11 End-to-End Flow

At the end of Phase 11:

```text
1. User/tool creates world.yaml.
2. WorldRepository loads it safely.
3. WorldValidator checks high-level world rules.
4. WorldCompiler compiles it into AuthoritativeState.
5. Compile report is written.
6. Compiled world can run in simulation.
7. CLI can list, validate, inspect, and compile worlds.
8. Basic resource/storage guardrails prevent huge accidental worlds.
```

---

# Minimal Phase 11 deliverables

Do not build the full lab yet.

Minimum implementation:

```text
WorldSpec schema
WorldRepository
WorldValidator
WorldCompiler
basic recipes
CLI commands
determinism tests
budget guardrails
```

Minimum example worlds:

```text
resource_valley_basic
combat_arena_basic
village_sandbox_basic
pathing_bottleneck_basic
```

---

# What Phase 11 should not do yet

```text
automatic experiment workflow
AI world generation
visual scenario editor
database storage
advanced procedural terrain
massive mutation system
full balance lab
automatic mining execution
```

Those belong later.

---

# Phase 12 preview

After Phase 11, the next big layer should be:

```text
Scenario Lab Workflow
```

That would connect:

```text
WorldSpec
+ ScenarioSpec
+ ExperimentSpec
+ Observatory
+ Mining
```

Into one automated workflow:

```text
create/load world
validate world
compile world
run simulation
record observability
analyze report
store artifacts
compare baseline
recommend next experiment
```

But Phase 11 must first make worlds reliable.

---

# Final acceptance criteria for Phase 11

```text
[ ] Worlds can be stored as files.
[ ] World specs have stable schema.
[ ] World repository loads safely.
[ ] Validation catches invalid high-level concepts.
[ ] Compiler creates AuthoritativeState.
[ ] Same world + same seed compiles deterministically.
[ ] Basic recipes work.
[ ] CLI can list/validate/compile worlds.
[ ] Budget guardrails exist.
[ ] Invalid worlds cannot silently compile.
[ ] Compiled worlds can run smoke simulations.
```

# My recommendation

Treat Phase 11 as:

```text
Data-Driven Worldbuilding Foundation
```

Not as:

```text
Scenario Lab
```

The system direction should be:

```text
Phase 11: Worldbuilding foundation
Phase 12: Scenario/experiment workflow lab
Phase 13: Mutation and balance lab
Phase 14: AI-assisted world/scenario generation
```

This keeps the implementation extensible but controlled.
