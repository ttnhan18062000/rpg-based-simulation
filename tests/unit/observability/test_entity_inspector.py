from __future__ import annotations
import pytest
from src.observability.live.entity_inspector import EntityInspector, EntityInspectionSnapshot
from src.observability.entity_timeline import EntityTimelineStore
from src.observability.config import ObservabilityMode
from src.observability.events import SimulationEvent
from src.core.state import (
    EntityState, CombatComponent, InventoryComponent, NavigationComponent,
    TaskComponent, IdentityComponent, AuthoritativeState, StrategicComponent
)
from src.core.strategic import ConcernState, ConcernKind, BlockerState, BlockerKind

def test_entity_inspector_idle():
    # 1. Test when manager is None
    snapshot = EntityInspector.inspect_entity(None, 42)
    assert isinstance(snapshot, EntityInspectionSnapshot)
    assert not snapshot.exists
    assert snapshot.entity_id == 42

    # 2. Test when latest_state is None
    class DummyManagerNoState:
        def __init__(self):
            self.latest_state = None
            self.kernel = None

    snapshot_no_state = EntityInspector.inspect_entity(DummyManagerNoState(), 42)
    assert not snapshot_no_state.exists

def test_entity_inspector_missing_entity():
    # Test when entity does not exist in state
    entity = EntityState(
        id=42,
        kind="HERO",
        combat=CombatComponent(hp=100, max_hp=100, tactical_role="VANGUARD", alive=True),
        inventory=InventoryComponent(gold=100, max_slots=10),
        navigation=NavigationComponent(position=(10.0, 20.0), target=(30.0, 40.0), region_id="forest_region"),
        task=TaskComponent(work_kind="FIGHT", payload={}),
        identity=IdentityComponent(faction=1, role=0, evolution_level=5, class_id="WARRIOR")
    )
    state = AuthoritativeState(tick=100, seed=1337, entities={42: entity})
    
    class DummyKernel:
        def __init__(self):
            self.entity_timeline_store = EntityTimelineStore(mode=ObservabilityMode.LIGHT)

    class DummyManager:
        def __init__(self):
            self.latest_state = state
            self.kernel = DummyKernel()

    snapshot = EntityInspector.inspect_entity(DummyManager(), 99)
    assert not snapshot.exists
    assert snapshot.entity_id == 99

