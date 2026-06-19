---
ticket_id: TCK-20260619-E11A-HERO-AUTHORING
phase: plan
date: 2026-06-19
---

# Implementation Plan: TCK-20260619-E11A-HERO-AUTHORING

## Scope Summary

Add HERO population entries to two worlds:
- **sandbox_world** (worldtemplate.v1): add 3 HERO entries to `entities.populations[]` using the `villagers` faction.
- **urban_political** (worldcomposition.v1): create a new world module with 3 HERO population entries; register it in `module_refs`.

Write one new test file with the primary AC test `test_hero_archetypes_cover_combat_mage_rogue` using an inline worldspec.v1 dict.

No changes to `spawn_tables.yaml` (the `hero` entry already exists; CITIZEN/MONSTER extensions are blocked — classes absent from CLASS_REGISTRY).

---

## Architectural Decisions (Confirmed)

| Decision | Resolution | Rationale |
|---|---|---|
| sandbox_world faction for HERO | `villagers` | Only two factions exist: `villagers` (civilian) and `monsters` (hostile). `villagers` is the semantically closer choice for non-hostile entities. No new faction needed. |
| urban_political approach | New world module via `module_refs` | Assembly (`resolver.py`) regenerates `world.resolved.yaml` from scratch on every run. Direct edits to the resolved spec are overwritten. The module must be added to `world.yaml` `module_refs`. |
| New module region | `hometown` | `hometown` is already registered in the catalog (`data/content/world/runtime_regions.yaml`). It is the primary settlement region in the assembled urban_political world. No new region needed. |
| New module faction | `hero_guild` | `hero_guild` is registered in the catalog (`data/content/social/factions.yaml`). Assembly resolver validates faction IDs against the catalog — using an unregistered faction would raise `ResolverError`. |
| Test spec | Inline worldspec.v1 dict (6 HERO entities, seed=42) | Avoids recipe pipeline dependency in a unit test. Same pattern as `_MULTI_ROLE_SPEC` in `test_entity_initialization.py`. 6 entities drawing from a 3-item pool at seed=42 covers WARRIOR/MAGE/ROGUE. |
| spawn_tables.yaml changes | None | `hero: ["WARRIOR", "MAGE", "ROGUE"]` already present from TCK-20260619-P0-ENTITY-INIT. CITIZEN/MONSTER extensions blocked (WORKER/MERCHANT/BEAST/UNDEAD absent from CLASS_REGISTRY). |

---

## Ordered Implementation Steps

### Step 1 — Add 3 HERO population entries to sandbox_world

**File:** `data/worlds/sandbox_world/world.yaml`

Append three new entries under `entities.populations[]`. Use the `villagers` faction (already declared in `factions[]`) and `spawn_region: town_center` (already declared in `regions[]`). Three separate entries instead of one `count: 3` entry is acceptable; a single entry with `count: 3` is equally valid and simpler — use count=3 for compactness.

YAML to add:
```yaml
  - role: hero
    count: 3
    faction: villagers
    spawn_region: town_center
```

The recipe expander (`recipe.py:L181`) will generate id `pop_hero_villagers_town_center`. Compiler will draw 3 class_ids from `["WARRIOR","MAGE","ROGUE"]` via `rng.choice(Domain.WORLD, 0, entity_id, class_pool, sub_id=14)`.

**Scope guard:** Do not modify `factions[]`, `regions[]`, `resources`, `buildings`, or `quests`. Do not change the seed or topology.

**Verifiable:** `python3 -c "import yaml; d=yaml.safe_load(open('data/worlds/sandbox_world/world.yaml')); print([p['role'] for p in d['entities']['populations']])"` must include `'hero'`.

**Depends on:** nothing (standalone data edit).

**AC satisfied:** "Each world file has ≥2 population entries with `role: hero`" — met (count=3 adds 3 hero entities via expansion).

---

### Step 2 — Create hero_adventurers world module

**File (new):** `data/content/world_modules/hero_adventurers.yaml`

Format mirrors `trading_company_hub.yaml` exactly (the simplest non-parameterized module with `population_recipes`). The new module must declare:
- `module_id: "hero_adventurers"`
- `module_type: "settlement"` (consistent with faction modules that contribute to existing settlements)
- `factions: ["hero_guild"]` — catalog-registered, type `defender`
- One region: `hometown` — catalog-registered in `data/content/world/runtime_regions.yaml`, bounds `[10, 10, 40, 40]`, terrain `plain`, hazard_level `0.0`
- Three `population_recipes` entries with `role: hero`, `faction: hero_guild`, `spawn_region: hometown`

