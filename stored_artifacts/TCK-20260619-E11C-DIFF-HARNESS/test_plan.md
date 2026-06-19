---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260619-E11C-DIFF-HARNESS
artifact_type: test_plan
tags: [entity-differentiation, test-harness, behavioral-quality, integration]
---

# Test Plan — TCK-20260619-E11C-DIFF-HARNESS
# E11-C · Build 400-tick differentiation test harness

---

## File to Create

`tests/integration/scenarios/test_entity_differentiation.py`

---

## Pytest Marks

- `@pytest.mark.integration` — runs in `pytest tests/integration/scenarios/`
- `@pytest.mark.slow` — 400-tick run; exclude from fast unit suites
- `@pytest.mark.xfail(strict=False)` — on `test_bravery_quartile_combat_rate_2x` only,
  until TCK-20260619-E11D-SCORING-CAL is complete

---

## Test 1: `test_no_identical_personality_vectors_at_spawn`

### Purpose
Assert that all entities in the compiled world have distinct `PersonalityComponent` tuples
at tick 0. This is a strictly-passing precondition gate for E11D calibration work.

### Prerequisite
TCK-20260619-E11A-HERO-AUTHORING must be complete (ensures HERO entities have distinct
bravery values seeded at world compile time).

### Setup

```python
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.schema import WorldSpec

def _build_differentiation_spec() -> WorldSpec:
    """Minimal world with 8 heroes spanning full bravery range for quartile testing."""
    raw = {
        "schema_version": "worldspec.v1",
        "world_id": "differentiation_test_world",
        "name": "Differentiation Test World",
        "topology": {"width": 64, "height": 64, "coordinate_system": "grid"},
        "regions": [
            {"id": "arena",   "type": "wilderness", "bounds": [0, 0, 32, 32], "terrain": "GRASS"},
            {"id": "village", "type": "town",        "bounds": [32, 0, 64, 32], "terrain": "GRASS"}
        ],
        "factions": [
            {"id": "heroes",   "type": "civilian"},
            {"id": "monsters", "type": "hostile"}
        ],
        "entities": [
            {"id": "hero_group",    "count": 8,  "role": "hero",    "faction": "heroes",   "spawn_region": "arena"},
            {"id": "monster_group", "count": 4,  "role": "monster", "faction": "monsters", "spawn_region": "arena"}
        ],
        "resources": [],
        "buildings": [],
        "quests": []
    }
    return WorldSpec.model_validate(raw)
```

**Note**: If `WorldSpec` does not support explicit per-entity bravery injection (E11A decides
this), the harness falls back to asserting uniqueness from the seeded distribution. If E11A
provides explicit bravery assignment, use that mechanism instead.

### Assertion

```python
def test_no_identical_personality_vectors_at_spawn():
    spec = _build_differentiation_spec()
    state, report = WorldCompiler.compile(spec, seed=42)

    personality_tuples = set()
    for entity in state.entities.values():
        p = entity.identity.personality
        tup = (p.greed, p.bravery, p.sociability, p.industry)
        assert tup not in personality_tuples, (
            f"Entity {entity.id} has duplicate personality vector {tup}"
        )
        personality_tuples.add(tup)
```

### Pass Criteria
- All entities have distinct `(greed, bravery, sociability, industry)` tuples
- No `WorldCompiler.compile` warnings that indicate entity spawn failure

---

## Test 2: `test_bravery_quartile_combat_rate_2x`

### Purpose
Assert that top-bravery-quartile HERO entities take `combat_engage` routes at ≥2× the rate
of bottom-bravery-quartile HERO entities, measured over 400 ticks.

### Mark
```python
@pytest.mark.xfail(strict=False, reason="Calibration pending TCK-20260619-E11D-SCORING-CAL")
@pytest.mark.slow
@pytest.mark.integration
```

### Setup

```python
from collections import defaultdict
from dataclasses import replace

from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.schema import WorldSpec
from src.core.strategic import GoalKind

TICKS = 400
SEED  = 42

def _test_profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="differentiation-test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=500,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=200.0
    )
```

### Execution

