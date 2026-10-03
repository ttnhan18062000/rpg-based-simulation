---
ticket_id: TCK-20260619-E11A-HERO-AUTHORING
phase: investigation
date: 2026-06-19
---

# Investigation: TCK-20260619-E11A-HERO-AUTHORING

## Current Behavior (file:line refs)

### sandbox_world (`data/worlds/sandbox_world/world.yaml`)

Schema version: `worldtemplate.v1`. **Not a WorldSpec/worldspec.v1 file.**
It is a recipe template consumed by `src/worldbuilding/recipe.py` via `WorldTemplateSpec`.
The recipe expander in `recipe.py:L169–L192` expands `entities.populations[]` into `worldspec.v1` `entities[]` entries before `WorldCompiler.compile()` is called.

Current `entities.populations`:
```yaml
entities:
  populations:
  - role: citizen
    count: 15
    faction: villagers
    spawn_region: town_center
  - role: monster
    count: 5
    faction: monsters
    spawn_distribution:
      type: region_random
      region: woods
```

No `role: hero` entries. Zero HERO entities compiled. The compile report at
`data/worlds/sandbox_world/world_compile_report.json` confirms 20 entities (15 citizens +
5 monsters, seed=42).

### urban_political (`data/worlds/urban_political/`)

Schema version: `worldcomposition.v1`. **Also not a direct worldspec.v1 file.**
The authoritative compiled form lives at
`data/worlds/urban_political/resolved/world.resolved.yaml` (schema: `worldspec.v1`).

Current `entities` in `world.resolved.yaml` (lines 72–120):
```
frontier_village_population_village_worker  — role: worker    (count 8)
frontier_village_population_frontier_guard  — role: guard     (count 3)
frontier_village_population_traveling_merchant — role: merchant (count 1)
frontier_village_population_village_blacksmith — role: blacksmith (count 1)
bandit_ambush_group_bandit_scout            — role: scout     (count 4)
merchant_caravan_traveling_merchant         — role: merchant  (count 2)
merchant_caravan_frontier_guard             — role: guard     (count 2)
trading_pop_0                               — role: merchant  (count 6)
```

No `role: hero` entries. Zero HERO entities. All 27 entities will receive class_id=NOVICE
(since `hero`, `worker`, `merchant`, `blacksmith`, `scout` roles hit the fallback path;
only `guard` maps to WARRIOR via `spawn_tables.yaml`).

### Key architectural distinction

- `sandbox_world/world.yaml` — **worldtemplate.v1** → must add entries under `entities.populations[]` with the `PopulationRecipeSpec` schema (fields: `role`, `count`, `faction`, `spawn_region` or `spawn_distribution`).
- `urban_political/` — **worldcomposition.v1** → module-assembled; the resolved spec lives at `resolved/world.resolved.yaml` (worldspec.v1). HERO entries need to be added to **`world.resolved.yaml`** directly (or injected via a module, but direct edit is in scope for this ticket).

---

## WorldSpec Population Entry Format

### For sandbox_world (worldtemplate.v1 recipe)

`src/worldbuilding/recipe.py:L25–L40` defines `PopulationRecipeSpec`:
```python
class PopulationRecipeSpec(BaseModel):
    role: str           # required, min_length=1
    count: Union[int, str]   # required; int or template expression string
    faction: str        # required
    spawn_region: str   # optional if spawn_distribution provided
    spawn_distribution: Optional[SpawnDistributionSpec]  # alternative to spawn_region
```

YAML entry for recipe template:
```yaml
entities:
  populations:
  - role: hero
    count: 3
    faction: villagers          # existing faction in sandbox_world
    spawn_region: town_center   # existing region in sandbox_world
```

The expander (`recipe.py:L181–L192`) generates an `id` as:
`pop_{role}_{faction}_{region}` → `pop_hero_villagers_town_center`

### For urban_political (worldspec.v1 — edit `world.resolved.yaml` directly)

`src/worldbuilding/schema.py:L51–L62` defines `PopulationSpec`:
```python
class PopulationSpec(BaseModel):
    id: str             # required, unique
    count: int          # required, ge=0
    role: str           # required
    faction: str        # required
    spawn_region: str   # required
    archetype_id: Optional[str]  # optional, set at assembly time
```

YAML entry for resolved world spec:
```yaml
- id: hero_adventurers
  count: 3
  role: hero
  faction: hero_guild
  spawn_region: hometown
```

---

## CLASS_REGISTRY Contents

File: `src/core/classes.py:L15–L51`

