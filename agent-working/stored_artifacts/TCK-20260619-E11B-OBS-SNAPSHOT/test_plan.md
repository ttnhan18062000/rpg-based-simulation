---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E11B-OBS-SNAPSHOT
artifact_type: test_plan
tags: [entity-differentiation, observability, personality, class-system, phase-1]
---

# Test Plan — TCK-20260619-E11B-OBS-SNAPSHOT

## Regression Surface

Changes touch exactly two files:
1. `src/observability/live/entity_inspector.py` — `EntityInspectionSnapshot` (new fields)
   and `EntityInspector.inspect_entity()` (new field assignments).

Tests that exercise this code and must not regress:

| Test file | What it covers |
|---|---|
| `tests/unit/observability/test_entity_inspector.py` | All existing `EntityInspectionSnapshot` fields; exists/alive/position/faction_id/anomaly flags/timeline events. Four test cases. |
| `tests/unit/observability/test_live_snapshot_provider.py` | `LiveSnapshotProvider` which calls `EntityInspector.inspect_entity()` indirectly. |
| `tests/integration/observability/test_cognition_snapshot_artifact.py` | Cognition snapshot pipeline — uses `ObservabilityMode.LIGHT`; should remain unaffected. |
| `tests/integration/observability/test_kernel_event_recording.py` | Kernel event recording with `EntityTimelineStore` in LIGHT mode. |

**All existing tests must pass without modification.** The only code change is additive
(new fields with defaults on `EntityInspectionSnapshot`; new assignments in one constructor
call in `inspect_entity()`).

---

## New Tests Required

### Test file: `tests/unit/observability/test_personality_snapshot.py`

#### `test_light_snapshot_includes_personality`

**Purpose:** Verify that a LIGHT-mode snapshot for an entity with known personality values
includes `role`, `class_id`, and `personality` dict with all four float fields.

**Approach:** Construct a minimal `EntityState` using `PersonalityComponent` with
explicit non-default values. Build a minimal manager stub. Call
`EntityInspector.inspect_entity()`. Assert field presence and types.

**Skeleton:**
```python
from __future__ import annotations
import pytest
from src.observability.live.entity_inspector import EntityInspector, EntityInspectionSnapshot
from src.observability.entity_timeline import EntityTimelineStore
from src.observability.config import ObservabilityMode
from src.core.state import (
    EntityState, CombatComponent, InventoryComponent, NavigationComponent,
    TaskComponent, IdentityComponent, PersonalityComponent, AuthoritativeState,
    StrategicComponent
)

def _make_entity(entity_id: int, personality: PersonalityComponent, class_id: str, role: int) -> EntityState:
    return EntityState(
        id=entity_id,
        kind="HERO",
        combat=CombatComponent(hp=100, max_hp=100, tactical_role="VANGUARD", alive=True),
        inventory=InventoryComponent(gold=50, max_slots=10),
        navigation=NavigationComponent(position=(1.0, 1.0), target=None, region_id="test_region"),
        task=TaskComponent(work_kind="IDLE", payload={}),
        identity=IdentityComponent(
            role=role,
            class_id=class_id,
            personality=personality,
        ),
    )

def _make_manager(entity: EntityState):
    state = AuthoritativeState(tick=1, seed=42, entities={entity.id: entity})
    class DummyKernel:
        entity_timeline_store = EntityTimelineStore(mode=ObservabilityMode.LIGHT)
    class DummyManager:
        latest_state = state
        kernel = DummyKernel()
    return DummyManager()


def test_light_snapshot_includes_personality():
    """LIGHT snapshot must include role, class_id, and personality dict with four float fields."""
    personality = PersonalityComponent(greed=0.8, bravery=0.3, sociability=0.5, industry=0.9)
    entity = _make_entity(1, personality, class_id="WARRIOR", role=0)
    manager = _make_manager(entity)

    snapshot = EntityInspector.inspect_entity(manager, 1)

    assert snapshot.exists
    # role
    assert hasattr(snapshot, "role")
    assert snapshot.role == 0
    # class_id
    assert hasattr(snapshot, "class_id")
    assert snapshot.class_id == "WARRIOR"
    # personality dict
    assert hasattr(snapshot, "personality")
    p = snapshot.personality
    assert isinstance(p, dict)
    assert set(p.keys()) == {"greed", "bravery", "sociability", "industry"}
    assert isinstance(p["greed"], float)
    assert isinstance(p["bravery"], float)
    assert isinstance(p["sociability"], float)
    assert isinstance(p["industry"], float)
    assert p["greed"] == pytest.approx(0.8)
    assert p["bravery"] == pytest.approx(0.3)
    assert p["sociability"] == pytest.approx(0.5)
    assert p["industry"] == pytest.approx(0.9)


def test_light_snapshot_personality_non_none_for_compiled_entity():
    """Personality fields must be non-None even for a default-constructed PersonalityComponent."""
    entity = _make_entity(2, PersonalityComponent(), class_id="NOVICE", role=0)
    manager = _make_manager(entity)

    snapshot = EntityInspector.inspect_entity(manager, 2)

    assert snapshot.exists
    assert snapshot.personality is not None
    assert snapshot.class_id is not None
    assert snapshot.role is not None
    # All four fields present, even if zero
    for key in ("greed", "bravery", "sociability", "industry"):
        assert key in snapshot.personality
        assert snapshot.personality[key] is not None


def test_light_snapshot_missing_entity_has_no_personality():
    """Missing entity snapshot must still return safely with None/default personality."""
    entity = _make_entity(3, PersonalityComponent(), class_id="NOVICE", role=0)
    manager = _make_manager(entity)

    snapshot = EntityInspector.inspect_entity(manager, 999)  # entity not in state

    assert not snapshot.exists
    # Fields must have safe defaults — not raise AttributeError
    assert snapshot.personality == {} or snapshot.personality is None
    assert snapshot.class_id is None or snapshot.class_id == ""
```

