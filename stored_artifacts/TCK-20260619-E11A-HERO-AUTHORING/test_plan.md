---
ticket_id: TCK-20260619-E11A-HERO-AUTHORING
phase: test_plan
date: 2026-06-19
---

# Test Plan: TCK-20260619-E11A-HERO-AUTHORING

## Regression Surface (existing tests that must continue to pass)

### Entity initialization tests
File: `tests/unit/entity/test_entity_initialization.py`

| Test | What it guards |
|------|---------------|
| `test_entity_personality_variance_at_spawn` | PersonalityComponent trait variance; adding HERO entries changes entity IDs and RNG draws for subsequent entities — this test must still pass with the expanded spec |
| `test_class_id_non_novice_for_hero_role` | HERO→{WARRIOR,MAGE,ROGUE} mechanism; uses inline `_MULTI_ROLE_SPEC` (6 heroes, seed=42) — not affected by world file changes |
| `test_personality_seeding_is_deterministic` | Determinism across two compiles; independent of world file content |
| `test_different_seeds_produce_different_personalities` | Seed isolation; independent of world file content |

Run command:
```
pytest tests/unit/entity/test_entity_initialization.py -v
```

### Compiler/schema tests
Verify WorldSpec validation doesn't break on new entries:
```
pytest tests/unit/ -k "compiler or schema or worldspec or worldbuilding" -v
```

### Determinism integration test
File: `tests/integration/kernel/test_phase2_determinism.py`
HERO entity additions change the compiled state hash. This test must pass — confirm it doesn't
assert a hardcoded state_hash from the sandbox_world compile report.
```
pytest tests/integration/kernel/test_phase2_determinism.py -v
```

### Performance stress tests (smoke check)
File: `tests/perf/test_perf_stress.py`
The stress test (`test_perf_mixed_stress`) builds 200 entities with mixed roles including
Heroes. It uses `build_mixed_state()` from `src/perf/scenarios.py`, not the world files
directly. Not affected by world file changes, but run as a smoke check.
```
pytest tests/perf/test_perf_stress.py -v -m "not slow"
```

---

## New Tests Required

### Primary AC test

**File:** `tests/unit/entity/test_entity_archetypes.py` (NEW)
**Test:** `test_hero_archetypes_cover_combat_mage_rogue`

**Purpose:** Compile a world containing ≥6 HERO entities; assert the compiled roster contains
at least one entity with each of WARRIOR, MAGE, ROGUE class_id.

**Design decision (from investigation §Open Questions):**
Use an inline `worldspec.v1` dict (same pattern as `_MULTI_ROLE_SPEC` in
`test_entity_initialization.py`) rather than loading `sandbox_world/world.yaml` through the
recipe pipeline. This keeps the test a proper unit test with no filesystem dependency and
avoids the recipe expansion complexity. 6 HERO entities at seed=42 is sufficient to cover all
3 class_id values given the 3-item pool.

**Sketch:**
```python
# tests/unit/entity/test_entity_archetypes.py

import pytest
from src.worldbuilding.schema import WorldSpec
from src.worldbuilding.compiler import WorldCompiler

_HERO_SPEC = {
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
        # 6 HERO entities — enough to cover WARRIOR/MAGE/ROGUE distribution
        {"id": "heroes", "count": 6, "role": "hero", "faction": "hero_guild", "spawn_region": "town"},
    ],
    "resources": [],
    "buildings": [],
    "quest_definitions": [],
}


def test_hero_archetypes_cover_combat_mage_rogue():
    """
    After compilation, the entity roster must include at least one entity
    with each of WARRIOR, MAGE, and ROGUE class_id across all HERO-role entities.

    AC: tests/unit/entity/test_entity_archetypes.py::test_hero_archetypes_cover_combat_mage_rogue
    Ref: TCK-20260619-E11A-HERO-AUTHORING, PROG-108
    """
    spec = WorldSpec.model_validate(_HERO_SPEC)
    state, _ = WorldCompiler.compile(spec, seed=42)

    from src.core.enums import EntityRole
    hero_classes = {
        ent.identity.class_id
        for ent in state.entities.values()
        if ent.identity.role == EntityRole.HERO.value
    }

    assert "WARRIOR" in hero_classes, f"No WARRIOR hero found; got {hero_classes}"
    assert "MAGE" in hero_classes, f"No MAGE hero found; got {hero_classes}"
    assert "ROGUE" in hero_classes, f"No ROGUE hero found; got {hero_classes}"
    assert hero_classes <= {"WARRIOR", "MAGE", "ROGUE"}, (
        f"Hero entities received unexpected class_ids outside allowed set: {hero_classes}"
    )
```

