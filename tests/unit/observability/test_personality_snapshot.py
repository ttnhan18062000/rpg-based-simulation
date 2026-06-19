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


def test_existing_fields_unaffected():
    """All original M22 fields must still be present and correct after the personality extension."""
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