| Class ID   | Base HP | Base ATK | Base DEF | Starting Skills        | Starting Gear                  |
|------------|---------|----------|----------|------------------------|-------------------------------|
| `NOVICE`   | 100     | 10       | 5        | []                     | {}                            |
| `WARRIOR`  | 150     | 15       | 10       | [power_strike]         | MAIN_HAND: iron_sword, TORSO: leather_armor |
| `MAGE`     | 80      | 20       | 2        | [fireball]             | MAIN_HAND: wooden_staff        |
| `ROGUE`    | 100     | 12       | 5        | [swift_reflexes]       | MAIN_HAND: iron_dagger         |

**WORKER, MERCHANT, BEAST, UNDEAD are NOT present in CLASS_REGISTRY.**
The ticket scope instruction "add only what's in CLASS_REGISTRY" means:
- CITIZEN→[WORKER, MERCHANT] spawn table entry must NOT be added (classes absent).
- MONSTER→[BEAST, UNDEAD] spawn table entry must NOT be added (classes absent).
- Only HERO→[WARRIOR, MAGE, ROGUE] is valid; this entry already exists in `spawn_tables.yaml`.

Classes valid for HERO role: `{WARRIOR, MAGE, ROGUE}`.

---

## spawn_tables.yaml — default_class_table (current)

File: `data/content/spawn_tables.yaml:L9–L18`

```yaml
- id: "default_class_table"
  display_name: "Default Class Assignments by Role"
  schema_version: "classtable.v1"
  class_id_by_role:
    hero: ["WARRIOR", "MAGE", "ROGUE"]
    monster: ["NOVICE"]
    citizen: ["NOVICE"]
    worker: ["NOVICE"]
    guard: ["WARRIOR"]
    shopkeeper: ["NOVICE"]
```

The `hero` entry is already correct. The compiler reads this via `_load_class_table()`
(`compiler.py:L93–L103`) and picks with `rng.choice(Domain.WORLD, 0, entity_id, class_pool, sub_id=14)`.

**Implication for scope**: No spawn_tables.yaml changes are needed for HERO authoring.
The CITIZEN→[WORKER, MERCHANT] and MONSTER→[BEAST, UNDEAD] additions are blocked because
WORKER, MERCHANT, BEAST, UNDEAD are not in CLASS_REGISTRY. Document this as a known gap.

---

## Mechanics / Engine Constraints

- **Determinism**: class_id is drawn with `rng.choice(Domain.WORLD, 0, entity_id, pool, sub_id=14)`. Adding new HERO entities changes entity IDs and sub-seed draws for subsequent entities. This will invalidate the existing `state_hash` in `sandbox_world/world_compile_report.json`. The compile report is a cached artifact, not authoritative state — it can be regenerated. This is expected drift, not a defect.
- **Population group ID uniqueness**: `WorldSpec` model validator enforces unique `id` per population entry (`schema.py:L172–L177`). New entries must use fresh IDs not present in the spec.
- **Faction reference**: `spawn_region` and `faction` values used in new HERO entries must reference IDs already declared in the same world spec's `regions[]` and `factions[]` sections. The WorldSpec validator does NOT cross-check faction/region references (no FK check), but the compiler silently skips entities whose `spawn_region` is not found in `regions` dict (`compiler.py:L255–L256`). Authoring a non-existent spawn_region causes silent entity loss.
- **`get_role_enum()` mapping** (`compiler.py:L39`): `"HERO" in r.upper()` — string `"hero"` correctly maps to `EntityRole.HERO`. No issue.
- **Mechanics Bible (01_entity_anatomy.md §3)**: WARRIOR/MAGE/ROGUE are the four listed tier-1 hero classes. No HERO class outside this set is canon. Assigning only these three is compliant.

---

## Parity Ledger Overlap

### PROG-108 (`docs/parity_ledger/progression.yaml:L1096–L1109`)
- Status: `verified`
- Text: Entity class_id is assigned by role from spawn_tables.yaml; HERO → {WARRIOR, MAGE, ROGUE}.
- Test path: `tests/unit/entity/test_entity_initialization.py::test_class_id_non_novice_for_hero_role`
- Impact: This entry verifies the mechanism. Adding HERO entities to world files exercises the same mechanism. **No status change required** — the mechanism proof is already `verified`. However, after implementation `v2_evidence` may be extended to reference the new world files and `test_hero_archetypes_cover_combat_mage_rogue`.

### SUB-370 (`docs/parity_ledger/substrate.yaml:L4072–L4083`)
- Status: `verified`
- Text: PersonalityComponent traits seeded per entity via DeterministicRNG.
- Impact: No change needed — personality seeding is independent of which roles exist.

### No new parity entries required for this ticket.
The new test (`test_hero_archetypes_cover_combat_mage_rogue`) tests world-authoring content, not a new engine mechanic. PROG-108 already covers the class assignment mechanic. The test path on PROG-108 may optionally be updated to reference the new test as additional evidence, but this is not required.

---

## Prior Work (TCK-20260619-P0-ENTITY-INIT)

