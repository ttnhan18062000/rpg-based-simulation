import pytest
from src_legacy.core.models.history import WorldHistoryRegistry, HistoricalEvent, EventKind
from src_legacy.core.models.households import HouseholdRecord
from src_legacy.core.models.local_scars import LocalScarRecord, ScarKind
from src_legacy.core.models.regions import RegionConsequenceRecord
from src_legacy.core.models.vectors import Vector2

def test_history_registry_serialization():
    registry = WorldHistoryRegistry()
    event = HistoricalEvent(
        event_id="evt_01",
        tick=1000,
        kind=EventKind.RAID,
        location=Vector2(10, 20),
        involved_ids={1, 2},
        tags=["traumatic"]
    )
    registry.add_event(event)
    
    # Check retrieval
    assert registry.get_event("evt_01").kind == EventKind.RAID
    
    # Check serialization/copy
    registry.freeze()
    copy_reg = registry.copy()
    assert copy_reg.events["evt_01"].event_id == "evt_01"
    assert "evt_01" in copy_reg.events

def test_household_record():
    house = HouseholdRecord(
        household_id="house_01",
        home_building_id=505,
        member_ids={1, 2},
        reputation=50.0,
        legacy_tags=["founders"]
    )
    assert house.reputation == 50.0
    house.freeze()
    assert house._frozen

def test_local_scar_record():
    scar = LocalScarRecord(
        location_pos=Vector2(50, 50),
        kind=ScarKind.RAID_DAMAGE,
        severity=0.8,
        created_tick=5000,
        source_event_id="evt_raid_01"
    )
    assert scar.severity == 0.8
    assert scar.source_event_id == "evt_raid_01"

def test_region_consequence_record():
    region_con = RegionConsequenceRecord(
        region_id="reg_forest",
        danger_level=0.5,
        stability=0.2
    )
    assert region_con.danger_level == 0.5
    assert region_con.stability == 0.2

def test_world_state_integration_phase4():
    from src_legacy.core.models.world_state import WorldState
    from src_legacy.core.world.grid import Grid
    from src_legacy.platform.spatial_hash import SpatialHash
    
    world = WorldState(seed=42, grid=Grid(10, 10), spatial_index=SpatialHash(cell_size=10))
    
    # Add data to Phase 4 registries
    event = HistoricalEvent(event_id="e1", tick=1, kind=EventKind.DEATH)
    world.world_history.add_event(event)
    
    house = HouseholdRecord(household_id="h1", home_building_id=10)
    world.household_registry["h1"] = house
    
    scar = LocalScarRecord(location_pos=Vector2(0,0), kind=ScarKind.FEAR_ZONE, created_tick=1, source_event_id="e1")
    world.scar_registry.append(scar)
    
    region_con = RegionConsequenceRecord(region_id="r1", danger_level=0.1)
    world.region_consequence_registry["r1"] = region_con
    
    # Test Freeze & Copy
    world.freeze()
    snapshot = WorldState.from_snapshot(world, world.spatial_index)
    
    assert snapshot.world_history.get_event("e1").event_id == "e1"
    assert snapshot.household_registry["h1"].household_id == "h1"
    assert len(snapshot.scar_registry) == 1
    assert snapshot.region_consequence_registry["r1"].danger_level == 0.1
    
    # Verify isolation
    assert snapshot is not world
    assert snapshot.world_history is not world.world_history
