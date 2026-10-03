# Test Plan — TCK-20260619-E53Aa-FACTION-STATE

## Regression Surface

Existing tests that must continue to pass after this ticket's changes:

| Test file | Why at risk |
|---|---|
| `tests/unit/core/test_authoritative_state_contract.py` | Directly checks `AuthoritativeState` field set and instantiation. New `factions` field must not break field-enumeration assertions or the `AuthoritativeState(tick=1, seed=1)` call. |
| `tests/unit/core/test_runtime_state_contract.py` | May instantiate `AuthoritativeState` — must still pass. |
| `tests/integration/pipeline/test_state_isolation.py` | Runs `apply_generation()` round trips. New `factions` field must be threaded through correctly or this test will catch state loss. |
| `tests/unit/optimization/test_state_update_compactor.py` | Uses `StateUpdate.merge()` / `merge_many()` — must not fail after `faction_updates` list is added. |
| `tests/integration/worldbuilding/test_world_compile_to_state.py` | Constructs full `AuthoritativeState` from world spec — must still instantiate without error. |

---

## New Tests Required

**File:** `tests/unit/faction/test_faction_state.py` (new file — create `tests/unit/faction/__init__.py` as well)

---

### test_faction_state_serialization_round_trip

**Purpose:** Verify `FactionState.to_canonical_dict()` and `FactionState.from_dict()` are inverses.

**Covers AC:** "FactionState is constructible, frozen, and serializes/deserializes via `to_canonical_dict()` / `from_dict()` round-trip"

```python
def test_faction_state_serialization_round_trip():
    from src.core.state import FactionState

    fs = FactionState(
        faction_id="hero_guild",
        territory=("region_north", "region_east"),
        resources={"gold": 100, "iron": 50},
        diplomatic_relations={"monster_horde": "hostile", "town_council": "allied"},
        active_doctrines=("doctrine_raid", "doctrine_defend"),
        military_strength=2.5,
        tension_level=0.3,
    )
    d = fs.to_canonical_dict()
    restored = FactionState.from_dict(d)

    assert restored == fs
    # Verify tuple fields survive JSON round-trip (list -> tuple)
    assert isinstance(restored.territory, tuple)
    assert isinstance(restored.active_doctrines, tuple)
    # Verify dict ordering is deterministic (canonical)
    keys = list(d["resources"].keys())
    assert keys == sorted(keys)
    keys2 = list(d["diplomatic_relations"].keys())
    assert keys2 == sorted(keys2)
```

**Edge cases to cover in additional parametrize / variants:**
- Empty `FactionState(faction_id="x")` round-trips to itself (all defaults).
- `tension_level=0.0`, `military_strength=1.0` survive round-trip without precision loss.

---

### test_authoritative_state_has_factions_field

**Purpose:** Verify `AuthoritativeState` accepts and stores `factions` dict.

**Covers AC:** "`AuthoritativeState(tick=0, seed=0)` instantiates with `factions={}` without error"

```python
def test_authoritative_state_has_factions_field():
    from dataclasses import fields
    from src.core.state import AuthoritativeState, FactionState

    # Default instantiation must work
    state = AuthoritativeState(tick=0, seed=0)
    assert hasattr(state, "factions")
    assert state.factions == {}

    # Field must appear in dataclass fields
    field_names = {f.name for f in fields(AuthoritativeState)}
    assert "factions" in field_names

    # Construction with a populated factions dict
    fs = FactionState(faction_id="hero_guild", military_strength=3.0)
    state2 = AuthoritativeState(tick=1, seed=0, factions={"hero_guild": fs})
    assert state2.factions["hero_guild"].military_strength == 3.0

    # Immutability — must raise FrozenInstanceError
    import pytest
    from dataclasses import FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        state.factions = {}  # type: ignore
```

---

### test_faction_update_apply_tension_delta

**Purpose:** Verify `FactionUpdate` with `tension_delta` accumulates correctly when applied through `ApplyPath`.

**Covers AC:** "`FactionUpdate` applies correctly: `tension_delta` accumulates"

```python
def test_faction_update_apply_tension_delta():
    from src.core.state import AuthoritativeState, FactionState
    from src.core.updates import StateUpdate, FactionUpdate
    from src.engine.apply import ApplyPath

    fs = FactionState(faction_id="monster_horde", tension_level=0.2)
    state = AuthoritativeState(tick=1, seed=0, factions={"monster_horde": fs})

    update = StateUpdate(
        faction_updates=[
            FactionUpdate(faction_id="monster_horde", tension_delta=0.1)
        ]
    )
    new_state = ApplyPath.apply_partial(state, update)

    assert "monster_horde" in new_state.factions
    result = new_state.factions["monster_horde"]
    assert abs(result.tension_level - 0.3) < 1e-9
    # military_strength unchanged
    assert result.military_strength == 1.0
```

---

### test_faction_update_territory_add_remove

**Purpose:** Verify `FactionUpdate.territory_add` and `territory_remove` merge correctly (set union/difference semantics).

**Covers AC:** "`FactionUpdate` applies correctly: `territory_add/remove` merge correctly"

