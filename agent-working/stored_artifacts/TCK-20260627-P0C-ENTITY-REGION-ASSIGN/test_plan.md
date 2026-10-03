---
ticket_id: TCK-20260627-P0C-ENTITY-REGION-ASSIGN
phase: test_plan
---

# Test Plan: Fix navigation.region_id assignment at world compile

## Regression Surface (existing tests that must pass)

| Test | Why it matters |
|---|---|
| `tests/integration/worldassembly/test_e2e_smoke.py` | Compiles all 4 world compositions; must still pass |
| `tests/certification/test_world_compile_determinism.py` | Determinism must be maintained |
| `pytest tests/ -k "world" -m "not slow"` | Broad world-related regression surface |

## New Tests Required (per AC)

### AC1 + AC3: All entities have non-None navigation.region_id after compile

**File**: `tests/integration/worldassembly/test_e2e_smoke.py` (add assertion to existing test)

**Location**: In `test_smoke_urban_political_compiles_to_authoritative_state()`, add:
```python
assert all(e.navigation.region_id is not None for e in state.entities.values()), (
    "All entities must have navigation.region_id assigned at compile time"
)
```

**Or** add a new dedicated test:
```python
def test_urban_political_all_entities_have_region_id(repos):
    state, _ = _compile_composition("urban_political", repos)
    missing = [
        eid for eid, e in state.entities.items()
        if e.navigation.region_id is None
    ]
    assert missing == [], (
        f"Entities with region_id=None: {missing} (expected all to be assigned at compile)"
    )
```

### AC4: Existing world assembly tests pass (regression guard)

Run: `pytest tests/integration/worldassembly/ tests/certification/ -m "not slow" -v`

## Scoped Pytest Commands

Primary (focused):
```
pytest tests/integration/worldassembly/test_e2e_smoke.py -v -m "not slow"
```

Broader regression:
```
pytest tests/integration/worldassembly/ tests/certification/test_world_compile_determinism.py -v -m "not slow"
```

Full world regression:
```
pytest tests/ -k "world" -m "not slow" -v
```

## Anti-Drift Test Guards

- The new assertion must be inside the existing `test_smoke_urban_political_compiles_to_authoritative_state` test or a new test in `test_e2e_smoke.py` — NOT in a unit test that mocks the compiler, because the bug is in the integration between `WorldAssemblyResolver` → `WorldCompiler`.
- Determinism test must still pass (no RNG in the fix).
