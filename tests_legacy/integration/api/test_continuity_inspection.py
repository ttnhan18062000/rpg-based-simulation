from __future__ import annotations
import pytest
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.models.continuity import SuccessorRecord
from src_legacy.core.models.households import HouseholdRecord
from src_legacy.core.entities.entity import Entity
from src_legacy.core.aspects.identity import IdentityAspect
from src_legacy.api.presenters.entity_presenter import EntityPresenter
from src_legacy.config import SimulationConfig

@pytest.fixture
def continuity_setup():
    config = SimulationConfig()
    from src_legacy.core.world.grid import Grid
    from src_legacy.systems.spatial_hash import SpatialHash
    grid = Grid(config.grid_width, config.grid_height)
    spatial = SpatialHash(config.spatial_cell_size)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    # 1. Setup a Predecessor and Successors
    # In Phase 4, SuccessorRecord maps PREDECESSOR ID to successor details
    successor_rec = SuccessorRecord(
        source_entity_id=101, # The dead legend
        successor_entity_id=202, # The heir
        death_event_id="evt_death_101",
        motive_fragments={
            "predecessor_name": "Old Hero",
            "legacy_level": 5
        },
        tick=50
    )
    world.successor_registry[202] = successor_rec # Keyed by heir ID for lookup during inspection
    
    # 2. Setup a Household
    household_rec = HouseholdRecord(
        household_id="hh_north_gate",
        home_building_id=500,
        member_ids={202, 303},
        reputation=0.85,
        legacy_tags=["ancient_bloodline"]
    )
    world.household_registry["hh_north_gate"] = household_rec
    
    # 3. Create the heir Entity
    heir = Entity(id=202, kind="hero")
    heir.identity = IdentityAspect()
    heir.identity.display_name = "Young Hero"
    heir.identity.generation = 2
    heir.identity.household_id = "hh_north_gate"
    
    world.entities[202] = heir
    
    snapshot = Snapshot.from_world(world)
    return snapshot, heir

def test_continuity_inspection_mapping(continuity_setup):
    snapshot, heir = continuity_setup
    
    # Act: Present the entity for inspection
    # The world (Snapshot) is passed so the presenter can access registries
    inspection = EntityPresenter.to_inspection_schema(heir, loot_duration=3, world=snapshot)
    
    # Assert
    assert inspection.entity.id == 202
    assert inspection.entity.generation == 2
    assert inspection.entity.household_id == "hh_north_gate"
    
    # Successor Record Check
    assert inspection.successor_record is not None
    assert inspection.successor_record.source_entity_id == 101
    assert inspection.successor_record.predecessor_name == "Old Hero"
    assert inspection.successor_record.legacy_level == 5
    assert inspection.successor_record.inherited_motive_count == 2
    
    # Household Record Check
    assert inspection.household_record is not None
    assert inspection.household_record.household_id == "hh_north_gate"
    assert inspection.household_record.reputation == 0.85
    assert inspection.household_record.member_count == 2
    assert "ancient_bloodline" in inspection.household_record.legacy_tags

def test_missing_continuity_handling():
    config = SimulationConfig()
    from src_legacy.core.world.grid import Grid
    from src_legacy.systems.spatial_hash import SpatialHash
    grid = Grid(config.grid_width, config.grid_height)
    spatial = SpatialHash(config.spatial_cell_size)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    # Entity with NO legacy or household
    loner = Entity(id=999, kind="hero")
    loner.identity = IdentityAspect()
    world.entities[999] = loner
    
    snapshot = Snapshot.from_world(world)
    
    # Act
    inspection = EntityPresenter.to_inspection_schema(loner, loot_duration=3, world=snapshot)
    
    # Assert
    assert inspection.successor_record is None
    assert inspection.household_record is None
    assert inspection.entity.generation == 1 # Default
    assert inspection.entity.household_id is None