**Note on seed=42 coverage guarantee:** With 6 entities drawing uniformly from a 3-item pool
using DeterministicRNG, all three values are expected to appear. If seed=42 fails to cover
all three, increase to count=9 or add a deterministic assertion comment. Verify empirically
during implementation.

---

### Secondary tests (optional but recommended)

**Test:** `test_hero_entities_exist_in_compiled_world`
Verify that after adding HERO entries to `sandbox_world/world.yaml` (recipe pipeline), at least
one entity with `role == EntityRole.HERO` exists in the compiled state. This guards against
silent entity-loss from a wrong `spawn_region` reference.

**Sketch:**
```python
def test_hero_entities_exist_in_compiled_world():
    """
    sandbox_world world.yaml (recipe template) must produce ≥1 HERO entity after compilation.
    Guards against silent entity loss from bad spawn_region reference in recipe template.
    Ref: TCK-20260619-E11A-HERO-AUTHORING
    """
    # If using recipe pipeline:
    from src.worldbuilding.recipe import WorldTemplateSpec, expand_template
    # ... or use inline worldspec.v1 that mirrors the authored content
    ...
```

This test is optional — `test_hero_archetypes_cover_combat_mage_rogue` already implicitly
verifies hero presence. Include if the implementation authors HERO entries in the world files
and wants a filesystem-backed smoke test.

---

## Scoped Pytest Commands

### Run only the new test (during development):
```bash
pytest tests/unit/entity/test_entity_archetypes.py -v
```

### Run the full entity unit suite (regression + new):
```bash
pytest tests/unit/entity/ -v
```

### Run scoped to entity + worldbuilding (full AC gate):
```bash
pytest tests/unit/entity/ tests/unit/worldbuilding/ -v
```

### Run without slow tests (pre-commit gate):
```bash
pytest tests/unit/ -m "not slow" -v
```

### Full integration regression (before PR):
```bash
pytest tests/integration/kernel/test_phase2_determinism.py tests/unit/entity/ -v
```

---

## Anti-Drift Test Guards

### 1. HERO class set must not silently expand
`test_hero_archetypes_cover_combat_mage_rogue` asserts `hero_classes <= {"WARRIOR", "MAGE", "ROGUE"}`.
If a future ticket adds RANGER or another class to the HERO pool in spawn_tables.yaml, this
test will fail loudly, forcing a conscious decision about the valid HERO class set.

### 2. Determinism guard
`test_personality_seeding_is_deterministic` in `test_entity_initialization.py` uses seed=42
with 6 heroes. After HERO entries are added to world files, that test remains independent
(it uses `_MULTI_ROLE_SPEC` inline). However, if the world file tests are ever made to depend
on sandbox_world compilation, add a determinism check:
```python
state_a = WorldCompiler.compile(spec, seed=42)
state_b = WorldCompiler.compile(spec, seed=42)
assert {e.identity.class_id for e in state_a.entities.values()} == \
       {e.identity.class_id for e in state_b.entities.values()}
```

### 3. CLASS_REGISTRY gate
If WORKER, MERCHANT, BEAST, UNDEAD are added to CLASS_REGISTRY in a future ticket, add:
```python
def test_spawn_table_hero_pool_is_subset_of_class_registry():
    from src.core.classes import CLASS_REGISTRY
    from src.worldbuilding.compiler import _load_class_table
    table = _load_class_table()
    for role, pool in table.items():
        for class_id in pool:
            assert class_id in CLASS_REGISTRY, (
                f"spawn_tables.yaml role '{role}' references class_id '{class_id}' "
                f"not in CLASS_REGISTRY — add the class definition or remove from spawn table"
            )
```
This test is a standing drift guard: it catches spawn table entries that reference non-existent
classes, which would cause silent NOVICE fallback at runtime.

### 4. World file population ID uniqueness
If population entries are added to urban_political's resolved spec, ensure their `id` values
do not collide with existing entries. The WorldSpec model validator (`schema.py:L172–L177`)
enforces uniqueness at parse time — a test that loads the world file through
`load_world_spec_from_yaml()` will catch duplicate IDs immediately.