#### Additional regression guard: `test_existing_fields_unaffected`

**Purpose:** Confirm that adding the new fields does not remove or rename any existing
fields in `EntityInspectionSnapshot`.

```python
def test_existing_fields_unaffected():
    """All original M22 fields must still be present and correct after the personality extension."""
    from pydantic.fields import FieldInfo
    model_fields = EntityInspectionSnapshot.model_fields
    required = [
        "entity_id", "exists", "alive", "position", "faction_id", "region_id",
        "current_goal", "current_target", "current_action",
        "combat_summary", "inventory_summary", "quest_summary",
        "strategic_summary", "recent_timeline_events",
        "latest_rejection_reason", "latest_anomaly_flags",
    ]
    for field in required:
        assert field in model_fields, f"Regression: field '{field}' missing from EntityInspectionSnapshot"
```

---

## Scoped Pytest Commands

Run these — in this order — during and after implementation:

```bash
# 1. New unit tests only (fast, during TDD)
pytest tests/unit/observability/test_personality_snapshot.py -v

# 2. Full entity inspector unit suite (regression check)
pytest tests/unit/observability/test_entity_inspector.py tests/unit/observability/test_live_snapshot_provider.py -v

# 3. Observability unit suite (broad regression)
pytest tests/unit/observability/ -v -m "not slow"

# 4. Observability integration (confirm no pipeline breakage)
pytest tests/integration/observability/test_cognition_snapshot_artifact.py tests/integration/observability/test_kernel_event_recording.py -v
```

Do **not** run `pytest tests/` (full suite) — scope to the observability domain only.

---

## Anti-Drift Test Guards

1. **`test_existing_fields_unaffected`** (above) — model-field presence assertion prevents
   accidental removal of original `EntityInspectionSnapshot` fields when editing the class.

2. **Explicit key-set assertion on personality dict** — `assert set(p.keys()) == {"greed",
   "bravery", "sociability", "industry"}` prevents future `PersonalityComponent` field
   additions silently changing the snapshot contract without a corresponding test update.

3. **Missing entity safe-default guard** — `test_light_snapshot_missing_entity_has_no_personality`
   ensures the three early-return `EntityInspectionSnapshot(entity_id=..., exists=False)`
   constructors (entity_inspector.py L33, L40, L44) do not raise when the new fields are
   accessed, confirming all new fields carry valid defaults.

4. **Float type assertion** — `isinstance(p["greed"], float)` prevents future refactors
   from changing personality values to int or string without detection.