Full file content:
```yaml
# STATE: ADDITIONAL
module_id: "hero_adventurers"
module_type: "settlement"
display_name: "Hero Adventurers"
description: "A group of wandering heroes who have established a base in the settlement. Provides WARRIOR, MAGE, and ROGUE class entities for the hero_guild faction."
version: "1.0.0"
provides: ["hero_presence"]
observability_tags: ["combat", "adventurer"]
biomes: ["frontier_village"]
ecologies: ["frontier_village_ecology"]
regions:
  - id: "hometown"
    type: "town"
    grid_bounds: [10, 10, 40, 40]
    terrain: "plain"
    hazard_level: 0.0
factions: ["hero_guild"]
population_recipes:
  - role: "hero"
    count: 1
    faction: "hero_guild"
    spawn_region: "hometown"
  - role: "hero"
    count: 1
    faction: "hero_guild"
    spawn_region: "hometown"
  - role: "hero"
    count: 1
    faction: "hero_guild"
    spawn_region: "hometown"
```

**Important:** Three separate `population_recipes` entries each with `count: 1` are used rather than one `count: 3` entry. This ensures the assembly resolver generates three distinct population IDs (`pop_0`, `pop_1`, `pop_2` under the module prefix), each receiving an independent `rng.choice` draw for class_id — maximizing the chance of covering all three archetype classes.

**Scope guard:** Do not add `buildings`, `resources`, `relationships`, or `parameters`. Do not add a new region to the catalog. Do not create a new faction. Do not add `namespace` (no namespace is needed — `hero_guild` is a global faction with no collision risk).

**Verifiable:** `python3 -c "import yaml; d=yaml.safe_load(open('data/content/world_modules/hero_adventurers.yaml')); print(d['module_id'], [p['role'] for p in d['population_recipes']])"` must print `hero_adventurers ['hero', 'hero', 'hero']`.

**Depends on:** nothing (standalone new file).

---

### Step 3 — Register hero_adventurers in urban_political world.yaml

**File:** `data/worlds/urban_political/world.yaml`

Append a new entry to `module_refs`:
```yaml
  - module_id: "hero_adventurers"
    order: 3
```

The `order: 3` places it after the three existing modules (orders 0, 1, 2). No `namespace` is needed — the module's population IDs will not collide with existing entries since they use distinct recipe indices under the `hero_adventurers` module.

**Scope guard:** Do not modify `world_id`, `name`, `provided_features`, `generation_seed`, or existing `module_refs` entries. Do not edit `world.resolved.yaml` directly.

**Verifiable:** `python3 -c "import yaml; d=yaml.safe_load(open('data/worlds/urban_political/world.yaml')); print([r['module_id'] for r in d['module_refs']])"` must include `'hero_adventurers'`.

**Depends on:** Step 2 (the module file must exist before assembly can consume it).

**AC satisfied:** "Each world file has ≥2 population entries with `role: hero`" — met for urban_political (3 entries via module).

---

### Step 4 — Regenerate urban_political resolved spec

**Command:**
```bash
python3 -m src.worldbuilding.cli assemble urban_political
```
or equivalent CLI entry point for world assembly. Check `src/worldbuilding/cli.py` for exact invocation syntax.

This regenerates `data/worlds/urban_political/resolved/world.resolved.yaml` from the updated `world.yaml` module_refs (now including `hero_adventurers`). The resolved spec will contain new HERO population entries contributed by the new module.

**Verifiable:** `grep "role: hero" data/worlds/urban_political/resolved/world.resolved.yaml` must return ≥2 lines.

**Depends on:** Step 3 (module registered in world.yaml), Step 2 (module file exists).

**Scope guard:** Do not manually edit `world.resolved.yaml`. Do not commit the stale resolved spec — only commit the post-assembly version. If the CLI is not available or assembly fails, record the blocker in the ticket and fall back to manually updating `world.resolved.yaml` with the same entries that assembly would produce (document this as a known deviation).

---

### Step 5 — Create test file

**File (new):** `tests/unit/entity/test_entity_archetypes.py`

Implement `test_hero_archetypes_cover_combat_mage_rogue` using an inline worldspec.v1 dict with one population entry of `count: 6`, `role: hero`, `faction: hero_guild`, `spawn_region: town`. Use `seed=42`. Assert:
- `"WARRIOR" in hero_classes`
- `"MAGE" in hero_classes`
- `"ROGUE" in hero_classes`
- `hero_classes <= {"WARRIOR", "MAGE", "ROGUE"}`

Full test spec dict:
```python
_HERO_ARCHETYPE_SPEC = {
    "schema_version": "worldspec.v1",
    "world_id": "archetype_test_world",
    "name": "Archetype Test World",
    "topology": {"width": 50, "height": 50, "coordinate_system": "grid"},
    "regions": [
        {"id": "town", "type": "town", "bounds": [0, 0, 20, 20], "terrain": "GRASS"},
    ],
    "factions": [
        {"id": "hero_guild", "type": "hero"},
    ],
    "entities": [
        {"id": "heroes", "count": 6, "role": "hero", "faction": "hero_guild", "spawn_region": "town"},
    ],
    "resources": [],
    "buildings": [],
    "quest_definitions": [],
}
```