```python
def test_faction_update_territory_add_remove():
    from src.core.state import AuthoritativeState, FactionState
    from src.core.updates import StateUpdate, FactionUpdate
    from src.engine.apply import ApplyPath

    fs = FactionState(
        faction_id="town_council",
        territory=("region_a", "region_b"),
    )
    state = AuthoritativeState(tick=1, seed=0, factions={"town_council": fs})

    update = StateUpdate(
        faction_updates=[
            FactionUpdate(
                faction_id="town_council",
                territory_add=("region_c",),
                territory_remove=("region_a",),
            )
        ]
    )
    new_state = ApplyPath.apply_partial(state, update)

    result_territory = set(new_state.factions["town_council"].territory)
    assert result_territory == {"region_b", "region_c"}
```

**Additional variant:**
```python
def test_faction_update_military_strength_set():
    """military_strength_set overwrites rather than accumulates."""
    from src.core.state import AuthoritativeState, FactionState
    from src.core.updates import StateUpdate, FactionUpdate
    from src.engine.apply import ApplyPath

    fs = FactionState(faction_id="neutral", military_strength=1.0)
    state = AuthoritativeState(tick=1, seed=0, factions={"neutral": fs})

    update = StateUpdate(
        faction_updates=[
            FactionUpdate(faction_id="neutral", military_strength_set=5.0)
        ]
    )
    new_state = ApplyPath.apply_partial(state, update)
    assert new_state.factions["neutral"].military_strength == 5.0
```

---

### test_faction_update_is_noop

**Purpose:** Verify `FactionUpdate.is_noop()` returns True for a zero-delta update.

```python
def test_faction_update_is_noop():
    from src.core.updates import FactionUpdate

    noop = FactionUpdate(faction_id="hero_guild")
    assert noop.is_noop()

    not_noop = FactionUpdate(faction_id="hero_guild", tension_delta=0.1)
    assert not not_noop.is_noop()
```

---

### test_state_update_merge_faction_updates

**Purpose:** Verify `StateUpdate.merge()` concatenates `faction_updates` lists and `is_noop()` reflects the new field.

```python
def test_state_update_merge_faction_updates():
    from src.core.updates import StateUpdate, FactionUpdate

    fu1 = FactionUpdate(faction_id="hero_guild", tension_delta=0.1)
    fu2 = FactionUpdate(faction_id="monster_horde", tension_delta=0.2)

    upd1 = StateUpdate(faction_updates=[fu1])
    upd2 = StateUpdate(faction_updates=[fu2])

    merged = upd1.merge(upd2)
    assert len(merged.faction_updates) == 2
    assert fu1 in merged.faction_updates
    assert fu2 in merged.faction_updates


def test_state_update_is_noop_with_faction_updates():
    from src.core.updates import StateUpdate, FactionUpdate

    empty = StateUpdate()
    assert empty.is_noop()

    with_faction = StateUpdate(
        faction_updates=[FactionUpdate(faction_id="x", tension_delta=0.1)]
    )
    assert not with_faction.is_noop()
```

---

### test_faction_state_factions_persist_across_ticks

**Purpose:** Regression — `factions` dict must survive `apply_generation()` tick advancement (guards against the `apply.py` omission hazard).

```python
def test_faction_state_factions_persist_across_ticks():
    from src.core.state import AuthoritativeState, FactionState
    from src.core.updates import StateUpdate
    from src.engine.apply import ApplyPath

    fs = FactionState(faction_id="hero_guild", tension_level=0.5)
    state = AuthoritativeState(tick=1, seed=0, factions={"hero_guild": fs})

    # Apply a no-op update and advance tick
    new_state = ApplyPath.apply_generation(state, StateUpdate(), next_tick=2)

    assert "hero_guild" in new_state.factions
    assert new_state.factions["hero_guild"].tension_level == 0.5
    assert new_state.tick == 2
```

---

## Scoped Pytest Commands

```bash
# Primary — new faction unit tests
pytest tests/unit/faction/ -x -v

# Regression — AuthoritativeState contract (must still pass)
pytest tests/unit/core/test_authoritative_state_contract.py -x -v

# Regression — state isolation (catches apply.py omission of factions)
pytest tests/integration/pipeline/test_state_isolation.py -x -v

# Regression — state update merge/compactor
pytest tests/unit/optimization/test_state_update_compactor.py -x -v

# Full scoped run (all of the above together)
pytest tests/unit/faction/ tests/unit/core/test_authoritative_state_contract.py tests/integration/pipeline/test_state_isolation.py tests/unit/optimization/test_state_update_compactor.py -x -v

# Exclude slow tests if needed
pytest tests/unit/faction/ tests/unit/core/ -x -v -m "not slow"
```

---

## Anti-Drift Test Guards

| Guard | What It Catches |
|---|---|
| `test_authoritative_state_has_factions_field` — asserts `"factions" in field_names` | Catches accidental removal of the field in a future refactor. |
| `test_faction_state_factions_persist_across_ticks` | Catches the `apply.py` omission hazard: if `factions=new_factions` is removed from the `AuthoritativeState(...)` call, this test fails with `assertion "hero_guild" in new_state.factions`. |
| `test_state_update_is_noop_with_faction_updates` | Catches `is_noop()` not being updated when `faction_updates` field is added. |
| `test_faction_state_serialization_round_trip` with `isinstance(restored.territory, tuple)` | Catches `from_dict` forgetting to convert list→tuple on JSON deserialization. |
| `test_authoritative_state_contract.py::test_authoritative_state_isolation` | Existing test — guards against unauthorized fields appearing on `AuthoritativeState`. `factions` is authorized and must appear in `field_names`; the test's `forbidden` set does not include `factions`. Verify it still passes after addition. |