```python
def test_bravery_quartile_combat_rate_2x():
    # 1. Compile world
    spec = _build_differentiation_spec()
    initial_state, report = WorldCompiler.compile(spec, seed=SEED)

    # 2. Enable COMBAT_ENGAGEMENT feature flag
    initial_state = replace(
        initial_state,
        feature_flags={"ENABLE_COMBAT_ENGAGEMENT": "ON", "ENABLE_ADVENTURE_ROUTING": "ON"}
    )

    # 3. Run 400 ticks, sampling current project kind per entity per tick
    project_kind_history: dict[int, list[str | None]] = defaultdict(list)

    rng = DeterministicRNG(SEED)
    kernel = Kernel(
        _test_profile(),
        initial_state,
        rng,
        flags={"no_replay": True}
    )
    for _ in range(TICKS):
        kernel.tick_once()
        s = kernel.state
        for eid, ent in s.entities.items():
            cur_proj_id = ent.strategic.current_project_id
            if cur_proj_id and cur_proj_id in ent.strategic.projects:
                kind_val = ent.strategic.projects[cur_proj_id].kind
                project_kind_history[eid].append(
                    kind_val.value if hasattr(kind_val, "value") else str(kind_val)
                )
            else:
                project_kind_history[eid].append(None)

    final_state = kernel.state

    # 4. Sort entities by bravery; compute quartile splits on HERO entities only
    hero_entities = [
        e for e in final_state.entities.values()
        if e.kind.lower() == "hero" and e.combat.alive
    ]
    assert len(hero_entities) >= 4, (
        f"Need at least 4 hero entities for quartile split, got {len(hero_entities)}"
    )

    hero_entities.sort(key=lambda e: e.identity.personality.bravery)
    n = len(hero_entities)
    q_size = max(1, n // 4)

    bottom_quartile = hero_entities[:q_size]
    top_quartile    = hero_entities[n - q_size:]

    # 5. Compute combat_engage rate per quartile
    def combat_engage_rate(entity_list):
        total_ticks = 0
        combat_ticks = 0
        for ent in entity_list:
            history = project_kind_history[ent.id]
            total_ticks += len(history)
            combat_ticks += sum(1 for k in history if k == GoalKind.COMBAT_ENGAGE.value)
        return combat_ticks / max(1, total_ticks)

    top_rate    = combat_engage_rate(top_quartile)
    bottom_rate = combat_engage_rate(bottom_quartile)

    # 6. Assert 2× differential
    # If both are zero (no combat happened), the assertion trivially fails — this is expected
    # pre-E11D and is why this test is marked xfail.
    assert bottom_rate > 0, (
        "Bottom-quartile entities never took combat_engage route — "
        "check ENABLE_COMBAT_ENGAGEMENT flag and entity proximity"
    )
    assert top_rate >= 2.0 * bottom_rate, (
        f"Top-quartile combat_engage rate ({top_rate:.3f}) is less than "
        f"2× bottom-quartile rate ({bottom_rate:.3f}). "
        f"Calibration required (E11D)."
    )
```

### Pass Criteria (post-E11D)
- `top_rate >= 2.0 * bottom_rate`
- `bottom_rate > 0` (some combat engagement occurred in bottom quartile)
- `top_rate > 0` (combat engagement occurred in top quartile)

### Failure Analysis Guide
| Failure Mode | Likely Cause | Resolution |
|---|---|---|
| `AssertionError: Need at least 4 hero entities` | E11A not complete or WorldSpec entity spawn failed | Complete E11A; check WorldSpec compile report |
| `bottom_rate == 0.0` | `ENABLE_COMBAT_ENGAGEMENT` flag not active, or entities never in range | Confirm feature_flags set; reduce world size |
| `top_rate < 2× bottom_rate` | Bravery coefficient too small relative to competing scorers | E11D scoring calibration |
| `AssertionError: duplicate personality vector` | E11A seeding not producing distinct vectors | Fix E11A personality seeder |

---

## Test 3 (implicit precondition check): entity kind filter

Within `test_bravery_quartile_combat_rate_2x`, filter to `ent.kind.lower() == "hero"` before
quartile computation. This isolates the signal from monster behavior (monsters have
`faction="monsters"` and may also engage in combat).

---

## Test Coverage Matrix

| Category | Covered |
|---|---|
| Normal flow — bravery drives combat rate differential | YES (`test_bravery_quartile_combat_rate_2x`) |
| Spawn uniqueness | YES (`test_no_identical_personality_vectors_at_spawn`) |
| Edge case — zero-entity quartile | YES (assert `len >= 4`) |
| Edge case — zero combat rate | YES (assert `bottom_rate > 0`) |
| Feature flag not set | YES (explicit `feature_flags={"ENABLE_COMBAT_ENGAGEMENT": "ON"}`) |
| Regression — personality vector collision | YES (strict pass test 1) |

---

## CI Integration

Add `@pytest.mark.slow` to prevent accidental inclusion in fast unit runs. The test file
lives in `tests/integration/scenarios/` and is collected by the existing
`pytest tests/integration/scenarios/` command.

Suggested conftest marker registration (if not already present in `conftest.py`):
```python
config.addinivalue_line("markers", "slow: marks test as slow-running integration test")
config.addinivalue_line("markers", "integration: marks test as integration test")
```

---

## Dependencies

| Dependency | Status | Risk if Missing |
|---|---|---|
| TCK-20260619-E11A-HERO-AUTHORING | Prerequisite | test_no_identical_personality_vectors_at_spawn fails (no HERO entities with distinct bravery) |
| TCK-20260619-E11B-OBS-SNAPSHOT | Soft prerequisite | No direct impact on harness; personality already in entity.identity.personality |
| TCK-20260619-E11D-SCORING-CAL | Post-requisite | test_bravery_quartile_combat_rate_2x remains xfail |
| `ENABLE_COMBAT_ENGAGEMENT` feature flag | Must be ON | combat_engage rate = 0 for all entities |

---

## Execution Command

```bash
# Run just this file (fast discovery)
pytest tests/integration/scenarios/test_entity_differentiation.py -v

# Run without slow tests (skips 400-tick test)
pytest tests/integration/scenarios/test_entity_differentiation.py -v -m "not slow"

# Full domain scope run
pytest tests/integration/scenarios/ -v -m "not extra_slow"
```