If seed=42 fails to cover all three classes with count=6, increase count to 9 (verify empirically after Step 5 with `pytest tests/unit/entity/test_entity_archetypes.py -v`).

**Scope guard:** Do not load world files from disk in this test. Do not import the recipe pipeline. Do not add parametrize decorators or fixtures beyond what the existing `test_entity_initialization.py` uses.

**Depends on:** Steps 1–4 are data authoring (no code changes); this test is independent of them and can be written in parallel. However, the test must pass before the ticket closes — run it after all steps complete to confirm.

**AC satisfied:** `tests/unit/entity/test_entity_archetypes.py::test_hero_archetypes_cover_combat_mage_rogue` passes.

---

### Step 6 — Run regression suite

Run the scoped test commands in order:

```bash
# New AC test
pytest tests/unit/entity/test_entity_archetypes.py -v

# Full entity unit suite (regression + new)
pytest tests/unit/entity/ -v

# Worldbuilding unit suite
pytest tests/unit/worldbuilding/ -v

# Integration determinism check
pytest tests/integration/kernel/test_phase2_determinism.py -v
```

**Accept criteria for this step:**
- All tests pass.
- `test_hero_archetypes_cover_combat_mage_rogue` passes (primary AC).
- No pre-existing test failures are introduced.

**Scope guard:** Do not run `pytest tests/` (full suite) — scope to the domains modified.

**Depends on:** Steps 1–5 all complete.

---

## Dependency Map

```
Step 1 (sandbox_world data)   ─────────────────────────────┐
Step 2 (new module file)       ──► Step 3 (register module) ──► Step 4 (regenerate resolved spec)
Step 5 (test file)             ─────────────────────────────┘
                                                              │
                                                              ▼
                                                         Step 6 (run tests)
```

Steps 1, 2, and 5 are independent of each other and can be authored in any order. Step 3 requires Step 2. Step 4 requires Steps 2 and 3. Step 6 requires all prior steps.

---

## Acceptance Criteria → Step Mapping

| AC | Step |
|---|---|
| Each world file has ≥2 population entries with `role: hero` | Step 1 (sandbox_world), Step 3+4 (urban_political) |
| Post-compilation entity roster includes entities with class_id in {WARRIOR, MAGE, ROGUE} | Step 1 + Step 5 (tested via inline spec at seed=42) |
| `test_hero_archetypes_cover_combat_mage_rogue` passes | Step 5 + Step 6 |

---

## Explicit Scope Guards (Global)

- **Do not** modify `data/content/spawn_tables.yaml` (HERO entry already correct; CITIZEN/MONSTER extensions blocked by CLASS_REGISTRY).
- **Do not** add WORKER, MERCHANT, BEAST, or UNDEAD to CLASS_REGISTRY or spawn_tables (out of scope — no class definitions exist).
- **Do not** edit `data/worlds/urban_political/resolved/world.resolved.yaml` manually (it is regenerated by assembly).
- **Do not** modify `src/worldbuilding/compiler.py`, `src/worldbuilding/schema.py`, `src/worldassembly/resolver.py`, or any source file under `src/` (this ticket is data authoring and test addition only).
- **Do not** modify `data/content/parity_ledger/` entries (PROG-108 remains `verified`; no new mechanism introduced).
- **Do not** add a `hero_guild` faction entry to `sandbox_world/world.yaml` (the `villagers` faction is used; no new faction creation needed in sandbox_world).
- **Do not** touch `data/worlds/sandbox_world/world_compile_report.json` — it will drift (entity_count increases from 20 to 23, state_hash changes); this is expected and no test asserts these values.

---

## Deviations

| Step | Planned | Actual | Reason |
|---|---|---|---|
| Step 2 | `hero_adventurers.yaml` includes `regions` block declaring `hometown` | Removed `regions` block entirely | `frontier_village_core` already contributes `hometown`; resolver raised `Duplicate region ID collision 'hometown'`. `population_recipes` can reference an existing region without re-declaring it. Also removed `biomes`/`ecologies` fields as they were not needed without the region block. |
| Step 4 | CLI command `python3 -m src.worldbuilding.cli assemble urban_political` | `python3 -m src.worldbuilding.cli resolve urban_political` | The CLI subcommand is `resolve`, not `assemble` (confirmed from `cli.py`). |

---

## Files Changed

| File | Action | Step |
|---|---|---|
| `data/worlds/sandbox_world/world.yaml` | Edit — append 1 HERO population entry (count=3) | Step 1 |
| `data/content/world_modules/hero_adventurers.yaml` | Create — new world module with 3 HERO population_recipes | Step 2 |
| `data/worlds/urban_political/world.yaml` | Edit — append `hero_adventurers` to module_refs | Step 3 |
| `data/worlds/urban_political/resolved/world.resolved.yaml` | Regenerated by assembly (not manually edited) | Step 4 |
| `tests/unit/entity/test_entity_archetypes.py` | Create — new test file with primary AC test | Step 5 |