def test_entity_inspector_active_entity():
    # Test inspecting a fully active entity
    entity = EntityState(
        id=42,
        kind="HERO",
        combat=CombatComponent(hp=80, max_hp=100, tactical_role="VANGUARD", alive=True),
        inventory=InventoryComponent(gold=150, max_slots=12),
        navigation=NavigationComponent(
            position=(10.0, 20.0), 
            target=(30.0, 40.0), 
            region_id="forest_region",
            oscillation_count=4,  # Triggers anomaly flag
            wait_count=6          # Triggers anomaly flag
        ),
        task=TaskComponent(work_kind="HARVEST", payload={}),
        identity=IdentityComponent(faction=2, role=1, evolution_level=10, class_id="MAGE")
    )
    # Set strategic fields
    strategic = StrategicComponent(
        current_project_id="quest_01",
        current_objective_id="gather_wood",
        boredom={"wood": 10}
    )
    # Re-build entity state to ensure strategic is bound
    entity = EntityState(
        id=entity.id,
        kind=entity.kind,
        combat=entity.combat,
        inventory=entity.inventory,
        navigation=entity.navigation,
        task=entity.task,
        identity=entity.identity,
        strategic=strategic
    )

    state = AuthoritativeState(tick=100, seed=1337, entities={42: entity})
    
    timeline_store = EntityTimelineStore(mode=ObservabilityMode.LIGHT)
    # Add timeline events
    ev1 = SimulationEvent(
        event_type="movement_success",
        event_category="movement",
        severity="INFO",
        source_system="locomotion_system",
        message="Moved to (10.0, 20.0)",
        tick=98,
        entity_id=42
    )
    ev2 = SimulationEvent(
        event_type="quest_started",
        event_category="quest",
        severity="WARNING",
        source_system="quest_system",
        message="Started quest_01",
        tick=99,
        entity_id=42
    )
    timeline_store.record(ev1)
    timeline_store.record(ev2)

    class DummyKernel:
        def __init__(self):
            self.entity_timeline_store = timeline_store

    class DummyManager:
        def __init__(self):
            self.latest_state = state
            self.kernel = DummyKernel()

    snapshot = EntityInspector.inspect_entity(DummyManager(), 42, timeline_limit=5)
    assert snapshot.exists
    assert snapshot.entity_id == 42
    assert snapshot.alive
    assert snapshot.position == (10.0, 20.0)
    assert snapshot.faction_id == 2
    assert snapshot.region_id == "forest_region"
    assert snapshot.current_goal == "gather_wood"
    assert snapshot.current_target == "(30.0, 40.0)"
    assert snapshot.current_action == "HARVEST"
    
    # Summaries
    assert snapshot.combat_summary["hp"] == 80
    assert snapshot.combat_summary["max_hp"] == 100
    assert snapshot.combat_summary["tactical_role"] == "VANGUARD"
    assert snapshot.inventory_summary["gold"] == 150
    assert snapshot.inventory_summary["item_count"] == 0
    assert snapshot.strategic_summary["current_project_id"] == "quest_01"
    
    # Timeline limiting and order (should be descending tick: 99 then 98)
    assert len(snapshot.recent_timeline_events) == 2
    assert snapshot.recent_timeline_events[0]["tick"] == 99
    assert snapshot.recent_timeline_events[0]["severity"] == "WARNING"
    assert snapshot.recent_timeline_events[1]["tick"] == 98
    assert snapshot.recent_timeline_events[1]["severity"] == "INFO"

    # Anomaly flags
    assert "HIGH_OSCILLATION" in snapshot.latest_anomaly_flags
    assert "HIGH_WAIT_COUNT" in snapshot.latest_anomaly_flags

def test_entity_inspector_dead_entity():
    # Test dead entity is still inspectable but shows alive = False
    entity = EntityState(
        id=42,
        kind="MONSTER",
        combat=CombatComponent(hp=0, max_hp=100, tactical_role="BRUTE", alive=False),
        inventory=InventoryComponent(gold=0, max_slots=5),
        navigation=NavigationComponent(position=(5.0, 5.0), target=None, region_id="graveyard"),
        task=TaskComponent(work_kind="DIE", payload={}),
        identity=IdentityComponent(faction=0, role=2, evolution_level=1, class_id="ZOMBIE")
    )
    state = AuthoritativeState(tick=105, seed=1337, entities={42: entity})
    
    class DummyKernel:
        def __init__(self):
            self.entity_timeline_store = EntityTimelineStore(mode=ObservabilityMode.LIGHT)

    class DummyManager:
        def __init__(self):
            self.latest_state = state
            self.kernel = DummyKernel()

    snapshot = EntityInspector.inspect_entity(DummyManager(), 42)
    assert snapshot.exists
    assert not snapshot.alive
    assert snapshot.combat_summary["hp"] == 0


# ---------------------------------------------------------------------------
# E43H — narrative_modifiers extraction (grief urgency + nemesis blockers)
# ---------------------------------------------------------------------------

def _simple_entity(eid: int = 1, strategic: "StrategicComponent | None" = None) -> "EntityState":
    return EntityState(
        id=eid,
        kind="worker",
        combat=CombatComponent(hp=80, max_hp=80, tactical_role="VANGUARD", alive=True),
        inventory=InventoryComponent(gold=0, max_slots=10),
        navigation=NavigationComponent(position=(0.0, 0.0), target=None, region_id="r1"),
        task=TaskComponent(work_kind="IDLE", payload={}),
        identity=IdentityComponent(faction=1, role=0, evolution_level=1, class_id="worker"),
        strategic=strategic or StrategicComponent(),
    )