Ticket: `tickets/done/TCK-20260619-P0-ENTITY-INIT.md` — status DONE.

What was delivered:
- `_load_class_table()` added to `src/worldbuilding/compiler.py` — reads `classtable.v1` from `spawn_tables.yaml`.
- `data/content/spawn_tables.yaml` — created with `default_class_table` (hero→[WARRIOR,MAGE,ROGUE], guard→[WARRIOR], others→[NOVICE]).
- `PersonalityComponent` seeded with `rng.get_float(Domain.WORLD, 0, entity_id, sub_id=10..13)`.
- `class_id` drawn with `rng.choice(Domain.WORLD, 0, entity_id, class_pool, sub_id=14)`.
- 4 tests in `tests/unit/entity/test_entity_initialization.py` all pass.
- Parity entries SUB-370 and PROG-108 added at `verified`.

**Remaining gap**: No world file actually contains HERO-role entities yet. This ticket (E11A) closes that gap.

---

## Risks and Open Questions

### Risk 1 — sandbox_world is worldtemplate.v1 (not worldspec.v1)
The recipe expander auto-generates population IDs as `pop_{role}_{faction}_{region}`.
The expander is in `recipe.py:L181`. Confirm the recipe pipeline is invoked before
`WorldCompiler.compile()` when running the test — or bypass recipe expansion by either:
  (a) adding entries to the recipe template (correct path, recipe expansion covers it), or
  (b) creating a companion `world.spec.yaml` (worldspec.v1) that the test uses directly.
**Decision needed**: Should the test compile `sandbox_world` via the recipe pipeline, or use
a fresh inline worldspec (like `_MULTI_ROLE_SPEC` in `test_entity_initialization.py`)? 
Using an inline spec is simpler and avoids dependency on the recipe pipeline in a unit test.

### Risk 2 — urban_political resolved spec vs. module source
`urban_political/resolved/world.resolved.yaml` is the assembled worldspec.v1. Adding entries
here directly bypasses the module assembly pipeline. This is acceptable for a content-authoring
ticket with no new modules, but the change to the resolved spec must survive a re-assembly
(i.e. the assembly should not overwrite the added entries). Confirm whether re-running world
assembly regenerates `world.resolved.yaml` from modules — if so, HERO entries must be injected
into a module instead.

### Risk 3 — faction reference in sandbox_world
sandbox_world has two factions: `villagers` and `monsters`. HERO entities spawning under
`villagers` faction is semantically odd but mechanically valid. Alternatively, add a
`hero_guild` faction entry in the template. Authoring decision needed.

### Risk 4 — spawn_region coverage for class distribution
With count=3 HERO entities in sandbox_world (all in one pool), the RNG may not hit all three
classes. With seed=42, WARRIOR/MAGE/ROGUE are all reachable from 3 draws of a 3-item pool
by probability, but not guaranteed. The acceptance criterion requires "≥1 entity with each
of WARRIOR, MAGE, ROGUE across 6 HERO entities total." With 3 per world, a single world
might miss one class. The test spans both worlds (6 total) — confirm this is the intent, or
require ≥3 per world.

### Open Question — test target spec
The AC specifies `test_hero_archetypes_cover_combat_mage_rogue` compiles `sandbox_world`.
If sandbox_world's recipe pipeline isn't exercised in unit tests, the test should use an
inline worldspec.v1 with 6 HERO entities (sufficient to probabilistically cover all 3 classes
at seed=42). Confirm before implementation.

---

## Anti-Drift Hazards

1. **sandbox_world compile report hash** — `data/worlds/sandbox_world/world_compile_report.json`
   state_hash `2f94f10135bc2aff1a68fc2c54b2c415` will change after HERO entities are added.
   The report must be regenerated. No test asserts this hash, so no test will break.

2. **entity_count in compile report** — currently 20; will increase by the count of added HERO
   entities. The report JSON is not consumed by any test (only by the CLI and observability layer).

3. **CLASS_REGISTRY gate** — if WORKER, MERCHANT, BEAST, or UNDEAD are added to CLASS_REGISTRY
   in a future ticket, spawn_tables.yaml must be updated simultaneously. PROG-108 text currently
   limits to {WARRIOR, MAGE, ROGUE}; a future ticket would need to update PROG-108 as well.

4. **WorldSpec `extra="forbid"` is NOT set** (model_config uses `frozen=True` only, not strict).
   Extra YAML keys in population entries won't cause validation errors but will be silently
   dropped — don't add extra fields like `archetype_class` or `class_hint`.

5. **urban_political re-assembly** — if `world.resolved.yaml` is regenerated from modules,
   manually added HERO entries will be lost. Guard against this by adding a comment header
   in the resolved YAML or tracking the change in the composition module.