def _dummy_manager(entity: "EntityState") -> object:
    from src.observability.entity_timeline import EntityTimelineStore
    state = AuthoritativeState(tick=1, seed=42, entities={entity.id: entity})

    class _K:
        entity_timeline_store = EntityTimelineStore(mode=ObservabilityMode.LIGHT)

    class _M:
        latest_state = state
        kernel = _K()

    return _M()


def test_narrative_modifiers_empty_when_no_grief_or_nemesis():
    entity = _simple_entity(1)
    snap = EntityInspector.inspect_entity(_dummy_manager(entity), 1)
    assert snap.narrative_modifiers["grief_concerns"] == []
    assert snap.narrative_modifiers["nemesis_blockers"] == []


def test_narrative_modifiers_grief_concern_extracted():
    concern = ConcernState(
        id="grief_ally_42",
        kind=ConcernKind.SOCIAL_THREAT,
        source="ally_42_died_ep0",
        urgency=0.6,
        created_tick=0,
    )
    strat = StrategicComponent(concerns={"grief_ally_42": concern})
    entity = _simple_entity(1, strat)
    snap = EntityInspector.inspect_entity(_dummy_manager(entity), 1)

    grief = snap.narrative_modifiers["grief_concerns"]
    assert len(grief) == 1
    assert grief[0]["concern_id"] == "grief_ally_42"
    assert grief[0]["dead_ally_id"] == 42
    assert grief[0]["urgency"] == pytest.approx(0.6)
    assert snap.narrative_modifiers["nemesis_blockers"] == []


def test_narrative_modifiers_nemesis_blocker_extracted():
    blocker = BlockerState(
        id="nemesis_9",
        kind=BlockerKind.SOCIAL,
        subject="9",
        severity=0.8,
    )
    strat = StrategicComponent(blockers={"nemesis_9": blocker})
    entity = _simple_entity(1, strat)
    snap = EntityInspector.inspect_entity(_dummy_manager(entity), 1)

    nemesis = snap.narrative_modifiers["nemesis_blockers"]
    assert len(nemesis) == 1
    assert nemesis[0]["blocker_id"] == "nemesis_9"
    assert nemesis[0]["antagonist_id"] == 9
    assert nemesis[0]["severity"] == pytest.approx(0.8)
    assert snap.narrative_modifiers["grief_concerns"] == []


def test_narrative_modifiers_non_narrative_blockers_excluded():
    material_blocker = BlockerState(
        id="need_iron",
        kind=BlockerKind.MATERIAL,
        subject="iron_ore",
        severity=0.5,
    )
    strat = StrategicComponent(blockers={"need_iron": material_blocker})
    entity = _simple_entity(1, strat)
    snap = EntityInspector.inspect_entity(_dummy_manager(entity), 1)
    assert snap.narrative_modifiers["nemesis_blockers"] == []


def test_narrative_modifiers_both_grief_and_nemesis():
    concern = ConcernState(
        id="grief_ally_7",
        kind=ConcernKind.SOCIAL_THREAT,
        source="ally_7_died_ep1",
        urgency=0.35,
        created_tick=10,
    )
    blocker = BlockerState(
        id="nemesis_5",
        kind=BlockerKind.SOCIAL,
        subject="5",
        severity=0.4,
    )
    strat = StrategicComponent(
        concerns={"grief_ally_7": concern},
        blockers={"nemesis_5": blocker},
    )
    entity = _simple_entity(1, strat)
    snap = EntityInspector.inspect_entity(_dummy_manager(entity), 1)

    assert len(snap.narrative_modifiers["grief_concerns"]) == 1
    assert snap.narrative_modifiers["grief_concerns"][0]["dead_ally_id"] == 7
    assert len(snap.narrative_modifiers["nemesis_blockers"]) == 1
    assert snap.narrative_modifiers["nemesis_blockers"][0]["antagonist_id"] == 5
